import type { Handler } from '@netlify/functions';
import { initDb, closeDb, setDbConnected } from './db';
import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';

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

export const handler: Handler = async (event, context) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Content-Type': 'application/json'
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers, body: '' };
  }

  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({ error: 'Method not allowed' })
    };
  }

  const skillBasePath = process.env.SKILL_BASE_PATH;

  if (!skillBasePath) {
    return {
      statusCode: 400,
      headers,
      body: JSON.stringify({ error: 'SKILL_BASE_PATH not configured' })
    };
  }

  try {
    const db = await initDb();
    setDbConnected(true);
    const skillsLoaded: string[] = [];
    const errors: string[] = [];

    // Resolve path (handle both relative and absolute)
    const resolvedPath = path.isAbsolute(skillBasePath) 
      ? skillBasePath 
      : path.join(process.cwd(), skillBasePath);

    // Check if directory exists
    if (!fs.existsSync(resolvedPath)) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ 
          error: 'Skill base path does not exist',
          path: resolvedPath
        })
      };
    }

    // Read skill directories
    const entries = fs.readdirSync(resolvedPath, { withFileTypes: true });

    for (const entry of entries) {
      if (entry.isDirectory()) {
        const skillPath = path.join(resolvedPath, entry.name);
        const skillFilePath = path.join(skillPath, 'SKILL.md');

        if (fs.existsSync(skillFilePath)) {
          try {
            const content = fs.readFileSync(skillFilePath, 'utf-8');
            
            // Parse YAML frontmatter from SKILL.md
            const parsed = parseSkillMarkdown(content, entry.name);
            
            if (parsed) {
              parsed.source_content = content;
              await insertOrUpdateSkill(db, parsed);
              skillsLoaded.push(parsed.name);
            }
          } catch (err) {
            errors.push(`${entry.name}: ${err instanceof Error ? err.message : 'Unknown error'}`);
          }
        }
      }
    }

    await closeDb();

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        message: 'Skills initialized successfully',
        loaded: skillsLoaded.length,
        skills: skillsLoaded,
        errors: errors.length > 0 ? errors : undefined
      })
    };
  } catch (error) {
    console.error('Error initializing skills:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({
        error: 'Failed to initialize skills',
        details: error instanceof Error ? error.message : 'Unknown error'
      })
    };
  }
};

function parseSkillMarkdown(content: string, skillId: string): any | null {
  // Extract YAML frontmatter between --- markers (support Windows \r\n and Unix \n)
  const frontmatterMatch = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  
  if (!frontmatterMatch) {
    console.warn(`No YAML frontmatter found in ${skillId}/SKILL.md`);
    return null;
  }

  try {
    const metadata = yaml.load(frontmatterMatch[1]) as SkillMetadata;
    
    // Map to skill schema
    return {
      id: skillId,
      name: metadata.name || skillId,
      description: metadata.description || '',
      category: 'skill',
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
      }
    };
  } catch (err) {
    console.error(`Failed to parse YAML in ${skillId}/SKILL.md:`, err);
    return null;
  }
}

async function insertOrUpdateSkill(db: any, skill: any) {
  await db.query(`
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
      use_cases = EXCLUDED.use_cases,
      dependencies = EXCLUDED.dependencies,
      input_data_types = EXCLUDED.input_data_types,
      output_format = EXCLUDED.output_format,
      statistical_concept = EXCLUDED.statistical_concept,
      algorithm_name = EXCLUDED.algorithm_name,
      complexity = EXCLUDED.complexity,
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