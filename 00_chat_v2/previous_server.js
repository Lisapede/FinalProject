// wine‑chatbot/server.js
import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { OpenAI } from "openai";

dotenv.config();

const app   = express();
const port  = process.env.PORT || 3000;
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

app.use(cors());
app.use(express.json());
app.use(express.static("public"));

/*─────────────────────────────────────────────────────────────
  Structured wine‑info endpoint (updated)
─────────────────────────────────────────────────────────────*/
app.post("/wine-info", async (req, res) => {
  try {
    const { producer = "", wineName = "", vintage = "" } = req.body;

    // ⚙️  Desired schema — keep in sync with the prompt
    const schemaKeys = [
      "region", "state", "country", "wine_type", "body", "brand",
      "producer", "varietal", "taste_profile", "typical_vintage", "price", "sources"
    ];

    // 1️⃣  Craft the single prompt we’ll send to GPT
    const userPrompt = `
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
  "sources": string[]           // array of short source names, e.g. ["TotalWine","Wine‑Searcher"]
}
• Do not add extra keys or comments.
• Use null for unknown values.

Wine to research:
  • Producer: "${producer}"
  • Wine / Label: "${wineName}"
  ${vintage ? `• Vintage hint: "${vintage}"` : ""}
`.trim();

    // Helper that sends the prompt and parses JSON
    async function queryGPT() {
      const chat = await openai.chat.completions.create({
        model: "gpt-4o",
        temperature: 0.2,
        messages: [{ role: "user", content: userPrompt }]
      });

      // Grab the first {...} block so stray text doesn’t break JSON.parse
      const match = chat.choices[0].message.content.match(/\{[\s\S]*\}/);
      if (!match) throw new Error("No JSON object returned");
      return JSON.parse(match[0]);
    }

    // 2️⃣  First attempt
    let wineInfo = await queryGPT();

    // 3️⃣  (optional) quick retry if any top‑level field is still null
    const missing = schemaKeys.some(k => wineInfo[k] === null || wineInfo[k] === "");
    if (missing) {
      console.log("Retrying GPT call — some fields were null");
      wineInfo = await queryGPT();
    }

    res.json(wineInfo);

  } catch (err) {
    console.error("OpenAI /wine-info error:", err);
    res.status(500).json({ error: "Could not fetch wine information" });
  }
});

/*─────────────────────────────────────────────────────────────*/
app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
