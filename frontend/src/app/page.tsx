'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Sparkles, BookOpen, Music, Wand2, Library } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const [childName, setChildName] = useState('');

  const handleStart = () => {
    router.push(`/create${childName ? `?name=${childName}` : ''}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-400 via-pink-400 to-blue-400">
      <div className="container mx-auto px-4 py-10">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="flex justify-center mb-4">
            <Sparkles className="w-16 h-16 text-yellow-300 animate-pulse" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-3 drop-shadow-md">
            ✨ Fairy Story Generator
          </h1>
          <p className="text-xl text-white/90 mb-6">
            Create magical AI-powered stories for your child
          </p>
          
          {/* ← THÊM MỚI: Button "My Stories" */}
          <button
            onClick={() => router.push('/stories')}
            className="inline-flex items-center gap-2 px-6 py-3 bg-white/20 backdrop-blur-md text-white rounded-xl hover:bg-white/30 transition border border-white/30 font-bold"
          >
            <Library className="w-5 h-5" />
            My Stories
          </button>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-6 mb-12 max-w-5xl mx-auto">
          <FeatureCard
            icon={<BookOpen className="w-10 h-10" />}
            title="AI-Generated Stories"
            description="Personalized fairy tales created just for your child"
          />
          <FeatureCard
            icon={<Wand2 className="w-10 h-10" />}
            title="Beautiful Illustrations"
            description="Stunning images for every scene"
          />
          <FeatureCard
            icon={<Music className="w-10 h-10" />}
            title="Voice Narration"
            description="Professional narration brings stories to life"
          />
        </div>

        {/* CTA */}
        <div className="max-w-md mx-auto bg-white rounded-3xl shadow-xl p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-5 text-center">
            Let's Create a Story!  📖
          </h2>
          
          <div className="space-y-5">
            <div>
              <label className="block text-base font-medium text-gray-700 mb-1. 5">
                Child's Name (Optional)
              </label>
              <input
                type="text"
                value={childName}
                onChange={(e) => setChildName(e.target.value)}
                placeholder="e.g., Lily, Max, Emma..."
                className="w-full px-4 py-3 text-base border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-200 transition"
              />
            </div>

            <button
              onClick={handleStart}
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white text-lg font-bold py-4 rounded-xl hover:from-purple-700 hover:to-pink-700 transform hover:scale-105 transition shadow-lg"
            >
              Start Creating Magic ✨
            </button>
          </div>

          <p className="text-center text-xs text-gray-400 mt-5">
            No sign-up required • Takes about 1 minute
          </p>
        </div>
      </div>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 text-center hover:bg-white/20 transition border border-white/10">
      <div className="flex justify-center text-yellow-300 mb-3">{icon}</div>
      <h3 className="text-lg font-bold text-white mb-1. 5">{title}</h3>
      <p className="text-sm text-white/80 leading-relaxed">{description}</p>
    </div>
  );
}