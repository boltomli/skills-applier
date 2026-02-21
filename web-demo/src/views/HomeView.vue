<template>
  <div class="home-view">
    <header class="app-header">
      <h1>🔧 Skill Recommender</h1>
      <p class="subtitle">
        Describe your problem and get AI-powered skill recommendations
      </p>
    </header>

    <main class="main-content">
      <div class="content-grid">
        <div class="left-panel">
          <section class="input-section">
            <ProblemInput
              :loading="loading"
              @submit="handleSubmit"
            />
          </section>

          <section v-if="loading" class="results-section">
            <LoadingState
              :show-cancel="true"
              @cancel="handleCancel"
            />
          </section>

          <section v-else-if="error" class="results-section">
            <ErrorDisplay
              :message="error"
              :show-retry="true"
              @retry="handleRetry"
            />
          </section>

          <section v-else-if="hasRecommendations" class="results-section">
            <RecommendationList
              :recommendations="sortedRecommendations"
              :method="method"
            />
          </section>

          <section v-else-if="hasSearched" class="results-section">
            <div class="no-results">
              <p>No matching skills found for your problem.</p>
              <p class="hint">Try describing your problem differently or check your LLM configuration.</p>
            </div>
          </section>
        </div>

        <aside class="right-panel">
          <LLMConfigPanel />
        </aside>
      </div>
    </main>

    <footer class="app-footer">
      <p>Powered by LLM + Skill Index</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import ProblemInput from '@/components/ProblemInput.vue';
import LoadingState from '@/components/LoadingState.vue';
import ErrorDisplay from '@/components/ErrorDisplay.vue';
import RecommendationList from '@/components/RecommendationList.vue';
import LLMConfigPanel from '@/components/LLMConfigPanel.vue';
import { useRecommendation } from '@/composables/useRecommendation';
import { useLLMConfig } from '@/composables/useLLMConfig';

const { config, isConfigured } = useLLMConfig();
const {
  recommendations,
  sortedRecommendations,
  loading,
  error,
  method,
  hasRecommendations,
  getRecommendations,
  clearRecommendations
} = useRecommendation();

const hasSearched = ref(false);
const lastQuery = ref('');

async function handleSubmit(problem: string) {
  hasSearched.value = true;
  lastQuery.value = problem;
  await getRecommendations(problem, isConfigured.value ? config.value : null);
}

function handleCancel() {
  // In a real implementation, this would abort the axios request
  clearRecommendations();
  loading.value = false;
}

function handleRetry() {
  if (lastQuery.value) {
    handleSubmit(lastQuery.value);
  }
}
</script>

<style scoped>
.home-view {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f3f4f6;
}

.app-header {
  background: white;
  border-bottom: 1px solid #e5e7eb;
  padding: 1.5rem 2rem;
  text-align: center;
}

.app-header h1 {
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
  margin: 0 0 0.5rem 0;
}

.subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
}

.main-content {
  flex: 1;
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 2rem;
}

.left-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.input-section,
.results-section {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: 1px solid #e5e7eb;
}

.right-panel {
  position: sticky;
  top: 2rem;
  align-self: flex-start;
}

.no-results {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.no-results .hint {
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.app-footer {
  background: white;
  border-top: 1px solid #e5e7eb;
  padding: 1rem 2rem;
  text-align: center;
}

.app-footer p {
  font-size: 0.875rem;
  color: #9ca3af;
  margin: 0;
}

/* Responsive design */
@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .right-panel {
    position: static;
    order: -1;
  }
}

@media (max-width: 640px) {
  .main-content {
    padding: 1rem;
  }

  .app-header {
    padding: 1rem;
  }

  .app-header h1 {
    font-size: 1.5rem;
  }
}
</style>