<template>
  <div class="skill-card" :class="{ 'high-confidence': recommendation.confidence >= 0.8 }">
    <div class="card-header">
      <h4 class="skill-name">{{ recommendation.skill_name }}</h4>
      <span class="confidence-badge" :class="confidenceClass">
        {{ Math.round(recommendation.confidence * 100) }}%
      </span>
    </div>

    <div class="skill-meta">
      <span v-if="skill?.category" class="category-tag">
        {{ formatCategory(skill.category) }}
      </span>
      <span v-if="skill?.type_group" class="type-tag">
        {{ skill.type_group === 'problem_solving' ? 'Problem Solving' : 'Programming' }}
      </span>
    </div>

    <p v-if="skill?.description" class="skill-description">
      {{ skill.description }}
    </p>

    <div class="recommendation-section">
      <h5>Why this skill?</h5>
      <p>{{ recommendation.reason }}</p>
    </div>

    <div v-if="recommendation.suggestions?.length" class="suggestions-section">
      <h5>Suggestions</h5>
      <ul>
        <li v-for="(suggestion, idx) in recommendation.suggestions" :key="idx">
          {{ suggestion }}
        </li>
      </ul>
    </div>

    <div v-if="skill?.tags?.length" class="tags-section">
      <span v-for="tag in skill.tags" :key="tag" class="tag">
        {{ tag }}
      </span>
    </div>

    <div v-if="skill?.use_cases?.length" class="use-cases-section">
      <h5>Use Cases</h5>
      <ul>
        <li v-for="(useCase, idx) in skill.use_cases.slice(0, 3)" :key="idx">
          {{ useCase }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { SkillRecommendation, Skill } from '@/types/skill';

const props = defineProps<{
  recommendation: SkillRecommendation;
  skill?: Skill;
}>();

const confidenceClass = computed(() => {
  const c = props.recommendation.confidence;
  if (c >= 0.8) return 'high';
  if (c >= 0.6) return 'medium';
  return 'low';
});

function formatCategory(category: string): string {
  return category
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
</script>

<style scoped>
.skill-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 1.25rem;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.skill-card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.skill-card.high-confidence {
  border-color: #3b82f6;
  background: #eff6ff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.skill-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
  flex: 1;
}

.confidence-badge {
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.confidence-badge.high {
  background: #d1fae5;
  color: #065f46;
}

.confidence-badge.medium {
  background: #dbeafe;
  color: #1e40af;
}

.confidence-badge.low {
  background: #fef3c7;
  color: #92400e;
}

.skill-meta {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

.category-tag,
.type-tag {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
}

.category-tag {
  background: #e0e7ff;
  color: #3730a3;
}

.type-tag {
  background: #fce7f3;
  color: #9d174d;
}

.skill-description {
  color: #4b5563;
  font-size: 0.875rem;
  line-height: 1.5;
  margin: 0 0 1rem 0;
}

.recommendation-section,
.suggestions-section,
.use-cases-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.recommendation-section h5,
.suggestions-section h5,
.use-cases-section h5 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 0.5rem 0;
}

.recommendation-section p {
  color: #4b5563;
  font-size: 0.875rem;
  line-height: 1.5;
  margin: 0;
}

.suggestions-section ul,
.use-cases-section ul {
  margin: 0;
  padding-left: 1.25rem;
}

.suggestions-section li,
.use-cases-section li {
  color: #4b5563;
  font-size: 0.875rem;
  line-height: 1.5;
  margin-bottom: 0.25rem;
}

.tags-section {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.tag {
  padding: 0.25rem 0.5rem;
  background: #f3f4f6;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  color: #6b7280;
}
</style>
