import os
import time
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from Bio import Entrez, Medline
import xml.etree.ElementTree as ET
from openai import OpenAI
import json
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Entrez
Entrez.email = os.getenv("PUBMED_EMAIL")
Entrez.api_key = os.getenv("PUBMED_API_KEY")

# Configure OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class PubMedSearchError(Exception):
    """Custom exception for PubMed search errors"""
    pass

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def convert_to_pubmed_query(user_input: str, year_filter: str = "5") -> str:
    """
    Convert natural language query to PubMed-compatible search string using GPT.
    Includes date filtering based on user preference.
    """
    try:
        # Calculate the year range for the filter
        date_filter = ""
        if year_filter:
            date_filter = f" AND {year_filter}[pdat]"
        
        prompt = f"""Convert the following natural language question into an effective PubMed search query.
        Guidelines:
        1. Use broad matching with OR operators between synonyms
        2. Avoid using too many MeSH terms as they can be too restrictive
        3. Include common alternative terms
        4. Focus on key concepts only
        5. Don't add date restrictions (they will be added automatically)
        6. Make the query broad enough to find relevant results
        
        Example good queries:
        Input: "Latest treatments for diabetes type 2"
        Output: (diabetes type 2 OR type 2 diabetes OR T2DM) AND (treatment OR therapy OR management)
        
        Input: "Heart attack risk in women"
        Output: (myocardial infarction OR heart attack) AND (women OR female) AND risk
        
        Input: {user_input}
        Output format: Just return the PubMed search string, nothing else."""

        logger.info(f"Sending query to GPT: {user_input}")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a PubMed search expert. Create effective, broad search strings that will find relevant results without being too restrictive. Focus on key concepts and use OR operators for synonyms."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        query = response.choices[0].message.content.strip() + date_filter
        logger.info(f"Generated PubMed query: {query}")
        return query
    except Exception as e:
        logger.error(f"Error in convert_to_pubmed_query: {str(e)}")
        raise PubMedSearchError(f"Failed to convert query: {str(e)}")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def search_pubmed(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search PubMed using the provided query string.
    """
    try:
        logger.info(f"Searching PubMed with query: {query}, max_results: {max_results}")
        handle = Entrez.esearch(
            db="pubmed",
            term=query,
            retmax=max_results,
            usehistory="y",
            sort="relevance",
            retmode="xml"
        )
        search_results = Entrez.read(handle)
        handle.close()
        
        if int(search_results["Count"]) == 0:
            # If no results, try without the date filter
            if "[pdat]" in query:
                logger.info("No results found with date filter, trying without it")
                query_without_date = query.split(" AND ")[:-1]  # Remove the date filter
                handle = Entrez.esearch(
                    db="pubmed",
                    term=" AND ".join(query_without_date),
                    retmax=max_results,
                    usehistory="y",
                    sort="relevance",
                    retmode="xml"
                )
                search_results = Entrez.read(handle)
                handle.close()
                
        logger.info(f"Found {search_results['Count']} results")
        return search_results
    except Exception as e:
        logger.error(f"Error in search_pubmed: {str(e)}")
        raise PubMedSearchError(f"Failed to search PubMed: {str(e)}")

def normalize_publication_type(pub_type: str) -> str:
    """
    Normalize publication type strings for better matching.
    Handles common variations in how publication types are written.
    """
    # Remove punctuation and convert to lowercase
    normalized = pub_type.lower().replace('-', ' ').replace('/', ' ').strip()
    
    # Map common variations to standard forms
    type_mapping = {
        'clinical trial': ['clinical trial', 'clinical study', 'clinical research', 'interventional study'],
        'randomized controlled trial': ['randomized controlled trial', 'randomised controlled trial', 'rct'],
        'systematic review': ['systematic review', 'systematic literature review', 'systematic analysis'],
        'meta analysis': ['meta analysis', 'metaanalysis', 'meta analytical study'],
        'case report': ['case report', 'case study', 'patient case'],
        'review': ['review', 'literature review', 'narrative review'],
        'comparative study': ['comparative study', 'comparison study', 'comparative analysis'],
        'observational study': ['observational study', 'observational research'],
        'cohort study': ['cohort study', 'cohort analysis'],
        'case control study': ['case control study', 'case control']
    }
    
    # Check if the normalized type matches any of the standard variations
    for standard_type, variations in type_mapping.items():
        if any(variation in normalized for variation in variations):
            return standard_type
            
    return normalized

def match_publication_type(article_type: str, pub_types: List[str]) -> bool:
    """
    Check if an article matches a requested publication type.
    Uses flexible matching to handle variations in how types are written.
    """
    normalized_request = normalize_publication_type(article_type)
    normalized_types = [normalize_publication_type(pt) for pt in pub_types]
    
    return any(normalized_request in pt for pt in normalized_types)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_article_details(search_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetch detailed information for articles found in search using XML format.
    """
    try:
        pmids = search_results.get("IdList", [])
        if not pmids:
            return []

        logger.info(f"Fetching details for {len(pmids)} articles")
        handle = Entrez.efetch(
            db="pubmed",
            id=",".join(pmids),
            rettype="xml",
            retmode="xml"
        )
        
        articles = []
        tree = ET.parse(handle)
        root = tree.getroot()
        
        for article in root.findall(".//PubmedArticle"):
            try:
                # Extract basic metadata
                pmid = article.find(".//PMID").text
                article_meta = article.find(".//Article")
                
                # Get title
                title = article_meta.find(".//ArticleTitle").text if article_meta.find(".//ArticleTitle") is not None else ""
                
                # Get abstract
                abstract_element = article_meta.find(".//Abstract/AbstractText")
                abstract = abstract_element.text if abstract_element is not None else "No abstract available"
                
                # Get authors
                authors = []
                author_list = article_meta.findall(".//Author")
                for author in author_list:
                    last_name = author.find("LastName")
                    fore_name = author.find("ForeName")
                    if last_name is not None and fore_name is not None:
                        authors.append(f"{last_name.text}, {fore_name.text}")
                    elif last_name is not None:
                        authors.append(last_name.text)
                
                # Get journal info
                journal = article_meta.find(".//Journal")
                journal_title = journal.find(".//Title").text if journal.find(".//Title") is not None else ""
                
                # Get publication date
                pub_date = journal.find(".//PubDate")
                year = pub_date.find("Year")
                month = pub_date.find("Month")
                pub_date_str = f"{year.text if year is not None else ''} {month.text if month is not None else ''}".strip()
                
                # Get DOI
                doi = None
                article_ids = article.findall(".//ArticleId")
                for article_id in article_ids:
                    if article_id.get("IdType") == "doi":
                        doi = article_id.text
                        break
                
                # Get MeSH terms
                mesh_terms = []
                mesh_headings = article.findall(".//MeshHeading")
                for mesh in mesh_headings:
                    descriptor = mesh.find("DescriptorName")
                    if descriptor is not None:
                        mesh_terms.append(descriptor.text)
                
                # Get publication types with normalization
                pub_types = []
                publication_types = article_meta.findall(".//PublicationType")
                for pub_type in publication_types:
                    if pub_type.text:
                        normalized_type = normalize_publication_type(pub_type.text)
                        if normalized_type not in pub_types:  # Avoid duplicates
                            pub_types.append(normalized_type)
                
                # Get keywords
                keywords = []
                keyword_list = article.findall(".//Keyword")
                for keyword in keyword_list:
                    if keyword.text:
                        keywords.append(keyword.text)
                
                # Get affiliations
                affiliations = []
                aff_list = article_meta.findall(".//Affiliation")
                for aff in aff_list:
                    if aff.text:
                        affiliations.append(aff.text)
                
                # Check for PMC ID
                pmc_id = None
                for article_id in article_ids:
                    if article_id.get("IdType") == "pmc":
                        pmc_id = article_id.text
                        break
                
                articles.append({
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "journal": journal_title,
                    "publication_date": pub_date_str,
                    "doi": doi,
                    "mesh_terms": mesh_terms,
                    "publication_types": pub_types,
                    "keywords": keywords,
                    "affiliations": affiliations,
                    "pmc_id": pmc_id,
                    "urls": {
                        "pubmed": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}",
                        "doi": f"https://doi.org/{doi}" if doi else None,
                        "pmc": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}" if pmc_id else None
                    }
                })
                
            except Exception as e:
                logger.error(f"Error parsing article {pmid}: {str(e)}")
                continue
        
        handle.close()
        logger.info(f"Successfully parsed {len(articles)} articles")
        return articles
        
    except Exception as e:
        logger.error(f"Error in fetch_article_details: {str(e)}")
        raise PubMedSearchError(f"Failed to fetch article details: {str(e)}")

def chunk_abstracts(articles: List[Dict[str, Any]], max_tokens: int = 2000) -> List[str]:
    """
    Split articles into chunks that fit within token limits.
    """
    chunks = []
    current_chunk = []
    current_length = 0
    
    for idx, article in enumerate(articles, 1):
        # Truncate abstract if too long
        abstract = article['abstract'][:300] + "..." if len(article['abstract']) > 300 else article['abstract']
        article_text = f"[{idx}] Title: {article['title']}\nAbstract: {abstract}\n\n"
        
        # Rough estimate of tokens (4 chars ≈ 1 token)
        estimated_tokens = len(article_text) // 4
        
        if current_length + estimated_tokens > max_tokens:
            chunks.append("\n".join(current_chunk))
            current_chunk = [article_text]
            current_length = estimated_tokens
        else:
            current_chunk.append(article_text)
            current_length += estimated_tokens
    
    if current_chunk:
        chunks.append("\n".join(current_chunk))
    
    return chunks

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def summarize_results(articles: List[Dict[str, Any]], user_query: str) -> Dict[str, Any]:
    """
    Generate a summary of the search results using GPT with numbered citations.
    Uses multi-step summarization for larger result sets.
    """
    if not articles:
        return {
            "summary": "No articles found matching your query.",
            "citations": []
        }
        
    # Create numbered citations with metadata
    citations = []
    for idx, article in enumerate(articles, 1):
        citation = {
            "number": idx,
            "title": article['title'],
            "authors": article['authors'],
            "journal": article['journal'],
            "year": article['publication_date'].split()[0] if article['publication_date'] else "",
            "pmid": article['pmid'],
            "doi": article['doi'],
            "urls": article['urls'],
            "publication_types": article['publication_types'],
            "mesh_terms": article['mesh_terms'],
            "keywords": article['keywords']
        }
        citations.append(citation)
    
    try:
        # Split articles into chunks if needed
        chunks = chunk_abstracts(articles)
        summaries = []
        
        # Generate summary for each chunk
        for chunk in chunks:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a scientific summarizer. Provide clear, accurate summaries with proper citation numbers."},
                    {"role": "user", "content": f"""Summarize the following research articles related to: "{user_query}"
                    Include citation numbers [1], [2], etc. when referencing specific findings.
                    
                    Articles:
                    {chunk}
                    
                    Guidelines:
                    1. Use citation numbers in square brackets
                    2. Focus on key findings and methodology
                    3. Maintain academic writing style
                    4. Synthesize information across articles
                    5. Be specific about findings and their sources
                    
                    Summary:"""}
                ],
                temperature=0,
                max_tokens=800
            )
            summaries.append(response.choices[0].message.content.strip())
        
        # If multiple chunks, create a final summary
        final_summary = summaries[0]
        if len(summaries) > 1:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a scientific summarizer. Create a cohesive summary from multiple partial summaries."},
                    {"role": "user", "content": f"Combine these summaries into a single coherent summary, maintaining citation numbers and academic style:\n\n{' '.join(summaries)}"}
                ],
                temperature=0,
                max_tokens=800
            )
            final_summary = response.choices[0].message.content.strip()
        
        logger.info("Successfully generated summary")
        return {
            "summary": final_summary,
            "citations": citations
        }
    except Exception as e:
        logger.error(f"Error in summarize_results: {str(e)}")
        return {
            "summary": f"Error generating summary: {str(e)}",
            "citations": citations
        }

def process_query(
    user_input: str,
    max_results: int = 5,
    year_filter: str = "5"
) -> Dict[str, Any]:
    """
    Process a natural language query and return structured results.
    """
    try:
        # Convert natural language to PubMed query
        pubmed_query = convert_to_pubmed_query(user_input, year_filter)
        
        # Search PubMed
        search_results = search_pubmed(pubmed_query, max_results)
        
        # Fetch article details
        articles = fetch_article_details(search_results)
        
        # Generate summary and citations
        summary_data = summarize_results(articles, user_input)
        
        return {
            "original_query": user_input,
            "pubmed_query": pubmed_query,
            "total_results": search_results["Count"],
            "articles": articles,
            "summary": summary_data["summary"],
            "citations": summary_data["citations"]
        }
    except Exception as e:
        logger.error(f"Error in process_query: {str(e)}")
        raise PubMedSearchError(f"Failed to process query: {str(e)}") 