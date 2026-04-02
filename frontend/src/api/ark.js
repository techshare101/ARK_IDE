const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ArkAPI {
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
  async createProject(goal) {
    return this.request('POST', '/api/projects', { goal });
  }

  async listProjects() {
    return this.request('GET', '/api/projects');
  }

  async getProject(id) {
    return this.request('GET', `/api/projects/${id}`);
  }

  async runPipeline(id) {
    return this.request('POST', `/api/projects/${id}/run`);
  }

  async getFiles(id) {
    return this.request('GET', `/api/projects/${id}/files`);
  }

  async getTests(id) {
    return this.request('GET', `/api/projects/${id}/tests`);
  }

  async getDeploy(id) {
    return this.request('GET', `/api/projects/${id}/deploy`);
  }

  async approveAction(id, actionId, approved) {
    return this.request('POST', `/api/projects/${id}/approve`, { action_id: actionId, approved });
  }

  async deleteProject(id) {
    return this.request('DELETE', `/api/projects/${id}`);
  }

  async health() {
    return this.request('GET', '/health');
  }

  // SSE stream URL
  getStreamUrl(id) {
    return `${API_BASE}/api/projects/${id}/stream`;
  }
}

export const arkAPI = new ArkAPI();
export default arkAPI;
