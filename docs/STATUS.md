# Seminar Compass Status

Status: ACTIVE / PRODUCT / MINIMUM ALIVE

Seminar Compass is a learning reconstruction tool.

It is not a generic summarizer.

Its purpose is to transform seminars, webinars, transcripts, articles, manuals, and other learning materials into reviewable learning structures: main claims, assumptions, prerequisites, priorities, practical takeaways, skippable material, and retrieval prompts.

## Current Position

Seminar Compass should remain focused on learning reconstruction.

Allowed by default:

- ingest provided text or local input
- clean and structure transcripts
- extract main claims
- separate assumptions and conditions
- identify prerequisite knowledge
- identify practical takeaways
- identify low-priority or skippable material
- generate retrieval questions
- generate short reactivation summaries
- preserve source references where available
- provide local or reviewable outputs

Prohibited by default:

- claiming unsupported facts as verified
- hiding uncertainty
- removing source context silently
- turning learning reconstruction into generic content generation
- adding external ingestion integrations without approval
- adding automatic publishing behavior
- adding background jobs
- weakening source tracking
- broad refactor without a task contract

## Product Boundary

Seminar Compass is adjacent to RTS but should remain an independent product candidate.

It may use RTS-style thinking around evidence, assumptions, and reconstructability.

It should not become RTS core.

It should not become RTS-AGE.

It should not become a general-purpose note app, LMS, scraping tool, or content farm generator.

## Minimum Alive Definition

This repository is considered Minimum Alive when:

1. Its learning reconstruction role is explicit.
2. Its next smallest validation tasks are documented.
3. Its agent rules prevent generic summarizer drift.
4. Source tracking and uncertainty boundaries are preserved.
5. No runtime behavior is changed by the rescue documentation itself.

## Current Decision

Keep this repository.

Treat it as an independent product candidate based on RTS-style learning reconstruction.

Do not merge it into RTS core.

Do not expand it into external ingestion or publishing until the local workflow is validated.
