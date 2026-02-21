import { ref, watch } from 'vue';
import type { LLMConfig } from '@/types/skill';

const STORAGE_KEY = 'llm-config';

const PROVIDER_MODELS: Record<string, string[]> = {
  'openai': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
  'anthropic': ['claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307']
};

export function useLLMConfig() {
  const config = ref<LLMConfig>({
    provider: 'openai',
    apiKey: '',
    model: 'gpt-4o-mini',
    baseUrl: ''
  });

  const isConfigured = ref(false);

  // Load from localStorage on init
  function loadConfig() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        config.value = {
          provider: parsed.provider || 'openai',
          apiKey: parsed.apiKey || '',
          model: parsed.model || 'gpt-4o-mini',
          baseUrl: parsed.baseUrl || ''
        };
        isConfigured.value = !!config.value.apiKey;
      }
    } catch (e) {
      console.error('Failed to load LLM config:', e);
    }
  }

  // Save to localStorage (excluding API key for security)
  function saveConfig(saveKey: boolean = false) {
    try {
      const toStore = {
        provider: config.value.provider,
        model: config.value.model,
        baseUrl: config.value.baseUrl,
        ...(saveKey && { apiKey: config.value.apiKey })
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore));
      isConfigured.value = !!config.value.apiKey;
    } catch (e) {
      console.error('Failed to save LLM config:', e);
    }
  }

  function clearConfig() {
    config.value = {
      provider: 'openai',
      apiKey: '',
      model: 'gpt-4o-mini',
      baseUrl: ''
    };
    localStorage.removeItem(STORAGE_KEY);
    isConfigured.value = false;
  }

  function getAvailableModels(provider: string): string[] {
    return PROVIDER_MODELS[provider] || [''];
  }

  function updateProvider(provider: string) {
    config.value.provider = provider as 'openai' | 'anthropic';
    const models = getAvailableModels(provider);
    if (models.length > 0 && models[0]) {
      config.value.model = models[0];
    } else {
      config.value.model = '';
    }
    // Note: We no longer clear baseUrl when switching providers
    // This allows users to keep a custom endpoint if they want
  }

  // Load on initialization
  loadConfig();

  return {
    config,
    isConfigured,
    saveConfig,
    clearConfig,
    getAvailableModels,
    updateProvider
  };
}
