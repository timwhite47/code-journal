use url::Url;

/// Parse robots.txt content and extract sitemap URLs
pub fn parse_robots_txt(content: &str, base_url: &str) -> Vec<String> {
    let mut sitemaps = Vec::new();
    
    for line in content.lines() {
        let line = line.trim();
        if line.to_lowercase().starts_with("sitemap:") {
            if let Some(sitemap_url) = line.get(8..).map(|s| s.trim()) {
                if !sitemap_url.is_empty() {
                    // Handle relative URLs
                    let absolute_url = if sitemap_url.starts_with('/') {
                        if let Ok(base) = Url::parse(base_url) {
                            if let Ok(joined) = base.join(sitemap_url) {
                                joined.to_string()
                            } else {
                                sitemap_url.to_string()
                            }
                        } else {
                            sitemap_url.to_string()
                        }
                    } else if sitemap_url.starts_with("http://") || sitemap_url.starts_with("https://") {
                        sitemap_url.to_string()
                    } else {
                        // Relative URL without leading slash
                        if let Ok(base) = Url::parse(base_url) {
                            if let Ok(joined) = base.join(sitemap_url) {
                                joined.to_string()
                            } else {
                                format!("{}/{}", base_url.trim_end_matches('/'), sitemap_url)
                            }
                        } else {
                            format!("{}/{}", base_url.trim_end_matches('/'), sitemap_url)
                        }
                    };
                    
                    sitemaps.push(absolute_url);
                }
            }
        }
    }
    
    sitemaps
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_robots_txt() {
        let content = r#"User-agent: *
Disallow: /private/

Sitemap: https://example.com/sitemap.xml
Sitemap: /relative-sitemap.xml

# More rules
Allow: /public/"#;

        let base_url = "https://example.com";
        let sitemaps = parse_robots_txt(content, base_url);
        
        assert_eq!(sitemaps.len(), 2);
        assert!(sitemaps.contains(&"https://example.com/sitemap.xml".to_string()));
        assert!(sitemaps.contains(&"https://example.com/relative-sitemap.xml".to_string()));
    }

    #[test]
    fn test_parse_robots_txt_case_insensitive() {
        let content = "SITEMAP: https://example.com/sitemap.xml\nsitemap: /another.xml";
        let base_url = "https://example.com";
        let sitemaps = parse_robots_txt(content, base_url);
        
        assert_eq!(sitemaps.len(), 2);
        assert!(sitemaps.contains(&"https://example.com/sitemap.xml".to_string()));
        assert!(sitemaps.contains(&"https://example.com/another.xml".to_string()));
    }

    #[test]
    fn test_parse_robots_txt_empty() {
        let content = "User-agent: *\nDisallow: /";
        let base_url = "https://example.com";
        let sitemaps = parse_robots_txt(content, base_url);
        
        assert!(sitemaps.is_empty());
    }
}
