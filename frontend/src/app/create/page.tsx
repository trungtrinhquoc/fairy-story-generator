'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { storyApi } from '@/lib/api';
import { StoryLength, StoryTone, Theme } from '@/types/story';
import { Loader2, Sparkles, Upload } from 'lucide-react';
// ← THÊM imports mới
import { useStoryGeneration } from '@/hooks/useStoryGeneration';
import ProgressBar from '@/components/ProgressBar';
import ScenePlaceholder from '@/components/ScenePlaceholder';

function CreateStoryContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Input fields theo spec (GIỮ NGUYÊN)
  const [childName, setChildName] = useState(searchParams.get('name') || '');
  const [childAge, setChildAge] = useState('');
  const [childGender, setChildGender] = useState<'boy' | 'girl' | 'other'>('boy');
  const [prompt, setPrompt] = useState('');
  const [theme, setTheme] = useState<Theme>('dragon');
  const [storyLength, setStoryLength] = useState<StoryLength>('short');
  const [storyTone, setStoryTone] = useState<StoryTone>('gentle');
  const [imageStyle, setImageStyle] = useState('Pixar 3D style');
  const [voice, setVoice] = useState('en-US-JennyNeural');
  
  // ← THAY ĐỔI:  Dùng hook thay vì state cũ
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

  // Themes, styles, voices (GIỮ NGUYÊN)
  const themes: { value: Theme; label: string; emoji: string }[] = [
    { value: 'princess', label: 'Princess', emoji: '👸' },
    { value: 'dragon', label: 'Dragon', emoji: '🐉' },
    { value: 'forest', label: 'Forest', emoji: '🌲' },
    { value: 'ocean', label: 'Ocean', emoji: '🌊' },
    { value: 'space', label: 'Space', emoji: '🚀' },
    { value:  'castle', label: 'Castle', emoji: '🏰' },
  ];

  const imageStyles = [
    { value: 'Pixar 3D style', label: 'Pixar 3D', emoji: '🎬' },
    { value: 'Watercolor style', label: 'Watercolor', emoji: '🎨' },
    { value: 'Anime style', label: 'Anime', emoji: '🎌' },
    { value: 'Storybook sketch', label: 'Sketch', emoji: '✏️' },
  ];

  const voices = [
    { value: 'en-US-JennyNeural', label: 'Female Storyteller', icon: '👩' },
    { value: 'en-US-GuyNeural', label: 'Gentle Male', icon: '👨' },
    { value: 'en-US-AriaNeural', label: 'Child Voice', icon: '👧' },
  ];

  // Generate summary message (GIỮ NGUYÊN)
  const getSummary = () => {
    if (!childName || !theme) return '';
    
    const ageText = childAge ? `, age ${childAge}` : '';
    const themeLabel = themes.find(t => t.value === theme)?.label || theme;
    const toneText = storyTone === 'gentle' ? 'bedtime' : storyTone;
    
    return `Let's make a ${toneText} story for ${childName}${ageText} about ${themeLabel. toLowerCase()}! `;
  };

  // ← SỬA:  handleGenerate dùng hook mới
  const handleGenerate = async () => {
    if (!childName. trim()) {
      setError("Please enter child's name");
      return;
    }
    
    if (!prompt.trim()) {
      setError('Please enter a story idea');
      return;
    }

    setError('');

    try {
      // Gọi generateStory từ hook (sẽ tự động poll)
      await generateStory({
        prompt,
        story_length: storyLength,
        story_tone: storyTone,
        theme,
        child_name: childName,
        image_style: imageStyle,
        voice:  voice,
      });
      
      // KHÔNG redirect ngay - để user xem progress
      // Khi completed, có thể redirect hoặc show button "View Full Story"
    } catch (err:  any) {
      setError(err.message || 'Failed to generate story');
    }
  };

  // ← THÊM: Auto redirect khi completed (optional)
  useEffect(() => {
    if (status === 'completed' && storyId) {
      // Có thể tự động redirect sau 2s
      // setTimeout(() => router.push(`/story/${storyId}`), 2000);
      
      // Hoặc để user tự click button "View Story"
    }
  }, [status, storyId]);

  // ← THÊM: Helper render placeholders
  const renderPlaceholders = () => {
    if (!progress) return null;
    
    const placeholders = [];
    for (let i = scenes.length + 1; i <= progress.total; i++) {
      placeholders. push(<ScenePlaceholder key={`placeholder-${i}`} sceneNumber={i} />);
    }
    return placeholders;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-400 via-purple-400 to-pink-400 py-12">
      <div className="container mx-auto px-4 max-w-5xl">
        <div className="bg-white rounded-3xl shadow-2xl p-8 md:p-12">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-2">
              Create Your Fairy Tale ✨
            </h1>
            <p className="text-gray-600">
              Tell us about your child and we'll create a magical story
            </p>
          </div>

          {/* Summary Message */}
          {getSummary() && (
            <div className="bg-purple-50 border-2 border-purple-200 rounded-xl p-4 mb-8 text-center">
              <p className="text-lg text-purple-800 font-medium">
                {getSummary()}
              </p>
            </div>
          )}

          {/* ← THÊM: Progress Section (chỉ show khi đang generate) */}
          {isGenerating && (
            <div className="mb-8 bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-6 border-2 border-purple-200">
              {/* Title */}
              {title && (
                <h2 className="text-2xl font-bold text-center mb-4 text-gray-800">
                  📖 {title}
                </h2>
              )}
              
              {/* Progress Bar */}
              {progress && (
                <ProgressBar
                  current={progress.completed}
                  total={progress. total}
                  message={`Creating magical scenes... `}
                />
              )}
              
              <p className="text-center text-sm text-gray-600 mt-3">
                {status === 'generating' 
                  ? `✨ Your story is being created...  (${scenes.length}/${progress?. total || 6} scenes ready)`
                  : status === 'completed'
                  ? '🎉 Story completed!'
                  : 'Preparing your story...'}
              </p>
            </div>
          )}

          {/* ← THÊM: Scenes Preview (show khi có scenes) */}
          {scenes. length > 0 && (
            <div className="mb-8">
              <h3 className="text-xl font-bold text-gray-800 mb-4">
                📚 Story Preview
              </h3>
              
              <div className="space-y-4 max-h-[600px] overflow-y-auto">
                {scenes.map((scene) => (
                  <div
                    key={scene.id}
                    className="border-2 border-purple-200 rounded-xl p-4 bg-white shadow-sm"
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center font-bold text-sm">
                        {scene.scene_order}
                      </div>
                      <h4 className="font-semibold text-gray-800">Scene {scene.scene_order}</h4>
                      <span className="ml-auto text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                        ✅ Ready
                      </span>
                    </div>
                    
                    <img
                      src={scene.image_url}
                      alt={`Scene ${scene.scene_order}`}
                      className="w-full aspect-video object-cover rounded-lg mb-3"
                    />
                    
                    <p className="text-sm text-gray-700 leading-relaxed mb-2">
                      {scene.paragraph_text}
                    </p>
                    
                    <audio src={scene.audio_url} controls className="w-full h-8" />
                  </div>
                ))}
                
                {/* Placeholders */}
                {renderPlaceholders()}
              </div>
            </div>
          )}

          {/* ← THÊM: View Full Story Button (khi completed) */}
          {status === 'completed' && storyId && (
            <div className="mb-8 text-center">
              <button
                onClick={() => router.push(`/story/${storyId}`)}
                className="bg-gradient-to-r from-green-500 to-emerald-500 text-white text-lg font-bold py-4 px-8 rounded-xl hover:from-green-600 hover:to-emerald-600 transition shadow-lg inline-flex items-center gap-2"
              >
                <Sparkles className="w-5 h-5" />
                View Full Story
              </button>
              
              <button
                onClick={reset}
                className="ml-4 bg-gray-200 text-gray-700 text-lg font-bold py-4 px-8 rounded-xl hover:bg-gray-300 transition"
              >
                Create Another Story
              </button>
            </div>
          )}

          {/* Form (GIỮ NGUYÊN - chỉ ẩn khi đang generate) */}
          {!isGenerating && status === 'idle' && (
            <div className="space-y-8">
              {/* Section 1: Child Info */}
              <div className="border-b pb-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                  👶 Child Information
                </h2>
                
                <div className="grid md:grid-cols-3 gap-4">
                  {/* Name */}
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Child's Name *
                    </label>
                    <input
                      type="text"
                      value={childName}
                      onChange={(e) => setChildName(e.target.value)}
                      placeholder="Lily, Max, Emma..."
                      className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring focus:ring-purple-200"
                    />
                  </div>

                  {/* Age */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Age (Optional)
                    </label>
                    <input
                      type="number"
                      value={childAge}
                      onChange={(e) => setChildAge(e.target.value)}
                      placeholder="5"
                      min="1"
                      max="12"
                      className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus: border-purple-500 focus: ring focus:ring-purple-200"
                    />
                  </div>
                </div>

                {/* Gender */}
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Gender
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {(['boy', 'girl', 'other'] as const).map((gender) => (
                      <button
                        key={gender}
                        onClick={() => setChildGender(gender)}
                        className={`px-4 py-3 rounded-lg border-2 font-medium transition ${
                          childGender === gender
                            ?  'border-purple-500 bg-purple-50 text-purple-700'
                            : 'border-gray-300 hover:border-purple-300'
                        }`}
                      >
                        {gender === 'boy' ?  '👦 Boy' : gender === 'girl' ? '👧 Girl' : '🧒 Other'}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Section 2: Story Details */}
              <div className="border-b pb-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                  📖 Story Details
                </h2>

                {/* Story Idea */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Story Idea *
                  </label>
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="A brave little girl meets a friendly dragon in a magical forest..."
                    rows={4}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus: border-purple-500 focus: ring focus:ring-purple-200"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Describe what happens in the story
                  </p>
                </div>

                {/* Theme Selection */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Theme
                  </label>
                  <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                    {themes.map((t) => (
                      <button
                        key={t.value}
                        onClick={() => setTheme(t.value)}
                        className={`p-4 rounded-lg border-2 transition ${
                          theme === t.value
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-300 hover:border-purple-300'
                        }`}
                      >
                        <div className="text-3xl mb-1">{t. emoji}</div>
                        <div className="text-xs font-medium">{t.label}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Story Length */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Story Length
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {(['short', 'medium', 'long'] as StoryLength[]).map((length) => (
                      <button
                        key={length}
                        onClick={() => setStoryLength(length)}
                        className={`px-4 py-3 rounded-lg border-2 font-medium transition ${
                          storyLength === length
                            ? 'border-purple-500 bg-purple-50 text-purple-700'
                            : 'border-gray-300 hover:border-purple-300'
                        }`}
                      >
                        {length. charAt(0).toUpperCase() + length.slice(1)}
                        <div className="text-xs text-gray-500 mt-1">
                          {length === 'short' ? '5-6 scenes' : length === 'medium' ? '8-10 scenes' : '12-14 scenes'}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Story Tone */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Story Tone
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {(['funny', 'adventurous', 'gentle'] as StoryTone[]).map((tone) => (
                      <button
                        key={tone}
                        onClick={() => setStoryTone(tone)}
                        className={`px-4 py-3 rounded-lg border-2 font-medium transition ${
                          storyTone === tone
                            ? 'border-purple-500 bg-purple-50 text-purple-700'
                            : 'border-gray-300 hover:border-purple-300'
                        }`}
                      >
                        {tone === 'funny' ? '😄 Funny' : tone === 'adventurous' ? '⚔️ Adventurous' :  '🌙 Gentle Bedtime'}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Section 3: Style Options */}
              <div className="border-b pb-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                  🎨 Style Options
                </h2>

                {/* Image Style */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Image Style
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {imageStyles.map((style) => (
                      <button
                        key={style. value}
                        onClick={() => setImageStyle(style.value)}
                        className={`p-4 rounded-lg border-2 transition ${
                          imageStyle === style. value
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-gray-300 hover:border-purple-300'
                        }`}
                      >
                        <div className="text-3xl mb-1">{style.emoji}</div>
                        <div className="text-xs font-medium">{style. label}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Voice Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Narrator Voice
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {voices.map((v) => (
                      <button
                        key={v.value}
                        onClick={() => setVoice(v.value)}
                        className={`px-4 py-3 rounded-lg border-2 transition flex items-center gap-2 ${
                          voice === v. value
                            ? 'border-purple-500 bg-purple-50 text-purple-700'
                            : 'border-gray-300 hover:border-purple-300'
                        }`}
                      >
                        <span className="text-2xl">{v.icon}</span>
                        <span className="text-sm font-medium">{v. label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Error */}
              {(error || generationError) && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                  {error || generationError}
                </div>
              )}

              {/* Generate Button */}
              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white text-xl font-bold py-5 rounded-xl hover: from-purple-700 hover: to-pink-700 disabled: opacity-50 disabled:cursor-not-allowed transition shadow-lg flex items-center justify-center gap-2"
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

              <p className="text-center text-sm text-gray-500">
                First scene ready in ~15 seconds • Full story in 30-60 seconds • Age 4-10 recommended
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CreateStory() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <CreateStoryContent />
    </Suspense>
  );
}