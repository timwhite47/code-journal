#!/usr/bin/env python3
"""
Pure Python sitemap parser implementation.

This module provides a pure Python implementation for parsing sitemaps,
fetching robots.txt files, and extracting URLs from sitemap indexes.
It serves as the baseline for performance comparison with the Rust implementation.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

import aiohttp


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SitemapResult:
    """Container for sitemap parsing results."""
    
    base_url: str
    urls: Set[str] = field(default_factory=set)
    sitemaps_found: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    parse_time: float = 0.0
    total_requests: int = 0


class PythonSitemapParser:
    """Pure Python implementation of sitemap parsing.
    
    This class handles:
    - Fetching robots.txt files
    - Extracting sitemap URLs from robots.txt
    - Parsing sitemap indexes (recursive)
    - Extracting individual URLs from sitemaps
    """

    def __init__(self, max_concurrent: int = 10, timeout: int = 30):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout,
            headers={'User-Agent': 'SitemapParser/1.0 (+https://timwhite.ninja)'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by ensuring it has a scheme and removing fragments."""
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        
        # Remove fragment
        parsed = urlparse(url)
        if parsed.fragment:
            url = url.split('#')[0]
        
        # Ensure trailing slash for domains
        if parsed.path == '':
            url = f"{url}/"
            
        return url

    async def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch content from a URL with error handling."""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.debug(f"Successfully fetched {url} ({len(content)} chars)")
                    return content
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def _parse_robots_txt(self, robots_content: str, base_url: str) -> List[str]:
        """Extract sitemap URLs from robots.txt content."""
        sitemaps = []
        
        for line in robots_content.split('\n'):
            line = line.strip()
            if line.lower().startswith('sitemap:'):
                sitemap_url = line[8:].strip()  # Remove 'sitemap:' prefix
                
                # Make relative URLs absolute
                if sitemap_url.startswith('/'):
                    sitemap_url = urljoin(base_url, sitemap_url)
                elif not sitemap_url.startswith(('http://', 'https://')):
                    sitemap_url = urljoin(base_url, sitemap_url)
                
                sitemaps.append(sitemap_url)
                logger.debug(f"Found sitemap in robots.txt: {sitemap_url}")
        
        return sitemaps

    def _parse_sitemap_xml(self, xml_content: str, base_url: str) -> tuple[Set[str], List[str]]:
        """Parse sitemap XML and extract URLs and nested sitemaps.
        
        Returns:
            tuple: (set of URLs, list of nested sitemap URLs)
        """
        urls = set()
        nested_sitemaps = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Handle sitemap index files
            if root.tag.endswith('}sitemapindex') or 'sitemapindex' in root.tag:
                for sitemap in root:
                    if sitemap.tag.endswith('}sitemap'):
                        for child in sitemap:
                            if child.tag.endswith('}loc'):
                                nested_url = child.text.strip() if child.text else ''
                                if nested_url:
                                    # Make relative URLs absolute
                                    if nested_url.startswith('/'):
                                        nested_url = urljoin(base_url, nested_url)
                                    nested_sitemaps.append(nested_url)
                                    logger.debug(f"Found nested sitemap: {nested_url}")
            
            # Handle regular sitemap files
            elif root.tag.endswith('}urlset') or 'urlset' in root.tag:
                for url_elem in root:
                    if url_elem.tag.endswith('}url'):
                        for child in url_elem:
                            if child.tag.endswith('}loc'):
                                url = child.text.strip() if child.text else ''
                                if url:
                                    urls.add(url)
            
            # Handle plain XML without namespace (some sites do this)
            else:
                # Try to find URL elements regardless of namespace
                for elem in root.iter():
                    if elem.tag.lower() == 'loc' or elem.tag.endswith('}loc'):
                        url = elem.text.strip() if elem.text else ''
                        if url:
                            urls.add(url)
                    elif elem.tag.lower() == 'sitemap' or elem.tag.endswith('}sitemap'):
                        # Look for loc within sitemap element
                        for child in elem:
                            if child.tag.lower() == 'loc' or child.tag.endswith('}loc'):
                                nested_url = child.text.strip() if child.text else ''
                                if nested_url:
                                    if nested_url.startswith('/'):
                                        nested_url = urljoin(base_url, nested_url)
                                    nested_sitemaps.append(nested_url)
        
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing XML: {e}")
        
        return urls, nested_sitemaps

    async def _process_sitemap(self, sitemap_url: str, base_url: str, 
                             visited: Set[str], max_depth: int = 3) -> tuple[Set[str], int]:
        """Process a single sitemap URL recursively.
        
        Returns:
            tuple: (set of URLs found, number of requests made)
        """
        if sitemap_url in visited or max_depth <= 0:
            return set(), 0
        
        visited.add(sitemap_url)
        request_count = 1
        
        logger.info(f"Processing sitemap: {sitemap_url}")
        content = await self._fetch_url(sitemap_url)
        
        if not content:
            return set(), request_count
        
        urls, nested_sitemaps = self._parse_sitemap_xml(content, base_url)
        logger.info(f"Found {len(urls)} URLs and {len(nested_sitemaps)} nested sitemaps in {sitemap_url}")
        
        # Process nested sitemaps concurrently
        if nested_sitemaps:
            tasks = [
                self._process_sitemap(nested_url, base_url, visited, max_depth - 1)
                for nested_url in nested_sitemaps
                if nested_url not in visited
            ]
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Error processing nested sitemap: {result}")
                    else:
                        nested_urls, nested_requests = result
                        urls.update(nested_urls)
                        request_count += nested_requests
        
        return urls, request_count

    async def parse_site(self, base_url: str) -> SitemapResult:
        """Parse sitemaps for a given base URL.
        
        Args:
            base_url: The base URL to parse (e.g., 'https://example.com')
            
        Returns:
            SitemapResult containing all discovered URLs and metadata
        """
        start_time = time.time()
        result = SitemapResult(base_url=base_url)
        
        # Normalize the base URL
        normalized_url = self._normalize_url(base_url)
        robots_url = urljoin(normalized_url, '/robots.txt')
        
        try:
            # Fetch robots.txt
            logger.info(f"Fetching robots.txt from {robots_url}")
            robots_content = await self._fetch_url(robots_url)
            result.total_requests += 1
            
            if robots_content:
                # Parse sitemaps from robots.txt
                sitemaps = self._parse_robots_txt(robots_content, normalized_url)
                result.sitemaps_found = sitemaps
                
                if not sitemaps:
                    # Try common sitemap locations if none found in robots.txt
                    common_sitemaps = [
                        urljoin(normalized_url, '/sitemap.xml'),
                        urljoin(normalized_url, '/sitemap_index.xml'),
                        urljoin(normalized_url, '/sitemaps.xml'),
                    ]
                    result.sitemaps_found = common_sitemaps
                    logger.info(f"No sitemaps in robots.txt, trying common locations: {common_sitemaps}")
                
                # Process all sitemaps
                visited = set()
                tasks = [
                    self._process_sitemap(sitemap_url, normalized_url, visited)
                    for sitemap_url in result.sitemaps_found
                ]
                
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for i, result_data in enumerate(results):
                        if isinstance(result_data, Exception):
                            error_msg = f"Error processing {result.sitemaps_found[i]}: {result_data}"
                            result.errors.append(error_msg)
                            logger.error(error_msg)
                        else:
                            urls, requests = result_data
                            result.urls.update(urls)
                            result.total_requests += requests
                
                logger.info(f"Completed parsing {normalized_url}: {len(result.urls)} URLs found")
            
            else:
                error_msg = f"Could not fetch robots.txt from {robots_url}"
                result.errors.append(error_msg)
                logger.error(error_msg)
        
        except Exception as e:
            error_msg = f"Error parsing {base_url}: {e}"
            result.errors.append(error_msg)
            logger.error(error_msg)
        
        finally:
            result.parse_time = time.time() - start_time
        
        return result

    async def parse_multiple_sites(self, base_urls: List[str]) -> List[SitemapResult]:
        """Parse sitemaps for multiple sites concurrently.
        
        Args:
            base_urls: List of base URLs to parse
            
        Returns:
            List of SitemapResult objects
        """
        logger.info(f"Starting to parse {len(base_urls)} sites")
        
        # Create semaphore to limit concurrent sites
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def parse_with_semaphore(url):
            async with semaphore:
                return await self.parse_site(url)
        
        tasks = [parse_with_semaphore(url) for url in base_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = SitemapResult(base_url=base_urls[i])
                error_result.errors.append(f"Failed to parse: {result}")
                final_results.append(error_result)
                logger.error(f"Error parsing {base_urls[i]}: {result}")
            else:
                final_results.append(result)
        
        total_urls = sum(len(r.urls) for r in final_results)
        total_time = sum(r.parse_time for r in final_results)
        logger.info(f"Completed parsing all sites: {total_urls} URLs in {total_time:.2f}s")
        
        return final_results


# Synchronous wrapper for easier testing
def parse_sitemaps_sync(base_urls: List[str], max_concurrent: int = 10) -> List[SitemapResult]:
    """Synchronous wrapper for parsing sitemaps.
    
    Args:
        base_urls: List of base URLs to parse
        max_concurrent: Maximum concurrent connections
        
    Returns:
        List of SitemapResult objects
    """
    async def run():
        async with PythonSitemapParser(max_concurrent=max_concurrent) as parser:
            return await parser.parse_multiple_sites(base_urls)
    
    return asyncio.run(run())


if __name__ == "__main__":
    # Example usage - major news sites with complex sitemaps
    test_urls = [
        "https://www.nytimes.com/",
        "https://www.cnn.com/",
        "https://www.seattletimes.com/",
    ]
    
    print("🐍 Running Pure Python Sitemap Parser")
    print("=" * 50)
    
    start_time = time.time()
    results = parse_sitemaps_sync(test_urls)
    total_time = time.time() - start_time
    
    for result in results:
        print(f"\n📊 Results for {result.base_url}:")
        print(f"   URLs found: {len(result.urls)}")
        print(f"   Sitemaps: {len(result.sitemaps_found)}")
        print(f"   Parse time: {result.parse_time:.2f}s")
        print(f"   Requests made: {result.total_requests}")
        
        if result.errors:
            print(f"   ❌ Errors: {len(result.errors)}")
            for error in result.errors[:3]:  # Show first 3 errors
                print(f"      - {error}")
    
    print(f"\n⏱️  Total execution time: {total_time:.2f}s")
    print(f"🔗 Total URLs discovered: {sum(len(r.urls) for r in results)}")
