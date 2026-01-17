Hey I want to build an Apify Actor called **Talent Scout - AI Powered Candidate Finder**.

## Project Overview

This Actor automatically searches for and evaluates ideal candidates for job positions. It combines web scraping from multiple platforms with AI-powered candidate evaluation.

### How it works

1. **Job Requirements Input** – Recruiter provides job description, required skills, experience, and other criteria
2. **Automated Search** – Actor scrapes multiple sources:
   - Google
   - LinkedIn
   - GitHub
   - Other social networks and professional platforms
3. **AI Evaluation** – Found candidates are evaluated using an LLM, which scores and ranks them from best to worst
4. **Output** – Structured JSON with ranked candidates

### Expected Input

```json
{
  "jobTitle": "Senior Frontend Developer",
  "jobDescription": "Looking for an experienced frontend developer...",
  "requiredSkills": ["React", "TypeScript", "CSS"],
  "niceToHave": ["Next.js", "Testing"],
  "location": "Prague",
  "experienceYears": 3
}
```

### Expected Output

```json
{
  "candidates": [
    {
      "name": "Jan Novák",
      "score": 95,
      "matchedSkills": ["React", "TypeScript", "Next.js"],
      "sources": ["LinkedIn", "GitHub"],
      "profileUrls": {...},
      "summary": "Senior developer with 5 years of experience..."
    }
  ]
}
```

---

## Before you start building the Actor itself:

- Analyze the HTML structure and network calls of target platforms (Google, LinkedIn, GitHub) using Chrome DevTools MCP or Cursor's native browser function
- Create a `PRD.md` (Product Requirements Document) file with detailed specs for this Actor to refer to during implementation
- Create a `CHANGELOG.md` file where you will document all progress/changes with each iteration
- Ask me any clarifying questions to fill in the gaps before we proceed with the implementation