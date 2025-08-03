"""
Sitemap Parser Showdown: Pure Python vs Rust+Python Performance Comparison

This package demonstrates the performance differences between pure Python
and Rust+Python hybrid implementations for parsing sitemaps from websites.
"""

from .python_parser import PythonSitemapParser, SitemapResult, parse_sitemaps_sync
from .benchmark import run_benchmark, compare_implementations

# Try to import Rust parser, gracefully handle if not built
try:
    from .rust_parser import RustParser, parse_sitemaps_rust
    RUST_AVAILABLE = True
except ImportError:
    RustParser = None
    parse_sitemaps_rust = None
    RUST_AVAILABLE = False

__version__ = "0.1.0"
__all__ = [
    "PythonSitemapParser",
    "SitemapResult", 
    "parse_sitemaps_sync",
    "RustParser",
    "parse_sitemaps_rust",
    "run_benchmark",
    "compare_implementations",
    "RUST_AVAILABLE",
]
