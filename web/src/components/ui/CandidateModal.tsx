import React from 'react';
import { X, Linkedin, Github, Mail, Phone, FileText, Download, Play, Video } from 'lucide-react';
import { Candidate } from '@/types';
import { ScoreBadge } from './ScoreBadge';

interface CandidateModalProps {
    candidate: Candidate | null;
    isOpen: boolean;
    onClose: () => void;
}

export function CandidateModal({ candidate, isOpen, onClose }: CandidateModalProps) {
    if (!candidate || !isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />

            {/* Modal Content */}
            <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto animate-in zoom-in-95 duration-200">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors z-10"
                >
                    <X className="w-5 h-5" />
                </button>

                <div className="flex flex-col md:flex-row min-h-[600px]">
                    {/* Left Column: Profile Info */}
                    <div className="w-full md:w-3/5 p-8 md:pr-10">
                        {/* Header */}
                        <div className="flex items-start gap-5 mb-8">
                            <div className="w-20 h-20 rounded-2xl overflow-hidden bg-gray-100 shadow-inner flex-shrink-0">
                                {candidate.avatar ? (
                                    <img src={candidate.avatar} alt={candidate.name} className="w-full h-full object-cover" />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center text-2xl font-bold text-gray-400">
                                        {candidate.name.charAt(0)}
                                    </div>
                                )}
                            </div>
                            <div className="pt-1">
                                <h2 className="text-2xl font-bold text-gray-900 tracking-tight">{candidate.name}</h2>
                                <p className="text-gray-500 font-medium mb-2">{candidate.bio || "Candidate"}</p>
                                <div className="flex items-center gap-3 text-gray-400">
                                    {candidate.profileUrls.linkedin && (
                                        <a href={candidate.profileUrls.linkedin} target="_blank" className="hover:text-[#0A66C2] transition-colors"><Linkedin className="w-5 h-5" /></a>
                                    )}
                                    {candidate.profileUrls.github && (
                                        <a href={candidate.profileUrls.github} target="_blank" className="hover:text-gray-900 transition-colors"><Github className="w-5 h-5" /></a>
                                    )}
                                    {candidate.email && (
                                        <a href={`mailto:${candidate.email}`} className="hover:text-gray-900 transition-colors"><Mail className="w-5 h-5" /></a>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* AI Summary */}
                        <div className="mb-8">
                            <p className="text-gray-600 leading-relaxed">
                                {candidate.summary || "No AI summary available. This candidate was found via search but hasn't been fully analyzed by the AI ranker yet."}
                            </p>
                        </div>

                        {/* Skills */}
                        <div className="mb-8">
                            <h3 className="text-lg font-bold text-gray-900 mb-3">Skills:</h3>
                            <div className="flex flex-wrap gap-2">
                                {/* Combine matched and general skills, simplify display */}
                                {candidate.matchedSkills?.map(s => (
                                    <span key={s} className="px-3 py-1 bg-green-50 text-green-700 text-sm font-medium rounded-full border border-green-100">
                                        {s}
                                    </span>
                                ))}
                                {(candidate.skills || []).slice(0, 10).filter(s => !candidate.matchedSkills?.includes(s)).map(s => (
                                    <span key={s} className="px-3 py-1 bg-gray-50 text-gray-600 text-sm font-medium rounded-full border border-gray-100">
                                        {s}
                                    </span>
                                ))}
                            </div>
                        </div>

                    </div>

                    {/* Right Column: Experience & Meta */}
                    <div className="w-full md:w-2/5 p-8 bg-gray-50/50 border-t md:border-t-0 md:border-l border-gray-100 flex flex-col">

                        {/* Score Card */}
                        <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm mb-8 flex flex-col items-center justify-center text-center">
                            <ScoreBadge score={candidate.score || 0} size={64} strokeWidth={5} />
                            <div className="mt-2 text-sm font-medium text-gray-500">AI Match Score</div>
                            <div className="mt-0.5 text-xs text-blue-500 font-semibold uppercase tracking-wider">Top Candidate</div>
                        </div>

                        {/* Work Experience */}
                        <div className="flex-1">
                            <h3 className="text-lg font-bold text-gray-900 mb-4">Work experience:</h3>
                            <div className="space-y-6">
                                {candidate.workExperience?.map((work, i) => (
                                    <div key={i} className="relative pl-4 border-l-2 border-gray-200">
                                        <div className="absolute -left-[5px] top-1.5 w-2.5 h-2.5 rounded-full bg-gray-300 ring-4 ring-white"></div>
                                        <div className="text-sm font-semibold text-gray-900 underline decoration-gray-300 underline-offset-2 hover:decoration-blue-400 transition-all cursor-pointer">
                                            {work.start} - {work.end}
                                        </div>
                                        <div className="text-sm font-medium text-gray-700 mt-1">{work.role}</div>
                                        <div className="text-sm text-gray-500">{work.company}</div>
                                    </div>
                                )) || (
                                        <p className="text-gray-400 text-sm italic">No specific work history extracted.</p>
                                    )}
                            </div>
                        </div>

                        {/* Action Bar */}
                        <div className="mt-8 pt-6 border-t border-gray-200">
                            <button className="w-full py-3.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-lg shadow-blue-600/20 transition-all transform hover:scale-[1.02] active:scale-[0.98]">
                                Invite to interview
                            </button>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
}
