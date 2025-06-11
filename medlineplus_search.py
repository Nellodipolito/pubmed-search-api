import requests
import logging
import time
from typing import Dict, Any, Optional
from xml.etree import ElementTree as ET
from urllib.parse import quote_plus
import threading
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter to ensure we don't exceed 85 requests per minute"""
    def __init__(self, requests_per_minute: int = 85):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = threading.Lock()

    def wait_if_needed(self):
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        with self.lock:
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests if req_time > minute_ago]
            
            # If we've hit the limit, wait until we can make another request
            if len(self.requests) >= self.requests_per_minute:
                sleep_time = (self.requests[0] - minute_ago).total_seconds()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.requests = self.requests[1:]
            
            # Add current request
            self.requests.append(now)

class MedlinePlusError(Exception):
    """Custom exception for MedlinePlus API errors"""
    pass

class MedlinePlusAPI:
    BASE_URL = "https://wsearch.nlm.nih.gov/ws/query"
    
    def __init__(self, tool_name: str = "pubmed_api_client", email: Optional[str] = None):
        self.tool_name = tool_name
        self.email = email
        self.rate_limiter = RateLimiter()
        self.cache = {}
        self.cache_duration = timedelta(hours=12)  # Cache results for 12 hours

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return result
            else:
                del self.cache[cache_key]
        return None

    def _add_to_cache(self, cache_key: str, result: Dict[str, Any]):
        self.cache[cache_key] = (result, datetime.now())

    def search_health_topics(
        self,
        query: str,
        language: str = "en",
        max_results: int = 10,
        ret_type: str = "all"
    ) -> Dict[str, Any]:
        """
        Search MedlinePlus health topics.
        
        Args:
            query: Search query string
            language: 'en' for English or 'es' for Spanish
            max_results: Number of results to return (default: 10)
            ret_type: Return type ('brief', 'topic', or 'all')
            
        Returns:
            Dictionary containing search results and metadata
        """
        # Check cache first
        cache_key = f"{query}:{language}:{max_results}:{ret_type}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        # Prepare parameters
        params = {
            'db': 'healthTopics' if language == 'en' else 'healthTopicsSpanish',
            'term': query,
            'retmax': str(max_results),
            'rettype': ret_type,
            'tool': self.tool_name
        }
        
        if self.email:
            params['email'] = self.email

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            result = {
                'count': int(root.find('count').text) if root.find('count') is not None else 0,
                'topics': []
            }

            # Add spelling correction if present
            spelling_correction = root.find('spellingCorrection')
            if spelling_correction is not None:
                result['spelling_correction'] = spelling_correction.text

            # Process documents
            for doc in root.findall('.//document'):
                topic = {
                    'url': doc.get('url'),
                    'rank': int(doc.get('rank')),
                    'title': None,
                    'summary': None,
                    'snippets': [],
                    'mesh_terms': [],
                    'groups': []
                }

                for content in doc.findall('content'):
                    name = content.get('name')
                    if name == 'title':
                        topic['title'] = self._clean_xml_text(content)
                    elif name == 'FullSummary':
                        topic['summary'] = self._clean_xml_text(content)
                    elif name == 'snippet':
                        topic['snippets'].append(self._clean_xml_text(content))
                    elif name == 'mesh':
                        topic['mesh_terms'].append(self._clean_xml_text(content))
                    elif name == 'groupName':
                        topic['groups'].append(self._clean_xml_text(content))

                result['topics'].append(topic)

            # Cache the result
            self._add_to_cache(cache_key, result)
            return result

        except requests.exceptions.RequestException as e:
            raise MedlinePlusError(f"Failed to fetch data from MedlinePlus: {str(e)}")
        except ET.ParseError as e:
            raise MedlinePlusError(f"Failed to parse MedlinePlus response: {str(e)}")

    def _clean_xml_text(self, element: ET.Element) -> str:
        """Clean XML text by removing highlighting tags while preserving the text"""
        text = ''.join(element.itertext())
        return text.strip() 