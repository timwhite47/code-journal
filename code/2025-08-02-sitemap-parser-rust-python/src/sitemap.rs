use quick_xml::events::Event;
use quick_xml::Reader;
use std::collections::HashSet;
use url::Url;

#[derive(Debug, Default)]
pub struct SitemapParseResult {
    pub urls: HashSet<String>,
    pub nested_sitemaps: Vec<String>,
}

/// Parse sitemap XML content and extract URLs and nested sitemap references
pub fn parse_sitemap_xml(content: &str, base_url: &str) -> Result<SitemapParseResult, Box<dyn std::error::Error + Send + Sync>> {
    let mut result = SitemapParseResult::default();
    let mut reader = Reader::from_str(content);
    reader.config_mut().trim_text(true);
    
    let mut buf = Vec::new();
    let mut in_url = false;
    let mut in_sitemap = false;
    let mut in_image = false;  // Track if we're inside an image element
    let mut in_loc = false;
    let mut current_text = String::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(ref e)) => {
                let name_bytes = e.local_name();
                if let Ok(name_str) = std::str::from_utf8(name_bytes.as_ref()) {
                    match name_str {
                        "url" => in_url = true,
                        "sitemap" => in_sitemap = true,
                        "image" => in_image = true,  // Track image elements
                        "loc" => {
                            in_loc = true;
                            current_text.clear();
                        }
                        _ => {}
                    }
                }
            }
            Ok(Event::End(ref e)) => {
                let name_bytes = e.local_name();
                if let Ok(name_str) = std::str::from_utf8(name_bytes.as_ref()) {
                    match name_str {
                        "url" => in_url = false,
                        "sitemap" => in_sitemap = false,
                        "image" => in_image = false,  // Reset image tracking
                        "loc" => {
                            if in_loc {
                                let url = current_text.trim();
                                if !url.is_empty() {
                                    if in_sitemap {
                                        // This is a nested sitemap reference
                                        let absolute_url = make_absolute_url(url, base_url)?;
                                        result.nested_sitemaps.push(absolute_url);
                                    } else if in_url && !in_image {
                                        // This is a regular URL, but NOT an image URL
                                        // Only include URLs that are directly in <url> elements, not in <image> elements
                                        result.urls.insert(url.to_string());
                                    }
                                    // Skip URLs that are in image elements (in_image = true)
                                }
                                in_loc = false;
                                current_text.clear();
                            }
                        }
                        _ => {}
                    }
                }
            }
            Ok(Event::Text(e)) => {
                if in_loc {
                    // Convert to string directly without unescaping for now
                    current_text.push_str(&String::from_utf8_lossy(&e));
                }
            }
            Ok(Event::CData(e)) => {
                if in_loc {
                    current_text.push_str(&String::from_utf8_lossy(&e));
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => {
                // Try to handle malformed XML gracefully
                eprintln!("XML parsing error: {}, continuing...", e);
                break;
            }
            _ => {}
        }
        buf.clear();
    }

    // Fallback: if we couldn't parse as structured XML, try a simpler approach
    if result.urls.is_empty() && result.nested_sitemaps.is_empty() {
        parse_fallback(content, base_url, &mut result)?;
    }

    Ok(result)
}

/// Fallback parser for malformed or non-standard XML
fn parse_fallback(content: &str, base_url: &str, result: &mut SitemapParseResult) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    // Simple regex-like approach to find <loc> tags
    let loc_pattern = "<loc>";
    let end_loc_pattern = "</loc>";
    
    let mut start = 0;
    while let Some(loc_start) = content[start..].find(loc_pattern) {
        let absolute_start = start + loc_start + loc_pattern.len();
        if let Some(loc_end) = content[absolute_start..].find(end_loc_pattern) {
            let url = content[absolute_start..absolute_start + loc_end].trim();
            if !url.is_empty() {
                // Check if this might be in a sitemap context by looking backwards
                let context_start = (start + loc_start).saturating_sub(100);
                let context = &content[context_start..start + loc_start];
                
                if context.contains("<sitemap") && !context.contains("</sitemap>") {
                    // Likely a sitemap reference
                    let absolute_url = make_absolute_url(url, base_url)?;
                    result.nested_sitemaps.push(absolute_url);
                } else {
                    // Likely a regular URL
                    result.urls.insert(url.to_string());
                }
            }
            start = absolute_start + loc_end + end_loc_pattern.len();
        } else {
            break;
        }
    }
    
    Ok(())
}

/// Convert a potentially relative URL to an absolute URL
fn make_absolute_url(url: &str, base_url: &str) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    if url.starts_with("http://") || url.starts_with("https://") {
        Ok(url.to_string())
    } else if url.starts_with('/') {
        if let Ok(base) = Url::parse(base_url) {
            Ok(base.join(url)?.to_string())
        } else {
            Ok(format!("{}{}", base_url.trim_end_matches('/'), url))
        }
    } else {
        // Relative URL without leading slash
        if let Ok(base) = Url::parse(base_url) {
            Ok(base.join(url)?.to_string())
        } else {
            Ok(format!("{}/{}", base_url.trim_end_matches('/'), url))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_urlset() {
        let xml = r#"<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/page1</loc>
    <lastmod>2023-01-01</lastmod>
  </url>
  <url>
    <loc>https://example.com/page2</loc>
    <lastmod>2023-01-02</lastmod>
  </url>
</urlset>"#;

        let result = parse_sitemap_xml(xml, "https://example.com").unwrap();
        assert_eq!(result.urls.len(), 2);
        assert!(result.urls.contains("https://example.com/page1"));
        assert!(result.urls.contains("https://example.com/page2"));
        assert!(result.nested_sitemaps.is_empty());
    }

    #[test]
    fn test_parse_sitemapindex() {
        let xml = r#"<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://example.com/sitemap1.xml</loc>
    <lastmod>2023-01-01</lastmod>
  </sitemap>
  <sitemap>
    <loc>/sitemap2.xml</loc>
    <lastmod>2023-01-02</lastmod>
  </sitemap>
</sitemapindex>"#;

        let result = parse_sitemap_xml(xml, "https://example.com").unwrap();
        assert!(result.urls.is_empty());
        assert_eq!(result.nested_sitemaps.len(), 2);
        assert!(result.nested_sitemaps.contains(&"https://example.com/sitemap1.xml".to_string()));
        assert!(result.nested_sitemaps.contains(&"https://example.com/sitemap2.xml".to_string()));
    }

    #[test]
    fn test_make_absolute_url() {
        assert_eq!(
            make_absolute_url("https://example.com/page", "https://base.com").unwrap(),
            "https://example.com/page"
        );
        
        assert_eq!(
            make_absolute_url("/relative", "https://example.com").unwrap(),
            "https://example.com/relative"
        );
        
        assert_eq!(
            make_absolute_url("relative", "https://example.com/").unwrap(),
            "https://example.com/relative"
        );
    }

    #[test]
    fn test_parse_malformed_xml() {
        let xml = r#"<loc>https://example.com/page1</loc>
<loc>https://example.com/page2</loc>"#;

        let result = parse_sitemap_xml(xml, "https://example.com").unwrap();
        assert_eq!(result.urls.len(), 2);
    }
}
