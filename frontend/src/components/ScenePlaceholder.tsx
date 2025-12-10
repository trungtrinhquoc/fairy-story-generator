import { Loader2 } from 'lucide-react';

interface ScenePlaceholderProps {
  sceneNumber: number;
}

export default function ScenePlaceholder({ sceneNumber }: ScenePlaceholderProps) {
  return (
    <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-xl p-6 animate-pulse">
      <div className="flex items-center justify-center gap-3 py-12">
        <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
        <p className="text-gray-500 font-medium">
          Creating Scene {sceneNumber}...
        </p>
      </div>
      
      <div className="grid md:grid-cols-2 gap-6 mt-4">
        {/* Image placeholder */}
        <div className="w-full h-48 bg-gray-200 rounded-lg" />
        
        {/* Text placeholder */}
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded w-full" />
          <div className="h-4 bg-gray-200 rounded w-5/6" />
          <div className="h-4 bg-gray-200 rounded w-4/6" />
        </div>
      </div>
    </div>
  );
}