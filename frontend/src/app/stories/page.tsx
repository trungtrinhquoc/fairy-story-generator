'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { getStories } from '@/lib/api';
import type { StoryListItem } from '@/lib/api';
import { Loader2, BookOpen, Home, Sparkles } from 'lucide-react';

export default function StoriesPage() {
  const [stories, setStories] = useState<StoryListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    fetchStories();
  }, []);

  const fetchStories = async () => {
    try {
      setLoading(true);
      const data = await getStories(20);
      setStories(data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch stories:', err);
      setError(err.message || 'Failed to load stories');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-pink-100 to-blue-100">
      {/* Header */}
      <div className="bg-white/50 backdrop-blur-md border-b border-white/20 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => router.push('/')}
              className="flex items-center gap-2 text-purple-700 hover:text-purple-900 transition"
            >
              <Home className="w-5 h-5" />
              <span className="font-medium">Home</span>
            </button>

            <h1 className="text-2xl font-bold text-purple-800 flex items-center gap-2">
              <BookOpen className="w-6 h-6" />
              My Stories
            </h1>

            <button
              onClick={() => router.push('/create')}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition font-medium text-sm"
            >
              <Sparkles className="w-4 h-4" />
              New Story
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center min-h-[50vh]">
            <Loader2 className="w-12 h-12 text-purple-600 animate-spin mb-4" />
            <p className="text-purple-700 font-medium">Loading your magical stories...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center min-h-[50vh]">
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center max-w-md">
              <p className="text-red-600 font-medium mb-4">😢 {error}</p>
              <button
                onClick={fetchStories}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
              >
                Try Again
              </button>
            </div>
          </div>
        ) : stories.length === 0 ? (
          <div className="flex flex-col items-center justify-center min-h-[50vh]">
            <div className="text-center max-w-md">
              <Sparkles className="w-16 h-16 text-purple-300 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-700 mb-2">No Stories Yet</h2>
              <p className="text-gray-500 mb-6">
                Start creating your first magical fairy tale!
              </p>
              <button
                onClick={() => router.push('/create')}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition font-bold"
              >
                Create First Story ✨
              </button>
            </div>
          </div>
        ) : (
          <>
            <p className="text-sm text-purple-600 font-medium mb-6">
              {stories.length} {stories.length === 1 ? 'story' : 'stories'} found
            </p>

            {/* Grid Layout - Mobile-First (2: 3 ratio thumbnails) */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-6">
              {stories.map((story) => (
                <div
                  key={story.id}
                  onClick={() => router.push(`/story/${story.id}`)}
                  className="cursor-pointer group"
                >
                  {/* Thumbnail Container - 2:3 Aspect Ratio */}
                  <div className="relative aspect-[2/3] rounded-lg overflow-hidden shadow-md group-hover:shadow-2xl transition-all duration-300 bg-gradient-to-br from-purple-200 to-pink-200">
                    {story.thumbnailUrl ? (
                      <Image
                        src={story.thumbnailUrl}
                        alt={story.shortTitle || story.title}
                        fill
                        className="object-cover group-hover:scale-105 transition-transform duration-300"
                        sizes="(max-width: 640px) 50vw, (max-width:  768px) 33vw, (max-width: 1024px) 25vw, 20vw"
                        unoptimized
                      />
                    ) : (
                      // Fallback gradient with emoji
                      <div className="w-full h-full bg-gradient-to-br from-purple-400 via-pink-400 to-blue-400 flex items-center justify-center">
                        <span className="text-6xl">📖</span>
                      </div>
                    )}

                    {/* Status Badge */}
                    {story.status === 'generating' && (
                      <div className="absolute top-2 right-2 bg-yellow-500 text-white text-[10px] font-bold px-2 py-1 rounded shadow-lg uppercase tracking-wide">
                        Generating...
                      </div>
                    )}
                    {story.status === 'failed' && (
                      <div className="absolute top-2 right-2 bg-red-500 text-white text-[10px] font-bold px-2 py-1 rounded shadow-lg uppercase tracking-wide">
                        FAILED
                      </div>
                    )}

                    {/* Gradient Overlay for Title (at bottom) */}
                    <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />

                    {/* Title Overlay (on thumbnail) */}
                    <div className="absolute inset-x-0 bottom-0 p-3">
                      <h3 className="text-white text-sm font-bold leading-tight line-clamp-2 drop-shadow-lg">
                        {story.shortTitle || story.title}
                      </h3>
                    </div>
                  </div>

                  {/* Character Name (below thumbnail) */}
                  {story.characterName && (
                    <p className="text-xs text-purple-600 mt-2 font-medium truncate">
                      ⭐ {story.characterName}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}