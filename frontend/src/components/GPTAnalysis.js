import React from 'react';
import { FaBookMedical, FaUserMd, FaClipboardList } from 'react-icons/fa';

const Citation = ({ reference }) => {
  const { source, title, authors, url, year } = reference;
  
  return (
    <div className="pl-4 border-l-2 border-gray-200 my-2">
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-600 hover:text-blue-800"
      >
        {title}
      </a>
      <div className="text-sm text-gray-600">
        {authors && `${authors.join(', ')} - `}
        {source} ({year})
      </div>
    </div>
  );
};

const AnalysisSection = ({ title, icon: Icon, children }) => (
  <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
    <div className="flex items-center space-x-2 mb-4">
      <Icon className="h-6 w-6 text-gray-600" />
      <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
    </div>
    {children}
  </div>
);

const GPTAnalysis = ({ analysis }) => {
  if (!analysis) return null;

  return (
    <div className="space-y-6">
      {/* Clinical Summary */}
      <AnalysisSection title="Clinical Summary" icon={FaUserMd}>
        <div className="prose max-w-none">
          {analysis.summary.map((paragraph, idx) => (
            <div key={idx} className="mb-4">
              <p className="text-gray-800">{paragraph.text}</p>
              {paragraph.citations && (
                <div className="mt-2">
                  {paragraph.citations.map((citation, cidx) => (
                    <Citation key={cidx} reference={citation} />
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </AnalysisSection>

      {/* Key Findings */}
      <AnalysisSection title="Key Findings" icon={FaClipboardList}>
        <div className="space-y-4">
          {analysis.findings.map((finding, idx) => (
            <div key={idx} className="border-b border-gray-200 pb-4 last:border-0">
              <div className="flex items-start">
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900">{finding.title}</h3>
                  <p className="text-gray-700 mt-1">{finding.description}</p>
                  {finding.evidence && (
                    <div className="mt-2">
                      <h4 className="text-sm font-medium text-gray-700">Supporting Evidence:</h4>
                      {finding.evidence.map((evidence, eidx) => (
                        <Citation key={eidx} reference={evidence} />
                      ))}
                    </div>
                  )}
                </div>
                <div className="ml-4">
                  <span className={`px-2 py-1 rounded-full text-sm ${
                    finding.strength === 'strong' 
                      ? 'bg-green-100 text-green-800'
                      : finding.strength === 'moderate'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {finding.strength} evidence
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </AnalysisSection>

      {/* Clinical Guidelines */}
      <AnalysisSection title="Clinical Guidelines" icon={FaBookMedical}>
        <div className="space-y-4">
          {analysis.guidelines.map((guideline, idx) => (
            <div key={idx} className="border-b border-gray-200 pb-4 last:border-0">
              <h3 className="font-medium text-gray-900">{guideline.organization}</h3>
              <p className="text-gray-700 mt-1">{guideline.recommendation}</p>
              <div className="mt-2 flex flex-wrap gap-2">
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                  Level {guideline.evidence_level}
                </span>
                <span className="px-2 py-1 bg-purple-100 text-purple-800 text-sm rounded-full">
                  Grade {guideline.recommendation_grade}
                </span>
                {guideline.year && (
                  <span className="px-2 py-1 bg-gray-100 text-gray-800 text-sm rounded-full">
                    {guideline.year}
                  </span>
                )}
              </div>
              {guideline.source && (
                <div className="mt-2">
                  <Citation reference={guideline.source} />
                </div>
              )}
            </div>
          ))}
        </div>
      </AnalysisSection>

      {/* Patient Resources */}
      {analysis.patient_resources && (
        <AnalysisSection title="Patient Education Resources" icon={FaBookMedical}>
          <div className="grid gap-4 md:grid-cols-2">
            {analysis.patient_resources.map((resource, idx) => (
              <div key={idx} className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-medium text-gray-900">{resource.title}</h3>
                <p className="text-gray-600 text-sm mt-1">{resource.description}</p>
                <a
                  href={resource.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 text-sm mt-2 inline-block"
                >
                  Learn more →
                </a>
              </div>
            ))}
          </div>
        </AnalysisSection>
      )}
    </div>
  );
};

export default GPTAnalysis; 