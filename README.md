# PubMed Natural Language Search API

This API provides a natural language interface for searching PubMed articles. It uses GPT to convert natural language queries into precise PubMed-compatible search strings and provides summarized results.

## Features

- Natural language query processing using GPT
- Automatic conversion to PubMed-compatible search strings
- Article fetching using NCBI E-utilities API
- Result summarization using GPT
- RESTful API interface using FastAPI

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
Search PubMed with a natural language query.

Request body:
```json
{
    "text": "Your natural language query",
    "max_results": 5
}
```

Response:
```json
{
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
}
```

### GET /
Get API information and available endpoints.

## Example Usage

Using curl:
```bash
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{"text": "latest treatments for pediatric asthma", "max_results": 5}'
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:
- 200: Successful request
- 500: Server error (with error details in the response)

## Dependencies

- Python 3.7+
- FastAPI
- Uvicorn
- Biopython
- OpenAI
- python-dotenv
- Pydantic 