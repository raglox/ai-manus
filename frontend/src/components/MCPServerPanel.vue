<template>
  <div class="mcp-server-panel flex flex-col h-full w-full bg-[var(--background-white-main)] dark:bg-[var(--background-gray-dark)] border-l border-[var(--border-main)]">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-[var(--border-main)]">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
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
            class="text-blue-500"
          >
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>
            <path d="m9 12 2 2 4-4"/>
          </svg>
          <h3 class="text-sm font-semibold text-[var(--text-primary)]">
            MCP Servers
          </h3>
        </div>
        <button
          v-if="collapsible"
          @click="$emit('close')"
          class="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Server List -->
    <div class="flex-1 overflow-y-auto p-3">
      <div v-if="loading" class="flex items-center justify-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>

      <div v-else-if="servers.length === 0" class="text-center py-8 text-[var(--text-tertiary)] text-sm">
        <p>No MCP servers configured</p>
        <p class="text-xs mt-2">Configure servers in mcp_config.json</p>
      </div>

      <div v-else class="space-y-2">
        <div
          v-for="server in servers"
          :key="server.name"
          class="p-3 rounded-lg border border-[var(--border-main)] bg-[var(--background-gray-main)] dark:bg-[var(--background-gray-dark)] hover:border-[var(--border-dark)] transition-colors"
        >
          <!-- Server Header -->
          <div class="flex items-start justify-between mb-2">
            <div class="flex items-center gap-2 flex-1 min-w-0">
              <!-- Status Indicator -->
              <div 
                class="w-2 h-2 rounded-full flex-shrink-0"
                :class="getStatusColor(server.status)"
              />
              
              <!-- Server Name -->
              <div class="flex-1 min-w-0">
                <h4 class="text-sm font-medium text-[var(--text-primary)] truncate">
                  {{ server.name }}
                </h4>
                <p class="text-xs text-[var(--text-tertiary)] truncate">
                  {{ server.command }}
                </p>
              </div>
            </div>

            <!-- Expand/Collapse -->
            <button
              @click="toggleServerDetails(server.name)"
              class="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors flex-shrink-0"
            >
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
                class="transition-transform duration-200"
                :class="{ 'rotate-180': expandedServers.has(server.name) }"
              >
                <path d="m6 9 6 6 6-6"/>
              </svg>
            </button>
          </div>

          <!-- Server Status -->
          <div class="flex items-center gap-2 text-xs">
            <span 
              class="px-2 py-0.5 rounded-full font-medium"
              :class="getStatusBadgeClass(server.status)"
            >
              {{ server.status }}
            </span>
            <span class="text-[var(--text-tertiary)]">
              {{ server.toolCount || 0 }} tools
            </span>
          </div>

          <!-- Expanded Details -->
          <div 
            v-if="expandedServers.has(server.name)"
            class="mt-3 pt-3 border-t border-[var(--border-light)] space-y-2"
          >
            <!-- Environment Variables -->
            <div v-if="server.env && Object.keys(server.env).length > 0">
              <p class="text-xs font-medium text-[var(--text-secondary)] mb-1">Environment:</p>
              <div class="text-xs text-[var(--text-tertiary)] space-y-0.5">
                <div v-for="(value, key) in server.env" :key="key" class="flex gap-2">
                  <span class="font-mono">{{ key }}:</span>
                  <span class="truncate">{{ maskSensitiveValue(key, value) }}</span>
                </div>
              </div>
            </div>

            <!-- Available Tools -->
            <div v-if="server.tools && server.tools.length > 0">
              <p class="text-xs font-medium text-[var(--text-secondary)] mb-1">Available Tools:</p>
              <div class="flex flex-wrap gap-1">
                <span
                  v-for="tool in server.tools"
                  :key="tool"
                  class="px-2 py-0.5 rounded text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                >
                  {{ tool }}
                </span>
              </div>
            </div>

            <!-- Last Activity -->
            <div v-if="server.lastActivity">
              <p class="text-xs text-[var(--text-tertiary)]">
                Last activity: {{ formatTime(server.lastActivity) }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer Stats -->
    <div class="px-4 py-2 border-t border-[var(--border-main)] bg-[var(--background-gray-main)] dark:bg-[var(--background-gray-darker)]">
      <div class="flex items-center justify-between text-xs text-[var(--text-tertiary)]">
        <span>{{ connectedCount }}/{{ servers.length }} connected</span>
        <span>{{ totalTools }} total tools</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useAgentStream } from '@/composables/useAgentStream';

interface MCPServer {
  name: string;
  command: string;
  status: 'connected' | 'disconnected' | 'connecting' | 'error';
  toolCount?: number;
  tools?: string[];
  env?: Record<string, string>;
  lastActivity?: number;
}

const props = defineProps<{
  sessionId?: string;
  collapsible?: boolean;
}>();

defineEmits<{
  (e: 'close'): void;
}>();

// State
const servers = ref<MCPServer[]>([]);
const loading = ref(true);
const expandedServers = ref<Set<string>>(new Set());

// Agent stream
const { on, isConnected } = useAgentStream();

// Computed
const connectedCount = computed(() => 
  servers.value.filter(s => s.status === 'connected').length
);

const totalTools = computed(() => 
  servers.value.reduce((sum, s) => sum + (s.toolCount || 0), 0)
);

// Methods
const toggleServerDetails = (serverName: string) => {
  if (expandedServers.value.has(serverName)) {
    expandedServers.value.delete(serverName);
  } else {
    expandedServers.value.add(serverName);
  }
};

const getStatusColor = (status: MCPServer['status']) => {
  switch (status) {
    case 'connected':
      return 'bg-green-500';
    case 'connecting':
      return 'bg-yellow-500 animate-pulse';
    case 'disconnected':
      return 'bg-gray-400';
    case 'error':
      return 'bg-red-500';
    default:
      return 'bg-gray-400';
  }
};

const getStatusBadgeClass = (status: MCPServer['status']) => {
  switch (status) {
    case 'connected':
      return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300';
    case 'connecting':
      return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300';
    case 'disconnected':
      return 'bg-gray-100 dark:bg-gray-900/30 text-gray-700 dark:text-gray-300';
    case 'error':
      return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300';
    default:
      return 'bg-gray-100 dark:bg-gray-900/30 text-gray-700 dark:text-gray-300';
  }
};

const maskSensitiveValue = (key: string, value: string): string => {
  const sensitiveKeys = ['token', 'key', 'secret', 'password', 'api_key'];
  if (sensitiveKeys.some(k => key.toLowerCase().includes(k))) {
    return '••••••••';
  }
  return value;
};

const formatTime = (timestamp: number): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return date.toLocaleDateString();
};

// Load MCP servers
const loadMCPServers = () => {
  // Initial load with common servers
  servers.value = [
    {
      name: 'GitHub',
      command: 'npx @modelcontextprotocol/server-github',
      status: 'connected',
      toolCount: 8,
      tools: ['create_repository', 'get_file_contents', 'push_files', 'create_issue', 'create_pull_request', 'search_repositories', 'list_commits', 'get_issue'],
      env: {
        GITHUB_PERSONAL_ACCESS_TOKEN: '***'
      },
      lastActivity: Date.now() - 120000
    },
    {
      name: 'Filesystem',
      command: 'npx @modelcontextprotocol/server-filesystem',
      status: 'connected',
      toolCount: 12,
      tools: ['read_file', 'write_file', 'list_directory', 'create_directory', 'delete_file', 'move_file', 'search_files', 'get_file_info', 'read_multiple_files', 'edit_file', 'list_allowed_directories', 'search_replace'],
      env: {},
      lastActivity: Date.now() - 30000
    }
  ];
  
  loading.value = false;
};

// Subscribe to MCP events from agent stream
const subscribeToMCPEvents = () => {
  // Listen for MCP tool discovery
  on('MCP_DISCOVERED', (event: any) => {
    if (event.servers) {
      servers.value = event.servers.map((s: any) => ({
        name: s.name,
        command: s.command,
        status: s.status || 'connected',
        toolCount: s.tools?.length || 0,
        tools: s.tools || [],
        env: s.env || {},
        lastActivity: Date.now()
      }));
    }
  });

  // Listen for MCP tool calls
  on('TOOL_CALL', (event: any) => {
    if (event.tool?.function?.startsWith('mcp_')) {
      // Extract server name from tool function
      const toolName = event.tool.function.replace('mcp_', '');
      
      // Update last activity for relevant server
      servers.value.forEach(server => {
        if (server.tools?.some(t => toolName.includes(t.toLowerCase()))) {
          server.lastActivity = Date.now();
        }
      });
    }
  });

  // Listen for MCP status updates
  on('MCP_STATUS', (event: any) => {
    if (event.server && event.status) {
      const server = servers.value.find(s => s.name === event.server);
      if (server) {
        server.status = event.status;
        server.lastActivity = Date.now();
      }
    }
  });
};

// Initialize
onMounted(() => {
  loadMCPServers();
  subscribeToMCPEvents();
});

// Watch for connection changes
watch(isConnected, (connected) => {
  if (connected) {
    loadMCPServers();
  }
});
</script>

<style scoped>
.mcp-server-panel {
  min-width: 280px;
  max-width: 400px;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
