use log::{info, warn, error, debug};
use pyo3::prelude::*;
use pyo3_async_runtimes::tokio::future_into_py;
use std::collections::HashSet;
use std::time::Instant;

mod parser;
mod robots;
mod sitemap;

use parser::RustSitemapParser;

/// Sitemap parsing result returned to Python
#[pyclass]
#[derive(Clone, Debug)]
pub struct SitemapResult {
    #[pyo3(get)]
    pub base_url: String,
    #[pyo3(get)]
    pub urls: Vec<String>,
    #[pyo3(get)]
    pub sitemaps_found: Vec<String>,
    #[pyo3(get)]
    pub errors: Vec<String>,
    #[pyo3(get)]
    pub parse_time: f64,
    #[pyo3(get)]
    pub total_requests: usize,
}

#[pymethods]
impl SitemapResult {
    #[new]
    fn new(base_url: String) -> Self {
        Self {
            base_url,
            urls: Vec::new(),
            sitemaps_found: Vec::new(),
            errors: Vec::new(),
            parse_time: 0.0,
            total_requests: 0,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "SitemapResult(base_url='{}', urls={}, sitemaps={}, errors={}, time={:.2}s, requests={})",
            self.base_url,
            self.urls.len(),
            self.sitemaps_found.len(),
            self.errors.len(),
            self.parse_time,
            self.total_requests
        )
    }

    fn __str__(&self) -> String {
        self.__repr__()
    }
}

/// Rust-powered sitemap parser exposed to Python
#[pyclass]
pub struct RustParser {
    max_concurrent: usize,
    max_sitemaps: usize,
    max_depth: usize,
    max_nested_per_level: usize,
    timeout_seconds: u64,
}

#[pymethods]
impl RustParser {
    #[new]
    #[pyo3(signature = (max_concurrent = 10, max_sitemaps = 10, max_depth = 2, max_nested_per_level = 5, timeout_seconds = 30))]
    fn new(max_concurrent: usize, max_sitemaps: usize, max_depth: usize, max_nested_per_level: usize, timeout_seconds: u64) -> Self {
        Self {
            max_concurrent,
            max_sitemaps,
            max_depth,
            max_nested_per_level,
            timeout_seconds,
        }
    }

    /// Parse a single site's sitemaps
    fn parse_site<'py>(&self, py: Python<'py>, base_url: String) -> PyResult<Bound<'py, PyAny>> {
        let max_concurrent = self.max_concurrent;
        let max_sitemaps = self.max_sitemaps;
        let max_depth = self.max_depth;
        let max_nested_per_level = self.max_nested_per_level;
        let timeout = tokio::time::Duration::from_secs(self.timeout_seconds);

        future_into_py(py, async move {
            let start_time = Instant::now();
            let mut result = SitemapResult::new(base_url.clone());

            let parser = RustSitemapParser::new(max_concurrent, max_sitemaps, max_depth, max_nested_per_level, timeout);
            
            match parser.parse_site(&base_url).await {
                Ok(parsed_result) => {
                    result.urls = parsed_result.urls.into_iter().collect();
                    result.sitemaps_found = parsed_result.sitemaps_found;
                    result.total_requests = parsed_result.total_requests;
                    result.errors = parsed_result.errors;
                }
                Err(e) => {
                    result.errors.push(format!("Failed to parse {}: {}", base_url, e));
                }
            }

            result.parse_time = start_time.elapsed().as_secs_f64();
            Ok(result)
        })
    }

    /// Parse specific sitemap URLs directly (bypassing robots.txt discovery)
    fn parse_sitemaps<'py>(&self, py: Python<'py>, sitemap_urls: Vec<String>) -> PyResult<Bound<'py, PyAny>> {
        let max_concurrent = self.max_concurrent;
        let max_sitemaps = self.max_sitemaps;
        let max_depth = self.max_depth;
        let max_nested_per_level = self.max_nested_per_level;
        let timeout = tokio::time::Duration::from_secs(self.timeout_seconds);

        future_into_py(py, async move {
            let parser = RustSitemapParser::new(max_concurrent, max_sitemaps, max_depth, max_nested_per_level, timeout);
            
            match parser.parse_specific_sitemaps(sitemap_urls).await {
                Ok(urls) => {
                    let url_vec: Vec<String> = urls.into_iter().collect();
                    info!("🦀 Finished parsing specific sitemaps, found {} URLs", url_vec.len());
                    Ok(url_vec)
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    format!("Failed to parse sitemaps: {}", e)
                ))
            }
        })
    }

    /// Parse multiple sites concurrently
    fn parse_multiple_sites<'py>(&self, py: Python<'py>, base_urls: Vec<String>) -> PyResult<Bound<'py, PyAny>> {
        let max_concurrent = self.max_concurrent;
        let max_sitemaps = self.max_sitemaps;
        let max_depth = self.max_depth;
        let max_nested_per_level = self.max_nested_per_level;
        let timeout = tokio::time::Duration::from_secs(self.timeout_seconds);

        future_into_py(py, async move {
            let parser = RustSitemapParser::new(max_concurrent, max_sitemaps, max_depth, max_nested_per_level, timeout);
            
            match parser.parse_multiple_sites(base_urls).await {
                Ok(results) => {
                    let py_results: Vec<SitemapResult> = results
                        .into_iter()
                        .map(|r| {
                            let mut result = SitemapResult::new(r.base_url);
                            result.urls = r.urls.into_iter().collect();
                            result.sitemaps_found = r.sitemaps_found;
                            result.total_requests = r.total_requests;
                            result.errors = r.errors;
                            result.parse_time = r.parse_time;
                            result
                        })
                        .collect();
                    Ok(py_results)
                }
                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    format!("Failed to parse sites: {}", e)
                ))
            }
        })
    }
}

/// Synchronous convenience function for parsing multiple sites
#[pyfunction]
#[pyo3(signature = (base_urls, max_concurrent = 10, max_sitemaps = 10, max_depth = 2, max_nested_per_level = 5, timeout_seconds = 30))]
fn parse_sitemaps_rust(
    base_urls: Vec<String>,
    max_concurrent: usize,
    max_sitemaps: usize,
    max_depth: usize,
    max_nested_per_level: usize,
    timeout_seconds: u64,
) -> PyResult<Vec<SitemapResult>> {
    info!("🦀 Starting Rust sitemap parsing for {} URLs", base_urls.len());
    debug!("🦀 Configuration: max_concurrent={}, max_sitemaps={}, max_depth={}, max_nested_per_level={}, timeout={}s", 
           max_concurrent, max_sitemaps, max_depth, max_nested_per_level, timeout_seconds);
    
    let rt = tokio::runtime::Runtime::new().map_err(|e| {
        error!("🦀 Failed to create Tokio runtime: {}", e);
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create runtime: {}", e))
    })?;

    let timeout = tokio::time::Duration::from_secs(timeout_seconds);
    let parser = RustSitemapParser::new(max_concurrent, max_sitemaps, max_depth, max_nested_per_level, timeout);

    rt.block_on(async {
        match parser.parse_multiple_sites(base_urls).await {
            Ok(results) => {
                let py_results: Vec<SitemapResult> = results
                    .into_iter()
                    .map(|r| {
                        let mut result = SitemapResult::new(r.base_url);
                        result.urls = r.urls.into_iter().collect();
                        result.sitemaps_found = r.sitemaps_found;
                        result.total_requests = r.total_requests;
                        result.errors = r.errors;
                        result.parse_time = r.parse_time;
                        result
                    })
                    .collect();
                Ok(py_results)
            }
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                format!("Failed to parse sites: {}", e)
            ))
        }
    })
}

/// The Rust sitemap parser module
#[pymodule]
fn rust_parser(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Initialize logging to send Rust logs to Python
    pyo3_log::init();
    
    m.add_class::<SitemapResult>()?;
    m.add_class::<RustParser>()?;
    m.add_function(wrap_pyfunction!(parse_sitemaps_rust, m)?)?;
    Ok(())
}
