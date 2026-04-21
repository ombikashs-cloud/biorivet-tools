const express = require('express');
const path = require('path');
const dotenv = require('dotenv');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json({ limit: '50mb' }));
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

// API Endpoint for Document Difficulty Analysis (PDF/OCR/Text)
app.post('/api/analyze-document', async (req, res) => {
    try {
        const { fileData, mimeType, textContent } = req.body;
        
        const apiKey = process.env.GEMINI_API_KEY;
        if (!apiKey) {
            return res.status(500).json({ error: 'GEMINI_API_KEY is not configured on the server.' });
        }

        let promptText = `You are a NEET UG difficulty analysis expert. Your job is to classify each question in this exam paper into Easy, Medium, or Hard using the strict NEET-calibrated rubric below.

## NEET DIFFICULTY RUBRIC
### EASY
- Direct recall of a single definition, fact, or diagram label
- No calculation required, OR a one-step formula substitution
- Covered in NCERT text verbatim or as a highlighted box
- A student with 60% preparation can answer correctly

### MEDIUM
- Requires understanding of a concept, not just recall
- May involve 2-step calculation OR applying a formula with given values requiring unit conversion
- Assertion-Reason or Statement I/II where both statements require independent verification
- Match-the-list questions with 4 items requiring accurate recall of ALL 4 pairs
- A student with 75% preparation can answer correctly

### HARD
- Multi-step calculation (3 or more steps), OR derivation required, OR the formula itself must be recalled AND applied
- Requires integrating knowledge from 2 or more different concepts/chapters
- Tricky or misleading options where a common misconception leads to wrong answer
- Numerical problems requiring dimensional analysis, unit conversion AND formula application together
- Questions testing exceptions, atypical cases, or facts NOT directly in NCERT main text
- Organic reaction mechanism questions requiring arrow-pushing logic or predicting major product through multiple steps
- A student with 90%+ preparation is needed to reliably answer correctly

## SUBJECT-SPECIFIC GUIDANCE
### PHYSICS
- If substituting values into a standard formula (F=ma, V=IR): MEDIUM
- If deriving formula or combining 2+ formulas: HARD
- Purely conceptual multiple-select/statement on EM waves, optics, semiconductors: MEDIUM
- Logic gate / truth table: EASY
- Graph/diagram requiring extracting values AND calculating: HARD

### CHEMISTRY
- IUPAC naming, reaction type ID, structure ID: MEDIUM
- Stoichiometry with mole concept in one step: MEDIUM
- Electrochemistry calculation, Arrhenius, Kc/Kp: HARD
- Matching organic reactions to reagents (4-pair): MEDIUM
- Predicting major product of multi-step organic reaction: HARD
- Qualitative analysis group ID order: HARD
- Coordination chemistry: isomerism MEDIUM, magnetic behaviour HARD

### BIOLOGY (BOTANY + ZOOLOGY)
- Single-word or single-fact recall from NCERT: EASY
- 5 statements (A,B,C,D,E choose correct set): MEDIUM
- Match-the-list with scientists/researchers: MEDIUM
- Assertion-Reason in Biology: MEDIUM
- Specific chromosome numbers, trisomy, genetic disorder mechanisms: HARD
- Multi-concept questions linking 2 chapters: HARD
- Process sequencing (enzyme cycle, spermatogenesis): MEDIUM

## IMPORTANT RULES
1. Do NOT default to Easy for Biology recall unless single-word NCERT verbatim.
2. Do NOT classify any multi-step Physics calculation as Easy.
3. Assertion-Reason and Statement I/II are NEVER Easy — minimum Medium.
4. Match-the-list with 4 pairs is NEVER Easy — minimum Medium.
5. 5 options to evaluate (A,B,C,D,E) is NEVER Easy — minimum Medium.
6. Each question must be tagged to ONE primary chapter only (no slashes).
7. If testing an exception or "most appropriate" nuance, classify one level harder.

Extract all questions and infer their properties. For each question, output:
1. "qno": The question number.
2. "chapter": The ONE primary chapter name.
3. "difficulty": "Easy", "Medium", or "Hard".
4. "reason": A one-line reason (max 12 words) explaining why.
5. "marks": Default to 4.

Return the result STRICTLY as a JSON array of objects. Do not include markdown formatting or any other text.
Format: [{"qno": "1", "chapter": "Cell Biology", "difficulty": "Medium", "reason": "Requires verifying 5 statements independently", "marks": 4}]`;

        const requestBody = {
            contents: [{ parts: [{ text: promptText }] }],
            generationConfig: {
                temperature: 0.2,
                responseMimeType: "application/json"
            }
        };

        if (fileData && mimeType) {
            requestBody.contents[0].parts.push({
                inlineData: {
                    mimeType: mimeType,
                    data: fileData
                }
            });
        } else if (textContent) {
            requestBody.contents[0].parts.push({ text: `\n\nDocument Content:\n${textContent}` });
        } else {
            return res.status(400).json({ error: 'No file data or text content provided.' });
        }

        const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();

        if (data.error) {
            console.error("Gemini API Error:", data.error);
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
