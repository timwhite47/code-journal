#!/usr/bin/env python3
"""
Benchmarking utilities for comparing Python vs Rust implementations.
"""

import time
import statistics
import asyncio
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

from .python_parser import PythonSitemapParser, parse_sitemaps_sync
try:
    from .rust_parser import parse_sitemaps_rust, RustParser
    RUST_AVAILABLE = True
except ImportError:
    parse_sitemaps_rust = None
    RustParser = None
    RUST_AVAILABLE = False


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    implementation: str
    urls_tested: List[str]
    total_urls_found: int
    total_sitemaps_found: int
    execution_time: float
    total_requests: int
    errors: List[str]
    urls_per_second: float
    requests_per_second: float


class SitemapBenchmark:
    """Performance benchmarking for sitemap parsers."""
    
    def __init__(self, test_urls: List[str], max_concurrent: int = 10, timeout: int = 30):
        self.test_urls = test_urls
        self.max_concurrent = max_concurrent
        self.timeout = timeout
    
    async def benchmark_python(self, runs: int = 1) -> List[BenchmarkResult]:
        """Benchmark the pure Python implementation."""
        results = []
        
        for run in range(runs):
            print(f"🐍 Python run {run + 1}/{runs}")
            start_time = time.time()
            
            # Run the Python parser
            parsed_results = parse_sitemaps_sync(
                self.test_urls, 
                max_concurrent=self.max_concurrent
            )
            
            execution_time = time.time() - start_time
            
            # Calculate metrics
            total_urls = sum(len(r.urls) for r in parsed_results)
            total_sitemaps = sum(len(r.sitemaps_found) for r in parsed_results)
            total_requests = sum(r.total_requests for r in parsed_results)
            all_errors = []
            for r in parsed_results:
                all_errors.extend(r.errors)
            
            result = BenchmarkResult(
                implementation="Python",
                urls_tested=self.test_urls.copy(),
                total_urls_found=total_urls,
                total_sitemaps_found=total_sitemaps,
                execution_time=execution_time,
                total_requests=total_requests,
                errors=all_errors,
                urls_per_second=total_urls / execution_time if execution_time > 0 else 0,
                requests_per_second=total_requests / execution_time if execution_time > 0 else 0,
            )
            results.append(result)
            
            print(f"   ✅ Found {total_urls} URLs in {execution_time:.2f}s")
        
        return results
    
    def benchmark_rust(self, runs: int = 1) -> List[BenchmarkResult]:
        """Benchmark the Rust implementation."""
        if not RUST_AVAILABLE:
            raise RuntimeError("Rust parser not available. Build with maturin first.")
        
        results = []
        
        for run in range(runs):
            print(f"🦀 Rust run {run + 1}/{runs}")
            start_time = time.time()
            
            # Run the Rust parser
            parsed_results = parse_sitemaps_rust(
                self.test_urls,
                max_concurrent=self.max_concurrent,
                timeout_seconds=self.timeout
            )
            
            execution_time = time.time() - start_time
            
            # Calculate metrics
            total_urls = sum(len(r.urls) for r in parsed_results)
            total_sitemaps = sum(len(r.sitemaps_found) for r in parsed_results)
            total_requests = sum(r.total_requests for r in parsed_results)
            all_errors = []
            for r in parsed_results:
                all_errors.extend(r.errors)
            
            result = BenchmarkResult(
                implementation="Rust",
                urls_tested=self.test_urls.copy(),
                total_urls_found=total_urls,
                total_sitemaps_found=total_sitemaps,
                execution_time=execution_time,
                total_requests=total_requests,
                errors=all_errors,
                urls_per_second=total_urls / execution_time if execution_time > 0 else 0,
                requests_per_second=total_requests / execution_time if execution_time > 0 else 0,
            )
            results.append(result)
            
            print(f"   ✅ Found {total_urls} URLs in {execution_time:.2f}s")
        
        return results


def run_benchmark(test_urls: List[str], runs: int = 3, max_concurrent: int = 10) -> Dict[str, Any]:
    """
    Run complete benchmark comparing Python and Rust implementations.
    
    Args:
        test_urls: URLs to test parsing
        runs: Number of runs per implementation
        max_concurrent: Maximum concurrent connections
        
    Returns:
        Dictionary with detailed benchmark results
    """
    print(f"🏁 Starting sitemap parser benchmark")
    print(f"   URLs: {test_urls}")
    print(f"   Runs per implementation: {runs}")
    print(f"   Max concurrent: {max_concurrent}")
    print("=" * 60)
    
    benchmark = SitemapBenchmark(test_urls, max_concurrent=max_concurrent)
    
    # Run Python benchmark
    python_results = asyncio.run(benchmark.benchmark_python(runs))
    
    # Run Rust benchmark if available
    rust_results = []
    if RUST_AVAILABLE:
        rust_results = benchmark.benchmark_rust(runs)
    else:
        print("⚠️  Rust implementation not available - run 'maturin develop' first")
    
    # Calculate statistics
    results = {
        "test_config": {
            "urls": test_urls,
            "runs": runs,
            "max_concurrent": max_concurrent,
        },
        "python": {
            "results": python_results,
            "avg_execution_time": statistics.mean([r.execution_time for r in python_results]),
            "avg_urls_per_second": statistics.mean([r.urls_per_second for r in python_results]),
            "avg_requests_per_second": statistics.mean([r.requests_per_second for r in python_results]),
        },
        "rust": {
            "results": rust_results,
            "avg_execution_time": statistics.mean([r.execution_time for r in rust_results]) if rust_results else 0,
            "avg_urls_per_second": statistics.mean([r.urls_per_second for r in rust_results]) if rust_results else 0,
            "avg_requests_per_second": statistics.mean([r.requests_per_second for r in rust_results]) if rust_results else 0,
        }
    }
    
    # Calculate performance comparison
    if rust_results:
        python_avg_time = results["python"]["avg_execution_time"]
        rust_avg_time = results["rust"]["avg_execution_time"]
        
        if rust_avg_time > 0:
            speedup = python_avg_time / rust_avg_time
            results["comparison"] = {
                "rust_speedup_factor": speedup,
                "rust_faster_percent": ((python_avg_time - rust_avg_time) / python_avg_time) * 100,
            }
    
    return results


def compare_implementations(test_urls: List[str], runs: int = 3) -> None:
    """
    Run benchmark and print a detailed comparison report.
    
    Args:
        test_urls: URLs to test
        runs: Number of runs per implementation
    """
    results = run_benchmark(test_urls, runs)
    
    print("\n" + "=" * 60)
    print("📊 BENCHMARK RESULTS")
    print("=" * 60)
    
    # Python results
    python_stats = results["python"]
    print(f"\n🐍 Python Implementation:")
    print(f"   Average execution time: {python_stats['avg_execution_time']:.2f}s")
    print(f"   Average URLs/second: {python_stats['avg_urls_per_second']:.1f}")
    print(f"   Average requests/second: {python_stats['avg_requests_per_second']:.1f}")
    
    # Rust results
    rust_stats = results["rust"]
    if rust_stats["results"]:
        print(f"\n🦀 Rust Implementation:")
        print(f"   Average execution time: {rust_stats['avg_execution_time']:.2f}s")
        print(f"   Average URLs/second: {rust_stats['avg_urls_per_second']:.1f}")
        print(f"   Average requests/second: {rust_stats['avg_requests_per_second']:.1f}")
        
        # Comparison
        if "comparison" in results:
            comp = results["comparison"]
            print(f"\n⚡ Performance Comparison:")
            print(f"   Rust is {comp['rust_speedup_factor']:.1f}x faster")
            print(f"   Rust improvement: {comp['rust_faster_percent']:.1f}%")
    else:
        print(f"\n🦀 Rust Implementation: Not available")
    
    # Summary table
    print(f"\n📋 Detailed Results:")
    print(f"{'Implementation':<12} {'Time (s)':<10} {'URLs/s':<10} {'Req/s':<10}")
    print("-" * 45)
    
    for result in python_stats["results"]:
        print(f"{'Python':<12} {result.execution_time:<10.2f} {result.urls_per_second:<10.1f} {result.requests_per_second:<10.1f}")
    
    for result in rust_stats["results"]:
        print(f"{'Rust':<12} {result.execution_time:<10.2f} {result.urls_per_second:<10.1f} {result.requests_per_second:<10.1f}")


if __name__ == "__main__":
    # Example benchmark run
    test_urls = [
        "https://www.nytimes.com/",
        "https://www.cnn.com/",
        "https://www.seattletimes.com/",
    ]
    
    compare_implementations(test_urls, runs=2)
