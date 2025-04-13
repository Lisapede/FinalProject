// server_new.js
// Run with: node server_new.js
import fs from "fs";
import path from "path";
import csv from "csv-parser";
import dotenv from "dotenv";
import { OpenAI } from "openai";
import { createObjectCsvWriter } from "csv-writer";
import cliProgress from "cli-progress";

dotenv.config();
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const inputPath = "/workspaces/codespaces-blank/Restaurant Data/wine_menu_extracted.csv";
const outputPath = "./export.csv";
const delay = (ms) => new Promise((res) => setTimeout(res, ms));

// 🧉 Cocktail filter
const isLikelyCocktail = (text) => {
  const keywords = [
    "vodka", "gin", "whiskey", "bourbon", "rum", "mezcal", "rye",
    "scotch", "brandy", "liqueur", "tequila", "margarita", "mojito",
    "martini", "bloody mary", "pina colada", "mixed drink", "cocktail", "coffee", "spritz", "tea"
  ];

  const lower = text.toLowerCase();

  // Match only if a keyword is found as a full word
  return keywords.some((word) => new RegExp(`\\b${word}\\b`).test(lower));
};

// 🍷 Extract price and vintage
const extractPricesFromWineName = (rawName) => {
  let wineName = rawName;
  let price = null;
  let price_glass = null;
  let price_bottle = null;
  let typical_vintage = null;

  const slashMatch = wineName.match(/(?:\$?\d{1,3})\s*\/\s*(?:\$?\d{1,4})/);
  if (slashMatch) {
    const [glass, bottle] = slashMatch[0].split("/").map((s) => s.replace(/\D/g, ""));
    price_glass = `$${glass}`;
    price_bottle = `$${bottle}`;
    wineName = wineName.replace(slashMatch[0], "").trim();
  }

  const glassMatch = wineName.match(/glass\s*\$?(\d{1,4})|\$?(\d{1,4})\s*glass/i);
  if (glassMatch) {
    price_glass = `$${glassMatch[1] || glassMatch[2]}`;
    wineName = wineName.replace(glassMatch[0], "").trim();
  }

  const bottleMatch = wineName.match(/bottle\s*\$?(\d{1,4})|\$?(\d{1,4})\s*bottle/i);
  if (bottleMatch) {
    price_bottle = `$${bottleMatch[1] || bottleMatch[2]}`;
    wineName = wineName.replace(bottleMatch[0], "").trim();
  }

  const endPriceMatch = wineName.match(/\$?(\d{1,4})(\.\d{2})?$/);
  if (endPriceMatch && !price_glass && !price_bottle) {
    price = `$${endPriceMatch[1]}${endPriceMatch[2] || ""}`;
    wineName = wineName.replace(endPriceMatch[0], "").trim();
  }

  // Match year only if it is not preceded by a $
  const yearRegex = /\b(19[0-9]{2}|20[0-2][0-9]|2025)\b/;
  const match = wineName.match(yearRegex);
  if (match) {
    const index = match.index;
    const charBefore = index > 0 ? wineName[index - 1] : null;
    if (charBefore !== "$") {
      typical_vintage = match[0];
      wineName = wineName.replace(match[0], "").trim();
    }
  }

  return {
    wineName,
    price,
    price_glass,
    price_bottle,
    typical_vintage,
  };
};

// 🚀 Main run
const run = async () => {
  const rows = [];

  fs.createReadStream(inputPath)
    .pipe(csv())
    .on("data", (row) => {
      const name = row.wine_name?.trim() || "";
      if (name && !isLikelyCocktail(name)) {
        rows.push(row);
      } else {
        console.log(`🧉 Skipped likely cocktail: "${name}"`);
      }
    })
    .on("end", async () => {
      const results = [];

      const progressBar = new cliProgress.SingleBar({
        format: 'Progress | {bar} | {percentage}% | {value}/{total} wines',
        barCompleteChar: '█',
        barIncompleteChar: '-',
        hideCursor: true,
      }, cliProgress.Presets.shades_classic);

      progressBar.start(rows.length, 0);

      for (const row of rows) {
        const { wine_name: rawWineName, city, restaurant } = row;
        const {
          wineName,
          price,
          price_glass,
          price_bottle,
          typical_vintage,
        } = extractPricesFromWineName(rawWineName);

        const prompt = `
You are a master sommelier and wine‑data researcher.
Return ONLY a valid, minified JSON object matching this exact schema:
{
  "brand": string|null,
  "producer": string|null,
  "wine_name": string|null,
  "typical_vintage": string|null,
  "region": string|null,
  "state": string|null,
  "country": string|null,
  "wine_type": string|null,
  "varietal": string|null,
  "body": string|null,
  "ABV": string|null,
  "taste_profile": string|null,
  "sweetness": string|null,
  "tannin": string|null,
  "acidity": string|null,
  "price_glass": string|null,
  "price_bottle": string|null,
  "sources": string[]
}
• Do not include any extra keys or comments.
• Use null for unknown values.

Wine to research:
"${wineName}"
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
            menu_wine_name: rawWineName,
            wine_name: gptData.wine_name ?? wineName,
            typical_vintage: typical_vintage ?? gptData.typical_vintage ?? null,
            brand: gptData.brand ?? null,
            producer: gptData.producer ?? null,
            region: gptData.region ?? null,
            state: gptData.state ?? null,
            country: gptData.country ?? null,
            wine_type: gptData.wine_type ?? null,
            varietal: gptData.varietal ?? null,
            body: gptData.body ?? null,
            ABV: gptData.ABV ?? null,
            taste_profile: gptData.taste_profile ?? null,
            sweetness: gptData.sweetness ?? null,
            tannin: gptData.tannin ?? null,
            acidity: gptData.acidity ?? null,
            price: price ?? gptData.price ?? null,
            price_glass: price_glass ?? gptData.price_glass ?? null,
            price_bottle: price_bottle ?? gptData.price_bottle ?? null,
            sources: (gptData.sources ?? []).join("; "),
          });

          await delay(500);
        } catch (err) {
          console.error("❌ Error:", rawWineName, err.message);
        }

        progressBar.increment();
      }

      progressBar.stop();

      const csvWriter = createObjectCsvWriter({
        path: outputPath,
        header: [
          { id: "city", title: "City" },
          { id: "restaurant", title: "Restaurant" },
          { id: "menu_wine_name", title: "Menu Wine Name" },
          { id: "brand", title: "Brand" },
          { id: "wine_name", title: "Wine Name" },
          { id: "typical_vintage", title: "Vintage" },
          { id: "region", title: "Region" },
          { id: "state", title: "State" },
          { id: "country", title: "Country" },
          { id: "wine_type", title: "Wine Type" },
          { id: "varietal", title: "Varietal" },
          { id: "body", title: "Body" },
          { id: "ABV", title: "ABV (Alcohol by Volume)" },
          { id: "taste_profile", title: "Taste Profile" },
          { id: "sweetness", title: "Sweetness Level" },
          { id: "tannin", title: "Tannin Level" },
          { id: "acidity", title: "Acidity" },
          { id: "price", title: "Price" },
          { id: "price_glass", title: "Price by Glass" },
          { id: "price_bottle", title: "Price by Bottle" },
          { id: "sources", title: "Sources" },
        ],
      });

      await csvWriter.writeRecords(results);
      console.log(`📄 CSV export complete → ${outputPath}`);
    });
};

run();
