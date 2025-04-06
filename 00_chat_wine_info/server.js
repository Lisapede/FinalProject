// wine‑chatbot/server.js
import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { OpenAI } from "openai";
import { saveWine, listWines } from "./db.js";   // ← comes from db.js

dotenv.config();

const app   = express();
const port  = process.env.PORT || 3000;
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

app.use(cors());
app.use(express.json());
app.use(express.static("public"));

/*──────────────── wine‑info endpoint ────────────────*/
app.post("/wine-info", async (req, res) => {
  try {
    const { producer = "", wineName = "", vintage = "" } = req.body;

    /* ---------- FULL prompt (no placeholder!) ---------- */
    const prompt = `
You are a master sommelier and wine‑data researcher.
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
• Do not add extra keys or comments.
• Use null for unknown values.

Wine to research:
  • Producer: "${producer}"
  • Wine / Label: "${wineName}"
  ${vintage ? `• Vintage hint: "${vintage}"` : ""}
`.trim();
    /* --------------------------------------------------- */

    const chat = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      temperature: 0.2,
      messages: [{ role: "user", content: prompt }]
    });

    const match = chat.choices[0].message.content.match(/\{[\s\S]*\}/);
    if (!match) throw new Error("No JSON object returned");
    const wineInfo = JSON.parse(match[0]);

    // store in SQLite
    saveWine({
      producer,
      wine_name: wineName,
      vintage_hint: vintage,
      ...wineInfo,
      sources: JSON.stringify(wineInfo.sources || [])
    });

    res.json(wineInfo);

  } catch (err) {
    console.error("OpenAI /wine-info error:", err);
    res.status(500).json({ error: "Could not fetch wine information" });
  }
});

/*────────── quick endpoint to view everything saved ─────*/
app.get("/wines", (req, res) => {
  res.json(listWines());
});

/*────────────────────────────────────────────────────────*/
app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
