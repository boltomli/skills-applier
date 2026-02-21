<template>
  <div class="problem-input">
    <label for="problem" class="input-label">Describe Your Problem</label>
    <textarea
      id="problem"
      v-model="problemText"
      class="input-textarea"
      placeholder="Describe what you're trying to solve... (e.g., 'I need to compare the average test scores between two student groups')"
      :maxlength="maxLength"
      rows="4"
      @keydown.enter.ctrl.prevent="submit"
    ></textarea>
    <div class="input-footer">
      <span class="char-count" :class="{ 'near-limit': problemText.length > maxLength * 0.9 }">
        {{ problemText.length }} / {{ maxLength }}
      </span>
      <button
        class="submit-btn"
        :disabled="!isValid || loading"
        @click="submit"
      >
        <span v-if="loading" class="spinner"></span>
        <span v-else>Get Recommendations</span>
      </button>
    </div>
    <p v-if="error" class="error-message">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const props = defineProps<{
  loading?: boolean;
}>();

const emit = defineEmits<{
  submit: [problem: string];
}>();

const problemText = ref('');
const maxLength = 2000;

const isValid = computed(() => problemText.value.trim().length > 0);
const error = computed(() => {
  if (problemText.value.trim().length === 0 && problemText.value.length > 0) {
    return 'Please enter a problem description';
  }
  return '';
});

function submit() {
  if (isValid.value && !props.loading) {
    emit('submit', problemText.value.trim());
  }
}
</script>

<style scoped>
.problem-input {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.input-label {
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
}

.input-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 1rem;
  line-height: 1.5;
  resize: vertical;
  min-height: 100px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.5rem;
}

.char-count {
  font-size: 0.75rem;
  color: #6b7280;
}

.char-count.near-limit {
  color: #f59e0b;
  font-weight: 600;
}

.submit-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background-color: #2563eb;
}

.submit-btn:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}

.spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid transparent;
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-message {
  color: #dc2626;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}
</style>
