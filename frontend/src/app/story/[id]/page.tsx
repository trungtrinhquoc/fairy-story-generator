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
    // Reset audio when scene changes
    if (audioRef.current) {
      audioRef.current.load();
      setTimeout(() => {
        audioRef.current?.play().catch(e => {
            // Thường là lỗi trình duyệt chặn autoplay
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
    if (! audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(! isPlaying);
  };

  const nextScene = () => {
    if (story && currentScene < story.scenes. length - 1) {
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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-600 to-pink-600">
        <div className="text-white text-2xl font-bold flex items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
          Loading story...
        </div>
      </div>
    );
  }

  if (!story) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-600 to-pink-600">
        <div className="text-center">
          <h1 className="text-3xl text-white font-bold mb-4">Story not found 😢</h1>
          <button
            onClick={() => router.push('/')}
            className="px-6 py-3 bg-white text-purple-600 rounded-lg font-bold hover:bg-purple-50"
          >
            Go Home
          </button>
        </div>
      </div>
    );
  }

  const scene = story.scenes[currentScene];

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex flex-col">
      {/* Header - Compact */}
      <div className="bg-black/30 backdrop-blur-sm border-b border-white/10">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <button
            onClick={() => router.push('/')}
            className="flex items-center gap-2 text-white/80 hover:text-white transition text-sm"
          >
            <Home className="w-4 h-4" />
            <span className="hidden sm:inline">Home</span>
          </button>
          <h1 className="text-lg sm:text-xl font-bold text-white text-center flex-1 px-4 truncate">
            {story.title}
          </h1>
          <div className="text-white/60 text-sm">
            {currentScene + 1}/{story.scenes.length}
          </div>
        </div>
      </div>

      {/* Main Content - SPLIT SCREEN */}
      <div className="flex-1 flex items-center justify-center p-4 sm:p-6">
        <div className="w-full max-w-6xl">
          <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
            {/* Desktop: Side by side | Mobile: Stacked */}
            <div className="grid lg:grid-cols-2 gap-0">
              {/* LEFT: Image */}
              <div className="relative bg-gray-100 flex items-center justify-center lg:min-h-[500px]">
                <img
                  src={scene.image_url}
                  alt={`Scene ${scene.scene_order}`}
                  className="w-full h-full object-contain max-h-[400px] lg:max-h-[600px]"
                />
                
                {/* Scene indicator on image */}
                <div className="absolute top-3 right-3 bg-purple-600 text-white px-3 py-1 rounded-full text-xs font-bold">
                  Scene {currentScene + 1}
                </div>
              </div>

              {/* RIGHT: Text & Controls */}
              <div className="flex flex-col justify-between p-6 sm:p-8 lg:min-h-[500px]">
                {/* Story Text */}
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center">
                    <BookOpen className="w-10 h-10 text-purple-600 mx-auto mb-4 opacity-50" />
                    <p className="text-lg sm:text-xl lg:text-2xl leading-relaxed text-gray-800">
                      {scene.paragraph_text}
                    </p>
                  </div>
                </div>

                {/* Controls */}
                <div className="mt-6">
                  {/* Play/Pause & Navigation */}
                  <div className="flex items-center justify-center gap-3 mb-6">
                    <button
                      onClick={prevScene}
                      disabled={currentScene === 0}
                      className="p-3 rounded-full bg-purple-100 text-purple-600 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-purple-200 transition"
                      title="Previous scene"
                    >
                      <ChevronLeft className="w-5 h-5" />
                    </button>

                    <button
                      onClick={handlePlayPause}
                      className="p-5 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700 transition shadow-lg"
                      title={isPlaying ? 'Pause' : 'Play'}
                    >
                      {isPlaying ? <Pause className="w-7 h-7" /> : <Play className="w-7 h-7 ml-0.5" />}
                    </button>

                    <button
                      onClick={nextScene}
                      disabled={currentScene === story.scenes.length - 1}
                      className="p-3 rounded-full bg-purple-100 text-purple-600 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-purple-200 transition"
                      title="Next scene"
                    >
                      <ChevronRight className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Progress Dots */}
                  <div className="flex gap-2 justify-center">
                    {story.scenes.map((_, index) => (
                      <button
                        key={index}
                        onClick={() => setCurrentScene(index)}
                        className={`transition-all ${
                          index === currentScene
                            ? 'w-8 h-2 bg-purple-600 rounded-full'
                            : 'w-2 h-2 bg-gray-300 rounded-full hover:bg-gray-400'
                        }`}
                        title={`Go to scene ${index + 1}`}
                      />
                    ))}
                  </div>

                  {/* Auto-advance hint */}
                  {isPlaying && (
                    <p className="text-center text-sm text-gray-500 mt-4">
                      🎵 Playing...  Will auto-advance when finished
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Audio Player (Hidden) */}
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
              });
            }
          }}
        />
      )}
    </div>
  );
}