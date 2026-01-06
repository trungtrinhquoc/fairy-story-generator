export type StoryLength = "short" | "medium" | "long";
export type StoryTone = "funny" | "adventurous" | "gentle";
export type Theme = "princess" | "dragon" | "forest" | "ocean" | "space" | "magical_forest" | "castle" | "adventure" | "cute_animals" | "robot" | "superhero" | "friendship" | "school_life" | "family_love";

export interface StoryRequest {
  prompt: string;
  story_length: StoryLength;
  story_tone: StoryTone;
  theme?:  Theme;
  child_name?: string;
  image_style?: string;
  voice?:  string;
}

export interface Scene {
  id: string;
  sceneOrder: number;
  paragraphText: string;
  imageUrl:  string;
  audioUrl:  string;
  audioDuration?:  number;
  wordCount?: number;
}

export interface Story {
  id: string;
  title: string;
  shortTitle?:  string;          
  thumbnailUrl?: string;        
  characterName?: string;        
  storyLength: StoryLength;
  storyTone: StoryTone;
  themeSelected: string;
  status: "generating" | "completed" | "failed";
  coverImageUrl:  string;
  createdAt: string;
  scenes: Scene[];
}

export interface StoryListItem {
  id: string;
  title: string;
  shortTitle?: string;
  thumbnailUrl?: string;
  characterName?: string;
  themeSelected: string;
  status: "generating" | "completed" | "failed";
  coverImageUrl?:  string;
  createdAt:  string;
  sceneCount?: number;
}