export type StoryLength = "short" | "medium" | "long";
export type StoryTone = "funny" | "adventurous" | "gentle";
export type Theme = "princess" | "dragon" | "forest" | "ocean" | "space" | "magical_forest" | "castle" | "adventure";

export interface StoryRequest {
  prompt: string;
  story_length: StoryLength;
  story_tone: StoryTone;
  theme?: Theme;
  child_name?: string;
  image_style?: string;
  voice?: string;
}

export interface Scene {
  id: string;
  scene_order: number;
  paragraph_text: string;
  image_url: string;
  audio_url: string;
  audio_duration?: number;
  word_count?: number;
}

export interface Story {
  id: string;
  title: string;
  story_length: StoryLength;
  story_tone: StoryTone;
  theme_selected: string;
  status: "generating" | "completed" | "failed";
  cover_image_url: string;
  created_at: string;
  scenes: Scene[];
}