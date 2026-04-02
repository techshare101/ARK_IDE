import axios from 'axios';

// Fallback to window.location.origin if env var is not set
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || window.location.origin;
const API = `${BACKEND_URL}/api`;

// Add request interceptor for debugging
axios.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Response Error:', error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    return Promise.reject(error);
  }
);

export const arkAPI = {
  // Session management
  createSession: async (userPrompt, workspacePath = '/app') => {
    const response = await axios.post(`${API}/sessions`, {
      user_prompt: userPrompt,
      workspace_path: workspacePath
    });
    return response.data;
  },

  listSessions: async (limit = 50) => {
    const response = await axios.get(`${API}/sessions`, { params: { limit } });
    return response.data;
  },

  getSession: async (sessionId) => {
    const response = await axios.get(`${API}/sessions/${sessionId}`);
    return response.data;
  },

  executeSession: async (sessionId) => {
    const response = await axios.post(`${API}/sessions/${sessionId}/execute`);
    return response.data;
  },

  approveAction: async (sessionId, approved, modifiedArgs = null) => {
    const response = await axios.post(`${API}/sessions/${sessionId}/approve`, {
      approved,
      modified_args: modifiedArgs
    });
    return response.data;
  },

  // Tools
  listTools: async () => {
    const response = await axios.get(`${API}/tools`);
    return response.data;
  },

  // Workflows
  listWorkflows: async () => {
    const response = await axios.get(`${API}/workflows`);
    return response.data;
  },

  executeWorkflow: async (workflowType, context = '') => {
    const response = await axios.post(
      `${API}/workflows/${workflowType}/execute`,
      null,
      { params: { context } }
    );
    return response.data;
  },

  // Agents
  listAgents: async () => {
    const response = await axios.get(`${API}/agents`);
    return response.data;
  },

  assignAgent: async (sessionId, role) => {
    const response = await axios.post(
      `${API}/sessions/${sessionId}/assign-agent`,
      null,
      { params: { role } }
    );
    return response.data;
  },

  // Summary & Diff
  getExecutionSummary: async (sessionId) => {
    const response = await axios.get(`${API}/sessions/${sessionId}/summary`);
    return response.data;
  },

  getFileChanges: async (sessionId) => {
    const response = await axios.get(`${API}/sessions/${sessionId}/file-changes`);
    return response.data;
  },

  generateDiff: async (originalContent, newContent, filename) => {
    const response = await axios.post(`${API}/diff`, {
      original_content: originalContent,
      new_content: newContent,
      filename
    });
    return response.data;
  },

  // SSE stream URL
  getStreamURL: (sessionId) => `${API}/sessions/${sessionId}/stream`,
  
  // Health check
  healthCheck: async () => {
    try {
      const response = await axios.get(`${API}/`);
      return { healthy: true, data: response.data };
    } catch (error) {
      return { healthy: false, error: error.message };
    }
  }
};

// Export API base URL for debugging
export { BACKEND_URL, API };
