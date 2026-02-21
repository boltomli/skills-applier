import type { Handler } from '@netlify/functions';
import { getDbClient } from './db';

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

  try {
    const { query, limit = 5 } = JSON.parse(event.body || '{}');

    if (!query || typeof query !== 'string') {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'Query is required' })
      };
    }

    const db = getDbClient();
    await db.connect();

    // Simple keyword matching using PostgreSQL full-text search
    // Fallback when LLM is not configured
    const searchQuery = query.toLowerCase().split(/\s+/).filter(w => w.length > 2).join(' | ');

    const result = await db.query(`
      SELECT 
        id, name, description, category, type_group, tags,
        use_cases, dependencies,
        ts_rank(
          to_tsvector('english', name || ' ' || COALESCE(description, '') || ' ' || COALESCE(array_to_string(tags, ' '), '')),
          to_tsquery('english', $1)
        ) as rank
      FROM skills
      WHERE to_tsvector('english', name || ' ' || COALESCE(description, '') || ' ' || COALESCE(array_to_string(tags, ' '), '')) @@ to_tsquery('english', $1)
      ORDER BY rank DESC
      LIMIT $2
    `, [searchQuery, limit]);

    await db.end();

    const recommendations = result.rows.map(row => ({
      skill_id: row.id,
      skill_name: row.name,
      reason: `Matches keywords in your query. Category: ${row.category}`,
      confidence: Math.min(0.3 + (row.rank * 0.5), 0.8),
      suggestions: row.use_cases?.slice(0, 2) || ['Consider reviewing the skill documentation'],
      skill: {
        ...row,
        tags: row.tags || [],
        use_cases: row.use_cases || [],
        dependencies: row.dependencies || []
      }
    }));

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        recommendations,
        method: 'keyword-matching',
        query
      })
    };
  } catch (error) {
    console.error('Recommendation Error:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({
        error: 'Failed to generate recommendations',
        details: error instanceof Error ? error.message : 'Unknown error'
      })
    };
  }
};
