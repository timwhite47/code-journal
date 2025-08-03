use log::{info, warn, error, debug};
use reqwest::Client;
use std::collections::HashSet;
use std::time::{Duration, Instant};
use tokio::time::timeout;
use tokio::sync::Semaphore;
use url::Url;
use futures::future::join_all;

use crate::robots::parse_robots_txt;
use crate::sitemap::{parse_sitemap_xml, SitemapParseResult};

#[derive(Debug, Clone)]
pub struct ParsedSiteResult {
    pub base_url: String,
    pub urls: HashSet<String>,
    pub sitemaps_found: Vec<String>,
    pub errors: Vec<String>,
    pub total_requests: usize,
    pub parse_time: f64,
}

impl ParsedSiteResult {
    pub fn new(base_url: String) -> Self {
        Self {
            base_url,
            urls: HashSet::new(),
            sitemaps_found: Vec::new(),
            errors: Vec::new(),
            total_requests: 0,
            parse_time: 0.0,
        }
    }
}

#[derive(Clone)]
pub struct RustSitemapParser {
    client: Client,
    max_concurrent: usize,
    max_sitemaps: usize,
    max_depth: usize,
    max_nested_per_level: usize,
    request_timeout: Duration,
}

impl RustSitemapParser {
    pub fn new(max_concurrent: usize, max_sitemaps: usize, max_depth: usize, max_nested_per_level: usize, timeout: Duration) -> Self {
        let client = Client::builder()
            .timeout(timeout)
            .user_agent("SitemapParser/1.0 (+https://timwhite.ninja)") // Match Python user agent exactly
            .pool_max_idle_per_host(10) // Enable connection pooling
            .pool_idle_timeout(Duration::from_secs(30))
            .tcp_keepalive(Duration::from_secs(30))
            .build()
            .expect("Failed to create HTTP client");

        Self {
            client,
            max_concurrent,
            max_sitemaps,
            max_depth,
            max_nested_per_level,
            request_timeout: timeout,
        }
    }

    fn normalize_url(&self, url: &str) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
        let mut normalized = url.to_string();
        
        // Add https if no scheme
        if !normalized.starts_with("http://") && !normalized.starts_with("https://") {
            normalized = format!("https://{}", normalized);
        }

        let parsed = Url::parse(&normalized)?;
        
        // Remove fragment
        let mut result = format!("{}://{}", parsed.scheme(), parsed.host_str().unwrap_or(""));
        
        if let Some(port) = parsed.port() {
            result.push_str(&format!(":{}", port));
        }

        let path = parsed.path();
        if path == "/" || path.is_empty() {
            result.push('/');
        } else {
            result.push_str(path);
        }

        if let Some(query) = parsed.query() {
            result.push_str(&format!("?{}", query));
        }

        Ok(result)
    }

    async fn fetch_url(&self, url: &str) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
        debug!("🦀 Attempting to fetch URL: {}", url);
        
        let response = self.client.get(url).send().await;
        
        match response {
            Ok(resp) => {
                debug!("🦀 Got HTTP response for {}: {}", url, resp.status());
                if resp.status().is_success() {
                    match resp.text().await {
                        Ok(content) => {
                            debug!("🦀 Successfully read content from {}: {} bytes", url, content.len());
                            Ok(content)
                        }
                        Err(e) => {
                            error!("🦀 Failed to read response body from {}: {}", url, e);
                            Err(e.into())
                        }
                    }
                } else {
                    warn!("🦀 HTTP error for {}: {}", url, resp.status());
                    Err(format!("HTTP {} for {}", resp.status(), url).into())
                }
            }
            Err(e) => {
                error!("🦀 Request failed for {}: {}", url, e);
                Err(e.into())
            }
        }
    }

    fn process_sitemap<'a>(
        &'a self,
        sitemap_url: &'a str,
        base_url: &'a str,
        visited: &'a mut HashSet<String>,
        max_depth: usize,
    ) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<(HashSet<String>, usize), Box<dyn std::error::Error + Send + Sync>>> + Send + 'a>> {
        Box::pin(async move {
            if visited.contains(sitemap_url) || max_depth == 0 {
                return Ok((HashSet::new(), 0));
            }

            visited.insert(sitemap_url.to_string());
            let mut request_count = 1;

            let content = self.fetch_url(sitemap_url).await?;
            let SitemapParseResult { urls, nested_sitemaps } = parse_sitemap_xml(&content, base_url)?;

            let mut all_urls = urls;

            // Process nested sitemaps concurrently for better performance
            if !nested_sitemaps.is_empty() && max_depth > 1 {
                // Pre-filter and collect URLs to process, avoiding borrowing conflicts
                let urls_to_process: Vec<String> = nested_sitemaps.iter()
                    .filter(|url| !visited.contains(*url))
                    .take(self.max_nested_per_level) // Use configurable limit
                    .cloned()
                    .collect();

                // Mark URLs as visited before processing to prevent duplicates
                for url in &urls_to_process {
                    visited.insert(url.clone());
                }

                let futures: Vec<_> = urls_to_process.iter()
                    .map(|nested_url| {
                        self.fetch_and_process_single_sitemap(nested_url, base_url, max_depth - 1)
                    })
                    .collect();

                let results = join_all(futures).await;
                
                for result in results {
                    match result {
                        Ok((nested_urls, nested_requests)) => {
                            all_urls.extend(nested_urls);
                            request_count += nested_requests;
                        }
                        Err(e) => {
                            warn!("🦀 Error processing nested sitemap: {}", e);
                        }
                    }
                }
            }

            Ok((all_urls, request_count))
        })
    }

    async fn fetch_and_process_single_sitemap(
        &self,
        sitemap_url: &str, 
        base_url: &str,
        max_depth: usize,
    ) -> Result<(HashSet<String>, usize), Box<dyn std::error::Error + Send + Sync>> {
        debug!("🦀 Processing single sitemap: {} (depth: {})", sitemap_url, max_depth);
        
        if max_depth == 0 {
            return Ok((HashSet::new(), 0));
        }

        let mut request_count = 1;
        let content = self.fetch_url(sitemap_url).await?;
        let SitemapParseResult { urls, nested_sitemaps } = parse_sitemap_xml(&content, base_url)?;
        
        let mut all_urls = urls;
        
        // Process nested sitemaps recursively if depth allows
        if !nested_sitemaps.is_empty() && max_depth > 1 {
            debug!("🦀 Found {} nested sitemaps in {}, processing up to {} with depth {}", 
                   nested_sitemaps.len(), sitemap_url, self.max_nested_per_level, max_depth - 1);
            
            // Limit nested sitemaps to process 
            let limited_nested: Vec<_> = nested_sitemaps.iter()
                .take(self.max_nested_per_level)
                .cloned()
                .collect();
            
            // Process nested sitemaps concurrently
            let futures: Vec<_> = limited_nested.iter()
                .map(|nested_url| {
                    self.fetch_and_process_single_sitemap(nested_url, base_url, max_depth - 1)
                })
                .collect();

            let results = join_all(futures).await;
            
            for result in results {
                match result {
                    Ok((nested_urls, nested_requests)) => {
                        all_urls.extend(nested_urls);
                        request_count += nested_requests;
                    }
                    Err(e) => {
                        warn!("🦀 Error processing nested sitemap: {}", e);
                    }
                }
            }
        }
        
        debug!("🦀 Completed processing {}: {} total URLs, {} requests", sitemap_url, all_urls.len(), request_count);
        Ok((all_urls, request_count))
    }

    pub async fn parse_site(&self, base_url: &str) -> Result<ParsedSiteResult, Box<dyn std::error::Error + Send + Sync>> {
        let start_time = Instant::now();
        let mut result = ParsedSiteResult::new(base_url.to_string());

        debug!("🦀 Starting to parse site: {}", base_url);
        let normalized_url = self.normalize_url(base_url)?;
        let robots_url = format!("{}/robots.txt", normalized_url.trim_end_matches('/'));

        debug!("🦀 Fetching robots.txt from: {}", robots_url);
        // Fetch robots.txt
        match self.fetch_url(&robots_url).await {
            Ok(robots_content) => {
                debug!("🦀 Successfully fetched robots.txt for {}", base_url);
                result.total_requests += 1;
                
                let sitemaps = parse_robots_txt(&robots_content, &normalized_url);
                
                if sitemaps.is_empty() {
                    // Try common sitemap locations
                    result.sitemaps_found = vec![
                        format!("{}/sitemap.xml", normalized_url.trim_end_matches('/')),
                        format!("{}/sitemap_index.xml", normalized_url.trim_end_matches('/')),
                        format!("{}/sitemaps.xml", normalized_url.trim_end_matches('/')),
                    ];
                } else {
                    result.sitemaps_found = sitemaps;
                }

                // Use configurable max_sitemaps limit
                let limited_sitemaps: Vec<_> = result.sitemaps_found.iter().take(self.max_sitemaps).cloned().collect();
                debug!("🦀 Processing first {} sitemaps out of {} total", limited_sitemaps.len(), result.sitemaps_found.len());

                // Process sitemaps concurrently for better performance
                let futures: Vec<_> = limited_sitemaps.iter()
                    .map(|sitemap_url| {
                        self.fetch_and_process_single_sitemap(sitemap_url, &normalized_url, self.max_depth) // Start with max_depth
                    })
                    .collect();

                let results = join_all(futures).await;
                
                for single_result in results {
                    match single_result {
                        Ok((urls, requests)) => {
                            result.urls.extend(urls);
                            result.total_requests += requests;
                        }
                        Err(e) => {
                            result.errors.push(format!("Error processing sitemap: {}", e));
                        }
                    }
                }
            }
            Err(e) => {
                result.errors.push(format!("Could not fetch robots.txt from {}: {}", robots_url, e));
            }
        }

        result.parse_time = start_time.elapsed().as_secs_f64();
        Ok(result)
    }

    pub async fn parse_multiple_sites(&self, base_urls: Vec<String>) -> Result<Vec<ParsedSiteResult>, Box<dyn std::error::Error + Send + Sync>> {
        let site_count = base_urls.len();
        info!("🦀 Rust parser starting to process {} sites concurrently with semaphore limit {}", site_count, self.max_concurrent);
        
        // Create semaphore to limit concurrent sites (exactly like Python)
        let semaphore = std::sync::Arc::new(Semaphore::new(self.max_concurrent));
        
        // Process sites concurrently with semaphore limit (matching Python exactly)
        let futures: Vec<_> = base_urls.into_iter()
            .enumerate()
            .map(|(i, base_url)| {
                let semaphore_clone = semaphore.clone();
                async move {
                    // Acquire semaphore permit (same as Python's `async with semaphore:`)
                    let _permit = semaphore_clone.acquire().await.map_err(|e| format!("Semaphore error: {}", e))?;
                    
                    info!("🦀 Starting site {}/{}: {}", i + 1, site_count, base_url);
                    match self.parse_site(&base_url).await {
                        Ok(result) => {
                            info!("🦀 Successfully parsed {}: {} URLs found", base_url, result.urls.len());
                            Ok(result)
                        },
                        Err(e) => {
                            error!("🦀 Failed to parse {}: {}", base_url, e);
                            let mut error_result = ParsedSiteResult::new(base_url.clone());
                            error_result.errors.push(format!("Failed to parse {}: {}", base_url, e));
                            Ok(error_result)
                        }
                    }
                }
            })
            .collect();
        
        // Wait for all sites to complete (same as Python's `await asyncio.gather()`)
        let results: Result<Vec<_>, _> = join_all(futures).await.into_iter().collect();
        
        info!("🦀 Rust parser completed processing all {} sites concurrently", site_count);
        results
    }

    /// Parse specific sitemap URLs directly without robots.txt discovery
    pub async fn parse_specific_sitemaps(&self, sitemap_urls: Vec<String>) -> Result<HashSet<String>, Box<dyn std::error::Error + Send + Sync>> {
        info!("🦀 Starting to parse {} specific sitemap URLs", sitemap_urls.len());
        
        // Pre-compute base URLs to avoid borrowing issues
        let url_pairs: Vec<(String, String)> = sitemap_urls.iter().map(|sitemap_url| {
            let base_url = if let Ok(parsed_url) = url::Url::parse(sitemap_url) {
                format!("{}://{}", parsed_url.scheme(), parsed_url.host_str().unwrap_or(""))
            } else {
                sitemap_url.clone() // fallback
            };
            (sitemap_url.clone(), base_url)
        }).collect();
        
        // Process all sitemaps concurrently
        let sitemap_futures: Vec<_> = url_pairs.iter().map(|(sitemap_url, base_url)| {
            self.fetch_and_process_single_sitemap(sitemap_url, base_url, 1)
        }).collect();

        // Wait for all sitemaps to complete
        let sitemap_results = join_all(sitemap_futures).await;
        
        let mut all_urls = HashSet::new();
        let mut total_requests = 0;
        
        for (i, result) in sitemap_results.into_iter().enumerate() {
            match result {
                Ok((urls, requests)) => {
                    debug!("🦀 Sitemap {}/{} found {} URLs", i + 1, sitemap_urls.len(), urls.len());
                    all_urls.extend(urls);
                    total_requests += requests;
                }
                Err(e) => {
                    warn!("🦀 Failed to process sitemap {}: {}", sitemap_urls[i], e);
                }
            }
        }
        
        info!("🦀 Completed parsing specific sitemaps: {} total URLs, {} requests", all_urls.len(), total_requests);
        Ok(all_urls)
    }
}
