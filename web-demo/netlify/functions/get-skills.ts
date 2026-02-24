import type { Handler } from '@netlify/functions';
import { getDbClient, isDbConnected, setDbConnected } from './db';

const DEFAULT_PAGE_SIZE = 100;
const MAX_PAGE_SIZE = 500;

export const handler: Handler = async (event, context) => {
  // Enable CORS
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Content-Type': 'application/json'
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers, body: '' };
  }

  if (event.httpMethod !== 'GET') {
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({ error: 'Method not allowed' })
    };
  }

  try {
    const db = getDbClient();
    if (!isDbConnected()) {
      await db.connect();
      setDbConnected(true);
    }

    // Parse query parameters
    const params = event.queryStringParameters || {};
    const page = parseInt(params.page || '1', 10);
    const limit = Math.min(parseInt(params.limit || String(DEFAULT_PAGE_SIZE), 10), MAX_PAGE_SIZE);
    const excludeSource = params.exclude_source !== 'false'; // Default to true
    const statsOnly = params.stats_only === 'true';
    const offset = (page - 1) * limit;

    // If stats_only is true, return only statistics without skills data
    if (statsOnly) {
      const countResult = await db.query('SELECT COUNT(*) as total FROM skills');
      const categoryResult = await db.query(`
        SELECT category, COUNT(*) as count
        FROM skills
        GROUP BY category
      `);
      const typeGroupResult = await db.query(`
        SELECT type_group, COUNT(*) as count
        FROM skills
        GROUP BY type_group
      `);

      const categories: Record<string, number> = {};
      categoryResult.rows.forEach(row => {
        categories[row.category || 'Uncategorized'] = parseInt(row.count, 10);
      });

      const typeGroups: Record<string, number> = {};
      typeGroupResult.rows.forEach(row => {
        typeGroups[row.type_group || 'unknown'] = parseInt(row.count, 10);
      });

      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          total: parseInt(countResult.rows[0].total, 10),
          categories,
          type_groups: typeGroups,
          page_size: limit
        })
      };
    }

    // Build SELECT columns based on excludeSource flag
    const selectColumns = excludeSource
      ? `id, name, description, category, type_group, tags,
         use_cases, dependencies, input_data_types, output_format,
         statistical_concept, algorithm_name, complexity, metadata`
      : `id, name, description, category, type_group, tags,
         use_cases, dependencies, input_data_types, output_format,
         statistical_concept, algorithm_name, complexity, metadata, source_content`;

    // Get total count
    const countResult = await db.query('SELECT COUNT(*) as total FROM skills');
    const total = parseInt(countResult.rows[0].total, 10);

    // Get paginated skills
    const result = await db.query(`
      SELECT ${selectColumns}
      FROM skills
      ORDER BY name ASC
      LIMIT $1 OFFSET $2
    `, [limit, offset]);

    const skills = result.rows.map(row => ({
      ...row,
      tags: row.tags || [],
      use_cases: row.use_cases || [],
      dependencies: row.dependencies || [],
      input_data_types: row.input_data_types || []
    }));

    // Calculate total pages
    const totalPages = Math.ceil(total / limit);

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        skills,
        pagination: {
          page,
          limit,
          total,
          total_pages: totalPages,
          has_next: page < totalPages,
          has_prev: page > 1
        }
      })
    };
  } catch (error) {
    console.error('Error fetching skills:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: 'Failed to fetch skills' })
    };
  }
};
