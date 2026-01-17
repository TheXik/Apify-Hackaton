# Talent Scout - Product Requirements Document

## Overview

**Talent Scout** is an Apify Actor that automates candidate sourcing for recruiters. It searches LinkedIn for candidates matching job requirements and uses an LLM to score and rank them.

## MVP Scope

- **Single source**: LinkedIn only (via `harvestapi/linkedin-profile-search`)
- **Simple scoring**: LLM evaluates profiles and assigns 1-100 score
- **Language**: Python

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Talent Scout Actor                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. INPUT (Job Requirements)                                     │
│     ↓                                                            │
│  2. Actor.call("harvestapi/linkedin-profile-search")             │
│     ↓                                                            │
│  3. Get LinkedIn profiles from dataset                           │
│     ↓                                                            │
│  4. Send profiles to LLM for scoring                             │
│     ↓                                                            │
│  5. OUTPUT (Ranked candidates with scores)                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Input Schema

```json
{
  "jobTitle": "Senior Frontend Developer",
  "jobDescription": "Looking for an experienced frontend developer with React expertise...",
  "requiredSkills": ["React", "TypeScript", "CSS"],
  "niceToHave": ["Next.js", "Testing", "GraphQL"],
  "location": "Prague",
  "experienceYears": 3,
  "maxCandidates": 20
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `jobTitle` | string | Yes | - | Job title to search for |
| `jobDescription` | string | Yes | - | Full job description for LLM context |
| `requiredSkills` | array[string] | Yes | - | Must-have skills |
| `niceToHave` | array[string] | No | [] | Bonus skills |
| `location` | string | No | null | Geographic location filter |
| `experienceYears` | integer | No | null | Minimum years of experience |
| `maxCandidates` | integer | No | 20 | Maximum candidates to return |

---

## Output Schema

```json
{
  "candidates": [
    {
      "rank": 1,
      "score": 95,
      "name": "Jan Novák",
      "headline": "Senior Frontend Developer at TechCorp",
      "linkedinUrl": "https://linkedin.com/in/jan-novak",
      "location": "Prague, Czech Republic",
      "matchedSkills": ["React", "TypeScript", "Next.js"],
      "missingSkills": ["CSS"],
      "experience": [
        {
          "title": "Senior Frontend Developer",
          "company": "TechCorp",
          "duration": "2 years"
        }
      ],
      "summary": "Strong React/TypeScript background with 5 years experience. Has Next.js which is a bonus. Missing explicit CSS mention but likely has it.",
      "profileData": { /* raw LinkedIn profile data */ }
    }
  ],
  "metadata": {
    "totalFound": 45,
    "evaluated": 20,
    "searchQuery": "Senior Frontend Developer",
    "timestamp": "2026-01-17T12:00:00Z"
  }
}
```

---

## LinkedIn Search Actor Integration

**Actor**: `harvestapi/linkedin-profile-search`

**Input mapping**:
```python
linkedin_input = {
    "profileScraperMode": "Full",  # Get detailed profiles
    "searchQuery": input.jobTitle,
    "currentJobTitles": [input.jobTitle],  # Optional: exact title match
    "locations": [input.location] if input.location else None,
    "maxItems": input.maxCandidates * 2,  # Get extra for filtering
    "startPage": 1,
}
```

**Cost estimate**: 
- $0.10 per search page (25 results)
- $0.004 per full profile
- 20 candidates ≈ $0.10 + $0.08 = ~$0.18

---

## LLM Scoring

### Provider
- Primary: OpenAI GPT-4 (via API)
- API key: Environment variable `OPENAI_API_KEY`

### Scoring Prompt

```
You are a technical recruiter evaluating candidates for the following position:

**Job Title**: {jobTitle}
**Description**: {jobDescription}
**Required Skills**: {requiredSkills}
**Nice to Have**: {niceToHave}
**Location**: {location}
**Experience Required**: {experienceYears}+ years

Evaluate the following LinkedIn profile and provide:
1. Score (1-100): How well does this candidate match the requirements?
2. Matched Skills: Which required/nice-to-have skills does the candidate have?
3. Missing Skills: Which required skills are missing?
4. Summary: 2-3 sentence evaluation

Profile:
{profileData}

Respond in JSON format:
{
  "score": <number>,
  "matchedSkills": [<strings>],
  "missingSkills": [<strings>],
  "summary": "<string>"
}
```

### Scoring Guidelines
- **90-100**: Perfect match - all required skills, relevant experience, good location
- **70-89**: Strong match - most required skills, some nice-to-haves
- **50-69**: Partial match - some required skills, potential to grow
- **30-49**: Weak match - missing key skills but has related experience
- **1-29**: Poor match - doesn't meet basic requirements

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for LLM scoring |
| `APIFY_TOKEN` | Auto | Provided by Apify platform |

---

## Error Handling

1. **LinkedIn Actor fails**: Log error, return partial results or fail gracefully
2. **LLM API fails**: Retry 3 times with exponential backoff, then skip candidate
3. **No candidates found**: Return empty array with appropriate message
4. **Invalid input**: Validate early and fail with clear error message

---

## Future Enhancements (Post-MVP)

- [ ] Multi-source search (GitHub, Google, other platforms)
- [ ] Email extraction mode
- [ ] Candidate deduplication across sources
- [ ] Custom scoring criteria
- [ ] Batch processing for large searches
- [ ] Integration with ATS systems

---

## Technical Stack

- **Language**: Python 3.11+
- **Apify SDK**: `apify` (Python SDK)
- **LLM**: OpenAI Python SDK (`openai`)
- **Base image**: `apify/actor-python:3.11`

---

## Success Metrics

- Successfully retrieve and score 20 candidates in under 2 minutes
- LLM scoring provides meaningful differentiation between candidates
- Output is structured and ready for recruiter review
