export interface Candidate {
    name: string;
    username?: string;
    bio?: string;
    avatar?: string;
    location?: string;
    company?: string;
    email?: string;
    blog?: string;
    source: 'linkedin' | 'twitter' | 'github' | 'multi';
    profileUrls: {
        linkedin?: string;
        twitter?: string;
        github?: string;
        tweet?: string;
        [key: string]: string | undefined;
    };
    skills: string[];
    engagement?: {
        likes?: number;
        retweets?: number;
        replies?: number;
    };
    stats?: {
        followers?: number;
        following?: number;
        contributions?: number;
    };
    repositories?: Array<{
        name: string;
        description: string;
        language: string;
        stars: number;
        url: string;
    }>;
    // Ranking fields
    score?: number;
    semantic_score?: number;
    matchedSkills?: string[];
    missingSkills?: string[];
    strengths?: string[];
    concerns?: string[];
    summary?: string;
    workExperience?: Array<{
        start: string;
        end: string;
        role: string;
        company: string;
    }>;
    languages?: string[];
}

export interface SearchResponse {
    jobTitle: string;
    totalFound?: number;
    ranked?: boolean;
    sources?: string[];
    candidates: Candidate[];
    metadata: {
        searchQuery: string;
        location: string;
        sources: string[];
        timestamp: string;
    };
}

export interface SearchRequest {
    jobTitle: string;
    jobDescription?: string;
    location?: string;
    requiredSkills: string[];
    maxCandidates?: number;
    enableRanking?: boolean;
}
