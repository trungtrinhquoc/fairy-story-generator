'use client';

import { useState, useEffect, useRef } from 'react';
import { getStoryProgress } from '@/lib/api';

export function useStoryPolling(storyId:  string | null) {
  const [progress, setProgress] = useState<any>(null);
  const [scenes, setScenes] = useState<any[]>([]);
  const [status, setStatus] = useState<'idle' | 'generating' | 'completed' | 'failed'>('idle');
  const [isPolling, setIsPolling] = useState(false);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);  // ✅ THÊM:  Track mount status
  
  const poll = async () => {
    if (!storyId || ! isMountedRef.current) return;  // ✅ Check mounted
    
    try {
      const data = await getStoryProgress(storyId);
      
      // ✅ Chỉ update nếu component vẫn mounted
      if (! isMountedRef.current) return;
      
      setProgress(data.progress);
      setScenes(data.scenes);
      setStatus(data.status as any);
      
      // ✅ Dừng polling khi completed/failed
      if (data.status === 'completed' || data. status === 'failed') {
        stopPolling();
      }
    } catch (err) {
      console.error('Poll error:', err);
      // ✅ KHÔNG stop polling khi lỗi network
    }
  };
  
  const startPolling = () => {
    if (! storyId || isPolling || intervalRef.current) return;  // ✅ Check interval exists
    
    console.log(`🔄 Start polling:  ${storyId}`);
    setIsPolling(true);
    
    // Poll ngay lần đầu
    poll();
    
    // Setup interval
    intervalRef.current = setInterval(poll, 2000);
  };
  
  const stopPolling = () => {
    console.log('⏸️ Stop polling');
    setIsPolling(false);
    
    if (intervalRef.current) {
      clearInterval(intervalRef. current);
      intervalRef.current = null;  // ✅ Set null
    }
  };
  
  // ✅ Effect chỉ chạy KHI storyId THAY ĐỔI
  useEffect(() => {
    if (storyId) {
      startPolling();
    }
    
    // Cleanup khi unmount HOẶC storyId thay đổi
    return () => {
      isMountedRef.current = false;  // ✅ Mark unmounted
      stopPolling();
    };
  }, [storyId]);  // ✅ ĐÚNG:  Chỉ dependency là storyId
  
  return { progress, scenes, status, isPolling };
}