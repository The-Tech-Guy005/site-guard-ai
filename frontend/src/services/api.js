const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
                      (import.meta.env.DEV ? '' : 'http://127.0.0.1:8000');

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function handleResponse(response) {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      errorData.detail || `API request failed with status ${response.status}`,
      response.status
    );
  }
  return response.json();
}

export const api = {
  async getDashboard() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard`);
      return await handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      throw error;
    }
  },

  async getEvents() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/events`);
      return await handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch events:', error);
      throw error;
    }
  },

  async getStats() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/stats`);
      return await handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      throw error;
    }
  },

  async getZones() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/zones`);
      return await handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch zones:', error);
      throw error;
    }
  },

  async getProgress() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/progress`);
      return await handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch progress:', error);
      throw error;
    }
  },

  async healthCheck() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      return await handleResponse(response);
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  },

  async uploadVideo(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${API_BASE_URL}/api/v1/recordings/upload`, {
        method: 'POST',
        body: formData,
      });
      
      return await handleResponse(response);
    } catch (error) {
      console.error('Failed to upload video:', error);
      throw error;
    }
  },

  async getCurrentDetections() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/current-detections`);
      return await handleResponse(response);
    } catch (error) {
      console.error('Failed to fetch current detections:', error);
      throw error;
    }
  },

  getStreamUrl() {
    return `${API_BASE_URL}/api/v1/stream`;
  }
};

export default api;