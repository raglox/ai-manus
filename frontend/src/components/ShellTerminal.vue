<template>
  <div class="shell-terminal-container flex flex-col h-full w-full">
    <!-- Terminal Header -->
    <div
      class="h-[36px] flex items-center px-3 w-full bg-[var(--background-gray-main)] border-b border-[var(--border-main)] rounded-t-[12px] shadow-[inset_0px_1px_0px_0px_#FFFFFF] dark:shadow-[inset_0px_1px_0px_0px_#FFFFFF30]">
      <div class="flex-1 flex items-center justify-center">
        <div class="max-w-[250px] truncate text-[var(--text-tertiary)] text-sm font-medium text-center">
          {{ shellSessionId || 'Terminal' }}
        </div>
      </div>
      <div class="flex items-center gap-2">
        <!-- Connection Status -->
        <div class="flex items-center gap-1">
          <div 
            class="w-2 h-2 rounded-full"
            :class="isConnected ? 'bg-green-500' : 'bg-red-500'"
          />
          <span class="text-xs text-[var(--text-tertiary)]">
            {{ isConnected ? 'Connected' : 'Disconnected' }}
          </span>
        </div>
        <!-- Clear Button -->
        <button
          @click="clearTerminal"
          class="text-xs px-2 py-1 rounded hover:bg-[var(--fill-tsp-gray-main)] text-[var(--text-tertiary)]"
          title="Clear terminal"
        >
          Clear
        </button>
      </div>
    </div>

    <!-- Terminal Content -->
    <div 
      ref="terminalContainer" 
      class="flex-1 min-h-0 w-full bg-[#1e1e1e] overflow-hidden"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebLinksAddon } from 'xterm-addon-web-links';
import { ToolContent } from '@/types/message';
import { useAgentStream } from '@/composables/useAgentStream';
import 'xterm/css/xterm.css';

const props = defineProps<{
  sessionId: string;
  toolContent?: ToolContent;
  live?: boolean;
  enableInput?: boolean; // Enable interactive input (for intervention)
}>();

const emit = defineEmits<{
  (e: 'command', command: string): void;
}>();

// Terminal instance and addons
const terminalContainer = ref<HTMLDivElement | null>(null);
let terminal: Terminal | null = null;
let fitAddon: FitAddon | null = null;
let webLinksAddon: WebLinksAddon | null = null;

// State
const isConnected = ref(false);
const currentLine = ref('');

// Get shell session ID from toolContent
const shellSessionId = computed(() => {
  if (props.toolContent && props.toolContent.args?.id) {
    return props.toolContent.args.id;
  }
  return props.toolContent?.tool_call_id || '';
});

// Connect to agent stream for real-time updates
const { isConnected: streamConnected, on } = useAgentStream();

// Initialize terminal
const initTerminal = () => {
  if (!terminalContainer.value) return;

  // Create terminal instance
  terminal = new Terminal({
    cursorBlink: true,
    cursorStyle: 'block',
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    fontSize: 13,
    lineHeight: 1.2,
    theme: {
      background: '#1e1e1e',
      foreground: '#d4d4d4',
      cursor: '#d4d4d4',
      black: '#000000',
      red: '#cd3131',
      green: '#0dbc79',
      yellow: '#e5e510',
      blue: '#2472c8',
      magenta: '#bc3fbc',
      cyan: '#11a8cd',
      white: '#e5e5e5',
      brightBlack: '#666666',
      brightRed: '#f14c4c',
      brightGreen: '#23d18b',
      brightYellow: '#f5f543',
      brightBlue: '#3b8eea',
      brightMagenta: '#d670d6',
      brightCyan: '#29b8db',
      brightWhite: '#e5e5e5',
    },
    allowTransparency: false,
    scrollback: 10000,
    convertEol: true,
  });

  // Create and load addons
  fitAddon = new FitAddon();
  webLinksAddon = new WebLinksAddon();
  
  terminal.loadAddon(fitAddon);
  terminal.loadAddon(webLinksAddon);

  // Open terminal in container
  terminal.open(terminalContainer.value);
  
  // Fit terminal to container
  fitAddon.fit();

  // Handle user input if enabled
  if (props.enableInput) {
    terminal.onData((data) => {
      handleTerminalInput(data);
    });
  }

  // Handle window resize
  window.addEventListener('resize', handleResize);

  isConnected.value = true;
};

// Handle terminal input
const handleTerminalInput = (data: string) => {
  if (!terminal || !props.enableInput) return;

  // Handle special keys
  if (data === '\r') {
    // Enter key - send command
    terminal.write('\r\n');
    if (currentLine.value.trim()) {
      emit('command', currentLine.value);
      currentLine.value = '';
    }
  } else if (data === '\u0003') {
    // Ctrl+C - send interrupt
    terminal.write('^C\r\n');
    emit('command', '\u0003'); // Send Ctrl+C signal
    currentLine.value = '';
  } else if (data === '\u007F') {
    // Backspace
    if (currentLine.value.length > 0) {
      currentLine.value = currentLine.value.slice(0, -1);
      terminal.write('\b \b');
    }
  } else {
    // Regular character
    currentLine.value += data;
    terminal.write(data);
  }
};

// Write to terminal
const writeToTerminal = (data: string) => {
  if (!terminal) return;
  terminal.write(data);
};

// Write output from shell command
const writeOutput = (output: string) => {
  if (!terminal) return;
  
  // Ensure proper line endings
  const formattedOutput = output.replace(/\n/g, '\r\n');
  terminal.write(formattedOutput);
};

// Clear terminal
const clearTerminal = () => {
  if (!terminal) return;
  terminal.clear();
};

// Handle terminal resize
const handleResize = () => {
  if (fitAddon && terminal) {
    fitAddon.fit();
  }
};

// Load shell content from toolContent
const loadShellContent = () => {
  if (!props.toolContent?.content?.console) return;
  
  clearTerminal();
  
  const console = props.toolContent.content.console;
  for (const entry of console) {
    if (terminal) {
      // Write prompt in green
      terminal.write(`\x1b[32m${entry.ps1}\x1b[0m `);
      // Write command
      terminal.write(`${entry.command}\r\n`);
      // Write output
      if (entry.output) {
        terminal.write(entry.output.replace(/\n/g, '\r\n'));
      }
      terminal.write('\r\n');
    }
  }
};

// Subscribe to real-time shell events
const subscribeToShellEvents = () => {
  // Listen for tool call events (shell commands)
  on('TOOL_CALL', (event: any) => {
    if (!props.live || !terminal) return;
    
    const tool = event.tool;
    if (tool?.name === 'shell' || tool?.function?.startsWith('shell_')) {
      // Write command to terminal
      if (tool.args?.command) {
        terminal.write(`\x1b[32m$\x1b[0m ${tool.args.command}\r\n`);
      }
    }
  });

  // Listen for observations (command output)
  on('OBSERVATION', (event: any) => {
    if (!props.live || !terminal) return;
    
    if (event.output) {
      writeOutput(event.output);
    }
  });
};

// Watch for tool content changes
watch(() => props.toolContent, () => {
  if (!props.live) {
    loadShellContent();
  }
}, { deep: true });

// Watch for live mode changes
watch(() => props.live, (isLive) => {
  if (isLive) {
    subscribeToShellEvents();
  }
});

// Watch for stream connection
watch(streamConnected, (connected) => {
  isConnected.value = connected;
});

// Initialize on mount
onMounted(() => {
  initTerminal();
  
  if (props.live) {
    subscribeToShellEvents();
  } else if (props.toolContent) {
    loadShellContent();
  }
});

// Cleanup on unmount
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  
  if (terminal) {
    terminal.dispose();
    terminal = null;
  }
  
  fitAddon = null;
  webLinksAddon = null;
});

// Expose methods
defineExpose({
  writeToTerminal,
  writeOutput,
  clearTerminal,
  loadContent: loadShellContent,
});
</script>

<style scoped>
.shell-terminal-container {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
}

/* Ensure xterm terminal fills container */
:deep(.xterm) {
  height: 100%;
  padding: 8px;
}

:deep(.xterm-viewport) {
  overflow-y: auto;
}
</style>
