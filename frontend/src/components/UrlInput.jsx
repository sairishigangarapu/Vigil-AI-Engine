// src/components/UrlInput.js
import React, { useState } from 'react';

export default function UrlInput({ onAnalyze, isLoading }) {
  const [url, setUrl] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (url) {
      onAnalyze(url);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl">
      <div className="flex flex-col gap-4">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
            <span className="text-2xl">🔗</span>
          </div>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Enter a URL..."
            className="w-full pl-14 pr-4 py-4 bg-gray-800/50 backdrop-blur-sm border-2 border-gray-700/50 rounded-xl text-white text-lg placeholder-gray-500 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all duration-200"
            disabled={isLoading}
            required
          />
        </div>
        <button
          type="submit"
          disabled={isLoading || !url}
          className={`w-full py-4 rounded-xl font-bold text-lg transition-all duration-200 ${
            isLoading || !url
              ? 'bg-gray-700/50 text-gray-500 cursor-not-allowed'
              : 'bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white shadow-lg hover:shadow-blue-500/50 hover:scale-[1.02]'
          }`}
        >
          {isLoading ? '⏳ Analyzing...' : '🚀 Analyze URL'}
        </button>
      </div>
      
      <div className="mt-6 text-center">
        <p className="text-gray-500 text-sm mb-3">Supported platforms:</p>
        <div className="flex flex-wrap justify-center gap-3">
          <span className="px-4 py-2 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300 text-sm font-medium">
            📺 YouTube
          </span>
          <span className="px-4 py-2 bg-blue-500/20 border border-blue-500/30 rounded-lg text-blue-300 text-sm font-medium">
            🎵 Social Media
          </span>
          <span className="px-4 py-2 bg-purple-500/20 border border-purple-500/30 rounded-lg text-purple-300 text-sm font-medium">
            🌐 Direct Links
          </span>
        </div>
      </div>
    </form>
  );
}
