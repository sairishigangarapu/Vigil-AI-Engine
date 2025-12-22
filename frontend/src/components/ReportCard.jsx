// src/components/ReportCard.js
import React from 'react';

export default function ReportCard({ data }) {
  // Debug: log the data
  console.log('ReportCard received data:', data);
  
  if (!data) return null;
  
  if (!data.report) {
    // Fallback: show raw data if report structure is missing
    return (
      <div className="mt-8 w-full max-w-4xl bg-gray-800 rounded-lg p-6 shadow-lg">
        <h2 className="text-2xl font-bold mb-4">Analysis Result</h2>
        <div className="bg-gray-700 p-4 rounded-lg">
          <pre className="text-sm whitespace-pre-wrap overflow-auto max-h-96">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      </div>
    );
  }

  const isFactCheck = data.source === 'Google Fact-Check Database';
  const report = data.report;

  // Helper function to normalize keys (handle both snake_case and "Spaced Words")
  const normalizeKey = (obj, possibleKeys) => {
    if (!obj) return null;
    
    // Try direct key match first
    for (let key of possibleKeys) {
      if (obj[key]) return obj[key];
    }
    
    // Try case-insensitive match
    const objKeys = Object.keys(obj);
    for (let key of possibleKeys) {
      const match = objKeys.find(k => 
        k.toLowerCase().replace(/[_\s]/g, '') === key.toLowerCase().replace(/[_\s]/g, '')
      );
      if (match) return obj[match];
    }
    
    return null;
  };

  // Get normalized fields for audio analysis
  const audioAuth = normalizeKey(report, ['audio_authenticity_assessment', 'Audio Authenticity Assessment']);
  const contentAnalysis = normalizeKey(report, ['content_analysis', 'Content Analysis']);
  const misinfo = normalizeKey(report, ['misinformation_indicators', 'Misinformation Indicators']);
  const redFlags = normalizeKey(report, ['red_flags', 'Red Flags']);
  const finalVerdict = normalizeKey(report, ['final_verdict', 'Final Verdict', 'final_verdict']);
  
  // Get PDF-specific fields
  const docCredibility = normalizeKey(report, ['document_credibility', 'Document Credibility']);
  const extractedTextSummary = normalizeKey(report, ['extracted_text_summary', 'Extracted Text Summary']);
  const authenticityIndicators = normalizeKey(report, ['authenticity_indicators', 'Authenticity Indicators']);
  const factVerification = normalizeKey(report, ['fact_verification', 'Fact Verification']);

  // Helper function to render an object's key-value pairs
  const renderObjectFields = (obj, title) => {
    if (!obj || typeof obj !== 'object') return null;
    
    return (
      <div className="bg-gray-800/50 backdrop-blur-sm p-6 rounded-xl mb-6 border border-gray-700/30 shadow-lg hover:shadow-xl transition-all duration-200">
        <h3 className="font-bold mb-4 text-xl text-white flex items-center gap-2">
          {title}
        </h3>
        {Object.entries(obj).map(([key, value]) => {
          // Skip if value is null/undefined
          if (value === null || value === undefined) return null;
          
          // Handle arrays
          if (Array.isArray(value)) {
            return (
              <div key={key} className="mb-4">
                <p className="text-blue-400 text-sm font-semibold mb-2">
                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </p>
                <ul className="list-disc pl-6 space-y-2 bg-gray-900/30 p-4 rounded-lg">
                  {value.map((item, idx) => (
                    <li key={idx} className="text-gray-300 leading-relaxed">{item}</li>
                  ))}
                </ul>
              </div>
            );
          }
          
          // Handle objects
          if (typeof value === 'object') {
            return (
              <div key={key} className="mb-4">
                <p className="text-blue-400 text-sm font-semibold mb-2">
                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </p>
                <div className="pl-4 border-l-2 border-blue-500/30 bg-gray-900/30 p-4 rounded-r-lg">
                  {Object.entries(value).map(([subKey, subValue]) => (
                    <div key={subKey} className="mb-3">
                      <span className="text-purple-400 text-xs font-medium">{subKey.replace(/_/g, ' ')}:</span>
                      <p className="text-gray-300 mt-1 leading-relaxed">{String(subValue)}</p>
                    </div>
                  ))}
                </div>
              </div>
            );
          }
          
          // Handle strings/numbers
          return (
            <div key={key} className="mb-4">
              <p className="text-blue-400 text-sm font-semibold mb-1">
                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </p>
              <p className="text-gray-300 whitespace-pre-wrap leading-relaxed bg-gray-900/30 p-3 rounded-lg">{String(value)}</p>
            </div>
          );
        })}
      </div>
    );
  };

  // Helper function to render risk level badge
  const renderRiskBadge = (riskLevel) => {
    const colors = {
      'Low Risk': 'bg-green-600',
      'Medium Risk': 'bg-yellow-600',
      'High Risk': 'bg-red-600'
    };
    
    return (
      <span className={`${colors[riskLevel] || 'bg-gray-600'} text-white px-3 py-1 rounded-full text-sm font-medium`}>
        {riskLevel}
      </span>
    );
  };

  return (
    <div className="mt-10 w-full max-w-4xl bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-md rounded-2xl p-8 shadow-2xl border border-gray-700/50">
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-700/50">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent leading-tight py-2">
          {isFactCheck ? '🔍 Fact-Check Result' : '🤖 Vigil AI Analysis'}
        </h2>
        {!isFactCheck && report.risk_level && renderRiskBadge(report.risk_level)}
      </div>
      
      {isFactCheck ? (
        // Render Google Fact Check result
        <div>
          <div className="bg-gray-700 p-4 rounded-lg mb-4">
            <h3 className="font-bold mb-2">Claim</h3>
            <p>{report.text || 'No claim text available'}</p>
            
            {report.claimant && (
              <p className="mt-2 text-gray-400">
                Claimed by: <span className="text-white">{report.claimant}</span>
              </p>
            )}
          </div>
          
          {report.rating && (
            <div className="bg-gray-700 p-4 rounded-lg mb-4">
              <h3 className="font-bold mb-2">Rating</h3>
              <div className="flex items-center">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  report.rating.toLowerCase().includes('false') ? 'bg-red-600' : 
                  report.rating.toLowerCase().includes('true') ? 'bg-green-600' : 'bg-yellow-600'
                }`}>
                  {report.rating}
                </span>
              </div>
            </div>
          )}
          
          {report.url && (
            <div className="mt-4">
              <a 
                href={report.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300"
              >
                Read the full fact-check →
              </a>
            </div>
          )}
        </div>
      ) : (
        // Render Gemini Analysis result
        <div>
          {/* Audio/Document/Image Analysis - Final Verdict (string format) */}
          {finalVerdict && typeof finalVerdict === 'string' && (
            <div className="bg-gray-700 p-4 rounded-lg mb-4">
              <h3 className="font-bold mb-2">🎯 Final Verdict</h3>
              <div className="flex items-center gap-3 mb-2">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  finalVerdict.toLowerCase().includes('authentic') ? 'bg-green-600' :
                  finalVerdict.toLowerCase().includes('suspicious') ? 'bg-yellow-600' :
                  finalVerdict.toLowerCase().includes('manipulated') || finalVerdict.toLowerCase().includes('error') ? 'bg-red-600' : 'bg-gray-600'
                }`}>
                  {finalVerdict.split('.')[0]}
                </span>
              </div>
              <p className="mt-2">{finalVerdict}</p>
            </div>
          )}

          {/* Audio/Document/Image Analysis - Final Verdict (object format) */}
          {finalVerdict && typeof finalVerdict === 'object' && (
            <div className="bg-gray-700 p-4 rounded-lg mb-4">
              <h3 className="font-bold mb-2">🎯 Final Verdict</h3>
              <div className="flex items-center gap-3 mb-2">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  (finalVerdict.overall_assessment || finalVerdict.conclusion || '')?.toLowerCase().includes('authentic') ? 'bg-green-600' :
                  (finalVerdict.overall_assessment || finalVerdict.conclusion || '')?.toLowerCase().includes('suspicious') ? 'bg-yellow-600' :
                  (finalVerdict.overall_assessment || finalVerdict.conclusion || '')?.toLowerCase().includes('manipulated') ? 'bg-red-600' : 'bg-gray-600'
                }`}>
                  {finalVerdict.overall_assessment || finalVerdict.conclusion || 'See details'}
                </span>
                {(finalVerdict.confidence_level || finalVerdict.trustworthiness_score) && (
                  <span className="text-gray-400">
                    {finalVerdict.confidence_level ? `Confidence: ${finalVerdict.confidence_level}` : 
                     finalVerdict.trustworthiness_score ? `Score: ${finalVerdict.trustworthiness_score}/100` : ''}
                  </span>
                )}
              </div>
              {(finalVerdict.reasoning || finalVerdict.recommendation) && (
                <p className="mt-2">{finalVerdict.reasoning || finalVerdict.recommendation}</p>
              )}
            </div>
          )}

          {/* PDF/Document-Specific Fields */}
          {docCredibility && renderObjectFields(docCredibility, '📄 Document Credibility')}
          
          {extractedTextSummary && renderObjectFields(extractedTextSummary, '📝 Extracted Text Summary')}
          
          {authenticityIndicators && renderObjectFields(authenticityIndicators, '🔍 Authenticity Indicators')}
          
          {factVerification && renderObjectFields(factVerification, '✅ Fact Verification')}

          {/* Audio Authenticity Assessment */}
          {audioAuth && (
            <div className="bg-gray-700 p-4 rounded-lg mb-4">
              <h3 className="font-bold mb-2">🎤 Audio Authenticity</h3>
              {Object.entries(audioAuth).map(([key, value]) => (
                <div key={key} className="mb-3">
                  <p className="text-blue-400 text-sm font-semibold">
                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </p>
                  <p className="text-gray-300">{value}</p>
                </div>
              ))}
            </div>
          )}

          {/* Content Analysis */}
          {contentAnalysis && renderObjectFields(contentAnalysis, '📊 Content Analysis')}

          {/* Misinformation Indicators */}
          {misinfo && renderObjectFields(misinfo, '⚠️ Misinformation Indicators')}

          {/* Video Analysis Fields (original) */}
          {report.summary && (
            <div className="bg-gray-700 p-4 rounded-lg mb-4">
              <h3 className="font-bold mb-2">Summary</h3>
              <p>{report.summary}</p>
            </div>
          )}
          
          {report.context_check && (
            <div className="bg-gray-700 p-4 rounded-lg mb-4">
              <h3 className="font-bold mb-2">Context Check</h3>
              <div className="flex items-center mb-2">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  report.context_check.status.includes('No') ? 'bg-yellow-600' : 'bg-blue-600'
                }`}>
                  {report.context_check.status}
                </span>
              </div>
              <p>{report.context_check.details}</p>
            </div>
          )}
          
          {report.claim_verification && (
            <div className="bg-gray-700 p-4 rounded-lg mb-4">
              <h3 className="font-bold mb-2">Claim Verification</h3>
              <div className="flex items-center mb-2">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  report.claim_verification.status.toLowerCase().includes('corroborated') ? 'bg-green-600' : 
                  report.claim_verification.status.toLowerCase().includes('refuted') ? 'bg-red-600' : 'bg-yellow-600'
                }`}>
                  {report.claim_verification.status}
                </span>
              </div>
              <p>{report.claim_verification.details}</p>
            </div>
          )}
          
          {/* Red Flags - for audio/document/image analysis */}
          {redFlags && Array.isArray(redFlags) && redFlags.length > 0 && (
            <div className="bg-gray-700 p-4 rounded-lg mb-4">
              <h3 className="font-bold mb-2">🚩 Red Flags</h3>
              <ul className="list-disc pl-5 space-y-1">
                {redFlags.map((flag, index) => (
                  <li key={index} className="text-red-400">{flag}</li>
                ))}
              </ul>
            </div>
          )}
          
          {report.visual_red_flags && report.visual_red_flags.length > 0 && (
            <div className="bg-gray-700 p-4 rounded-lg">
              <h3 className="font-bold mb-2">Visual Red Flags</h3>
              <ul className="list-disc pl-5 space-y-1">
                {report.visual_red_flags.map((flag, index) => (
                  <li key={index}>{flag}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
