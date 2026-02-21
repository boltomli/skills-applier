export interface Skill {
  id: string;
  name: string;
  description: string;
  category: string;
  type_group: 'problem_solving' | 'programming';
  tags: string[];
  use_cases: string[];
  dependencies: string[];
  input_data_types: string[];
  output_format?: string;
  statistical_concept?: string;
  algorithm_name?: string;
  complexity?: string;
  metadata?: Record<string, any>;
  source_content?: string;
}

export interface SkillRecommendation {
  skill_id: string;
  skill_name: string;
  reason: string;
  confidence: number;
  suggestions: string[];
  skill?: Skill;
}

export interface LLMConfig {
  provider: 'openai' | 'anthropic';
  apiKey: string;
  baseUrl?: string;
  model: string;
}

export interface RecommendationResponse {
  recommendations: SkillRecommendation[];
  method: 'llm' | 'keyword-matching';
  query: string;
}
