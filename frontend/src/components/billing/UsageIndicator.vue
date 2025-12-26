<template>
  <div class="usage-indicator">
    <div class="usage-header">
      <h3 class="usage-title">{{ title }}</h3>
      <span class="usage-count">
        {{ used }} / {{ formatLimit(limit) }} runs
      </span>
    </div>

    <div class="progress-container">
      <div 
        class="progress-bar"
        :style="{ width: `${percentage}%` }"
        :class="progressClass"
      >
        <span v-if="percentage > 10" class="progress-text">
          {{ Math.round(percentage) }}%
        </span>
      </div>
    </div>

    <div class="usage-footer">
      <span :class="statusClass">
        {{ statusIcon }} {{ statusText }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { formatRunsLimit } from '@/api/billing';

// Props
const props = withDefaults(defineProps<{
  used: number;
  limit: number;
  title?: string;
}>(), {
  title: 'Usage This Month'
});

// Computed
const percentage = computed(() => {
  if (props.limit <= 0) return 0;
  return Math.min(100, (props.used / props.limit) * 100);
});

const remaining = computed(() => {
  return Math.max(0, props.limit - props.used);
});

const progressClass = computed(() => {
  const pct = percentage.value;
  if (pct >= 100) return 'danger';
  if (pct >= 90) return 'danger';
  if (pct >= 75) return 'warning';
  return 'success';
});

const statusClass = computed(() => {
  const pct = percentage.value;
  if (pct >= 100) return 'status status-danger';
  if (pct >= 90) return 'status status-warning';
  return 'status status-success';
});

const statusIcon = computed(() => {
  const pct = percentage.value;
  if (pct >= 100) return '⚠️';
  if (pct >= 90) return '⚠️';
  return '✅';
});

const statusText = computed(() => {
  if (remaining.value === 0) {
    return 'Limit reached - Upgrade to continue';
  }
  if (percentage.value >= 90) {
    return `Only ${remaining.value} runs remaining`;
  }
  return `${remaining.value} runs remaining`;
});

const formatLimit = (limit: number) => formatRunsLimit(limit);
</script>

<style scoped>
.usage-indicator {
  background: var(--bg-card, #ffffff);
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 8px;
  padding: 1.5rem;
}

.usage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.usage-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary, #111827);
}

.usage-count {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary, #6b7280);
}

.progress-container {
  width: 100%;
  height: 24px;
  background: #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.progress-bar {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: width 0.5s ease, background-color 0.3s ease;
  border-radius: 12px;
  position: relative;
}

.progress-text {
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.progress-bar.success {
  background: linear-gradient(90deg, #10b981 0%, #059669 100%);
}

.progress-bar.warning {
  background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
}

.progress-bar.danger {
  background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
}

.usage-footer {
  display: flex;
  justify-content: flex-start;
}

.status {
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.status-success {
  color: #059669;
  background: #d1fae5;
}

.status-warning {
  color: #d97706;
  background: #fef3c7;
}

.status-danger {
  color: #dc2626;
  background: #fee2e2;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .usage-indicator {
    background: var(--bg-card-dark, #1f2937);
    border-color: var(--border-color-dark, #374151);
  }

  .usage-title {
    color: var(--text-primary-dark, #f9fafb);
  }

  .usage-count {
    color: var(--text-secondary-dark, #9ca3af);
  }

  .progress-container {
    background: #374151;
  }

  .status-success {
    color: #34d399;
    background: #064e3b;
  }

  .status-warning {
    color: #fbbf24;
    background: #78350f;
  }

  .status-danger {
    color: #f87171;
    background: #7f1d1d;
  }
}
</style>
