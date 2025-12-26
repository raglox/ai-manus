<template>
  <div v-if="message.type === 'user'" class="flex w-full flex-col items-end justify-end gap-1 group mt-3">
    <div class="flex items-end">
      <div class="flex items-center justify-end gap-[2px] invisible group-hover:visible">
        <div class="float-right transition text-[12px] text-[var(--text-tertiary)] invisible group-hover:visible">
          {{ relativeTime(message.content.timestamp) }}
        </div>
      </div>
    </div>
    <div class="flex max-w-[90%] relative flex-col gap-2 items-end">
      <div
        class="relative flex items-center rounded-[12px] overflow-hidden bg-[var(--fill-white)] dark:bg-[var(--fill-tsp-white-main)] p-3 ltr:rounded-br-none rtl:rounded-bl-none border border-[var(--border-main)] dark:border-0"
        v-html="renderMarkdown(messageContent.content)">
      </div>
    </div>
  </div>
  <div v-else-if="message.type === 'assistant'" class="flex flex-col gap-2 w-full group mt-3">
    <div class="flex items-center justify-between h-7 group">
      <div class="flex items-center gap-[3px]">
        <Bot :size="24" class="w-6 h-6" />
        <ManusTextIcon />
      </div>
      <div class="flex items-center gap-[2px] invisible group-hover:visible">
        <div class="float-right transition text-[12px] text-[var(--text-tertiary)] invisible group-hover:visible">
          {{ relativeTime(message.content.timestamp) }}
        </div>
      </div>
    </div>
    
    <!-- Agent Thoughts Section (Reflexion) -->
    <div 
      v-if="messageContent.reflection || messageContent.thinking"
      class="mb-2 border border-yellow-500/30 dark:border-yellow-400/30 rounded-lg overflow-hidden bg-yellow-50/50 dark:bg-yellow-900/10"
    >
      <div 
        @click="isThinkingExpanded = !isThinkingExpanded"
        class="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-yellow-100/50 dark:hover:bg-yellow-900/20 transition-colors"
      >
        <div class="flex items-center gap-2">
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            width="16" 
            height="16" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            stroke-width="2" 
            stroke-linecap="round" 
            stroke-linejoin="round"
            class="text-yellow-600 dark:text-yellow-400"
          >
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          </svg>
          <span class="text-sm font-medium text-yellow-800 dark:text-yellow-300">
            💭 Agent Thoughts
          </span>
          <span class="text-xs text-yellow-600/70 dark:text-yellow-400/70">
            ({{ messageContent.reflection ? 'Reflecting' : 'Thinking' }})
          </span>
        </div>
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          width="20" 
          height="20" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          stroke-width="2" 
          stroke-linecap="round" 
          stroke-linejoin="round"
          class="transition-transform duration-300 text-yellow-600 dark:text-yellow-400"
          :class="{ 'rotate-180': isThinkingExpanded }"
        >
          <path d="m6 9 6 6 6-6"/>
        </svg>
      </div>
      <div 
        class="px-3 pb-3 text-sm text-yellow-900 dark:text-yellow-100 transition-all duration-300 ease-in-out overflow-hidden"
        :class="{ 'max-h-[1000px] opacity-100': isThinkingExpanded, 'max-h-0 opacity-0 pb-0': !isThinkingExpanded }"
      >
        <div class="prose prose-sm dark:prose-invert prose-yellow max-w-none">
          <div v-html="renderMarkdown(messageContent.reflection || messageContent.thinking || '')"></div>
        </div>
      </div>
    </div>

    <!-- Main Message Content -->
    <div
      class="max-w-none p-0 m-0 prose prose-sm sm:prose-base dark:prose-invert [&_pre:not(.shiki)]:!bg-[var(--fill-tsp-white-light)] [&_pre:not(.shiki)]:text-[var(--text-primary)] text-base text-[var(--text-primary)]"
      v-html="renderMarkdown(messageContent.content)"></div>
  </div>
  <ToolUse v-else-if="message.type === 'tool'" :tool="toolContent" @click="handleToolClick(toolContent)" />
  <div v-else-if="message.type === 'step'" class="flex flex-col">
    <div class="text-sm w-full clickable flex gap-2 justify-between group/header truncate text-[var(--text-primary)]"
      data-event-id="HNtP7XOMUOhPemItd2EkK2">
      <div class="flex flex-row gap-2 justify-center items-center truncate">
        <div v-if="stepContent.status !== 'completed'"
          class="w-4 h-4 flex-shrink-0 flex items-center justify-center border border-[var(--border-dark)] rounded-[15px]">
        </div>
        <div v-else
          class="w-4 h-4 flex-shrink-0 flex items-center justify-center border-[var(--border-dark)] rounded-[15px] bg-[var(--text-disable)] dark:bg-[var(--fill-tsp-white-dark)] border-0">
          <CheckIcon class="text-[var(--icon-white)] dark:text-[var(--icon-white-tsp)]" :size="10" />
        </div>
        <div class="truncate font-medium markdown-content"
          v-html="stepContent.description ? renderMarkdown(stepContent.description) : ''">
        </div>
        <span class="flex-shrink-0 flex" @click="isExpanded = !isExpanded;">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
            class="lucide lucide-chevron-down transition-transform duration-300 w-4 h-4"
            :class="{ 'rotate-180': isExpanded }">
            <path d="m6 9 6 6 6-6"></path>
          </svg>
        </span>
      </div>
      <div class="float-right transition text-[12px] text-[var(--text-tertiary)] invisible group-hover/header:visible">
        {{ relativeTime(message.content.timestamp) }}
      </div>
    </div>
    <div class="flex">
      <div class="w-[24px] relative">
        <div class="border-l border-dashed border-[var(--border-dark)] absolute start-[8px] top-0 bottom-0"
          style="height: calc(100% + 14px);"></div>
      </div>
      <div
        class="flex flex-col gap-3 flex-1 min-w-0 overflow-hidden pt-2 transition-[max-height,opacity] duration-150 ease-in-out"
        :class="{ 'max-h-[100000px] opacity-100': isExpanded, 'max-h-0 opacity-0': !isExpanded }">
        <ToolUse v-for="(tool, index) in stepContent.tools" :key="index" :tool="tool" @click="handleToolClick(tool)" />
      </div>
    </div>
  </div>
  <AttachmentsMessage v-else-if="message.type === 'attachments'" :content="attachmentsContent"/>
</template>

<script setup lang="ts">
import ManusTextIcon from './icons/ManusTextIcon.vue';
import { Message, MessageContent, AttachmentsContent } from '../types/message';
import ToolUse from './ToolUse.vue';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { CheckIcon } from 'lucide-vue-next';
import { computed, ref } from 'vue';
import { ToolContent, StepContent } from '../types/message';
import { useRelativeTime } from '../composables/useTime';
import { Bot } from 'lucide-vue-next';
import AttachmentsMessage from './AttachmentsMessage.vue';


const props = defineProps<{
  message: Message;
  sessionId?: string;
}>();

const emit = defineEmits<{
  (e: 'toolClick', tool: ToolContent): void;
}>();

const handleToolClick = (tool: ToolContent) => {
  emit('toolClick', tool);
};

// For backward compatibility, provide the original computed properties
const stepContent = computed(() => props.message.content as StepContent);
const messageContent = computed(() => props.message.content as MessageContent);
const toolContent = computed(() => props.message.content as ToolContent);
const attachmentsContent = computed(() => props.message.content as AttachmentsContent);

// Control content expand/collapse state
const isExpanded = ref(true);
const isThinkingExpanded = ref(true); // Reflexion section expanded by default

const { relativeTime } = useRelativeTime();

// Render Markdown to HTML and sanitize
const renderMarkdown = (text: string) => {
  if (typeof text !== 'string') return '';
  const html = marked(text) as string;
  return DOMPurify.sanitize(html);
};
</script>

<style>
.duration-300 {
  animation-duration: .3s;
}

.duration-300 {
  transition-duration: .3s;
}
</style>
