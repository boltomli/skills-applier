import { ref, computed } from 'vue';
import axios from 'axios';
import type { Skill } from '@/types/skill';

const API_BASE = '/.netlify/functions';

export function useSkillStats() {
  const skills = ref<Skill[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Stats from API
  const totalCount = ref(0);
  const categoriesFromApi = ref<Record<string, number>>({});
  const typeGroupsFromApi = ref<Record<string, number>>({});

  const skillCount = computed(() => totalCount.value);

  const categoryStats = computed(() => {
    return Object.entries(categoriesFromApi.value)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
  });

  const typeGroupStats = computed(() => {
    const stats: Record<string, number> = {};
    Object.entries(typeGroupsFromApi.value).forEach(([key, count]) => {
      const label = key === 'problem_solving' ? 'Problem Solving' : 'Programming';
      stats[label] = (stats[label] || 0) + count;
    });
    return Object.entries(stats);
  });

  async function fetchStats() {
    loading.value = true;
    error.value = null;

    try {
      const response = await axios.get(`${API_BASE}/get-skills?stats_only=true`);
      totalCount.value = response.data.total || 0;
      categoriesFromApi.value = response.data.categories || {};
      typeGroupsFromApi.value = response.data.type_groups || {};
    } catch (err) {
      console.error('Failed to fetch stats:', err);
      error.value = 'Failed to load skill statistics';
    } finally {
      loading.value = false;
    }
  }

  async function fetchSkills(page: number = 1, limit: number = 100) {
    loading.value = true;
    error.value = null;

    try {
      const response = await axios.get(`${API_BASE}/get-skills?page=${page}&limit=${limit}&exclude_source=true`);
      skills.value = response.data.skills || [];
      totalCount.value = response.data.pagination?.total || 0;
      return response.data.pagination;
    } catch (err) {
      console.error('Failed to fetch skills:', err);
      error.value = 'Failed to load skills';
      skills.value = [];
      return null;
    } finally {
      loading.value = false;
    }
  }

  // Fetch all skills using pagination (for LLM recommendations)
  async function fetchAllSkills(): Promise<Skill[]> {
    const allSkills: Skill[] = [];
    let page = 1;
    const limit = 500;
    let hasMore = true;

    while (hasMore) {
      try {
        const response = await axios.get(`${API_BASE}/get-skills?page=${page}&limit=${limit}&exclude_source=true`);
        const skills = response.data.skills || [];
        allSkills.push(...skills);

        const pagination = response.data.pagination;
        hasMore = pagination?.has_next || false;
        page++;
      } catch (err) {
        console.error(`Failed to fetch skills page ${page}:`, err);
        break;
      }
    }

    return allSkills;
  }

  return {
    skills,
    skillCount,
    categoryStats,
    typeGroupStats,
    loading,
    error,
    fetchStats,
    fetchSkills,
    fetchAllSkills
  };
}
