// npm install csv-parser csv-writer

// 02_clean.js
import fs from "fs";
import dotenv from "dotenv";
import { createObjectCsvWriter } from "csv-writer";
import { OpenAI } from "openai";

dotenv.config();

const { parse } = await import("csv-parse");

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const inputPath = "./export.csv";
const outputPath = "./cleaned_export.csv";

const missingOrNull = (val) => val === null || val === "" || val.toLowerCase() === "null";

const cleanRowWithGPT = async (row) => {
  const fieldsToFill = Object.entries(row).filter(([key, val]) => missingOrNull(val));
  if (fieldsToFill.length === 0) return row;

  const prompt = `
You are a wine data expert. Fill in any missing fields in this wine data object, returning ONLY a valid JSON object with the same keys.

Original wine data:
${JSON.stringify(row, null, 2)}

• Keep existing values.
• Do not guess price if unsure.
• If a field cannot be confidently completed, return null.
`.trim();

  const chat = await openai.chat.completions.create({
    model: "gpt-4",
    temperature: 0.2,
    messages: [{ role: "user", content: prompt }],
  });

  const responseText = chat.choices[0].message.content;
  const match = responseText.match(/\{[\s\S]*\}/);
  if (!match) throw new Error("GPT response did not contain valid JSON");

  const cleaned = JSON.parse(match[0]);

  // Ensure sources is a clean string for CSV
  if (Array.isArray(cleaned.sources)) {
    cleaned.sources = cleaned.sources.join("; ");
  }

  return { ...row, ...cleaned };
};

const processCSV = async () => {
  if (!fs.existsSync(inputPath)) {
    console.error(`🚫 File not found: ${inputPath}`);
    process.exit(1);
  }

  const records = [];

  const parser = fs
    .createReadStream(inputPath)
    .pipe(parse({ columns: true, skip_empty_lines: true }));

  for await (const record of parser) {
    records.push(record);
  }

  const cleaned = [];
  for (const row of records) {
    try {
      const filled = await cleanRowWithGPT(row);
      cleaned.push(filled);
      console.log("✅ Cleaned:", filled.wine_name || filled["Wine Name"]);
      await new Promise((res) => setTimeout(res, 500)); // avoid rate limit
    } catch (err) {
      console.error("❌ Failed to clean:", row["Wine Name"] || row.wine_name, err.message);
      cleaned.push(row); // fallback to original
    }
  }

  const headers = Object.keys(cleaned[0]).map((key) => ({
    id: key,
    title: key,
  }));

  const writer = createObjectCsvWriter({ path: outputPath, header: headers });
  await writer.writeRecords(cleaned);

  console.log(`🎉 Cleaned CSV written to ${outputPath}`);
};

processCSV();
