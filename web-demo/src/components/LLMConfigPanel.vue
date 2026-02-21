<template>
  <div class="config-panel">
    <div class="form-row">
      <div class="form-group">
        <label for="provider">Provider</label>
        <select
          id="provider"
          v-model="config.provider"
          @change="onProviderChange"
        >
          <option value="openai">OpenAI</option>
          <option value="anthropic">Anthropic</option>
        </select>
      </div>

      <div class="form-group">
        <label for="model">Model</label>
        <input
          id="model"
          v-model="config.model"
          type="text"
          placeholder="e.g., gpt-4, claude-3"
        />
      </div>
    </div>

    <div class="form-group">
      <label for="baseUrl">
        Base URL
        <small class="optional-label">(optional)</small>
      </label>
      <input
        id="baseUrl"
        v-model="config.baseUrl"
        type="url"
        :placeholder="getBaseUrlPlaceholder()"
      />
      <small class="help-text">{{ getBaseUrlHelpText() }}</small>
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

    <div class="form-actions">
      <button class="save-btn" @click="save">Save Configuration</button>
      <button class="clear-btn" @click="clear">Clear</button>
    </div>

    <div v-if="saveSuccess" class="success-message">
      ✓ Configuration saved successfully!
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useLLMConfig } from '@/composables/useLLMConfig';

const emit = defineEmits<{
  saved: [];
}>();

const { config, saveConfig, clearConfig, updateProvider } = useLLMConfig();

const showKey = ref(false);
const saveSuccess = ref(false);

function onProviderChange() {
  updateProvider(config.value.provider);
}

function getBaseUrlPlaceholder(): string {
  switch (config.value.provider) {
    case 'openai':
      return 'https://api.openai.com/v1';
    case 'anthropic':
      return 'https://api.anthropic.com';
    default:
      return '';
  }
}

function getBaseUrlHelpText(): string {
  switch (config.value.provider) {
    case 'openai':
      return 'Leave empty to use the official OpenAI API, or enter a custom endpoint (e.g., OpenRouter, Azure).';
    case 'anthropic':
      return 'Leave empty to use the official Anthropic API, or enter a custom endpoint.';
    default:
      return '';
  }
}

function save() {
  saveConfig(true);
  saveSuccess.value = true;
  setTimeout(() => {
    saveSuccess.value = false;
  }, 2000);
  emit('saved');
}

function clear() {
  clearConfig();
}
</script>

<style scoped>
.config-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
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
  font-size: 0.75rem;
  color: #6b7280;
}

.optional-label {
  font-weight: 400;
  color: #9ca3af;
  margin-left: 0.25rem;
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.5rem;
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

.success-message {
  padding: 0.75rem 1rem;
  background: #d1fae5;
  color: #065f46;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  text-align: center;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-0.5rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
