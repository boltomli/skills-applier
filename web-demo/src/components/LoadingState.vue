<template>
  <div class="loading-state">
    <div class="spinner-container">
      <div class="spinner"></div>
    </div>
    <p class="loading-text">Analyzing your problem...</p>
    <p class="loading-subtext">Matching with available skills</p>
    <button v-if="showCancel" class="cancel-btn" @click="cancel">
      Cancel
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  showCancel?: boolean;
}>();

const emit = defineEmits<{
  cancel: [];
}>();

function cancel() {
  emit('cancel');
}
</script>

<style scoped>
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
}

.spinner-container {
  margin-bottom: 1.5rem;
}

.spinner {
  width: 3rem;
  height: 3rem;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 1.125rem;
  font-weight: 500;
  color: #111827;
  margin: 0 0 0.5rem 0;
}

.loading-subtext {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0 0 1.5rem 0;
}

.cancel-btn {
  padding: 0.5rem 1rem;
  background: white;
  color: #6b7280;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn:hover {
  background: #f3f4f6;
  color: #374151;
}
</style>
