# PubMed Natural Language Search API

This API provides a natural language interface for searching PubMed articles and MedlinePlus health topics. It uses GPT to convert natural language queries into precise search strings and provides summarized results from both sources.

## Features

- Natural language query processing using GPT
- Automatic conversion to PubMed-compatible search strings
- Article fetching using NCBI E-utilities API
- Result summarization using GPT
- MedlinePlus health topics integration
- Multi-language support (English and Spanish) for MedlinePlus content
- RESTful API interface using FastAPI
- Intelligent caching and rate limiting for MedlinePlus requests

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with the following variables:
   ```
   PUBMED_EMAIL=your@email.com
   PUBMED_API_KEY=your_pubmed_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

## Running the API

Start the API server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /search
Search PubMed and MedlinePlus with a natural language query.

Request body:
```json
{
    "text": "Your natural language query",
    "max_results": 5,
    "year_filter": "5",
    "article_types": ["Review", "Clinical Trial"],
    "include_medlineplus": true,
    "language": "en"
}
```

Response:
```json
{
    "pubmed_results": {
        "original_query": "Your natural language query",
        "pubmed_query": "Converted PubMed search string",
        "total_results": 100,
        "articles": [
            {
                "pmid": "12345678",
                "title": "Article Title",
                "authors": ["Author 1", "Author 2"],
                "abstract": "Article abstract...",
                "journal": "Journal Name",
                "publication_date": "2023",
                "doi": "10.1234/example"
            }
        ],
        "summary": "GPT-generated summary of the results"
    },
    "medlineplus_results": {
        "count": 10,
        "topics": [
            {
                "url": "https://medlineplus.gov/topic.html",
                "rank": 0,
                "title": "Topic Title",
                "summary": "Topic summary...",
                "snippets": ["Relevant text snippets..."],
                "mesh_terms": ["MeSH Term 1", "MeSH Term 2"],
                "groups": ["Topic Group 1", "Topic Group 2"]
            }
        ],
        "spelling_correction": "Optional spelling suggestion"
    }
}
```

### GET /
Get API information and available endpoints.

## Example Usage

Using curl:
```bash
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{
         "text": "latest treatments for pediatric asthma",
         "max_results": 5,
         "include_medlineplus": true,
         "language": "en"
     }'
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:
- 200: Successful request
- 500: Server error (with error details in the response)

## Rate Limiting

The MedlinePlus integration follows the official rate limiting guidelines:
- Maximum 85 requests per minute per IP address
- Results are cached for 12-24 hours to minimize API calls
- Automatic request throttling is implemented

## Dependencies

- Python 3.7+
- FastAPI
- Uvicorn
- Biopython
- OpenAI
- python-dotenv
- Pydantic
- Requests
- Tenacity

## Attribution

When using data from the MedlinePlus Web service, please indicate that the information is from MedlinePlus.gov. Do not use the MedlinePlus logo or imply that MedlinePlus endorses your product. 