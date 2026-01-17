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
- **TypeScript/JavaScript** – Hlavní jazyk

## 📄 Licence

MIT

---

*Vytvořeno na Apify Hackathonu 2026* 🚀