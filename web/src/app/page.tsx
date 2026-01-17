'use client';

import React, { useState, useEffect } from 'react';
import { Search, MapPin, Code2, Loader2, Sparkles, Filter, Linkedin, Twitter, Github } from 'lucide-react';
import { CandidateTable } from '@/components/ui/CandidateTable';
import { CandidateModal } from '@/components/ui/CandidateModal';
import { Candidate, SearchResponse } from '@/types';

const FUN_FACTS = [
  "We're searching LinkedIn, GitHub, and Twitter simultaneously...",
  "Our AI analyzes skills, experience, and profile quality...",
  "Each candidate gets scored based on your requirements...",
  "We extract work history and languages from profiles...",
  "Top candidates are ranked by AI match score...",
];

export default function Home() {
  const [jobTitle, setJobTitle] = useState('');
  const [location, setLocation] = useState('Prague');
  const [skills, setSkills] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingSeconds, setLoadingSeconds] = useState(0);
  const [funFactIndex, setFunFactIndex] = useState(0);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);

  // Timer for loading duration
  useEffect(() => {
    if (!isLoading) {
      setLoadingSeconds(0);
      return;
    }
    const interval = setInterval(() => {
      setLoadingSeconds(prev => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [isLoading]);

  // Rotate fun facts every 8 seconds
  useEffect(() => {
    if (!isLoading) return;
    const interval = setInterval(() => {
      setFunFactIndex(prev => (prev + 1) % FUN_FACTS.length);
    }, 8000);
    return () => clearInterval(interval);
  }, [isLoading]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      const res = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jobTitle,
          location,
          requiredSkills: skills.split(',').map(s => s.trim()).filter(Boolean),
          jobDescription: `${jobTitle} in ${location}. Focusing on ${skills}`,
          maxCandidates: 10
        }),
      });

      if (!res.ok) throw new Error('Search failed');

      const data: SearchResponse = await res.json();
      setResults(data);
    } catch (err) {
      setError('Failed to fetch candidates. Ensure backend is running.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#FDFDFD] font-sans pb-20">
      {/* Navbar/Header */}
      <nav className="border-b border-gray-100 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 flex items-center justify-center">
              <img src="/logo.png" className="w-8 h-8" />
            </div>
            <span className="font-bold text-gray-900 tracking-tight text-lg">Talent Scout AI</span>
          </div>
          <div>
            <div className="w-8 h-8 rounded-full bg-gray-100 border border-gray-200"></div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 pt-12">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight sm:text-5xl mb-4">
            Find your next <span className="text-blue-600">10x Developer</span>
          </h1>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            Stop sifting through resumes. Our AI agent actively scouts LinkedIn, GitHub, and Twitter to find and rank the best talent for you.
          </p>
        </div>

        {/* Floating Search Bar */}
        <div className="max-w-6xl mx-auto bg-white rounded-2xl shadow-xl shadow-gray-200/50 border border-gray-100 p-2 mb-12 transform transition-all duration-300">
          <form onSubmit={handleSearch} className="flex flex-col md:flex-row divide-y md:divide-y-0 md:divide-x divide-gray-100">

            <div className="flex-1 flex items-center px-4 py-3">
              <Search className="w-5 h-5 text-gray-400 mr-3" />
              <input
                type="text"
                placeholder="Role (e.g. Frontend Dev)"
                className="w-full bg-transparent outline-none text-gray-900 placeholder-gray-400 font-medium"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
              />
            </div>

            <div className="flex-1 flex items-center px-4 py-3">
              <MapPin className="w-5 h-5 text-gray-400 mr-3" />
              <input
                type="text"
                placeholder="Location"
                className="w-full bg-transparent outline-none text-gray-900 placeholder-gray-400 font-medium"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </div>

            <div className="flex-1 flex items-center px-4 py-3">
              <Code2 className="w-5 h-5 text-gray-400 mr-3" />
              <input
                type="text"
                placeholder="Skills"
                className="w-full bg-transparent outline-none text-gray-900 placeholder-gray-400 font-medium"
                value={skills}
                onChange={(e) => setSkills(e.target.value)}
              />
            </div>

            <div className="p-1.5 md:pl-2">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full md:w-auto h-full px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-all shadow-md shadow-blue-600/20 flex items-center justify-center gap-2 whitespace-nowrap disabled:opacity-70"
              >
                {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Scout Talent'}
              </button>
            </div>

          </form>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="max-w-2xl mx-auto mb-12 animate-in fade-in duration-500">
            <div className="bg-white rounded-2xl border border-gray-100 shadow-lg p-8 text-center">
              <div className="flex justify-center gap-4 mb-6">
                <div className="w-12 h-12 rounded-full bg-[#0A66C2]/10 flex items-center justify-center">
                  <Linkedin className="w-6 h-6 text-[#0A66C2] animate-pulse" />
                </div>
                <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center">
                  <Github className="w-6 h-6 text-gray-900 animate-pulse" style={{ animationDelay: '0.3s' }} />
                </div>
                <div className="w-12 h-12 rounded-full bg-[#1DA1F2]/10 flex items-center justify-center">
                  <Twitter className="w-6 h-6 text-[#1DA1F2] animate-pulse" style={{ animationDelay: '0.6s' }} />
                </div>
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">
                Scouting talent across platforms...
              </h3>
              <p className="text-sm text-gray-500 mb-4 transition-opacity duration-500">
                {FUN_FACTS[funFactIndex]}
              </p>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-50 rounded-full">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                <span className="text-sm font-medium text-gray-600">
                  {loadingSeconds}s elapsed
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="max-w-5xl mx-auto mb-8 p-4 bg-red-50 text-red-600 rounded-lg border border-red-100 text-center font-medium">
            {error}
          </div>
        )}

        {/* Results */}
        {results && (
          <div className="max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-8 duration-700">
            <div className="flex items-center justify-between mb-6 px-2">
              <h2 className="text-xl font-bold text-gray-900">
                Top Candidates
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({results.totalFound || results.candidates.length} found)
                </span>
              </h2>
              <button className="text-sm font-medium text-gray-500 hover:text-gray-900 flex items-center gap-1">
                <Filter className="w-4 h-4" /> Filter
              </button>
            </div>

            <CandidateTable
              candidates={results.candidates}
              onSelectCandidate={setSelectedCandidate}
            />
          </div>
        )}

        <CandidateModal
          candidate={selectedCandidate}
          isOpen={!!selectedCandidate}
          onClose={() => setSelectedCandidate(null)}
        />
      </div>
    </main>
  );
}
