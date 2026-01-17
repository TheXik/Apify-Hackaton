import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import { SearchRequest } from '@/types';

export async function POST(req: NextRequest) {
    try {
        const body: SearchRequest = await req.json();

        if (!body.jobTitle) {
            return NextResponse.json({ error: 'Job title is required' }, { status: 400 });
        }

        console.log('🚀 API: Starting search for', body.jobTitle);

        // Local execution strategy: Spawn Python script
        const scriptPath = path.resolve(process.cwd(), '../scripts/local_search.py');
        const pythonPath = '/Users/hodan/miniforge3/bin/python3'; // Verified path

        console.log('🚀 Spawning python:', pythonPath, scriptPath);

        const pythonProcess = spawn(pythonPath, [scriptPath]);

        let resultData = '';
        let errorData = '';

        // Write input JSON to stdin
        pythonProcess.stdin.write(JSON.stringify({
            jobTitle: body.jobTitle,
            location: body.location,
            requiredSkills: body.requiredSkills || [],
            jobDescription: body.jobDescription
        }));
        pythonProcess.stdin.end();

        pythonProcess.stdout.on('data', (data: Buffer) => {
            resultData += data.toString();
        });

        pythonProcess.stderr.on('data', (data: Buffer) => {
            errorData += data.toString();
            console.error('🐍 Python Error:', data.toString());
        });

        // Wrap in promise to await completion
        const exitCode = await new Promise((resolve) => {
            pythonProcess.on('close', (code: number) => resolve(code));
        });

        if (exitCode !== 0) {
            return NextResponse.json({ error: 'Search failed', details: errorData }, { status: 500 });
        }

        try {
            const parsedResult = JSON.parse(resultData);
            return NextResponse.json(parsedResult);
        } catch (e) {
            console.error('Failed to parse Python output:', resultData);
            return NextResponse.json({ error: 'Invalid response from scraper' }, { status: 500 });
        }

    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}
