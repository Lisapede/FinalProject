// npm install csv-parser csv-writer

import fs from "fs";
import dotenv from "dotenv";
import { createObjectCsvWriter } from "csv-writer";
import { OpenAI } from "openai";

dotenv.config(); // Load OPENAI_API_KEY from .env

const { parse } = await import("csv-parse"); // Dynamic import fix

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });


const inputPath = "./export.csv";
const outputPath = "./cleaned_export.csv";

const missingOrNull = (val) => val === null || val === "" || val.toLowerCase() === "null";

const cleanRowWithGPT = async (row) => {
  const fieldsToFill = Object.entries(row).filter(([key, val]) => missingOrNull(val));
  if (fieldsToFill.length === 0) return row; // nothing to clean

  const prompt = `
You are a wine data expert. Fill in any missing fields in this wine data object, returning ONLY a valid JSON matching the same keys.

Original wine data:
${JSON.stringify(row, null, 2)}

• Keep existing values.
• Do not guess price if unsure.
• If a field cannot be confidently completed, return null for it.
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
  return { ...row, ...cleaned };
};

const processCSV = async () => {
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
