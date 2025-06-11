import axios from 'axios';

const GPT_ENDPOINT = 'http://localhost:8000/analyze';

export const analyzeResults = async (data) => {
  try {
    const response = await axios.post(`${GPT_ENDPOINT}/results`, {
      pubmed_results: data.pubmed_results,
      medlineplus_results: data.medlineplus_results,
      search_query: data.query
    });
    return response.data;
  } catch (error) {
    console.error('Error analyzing results:', error);
    throw error;
  }
};

export const analyzeSOAPNote = async (content, type = 'text') => {
  try {
    const formData = new FormData();
    
    if (type === 'pdf') {
      formData.append('file', new Blob([content], { type: 'application/pdf' }));
    } else {
      formData.append('content', content);
    }

    const response = await axios.post(`${GPT_ENDPOINT}/soap`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error analyzing SOAP note:', error);
    throw error;
  }
}; 