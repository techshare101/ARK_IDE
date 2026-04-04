const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

class ArkAPI {
  constructor() {
    this.baseUrl = API_BASE;
  }

  async request(method, path, body = null) {
    const options = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (body) options.body = JSON.stringify(body);

    const response = await fetch(`${API_BASE}${path}`, options);
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
  }

  // Projects
  async createProject(goal, workspace_path = '/app') {
    return this.request('POST', '/api/projects/', { goal, workspace_path });
  }

  async createSession(userPrompt, workspacePath = '/app') {
    // Create project — pipeline auto-starts in the background
    const project = await this.createProject(userPrompt, workspacePath);
    const projectId = project.project_id || project.id;
    return { ...project, project_id: projectId };
  }

  async listProjects() {
    return this.request('GET', '/api/projects/');
  }

  async getProject(id) {
    return this.request('GET', `/api/projects/${id}`);
  }

  async cancelPipeline(id) {
    return this.request('POST', `/api/projects/${id}/cancel`);
  }

  async getFiles(id) {
    return this.request('GET', `/api/projects/${id}/files`);
  }

  async getTests(id) {
    const project = await this.getProject(id);
    return project.test_results ? [project.test_results] : [];
  }

  async getDeploy(id) {
    const project = await this.getProject(id);
    return project.deploy_info || null;
  }

  async approveAction(id, actionId, approved) {
    return this.request('POST', `/api/projects/${id}/approve`, { action_id: actionId, approved });
  }

  async deleteProject(id) {
    return this.request('DELETE', `/api/projects/${id}`);
  }

  async health() {
    return this.request('GET', '/api/health/');
  }

  async healthCheck() {
    return this.health();
  }

  // SSE stream URL (both casings for compatibility)
  getStreamUrl(id) {
    return `${API_BASE}/api/projects/${id}/stream`;
  }
  getStreamURL(id) {
    return this.getStreamUrl(id);
  }

  // Session aliases (session == project in ARK IDE)
  async getSession(id) {
    return this.getProject(id);
  }
  async executeSession(id) {
    // Pipeline auto-starts on project creation — this is a no-op
    return { status: 'running' };
  }

  // Workflow stubs (not yet implemented in backend)
  async listWorkflows() {
    return { workflows: [] };
  }
  async executeWorkflow(type) {
    throw new Error(`Workflow "${type}" not yet available`);
  }

  // Agent stubs (agents are internal to the pipeline, not externally assignable)
  async listAgents() {
    return { agents: [] };
  }
  async assignAgent(sessionId, role) {
    return { session_id: sessionId, role };
  }

  // Execution summary — derived from project detail
  async getExecutionSummary(id) {
    const project = await this.getProject(id);
    return { summary: project.summary || project.goal || null };
  }
}

export const arkAPI = new ArkAPI();
export const BACKEND_URL = API_BASE;
export default arkAPI;
