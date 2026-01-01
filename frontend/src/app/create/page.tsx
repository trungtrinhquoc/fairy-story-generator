'use client';

import { useState, Suspense, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { StoryLength, StoryTone, Theme } from '@/types/story';
import { Loader2, Sparkles, Wand2 } from 'lucide-react';
import { useStoryGeneration } from '@/hooks/useStoryGeneration';
import ProgressBar from '@/components/ProgressBar';
import ScenePlaceholder from '@/components/ScenePlaceholder';

function CreateStoryContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // ========================================
  // FORM STATE
  // ========================================
  const [childName, setChildName] = useState(searchParams.get('name') || '');
  const [childAge, setChildAge] = useState('');
  const [childGender, setChildGender] = useState<'boy' | 'girl' | 'other'>('boy');
  const [prompt, setPrompt] = useState('');
  const [theme, setTheme] = useState<Theme>('dragon');
  const [storyLength, setStoryLength] = useState<StoryLength>('short');
  const [storyTone, setStoryTone] = useState<StoryTone>('gentle');
  const [imageStyle, setImageStyle] = useState('Pixar 3D style, vibrant colors, detailed');
  const [voice, setVoice] = useState('en-US-Wavenet-F');
  
  // UI state
  const [currentStep, setCurrentStep] = useState(1);
  const [showConfetti, setShowConfetti] = useState(false);
  const [error, setError] = useState('');
  const [isMounted, setIsMounted] = useState(false);
  
  // Story generation hook
  const {
    generateStory,
    storyId,
    title,
    scenes,
    progress,
    status,
    isGenerating,
    error: generationError,
    reset,
  } = useStoryGeneration();

  // Client-only mounting
  useEffect(() => {
    setIsMounted(true);
  }, []);

  // ========================================
  // OPTIONS DATA
  // ========================================
  
  const themes = [
    { value: 'princess', label: 'Princess Castle', emoji: '👸', color: 'from-pink-400 to-pink-600', bg: 'bg-pink-50' },
    { value: 'dragon', label: 'Dragon Adventure', emoji: '🐉', color: 'from-red-400 to-orange-600', bg: 'bg-orange-50' },
    { value: 'castle', label: 'Magic Castle', emoji: '🏰', color: 'from-purple-400 to-purple-600', bg: 'bg-purple-50' },
    { value: 'forest', label: 'Enchanted Forest', emoji: '🌲', color: 'from-green-400 to-green-600', bg: 'bg-green-50' },
    { value: 'ocean', label: 'Under the Sea', emoji: '🌊', color: 'from-blue-400 to-cyan-600', bg: 'bg-blue-50' },
    { value: 'space', label: 'Space Explorer', emoji: '🚀', color: 'from-indigo-400 to-purple-600', bg: 'bg-indigo-50' },
    { value: 'magical_forest', label: 'Desert Quest', emoji: '🏜️', color: 'from-yellow-400 to-orange-600', bg: 'bg-yellow-50' },
    { value: 'adventure', label: 'Arctic Journey', emoji: '❄️', color: 'from-cyan-400 to-blue-600', bg: 'bg-cyan-50' },
    { value: 'cute_animals', label: 'Chocolate World', emoji: '🍫', color: 'from-amber-600 to-yellow-600', bg: 'bg-amber-50' },
    { value: 'robot', label: 'Toy Come Alive', emoji: '🧸', color: 'from-rose-400 to-pink-600', bg: 'bg-rose-50' },
    { value: 'superhero', label: 'Neon City', emoji: '🌃', color: 'from-purple-600 to-pink-600', bg: 'bg-fuchsia-50' },
    { value: 'friendship', label: 'Candy Land', emoji: '🍭', color: 'from-pink-400 to-rose-600', bg: 'bg-pink-50' },
    { value: 'school_life', label: 'Racing Snail', emoji: '🐌', color: 'from-lime-400 to-green-600', bg: 'bg-lime-50' },
    { value: 'family', label: 'Painted Bird', emoji: '🎨', color: 'from-violet-400 to-purple-600', bg: 'bg-violet-50' },
  ];

  const imageStyles = [
    { value: 'Pixar 3D style, vibrant colors, detailed', label: 'Pixar Magic', emoji: '✨', preview: '🎬' },
    { value: 'Studio Ghibli style, soft colors, dreamy', label: 'Ghibli Dreams', emoji: '🌸', preview: '🎨' },
    { value: 'Disney 3D animation, colorful, cheerful', label: 'Disney Wonder', emoji: '🏰', preview: '🎪' },
    { value: 'Van Gogh oil painting, thick brushstrokes, swirling', label: 'Van Gogh Art', emoji: '🖌️', preview: '🎨' },
    { value: 'Watercolor painting, soft pastels, dreamy', label: 'Watercolor Dream', emoji: '💧', preview: '🌈' },
    { value: 'Crayon drawing style, childlike, colorful', label: 'Crayon Fun', emoji: '🖍️', preview: '📝' },
    { value: 'Synthwave neon lights, cyberpunk, vibrant glowing', label: 'Neon Glow', emoji: '🌃', preview: '⚡' },
    { value: 'Papercraft origami style, folded paper, 3D', label: 'Paper Magic', emoji: '📄', preview: '✂️' },
    { value:  'Clay animation stop-motion, textured', label: 'Clay World', emoji: '🧱', preview: '🎭' },
    { value: 'Storybook illustration, hand-drawn, whimsical', label: 'Storybook', emoji: '📖', preview: '✏️' },
    { value:  'Anime manga style, big eyes, dynamic', label: 'Anime Style', emoji: '🎌', preview: '⭐' },
    { value:  'Comic book style, bold lines, speech bubbles', label: 'Comic Hero', emoji: '💥', preview: '📰' },
  ];

  const voices = [
    { value: 'en-US-Wavenet-F', label: 'Fairy Godmother', emoji: '🧚', desc: 'Sweet & magical', color: 'from-pink-300 to-purple-300' },
    { value: 'en-US-Wavenet-D', label: 'Wise Wizard', emoji: '🧙', desc: 'Deep & calm', color: 'from-blue-300 to-indigo-300' },
    { value:  'en-AU-Neural2-A', label: 'Fun Friend', emoji: '🎈', desc: 'Playful & happy', color: 'from-yellow-300 to-orange-300' },
    { value: 'en-GB-Neural2-B', label: 'Royal Reader', emoji: '👑', desc: 'Elegant & clear', color: 'from-purple-300 to-pink-300' },
    { value: 'vi-VN-Standard-A', label: 'Vietnamese', emoji: '🇻🇳', desc: 'Tiếng Việt', color: 'from-red-300 to-yellow-300' },
  ];

  const quickIdeas = [
    { text: '🍫 A chocolate knight crosses a hot desert to save marshmallow friends', prompt: 'A small knight made entirely of chocolate must cross a desert of hot sand to save his marshmallow friends from a giant campfire.  He uses a peppermint shield. ', theme: 'cute_animals' as Theme, style: 'Pixar 3D style, vibrant colors, detailed' },
    { text: '🐌 A speedy snail with jet engines joins a rainbow race', prompt: 'Turbo is a snail who finds magical tiny jet engines.  He joins a race against rabbits through a neon forest, leaving rainbow slime trails.', theme: 'school_life' as Theme, style:  'Synthwave neon lights, cyberpunk, vibrant glowing' },
    { text: '🧸 A teddy bear climbs pillow mountains to find a lost puzzle', prompt: 'When lights go out, Barnaby the teddy wakes up to find a lost puzzle piece under the giant sofa. He climbs pillow mountains and dodges lava carpets.', theme: 'robot' as Theme, style: 'Storybook illustration, hand-drawn, whimsical' },
    { text: '🎨 A painted bird helps an origami crane learn to fly', prompt: 'Sky is a bird made of oil paint strokes.  Her wings change colors as she flies into a paper world to help an origami crane learn to fly.', theme: 'family' as Theme, style: 'Van Gogh oil painting, thick brushstrokes, swirling' },
    { text: '🍦 Find the Golden Spoon in an ice cream volcano land', prompt: 'Mochi travels to a land where volcanoes erupt strawberry ice cream. Trees are lollipops and clouds are cotton candy.  Find the legendary Golden Spoon!', theme:  'friendship' as Theme, style: 'Disney 3D animation, colorful, cheerful' },
  ];

  const summaryMessage = childName && childAge && prompt
    ? `Let's make a ${storyTone} story for ${childName}, age ${childAge} about ${prompt}!`
    : '';

  // ========================================
  // HANDLERS
  // ========================================
  
  const handleQuickIdea = (idea:  typeof quickIdeas[0]) => {
    setPrompt(idea.prompt);
    setTheme(idea.theme);
    setImageStyle(idea.style);
    setShowConfetti(true);
    setTimeout(() => setShowConfetti(false), 2000);
  };

  const handleGenerate = async () => {
    if (!childName. trim() || !prompt.trim()) {
      setError('Please enter child name and story idea!  🎈');
      return;
    }
    setError('');
    setShowConfetti(true);
    try {
      await generateStory({
        child_name: childName,
        prompt,
        story_length: storyLength,
        story_tone: storyTone,
        theme,
        image_style: imageStyle,
        voice,
      });
    } catch (err: any) {
      setError(err.message || 'Failed to generate story');
    } finally {
      setTimeout(() => setShowConfetti(false), 3000);
    }
  };

  const canProceed = (step: number) => {
    if (step === 1) return childName. trim().length > 0;
    if (step === 2) return prompt.trim().length > 0;
    return true;
  };

  // ========================================
  // RENDER
  // ========================================
  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-100 via-pink-100 via-purple-100 to-blue-100 py-8 px-4 relative overflow-hidden">
      
      {/* Background Decorations */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-30">
        <div className="absolute top-10 left-10 text-4xl animate-bounce">⭐</div>
        <div className="absolute top-20 right-20 text-3xl animate-spin-slow">🌈</div>
        <div className="absolute bottom-20 left-20 text-4xl animate-pulse">🎈</div>
      </div>

      {/* Confetti Effect - Client Only */}
      {isMounted && showConfetti && (
        <div className="fixed inset-0 pointer-events-none z-50">
          {Array. from({ length: 25 }).map((_, i) => (
            <div
              key={i}
              className="absolute text-2xl animate-confetti"
              style={{
                left: `${(i * 4) % 100}%`,
                top: `-5%`,
                animationDelay: `${(i * 0.1) % 1}s`,
                animationDuration: `${2 + (i % 3)}s`,
              }}
            >
              {['🎉', '⭐', '✨', '🌟', '💫'][i % 5]}
            </div>
          ))}
        </div>
      )}

      <div className="max-w-5xl mx-auto relative z-10">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 mb-2 drop-shadow-md">
            ✨ Magic Story Maker ✨
          </h1>
          <p className="text-lg md:text-xl text-gray-700 font-bold">
            Let's create YOUR magical story! 🎪
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white/95 backdrop-blur-sm rounded-[2. 5rem] shadow-2xl p-6 md:p-10 border-4 border-white">
          
          {/* Summary Message */}
          {summaryMessage && ! storyId && (
            <div className="bg-gradient-to-r from-purple-50 to-pink-50 border-2 border-purple-200 rounded-2xl p-4 mb-6">
              <p className="text-purple-700 font-medium text-center">
                {summaryMessage}
              </p>
            </div>
          )}

          {/* ========================================
              STORY DISPLAY SECTION
              ======================================== */}
          {storyId && (
            <div className="mb-8 animate-fade-in">
              {/* Story Title */}
              <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl p-6 mb-6 text-white">
                <h2 className="text-3xl font-bold flex items-center gap-2">
                  📖 {title || 'Your Story'}
                </h2>
                
                {/* Progress Bar */}
                {status === 'generating' && progress && (
                  <div className="mt-4">
                    <ProgressBar 
                      completed={progress. completed}
                      total={progress.total}
                      percentage={progress.percentage}
                    />
                    <p className="text-sm text-white/90 mt-2 text-center">
                      Creating scene {progress.completed}/{progress.total}...  ✨
                    </p>
                  </div>
                )}

                {status === 'completed' && (
                  <p className="text-white/90 font-medium mt-2">
                    ✅ Story complete! All {progress?. total || 0} scenes ready. 
                  </p>
                )}
              </div>

              {/* Scenes Grid */}
              <div className="space-y-6">
                {scenes && scenes.length > 0 ? (
                  scenes.map((scene) => (
                    <div
                      key={scene.id}
                      className="bg-white border-2 border-purple-200 rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-shadow"
                    >
                      {/* Scene Header */}
                      <div className="bg-gradient-to-r from-purple-400 to-pink-400 px-6 py-3">
                        <h3 className="text-white font-bold text-lg">
                          Scene {scene.sceneOrder}
                        </h3>
                      </div>

                      {/* Scene Content */}
                      <div className="p-6">
                        <div className="grid md:grid-cols-2 gap-6">
                          {/* Image */}
                          <div className="relative">
                            {scene.imageUrl ?  (
                              <img
                                src={scene.imageUrl}
                                alt={`Scene ${scene.sceneOrder}`}
                                className="w-full h-64 object-cover rounded-lg shadow-md"
                              />
                            ) : (
                              <div className="w-full h-64 bg-gradient-to-br from-purple-100 to-pink-100 rounded-lg flex items-center justify-center">
                                <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                              </div>
                            )}
                          </div>

                          {/* Text & Audio */}
                          <div className="flex flex-col justify-between">
                            <p className="text-gray-700 leading-relaxed mb-4">
                              {scene.paragraphText}
                            </p>

                            {/* Audio Player */}
                            {scene.audioUrl && (
                              <div className="mt-auto">
                                <audio
                                  controls
                                  className="w-full"
                                  src={scene.audioUrl}
                                >
                                  Your browser does not support audio.
                                </audio>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-12">
                    <Loader2 className="w-12 h-12 animate-spin text-purple-500 mx-auto mb-4" />
                    <p className="text-gray-600">Preparing your first scene...</p>
                  </div>
                )}

                {/* Placeholders for remaining scenes */}
                {status === 'generating' && progress && scenes.length < progress.total && (
                  Array.from({ length: progress.total - scenes.length }).map((_, i) => (
                    <ScenePlaceholder key={`placeholder-${i}`} sceneNumber={scenes.length + i + 1} />
                  ))
                )}
              </div>

              {/* Action Buttons */}
              <div className="mt-8 flex gap-4 justify-center">
                {status === 'completed' && (
                  <>
                    <button
                      onClick={() => router.push(`/story/${storyId}`)}
                      className="px-6 py-3 bg-purple-600 text-white rounded-xl font-bold hover:bg-purple-700 transition shadow-lg"
                    >
                      📖 View Full Story
                    </button>
                    <button
                      onClick={() => {
                        reset();
                        setChildName('');
                        setChildAge('');
                        setPrompt('');
                        setError('');
                        setCurrentStep(1);
                      }}
                      className="px-6 py-3 bg-gray-600 text-white rounded-xl font-bold hover:bg-gray-700 transition shadow-lg"
                    >
                      ✨ Create Another
                    </button>
                  </>
                )}
              </div>
            </div>
          )}

          {/* ========================================
              ERROR DISPLAY
              ======================================== */}
          {(error || generationError) && (
            <div className="bg-red-50 border-2 border-red-200 rounded-2xl p-4 mb-6 text-center animate-shake">
              <p className="text-red-700 font-bold">
                ⚠️ {error || generationError}
              </p>
            </div>
          )}

          {/* ========================================
              FORM - 3 STEPS
              ======================================== */}
          {! storyId && (
            <>
              {/* Progress Steps */}
              <div className="mb-10">
                <div className="flex justify-center items-center gap-2 max-w-md mx-auto">
                  {[
                    { num: 1, label: 'Who? ', icon: '👶', color: 'bg-pink-500' },
                    { num:  2, label: 'What?', icon: '📖', color: 'bg-purple-500' },
                    { num: 3, label: 'Style! ', icon: '🎨', color: 'bg-blue-500' },
                  ].map((step, i) => (
                    <div key={step.num} className="flex items-center">
                      <button
                        onClick={() => setCurrentStep(step.num)}
                        className={`w-14 h-14 md:w-16 md:h-16 rounded-full flex flex-col items-center justify-center transition-all ${
                          currentStep === step. num 
                            ? `${step.color} text-white scale-110 shadow-lg animate-pulse-slow` 
                            : currentStep > step.num 
                              ? `${step.color} text-white` 
                              : 'bg-gray-200 text-gray-400'
                        }`}
                      >
                        <span className="text-2xl">{step.icon}</span>
                        <span className="text-[10px] font-bold uppercase">{step.label}</span>
                      </button>
                      {i < 2 && (
                        <div className={`w-10 md:w-16 h-1. 5 mx-1 rounded-full ${currentStep > step.num ? step.color : 'bg-gray-200'}`} />
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Step Content */}
              <div className="min-h-[450px]">
                
                {/* STEP 1: Child Info */}
                {currentStep === 1 && (
                  <div className="space-y-8 animate-slide-in max-w-2xl mx-auto">
                    <div className="text-center">
                      <h2 className="text-3xl md:text-4xl font-black text-gray-800 mb-1">
                        What's your name?  🎈
                      </h2>
                    </div>

                    <input
                      type="text"
                      value={childName}
                      onChange={(e) => setChildName(e.target.value)}
                      placeholder="Type your name here..."
                      className="w-full px-6 py-4 text-2xl font-bold text-center border-4 border-purple-200 rounded-3xl focus:border-pink-400 outline-none transition-all shadow-inner"
                      autoFocus
                    />
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="text-lg font-bold text-gray-600 mb-2 block ml-1">
                          How old are you?  🎂
                        </label>
                        <input
                          type="number"
                          value={childAge}
                          onChange={(e) => setChildAge(e.target.value)}
                          placeholder="7"
                          min="3"
                          max="12"
                          className="w-full px-4 py-3 text-xl font-bold text-center border-2 border-blue-200 rounded-2xl focus:border-blue-400 outline-none"
                        />
                      </div>

                      <div>
                        <label className="text-lg font-bold text-gray-600 mb-2 block ml-1">
                          I am a...  🌟
                        </label>
                        <div className="flex gap-2">
                          {['boy', 'girl', 'other'].map((g) => (
                            <button
                              key={g}
                              type="button"
                              onClick={() => setChildGender(g as any)}
                              className={`flex-1 py-3 rounded-2xl font-bold text-base transition-all ${
                                childGender === g 
                                  ? 'bg-gradient-to-r from-blue-400 to-indigo-500 text-white shadow-md' 
                                  : 'bg-gray-100 text-gray-500'
                              }`}
                            >
                              {g === 'boy' ? '👦 Boy' : g === 'girl' ? '👧 Girl' :  '🌈 Other'}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="text-center pt-4">
                      <button
                        onClick={() => setCurrentStep(2)}
                        disabled={!canProceed(1)}
                        className={`px-12 py-4 text-xl font-black rounded-full transition-all ${
                          canProceed(1) 
                            ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:scale-105 shadow-xl' 
                            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                        }`}
                      >
                        Next Adventure!  🚀
                      </button>
                    </div>
                  </div>
                )}

                {/* STEP 2: Story Idea & Options */}
                {currentStep === 2 && (
                  <div className="space-y-8 animate-slide-in">
                    <div className="text-center">
                      <h2 className="text-3xl md:text-4xl font-black text-gray-800 mb-1">
                        What adventure?  🌟
                      </h2>
                    </div>

                    {/* Quick Ideas */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-w-5xl mx-auto">
                      {quickIdeas.map((idea, i) => (
                        <button
                          key={i}
                          onClick={() => handleQuickIdea(idea)}
                          className="p-4 bg-gradient-to-br from-yellow-50 to-pink-50 border-2 border-purple-200 rounded-2xl hover:border-purple-400 hover:shadow-md transition-all text-left"
                        >
                          <p className="text-sm font-bold text-gray-800 leading-snug">
                            {idea. text}
                          </p>
                        </button>
                      ))}
                    </div>

                    {/* Custom Textarea */}
                    <div className="max-w-3xl mx-auto">
                      <textarea
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        placeholder="Tell me about your magical adventure..."
                        rows={4}
                        className="w-full px-6 py-4 text-lg border-2 border-blue-200 rounded-[2rem] focus:border-pink-400 focus:outline-none shadow-inner resize-none"
                      />
                    </div>

                    {/* Themes */}
                    <div className="max-w-5xl mx-auto">
                      <h3 className="text-base font-black text-center mb-4 text-green-700 uppercase tracking-widest">
                        🎨 Pick your world! 
                      </h3>
                      <div className="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-7 gap-2">
                        {themes.map((t) => (
                          <button
                            key={t. value}
                            onClick={() => setTheme(t.value as Theme)}
                            className={`p-3 rounded-2xl border-2 transition-all ${
                              theme === t.value 
                                ?  `bg-gradient-to-br ${t.color} text-white border-white scale-110 shadow-lg` 
                                : `${t.bg} border-gray-200 hover:border-gray-400`
                            }`}
                          >
                            <div className="text-3xl mb-1">{t.emoji}</div>
                            <div className="text-[10px] font-bold truncate leading-none">{t.label}</div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Length & Tone */}
                    <div className="grid grid-cols-1 md: grid-cols-2 gap-8 max-w-4xl mx-auto">
                      <div>
                        <h3 className="text-lg font-black mb-4 text-orange-700 text-center md:text-left">
                          📏 How long? 
                        </h3>
                        <div className="space-y-2">
                          {[
                            { value: 'short', label: 'Quick Story', emoji: '⚡', time: '6 scenes' },
                            { value:  'medium', label: 'Medium Story', emoji: '📖', time: '10 scenes' },
                            { value: 'long', label:  'Long Adventure', emoji: '📚', time: '14 scenes' },
                          ].map((l) => (
                            <button
                              key={l.value}
                              onClick={() => setStoryLength(l.value as StoryLength)}
                              className={`w-full p-3 rounded-xl border-2 font-bold transition-all flex items-center justify-between ${
                                storyLength === l.value 
                                  ? 'bg-gradient-to-r from-orange-400 to-red-500 text-white border-white shadow-md scale-102' 
                                  : 'bg-white border-orange-200'
                              }`}
                            >
                              <span className="text-xl">{l.emoji}</span>
                              <div className="text-right">
                                <div className="text-sm">{l.label}</div>
                                <div className="text-[10px] opacity-80">{l.time}</div>
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h3 className="text-lg font-black mb-4 text-pink-700 text-center md: text-left">
                          🎭 What mood?
                        </h3>
                        <div className="space-y-2">
                          {[
                            { value:  'gentle', emoji: '🌸', label: 'Gentle & Sweet', color: 'from-pink-400 to-rose-500' },
                            { value:  'funny', emoji: '😂', label: 'Funny & Silly', color: 'from-yellow-400 to-orange-500' },
                            { value:  'adventurous', emoji: '⚔️', label: 'Exciting Adventure', color: 'from-red-400 to-purple-500' },
                          ].map((t) => (
                            <button
                              key={t.value}
                              onClick={() => setStoryTone(t.value as StoryTone)}
                              className={`w-full p-3 rounded-xl border-2 font-bold transition-all flex items-center gap-3 ${
                                storyTone === t.value 
                                  ? `bg-gradient-to-r ${t.color} text-white border-white shadow-md scale-102` 
                                  : 'bg-white border-pink-200'
                              }`}
                            >
                              <span className="text-2xl">{t.emoji}</span>
                              <span className="text-sm">{t.label}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-between max-w-3xl mx-auto pt-6">
                      <button
                        onClick={() => setCurrentStep(1)}
                        className="px-6 py-2 text-lg font-bold text-gray-400 hover:text-gray-600 transition"
                      >
                        ← Back
                      </button>
                      <button
                        onClick={() => setCurrentStep(3)}
                        disabled={!canProceed(2)}
                        className={`px-12 py-4 text-xl font-black rounded-full transition-all ${
                          canProceed(2) 
                            ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-xl hover:scale-105' 
                            : 'bg-gray-200 text-gray-400'
                        }`}
                      >
                        Next:  Style!  🎨
                      </button>
                    </div>
                  </div>
                )}

                {/* STEP 3: Style & Voice */}
                {currentStep === 3 && (
                  <div className="space-y-10 animate-slide-in max-w-5xl mx-auto">
                    <div className="text-center">
                      <h2 className="text-3xl md:text-4xl font-black text-gray-800 mb-1">
                        Look & Sound 🎨🎵
                      </h2>
                    </div>

                    {/* Image Styles */}
                    <div>
                      <h3 className="text-center text-sm font-black text-purple-700 uppercase mb-4 tracking-wider">
                        🖌️ Pick an Art Style
                      </h3>
                      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
                        {imageStyles.map((s) => (
                          <button
                            key={s. value}
                            onClick={() => setImageStyle(s.value)}
                            className={`p-3 rounded-2xl border-2 transition-all ${
                              imageStyle === s.value 
                                ? 'bg-purple-500 text-white border-white scale-110 shadow-lg' 
                                : 'bg-white border-gray-100 hover:border-purple-200'
                            }`}
                          >
                            <div className="text-2xl mb-1">{s.preview}</div>
                            <div className="text-[10px] font-bold leading-tight">{s.label}</div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Voices */}
                    <div>
                      <h3 className="text-center text-sm font-black text-blue-700 uppercase mb-4 tracking-wider">
                        🎤 Pick a Narrator
                      </h3>
                      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
                        {voices.map((v) => (
                          <button
                            key={v.value}
                            onClick={() => setVoice(v. value)}
                            className={`p-4 rounded-3xl border-2 transition-all text-left ${
                              voice === v. value 
                                ? `bg-gradient-to-r ${v.color} border-white shadow-lg scale-105` 
                                : 'bg-white border-gray-100 hover:border-blue-200'
                            }`}
                          >
                            <div className="text-3xl mb-2">{v.emoji}</div>
                            <div className="font-bold text-xs mb-1">{v.label}</div>
                            <div className="text-[9px] opacity-70 leading-tight">{v.desc}</div>
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="flex justify-between items-center pt-6">
                      <button
                        onClick={() => setCurrentStep(2)}
                        className="px-4 py-2 text-sm font-bold text-gray-400 hover:text-gray-600 transition"
                      >
                        ← Back
                      </button>
                      
                      <button
                        onClick={handleGenerate}
                        disabled={isGenerating}
                        className={`px-8 py-3 text-lg font-black rounded-full transition-all flex items-center gap-3 ${
                          isGenerating 
                            ? 'bg-gray-300 cursor-not-allowed' 
                            : 'bg-gradient-to-r from-green-500 via-blue-500 to-purple-600 text-white hover:scale-105 shadow-xl animate-pulse-slow'
                        }`}
                      >
                        {isGenerating ? (
                          <>
                            <Loader2 className="animate-spin w-6 h-6" />
                            Making Magic... 
                          </>
                        ) : (
                          <>
                            <Wand2 className="w-6 h-6" />
                            CREATE STORY!  ✨
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Footer Info */}
              <p className="text-center text-sm text-gray-500 mt-6">
                ✨ First scene ready in ~20 seconds • Full story in 30-40 seconds
              </p>
            </>
          )}
        </div>
      </div>

      {/* Animations CSS */}
      <style jsx>{`
        @keyframes confetti {
          0% { transform: translateY(0) rotate(0deg); opacity: 1; }
          100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
        }
        . animate-confetti {
          animation: confetti linear forwards;
        }
        .animate-spin-slow {
          animation: spin 5s linear infinite;
        }
        .animate-pulse-slow {
          animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        .animate-fade-in {
          animation: fadeIn 0.6s ease-in;
        }
        @keyframes fadeIn {
          from { opacity:  0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        . animate-slide-in {
          animation: slideIn 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(-30px); }
          to { opacity: 1; transform: translateX(0); }
        }
        .animate-shake {
          animation: shake 0.4s;
        }
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-5px); }
          75% { transform: translateX(5px); }
        }
        .scale-102 {
          transform: scale(1.02);
        }
      `}</style>
    </div>
  );
}

export default function CreatePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex flex-col items-center justify-center bg-purple-50">
        <Loader2 className="w-12 h-12 animate-spin text-purple-600" />
        <p className="text-xl font-bold text-purple-700 mt-6 animate-pulse">Magic Loading...  ✨</p>
      </div>
    }>
      <CreateStoryContent />
    </Suspense>
  );
}