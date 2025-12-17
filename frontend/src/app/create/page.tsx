'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { StoryLength, StoryTone, Theme } from '@/types/story';
import { Loader2, Sparkles } from 'lucide-react';
import { useStoryGeneration } from '@/hooks/useStoryGeneration';
import ProgressBar from '@/components/ProgressBar';
import ScenePlaceholder from '@/components/ScenePlaceholder';

function CreateStoryContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Form state
  const [childName, setChildName] = useState(searchParams.get('name') || '');
  const [childAge, setChildAge] = useState('');
  const [childGender, setChildGender] = useState<'boy' | 'girl' | 'other'>('boy');
  const [prompt, setPrompt] = useState('');
  const [theme, setTheme] = useState<Theme>('dragon');
  const [storyLength, setStoryLength] = useState<StoryLength>('short');
  const [storyTone, setStoryTone] = useState<StoryTone>('gentle');
  const [imageStyle, setImageStyle] = useState('Pixar 3D style');
  const [voice, setVoice] = useState('en-US-JennyNeural');
  
  // Story generation hook
  const {
    generateStory,
    storyId,
    title,
    scenes,
    progress,
    status,
    isGenerating,
    error:  generationError,
    reset,
  } = useStoryGeneration();
  
  const [error, setError] = useState('');

  // Theme options
  const themes:  { value: Theme; label: string; emoji: string }[] = [
    { value: 'princess', label: 'Princess', emoji: '👸' },
    { value: 'dragon', label: 'Dragon', emoji: '🐉' },
    { value: 'forest', label: 'Forest', emoji: '🌲' },
    { value: 'ocean', label: 'Ocean', emoji: '🌊' },
    { value: 'space', label: 'Space', emoji: '🚀' },
    { value: 'castle', label: 'Castle', emoji: '🏰' },
  ];

  const imageStyles = [
    { value: 'Pixar 3D style', label: 'Pixar 3D', emoji: '🎬' },
    { value: 'Watercolor style', label: 'Watercolor', emoji: '🎨' },
    { value: 'Anime style', label: 'Anime', emoji: '🎌' },
    { value: 'Storybook sketch', label: 'Sketch', emoji: '✏️' },
  ];

  const voices = [
    { value: 'en-US-Wavenet-F', label: 'Female Storyteller', icon: '👩' },
    { value: 'en-US-Wavenet-D', label: 'Gentle Male', icon: '👨' },
    { value: 'en-AU-Neural2-A', label: 'Child Voice', icon: '👧' },
    { value: 'vi-VN-Standard-A', label: 'Vietnamese (Standard)', icon: '🇻🇳' },

  ];

  // Generate summary message
  const summaryMessage = childName && childAge && prompt
    ? `Let's make a ${storyTone} story for ${childName}, age ${childAge} about ${prompt}! `
    : '';

  // Handle generate
  const handleGenerate = async () => {
    if (!childName. trim() || !prompt.trim()) {
      setError('Please enter child name and story idea');
      return;
    }

    setError('');
    
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
    } catch (err:  any) {
      setError(err.message || 'Failed to generate story');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-400 via-pink-400 to-blue-400 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-3xl shadow-2xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-2 flex items-center justify-center gap-2">
              Create Your Fairy Tale ✨
            </h1>
            <p className="text-gray-600">
              Tell us about your child and we'll create a magical story
            </p>
          </div>

          {/* Summary Message */}
          {summaryMessage && ! storyId && (
            <div className="bg-purple-50 border-2 border-purple-200 rounded-xl p-4 mb-6">
              <p className="text-purple-700 font-medium text-center">
                {summaryMessage}
              </p>
            </div>
          )}

          {/* ========================================
              STORY DISPLAY SECTION
              ======================================== */}
          {storyId && (
            <div className="mb-8">
              {/* Story Title */}
              <div className="bg-gradient-to-r from-purple-100 to-pink-100 rounded-xl p-6 mb-6">
                <h2 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
                  📖 {title || 'Your Story'}
                </h2>
                
                {/* Progress Bar */}
                {status === 'generating' && progress && (
                  <div className="mt-4">
                    <ProgressBar 
                      completed={progress.completed}
                      total={progress.total}
                      percentage={progress.percentage}
                    />
                    <p className="text-sm text-gray-600 mt-2 text-center">
                      Creating scene {progress.completed}/{progress.total}... 
                    </p>
                  </div>
                )}

                {status === 'completed' && (
                  <p className="text-green-600 font-medium mt-2">
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
                      className="bg-white border-2 border-purple-200 rounded-xl overflow-hidden shadow-lg hover:shadow-2xl transition-shadow"
                    >
                      {/* Scene Header */}
                      <div className="bg-gradient-to-r from-purple-500 to-pink-500 px-6 py-3">
                        <h3 className="text-white font-bold text-lg">
                          Scene {scene.scene_order}
                        </h3>
                      </div>

                      {/* Scene Content */}
                      <div className="p-6">
                        <div className="grid md:grid-cols-2 gap-6">
                          {/* Image */}
                          <div className="relative">
                            {scene.image_url ?  (
                              <img
                                src={scene.image_url}
                                alt={`Scene ${scene.scene_order}`}
                                className="w-full h-64 object-cover rounded-lg shadow-md"
                              />
                            ) : (
                              <div className="w-full h-64 bg-gray-200 rounded-lg flex items-center justify-center">
                                <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
                              </div>
                            )}
                          </div>

                          {/* Text & Audio */}
                          <div className="flex flex-col justify-between">
                            <p className="text-gray-700 leading-relaxed mb-4">
                              {scene.paragraph_text}
                            </p>

                            {/* Audio Player */}
                            {scene.audio_url && (
                              <div className="mt-auto">
                                <audio
                                  controls
                                  className="w-full"
                                  src={scene.audio_url}
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
                      className="px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition"
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
                      }}
                      className="px-6 py-3 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition"
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
            <div className="bg-red-50 border-2 border-red-200 rounded-xl p-4 mb-6">
              <p className="text-red-700 font-medium">
                ⚠️ {error || generationError}
              </p>
            </div>
          )}

          {/* ========================================
              FORM (CHỈ HIỂN THỊ KHI CHƯA TẠO STORY)
              ======================================== */}
          {! storyId && (
            <>
              {/* Child Info Section */}
              <div className="space-y-6 mb-8">
                {/* Child Name */}
                <div>
                  <label className="block text-gray-700 font-medium mb-2">
                    Child's Name *
                  </label>
                  <input
                    type="text"
                    value={childName}
                    onChange={(e) => setChildName(e.target.value)}
                    placeholder="Enter your child's name"
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus: border-purple-500 focus: outline-none"
                  />
                </div>

                {/* Child Age */}
                <div>
                  <label className="block text-gray-700 font-medium mb-2">
                    Age (Optional)
                  </label>
                  <input
                    type="number"
                    value={childAge}
                    onChange={(e) => setChildAge(e.target.value)}
                    placeholder="e.g., 7"
                    min="3"
                    max="12"
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none"
                  />
                </div>

                {/* Gender */}
                <div>
                  <label className="block text-gray-700 font-medium mb-2">
                    Gender (Optional)
                  </label>
                  <div className="flex gap-4">
                    {['boy', 'girl', 'other'].map((g) => (
                      <button
                        key={g}
                        type="button"
                        onClick={() => setChildGender(g as any)}
                        className={`px-6 py-2 rounded-lg border-2 transition ${
                          childGender === g
                            ? 'border-purple-500 bg-purple-50 text-purple-700 font-medium'
                            : 'border-gray-300 hover:border-purple-300'
                        }`}
                      >
                        {g. charAt(0).toUpperCase() + g.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Story Idea */}
                <div>
                  <label className="block text-gray-700 font-medium mb-2">
                    Story Idea *
                  </label>
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="What should the story be about?  (e.g., 'A brave adventure in the jungle')"
                    rows={3}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none resize-none"
                  />
                </div>

                {/* Theme */}
                <div>
                  <label className="block text-gray-700 font-medium mb-2">
                    🎨 Theme
                  </label>
                  <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                    {themes.map((t) => (
                      <button
                        key={t.value}
                        type="button"
                        onClick={() => setTheme(t.value)}
                        className={`p-3 rounded-lg border-2 transition text-center ${
                          theme === t.value
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-300 hover:border-purple-300'
                        }`}
                      >
                        <div className="text-3xl mb-1">{t.emoji}</div>
                        <div className="text-xs font-medium">{t.label}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Story Length */}
                <div>
                  <label className="block text-gray-700 font-medium mb-2">
                    📏 Story Length
                  </label>
                  <div className="flex gap-4">
                    {['short', 'medium', 'long'].map((length) => (
                      <button
                        key={length}
                        type="button"
                        onClick={() => setStoryLength(length as StoryLength)}
                        className={`flex-1 px-4 py-3 rounded-lg border-2 transition ${
                          storyLength === length
                            ?  'border-purple-500 bg-purple-50 text-purple-700 font-medium'
                            :  'border-gray-300 hover:border-purple-300'
                        }`}
                      >
                        {length. charAt(0).toUpperCase() + length.slice(1)}
                        <div className="text-xs text-gray-500">
                          {length === 'short' && '6 scenes'}
                          {length === 'medium' && '10 scenes'}
                          {length === 'long' && '14 scenes'}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Story Tone */}
                <div>
                  <label className="block text-gray-700 font-medium mb-2">
                    🎭 Story Tone
                  </label>
                  <div className="flex gap-4">
                    {['gentle', 'funny', 'adventurous']. map((tone) => (
                      <button
                        key={tone}
                        type="button"
                        onClick={() => setStoryTone(tone as StoryTone)}
                        className={`flex-1 px-4 py-3 rounded-lg border-2 transition ${
                          storyTone === tone
                            ? 'border-purple-500 bg-purple-50 text-purple-700 font-medium'
                            : 'border-gray-300 hover:border-purple-300'
                        }`}
                      >
                        {tone.charAt(0).toUpperCase() + tone.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Image Style */}
                <div>
                  <label className="block text-gray-700 font-medium mb-2">
                    🎨 Image Style
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {imageStyles. map((style) => (
                      <button
                        key={style. value}
                        type="button"
                        onClick={() => setImageStyle(style.value)}
                        className={`p-3 rounded-lg border-2 transition ${
                          imageStyle === style.value
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-300 hover:border-purple-300'
                        }`}
                      >
                        <div className="text-2xl mb-1">{style. emoji}</div>
                        <div className="text-xs font-medium">{style.label}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Narrator Voice */}
                <div>
                  <label className="block text-gray-700 font-medium mb-2">
                    🎤 Narrator Voice
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {voices.map((v) => (
                      <button
                        key={v.value}
                        type="button"
                        onClick={() => setVoice(v.value)}
                        className={`p-3 rounded-lg border-2 transition ${
                          voice === v.value
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-300 hover:border-purple-300'
                        }`}
                      >
                        <div className="text-2xl mb-1">{v. icon}</div>
                        <div className="text-xs font-medium">{v.label}</div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Generate Button */}
              <button
                onClick={handleGenerate}
                disabled={isGenerating || !childName.trim() || !prompt.trim()}
                className={`
                  w-full text-xl font-bold py-5 rounded-xl 
                  transition-all duration-300 shadow-lg 
                  flex items-center justify-center gap-2
                  ${
                    isGenerating || !childName.trim() || !prompt.trim()
                      ?  'bg-gray-400 text-gray-200 cursor-not-allowed opacity-70'
                      : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700 hover:scale-[1.02] hover:shadow-xl cursor-pointer'
                  }
                `}
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-6 h-6 animate-spin" />
                    Creating Your Magical Story...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-6 h-6" />
                    Generate Story ✨
                  </>
                )}
              </button>

              <p className="text-center text-sm text-gray-500 mt-4">
                ✨ First scene ready in ~15 seconds • Full story in 30-60 seconds
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CreatePage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><Loader2 className="w-12 h-12 animate-spin text-purple-500" /></div>}>
      <CreateStoryContent />
    </Suspense>
  );
}