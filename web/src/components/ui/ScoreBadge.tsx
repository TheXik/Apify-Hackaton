import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface ScoreBadgeProps {
    score: number;
    size?: number;
    strokeWidth?: number;
}

export function ScoreBadge({ score, size = 40, strokeWidth = 3 }: ScoreBadgeProps) {
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (score / 100) * circumference;

    let colorClass = "text-blue-600";
    // Match reference colors more closely
    if (score >= 90) colorClass = "text-blue-600";
    else if (score >= 80) colorClass = "text-blue-500";
    else if (score >= 70) colorClass = "text-indigo-500";
    else colorClass = "text-slate-400"; // Low score gray

    return (
        <div className="relative inline-flex items-center justify-center">
            <svg width={size} height={size} className="transform -rotate-90">
                {/* Background circle */}
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    stroke="currentColor"
                    strokeWidth={strokeWidth}
                    fill="transparent"
                    className="text-slate-100" // Lighter background ring
                />
                {/* Progress circle */}
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    stroke="currentColor"
                    strokeWidth={strokeWidth}
                    fill="transparent"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    strokeLinecap="round"
                    className={cn("transition-all duration-1000 ease-out", colorClass)}
                />
            </svg>
            <span className={cn("absolute text-sm font-bold tracking-tight text-slate-700", colorClass)}>
                {score}
            </span>
        </div>
    );
}
