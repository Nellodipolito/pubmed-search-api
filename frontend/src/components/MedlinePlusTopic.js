import React from 'react';
import DOMPurify from 'dompurify';
import { FaExternalLinkAlt } from 'react-icons/fa';

const MedlinePlusTopic = ({ topic }) => {
  const createMarkup = (html) => {
    return {
      __html: DOMPurify.sanitize(html, {
        ALLOWED_TAGS: ['p', 'ul', 'li', 'span', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
        ALLOWED_ATTR: ['class']
      })
    };
  };

  const renderContent = (content) => {
    // Handle sections with headers
    const sections = content.split(/(?=<h[1-6]>)/);
    
    return sections.map((section, index) => {
      if (section.trim()) {
        return (
          <div key={index} className="mb-4">
            <div 
              dangerouslySetInnerHTML={createMarkup(section)}
              className="prose max-w-none"
            />
          </div>
        );
      }
      return null;
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
      <div className="flex items-start justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">
          <a
            href={topic.url}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-blue-600 flex items-center"
          >
            {topic.title}
            <FaExternalLinkAlt className="ml-2 h-4 w-4" />
          </a>
        </h2>
      </div>

      <div className="text-gray-700">
        {renderContent(topic.summary)}
      </div>

      {topic.mesh_terms && topic.mesh_terms.length > 0 && (
        <div className="mt-4">
          <div className="flex flex-wrap gap-2">
            {topic.mesh_terms.map((term, idx) => (
              <span
                key={idx}
                className="px-2 py-1 bg-green-100 text-green-800 text-sm rounded-full"
              >
                {term}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MedlinePlusTopic; 