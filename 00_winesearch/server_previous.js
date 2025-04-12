// server.js

// To run:
// 1. npm install express cors dotenv openai
// 2. Create a .env file with: OPENAI_API_KEY=sk-...
// 3. node server.js

import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { OpenAI } from "openai";

// Load environment variables
dotenv.config();

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const app = express();
const port = 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static("public")); // Serve index.html from /public

/**
 * POST /wine-info
 * Expects JSON: { producer: string, wineName: string, vintage: string (optional) }
 */
app.post("/wine-info", async (req, res) => {
  try {
    const { producer = "", wineName = "", vintage = "" } = req.body;

    if (!producer || !wineName) {
      return res.status(400).json({ error: "Producer and wine name are required." });
    }

    // Enhanced GPT prompt
    const prompt = `
You are a master sommelier and wine data researcher.

Return ONLY a valid, minified JSON object that matches this exact schema:
{
  "region": string|null,
  "state": string|null,
  "country": string|null,
  "wine_type": string|null,
  "body": string|null,
  "brand": string|null,
  "producer": string|null,
  "varietal": string|null,
  "taste_profile": string|null,
  "typical_vintage": string|null,
  "price": string|null,
  "sources": string[]
}

• Do not include any explanation or text outside the JSON object.
• Use null for any unknown value.
• If the wine is common or widely available, return typical or widely accepted information.
• Make your best effort to return accurate, clean, and complete data.

Wine to research:
Producer: ${producer}
Wine / Label: ${wineName}
${vintage ? `Vintage: ${vintage}` : ""}
    `.trim();

    // GPT call
    const response = await openai.chat.completions.create({
      model: "gpt-4",
      temperature: 0.2,
      messages: [{ role: "user", content: prompt }],
    });

    const raw = response.choices[0]?.message?.content;
    if (!raw) throw new Error("No response content from OpenAI");

    console.log("🧠 GPT raw response:\n", raw);

    // Extract JSON object from response
    const match = raw.match(/\{[\s\S]*\}/);
    if (!match) throw new Error("No valid JSON found in GPT response");

    const wineInfo = JSON.parse(match[0]);
    res.json(wineInfo);

  } catch (error) {
    console.error("❌ Error in /wine-info:", error);
    res.status(500).json({ error: error.message || "Internal Server Error" });
  }
});

/**
 * GET /ping — health check
 */
app.get("/ping", (req, res) => {
  res.send("pong");
});

// Start server
app.listen(port, () => {
  console.log(`🚀 Server running at http://localhost:${port}`);
});
