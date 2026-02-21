import { Client } from 'pg';
import * as dotenv from 'dotenv';
import * as path from 'path';

// Load .env file from project root (2 levels up from netlify/functions/)
dotenv.config({ path: path.resolve(__dirname, '../../.env') });

let client: Client | null = null;
let isConnected = false;

export function getDbClient(): Client {
  if (!client) {
    client = new Client({
      connectionString: process.env.DATABASE_URL,
      ssl: {
        rejectUnauthorized: false
      }
    });
    isConnected = false;
  }
  return client;
}

export function isDbConnected(): boolean {
  return isConnected;
}

export function setDbConnected(connected: boolean): void {
  isConnected = connected;
}

export async function initDb() {
  const db = getDbClient();
  if (!isConnected) {
    await db.connect();
    isConnected = true;
  }

  // Create skills table
  await db.query(`
    CREATE TABLE IF NOT EXISTS skills (
      id VARCHAR(255) PRIMARY KEY,
      name VARCHAR(255) NOT NULL,
      description TEXT,
      category VARCHAR(100),
      type_group VARCHAR(50),
      tags TEXT[],
      use_cases TEXT[],
      dependencies TEXT[],
      input_data_types TEXT[],
      output_format VARCHAR(100),
      statistical_concept VARCHAR(255),
      algorithm_name VARCHAR(255),
      complexity VARCHAR(50),
      metadata JSONB,
      source_content TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Add source_content column if it doesn't exist (for existing tables)
  await db.query(`
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'skills' AND column_name = 'source_content'
      ) THEN
        ALTER TABLE skills ADD COLUMN source_content TEXT;
      END IF;
    END $$;
  `);

  // Create index for full-text search
  await db.query(`
    CREATE INDEX IF NOT EXISTS idx_skills_search ON skills 
    USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')))
  `);

  return db;
}

export async function closeDb() {
  if (client) {
    await client.end();
    client = null;
    isConnected = false;
  }
}
