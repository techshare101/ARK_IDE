import axios from 'axios';

// Keep consistent with existing API conventions
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || window.location.origin;
const API = `${BACKEND_URL}/api`;

export const todosAPI = {
  list: async () => {
    const response = await axios.get(`${API}/todos`);
    // backend returns: { todos: [...], count: n }
    return response.data?.todos ?? [];
  },

  create: async (payload) => {
    // payload: { title, description?, completed? }
    const response = await axios.post(`${API}/todos`, payload);
    // backend returns: { todo: {...} }
    return response.data?.todo;
  },

  get: async (id) => {
    const response = await axios.get(`${API}/todos/${id}`);
    return response.data?.todo;
  },

  update: async (id, payload) => {
    // backend uses PATCH and returns: { todo: {...} }
    const response = await axios.patch(`${API}/todos/${id}`, payload);
    return response.data?.todo;
  },

  remove: async (id) => {
    const response = await axios.delete(`${API}/todos/${id}`);
    return response.data;
  }
};

export { BACKEND_URL };
