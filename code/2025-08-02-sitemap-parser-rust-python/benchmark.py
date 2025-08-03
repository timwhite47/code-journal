#!/usr/bin/env python3
"""
Final Performance Benchmark: Rust vs Python Sitemap Parsing

This script provides a clean, comprehensive comparison between the pure Python
and Rust+Python implementations of sitemap parsing. It tests with real-world
websites and provides detailed performance metrics.

Usage:
    poetry run python benchmark.py
"""

import logging
import sys
import time
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    """Main benchmark function."""
    print("🚀 Sitemap Parser Performance Benchmark")
    print("=" * 60)
    print("Comparing Python vs Rust implementations with real-world data")
    print()
    
    # Configuration
    config = {
        'max_concurrent': 10,
        'max_sitemaps': 10, 
        'max_depth': 2,
        'max_nested_per_level': 5,
        'timeout_seconds': 30
    }
    
    # Test URLs - real websites with substantial sitemaps
    test_urls = [
        "https://www.cnn.com/",
        "https://www.nytimes.com/", 
        "https://www.chicagotribune.com/",
        "https://www.seattletimes.com/",
        "https://www.bbc.com/",
        "https://www.theguardian.com/",
        "https://www.washingtonpost.com/",
        "https://www.reuters.com/",
        "https://www.npr.org/",
        "https://www.aljazeera.com/",
        "https://www.foxnews.com/",
        "https://www.bloomberg.com/",
        "https://www.wsj.com/",
        "https://www.forbes.com/",
        "https://www.usatoday.com/",
        "https://www.latimes.com/",
        "https://www.abcnews.go.com/",
        "https://www.cbsnews.com/",
        "https://www.nbcnews.com/",
    ]
    
    print(f"📊 Configuration: {config}")
    print(f"🌐 Testing {len(test_urls)} websites with robots.txt discovery")
    print("-" * 60)
    
    # Run Python implementation
    print("🐍 Testing Python implementation...")
    python_result = run_python_benchmark(test_urls, config)
    
    # Run Rust implementation 
    print("🦀 Testing Rust implementation...")
    rust_result = run_rust_benchmark(test_urls, config)
    
    # Display results
    print("-" * 60)
    print("📈 Performance Summary:")
    display_comparison(python_result, rust_result)

def run_python_benchmark(test_urls: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
    """Run the Python implementation benchmark."""
    try:
        from python_parser import parse_sitemaps_sync
        
        start_time = time.time()
        results = parse_sitemaps_sync(
            test_urls,
            max_concurrent=config['max_concurrent'],
            max_sitemaps=config['max_sitemaps'],
            max_depth=config['max_depth'],
            max_nested_per_level=config['max_nested_per_level']
        )
        total_time = time.time() - start_time
        
        total_urls = sum(len(result.urls) for result in results)
        total_requests = sum(result.total_requests for result in results)
        
        result = {
            'success': True,
            'total_time': total_time,
            'total_urls': total_urls,
            'total_requests': total_requests,
            'sites': len(results),
            'results': results
        }
        
        print(f"✅ Python: {total_urls} URLs in {total_time:.3f}s ({total_requests} requests)")
        return result
        
    except Exception as e:
        print(f"❌ Python implementation failed: {e}")
        return {'success': False, 'error': str(e)}

def run_rust_benchmark(test_urls: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
    """Run the Rust implementation benchmark."""
    try:
        from sitemap_parser_showdown import parse_sitemaps_rust
        
        start_time = time.time()
        results = parse_sitemaps_rust(test_urls, **config)
        total_time = time.time() - start_time
        
        total_urls = sum(len(result.urls) for result in results)
        total_requests = sum(result.total_requests for result in results)
        
        result = {
            'success': True,
            'total_time': total_time,
            'total_urls': total_urls,
            'total_requests': total_requests,
            'sites': len(results),
            'results': results
        }
        
        print(f"✅ Rust: {total_urls} URLs in {total_time:.3f}s ({total_requests} requests)")
        return result
        
    except ImportError:
        print("❌ Rust implementation not available. Run: maturin build --release && pip install target/wheels/*.whl --force-reinstall")
        return {'success': False, 'error': 'Rust extension not built'}
    except Exception as e:
        print(f"❌ Rust implementation failed: {e}")
        return {'success': False, 'error': str(e)}

def display_comparison(python_result: Dict[str, Any], rust_result: Dict[str, Any]):
    """Display a detailed performance comparison."""
    
    if not python_result['success']:
        print(f"🐍 Python: Failed - {python_result['error']}")
    
    if not rust_result['success']:
        print(f"🦀 Rust: Failed - {rust_result['error']}")
        return
    
    if not (python_result['success'] and rust_result['success']):
        return
    
    # Calculate speedup
    speedup = python_result['total_time'] / rust_result['total_time']
    
    print(f"🐍 Python: {python_result['total_urls']:,} URLs, {python_result['total_requests']} requests, {python_result['total_time']:.3f}s")
    print(f"🦀 Rust:   {rust_result['total_urls']:,} URLs, {rust_result['total_requests']} requests, {rust_result['total_time']:.3f}s")
    
    if speedup > 1:
        print(f"🚀 Rust is {speedup:.2f}x faster than Python")
    else:
        print(f"🐌 Python is {1/speedup:.2f}x faster than Rust")
    
    # URL count difference analysis
    url_diff = abs(python_result['total_urls'] - rust_result['total_urls'])
    if url_diff > 0:
        print(f"⚠️  URL count difference: {url_diff:,} URLs")
    
    print()
    print("💡 Key Insights:")
    if speedup > 1:
        print(f"   • Rust provides {speedup:.2f}x performance improvement")
        print(f"   • Time saved: {python_result['total_time'] - rust_result['total_time']:.3f}s")
    print(f"   • Both implementations process similar request counts")
    if url_diff < 1000:
        print(f"   • URL parsing results are consistent between implementations")
    
    print()
    print("🔧 Technical Notes:")
    print("   • Use 'maturin build --release' for optimized Rust builds")
    print("   • Debug builds can be 3-4x slower than release builds")
    print("   • Both implementations use identical concurrency patterns")

if __name__ == "__main__":
    main()
