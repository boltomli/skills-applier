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

    <div class="card-footer">
      <button
        v-if="skill?.source_content"
        class="download-btn"
        @click="downloadMarkdown"
        title="Download original SKILL.md"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        Download SKILL.md
      </button>
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

function downloadMarkdown() {
  if (!props.skill?.source_content) return;

  const blob = new Blob([props.skill.source_content], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${props.skill.id || 'skill'}.md`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
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

.card-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.download-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  color: #374151;
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s;
}

.download-btn:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
}

.download-btn svg {
  flex-shrink: 0;
}
</style>
