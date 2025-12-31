import { useState } from 'react';
import { useStoryPolling } from './useStoryPolling';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export function useStoryGeneration() {
  const [storyId, setStoryId] = useState<string | null>(null);
  const [title, setTitle] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const polling = useStoryPolling(storyId);
  
  const generateStory = async (request: any) => {
    try {
      setIsGenerating(true);
      setError(null);
      
      console.log('📤 Calling API:  POST /api/v1/stories/generate');
      console.log('   Request:', request);
      
      const response = await fetch(`${API_BASE_URL}/api/v1/stories/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
      
      if (!response. ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate story');
      }
      
      const result = await response.json();
      
      console.log('✅ API Response:', result);
      console.log('   Story ID:', result.storyId);  // ✅ camelCase
      console.log('   Title:', result. title);
      console.log('   Scenes:', result.scenes?. length || 0);
      
      if (! result.scenes || result.scenes. length === 0) {
        console.error('❌ No scenes in response! ');
        throw new Error('Scene 1 not returned from API');
      }
      
      // ✅ Check camelCase fields
      console.log('   Scene 1 image:', result.scenes[0]?.imageUrl);  // ✅ camelCase
      console.log('   Scene 1 audio:', result.scenes[0]?.audioUrl);  // ✅ camelCase
      console.log('   Scene 1 text:', result.scenes[0]?. paragraphText?. substring(0, 50));  // ✅ camelCase
      
      setStoryId(result.storyId);  // ✅ camelCase
      setTitle(result.title);
      setIsGenerating(false);
      
    } catch (err: any) {
      console.error('❌ Generation error:', err);
      setError(err.message);
      setIsGenerating(false);
    }
  };
  
  const reset = () => {
    console.log('🔄 Reset story generation');
    setStoryId(null);
    setTitle(null);
    setIsGenerating(false);
    setError(null);
  };
  
  return {
    generateStory,
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