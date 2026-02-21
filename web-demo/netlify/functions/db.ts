import { Client } from 'pg';

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
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
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
