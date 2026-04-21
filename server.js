const express = require('express');
const path = require('path');
const dotenv = require('dotenv');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// API Endpoint for Auto-Tagging
app.post('/api/auto-tag', async (req, res) => {
    try {
        const { questions } = req.body;
        if (!questions || !Array.isArray(questions)) {
            return res.status(400).json({ error: 'Invalid question data provided.' });
        }

        const apiKey = process.env.GEMINI_API_KEY;
        if (!apiKey) {
            return res.status(500).json({ error: 'GEMINI_API_KEY is not configured on the server.' });
        }

        // Format the questions into a text prompt
        let promptText = `Analyze the following NEET exam questions. For each question, infer the missing fields:
1. "chapter": The most relevant biology/physics/chemistry chapter name (e.g., Digestion, Kinematics, Cell Biology).
2. "subConcept": The specific sub-topic or concept within that chapter.
3. "errorType": Classify the question as either "Memory" (rote fact), "Conceptual" (understanding principles), or "Application" (calculating/applying formulas).
4. "ans": The correct answer option: A, B, C, or D. If unsure, take your best guess.

Return the result STRICTLY as a JSON array of objects. Do not include markdown formatting or any other text.
Format: [{"qno": "Q1", "chapter": "Cell Biology", "subConcept": "Cell Membrane", "errorType": "Memory", "ans": "B"}]

Questions to analyze:\n`;

        questions.forEach((q) => {
            promptText += `\n[Q No: ${q.qno}]\nText: ${q.text}\n`;
        });

        const requestBody = {
            contents: [{ parts: [{ text: promptText }] }],
            generationConfig: {
                temperature: 0.2, // Low temperature for more deterministic/factual output
                responseMimeType: "application/json"
            }
        };

        const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();

        if (data.error) {
            console.error("Gemini API Error:", data.error);
            // Return the specific error message from Google so the user knows what went wrong
            return res.status(500).json({ error: data.error.message || 'AI provider error.' });
        }

        const rawText = data.candidates[0].content.parts[0].text;
        
        try {
            const parsedResults = JSON.parse(rawText);
            return res.json({ results: parsedResults });
        } catch (parseError) {
            console.error("Failed to parse JSON from AI:", rawText);
            return res.status(500).json({ error: 'Failed to parse AI response.' });
        }

    } catch (error) {
        console.error("Server Error:", error);
        res.status(500).json({ error: 'Internal server error.' });
    }
});

// Fallback to index.html for SPA routing (if needed)
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
    console.log(`BioRivet Server is running on http://localhost:${PORT}`);
});
