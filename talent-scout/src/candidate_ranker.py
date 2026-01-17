"""
Candidate Ranker - Semantic Search + LLM Reranking

This module provides functionality to rank job candidates using:
1. Semantic search (OpenAI embeddings + cosine similarity)
2. LLM reranking (GPT-4o-mini for detailed evaluation)
"""

import json
import numpy as np
from openai import OpenAI


class CandidateRanker:
    """
    Ranks candidates for a job position using semantic search and LLM evaluation.
    
    Flow:
    1. Generate embeddings for job description and candidate profiles
    2. Use cosine similarity to find top K semantic matches
    3. Use LLM to evaluate and score each candidate in detail
    """
    
    def __init__(self, openai_api_key: str):
        """Initialize with OpenAI API key."""
        self.client = OpenAI(api_key=openai_api_key)
        self.embedding_model = "text-embedding-3-small"
        self.llm_model = "gpt-4o-mini"
    
    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding vector for text using OpenAI.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector (1536 dims)
        """
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in a single API call.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=texts
        )
        return [item.embedding for item in response.data]
    
    def cosine_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a = np.array(vec_a)
        b = np.array(vec_b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def candidate_to_text(self, candidate: dict) -> str:
        """Convert candidate profile to searchable text."""
        parts = []
        
        if candidate.get("name"):
            parts.append(f"Name: {candidate['name']}")
        if candidate.get("bio"):
            parts.append(f"Bio: {candidate['bio']}")
        if candidate.get("skills"):
            parts.append(f"Skills: {', '.join(candidate['skills'])}")
        if candidate.get("experience"):
            parts.append(f"Experience: {candidate['experience']}")
        if candidate.get("location"):
            parts.append(f"Location: {candidate['location']}")
            
        return "\n".join(parts)
    
    def job_to_text(self, job_input: dict) -> str:
        """Convert job input to searchable text."""
        parts = [
            f"Job Title: {job_input.get('jobTitle', '')}",
            f"Description: {job_input.get('jobDescription', '')}"
        ]
        
        if job_input.get("requiredSkills"):
            parts.append(f"Required Skills: {', '.join(job_input['requiredSkills'])}")
        if job_input.get("niceToHave"):
            parts.append(f"Nice to Have: {', '.join(job_input['niceToHave'])}")
        if job_input.get("location"):
            parts.append(f"Location: {job_input['location']}")
        if job_input.get("experienceYears"):
            parts.append(f"Minimum Experience: {job_input['experienceYears']} years")
            
        return "\n".join(parts)
    
    def semantic_search(
        self, 
        job_embedding: list[float], 
        candidates: list[dict], 
        top_k: int = 20
    ) -> list[dict]:
        """
        Find top K candidates by semantic similarity.
        
        Args:
            job_embedding: Embedding vector for job description
            candidates: List of candidate dicts with embeddings
            top_k: Number of top candidates to return
            
        Returns:
            Top K candidates sorted by similarity score
        """
        # Calculate similarity for each candidate
        scored = []
        for candidate in candidates:
            if "embedding" in candidate:
                similarity = self.cosine_similarity(job_embedding, candidate["embedding"])
                scored.append({
                    **candidate,
                    "semantic_score": similarity
                })
        
        # Sort by similarity (descending) and return top K
        scored.sort(key=lambda x: x["semantic_score"], reverse=True)
        return scored[:top_k]
    
    def llm_rerank(self, job_input: dict, candidates: list[dict]) -> list[dict]:
        """
        Use LLM to evaluate and score each candidate.
        
        Args:
            job_input: Job requirements dict
            candidates: List of candidate profiles
            
        Returns:
            Candidates with LLM evaluation scores and details
        """
        evaluated = []
        
        for candidate in candidates:
            prompt = self._build_evaluation_prompt(job_input, candidate)
            
            try:
                response = self.client.chat.completions.create(
                    model=self.llm_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert technical recruiter. Evaluate candidates objectively and return structured JSON."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )
                
                evaluation = json.loads(response.choices[0].message.content)
                evaluated.append({
                    **candidate,
                    "score": evaluation.get("score", 0),
                    "matchedSkills": evaluation.get("matchedSkills", []),
                    "missingSkills": evaluation.get("missingSkills", []),
                    "strengths": evaluation.get("strengths", []),
                    "concerns": evaluation.get("concerns", []),
                    "score": evaluation.get("score", 0),
                    "matchedSkills": evaluation.get("matchedSkills", []),
                    "missingSkills": evaluation.get("missingSkills", []),
                    "strengths": evaluation.get("strengths", []),
                    "concerns": evaluation.get("concerns", []),
                    "summary": evaluation.get("summary", ""),
                    "workExperience": evaluation.get("workExperience", []),
                    "languages": evaluation.get("languages", [])
                })
                
            except Exception as e:
                # If evaluation fails, use semantic score as fallback
                evaluated.append({
                    **candidate,
                    "score": int(candidate.get("semantic_score", 0) * 100),
                    "summary": f"Evaluation failed: {str(e)}"
                })
        
        # Sort by LLM score (descending)
        evaluated.sort(key=lambda x: x.get("score", 0), reverse=True)
        return evaluated
    
    def _build_evaluation_prompt(self, job_input: dict, candidate: dict) -> str:
        """Build the LLM evaluation prompt."""
        return f"""Evaluate this candidate for the job position.

JOB REQUIREMENTS:
- Title: {job_input.get('jobTitle', 'N/A')}
- Description: {job_input.get('jobDescription', 'N/A')}
- Required Skills: {', '.join(job_input.get('requiredSkills', []))}
- Nice to Have: {', '.join(job_input.get('niceToHave', []))}
- Location: {job_input.get('location', 'Any')}
- Min Experience: {job_input.get('experienceYears', 0)} years

CANDIDATE PROFILE:
- Name: {candidate.get('name', 'Unknown')}
- Bio: {candidate.get('bio', 'N/A')}
- Skills: {', '.join(candidate.get('skills', []))}
- Experience: {candidate.get('experience', 'N/A')}

Return a JSON object with:
{{
    "score": <0-100 integer>,
    "matchedSkills": ["skill1", "skill2"],
    "missingSkills": ["skill3"],
    "strengths": ["strength1", "strength2"],
    "concerns": ["concern1"],
    "summary": "2-3 sentence summary of fit",
    "workExperience": [{{ "start": "2020", "end": "2024", "role": "Title", "company": "Company" }}],
    "languages": ["English (Native)", "Czech (Fluent)"]
}}"""
    
    def rank_candidates(
        self, 
        job_input: dict, 
        candidates: list[dict],
        top_k: int = 10,
        skip_semantic: bool = False
    ) -> list[dict]:
        """
        Full ranking pipeline: embed -> semantic search -> LLM rerank.
        
        Args:
            job_input: Job requirements dict
            candidates: List of candidate profiles
            top_k: Number of candidates to return
            skip_semantic: If True, skip semantic search and evaluate all candidates
            
        Returns:
            Top K candidates ranked by LLM score
        """
        if not candidates:
            return []
        
        # Step 1: Generate embeddings
        job_text = self.job_to_text(job_input)
        job_embedding = self.embed_text(job_text)
        
        candidate_texts = [self.candidate_to_text(c) for c in candidates]
        candidate_embeddings = self.embed_batch(candidate_texts)
        
        # Add embeddings to candidates
        for i, candidate in enumerate(candidates):
            candidate["embedding"] = candidate_embeddings[i]
        
        # Step 2: Semantic search (unless skipped or few candidates)
        if skip_semantic or len(candidates) <= top_k * 2:
            semantic_top = candidates
        else:
            semantic_top = self.semantic_search(
                job_embedding, 
                candidates, 
                top_k=min(top_k * 2, len(candidates))  # Get 2x for LLM to rerank
            )
        
        # Step 3: LLM reranking
        ranked = self.llm_rerank(job_input, semantic_top)
        
        # Clean up embeddings from output (not needed in final result)
        for candidate in ranked:
            candidate.pop("embedding", None)
        
        return ranked[:top_k]
