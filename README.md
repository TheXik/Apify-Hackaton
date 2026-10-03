# 🎯 Talent Scout: AI-Powered Candidate Finder

> **Apify Actor** that automatically finds and ranks the best candidates for a job opening.

## 📋 About

Talent Scout helps recruiters quickly find the strongest candidates for an open position. It combines web scraping across several platforms with LLM-based candidate evaluation.

### How it works

1. **📝 Define the role:** the recruiter fills in the job description and the required skills, experience and other criteria.
2. **🔍 Automated search:** the Actor searches several sources:
   - Google
   - LinkedIn
   - GitHub
   - Other social networks and professional platforms
3. **🤖 AI evaluation:** an LLM scores every candidate it found and ranks them from best to worst.
4. **📊 Output:** structured JSON with the ranked candidates.

## 🚀 Usage

### Input

```json
{
  "jobTitle": "Senior Frontend Developer",
  "jobDescription": "We are looking for an experienced frontend developer...",
  "requiredSkills": ["React", "TypeScript", "CSS"],
  "niceToHave": ["Next.js", "Testing"],
  "location": "Prague",
  "experienceYears": 3
}
```

### Output

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

## ⚙️ Setup

### Environment variables

```env
APIFY_TOKEN=your_apify_token_here
```

## 🛠️ Tech stack

- **Apify SDK:** web scraping and orchestration
- **LLM:** candidate evaluation and ranking
- **Python:** main language

## 📄 License

MIT

---

*Built at the Apify Hackathon 2026* 🚀

<details>
<summary>🇨🇿 Česká verze</summary>

# 🎯 Talent Scout - AI Powered Candidate Finder

> **Apify Actor** pro automatizované vyhledávání a hodnocení ideálních kandidátů na pracovní pozice.

## 📋 O projektu

Talent Scout je nástroj, který pomáhá recruiterům rychle najít ty nejlepší kandidáty na otevřené pozice. Kombinuje web scraping z více platforem s AI hodnocením kandidátů.

### Jak to funguje

1. **📝 Zadání požadavků** – Recruiter vyplní job description a specifikuje požadované dovednosti, zkušenosti a další kritéria
2. **🔍 Automatické vyhledávání** – Actor prohledává více zdrojů:
   - Google
   - LinkedIn
   - GitHub
   - Další sociální sítě a profesní platformy
3. **🤖 AI Evaluace** – Nalezení kandidáti jsou vyhodnoceni pomocí LLM, které je ohodnotí a seřadí od nejlepšího po nejhoršího
4. **📊 Výstup** – Strukturovaný JSON se seřazenými kandidáty

## 🚀 Použití

### Input

```json
{
  "jobTitle": "Senior Frontend Developer",
  "jobDescription": "Hledáme zkušeného frontend developera...",
  "requiredSkills": ["React", "TypeScript", "CSS"],
  "niceToHave": ["Next.js", "Testing"],
  "location": "Praha",
  "experienceYears": 3
}
```

### Output

```json
{
  "candidates": [
    {
      "name": "Jan Novák",
      "score": 95,
      "matchedSkills": ["React", "TypeScript", "Next.js"],
      "sources": ["LinkedIn", "GitHub"],
      "profileUrls": {...},
      "summary": "Senior developer s 5 lety zkušeností..."
    }
  ]
}
```

## ⚙️ Setup

### Environment Variables

```env
APIFY_TOKEN=your_apify_token_here
```

## 🛠️ Tech Stack

- **Apify SDK** – Web scraping a orchestrace
- **LLM** – Evaluace a ranking kandidátů
- **Python** – Hlavní jazyk

## 📄 Licence

MIT

---

*Vytvořeno na Apify Hackathonu 2026* 🚀

</details>
