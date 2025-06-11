import React, { useState } from 'react';
import { FaSearch, FaExternalLinkAlt, FaFilter, FaTimes } from 'react-icons/fa';
import axios from 'axios';

const YEAR_FILTERS = [
  { value: "1", label: "Last Year" },
  { value: "5", label: "Last 5 Years" },
  { value: "10", label: "Last 10 Years" },
  { value: "", label: "All Time" }
];

const COMMON_ARTICLE_TYPES = [
  "Review",
  "Clinical Trial",
  "Meta-Analysis",
  "Randomized Controlled Trial",
  "Systematic Review",
  "Case Reports",
  "Comparative Study"
];

function App() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    yearFilter: "5",
    maxResults: 5,
    articleTypes: []
  });

  const handleSearch = async () => {
    if (!query.trim()) {
      alert('Please enter a search query');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/search', {
        text: query,
        max_results: filters.maxResults,
        year_filter: filters.yearFilter,
        article_types: filters.articleTypes.length > 0 ? filters.articleTypes : null
      });
      setResults(response.data);
    } catch (error) {
      alert(error.response?.data?.detail?.error || 'Failed to search PubMed');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const toggleArticleType = (type) => {
    setFilters(prev => ({
      ...prev,
      articleTypes: prev.articleTypes.includes(type)
        ? prev.articleTypes.filter(t => t !== type)
        : [...prev.articleTypes, type]
    }));
  };

  const renderFilters = () => (
    <div className="bg-white rounded-lg shadow p-4 mb-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Search Filters</h3>
        <button
          onClick={() => setShowFilters(false)}
          className="text-gray-500 hover:text-gray-700"
        >
          <FaTimes />
        </button>
      </div>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Time Period
          </label>
          <select
            value={filters.yearFilter}
            onChange={(e) => setFilters(prev => ({ ...prev, yearFilter: e.target.value }))}
            className="w-full rounded-md border border-gray-300 p-2"
          >
            {YEAR_FILTERS.map(filter => (
              <option key={filter.value} value={filter.value}>
                {filter.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Maximum Results
          </label>
          <input
            type="number"
            min="1"
            max="100"
            value={filters.maxResults}
            onChange={(e) => setFilters(prev => ({ ...prev, maxResults: parseInt(e.target.value) || 5 }))}
            className="w-full rounded-md border border-gray-300 p-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Article Types
          </label>
          <div className="flex flex-wrap gap-2">
            {COMMON_ARTICLE_TYPES.map(type => (
              <button
                key={type}
                onClick={() => toggleArticleType(type)}
                className={`px-3 py-1 rounded-full text-sm ${
                  filters.articleTypes.includes(type)
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderMetadataTags = (citation) => (
    <div className="flex flex-wrap gap-2 mt-2">
      {citation.publication_types?.map((type, idx) => (
        <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
          {type}
        </span>
      ))}
      {citation.mesh_terms?.slice(0, 5).map((term, idx) => (
        <span key={idx} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
          {term}
        </span>
      ))}
      {citation.keywords?.slice(0, 3).map((keyword, idx) => (
        <span key={idx} className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
          {keyword}
        </span>
      ))}
    </div>
  );

  const renderCitation = (citation) => (
    <div key={citation.number} className="flex items-start space-x-2 py-4">
      <span className="text-gray-500 font-medium">[{citation.number}]</span>
      <div className="flex-1">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <a
              href={citation.urls.pubmed}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 font-medium flex items-center"
            >
              {citation.title}
              <FaExternalLinkAlt className="ml-1 h-3 w-3" />
            </a>
            <p className="text-sm text-gray-600 mt-1">
              {citation.authors.join(', ')}
            </p>
            <p className="text-sm text-gray-500">
              {citation.journal} ({citation.year})
            </p>
          </div>
          <div className="flex flex-col items-end ml-4 space-y-1">
            {citation.urls.pmc && (
              <a
                href={citation.urls.pmc}
                target="_blank"
                rel="noopener noreferrer"
                className="text-green-600 hover:text-green-800 text-sm"
              >
                Full Text (PMC)
              </a>
            )}
            {citation.urls.doi && (
              <a
                href={citation.urls.doi}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                DOI
              </a>
            )}
          </div>
        </div>
        {renderMetadataTags(citation)}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="space-y-8">
          <h1 className="text-4xl font-bold text-center text-gray-900">
            PubMed Natural Language Search
          </h1>
          
          <div className="w-full space-y-4">
            <div className="relative">
              <input
                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
                placeholder="Enter your medical research question..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex space-x-2">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="p-2 text-gray-500 hover:text-gray-700 focus:outline-none"
                  title="Show filters"
                >
                  <FaFilter className="w-5 h-5" />
                </button>
                <button
                  className="p-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  onClick={handleSearch}
                  disabled={loading}
                >
                  {loading ? (
                    <div className="w-5 h-5 border-t-2 border-white rounded-full animate-spin" />
                  ) : (
                    <FaSearch className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>

            {showFilters && renderFilters()}
          </div>

          {loading && (
            <div className="text-center py-10">
              <div className="w-12 h-12 border-t-4 border-blue-500 rounded-full animate-spin mx-auto"></div>
              <p className="mt-4 text-gray-600">Searching PubMed and generating summary...</p>
            </div>
          )}

          {results && !loading && (
            <div className="space-y-8">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Summary
                </h2>
                <div className="prose max-w-none">
                  {results.summary.split(/(\[[0-9]+\])/).map((part, index) => {
                    if (part.match(/\[[0-9]+\]/)) {
                      return (
                        <span key={index} className="font-medium text-blue-600">
                          {part}
                        </span>
                      );
                    }
                    return part;
                  })}
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  References
                </h2>
                <div className="divide-y divide-gray-200">
                  {results.citations.map(renderCitation)}
                </div>
              </div>

              <div className="text-sm text-gray-500 text-center">
                Found {results.total_results} total results in PubMed
                {filters.articleTypes.length > 0 && (
                  <span> ({results.citations.length} matching selected filters)</span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App; 