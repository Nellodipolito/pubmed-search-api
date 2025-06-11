import React, { useState } from 'react';
import { FaSearch, FaExternalLinkAlt, FaFilter, FaTimes, FaNotesMedical } from 'react-icons/fa';
import axios from 'axios';
import ClinicalRecommendations from './components/ClinicalRecommendations';
import SOAPNoteInput from './components/SOAPNoteInput';
import MedlinePlusTopic from './components/MedlinePlusTopic';

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
  const [mode, setMode] = useState('search'); // 'search' or 'soap'
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    yearFilter: "5",
    maxResults: 5,
    articleTypes: [],
    includeMedlinePlus: true,
    language: "en"
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
        article_types: filters.articleTypes.length > 0 ? filters.articleTypes : null,
        include_medlineplus: filters.includeMedlinePlus,
        language: filters.language
      });
      setResults(response.data);
    } catch (error) {
      alert(error.response?.data?.detail?.error || 'Failed to search PubMed');
    } finally {
      setLoading(false);
    }
  };

  const handleSOAPSubmit = async (soapNote) => {
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/process_soap', {
        soap_note: soapNote,
        max_results_per_query: 3,
        include_medlineplus: true
      });
      setResults(response.data);
    } catch (error) {
      alert(error.response?.data?.detail?.error || 'Failed to process SOAP note');
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

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Include MedlinePlus Results
          </label>
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={filters.includeMedlinePlus}
              onChange={(e) => setFilters(prev => ({ ...prev, includeMedlinePlus: e.target.checked }))}
              className="h-4 w-4 text-blue-600 rounded border-gray-300"
            />
            <span className="ml-2 text-sm text-gray-600">Show consumer health information</span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Language (MedlinePlus)
          </label>
          <select
            value={filters.language}
            onChange={(e) => setFilters(prev => ({ ...prev, language: e.target.value }))}
            className="w-full rounded-md border border-gray-300 p-2"
            disabled={!filters.includeMedlinePlus}
          >
            <option value="en">English</option>
            <option value="es">Spanish</option>
          </select>
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

  const renderCitation = (article) => (
    <div key={article.pmid} className="flex items-start space-x-2 py-4">
      <div className="flex-1">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <a
              href={`https://pubmed.ncbi.nlm.nih.gov/${article.pmid}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 font-medium flex items-center"
            >
              {article.title}
              <FaExternalLinkAlt className="ml-1 h-3 w-3" />
            </a>
            <p className="text-sm text-gray-600 mt-1">
              {article.authors.join(', ')}
            </p>
            <p className="text-sm text-gray-500">
              {article.journal} ({article.publication_date})
            </p>
          </div>
          <div className="flex flex-col items-end ml-4 space-y-1">
            {article.doi && (
              <a
                href={`https://doi.org/${article.doi}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                DOI
              </a>
            )}
          </div>
        </div>
        {renderMetadataTags(article)}
      </div>
    </div>
  );

  const renderMedlinePlusTopic = (topic) => (
    <div key={topic.url} className="border-b border-gray-200 last:border-0 py-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <a
            href={topic.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 font-medium flex items-center"
          >
            {topic.title}
            <FaExternalLinkAlt className="ml-1 h-3 w-3" />
          </a>
          <p className="text-sm text-gray-600 mt-2">{topic.summary}</p>
          {topic.mesh_terms.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {topic.mesh_terms.map((term, idx) => (
                <span key={idx} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                  {term}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="space-y-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Clinical Evidence Search
            </h1>
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => setMode('search')}
                className={`px-4 py-2 rounded-md ${
                  mode === 'search'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Literature Search
              </button>
              <button
                onClick={() => setMode('soap')}
                className={`px-4 py-2 rounded-md ${
                  mode === 'soap'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                SOAP Note Analysis
              </button>
            </div>
          </div>

          {mode === 'search' ? (
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
          ) : (
            <SOAPNoteInput onSubmit={handleSOAPSubmit} />
          )}

          {loading && (
            <div className="text-center py-10">
              <div className="w-12 h-12 border-t-4 border-blue-500 rounded-full animate-spin mx-auto"></div>
              <p className="mt-4 text-gray-600">
                {mode === 'search' ? 'Searching medical literature...' : 'Processing SOAP note...'}
              </p>
            </div>
          )}

          {results && !loading && (
            <div className="space-y-8">
              {/* Clinical Recommendations */}
              {results.recommendations && (
                <ClinicalRecommendations recommendations={results.recommendations} />
              )}

              {/* PubMed Results */}
              {results.pubmed_results && (
                <>
                  <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">
                      Research Summary
                    </h2>
                    <div className="prose max-w-none">
                      {results.pubmed_results.summary.split(/(\[[0-9]+\])/).map((part, index) => {
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
                      Research Articles
                    </h2>
                    <div className="divide-y divide-gray-200">
                      {results.pubmed_results.articles.map(renderCitation)}
                    </div>
                    <div className="text-sm text-gray-500 text-center mt-4">
                      Found {results.pubmed_results.total_results} total results in PubMed
                      {filters.articleTypes.length > 0 && (
                        <span> ({results.pubmed_results.articles.length} matching selected filters)</span>
                      )}
                    </div>
                  </div>
                </>
              )}

              {/* MedlinePlus Results */}
              {results.medlineplus_results && results.medlineplus_results.topics.length > 0 && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold text-gray-900">
                    Patient Education Resources
                    <span className="text-sm font-normal text-gray-500 ml-2">
                      from MedlinePlus.gov
                    </span>
                  </h2>
                  {results.medlineplus_results.topics.map((topic, index) => (
                    <MedlinePlusTopic key={index} topic={topic} />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App; 