<template>
  <div class="error-display">
    <div class="error-icon">⚠️</div>
    <h4 class="error-title">Something went wrong</h4>
    <p class="error-message">{{ message }}</p>
    <button v-if="showRetry" class="retry-btn" @click="retry">
      Try Again
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  message: string;
  showRetry?: boolean;
}>();

const emit = defineEmits<{
  retry: [];
}>();

function retry() {
  emit('retry');
}
</script>

<style scoped>
.error-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  text-align: center;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 0.75rem;
}

.error-icon {
  font-size: 2rem;
  margin-bottom: 0.75rem;
}

.error-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #991b1b;
  margin: 0 0 0.5rem 0;
}

.error-message {
  font-size: 0.875rem;
  color: #b91c1c;
  margin: 0 0 1rem 0;
  line-height: 1.5;
}

.retry-btn {
  padding: 0.625rem 1.25rem;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.retry-btn:hover {
  background: #b91c1c;
}
</style>
