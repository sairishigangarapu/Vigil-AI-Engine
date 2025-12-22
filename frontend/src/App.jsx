// src/App.js
import React, { useState } from 'react';
import axios from 'axios';
import UrlInput from './components/UrlInput';
import FileUpload from './components/FileUpload';
import LoadingIndicator from './components/LoadingIndicator';
import ReportCard from './components/ReportCard';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('url'); // 'url' or 'file'
  const [currentFileType, setCurrentFileType] = useState(null); // Track file type for loading messages

  const handleAnalyzeUrl = async (url) => {
    setIsLoading(true);
    setReportData(null);
    setError('');
    
    // Detect URL type based on common patterns
    let urlType = 'webpage'; // Default to webpage
    if (url.includes('youtube.com') || url.includes('youtu.be')) {
      urlType = 'video';
    } else if (url.includes('twitter.com') || url.includes('x.com') || url.includes('facebook.com') || url.includes('instagram.com')) {
      urlType = 'social';
    } else if (url.match(/\.(mp4|avi|mov|mkv|webm)$/i)) {
      urlType = 'video';
    }
    
    setCurrentFileType(urlType);
    
    try {
      const response = await axios.post('http://localhost:8000/analyze', {
        video_url: url,
      });
      setReportData(response.data);
    } catch (err) {
      // Extract error message from response
      const errorMessage = err.response?.data?.detail || err.message || 'Analysis failed. Please try again.';
      setError(errorMessage);
      console.error('URL analysis error:', err);
      console.error('Error response:', err.response);
    } finally {
      setIsLoading(false);
      setCurrentFileType(null);
    }
  };

  const handleAnalyzeFile = async (file) => {
    setIsLoading(true);
    setReportData(null);
    setError('');
    
    // Detect file type
    const ext = file.name.split('.').pop().toLowerCase();
    let fileType = 'file';
    if (['mp4', 'avi', 'mov', 'mkv', 'webm'].includes(ext)) fileType = 'video';
    else if (['mp3', 'wav', 'm4a', 'aac'].includes(ext)) fileType = 'audio';
    else if (['pdf', 'docx', 'doc', 'txt'].includes(ext)) fileType = 'document';
    else if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) fileType = 'image';
    
    setCurrentFileType(fileType);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post('http://localhost:8000/analyze/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      console.log('File upload response:', response.data);
      setReportData(response.data);
    } catch (err) {
      // Extract error message from response
      const errorMessage = err.response?.data?.detail || err.message || 'File analysis failed. Please try again.';
      setError(errorMessage);
      console.error('File upload error:', err);
      console.error('Error response:', err.response);
    } finally {
      setIsLoading(false);
      setCurrentFileType(null);
    }
  };

  return (
    <div className="bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900 text-white min-h-screen flex flex-col items-center p-8 font-sans">
      {/* Header with gradient accent */}
      <div className="text-center mb-8">
        <h1 className="text-6xl font-bold mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent leading-tight py-2">
          Vigil AI
        </h1>
        <p className="text-gray-400 text-lg">Your AI-powered truth navigator for media verification</p>
      </div>
      
      {/* Tab Switcher with improved styling */}
      <div className="flex gap-2 mb-8 bg-gray-800/50 backdrop-blur-sm p-1.5 rounded-xl border border-gray-700/50 shadow-lg">
        <button
          onClick={() => setActiveTab('url')}
          className={`px-8 py-3 rounded-lg font-semibold transition-all duration-200 ${
            activeTab === 'url'
              ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/50'
              : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
          }`}
        >
          🔗 Analyze URL
        </button>
        <button
          onClick={() => setActiveTab('file')}
          className={`px-8 py-3 rounded-lg font-semibold transition-all duration-200 ${
            activeTab === 'file'
              ? 'bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg shadow-purple-500/50'
              : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
          }`}
        >
          📤 Upload File
        </button>
      </div>

      {/* Content based on active tab */}
      {activeTab === 'url' ? (
        <UrlInput onAnalyze={handleAnalyzeUrl} isLoading={isLoading} />
      ) : (
        <FileUpload onAnalyze={handleAnalyzeFile} isLoading={isLoading} />
      )}

      {isLoading && <LoadingIndicator fileType={currentFileType} />}
      {error && (
        <div className="mt-6 p-4 bg-red-900/30 border border-red-500/50 rounded-lg backdrop-blur-sm max-w-2xl w-full">
          <p className="text-red-400 text-center">⚠️ {error}</p>
        </div>
      )}
      {reportData && <ReportCard data={reportData} />}
    </div>
  );
}

export default App;
