const API_BASE_URL = process. env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface StoryGenerationRequest {
  child_name: string;
  prompt: string;
  story_length: 'short' | 'medium' | 'long';
  story_tone: 'gentle' | 'funny' | 'adventurous';
  theme?:  string;
  image_style?: string;
  voice?:  string;
}

export interface StoryProgressResponse {
  story_id: string;
  title: string;
  status: 'generating' | 'completed' | 'failed';
  progress: {
    completed: number;
    total: number;
    percentage: number;
  };
  scenes: any[];
  estimated_time_remaining?:  number;
  error_message?: string;
}

/**
 * Generate a new story
 */
export async function generateStory(request: StoryGenerationRequest) {
  console.log('🔗 API Call: POST /api/v1/stories/generate');
  console.log('   Request:', request);
  
  const response = await fetch(`${API_BASE_URL}/api/v1/stories/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON. stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    console.error('❌ API Error:', error);
    throw new Error(error.detail || 'Failed to generate story');
  }

  const data = await response.json();
  console.log('✅ API Response:', data);
  
  return data;
}

/**
 * Get story progress (for polling)
 */
export async function getStoryProgress(storyId: string): Promise<StoryProgressResponse> {
  console.log(`🔗 API Call: GET /api/v1/stories/${storyId}/progress`);
  
  const response = await fetch(`${API_BASE_URL}/api/v1/stories/${storyId}/progress`, {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    console.error(`❌ API Error: ${response.status} ${response.statusText}`);
    throw new Error(`Failed to fetch progress: ${response.statusText}`);
  }

  const data = await response.json();
  console.log(`✅ Progress:  ${data.progress?. completed}/${data.progress?.total} scenes`);
  
  return data;
}

/**
 * Get complete story
 */
export async function getStory(storyId: string) {
  console.log(`🔗 API Call: GET /api/v1/stories/${storyId}`);
  
  const response = await fetch(`${API_BASE_URL}/api/v1/stories/${storyId}`, {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    console.error(`❌ API Error: ${response.status} ${response.statusText}`);
    throw new Error('Story not found');
  }

  const data = await response.json();
  console.log('✅ Story loaded:', data. title);
  
  return data;
}

/**
 * List all stories
 */
export async function listStories(limit: number = 10) {
  console.log(`🔗 API Call: GET /api/v1/stories? limit=${limit}`);
  
  const response = await fetch(`${API_BASE_URL}/api/v1/stories?limit=${limit}`, {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    console.error(`❌ API Error: ${response.status} ${response. statusText}`);
    throw new Error('Failed to list stories');
  }

  const data = await response.json();
  console.log(`✅ Loaded ${data.length} stories`);
  
  return data;
}

export const storyApi = {
  generateStory,
  getStoryProgress,
  getStory,
  listStories,
};