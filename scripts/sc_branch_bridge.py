#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def run(cmd: list[str], check: bool = True) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc.stdout.strip()


def parse_allowed_files(raw: str) -> list[str]:
    items = [p.strip() for p in re.split(r"[\n,]", raw) if p.strip()]
    unique: list[str] = []
    for item in items:
        if item not in unique:
            unique.append(item)
    return unique


def assert_safe_repo_path(path: str) -> None:
    if path.startswith("/"):
        raise ValueError(f"Absolute path is not allowed: {path}")
    p = Path(path)
    if ".." in p.parts:
        raise ValueError(f"Parent traversal is not allowed: {path}")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "task"


def changed_files() -> list[str]:
    out = run(["git", "diff", "--name-only"])
    return [line.strip() for line in out.splitlines() if line.strip()]


def apply_full_file_replace(payload: dict[str, Any], allowed: set[str]) -> None:
    files = payload.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("target_files_payload for full_file_replace must be JSON: {\"files\": [...]} with at least one file")

    for item in files:
        if not isinstance(item, dict):
            raise ValueError("Each files[] item must be an object with path/content")
        path = item.get("path")
        content = item.get("content")
        if not isinstance(path, str) or not isinstance(content, str):
            raise ValueError("Each files[] item requires string path and content")
        assert_safe_repo_path(path)
        if path not in allowed:
            raise ValueError(f"Payload contains file not in allowed_files: {path}")
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")


def apply_patch(payload: dict[str, Any]) -> None:
    patch = payload.get("patch")
    if not isinstance(patch, str) or not patch.strip():
        raise ValueError("target_files_payload for patch mode must be JSON: {\"patch\": \"...\"}")

    temp_patch = Path(".sc_branch_bridge.patch")
    temp_patch.write_text(patch, encoding="utf-8")
    try:
        run(["git", "apply", "--whitespace=nowarn", str(temp_patch)])
    finally:
        if temp_patch.exists():
            temp_patch.unlink()


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seminar Compass branch/PR safety bridge")
    parser.add_argument("--task-name", required=True)
    parser.add_argument("--allowed-files", required=True)
    parser.add_argument("--change-mode", choices=["full_file_replace", "patch"], required=True)
    parser.add_argument("--target-files-payload", required=True)
    parser.add_argument("--dry-run", default="false")
    parser.add_argument("--base-main-sha", required=True)
    parser.add_argument("--pr-title", default="")
    parser.add_argument("--pr-body", default="")
    args = parser.parse_args()

    dry_run = str(args.dry_run).lower() == "true"
    allowed = parse_allowed_files(args.allowed_files)
    if not allowed:
        raise ValueError("allowed_files cannot be empty")
    allowed_set = set(allowed)

    base_sha = run(["git", "rev-parse", args.base_main_sha])
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    branch_name = f"autofix/{slugify(args.task_name)[:40]}-{timestamp}"

    run(["git", "checkout", "-B", branch_name, base_sha])

    try:
        payload = json.loads(args.target_files_payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"target_files_payload must be valid JSON: {exc}") from exc

    if args.change_mode == "full_file_replace":
        apply_full_file_replace(payload, allowed_set)
    else:
        apply_patch(payload)

    files_changed = changed_files()
    if not files_changed:
        raise RuntimeError("No effective diff exists; stopping safely.")

    disallowed = sorted(set(files_changed) - allowed_set)
    if disallowed:
        raise RuntimeError(
            "Changed files exceed allowlist. "
            f"Allowed={sorted(allowed_set)} Actual={sorted(set(files_changed))} Disallowed={disallowed}"
        )

    if len(files_changed) > len(allowed_set):
        raise RuntimeError("Scope safety check failed: changed file count exceeds allowlist size.")

    commit_hash = ""
    if not dry_run:
        run(["git", "add", "--", *files_changed])
        commit_message = f"sc-bridge: {args.task_name.strip()}"
        run(["git", "commit", "-m", commit_message])
        commit_hash = run(["git", "rev-parse", "HEAD"])

    manifest = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_name": args.task_name,
        "base_main_sha": base_sha,
        "fresh_branch_name": branch_name,
        "allowed_files": allowed,
        "actual_changed_files": files_changed,
        "commit_hash": commit_hash or None,
        "pr_url": None,
        "dry_run": dry_run,
    }

    manifest_path = Path("artifacts/branch_bridge") / f"{timestamp}-{slugify(args.task_name)[:40]}.json"
    write_manifest(manifest_path, manifest)

    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as fh:
            fh.write(f"branch_name={branch_name}\n")
            fh.write(f"base_main_sha={base_sha}\n")
            fh.write(f"commit_hash={commit_hash}\n")
            fh.write(f"changed_files={','.join(files_changed)}\n")
            fh.write(f"manifest_path={manifest_path}\n")
            fh.write(f"dry_run={'true' if dry_run else 'false'}\n")

    print(json.dumps({
        "branch_name": branch_name,
        "base_main_sha": base_sha,
        "commit_hash": commit_hash,
        "changed_files": files_changed,
        "manifest_path": str(manifest_path),
        "dry_run": dry_run,
    }, indent=2))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # fail safely with useful context
        print(f"sc_branch_bridge failed: {exc}", file=sys.stderr)
        raise
