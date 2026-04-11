# Seminar Compass Specification

## Product definition
Seminar Compass is a learning reconstruction tool that helps users understand long or dense learning content before they get frustrated.

It is not just a summarizer.

It restructures content into a learner-friendly format by separating:
- main points
- claims
- conditions and assumptions
- prerequisite knowledge
- priorities
- noise and optional material

It supports both video-based and text-based learning content.

---

## Core goals
- prevent drop-off before understanding
- make the main point visible early
- separate signal from noise
- surface missing prerequisite knowledge
- support strong preview before full consumption
- support retrieval-based review instead of passive rereading
- allow recomposition without changing facts
- provide grounded prerequisite support using explicit reference materials only

---

## Supported content
- seminar videos
- webinars
- lecture recordings
- audio learning content
- transcripts
- articles
- notes
- manuals
- dense study text
- document text

---

## Main user problems
Users often drop off before understanding because:
- they cannot tell what matters most
- too much information is presented without visible priority
- prerequisite knowledge is missing
- the original speaker or writer may explain poorly
- the content level may not match the learner
- they do not want to fully consume 1-hour videos or long dense text just to understand the main idea

---

## MVP scope

### Inputs
- URL input
- raw text input
- audio/video upload
- optional support-material input

### Core processing
- extract readable text from URLs when possible
- inspect embedded video pages when possible
- transcribe uploaded audio/video
- clean transcript or text
- preserve timestamps when available
- preserve paragraph/reference positions for text

### Core outputs
- top 3 takeaways
- main claim
- conditions / assumptions
- practical takeaway
- prerequisite knowledge
- what to watch/read first
- safely skippable parts
- original-order summary
- learner-friendly reconstructed summary
- 3-line reactivation summary
- retrieval questions
- confidence note
- source references

### Recomposition
The system must support recomposition modes such as:
- shorter
- easier
- more practical
- preview mode
- review mode
- stronger prerequisite support

Recomposition must not change facts.

---

## Core principles
- learning reconstruction over plain summarization
- priority compression over equal-weight summaries
- preserve the relationship between claim and condition
- separate original content from supplemental explanation
- no unsupported factual supplementation
- no uncertain inference presented as fact
- learner-level adaptation is allowed only in explanation granularity, not in facts

---

## Grounded support-material rule
If support materials are provided, they must be used only as explicit references.

The system must:
- clearly state which materials were used
- keep original-content summary separate from supplemental explanation
- avoid unsupported conclusions
- avoid uncertain inference
- mark insufficient evidence when support materials are weak or incomplete

---

## Review design
Review should be retrieval-based, not passive rereading.

The system should generate:
- a short reactivation summary
- recall prompts
- a prompt asking the learner to restate the main claim
- a prompt asking the learner to state the next action
- pointers back to the original content only where needed

---

## Final definition
Seminar Compass is a learning assistance tool that reconstructs long or dense learning content into a format that helps users understand it before they lose motivation.
