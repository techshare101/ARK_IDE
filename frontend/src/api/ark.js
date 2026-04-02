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
    return this.request('POST', '/projects/', { goal, workspace_path });
  }

  async createSession(userPrompt, workspacePath = '/app') {
    // Create project and auto-start pipeline
    const project = await this.createProject(userPrompt, workspacePath);
    const projectId = project.project_id || project.id;
    
    // Immediately trigger the pipeline
    await this.runPipeline(projectId);
    
    return { ...project, project_id: projectId };
  }

  async listProjects() {
    return this.request('GET', '/projects/');
  }

  async getProject(id) {
    return this.request('GET', `/projects/${id}`);
  }

  async runPipeline(id) {
    return this.request('POST', `/projects/${id}/run`);
  }

  async getFiles(id) {
    return this.request('GET', `/projects/${id}/files`);
  }

  async getTests(id) {
    return this.request('GET', `/projects/${id}/tests`);
  }

  async getDeploy(id) {
    return this.request('GET', `/projects/${id}/deploy`);
  }

  async approveAction(id, actionId, approved) {
    return this.request('POST', `/projects/${id}/approve`, { action_id: actionId, approved });
  }

  async deleteProject(id) {
    return this.request('DELETE', `/projects/${id}`);
  }

  async health() {
    return this.request('GET', '/health');
  }

  async healthCheck() {
    return this.health();
  }

  // SSE stream URL
  getStreamUrl(id) {
    return `${API_BASE}/projects/${id}/stream`;
  }
}

export const arkAPI = new ArkAPI();
export const BACKEND_URL = API_BASE;
export default arkAPI;
