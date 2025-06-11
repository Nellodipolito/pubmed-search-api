import React from 'react';
import { 
  FaExclamationTriangle, 
  FaChartLine, 
  FaStethoscope, 
  FaPills,
  FaChartBar,
  FaBook,
  FaCalendarCheck,
  FaExternalLinkAlt
} from 'react-icons/fa';

const RecommendationSection = ({ title, icon: Icon, children, className = "" }) => (
  <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
    <div className="flex items-center space-x-2 mb-4">
      <Icon className="h-6 w-6 text-gray-600" />
      <h3 className="text-xl font-semibold text-gray-900">{title}</h3>
    </div>
    {children}
  </div>
);

const Badge = ({ type, children }) => {
  const colors = {
    urgent: "bg-red-100 text-red-800",
    warning: "bg-yellow-100 text-yellow-800",
    info: "bg-blue-100 text-blue-800",
    success: "bg-green-100 text-green-800"
  };

  return (
    <span className={`px-2 py-1 rounded-full text-sm ${colors[type] || colors.info}`}>
      {children}
    </span>
  );
};

const ClinicalRecommendations = ({ recommendations }) => {
  if (!recommendations) return null;

  return (
    <div className="space-y-6">
      {/* Urgent Actions */}
      {recommendations.urgent_actions?.length > 0 && (
        <RecommendationSection 
          title="Urgent Actions" 
          icon={FaExclamationTriangle}
          className="border-l-4 border-red-500"
        >
          <div className="space-y-4">
            {recommendations.urgent_actions.map((action, idx) => (
              <div key={idx} className="flex items-start space-x-3 bg-red-50 p-4 rounded-lg">
                <FaExclamationTriangle className="h-5 w-5 text-red-600 mt-1" />
                <div>
                  <div className="font-medium text-red-900">{action.action}</div>
                  <div className="text-sm text-red-700 mt-1">{action.rationale}</div>
                  <div className="flex items-center space-x-2 mt-2">
                    <Badge type="info">{action.guideline}</Badge>
                    <Badge type="warning">{action.evidence_level}</Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </RecommendationSection>
      )}

      {/* Risk Assessment */}
      {recommendations.risk_assessment?.length > 0 && (
        <RecommendationSection title="Risk Assessment" icon={FaChartLine}>
          <div className="grid gap-4 md:grid-cols-2">
            {recommendations.risk_assessment.map((assessment, idx) => (
              <div key={idx} className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900">{assessment.tool}</h4>
                <p className="text-sm text-gray-600 mt-1">{assessment.description}</p>
                {assessment.score && (
                  <div className="mt-2">
                    <Badge type="info">Score: {assessment.score}</Badge>
                  </div>
                )}
              </div>
            ))}
          </div>
        </RecommendationSection>
      )}

      {/* Diagnostic Recommendations */}
      {recommendations.diagnostics?.length > 0 && (
        <RecommendationSection title="Diagnostic Workup" icon={FaStethoscope}>
          <div className="space-y-4">
            {recommendations.diagnostics.map((diagnostic, idx) => (
              <div key={idx} className="flex items-start space-x-3 border-b border-gray-200 pb-4 last:border-0">
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{diagnostic.test}</div>
                  <div className="text-sm text-gray-600 mt-1">{diagnostic.rationale}</div>
                  <div className="flex items-center space-x-2 mt-2">
                    <Badge type={diagnostic.priority === 'high' ? 'urgent' : 'info'}>
                      {diagnostic.priority}
                    </Badge>
                    <span className="text-sm text-gray-500">{diagnostic.guideline}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </RecommendationSection>
      )}

      {/* Medication Recommendations */}
      {recommendations.medications?.length > 0 && (
        <RecommendationSection title="Medication Recommendations" icon={FaPills}>
          <div className="space-y-4">
            {recommendations.medications.map((medication, idx) => (
              <div key={idx} className="bg-gray-50 p-4 rounded-lg">
                <div className="font-medium text-gray-900">{medication.action}</div>
                <div className="text-sm text-gray-600 mt-1">{medication.rationale}</div>
                {medication.examples && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {medication.examples.map((example, i) => (
                      <Badge key={i} type="info">{example}</Badge>
                    ))}
                  </div>
                )}
                <div className="text-sm text-gray-500 mt-2">{medication.guideline}</div>
              </div>
            ))}
          </div>
        </RecommendationSection>
      )}

      {/* Monitoring Plan */}
      {recommendations.monitoring?.length > 0 && (
        <RecommendationSection title="Monitoring Plan" icon={FaChartBar}>
          <div className="space-y-4">
            {recommendations.monitoring.map((plan, idx) => (
              <div key={idx} className="flex items-start space-x-3 border-b border-gray-200 pb-4 last:border-0">
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{plan.action}</div>
                  <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Frequency:</span>
                      <span className="ml-2 text-gray-900">{plan.frequency}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Duration:</span>
                      <span className="ml-2 text-gray-900">{plan.duration}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Target:</span>
                      <span className="ml-2 text-gray-900">{plan.target}</span>
                    </div>
                  </div>
                  <div className="text-sm text-gray-500 mt-2">{plan.guideline}</div>
                </div>
              </div>
            ))}
          </div>
        </RecommendationSection>
      )}

      {/* Patient Education */}
      {recommendations.patient_education?.length > 0 && (
        <RecommendationSection title="Patient Education" icon={FaBook}>
          <div className="space-y-6">
            {recommendations.patient_education.map((education, idx) => (
              <div key={idx} className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900">{education.topic}</h4>
                <div className="mt-3">
                  <h5 className="text-sm font-medium text-gray-700">Key Points:</h5>
                  <ul className="mt-2 space-y-2">
                    {education.key_points.map((point, i) => (
                      <li key={i} className="text-sm text-gray-600 flex items-start">
                        <span className="mr-2">•</span>
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="mt-3">
                  <h5 className="text-sm font-medium text-gray-700">Resources:</h5>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {education.resources.map((resource, i) => (
                      <a
                        key={i}
                        href="#"
                        className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800"
                      >
                        {resource}
                        <FaExternalLinkAlt className="ml-1 h-3 w-3" />
                      </a>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </RecommendationSection>
      )}

      {/* Follow-up Schedule */}
      {recommendations.follow_up?.length > 0 && (
        <RecommendationSection title="Follow-up Schedule" icon={FaCalendarCheck}>
          <div className="space-y-4">
            {recommendations.follow_up.map((followUp, idx) => (
              <div key={idx} className="flex items-start space-x-3 border-b border-gray-200 pb-4 last:border-0">
                <div className="flex-1">
                  <div className="font-medium text-gray-900">
                    {followUp.timing} - {followUp.purpose}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    Recommended modality: {followUp.modality}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </RecommendationSection>
      )}
    </div>
  );
};

export default ClinicalRecommendations; 