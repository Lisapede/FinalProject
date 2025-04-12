// Open folder: cd 00_chat_wine_info
// node server_new.js
// open new terminal
// curl -X POST http://localhost:3000/batch-wine-info

import fs from "fs";
import path from "path";
import csv from "csv-parser";
import dotenv from "dotenv";
import { OpenAI } from "openai";
import { createObjectCsvWriter } from "csv-writer";

dotenv.config();

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const inputPath = "/workspaces/codespaces-blank/data/wine_menu_extracted.csv";
const outputPath = "./export.csv";
const delay = (ms) => new Promise((res) => setTimeout(res, ms));

const run = async () => {
  const rows = [];

  fs.createReadStream(inputPath)
    .pipe(csv())
    .on("data", (row) => {
      if (row.wine_name?.trim()) {
        rows.push(row);
      }
    })
    .on("end", async () => {
      const results = [];

      for (const row of rows) {
        const { wine_name, city, restaurant } = row;
        console.log(`Processing: "${wine_name}"`);

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
"${wine_name}"
`.trim();

        try {
          const chat = await openai.chat.completions.create({
            model: "gpt-4",
            temperature: 0.2,
            messages: [{ role: "user", content: prompt }],
          });

          const match = chat.choices[0].message.content.match(/\{[\s\S]*\}/);
          if (!match) throw new Error("No JSON object returned");

          const gptData = JSON.parse(match[0]);

          results.push({
            city,
            restaurant,
            wine_name,
            ...gptData,
            sources: (gptData.sources ?? []).join("; "),
          });

          console.log("✅ Enriched:", wine_name);
          await delay(500); // rate limiting
        } catch (err) {
          console.error("❌ Error:", wine_name, err.message);
          results.push({
            city,
            restaurant,
            wine_name,
            region: null,
            state: null,
            country: null,
            wine_type: null,
            body: null,
            brand: null,
            producer: null,
            varietal: null,
            taste_profile: null,
            typical_vintage: null,
            price: null,
            sources: null,
          });
        }
      }

      const csvWriter = createObjectCsvWriter({
        path: outputPath,
        header: [
          { id: "city", title: "City" },
          { id: "restaurant", title: "Restaurant" },
          { id: "wine_name", title: "Menu Wine Name" },
          { id: "region", title: "Region" },
          { id: "state", title: "State" },
          { id: "country", title: "Country" },
          { id: "wine_type", title: "Wine Type" },
          { id: "body", title: "Body" },
          { id: "brand", title: "Brand" },
          { id: "producer", title: "Producer" },
          { id: "varietal", title: "Varietal" },
          { id: "taste_profile", title: "Taste Profile" },
          { id: "typical_vintage", title: "Typical Vintage" },
          { id: "price", title: "Price" },
          { id: "sources", title: "Sources" },
        ],
      });

      await csvWriter.writeRecords(results);
      console.log(`📄 CSV export complete → ${outputPath}`);
    });
};

run();
