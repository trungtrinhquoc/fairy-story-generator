import axios from 'axios';
import { StoryRequest, Story } from '@/types/story';

const API_BASE_URL = process.env. NEXT_PUBLIC_API_URL || 'http://127.0. 0.1:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const storyApi = {
  async generateStory(request: StoryRequest): Promise<Story> {
    const response = await api.post<Story>('/stories/generate', request);
    return response.data;
  },

  async getStory(id: string): Promise<Story> {
    const response = await api.get<Story>(`/stories/${id}`);
    return response.data;
  },

  async listStories(limit: number = 10): Promise<Story[]> {
    const response = await api.get<Story[]>('/stories/', { params: { limit } });
    return response.data;
  },
};

export default api;