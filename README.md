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
- Core input types: URL, raw text, media upload
- Source tracking with `source_kind`: `url_text | raw_text | transcript | uploaded_support | extracted_article`
- Reconstruction outputs with explicit `output_type`: `base | preview | review | easier`
- Recomposition modes are intentionally limited to exactly: `preview`, `review`, `easier`
- Support-material handling is separated via `supplemental_explanation`

## Run tests

```bash
python -m pytest -q
```

## Small public beta deployment (FastAPI)

### What this beta supports now
- Raw-text reconstruction via the web form
- Simple URL-to-text extraction path in the MVP pipeline
- Mode comparison across `base`, `preview`, `review`, and `easier`
- Support-material separation via `supplemental_explanation`

### Not supported yet
- Embedded-video handling
- Media transcription
- Advanced ingestion workflows

### Install

```bash
pip install -r requirements.txt
```

### Local run

```bash
uvicorn seminar_compass.web:app --reload
```

### Render start command

```bash
uvicorn seminar_compass.web:app --host 0.0.0.0 --port $PORT
```

### Railway start command

```bash
uvicorn seminar_compass.web:app --host 0.0.0.0 --port $PORT
```
