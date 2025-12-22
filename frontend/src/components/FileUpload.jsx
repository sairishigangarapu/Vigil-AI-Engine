// src/components/FileUpload.js
import React, { useState } from 'react';

function FileUpload({ onAnalyze, isLoading }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = () => {
    if (selectedFile && !isLoading) {
      onAnalyze(selectedFile);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
      'mp4': '🎬', 'avi': '🎬', 'mov': '🎬', 'mkv': '🎬', 'webm': '🎬',
      'mp3': '🎵', 'wav': '🎵', 'm4a': '🎵', 'aac': '🎵',
      'pdf': '📄', 'docx': '📄', 'doc': '📄', 'txt': '📄',
      'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'webp': '🖼️'
    };
    return icons[ext] || '📁';
  };

  return (
    <div className="w-full max-w-2xl">
      <div 
        className={`border-2 border-dashed rounded-xl p-10 text-center transition-all duration-300 backdrop-blur-sm ${
          dragActive 
            ? 'border-purple-500 bg-purple-500/20 shadow-lg shadow-purple-500/30 scale-105' 
            : 'border-gray-600/50 hover:border-purple-500/50 hover:bg-gray-800/30 bg-gray-800/20'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          className="hidden"
          onChange={handleFileSelect}
          accept=".mp4,.avi,.mov,.mkv,.webm,.mp3,.wav,.m4a,.aac,.pdf,.docx,.doc,.txt,.jpg,.jpeg,.png,.gif,.webp"
        />
        
        {!selectedFile ? (
          <>
            <div className="text-7xl mb-6 animate-bounce">📤</div>
            <label 
              htmlFor="file-upload" 
              className="cursor-pointer text-transparent bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text hover:from-blue-300 hover:to-purple-300 font-bold text-lg transition-all"
            >
              Choose a file
            </label>
            <span className="text-gray-400 text-lg"> or drag it here</span>
            <div className="mt-6 space-y-3">
              <p className="text-gray-400 font-semibold">
                Supported File Types:
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                <span className="px-3 py-1 bg-blue-500/20 border border-blue-500/30 rounded-lg text-blue-300 text-sm">🎬 Video</span>
                <span className="px-3 py-1 bg-purple-500/20 border border-purple-500/30 rounded-lg text-purple-300 text-sm">🎵 Audio</span>
                <span className="px-3 py-1 bg-pink-500/20 border border-pink-500/30 rounded-lg text-pink-300 text-sm">📄 Documents</span>
                <span className="px-3 py-1 bg-green-500/20 border border-green-500/30 rounded-lg text-green-300 text-sm">🖼️ Images</span>
              </div>
              <p className="text-gray-600 text-xs mt-3">
                MP4, AVI, MOV, MP3, WAV, PDF, DOCX, JPG, PNG, and more...
              </p>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center space-y-4">
            <div className="text-7xl mb-2 animate-pulse">{getFileIcon(selectedFile.name)}</div>
            <div className="space-y-1">
              <p className="text-white font-bold text-lg">{selectedFile.name}</p>
              <p className="text-gray-400 text-sm">{formatFileSize(selectedFile.size)}</p>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={handleSubmit}
                disabled={isLoading}
                className={`px-8 py-3 rounded-xl font-bold transition-all duration-200 ${
                  isLoading
                    ? 'bg-gray-600 cursor-not-allowed opacity-50'
                    : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white shadow-lg hover:shadow-purple-500/50 hover:scale-105'
                }`}
              >
                {isLoading ? '⏳ Analyzing...' : '🚀 Analyze File'}
              </button>
              <button
                onClick={() => setSelectedFile(null)}
                disabled={isLoading}
                className="px-8 py-3 rounded-xl font-bold bg-gray-700/50 hover:bg-gray-600/50 text-white transition-all duration-200 border border-gray-600/50 hover:border-gray-500/50"
              >
                ✕ Remove
              </button>
            </div>
          </div>
        )}
      </div>
      
      <div className="mt-6 text-center">
        <div className="inline-flex items-center gap-4 px-6 py-3 bg-gray-800/30 backdrop-blur-sm rounded-full border border-gray-700/30">
          <span className="text-green-400 text-sm">✓ Deepfake Detection</span>
          <span className="text-gray-600">•</span>
          <span className="text-blue-400 text-sm">✓ Audio Forensics</span>
          <span className="text-gray-600">•</span>
          <span className="text-purple-400 text-sm">✓ Document Verification</span>
          <span className="text-gray-600">•</span>
          <span className="text-pink-400 text-sm">✓ Image Analysis</span>
        </div>
      </div>
    </div>
  );
}

export default FileUpload;
