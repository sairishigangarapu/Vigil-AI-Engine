// src/components/LoadingIndicator.js
import React from 'react';

export default function LoadingIndicator({ fileType = 'file' }) {
  // Define messages based on file type
  const getMessages = () => {
    const messages = {
      video: {
        title: 'Analyzing video content...',
        steps: [
          '🎬 Downloading video data...',
          '🔍 Checking fact-check database...',
          '🎞️ Extracting video frames...',
          '🤖 Running AI deepfake detection...',
        ]
      },
      audio: {
        title: 'Analyzing audio content...',
        steps: [
          '🎵 Processing audio file...',
          '🔍 Checking fact-check database...',
          '🎙️ Extracting audio features...',
          '🤖 Running AI audio forensics...',
        ]
      },
      document: {
        title: 'Analyzing document...',
        steps: [
          '📄 Reading document content...',
          '📝 Extracting text...',
          '🔍 Checking for misinformation...',
          '🤖 Running AI credibility analysis...',
        ]
      },
      image: {
        title: 'Analyzing image...',
        steps: [
          '🖼️ Processing image file...',
          '🔍 Checking fact-check database...',
          '🎨 Detecting manipulation...',
          '🤖 Running AI authenticity check...',
        ]
      },
      webpage: {
        title: 'Analyzing webpage content...',
        steps: [
          '🌐 Fetching webpage data...',
          '🔍 Checking fact-check database...',
          '📰 Extracting article content...',
          '🤖 Running AI fact verification...',
        ]
      },
      social: {
        title: 'Analyzing social media content...',
        steps: [
          '📱 Downloading social media data...',
          '🔍 Checking fact-check database...',
          '💬 Extracting post content...',
          '🤖 Running AI misinformation detection...',
        ]
      },
      file: {
        title: 'Analyzing content...',
        steps: [
          '📁 Processing data...',
          '🔍 Checking fact-check database...',
          '📊 Extracting features...',
          '🤖 Running AI analysis...',
        ]
      }
    };

    return messages[fileType] || messages.file;
  };

  const { title, steps } = getMessages();

  return (
    <div className="mt-8 w-full max-w-2xl">
      <div className="flex items-center justify-center mb-6">
        <div className="relative">
          <div className="w-16 h-16 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-10 h-10 bg-blue-500/20 rounded-full animate-pulse"></div>
          </div>
        </div>
      </div>
      
      <p className="text-center text-2xl font-semibold mb-6 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
        {title}
      </p>
      
      <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50 shadow-xl">
        <ul className="space-y-4">
          {steps.map((step, index) => (
            <li 
              key={index} 
              className="flex items-center transition-all duration-300"
              style={{
                animation: `fadeInSlide 0.5s ease-out ${index * 0.2}s both`
              }}
            >
              <div className={`flex items-center ${
                index === 0 ? 'text-blue-400' : 
                index === 1 ? 'text-purple-400 animate-pulse' : 
                'text-gray-500'
              }`}>
                <svg 
                  className={`w-6 h-6 mr-3 ${index === 1 ? 'animate-spin' : ''}`} 
                  fill="currentColor" 
                  viewBox="0 0 20 20"
                >
                  {index === 0 ? (
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  ) : index === 1 ? (
                    <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                  ) : (
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clipRule="evenodd" />
                  )}
                </svg>
                <span className="text-base">{step}</span>
              </div>
            </li>
          ))}
        </ul>
      </div>
      
      <style jsx>{`
        @keyframes fadeInSlide {
          from {
            opacity: 0;
            transform: translateX(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
      `}</style>
    </div>
  );
}
