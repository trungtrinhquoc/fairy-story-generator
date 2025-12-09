'use client';

import { useState } from 'react';
import { useStoryPolling } from './useStoryPolling';

const API_BASE_URL = process.env. NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useStoryGeneration() {
  const [storyId, setStoryId] = useState<string | null>(null);
  const [title, setTitle] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // ✅ Hook chỉ poll KHI có storyId
  const polling = useStoryPolling(storyId);
  
  // ✅ Function (KHÔNG phải useEffect)
  const generateStory = async (request: any) => {
    try {
      setIsGenerating(true);
      setError(null);
      
      console.log('📤 Calling API 1:  POST /generate');
      
      // ✅ ĐÚNG URL
      const response = await fetch(`${API_BASE_URL}/api/v1/stories/generate`, {
        method: 'POST',
        headers:  { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
      
      if (! response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate');
      }
      
      const result = await response.json();
      
      console.log('✅ API 1 success:', result. story_id);
      
      // ✅ Set storyId → Trigger polling
      setStoryId(result.story_id);
      setTitle(result.title);
      
    } catch (err:  any) {
      console.error('❌ Generation error:', err);
      setError(err.message);
      setIsGenerating(false);
    }
  };
  
  const reset = () => {
    console.log('🔄 Reset');
    setStoryId(null);  // → Stop polling
    setTitle(null);
    setIsGenerating(false);
    setError(null);
  };
  
  return {
    generateStory,  // ← Function để component gọi
    storyId,
    title,
    scenes: polling.scenes,
    progress: polling.progress,
    status: polling.status,
    isGenerating:  isGenerating || polling.status === 'generating',
    error,
    reset,
  };
}