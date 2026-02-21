<template>
  <div class="config-panel">
    <h3 class="panel-title">LLM Configuration</h3>
    <p class="panel-description">
      Configure your own LLM provider (BYOK) or leave empty to use keyword matching.
    </p>

    <div class="form-group">
      <label for="provider">Provider</label>
      <select
        id="provider"
        v-model="config.provider"
        @change="onProviderChange"
      >
        <option value="openai">OpenAI</option>
        <option value="anthropic">Anthropic</option>
        <option value="openai-compatible">OpenAI Compatible (LM Studio, Ollama)</option>
      </select>
    </div>

    <div v-if="config.provider === 'openai-compatible'" class="form-group">
      <label for="baseUrl">Base URL</label>
      <input
        id="baseUrl"
        v-model="config.baseUrl"
        type="url"
        placeholder="http://localhost:1234/v1"
      />
    </div>

    <div class="form-group">
      <label for="apiKey">API Key</label>
      <div class="input-with-toggle">
        <input
          id="apiKey"
          v-model="config.apiKey"
          :type="showKey ? 'text' : 'password'"
          placeholder="Enter your API key"
        />
        <button
          type="button"
          class="toggle-btn"
          @click="showKey = !showKey"
        >
          {{ showKey ? 'Hide' : 'Show' }}
        </button>
      </div>
      <small class="help-text">Your API key is stored locally and never sent to our servers.</small>
    </div>

    <div class="form-group">
      <label for="model">Model</label>
      <select
        v-if="availableModels.length > 1"
        id="model"
        v-model="config.model"
      >
        <option v-for="model in availableModels" :key="model" :value="model">
          {{ model }}
        </option>
      </select>
      <input
        v-else
        id="model"
        v-model="config.model"
        type="text"
        placeholder="Enter model name"
      />
    </div>

    <div class="form-actions">
      <button class="save-btn" @click="save">Save Configuration</button>
      <button class="clear-btn" @click="clear">Clear</button>
    </div>

    <div v-if="isConfigured" class="status-badge configured">
      ✓ LLM Configured
    </div>
    <div v-else class="status-badge not-configured">
      Using keyword matching fallback
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useLLMConfig } from '@/composables/useLLMConfig';

const { config, isConfigured, saveConfig, clearConfig, getAvailableModels, updateProvider } = useLLMConfig();

const showKey = ref(false);

const availableModels = computed(() => getAvailableModels(config.value.provider));

function onProviderChange() {
  updateProvider(config.value.provider);
}

function save() {
  saveConfig(true);
}

function clear() {
  clearConfig();
}
</script>

<style scoped>
.config-panel {
  background: #f9fafb;
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: 1px solid #e5e7eb;
}

.panel-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
  margin: 0 0 0.5rem 0;
}

.panel-description {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0 0 1.5rem 0;
  line-height: 1.5;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.375rem;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input-with-toggle {
  display: flex;
  gap: 0.5rem;
}

.input-with-toggle input {
  flex: 1;
}

.toggle-btn {
  padding: 0.5rem 0.75rem;
  background: #e5e7eb;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  cursor: pointer;
  white-space: nowrap;
}

.toggle-btn:hover {
  background: #d1d5db;
}

.help-text {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.save-btn {
  flex: 1;
  padding: 0.625rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.save-btn:hover {
  background: #2563eb;
}

.clear-btn {
  padding: 0.625rem 1rem;
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.clear-btn:hover {
  background: #f3f4f6;
}

.status-badge {
  margin-top: 1rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  text-align: center;
}

.status-badge.configured {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.not-configured {
  background: #fef3c7;
  color: #92400e;
}
</style>
