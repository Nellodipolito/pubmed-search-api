from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pubmed_search import process_query, PubMedSearchError
import uvicorn
from typing import Optional, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PubMed Natural Language Search API",
    description="API for searching PubMed using natural language queries",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    text: str
    max_results: int = Field(default=5, ge=1, le=100)
    year_filter: Optional[str] = Field(
        default="5",
        description="Filter for publication date: '1', '5', '10' for years, or empty for no filter"
    )
    article_types: Optional[List[str]] = Field(
        default=None,
        description="Filter by article types (e.g., 'Review', 'Clinical Trial')"
    )

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None

@app.post("/search")
async def search(query: Query):
    """
    Search PubMed using a natural language query.
    
    The query will be processed through GPT to create an optimal PubMed search string,
    then results will be fetched and summarized.
    
    Parameters:
    - text: Natural language query
    - max_results: Maximum number of results to return (1-100)
    - year_filter: Filter for publication date ('1', '5', '10' years, or empty)
    - article_types: List of article types to filter by
    """
    try:
        logger.info(f"Received search request: {query.dict()}")
        
        # Process the query with increased max_results if filtering is requested
        max_results = query.max_results * 3 if query.article_types else query.max_results
        
        # Process the query
        results = process_query(
            user_input=query.text,
            max_results=max_results,  # Fetch more results if we're going to filter
            year_filter=query.year_filter
        )
        
        # Filter by article type if specified
        if query.article_types:
            logger.info(f"Filtering results by article types: {query.article_types}")
            filtered_articles = []
            filtered_citations = []
            
            for article in results["articles"]:
                # Check if any of the requested article types match
                if any(art_type.lower() in [pt.lower() for pt in article["publication_types"]] 
                      for art_type in query.article_types):
                    filtered_articles.append(article)
            
            # If we have filtered articles, update the results
            if filtered_articles:
                # Regenerate summary with filtered articles
                summary_data = summarize_results(filtered_articles, query.text)
                results["articles"] = filtered_articles
                results["summary"] = summary_data["summary"]
                results["citations"] = summary_data["citations"]
            else:
                # If no articles match the filter, return empty results with explanation
                results["articles"] = []
                results["summary"] = f"No articles of type {', '.join(query.article_types)} were found. Try broadening your search criteria or removing some filters."
                results["citations"] = []
            
            logger.info(f"Found {len(filtered_articles)} articles matching the article type filter")
        
        return results
    except PubMedSearchError as e:
        logger.error(f"PubMed search error: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "PubMed search failed", "details": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "Internal server error", "details": str(e)})

@app.get("/")
async def root():
    """
    Root endpoint providing basic API information.
    """
    return {
        "name": "PubMed Natural Language Search API",
        "version": "1.0.0",
        "description": "Use natural language to search PubMed articles",
        "endpoints": {
            "/search": {
                "method": "POST",
                "description": "Search PubMed with natural language query",
                "parameters": {
                    "text": "Natural language query string",
                    "max_results": "Number of results (1-100)",
                    "year_filter": "Publication date filter ('1', '5', '10' years)",
                    "article_types": "Filter by article types (e.g., 'Review', 'Clinical Trial')"
                }
            },
            "/": {
                "method": "GET",
                "description": "This information"
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 