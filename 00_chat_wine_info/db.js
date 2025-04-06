// wine‑chatbot/db.js
import Database from "better-sqlite3";

const db = new Database("wine.db");      // creates file if it doesn't exist

// 1️⃣  Schema (runs once)
db.exec(`
  CREATE TABLE IF NOT EXISTS wines (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    producer         TEXT,
    wine_name        TEXT,
    vintage_hint     TEXT,
    region           TEXT,
    state            TEXT,
    country          TEXT,
    wine_type        TEXT,
    body             TEXT,
    brand            TEXT,
    varietal         TEXT,
    taste_profile    TEXT,
    typical_vintage  TEXT,
    price            TEXT,
    sources          TEXT,               -- JSON array as string
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
  )
`);

// 2️⃣  Prepared statements = fast & safe
const insertWine = db.prepare(`
  INSERT INTO wines (
    producer, wine_name, vintage_hint,
    region, state, country, wine_type, body, brand,
    varietal, taste_profile, typical_vintage, price, sources
  ) VALUES (
    @producer, @wine_name, @vintage_hint,
    @region, @state, @country, @wine_type, @body, @brand,
    @varietal, @taste_profile, @typical_vintage, @price, @sources
  )
`);

const getAllWines = db.prepare("SELECT * FROM wines ORDER BY created_at DESC");

export function saveWine(record) {
  insertWine.run(record);
}

export function listWines() {
  return getAllWines.all();
}
