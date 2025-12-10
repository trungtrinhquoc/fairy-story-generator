import { useState, useEffect, useRef } from 'react';
import { getStoryProgress } from '@/lib/api';

export function useStoryPolling(storyId: string | null) {
  const [progress, setProgress] = useState<any>(null);
  const [scenes, setScenes] = useState<any[]>([]);
  const [status, setStatus] = useState<'idle' | 'generating' | 'completed' | 'failed'>('idle');
  const [isPolling, setIsPolling] = useState(false);
  
  const intervalRef = useRef<NodeJS. Timeout | null>(null);
  const isMountedRef = useRef(true);
  const pollCountRef = useRef(0);
  const MAX_POLLS = 60; // 2 minutes max
  
  const poll = async () => {
    if (!storyId || !isMountedRef.current) return;
    
    pollCountRef.current += 1;
    
    if (pollCountRef.current > MAX_POLLS) {
      console.warn('⚠️ Max polls reached (60 polls = 2 minutes)');
      stopPolling();
      return;
    }
    
    try {
      console.log(`🔄 Poll ${pollCountRef.current}/${MAX_POLLS}:  ${storyId}`);
      
      const data = await getStoryProgress(storyId);
      
      console.log(`   Status: ${data.status}, Scenes: ${data.scenes?.length || 0}/${data.progress?.total || 0}`);
      
      if (! isMountedRef.current) return;
      
      setProgress(data. progress);
      setScenes(data.scenes || []);
      setStatus(data.status as any);
      
      if (data.status === 'completed' || data.status === 'failed') {
        console.log('🎉 Story completed/failed, stopping poll');
        stopPolling();
      }
    } catch (err) {
      console.error('❌ Poll error:', err);
    }
  };
  
  const startPolling = () => {
    if (! storyId || isPolling || intervalRef.current) return;
    
    console.log(`🚀 Start polling:  ${storyId}`);
    setIsPolling(true);
    pollCountRef.current = 0;
    
    // Poll immediately
    poll();
    
    // Then poll every 2s
    intervalRef.current = setInterval(poll, 2000);
  };
  
  const stopPolling = () => {
    console.log('⏸️ Stop polling');
    setIsPolling(false);
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };
  
  useEffect(() => {
    isMountedRef.current = true;
    
    if (storyId) {
      startPolling();
    }
    
    return () => {
      isMountedRef.current = false;
      stopPolling();
    };
  }, [storyId]);
  
  return { progress, scenes, status, isPolling };
}