# Changelog

All notable changes to the Talent Scout Actor will be documented in this file.

## [Unreleased]

### v2 - Multi-Source Scraping
- Added parallel scraping from 3 sources: LinkedIn, GitHub, Google
- Results stored in separate named datasets (`linkedin`, `github`, `google`)
- Normalized profile format across all sources
- Added `sources` input to select which platforms to scrape

### Planning Phase
- Created PRD.md with detailed specifications
- Defined input/output schemas
- Mapped LinkedIn Actor integration
- Designed LLM scoring approach

---

## Version History

### [0.1.0] - 2026-01-17
**MVP Release**

#### Added
- Initial Actor structure using `python-empty` template
- LinkedIn search integration via `harvestapi/linkedin-profile-search`
- LLM-based candidate scoring using OpenAI GPT-4o-mini
- Input schema with validation (jobTitle, jobDescription, requiredSkills)
- Ranked candidate output with scores 1-100
- Experience extraction from profiles
- Status messages for progress tracking

#### Technical
- Python 3.12+ base
- Apify Python SDK integration
- OpenAI API integration
- Async architecture

#### Files Created
- `.actor/actor.json` - Actor configuration
- `.actor/input_schema.json` - Input validation schema
- `src/main.py` - Main Actor logic
- `requirements.txt` - Dependencies (apify, apify-client, openai)
