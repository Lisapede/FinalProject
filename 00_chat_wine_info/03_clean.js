import dotenv from 'dotenv';
import fs from 'fs';
import csv from 'csv-parser';
import { parse as json2csv } from 'json2csv';
import OpenAI from 'openai';
import cliProgress from 'cli-progress';

// Load env variables
dotenv.config();

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const inputFile = 'cleaned_export.csv';
const outputFile = 'cleaned_export_v2.csv';

async function processCSV() {
  const rows = [];

  // Step 1: Load CSV into memory
  fs.createReadStream(inputFile)
    .pipe(csv())
    .on('data', (row) => rows.push(row))
    .on('end', async () => {
      const cleanedRows = [];
      const progressBar = new cliProgress.SingleBar(
        {
          format: 'Progress | {bar} | {percentage}% | {value}/{total} rows',
          barCompleteChar: '█',
          barIncompleteChar: '-',
          hideCursor: true,
        },
        cliProgress.Presets.shades_classic
      );

      progressBar.start(rows.length, 0);

      // Step 2: Loop through rows and clean
      for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const rawText = Object.values(row).filter(Boolean).join(' ');
        const shouldClean = Object.values(row).some(v => v === '');

        if (shouldClean) {
          const prompt = `
Check if the following line describes a wine. If yes, extract and complete this information:
- is_wine (yes or no)
- wine_name
- producer
- vintage
- varietal
- body
- region
- country
- price

Raw entry: """${rawText}"""
Return only a valid JSON object with those fields.
          `.trim();

          try {
            const chat = await openai.chat.completions.create({
              model: 'gpt-4',
              messages: [{ role: 'user', content: prompt }],
              temperature: 0,
            });

            const resultText = chat.choices[0].message.content;
            const cleaned = JSON.parse(resultText);
            cleanedRows.push({ ...row, ...cleaned });
          } catch (err) {
            console.error(`⚠️ Error on row ${i + 1}: ${err.message}`);
            cleanedRows.push(row); // fallback
          }
        } else {
          cleanedRows.push(row);
        }

        progressBar.update(i + 1);
      }

      progressBar.stop();

      // Step 3: Save output
      const csvOutput = json2csv(cleanedRows);
      fs.writeFileSync(outputFile, csvOutput);
      console.log(`✅ Done. Output saved to ${outputFile}`);
    });
}

processCSV();
