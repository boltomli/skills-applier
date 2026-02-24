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

    // Migrate old id format to new format (category/id)
    const migrateResult = await client.query(`
      UPDATE skills
      SET id = category || '/' || id
      WHERE id NOT LIKE '%/%' AND category IS NOT NULL
      RETURNING id
    `);
    if (migrateResult.rowCount && migrateResult.rowCount > 0) {
      console.log(`🔧 Migrated ${migrateResult.rowCount} skill IDs to new format (category/id)`);
    }

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
    let skipped = 0;
    let errors = 0;

    // Fetch existing skills from database (by id, which is the primary key)
    const existingSkillsResult = await client.query<{ id: string }>(
      'SELECT id FROM skills'
    );
    const existingSkills = new Set(
      existingSkillsResult.rows.map(row => row.id)
    );
    console.log(`📋 Found ${existingSkills.size} existing skills in database`);

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
                  // Check if skill already exists (by id, which is the primary key)
                  if (existingSkills.has(skill.id)) {
                    console.log(`  ⏭️ [${category}] ${skill.name} (skipped, already exists)`);
                    skipped++;
                  } else {
                    await insertSkill(client, skill);
                    console.log(`  ✅ [${category}] ${skill.name}`);
                    loaded++;
                  }
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

    console.log(`\n📊 Summary: ${loaded} skills loaded, ${skipped} skipped, ${errors} errors`);

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
    // Pre-process YAML to fix multi-line block scalars that may contain list-like content
    // The issue: |- or >- followed by indented lines starting with '-' are parsed as new documents
    // Solution: Convert block scalars to quoted single-line strings
    let yamlContent = frontmatterMatch[1];

    // Fix description field with block scalar format (|- or >-)
    // The issue: block scalar content may contain lines starting with '-' which YAML
    // interprets incorrectly. Solution: convert to quoted single-line string.
    // Use line-by-line parsing to handle all cases correctly.
    const yamlLines = yamlContent.split('\n');
    const fixedLines: string[] = [];
    let inBlockScalar = false;
    let blockContent: string[] = [];

    for (const line of yamlLines) {
      // Check if this is a description with block scalar
      if (line.match(/^description:\s*[|>][-]?$/)) {
        inBlockScalar = true;
        blockContent = [];
        continue;
      }

      if (inBlockScalar) {
        // Check if this is a new top-level key (starts with a word followed by colon, not indented)
        if (line.match(/^\w+:/)) {
          // End of block scalar, convert to quoted string
          const singleLine = blockContent
            .map(l => l.trim())
            .filter(l => l.length > 0)
            .join(' ')
            .replace(/"/g, '\\"');
          fixedLines.push(`description: "${singleLine}"`);
          fixedLines.push(line);
          inBlockScalar = false;
          blockContent = [];
        } else {
          blockContent.push(line);
        }
      } else {
        fixedLines.push(line);
      }
    }

    // Handle case where block scalar ends at end of file
    if (inBlockScalar && blockContent.length > 0) {
      const singleLine = blockContent
        .map(l => l.trim())
        .filter(l => l.length > 0)
        .join(' ')
        .replace(/"/g, '\\"');
      fixedLines.push(`description: "${singleLine}"`);
    }

    yamlContent = fixedLines.join('\n');

    // Fix single-line description that contains colons (which YAML interprets as new key-value pairs)
    // Match: description: <value with colon but not quoted>
    yamlContent = yamlContent.replace(
      /^description:\s*(.+)$/gm,
      (match, value) => {
        const trimmed = value.trim();
        // Already quoted - skip
        if ((trimmed.startsWith('"') && trimmed.endsWith('"')) ||
            (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
          return match;
        }
        // Contains colon - needs quoting
        if (trimmed.includes(':')) {
          const escaped = trimmed.replace(/"/g, '\\"');
          return `description: "${escaped}"`;
        }
        return match;
      }
    );

    const metadata = yaml.load(yamlContent) as SkillMetadata;

    // Generate unique id combining category and skillId to avoid conflicts
    const uniqueId = `${category}/${skillId}`;

    return {
      id: uniqueId,
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

async function insertSkill(client: Client, skill: any) {
  await client.query(`
    INSERT INTO skills (
      id, name, description, category, type_group, tags,
      use_cases, dependencies, input_data_types, output_format,
      statistical_concept, algorithm_name, complexity, metadata, source_content
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
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
