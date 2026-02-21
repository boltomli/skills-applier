import type { Handler } from '@netlify/functions';
import { getDbClient, isDbConnected, setDbConnected } from './db';

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

    const result = await db.query(`
      SELECT
        id, name, description, category, type_group, tags,
        use_cases, dependencies, input_data_types, output_format,
        statistical_concept, algorithm_name, complexity, metadata, source_content
      FROM skills
      ORDER BY name ASC
    `);

    // Don't close the connection in serverless environment
    // Let it persist for reuse across warm invocations

    const skills = result.rows.map(row => ({
      ...row,
      tags: row.tags || [],
      use_cases: row.use_cases || [],
      dependencies: row.dependencies || [],
      input_data_types: row.input_data_types || []
    }));

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        skills,
        total: skills.length,
        categories: skills.reduce((acc: Record<string, number>, skill: any) => {
          acc[skill.category] = (acc[skill.category] || 0) + 1;
          return acc;
        }, {})
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
