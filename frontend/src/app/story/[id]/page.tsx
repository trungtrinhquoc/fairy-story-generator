'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { storyApi } from '@/lib/api';
import { Story } from '@/types/story';
import { Play, Pause, ChevronLeft, ChevronRight, Home, BookOpen } from 'lucide-react';

export default function StoryViewer() {
  const params = useParams();
  const router = useRouter();
  const storyId = params.id as string;

  const [story, setStory] = useState<Story | null>(null);
  const [currentScene, setCurrentScene] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [loading, setLoading] = useState(true);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    loadStory();
  }, [storyId]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.load();
      setTimeout(() => {
        audioRef.current?.play().catch(e => {
          console.warn("Autoplay blocked or failed:", e); 
          setIsPlaying(false);
        });
        setIsPlaying(true);
      }, 100);
    }
  }, [currentScene]);

  const loadStory = async () => {
    try {
      const data = await storyApi.getStory(storyId);
      setStory(data);
    } catch (err) {
      console.error('Failed to load story:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayPause = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const nextScene = () => {
    if (story && currentScene < story.scenes.length - 1) {
      setCurrentScene(currentScene + 1);
    }
  };

  const prevScene = () => {
    if (currentScene > 0) {
      setCurrentScene(currentScene - 1);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-900 to-purple-900">
        <div className="text-white text-lg font-bold flex items-center gap-3">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
          Loading magic...
        </div>
      </div>
    );
  }

  if (!story) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-indigo-950">
        <div className="text-center">
          <h1 className="text-xl text-white font-bold mb-4">Story not found 😢</h1>
          <button onClick={() => router.push('/')} className="px-5 py-2 bg-white text-indigo-900 rounded-lg text-sm font-bold hover:bg-gray-100 transition">
            Go Home
          </button>
        </div>
      </div>
    );
  }

  const scene = story.scenes[currentScene];

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-slate-900 to-purple-950 flex flex-col">
      {/* Header */}
      <div className="bg-black/20 backdrop-blur-md border-b border-white/5">
        <div className="container mx-auto px-4 py-2 flex items-center justify-between">
          <button onClick={() => router.push('/')} className="flex items-center gap-1.5 text-white/70 hover:text-white transition text-xs font-medium">
            <Home className="w-3.5 h-3.5" />
            <span>Home</span>
          </button>
          <h1 className="text-sm sm:text-base font-bold text-white text-center flex-1 px-4 truncate tracking-tight">
            {story.title}
          </h1>
          <div className="text-white/40 text-[10px] font-mono bg-white/5 px-2 py-0.5 rounded">
            {currentScene + 1} / {story.scenes.length}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center p-4 sm:p-8">
        <div className="w-full max-w-5xl">
          <div className="bg-white rounded-xl shadow-2xl overflow-hidden border border-white/10">
            <div className="grid lg:grid-cols-2">
              {/* LEFT: Image */}
              <div className="relative bg-slate-50 flex items-center justify-center aspect-square lg:aspect-auto lg:h-[480px]">
                <img
                  src={scene.image_url}
                  alt={`Scene ${scene.scene_order}`}
                  className="w-full h-full object-cover lg:object-contain"
                />
                <div className="absolute bottom-2 left-2 bg-black/40 backdrop-blur-md text-white px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">
                  Scene {currentScene + 1}
                </div>
              </div>

              {/* RIGHT: Text & Controls - ĐÃ SỬA Ở ĐÂY */}
              <div className="flex flex-col p-6 sm:p-8 lg:h-[480px] bg-white">
                
                {/* 1. Phần văn bản: Sử dụng overflow-y-auto để có thể cuộn */}
                <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                  <div className="min-h-full flex flex-col items-center justify-center text-center">
                    <BookOpen className="w-6 h-6 text-indigo-200 mb-4 flex-shrink-0" />
                    <p className="text-base sm:text-lg lg:text-xl leading-relaxed text-slate-700 font-medium">
                      {scene.paragraph_text}
                    </p>
                  </div>
                </div>

                {/* 2. Phần Controls: Sử dụng flex-shrink-0 để không bị co lại khi text dài */}
                <div className="mt-6 pt-4 border-t border-slate-100 flex-shrink-0">
                  <div className="flex items-center justify-center gap-6 mb-5">
                    <button
                      onClick={prevScene}
                      disabled={currentScene === 0}
                      className="p-2 rounded-full text-slate-400 disabled:opacity-20 hover:bg-slate-50 hover:text-indigo-600 transition"
                    >
                      <ChevronLeft className="w-7 h-7" />
                    </button>

                    <button
                      onClick={handlePlayPause}
                      className="p-4 rounded-full bg-indigo-600 text-white hover:bg-indigo-700 transition shadow-lg active:scale-95"
                    >
                      {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6 ml-1" />}
                    </button>

                    <button
                      onClick={nextScene}
                      disabled={currentScene === story.scenes.length - 1}
                      className="p-2 rounded-full text-slate-400 disabled:opacity-20 hover:bg-slate-50 hover:text-indigo-600 transition"
                    >
                      <ChevronRight className="w-7 h-7" />
                    </button>
                  </div>

                  {/* Progress Dots */}
                  <div className="flex gap-2 justify-center">
                    {story.scenes.map((_, index) => (
                      <button
                        key={index}
                        onClick={() => setCurrentScene(index)}
                        className={`transition-all duration-300 ${
                          index === currentScene
                            ? 'w-8 h-1.5 bg-indigo-600 rounded-full'
                            : 'w-1.5 h-1.5 bg-slate-200 rounded-full hover:bg-slate-300'
                        }`}
                      />
                    ))}
                  </div>

                  {/* Narration Status */}
                  <div className="h-6 mt-4 flex justify-center items-center">
                    {isPlaying && (
                      <div className="flex justify-center items-center gap-2">
                        <span className="flex h-2 w-2 relative">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                        </span>
                        <p className="text-[10px] uppercase font-bold text-indigo-400 tracking-widest">
                          Narration Playing
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              {/* KẾT THÚC PHẦN SỬA */}
            </div>
          </div>
        </div>
      </div>

      {/* Audio Player */}
      {scene.audio_url && (
        <audio
          ref={audioRef}
          src={scene.audio_url}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onEnded={() => {
            setIsPlaying(false);
            if (currentScene < story.scenes.length - 1) {
              setTimeout(() => {
                setCurrentScene(currentScene + 1);
              }, 800);
            }
          }}
        />
      )}
    </div>
  );
}