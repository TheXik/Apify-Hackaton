import React from 'react';
import { Candidate } from '@/types';
import { ScoreBadge } from './ScoreBadge';
import { Github, Linkedin, Twitter } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface CandidateTableProps {
    candidates: Candidate[];
    onSelectCandidate: (candidate: Candidate) => void;
}

function getStatus(score: number) {
    if (score >= 90) return { label: 'Hire', bg: 'bg-[#F2F8E7]', text: 'text-[#587329]', border: 'border-[#E6F0D6]' }; // Pastel Yellow/Green mix
    if (score >= 80) return { label: 'Interview', bg: 'bg-[#F3F0FF]', text: 'text-[#6B46C1]', border: 'border-[#E9D8FD]' }; // Pastel Purple
    if (score >= 70) return { label: 'Good fit', bg: 'bg-[#E6FFFA]', text: 'text-[#2C7A7B]', border: 'border-[#B2F5EA]' }; // Pastel Teal
    return { label: 'Bad fit', bg: 'bg-[#FFF5F5]', text: 'text-[#C53030]', border: 'border-[#FED7D7]' }; // Pastel Red
}

export function CandidateTable({ candidates, onSelectCandidate }: CandidateTableProps) {
    return (
        <div className="w-full bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <table className="w-full text-left">
                <thead>
                    <tr className="border-b border-gray-100">
                        <th className="py-4 pl-6 pr-4 font-semibold text-sm text-gray-900 w-[240px]">Full name</th>
                        <th className="py-4 px-4 font-semibold text-sm text-gray-900">Email</th>
                        <th className="py-4 px-4 font-semibold text-sm text-gray-900">State</th>
                        <th className="py-4 px-4 font-semibold text-sm text-gray-900 text-center">Score</th>
                        <th className="py-4 px-4 font-semibold text-sm text-gray-900">Overview</th>
                        <th className="py-4 px-4 w-10"></th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                    {candidates.map((candidate, idx) => {
                        const status = getStatus(candidate.score || 0);

                        return (
                            <tr
                                key={idx}
                                className="group hover:bg-gray-50/50 transition-colors cursor-pointer"
                                onClick={() => onSelectCandidate(candidate)}
                            >
                                <td className="py-5 pl-6 pr-4 align-top">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-full bg-gray-100 flex-shrink-0 overflow-hidden border border-gray-200">
                                            {candidate.avatar ? (
                                                <img src={candidate.avatar} alt="" className="w-full h-full object-cover" />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center text-gray-400 font-medium">
                                                    {candidate.name.charAt(0)}
                                                </div>
                                            )}
                                        </div>
                                        <div>
                                            <div className="font-semibold text-gray-900">{candidate.name}</div>
                                            <div className="text-xs text-gray-500 mt-0.5 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                                                {candidate.profileUrls.linkedin && <Linkedin className="w-3 h-3 hover:text-blue-600 cursor-pointer" />}
                                                {candidate.profileUrls.github && <Github className="w-3 h-3 hover:text-gray-900 cursor-pointer" />}
                                            </div>
                                        </div>
                                    </div>
                                </td>

                                <td className="py-5 px-4 align-top">
                                    <div className="text-sm text-gray-600 mt-2.5">
                                        {candidate.email || <span className="text-gray-400 italic">Hidden</span>}
                                    </div>
                                </td>

                                <td className="py-5 px-4 align-top">
                                    <div className="mt-1.5">
                                        <span className={cn(
                                            "inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold border shadow-sm",
                                            status.bg,
                                            status.text,
                                            status.border
                                        )}>
                                            {status.label}
                                        </span>
                                    </div>
                                </td>

                                <td className="py-5 px-4 align-top">
                                    <div className="flex justify-center -mt-1">
                                        <ScoreBadge score={candidate.score || 0} size={42} strokeWidth={3} />
                                    </div>
                                </td>

                                <td className="py-5 px-4 align-top">
                                    <div className="mt-2.5">
                                        <button className="text-sm font-medium text-gray-500 underline decoration-gray-300 underline-offset-4 hover:text-gray-900 hover:decoration-gray-900 transition-all">
                                            See overview
                                        </button>
                                    </div>
                                </td>

                                <td className="py-5 px-4 align-top text-right">
                                    <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors mt-0.5">
                                        <span className="sr-only">More</span>
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <circle cx="12" cy="12" r="1" />
                                            <circle cx="19" cy="12" r="1" />
                                            <circle cx="5" cy="12" r="1" />
                                        </svg>
                                    </button>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}
