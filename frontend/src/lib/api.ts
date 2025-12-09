import axios from 'axios';
import { StoryRequest, Story } from '@/types/story';

// ✅ FIX: API_BASE_URL đã có /api/v1
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,  // ← Đã có /api/v1
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
    const response = await api.get<Story[]>('/stories/', { params:  { limit } });
    return response.data;
  },
};

export default api;


// ========================================
// PROGRESSIVE GENERATION APIs (NEW)
// ========================================

export interface StoryProgress {
  story_id:  string;
  title: string;
  status: 'generating' | 'completed' | 'failed';
  progress: {
    completed: number;
    total: number;
    percentage: number;
  };
  scenes:  any[];
  estimated_time_remaining?:  number;
  error_message?:  string;
}

export interface StoryGenerationStart {
  story_id: string;
  title: string;
  status: 'generating';
  progress: {
    completed: number;
    total: number;
    percentage:  number;
  };
  scenes: any[];
  message: string;
  poll_url:  string;
}

/**
 * API 2: Lấy progress của story đang tạo. 
 * 
 * ✅ FIX: Dùng API_BASE_URL (đã có /api/v1)
 */
export async function getStoryProgress(storyId:  string): Promise<StoryProgress> {
  // ✅ ĐÚNG: API_BASE_URL đã có /api/v1
  const response = await fetch(`${API_BASE_URL}/stories/${storyId}/progress`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get progress' }));
    throw new Error(error.detail || 'Failed to get progress');
  }
  
  return response.json();
}