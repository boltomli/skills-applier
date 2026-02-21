import { ref, computed } from 'vue';
import axios from 'axios';
import type { Skill, SkillRecommendation, LLMConfig, RecommendationResponse } from '@/types/skill';

const API_BASE = '/.netlify/functions';

export function useRecommendation() {
  const recommendations = ref<SkillRecommendation[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const method = ref<'llm' | 'keyword-matching'>('keyword-matching');

  const hasRecommendations = computed(() => recommendations.value.length > 0);
  const sortedRecommendations = computed(() => {
    return [...recommendations.value].sort((a, b) => b.confidence - a.confidence);
  });

  async function fetchSkills(): Promise<Skill[]> {
    try {
      const response = await axios.get(`${API_BASE}/get-skills`);
      return response.data.skills || [];
    } catch (err) {
      console.error('Failed to fetch skills:', err);
      return [];
    }
  }

  function buildSystemPrompt(skills: Skill[]): string {
    const skillsList = skills.map(skill => `
- ${skill.name} (ID: ${skill.id})
  Category: ${skill.category}
  Description: ${skill.description}
  Tags: ${skill.tags?.join(', ') || 'none'}
  Use Cases: ${skill.use_cases?.join(', ') || 'none'}
`).join('\n');

    return `You are a skill recommendation assistant. Based on the user's problem description, recommend the most relevant skills from the following list.

Available Skills:
${skillsList}

Analyze the user's problem and recommend 1-5 most relevant skills. For each recommendation, provide:
1. skill_id: The ID of the recommended skill
2. skill_name: The name of the skill
3. reason: A clear explanation of why this skill is relevant to the user's problem (2-3 sentences)
4. confidence: A number between 0 and 1 indicating your confidence in this recommendation
5. suggestions: 2-3 specific suggestions on how to apply this skill to solve the problem

Respond in JSON format with this structure:
{
  "recommendations": [
    {
      "skill_id": "skill-id",
      "skill_name": "Skill Name",
      "reason": "Explanation of relevance...",
      "confidence": 0.85,
      "suggestions": ["Suggestion 1", "Suggestion 2"]
    }
  ]
}`;
  }

  async function getRecommendations(
    problemDescription: string,
    llmConfig?: LLMConfig | null
  ): Promise<void> {
    loading.value = true;
    error.value = null;
    recommendations.value = [];

    try {
      if (llmConfig?.apiKey) {
        // Use LLM for intelligent recommendations
        await getLLMRecommendations(problemDescription, llmConfig);
      } else {
        // Fallback to keyword matching
        await getKeywordRecommendations(problemDescription);
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to get recommendations';
      console.error('Recommendation error:', err);
    } finally {
      loading.value = false;
    }
  }

  async function getLLMRecommendations(
    problemDescription: string,
    llmConfig: LLMConfig
  ): Promise<void> {
    const skills = await fetchSkills();

    if (skills.length === 0) {
      error.value = 'No skills available for recommendation';
      return;
    }

    const systemPrompt = buildSystemPrompt(skills);

    const response = await axios.post(`${API_BASE}/llm-proxy`, {
      provider: llmConfig.provider,
      apiKey: llmConfig.apiKey,
      baseUrl: llmConfig.baseUrl,
      model: llmConfig.model,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: problemDescription }
      ],
      temperature: 0.7,
      max_tokens: 2000
    });

    const content = response.data.content;

    // Parse JSON response
    let parsed: { recommendations: SkillRecommendation[] };
    try {
      parsed = JSON.parse(content);
    } catch {
      // Try to extract JSON from markdown code block
      const jsonMatch = content.match(/```json\n?([\s\S]*?)\n?```/);
      if (jsonMatch) {
        parsed = JSON.parse(jsonMatch[1]);
      } else {
        throw new Error('Failed to parse LLM response');
      }
    }

    // Filter low confidence recommendations and enrich with skill data
    recommendations.value = parsed.recommendations
      .filter(rec => rec.confidence >= 0.3)
      .map(rec => ({
        ...rec,
        skill: skills.find(s => s.id === rec.skill_id)
      }));

    method.value = 'llm';
  }

  async function getKeywordRecommendations(problemDescription: string): Promise<void> {
    const response = await axios.post(`${API_BASE}/recommend`, {
      query: problemDescription,
      limit: 5
    });

    recommendations.value = response.data.recommendations || [];
    method.value = 'keyword-matching';
  }

  function clearRecommendations() {
    recommendations.value = [];
    error.value = null;
    method.value = 'keyword-matching';
  }

  return {
    recommendations,
    sortedRecommendations,
    loading,
    error,
    method,
    hasRecommendations,
    getRecommendations,
    clearRecommendations
  };
}
