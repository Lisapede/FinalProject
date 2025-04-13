// server.js

import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { OpenAI } from "openai";
import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";

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

    const prompt = `
You are a wine researcher. Return up to 3 closely matching wine profiles in this exact format:

[
  {
    "region": string|null,
    "state": string|null,
    "country": string|null,
    "wine_name": string|null,
    "body": string|null,
    "brand": string|null,
    "producer": string|null,
    "varietal": string|null,
    "taste_profile": string|null,
    "typical_vintage": string|null,
    "price": string|null,
    "sources": string[]
  }
]

• Output ONLY valid JSON.
• Use null for unknown fields.
• Choose different vintages or sub-labels if applicable.
• Only include wines that can be matched to restaurant listings by wine_name and producer.

Wine to research:
Producer: ${producer}
Wine / Label: ${wineName}
${vintage ? `Vintage: ${vintage}` : ""}
    `.trim();

    const response = await openai.chat.completions.create({
      model: "gpt-4",
      temperature: 0.2,
      messages: [{ role: "user", content: prompt }],
    });

    const raw = response.choices[0]?.message?.content;
    if (!raw) throw new Error("No response content from OpenAI");

    console.log("🧠 GPT raw response:\n", raw);

    const match = raw.match(/\[[\s\S]*\]/);
    if (!match) throw new Error("No valid JSON array found in GPT response");

    const wineInfoArray = JSON.parse(match[0]);
    res.json(wineInfoArray);

  } catch (error) {
    console.error("❌ Error in /wine-info:", error);
    res.status(500).json({ error: error.message || "Internal Server Error" });
  }
});

/**
 * POST /find-matches
 * Matches selected wine to restaurant listings
 */
app.post("/find-matches", async (req, res) => {
  try {
    const wine = req.body;

    if (!wine || !wine.producer || !wine.wine_name) {
      return res.status(400).json({ error: "Producer and wine name are required for matching." });
    }

    const csvPath = path.resolve("/mnt/data/cleaned_export (5).csv");
    if (!fs.existsSync(csvPath)) {
      return res.status(404).json({ error: "CSV file not found." });
    }

    const content = fs.readFileSync(csvPath, "utf8");
    const records = parse(content, {
      columns: true,
      skip_empty_lines: true,
    });

    const matches = records.filter((row) => {
      const rowProducer = (row.producer || row.Producer || "").trim().toLowerCase();
      const rowName = (row.wine_name || row["Wine Name"] || row["Menu Wine Name"] || "").trim().toLowerCase();
      const matchProducer = wine.producer.trim().toLowerCase();
      const matchName = wine.wine_name.trim().toLowerCase();

      console.log("Comparing:", {
        rowProducer,
        matchProducer,
        rowName,
        matchName
      });

      return (
        rowProducer.includes(matchProducer) &&
        rowName.includes(matchName)
      );
    });

    res.json(matches);
  } catch (error) {
    console.error("❌ Error in /find-matches:", error);
    res.status(500).json({ error: error.message || "Failed to search matches." });
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
