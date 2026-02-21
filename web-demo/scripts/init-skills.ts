#!/usr/bin/env node
/**
 * Build-time script to initialize skills from SKILL.md files
 * This runs during Netlify build to populate the database
 */

import * as dotenv from 'dotenv';
import { Client } from 'pg';
import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';

// Load .env file from project root
dotenv.config({ path: path.resolve(process.cwd(), '.env') });

interface SkillMetadata {
  name: string;
  description: string;
  license?: string;
  compatibility?: string;
  metadata?: {
    author?: string;
    version?: string;
    generatedBy?: string;
  };
}

async function initSkills() {
  const databaseUrl = process.env.DATABASE_URL;
  const skillBasePath = process.env.SKILL_BASE_PATH || '../.iflow/skills';

  if (!databaseUrl) {
    console.error('❌ DATABASE_URL not set');
    process.exit(1);
  }

  console.log('🔄 Initializing skills...');
  console.log(`📁 Skill path: ${skillBasePath}`);

  const client = new Client({
    connectionString: databaseUrl,
    ssl: { rejectUnauthorized: false }
  });

  try {
    await client.connect();
    console.log('✅ Connected to database');

    // Create table if not exists
    await client.query(`
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
    await client.query(`
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

    // Create search index
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_skills_search ON skills 
      USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')))
    `);

    // Resolve skill path
    const resolvedPath = path.isAbsolute(skillBasePath)
      ? skillBasePath
      : path.join(process.cwd(), skillBasePath);

    if (!fs.existsSync(resolvedPath)) {
      console.warn(`⚠️ Skill path does not exist: ${resolvedPath}`);
      console.log('ℹ️ Skipping skill initialization (will use existing database data)');
      return;
    }

    // Read and parse skills
    const categoryEntries = fs.readdirSync(resolvedPath, { withFileTypes: true });
    let loaded = 0;
    let errors = 0;

    for (const categoryEntry of categoryEntries) {
      if (categoryEntry.isDirectory()) {
        const category = categoryEntry.name;
        const categoryPath = path.join(resolvedPath, category);
        const skillEntries = fs.readdirSync(categoryPath, { withFileTypes: true });

        for (const entry of skillEntries) {
          if (entry.isDirectory()) {
            const skillFilePath = path.join(categoryPath, entry.name, 'SKILL.md');

            if (fs.existsSync(skillFilePath)) {
              try {
                const content = fs.readFileSync(skillFilePath, 'utf-8');
                const skill = parseSkillMarkdown(content, entry.name, category);

                if (skill) {
                  await insertOrUpdateSkill(client, skill);
                  console.log(`  ✅ [${category}] ${skill.name}`);
                  loaded++;
                }
              } catch (err) {
                console.error(`  ❌ [${category}] ${entry.name}: ${err instanceof Error ? err.message : 'Unknown error'}`);
                errors++;
              }
            }
          }
        }
      }
    }

    console.log(`\n📊 Summary: ${loaded} skills loaded, ${errors} errors`);

  } catch (error) {
    console.error('❌ Database error:', error);
    process.exit(1);
  } finally {
    await client.end();
  }
}

function parseSkillMarkdown(content: string, skillId: string, category: string): any | null {
  // Extract YAML frontmatter between --- markers (support Windows \r\n and Unix \n)
  const frontmatterMatch = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);

  if (!frontmatterMatch) {
    console.warn(`⚠️ No YAML frontmatter in ${skillId}/SKILL.md`);
    return null;
  }

  try {
    const metadata = yaml.load(frontmatterMatch[1]) as SkillMetadata;

    return {
      id: skillId,
      name: metadata.name || skillId,
      description: metadata.description || '',
      category: category,
      type_group: 'problem_solving',
      tags: [metadata.license || 'MIT', metadata.compatibility ? 'compatible' : ''].filter(Boolean),
      use_cases: [],
      dependencies: [],
      input_data_types: [],
      output_format: null,
      statistical_concept: null,
      algorithm_name: null,
      complexity: null,
      metadata: {
        ...metadata.metadata,
        license: metadata.license,
        compatibility: metadata.compatibility,
        sourceFile: 'SKILL.md'
      },
      source_content: content
    };
  } catch (err) {
    console.error(`❌ Failed to parse YAML in ${skillId}/SKILL.md:`, err);
    return null;
  }
}

async function insertOrUpdateSkill(client: Client, skill: any) {
  await client.query(`
    INSERT INTO skills (
      id, name, description, category, type_group, tags,
      use_cases, dependencies, input_data_types, output_format,
      statistical_concept, algorithm_name, complexity, metadata, source_content
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
    ON CONFLICT (id) DO UPDATE SET
      name = EXCLUDED.name,
      description = EXCLUDED.description,
      category = EXCLUDED.category,
      type_group = EXCLUDED.type_group,
      tags = EXCLUDED.tags,
      metadata = EXCLUDED.metadata,
      source_content = EXCLUDED.source_content,
      updated_at = CURRENT_TIMESTAMP
  `, [
    skill.id,
    skill.name,
    skill.description,
    skill.category,
    skill.type_group,
    skill.tags,
    skill.use_cases,
    skill.dependencies,
    skill.input_data_types,
    skill.output_format,
    skill.statistical_concept,
    skill.algorithm_name,
    skill.complexity,
    JSON.stringify(skill.metadata),
    skill.source_content
  ]);
}

// Run if called directly (support Windows and Unix)
const isMainModule = import.meta.url === `file://${process.argv[1]}` || 
                     import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/')}` ||
                     process.argv[1].endsWith('init-skills.ts');

if (isMainModule) {
  initSkills().catch(console.error);
}

export { initSkills };
