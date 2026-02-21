import type { Handler } from '@netlify/functions';
import axios from 'axios';

interface LLMRequest {
  provider: 'openai' | 'anthropic';
  apiKey: string;
  baseUrl?: string;
  model: string;
  messages: Array<{ role: string; content: string }>;
  temperature?: number;
  max_tokens?: number;
}

const ALLOWED_ORIGINS = ['*']; // Configure as needed

export const handler: Handler = async (event, context) => {
  // CORS headers
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Content-Type': 'application/json'
  };

  // Handle preflight
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
    const body: LLMRequest = JSON.parse(event.body || '{}');
    const { provider, apiKey, baseUrl, model, messages, temperature = 0.7, max_tokens = 2000 } = body;

    // Validate required fields
    if (!provider || !apiKey || !model || !messages || !Array.isArray(messages)) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({
          error: 'Missing required fields: provider, apiKey, model, messages'
        })
      };
    }

    // Validate provider
    const validProviders = ['openai', 'anthropic'];
    if (!validProviders.includes(provider)) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({
          error: `Invalid provider. Must be one of: ${validProviders.join(', ')}`
        })
      };
    }

    let response;

    switch (provider) {
      case 'openai':
        response = await callOpenAI(apiKey, model, messages, temperature, max_tokens, baseUrl);
        break;
      case 'anthropic':
        response = await callAnthropic(apiKey, model, messages, temperature, max_tokens, baseUrl);
        break;

    }

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify(response)
    };
  } catch (error) {
    console.error('LLM Proxy Error:', error);

    if (axios.isAxiosError(error)) {
      const status = error.response?.status || 500;
      const message = error.response?.data?.error?.message || error.message;

      return {
        statusCode: status,
        headers,
        body: JSON.stringify({
          error: 'LLM API Error',
          message,
          providerError: error.response?.data
        })
      };
    }

    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error'
      })
    };
  }
};

async function callOpenAI(
  apiKey: string,
  model: string,
  messages: Array<{ role: string; content: string }>,
  temperature: number,
  max_tokens: number,
  baseUrl?: string
) {
  const url = baseUrl ? baseUrl.replace(/\/$/, '') : 'https://api.openai.com/v1';

  const response = await axios.post(
    `${url}/chat/completions`,
    {
      model,
      messages,
      temperature,
      max_tokens,
      response_format: { type: 'json_object' }
    },
    {
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      timeout: 30000
    }
  );

  return {
    provider: 'openai',
    model: response.data.model,
    content: response.data.choices[0]?.message?.content,
    usage: response.data.usage
  };
}

async function callAnthropic(
  apiKey: string,
  model: string,
  messages: Array<{ role: string; content: string }>,
  temperature: number,
  max_tokens: number,
  baseUrl?: string
) {
  // Convert messages to Anthropic format
  const systemMessage = messages.find(m => m.role === 'system')?.content || '';
  const userMessages = messages.filter(m => m.role !== 'system');

  const url = baseUrl ? baseUrl.replace(/\/$/, '') : 'https://api.anthropic.com';

  const response = await axios.post(
    `${url}/v1/messages`,
    {
      model,
      max_tokens,
      temperature,
      system: systemMessage,
      messages: userMessages.map(m => ({
        role: m.role === 'user' ? 'user' : 'assistant',
        content: m.content
      }))
    },
    {
      headers: {
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json'
      },
      timeout: 30000
    }
  );

  return {
    provider: 'anthropic',
    model: response.data.model,
    content: response.data.content[0]?.text,
    usage: response.data.usage
  };
}


