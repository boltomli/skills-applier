<template>
  <div class="recommendation-list">
    <div class="list-header">
      <h3>Recommended Skills</h3>
      <span class="method-badge" :class="method">
        {{ method === 'llm' ? 'AI Powered' : 'Keyword Match' }}
      </span>
    </div>

    <div class="recommendations">
      <SkillCard
        v-for="(rec, index) in recommendations"
        :key="rec.skill_id"
        :recommendation="rec"
        :skill="rec.skill"
        :style="{ animationDelay: `${index * 100}ms` }"
        class="animated-card"
      />
    </div>

    <div class="list-footer">
      <p class="results-count">
        Found {{ recommendations.length }} relevant skill{{ recommendations.length !== 1 ? 's' : '' }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import SkillCard from './SkillCard.vue';
import type { SkillRecommendation } from '@/types/skill';

defineProps<{
  recommendations: SkillRecommendation[];
  method: 'llm' | 'keyword-matching';
}>();
</script>

<style scoped>
.recommendation-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
}

.list-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.method-badge {
  padding: 0.375rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.method-badge.llm {
  background: #dbeafe;
  color: #1e40af;
}

.method-badge.keyword-matching {
  background: #f3e8ff;
  color: #6b21a8;
}

.recommendations {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.animated-card {
  opacity: 0;
  transform: translateY(10px);
  animation: fadeInUp 0.4s ease forwards;
}

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.list-footer {
  padding-top: 0.75rem;
  border-top: 1px solid #e5e7eb;
}

.results-count {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
}
</style>
