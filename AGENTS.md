# AGENTS.md

These instructions apply to AI coding agents working in this repository.

## Repository Role

Seminar Compass is a learning reconstruction tool.

It is not a generic summarizer.

It helps transform provided learning material into structured learning outputs such as main claims, assumptions, prerequisites, priorities, practical takeaways, retrieval questions, and short reactivation summaries.

## Required Reading

Before editing, read:

1. `README.md`
2. `docs/STATUS.md`
3. `docs/NEXT.md`

## Default Mode

Use strict minimal patch mode unless the task explicitly says otherwise.

Prefer:

- small diffs
- local validation first
- stable output contracts
- clear learning sections
- preservation of assumptions and conditions
- documentation before expansion

## Forbidden by Default

Do not perform any of the following without explicit operator approval in the current task:

- broad refactor
- dependency replacement
- output contract rewrite
- removal of assumption or condition sections
- conversion into a generic summarizer
- conversion into a general note app
- automatic publishing behavior
- background jobs
- cross-repository migration

If a task appears to require one of these, stop and write a proposal.

## Learning Reconstruction Boundary

AI may structure learning material.

AI may identify claims, conditions, assumptions, prerequisites, priorities, and retrieval prompts.

AI must not hide uncertainty or remove context for convenience.

## Change Scope Rule

Before editing, identify:

- files you plan to change
- files you will not touch
- assumptions
- risks
- stop conditions

After editing, report:

- changed files
- what changed
- what did not change
- validation performed
- remaining risks
- recommended next task

## Unknown Handling

When uncertain, classify the unknown as:

- product unknown
- learning design unknown
- input unknown
- output contract unknown
- runtime unknown
- operator intent unknown

Then either proceed with the smallest safe local draft or stop with a proposal.
