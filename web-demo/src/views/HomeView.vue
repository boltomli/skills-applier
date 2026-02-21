<template>
  <div class="home-view">
    <header class="app-header">
      <h1>🔧 Skill Recommender</h1>
      <p class="subtitle">
        Describe your problem and get AI-powered skill recommendations
      </p>
    </header>

    <main class="main-content">
      <div class="content-stack">
        <!-- 可收起的模型配置 -->
        <section class="config-section">
          <button
            class="config-toggle"
            @click="isConfigExpanded = !isConfigExpanded"
          >
            <span class="toggle-icon">{{ isConfigExpanded ? '▼' : '▶' }}</span>
            <span class="toggle-text">LLM Configuration</span>
            <span class="config-status" :class="isConfigured ? 'configured' : 'fallback'">
              {{ isConfigured ? '✓ Configured' : 'Using keyword matching' }}
            </span>
          </button>
          <div v-show="isConfigExpanded" class="config-content">
            <LLMConfigPanel @saved="isConfigExpanded = false" />
          </div>
        </section>

        <!-- 问题输入 -->
        <section class="input-section">
          <ProblemInput
            :loading="loading"
            @submit="handleSubmit"
          />
        </section>

        <!-- 结果展示 -->
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
    </main>

    <footer class="app-footer">
      <div class="footer-content">
        <p class="footer-main">Powered by LLM + Skill Index</p>
        <div v-if="!skillStatsLoading" class="skill-stats">
          <span class="stat-item">
            <span class="stat-value">{{ skillCount }}</span>
            <span class="stat-label">skills available</span>
          </span>
          <span class="stat-divider">|</span>
          <span class="stat-categories">
            <span
              v-for="([category, count], index) in categoryStats"
              :key="category"
              class="category-tag"
            >
              {{ category }} ({{ count }}){{ index < categoryStats.length - 1 ? ', ' : '' }}
            </span>
          </span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import ProblemInput from '@/components/ProblemInput.vue';
import LoadingState from '@/components/LoadingState.vue';
import ErrorDisplay from '@/components/ErrorDisplay.vue';
import RecommendationList from '@/components/RecommendationList.vue';
import LLMConfigPanel from '@/components/LLMConfigPanel.vue';
import { useRecommendation } from '@/composables/useRecommendation';
import { useLLMConfig } from '@/composables/useLLMConfig';
import { useSkillStats } from '@/composables/useSkillStats';

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

const { skillCount, categoryStats, loading: skillStatsLoading, fetchSkills } = useSkillStats();

const hasSearched = ref(false);
const lastQuery = ref('');
const isConfigExpanded = ref(false);

onMounted(() => {
  fetchSkills();
});

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
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

.content-stack {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* 配置区域 */
.config-section {
  background: white;
  border-radius: 0.75rem;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.config-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  background: #f9fafb;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  color: #374151;
  transition: background-color 0.2s;
}

.config-toggle:hover {
  background: #f3f4f6;
}

.toggle-icon {
  font-size: 0.75rem;
  color: #6b7280;
}

.toggle-text {
  flex: 1;
  text-align: left;
}

.config-status {
  font-size: 0.8125rem;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-weight: 500;
}

.config-status.configured {
  background: #d1fae5;
  color: #065f46;
}

.config-status.fallback {
  background: #fef3c7;
  color: #92400e;
}

.config-content {
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

/* 输入和结果区域 */
.input-section,
.results-section {
  background: white;
  border-radius: 0.75rem;
  padding: 2rem;
  border: 1px solid #e5e7eb;
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

/* 页脚 */
.app-footer {
  background: white;
  border-top: 1px solid #e5e7eb;
  padding: 1rem 2rem;
}

.footer-content {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.footer-main {
  font-size: 0.875rem;
  color: #9ca3af;
  margin: 0;
}

.skill-stats {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  justify-content: center;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.stat-value {
  font-weight: 600;
  color: #3b82f6;
}

.stat-label {
  color: #6b7280;
  font-size: 0.875rem;
}

.stat-divider {
  color: #d1d5db;
}

.stat-categories {
  color: #6b7280;
  font-size: 0.875rem;
}

.category-tag {
  color: #6b7280;
}

/* Responsive design */
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

  .input-section,
  .results-section {
    padding: 1.5rem;
  }

  .config-toggle {
    padding: 0.875rem 1rem;
  }

  .config-content {
    padding: 1rem;
  }

  .skill-stats {
    flex-direction: column;
    gap: 0.5rem;
  }

  .stat-divider {
    display: none;
  }
}
</style>