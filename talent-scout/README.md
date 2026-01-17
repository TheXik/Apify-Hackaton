# Talent Scout - AI Powered Candidate Finder

Talent Scout is an intelligent Apify Actor designed to help recruiters and hiring managers find the best developer talent across multiple platforms. It combines automated web scraping with AI-powered evaluation to deliver a ranked list of relevant candidates.

## Features

-   **Multi-Platform Search**: Scrapes candidate profiles from sources like LinkedIn, GitHub, and Twitter/X (via Google Search).
-   **AI Ranking**: Uses an LLM (requires API key) to evaluate and rank candidates based on your specific job description.
-   **Skill Matching**: Automatically identifies and highlights matched skills from your required and nice-to-have lists.
-   **Structured Output**: Returns a clean, structured JSON dataset including candidate names, profiles, scores, and summaries.

## Input Parameters

The actor accepts the following input parameters in JSON format:

| Field | Type | Description | Default |
|---|---|---|---|
| `jobTitle` | String | **Required**. The job title or search query (e.g., "Senior Frontend Developer"). | `Frontend Developer` |
| `jobDescription` | String | Detailed description of the job. **Required for AI ranking.** | - |
| `requiredSkills` | Array | List of must-have skills (e.g., `["React", "TypeScript"]`). | `[]` |
| `niceToHave` | Array | List of bonus skills. | - |
| `location` | String | Geographic location to filter candidates (e.g., "Prague"). | `null` |
| `maxCandidates` | Integer | Maximum number of candidates to process. | `20` |
| `sources` | Array | List of platforms to search. Supported: `linkedin`, `twitter`, `github`. | `["linkedin", "twitter"]` |
| `enableRanking` | Boolean | Enable AI evaluation of candidates. | `true` |
| `topK` | Integer | Number of top-ranked candidates to return in the final output. | `10` |
| `experienceYears` | Integer | Minimum years of experience required. | `0` |

### Input Example

```json
{
    "jobTitle": "Senior Python Backend Engineer",
    "jobDescription": "We are looking for an expert in Python and Django with experience in high-scale systems...",
    "requiredSkills": ["Python", "Django", "PostgreSQL"],
    "niceToHave": ["AWS", "Kubernetes"],
    "location": "Berlin",
    "sources": ["linkedin", "github"],
    "enableRanking": true,
    "maxCandidates": 50,
    "topK": 10
}
```

## Output

The actor stores results in the default Apify Dataset. Each item represents a ranked candidate:

```json
{
    "name": "Jane Doe",
    "score": 95,
    "matchedSkills": ["Python", "Django", "AWS"],
    "sources": ["https://linkedin.com/in/janedoe"],
    "profileUrls": {
        "linkedin": "https://linkedin.com/in/janedoe",
        "github": "https://github.com/janedoe"
    },
    "summary": "Senior engineer with 7 years of experience in Python...",
    "rank": 1
}
```

## Usage

You can can run this actor programmatically using the Apify API or Client:

```javascript
/* Example using Apify Client for JavaScript */
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: 'YOUR_API_TOKEN' });

const input = {
    jobTitle: 'DevOps Engineer',
    // ... other parameters
};

const run = await client.actor('your-username/talent-scout').call(input);

console.log('Results installed in dataset:', run.defaultDatasetId);
```
