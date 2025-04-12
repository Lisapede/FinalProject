// Open folder: cd 00_chat_wine_info
// node server_new.js
// open new terminal
// curl -X POST http://localhost:3000/batch-wine-info


import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { OpenAI } from "openai";
import { saveWine, listWines } from "../00_chat_wine_info/db.js";
import fs from "fs";
import path from "path";
import { createObjectCsvWriter } from "csv-writer";

dotenv.config();

const app = express();
const port = process.env.PORT || 3000;
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

app.use(cors());
app.use(express.json());
app.use(express.static("public"));

/*──────────────── wine batch endpoint ────────────────*/
app.post("/batch-wine-info", async (req, res) => {
  try {
    // const filePath = path.resolve("./wine_names.txt");  ------ previous
    
    const filePath = path.resolve("/workspaces/codespaces-blank/data/wine_menu_extracted.csv");
    console.log("Reading file from:", filePath);

    const data = fs.readFileSync(filePath, "utf8");
    const lines = data
      .split("\n")
      .map((line) => line.trim())
      .filter(
        (line) =>
          line &&
          !/^sparkling$/i.test(line) &&
          !/^white\s*&\s*ros[eé]$/i.test(line)
      );

    const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const results = [];

    for (const line of lines) {
      console.log(`Processing: "${line}"`);

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
"${line}"
      `.trim();

      try {
        const chat = await openai.chat.completions.create({
          model: "gpt-4",
          temperature: 0.2,
          messages: [{ role: "user", content: prompt }],
        });

        const raw = chat.choices[0].message.content;
        const match = raw.match(/\{[\s\S]*\}/);
        if (!match) throw new Error("No JSON object returned");
        const wineInfo = JSON.parse(match[0]);

        saveWine({
          wine_name: wineInfo.wine_name ?? null,
          producer: wineInfo.producer ?? null,
          region: wineInfo.region ?? null,
          state: wineInfo.state ?? null,
          country: wineInfo.country ?? null,
          wine_type: wineInfo.wine_type ?? null,
          body: wineInfo.body ?? null,
          brand: wineInfo.brand ?? null,
          varietal: wineInfo.varietal ?? null,
          taste_profile: wineInfo.taste_profile ?? null,
          typical_vintage: wineInfo.typical_vintage ?? null,
          price: wineInfo.price ?? null,
          vintage_hint: wineInfo.typical_vintage ?? null,
          full_row: line,
          sources: JSON.stringify(wineInfo.sources ?? []),
        });

        results.push({ input: line, output: wineInfo });
        console.log("✅ Processed:", wineInfo);

        await delay(500); // avoid OpenAI rate limits
      } catch (err) {
        console.error("❌ Error processing:", line, err.message);
      }
    }

    // Save all results to export.csv
    const csvWriter = createObjectCsvWriter({
      path: "./export.csv",
      header: [
        { id: "full_row", title: "Original Line" },
        { id: "wine_name", title: "Wine Name" },
        { id: "producer", title: "Producer" },
        { id: "region", title: "Region" },
        { id: "state", title: "State" },
        { id: "country", title: "Country" },
        { id: "wine_type", title: "Wine Type" },
        { id: "body", title: "Body" },
        { id: "brand", title: "Brand" },
        { id: "varietal", title: "Varietal" },
        { id: "taste_profile", title: "Taste Profile" },
        { id: "typical_vintage", title: "Typical Vintage" },
        { id: "price", title: "Price" },
        { id: "sources", title: "Sources" },
      ],
    });

    await csvWriter.writeRecords(
      results.map(({ input, output }) => ({
        full_row: input,
        wine_name: output.wine_name ?? null,
        producer: output.producer ?? null,
        region: output.region ?? null,
        state: output.state ?? null,
        country: output.country ?? null,
        wine_type: output.wine_type ?? null,
        body: output.body ?? null,
        brand: output.brand ?? null,
        varietal: output.varietal ?? null,
        taste_profile: output.taste_profile ?? null,
        typical_vintage: output.typical_vintage ?? null,
        price: output.price ?? null,
        sources: (output.sources ?? []).join("; "),
      }))
    );

    console.log("📄 CSV export complete → export.csv");
    res.json({ message: "Batch processing complete", results });
  } catch (err) {
    console.error("Batch processing error:", err.message);
    res.status(500).json({ error: "Could not process batch wine information" });
  }
});

/*────────── view saved wines (optional) ─────*/
app.get("/wines", (req, res) => {
  res.json(listWines());
});

/*────────── test server ─────*/
app.get("/ping", (req, res) => res.send("pong"));

/*─────────────────────────────────────────────*/
app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
