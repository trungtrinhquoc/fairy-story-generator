'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Sparkles, BookOpen, Music, Wand2 } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const [childName, setChildName] = useState('');

  const handleStart = () => {
    router. push(`/create${childName ? `? name=${childName}` : ''}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-400 via-pink-400 to-blue-400">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="flex justify-center mb-6">
            <Sparkles className="w-20 h-20 text-yellow-300 animate-pulse" />
          </div>
          <h1 className="text-6xl font-bold text-white mb-4 drop-shadow-lg">
            ✨ Fairy Story Generator
          </h1>
          <p className="text-2xl text-white/90 mb-8">
            Create magical AI-powered stories for your child
          </p>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <FeatureCard
            icon={<BookOpen className="w-12 h-12" />}
            title="AI-Generated Stories"
            description="Personalized fairy tales created just for your child"
          />
          <FeatureCard
            icon={<Wand2 className="w-12 h-12" />}
            title="Beautiful Illustrations"
            description="Stunning images for every scene"
          />
          <FeatureCard
            icon={<Music className="w-12 h-12" />}
            title="Voice Narration"
            description="Professional narration brings stories to life"
          />
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto bg-white rounded-3xl shadow-2xl p-12">
          <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">
            Let's Create a Story!  📖
          </h2>
          
          <div className="space-y-6">
            <div>
              <label className="block text-lg font-medium text-gray-700 mb-2">
                Child's Name (Optional)
              </label>
              <input
                type="text"
                value={childName}
                onChange={(e) => setChildName(e.target.value)}
                placeholder="e.g., Lily, Max, Emma..."
                className="w-full px-6 py-4 text-lg border-2 border-gray-300 rounded-xl focus:border-purple-500 focus:ring focus:ring-purple-200 transition"
              />
            </div>

            <button
              onClick={handleStart}
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white text-xl font-bold py-6 rounded-xl hover:from-purple-700 hover:to-pink-700 transform hover:scale-105 transition shadow-lg"
            >
              Start Creating Magic ✨
            </button>
          </div>

          <p className="text-center text-gray-500 mt-6">
            No sign-up required • Takes about 1 minute
          </p>
        </div>
      </div>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 text-center hover:bg-white/20 transition">
      <div className="flex justify-center text-yellow-300 mb-4">{icon}</div>
      <h3 className="text-xl font-bold text-white mb-2">{title}</h3>
      <p className="text-white/80">{description}</p>
    </div>
  );
}