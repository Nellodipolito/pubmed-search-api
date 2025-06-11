from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pubmed_search import process_query, PubMedSearchError
from medlineplus_search import MedlinePlusAPI, MedlinePlusError
from soap_processor import SOAPProcessor, SOAPNote
import uvicorn
from typing import Optional, List, Dict, Any
import logging
import openai
from openai import AsyncOpenAI
import PyPDF2
import io
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI()

app = FastAPI(
    title="Clinical Evidence Search API",
    description="API for searching medical literature and analyzing clinical notes",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize APIs and processors
medlineplus_api = MedlinePlusAPI(tool_name="pubmed_api_client")
soap_processor = SOAPProcessor()

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
    include_medlineplus: bool = Field(
        default=True,
        description="Whether to include MedlinePlus health topics in the results"
    )
    language: str = Field(
        default="en",
        description="Language for MedlinePlus results ('en' for English, 'es' for Spanish)"
    )

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None

class SOAPRequest(BaseModel):
    soap_note: str
    include_medlineplus: bool = Field(
        default=True,
        description="Whether to include MedlinePlus health topics in the results"
    )
    max_results_per_query: int = Field(
        default=5,
        description="Maximum number of results to return per generated query"
    )

class AnalysisRequest(BaseModel):
    pubmed_results: Optional[Dict[str, Any]]
    medlineplus_results: Optional[Dict[str, Any]]
    search_query: str

class SOAPAnalysisRequest(BaseModel):
    content: str
    type: str = "text"

async def analyze_with_gpt(content: str, system_prompt: str) -> Dict[str, Any]:
    try:
        # Update system prompt to explicitly request JSON
        json_system_prompt = f"""
{system_prompt}

IMPORTANT: Your response MUST be a valid JSON object. 
- Use double quotes for strings
- Ensure all property names are quoted
- Do not include any explanatory text outside the JSON
- Validate the JSON structure before responding
"""
        
        response = await client.chat.completions.create(
            model="gpt-4-0125-preview",  # Using GPT-4 Turbo which supports JSON response format
            messages=[
                {"role": "system", "content": json_system_prompt},
                {"role": "user", "content": content}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as json_err:
            logger.error(f"JSON parsing error: {str(json_err)}")
            logger.error(f"Raw response content: {response.choices[0].message.content}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Failed to parse GPT response as JSON",
                    "details": str(json_err)
                }
            )
    except Exception as e:
        logger.error(f"Error in GPT analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to analyze content with GPT", "details": str(e)}
        )

@app.post("/search")
async def search(query: Query):
    """
    Search PubMed using a natural language query and optionally include MedlinePlus health topics.
    
    The query will be processed through GPT to create an optimal PubMed search string,
    then results will be fetched and summarized. If requested, relevant MedlinePlus
    health topics will also be included.
    
    Parameters:
    - text: Natural language query
    - max_results: Maximum number of results to return (1-100)
    - year_filter: Filter for publication date ('1', '5', '10' years, or empty)
    - article_types: List of article types to filter by
    - include_medlineplus: Whether to include MedlinePlus health topics
    - language: Language for MedlinePlus results ('en' or 'es')
    """
    try:
        logger.info(f"Received search request: {query.dict()}")
        
        # Process the query with increased max_results if filtering is requested
        max_results = query.max_results * 3 if query.article_types else query.max_results
        
        # Process the PubMed query
        pubmed_results = process_query(
            user_input=query.text,
            max_results=max_results,
            year_filter=query.year_filter
        )
        
        # Filter by article type if specified
        if query.article_types:
            logger.info(f"Filtering results by article types: {query.article_types}")
            filtered_articles = []
            
            for article in pubmed_results["articles"]:
                if any(art_type.lower() in [pt.lower() for pt in article["publication_types"]] 
                      for art_type in query.article_types):
                    filtered_articles.append(article)
            
            if filtered_articles:
                pubmed_results["articles"] = filtered_articles[:query.max_results]
            else:
                pubmed_results["articles"] = []
                pubmed_results["summary"] = f"No articles of type {', '.join(query.article_types)} were found. Try broadening your search criteria or removing some filters."

        # Get MedlinePlus results if requested
        medlineplus_results = None
        if query.include_medlineplus:
            try:
                medlineplus_results = medlineplus_api.search_health_topics(
                    query=query.text,
                    language=query.language,
                    max_results=5,  # Limit to top 5 most relevant health topics
                    ret_type="all"
                )
                logger.info(f"Found {len(medlineplus_results['topics'])} MedlinePlus topics")
            except MedlinePlusError as e:
                logger.error(f"MedlinePlus search error: {str(e)}")
                medlineplus_results = {
                    "error": str(e),
                    "topics": []
                }

        # Combine results
        combined_results = {
            "pubmed_results": pubmed_results,
            "medlineplus_results": medlineplus_results if query.include_medlineplus else None
        }

        return combined_results

    except PubMedSearchError as e:
        logger.error(f"PubMed search error: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "PubMed search failed", "details": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "Internal server error", "details": str(e)})

@app.post("/process_soap")
async def process_soap(request: SOAPRequest):
    """
    Process a SOAP note and return relevant medical literature and recommendations.
    
    The endpoint will:
    1. Parse the SOAP note
    2. Generate targeted search queries
    3. Search medical literature (PubMed and optionally MedlinePlus)
    4. Generate clinical recommendations
    5. Return structured results with evidence-based suggestions
    """
    try:
        # Parse SOAP note
        soap_note = soap_processor.parse_soap_note(request.soap_note)
        
        # Generate search queries
        queries = soap_processor.generate_search_queries(soap_note)
        
        # Generate initial recommendations
        recommendations = soap_processor.generate_recommendations(soap_note)
        
        # Search literature for each query
        evidence = {
            'clinical_guidelines': [],
            'treatment': [],
            'age_specific': [],
            'medication': []
        }
        
        for query in queries:
            try:
                # Search PubMed
                pubmed_results = process_query(
                    user_input=query['text'],
                    max_results=request.max_results_per_query
                )
                
                # Search MedlinePlus if requested
                medlineplus_results = None
                if request.include_medlineplus:
                    try:
                        medlineplus_results = medlineplus_api.search_health_topics(
                            query=query['text'],
                            language="en",
                            max_results=3
                        )
                    except MedlinePlusError as e:
                        logger.error(f"MedlinePlus search error: {str(e)}")
                        medlineplus_results = {"error": str(e), "topics": []}
                
                # Add results to evidence
                evidence[query['focus']].append({
                    'query': query['text'],
                    'pubmed_results': pubmed_results,
                    'medlineplus_results': medlineplus_results
                })
                
            except Exception as e:
                logger.error(f"Error processing query '{query['text']}': {str(e)}")
                evidence[query['focus']].append({
                    'query': query['text'],
                    'error': str(e)
                })
        
        # Prepare response
        response = {
            'patient_info': {
                'name': soap_note.patient_name,
                'age': soap_note.age,
                'visit_date': soap_note.date.isoformat(),
                'provider': soap_note.provider,
                'visit_type': soap_note.visit_type
            },
            'clinical_summary': {
                'problems': soap_note.assessment,
                'vital_signs': {
                    'blood_pressure': soap_note.vital_signs.blood_pressure,
                    'heart_rate': soap_note.vital_signs.heart_rate,
                    'temperature': soap_note.vital_signs.temperature,
                    'respiratory_rate': soap_note.vital_signs.respiratory_rate,
                    'oxygen_saturation': soap_note.vital_signs.oxygen_saturation
                }
            },
            'recommendations': recommendations,
            'evidence': evidence
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing SOAP note: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to process SOAP note",
                "details": str(e)
            }
        )

@app.post("/analyze/results")
async def analyze_search_results(request: AnalysisRequest):
    """
    Analyze search results using GPT to provide a comprehensive summary with citations.
    """
    system_prompt = """
    You are a medical research analyst. Analyze the provided search results and create a structured summary with the following components:
    1. Clinical Summary: Key points with citations
    2. Key Findings: Main conclusions with evidence strength
    3. Clinical Guidelines: Relevant recommendations
    4. Patient Resources: Educational materials

    Format the response as a JSON object with these sections. Include proper citations for each claim.
    Ensure all citations link back to the source documents provided.
    """
    
    # Prepare content for analysis
    content = {
        "query": request.search_query,
        "pubmed_results": request.pubmed_results,
        "medlineplus_results": request.medlineplus_results
    }
    
    return await analyze_with_gpt(json.dumps(content), system_prompt)

@app.post("/analyze/soap")
async def analyze_soap_note(
    content: str = Form(None),
    file: UploadFile = File(None)
):
    """
    Analyze a SOAP note from text or PDF and extract structured information.
    """
    try:
        # First get the content from either file or text input
        note_content = ""
        if file:
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(await file.read()))
                for page in pdf_reader.pages:
                    note_content += page.extract_text()
            except Exception as e:
                logger.error(f"Error processing PDF: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail={"error": "Failed to process PDF file"}
                )
        elif content:
            note_content = content
        else:
            raise HTTPException(
                status_code=400,
                detail={"error": "Either file or content must be provided"}
            )

        # Step 1: Extract structured information from the SOAP note
        extraction_prompt = """
        Extract structured information from the provided SOAP note. Include:
        1. Patient Demographics (name, age, gender)
        2. Vital Signs (BP, HR, RR, Temp, O2 Sat)
        3. Chief Complaints
        4. Key Symptoms
        5. Relevant Medical History
        6. Current Medications
        7. Physical Exam Findings
        8. Assessment/Diagnoses
        9. Treatment Plan

        Return as a JSON object with these sections. For each finding or diagnosis, include a confidence level (high/medium/low).
        """
        
        structured_data = await analyze_with_gpt(note_content, extraction_prompt)
        
        # Step 2: Generate targeted search queries based on the extracted information
        search_prompt = """
        Based on the following structured medical information, generate focused search queries for medical literature.
        For each query, specify:
        1. The search focus (diagnosis, treatment, guidelines, etc.)
        2. The specific query text optimized for medical search
        3. Priority level (high/medium/low)

        Return as a JSON object with an array of search queries, each containing focus, text, and priority fields.
        """
        
        search_queries = await analyze_with_gpt(json.dumps(structured_data), search_prompt)
        
        # Step 3: Execute the searches
        evidence = {
            'clinical_guidelines': [],
            'treatment': [],
            'diagnosis': [],
            'medication': []
        }
        
        for query in search_queries.get('queries', []):
            try:
                # Only process high and medium priority queries
                if query['priority'].lower() not in ['high', 'medium']:
                    continue
                    
                # Search PubMed
                pubmed_results = process_query(
                    user_input=query['text'],
                    max_results=5
                )
                
                # Search MedlinePlus for relevant topics
                medlineplus_results = None
                try:
                    medlineplus_results = medlineplus_api.search_health_topics(
                        query=query['text'],
                        language="en",
                        max_results=3
                    )
                except Exception as e:
                    logger.error(f"MedlinePlus search error: {str(e)}")
                    medlineplus_results = {"error": str(e), "topics": []}
                
                # Add results to evidence
                focus = query['focus'].lower()
                if focus not in evidence:
                    focus = 'clinical_guidelines'  # default category
                    
                evidence[focus].append({
                    'query': query['text'],
                    'priority': query['priority'],
                    'pubmed_results': pubmed_results,
                    'medlineplus_results': medlineplus_results
                })
                
            except Exception as e:
                logger.error(f"Error processing query '{query['text']}': {str(e)}")
                continue
        
        # Step 4: Generate final analysis and recommendations
        analysis_prompt = """
        Based on the structured patient information and search results, provide:
        1. Clinical Summary
        2. Evidence-Based Recommendations
        3. Treatment Considerations
        4. Follow-up Plans
        5. Patient Education Points

        Include citation references for each recommendation.
        Return as a JSON object with these sections.
        """
        
        final_analysis = await analyze_with_gpt(
            json.dumps({
                "patient_data": structured_data,
                "evidence": evidence
            }),
            analysis_prompt
        )
        
        # Combine everything into the final response
        return {
            "structured_data": structured_data,
            "evidence": evidence,
            "analysis": final_analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing SOAP note: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to analyze SOAP note", "details": str(e)}
        )

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
                    "article_types": "Filter by article types (e.g., 'Review', 'Clinical Trial')",
                    "include_medlineplus": "Whether to include MedlinePlus health topics",
                    "language": "Language for MedlinePlus results ('en' or 'es')"
                }
            },
            "/process_soap": {
                "method": "POST",
                "description": "Process a SOAP note and return relevant medical literature and recommendations",
                "parameters": {
                    "soap_note": "SOAP note text",
                    "include_medlineplus": "Whether to include MedlinePlus health topics",
                    "max_results_per_query": "Maximum number of results to return per generated query"
                }
            },
            "/analyze/results": {
                "method": "POST",
                "description": "Analyze search results using GPT to provide a comprehensive summary with citations",
                "parameters": {
                    "pubmed_results": "PubMed search results",
                    "medlineplus_results": "MedlinePlus search results",
                    "search_query": "Search query"
                }
            },
            "/analyze/soap": {
                "method": "POST",
                "description": "Analyze a SOAP note from text or PDF and extract structured information",
                "parameters": {
                    "content": "SOAP note text or PDF file",
                    "type": "Type of input (text or pdf)"
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