# Seminar Compass

Seminar Compass is a learning reconstruction tool designed to help users understand long or dense learning content before they get frustrated.

It is not just a summarizer.

It separates:
- main points
- conditions and assumptions
- prerequisite knowledge
- priorities
- noise and optional material

It then restructures the content into a learner-friendly format for:
- preview
- active learning
- retrieval-based review
- grounded prerequisite support

## Supported content
- seminar videos
- webinars
- lecture videos
- audio learning content
- transcripts
- articles
- dense study text
- manuals
- notes
- document text

## MVP scope
- URL input
- raw text input
- audio/video upload
- transcript or text cleaning
- top 3 takeaways
- main claim / conditions / practical takeaway
- prerequisite knowledge
- what to watch/read first
- safely skippable parts
- 3-line reactivation summary
- retrieval questions
- basic recomposition
- source references
- confidence notes

## Core principles
- learning reconstruction over plain summarization
- priority compression over equal-weight summaries
- strong preview before full consumption
- retrieval-based review instead of passive rereading
- no unsupported factual supplementation
- clear separation between original content and supplemental support

## MVP implementation status
Current code implements a minimal reconstruction pipeline in `seminar_compass/`:
- Current active user flow: raw text input (URL/media ingestion intentionally deferred in this step)
- Source tracking with `source_kind`: `url_text | raw_text | transcript | uploaded_support | extracted_article`
- Reconstruction outputs with explicit `output_type`: `base | preview | review | easier`
- Recomposition modes are intentionally limited to exactly: `preview`, `review`, `easier`
- Support-material handling is separated via `supplemental_explanation`

Run tests:

```bash
python -m pytest -q
```


## Minimal user-facing entrypoint (raw text)
Run the raw-text MVP flow and print an inspectable result view:

```bash
python -m seminar_compass.cli --text "Your learning content here."
```

Optional:
- `--text-file path/to/input.txt`
- `--support-file path/to/support1.txt --support-file path/to/support2.txt`
- `--mode base|preview|review|easier`
