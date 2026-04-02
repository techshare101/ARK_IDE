import aiohttp
from typing import Dict, Any, List
from bs4 import BeautifulSoup
import json

class WebTool:
    """Web search and fetch tool"""
    
    @staticmethod
    async def fetch_url(url: str, timeout: int = 30) -> Dict[str, Any]:
        """Fetch content from URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as response:
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'application/json' in content_type:
                        data = await response.json()
                        return {
                            'url': url,
                            'status': response.status,
                            'content_type': 'json',
                            'data': data
                        }
                    else:
                        text = await response.text()
                        return {
                            'url': url,
                            'status': response.status,
                            'content_type': 'html',
                            'html': text,
                            'text': WebTool._extract_text(text)
                        }
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'success': False
            }
    
    @staticmethod
    def _extract_text(html: str) -> str:
        """Extract clean text from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text[:10000]  # Limit to first 10k chars
        except:
            return html[:10000]
    
    @staticmethod
    async def web_search(query: str, num_results: int = 5) -> Dict[str, Any]:
        """Search the web (using DuckDuckGo)"""
        try:
            # Simple DuckDuckGo instant answer API
            async with aiohttp.ClientSession() as session:
                params = {
                    'q': query,
                    'format': 'json',
                    'no_html': 1
                }
                async with session.get(
                    'https://api.duckduckgo.com/',
                    params=params,
                    timeout=15
                ) as response:
                    data = await response.json()
                    
                    results = []
                    
                    # Extract related topics
                    for topic in data.get('RelatedTopics', [])[:num_results]:
                        if isinstance(topic, dict) and 'Text' in topic:
                            results.append({
                                'title': topic.get('Text', ''),
                                'url': topic.get('FirstURL', ''),
                                'snippet': topic.get('Text', '')[:200]
                            })
                    
                    return {
                        'query': query,
                        'results': results,
                        'abstract': data.get('Abstract', ''),
                        'answer': data.get('Answer', '')
                    }
        except Exception as e:
            return {
                'query': query,
                'error': str(e),
                'results': []
            }

web_tool = WebTool()
