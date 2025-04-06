// Talk to OpenAI API

// Steps to run in the terminal
// npm install
// open up the file - cd 00_chat
// node server.js 


import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { OpenAI } from "openai";

// Load environment variables
dotenv.config();

// Initialize OpenAI API client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const app = express();
const port = 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static("public")); // Serve static frontend files

/**
 * Handles chat requests to OpenAI
 */
app.post("/chat", async (req, res) => {
  try {
    const { systemMessage, prompt, model, thread } = req.body;

    // Construct conversation history
    const messages = thread.length > 0 ? [...thread] : [{ role: "system", content: systemMessage }];
    messages.push({ role: "user", content: prompt });

    // Send request to OpenAI
    const response = await openai.chat.completions.create({
      model: model,
      messages: messages,
    });

    const aiResponse = response.choices[0].message;

    res.json({ response: aiResponse });

  } catch (error) {
    console.error("OpenAI API Error:", error);
    res.status(500).json({ error: "Failed to fetch OpenAI response" });
  }
});

// Start server
app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
