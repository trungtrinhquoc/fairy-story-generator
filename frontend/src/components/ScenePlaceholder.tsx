'use client';

export default function ScenePlaceholder({ sceneNumber }: { sceneNumber: number }) {
  return (
    <div className="border rounded-lg p-6 animate-pulse">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 bg-gray-300 rounded-full" />
        <div className="h-4 bg-gray-300 rounded w-32" />
      </div>
      
      <div className="w-full aspect-video bg-gray-300 rounded-lg mb-4 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-2" />
          <p className="text-gray-500 text-sm">Đang tạo scene {sceneNumber}...</p>
        </div>
      </div>
      
      <div className="space-y-2">
        <div className="h-3 bg-gray-300 rounded w-full" />
        <div className="h-3 bg-gray-300 rounded w-5/6" />
      </div>
    </div>
  );
}