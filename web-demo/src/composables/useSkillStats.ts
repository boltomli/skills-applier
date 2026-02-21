import { ref, computed } from 'vue';
import axios from 'axios';
import type { Skill } from '@/types/skill';

const API_BASE = '/.netlify/functions';

export function useSkillStats() {
  const skills = ref<Skill[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const skillCount = computed(() => skills.value.length);

  const categoryStats = computed(() => {
    const stats: Record<string, number> = {};
    skills.value.forEach(skill => {
      const category = skill.category || 'Uncategorized';
      stats[category] = (stats[category] || 0) + 1;
    });
    // Sort by count descending and take top categories
    return Object.entries(stats)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
  });

  const typeGroupStats = computed(() => {
    const stats: Record<string, number> = {};
    skills.value.forEach(skill => {
      const typeGroup = skill.type_group === 'problem_solving' ? 'Problem Solving' : 'Programming';
      stats[typeGroup] = (stats[typeGroup] || 0) + 1;
    });
    return Object.entries(stats);
  });

  async function fetchSkills() {
    loading.value = true;
    error.value = null;

    try {
      const response = await axios.get(`${API_BASE}/get-skills`);
      skills.value = response.data.skills || [];
    } catch (err) {
      console.error('Failed to fetch skills:', err);
      error.value = 'Failed to load skill statistics';
      skills.value = [];
    } finally {
      loading.value = false;
    }
  }

  return {
    skills,
    skillCount,
    categoryStats,
    typeGroupStats,
    loading,
    error,
    fetchSkills
  };
}
