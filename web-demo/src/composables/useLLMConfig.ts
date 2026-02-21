import { ref } from 'vue';
import type { LLMConfig } from '@/types/skill';

const STORAGE_KEY = 'llm-config';

const PROVIDER_MODELS: Record<string, string[]> = {
  'openai': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
  'anthropic': ['claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307']
};

// 全局共享状态 - 直接导出 ref 供组件使用
const config = ref<LLMConfig>({
  provider: 'openai',
  apiKey: '',
  model: 'gpt-4o-mini',
  baseUrl: ''
});

const isConfigured = ref(false);
let isInitialized = false;

// Load from localStorage on init
function loadConfig() {
  if (isInitialized) return;

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
    isInitialized = true;
  } catch (e) {
    console.error('Failed to load LLM config:', e);
  }
}

export function useLLMConfig() {
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
    const models = getAvailableModels(provider);
    config.value = {
      ...config.value,
      provider: provider as 'openai' | 'anthropic',
      model: models.length > 0 && models[0] ? models[0] : ''
    };
  }

  return {
    config,
    isConfigured,
    saveConfig,
    clearConfig,
    getAvailableModels,
    updateProvider
  };
}

// 初始化时加载配置
loadConfig();