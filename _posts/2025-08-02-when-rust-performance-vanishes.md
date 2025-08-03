---
layout: post
title: "When Rust Performance Vanishes: A Real-World AI-Assisted Discovery"
date: 2025-08-02
categories: [ai-coding, performance, rust, python]
tags: [rust, python, pyo3, maturin, performance, benchmarking, ai-assisted-development]
excerpt: "Rust was supposed to be 18x faster than Python for sitemap parsing. Then we scaled up the test and watched that advantage evaporate to 1.01x. Here's what we discovered about performance, profiling, and the surprising effectiveness of AI pair programming."
---

Rust is supposed to be blazingly fast, right? So when my AI pair programming session showed Rust beating Python by 18x, I was ready to declare victory. Then we scaled up the test and watched that advantage evaporate to 1.01x. Here's what we discovered about performance, profiling, and the surprising effectiveness of AI-assisted debugging.

Everyone "knows" Rust is faster than Python, but real-world performance tells a more nuanced story. This post chronicles an AI-assisted investigation that revealed when language choice matters and when it absolutely doesn't. We'll cover building identical sitemap parsers in Python and Rust+PyO3, discovering why 18x speedups disappeared at scale, AI pair programming insights, and when to choose Rust vs async Python for I/O-heavy workloads.

## The AI Collaboration Story

### What We Set Out to Build

My goal was simple: "Rust + Python performance demonstration using sitemap parsing." I wanted to see Rust's legendary performance in action, and sitemap parsing seemed like a perfect use case - lots of XML processing, HTTP requests, and data extraction. 

The AI's role evolved from implementation partner to debugger to methodology critic. What started as a simple comparison turned into a deep performance investigation that taught us both more than we expected.

### AI-Assisted Development: What Worked

**Rapid prototyping:** The AI's strength was taking high-level goals and rapidly scaffolding complete implementations. When I described wanting a "Rust + Python performance demonstration using sitemap parsing," the AI immediately understood this meant building identical parsers for fair comparison.

The AI broke down the task systematically: create a Rust library with PyO3 bindings, implement matching Python code, set up maturin for builds, and create benchmark scripts. Within minutes, I had a complete project structure that would have taken me hours to research and configure from scratch. The AI handled all the PyO3 boilerplate, tokio async setup, and maturin configuration that usually makes me procrastinate on Rust projects.

**Performance investigation partnership:** The real breakthrough came when initial results didn't make sense. I started with straightforward questions about why performance varied so dramatically between small and large datasets. The AI guided me through systematic analysis - comparing execution time breakdowns, examining network request patterns, and identifying where time was actually spent.

What impressed me was how the AI approached the performance mystery methodically. Rather than guessing, it suggested measuring different components separately: HTTP request time, XML parsing time, and overall execution patterns. This systematic debugging approach helped us discover that network I/O was dominating execution time in the large dataset scenario.

**Maintaining implementation consistency:** One of the trickiest aspects was ensuring both implementations were truly comparable. The AI excelled at maintaining identical patterns across languages - same semaphore limits, matching timeout configurations, equivalent error handling, and parallel concurrency models.

The AI caught subtle differences I would have missed, like default timeout settings between aiohttp and reqwest clients. It systematically aligned every configuration parameter to ensure fair comparison, which was crucial for meaningful performance analysis.

### AI-Assisted Development: What Didn't Work

**Over-engineering early phases:** The AI's initial instinct was to create comprehensive test suites with separate files for every conceivable scenario. This led to a proliferation of test files - benchmark variants, individual component tests, configuration experiments - that quickly became unwieldy.

I had to step in and ask for consolidation. The AI was excellent at implementing features but needed human guidance on when to stop adding complexity and start simplifying. This taught me that AI pairs well with explicit boundaries and consolidation requests rather than open-ended "build everything" instructions.

**Missing performance intuition:** When the 18x performance advantage disappeared at scale, the AI initially focused on implementation details rather than system-level analysis. It suggested code optimizations, memory management tweaks, and parsing improvements - all missing the fundamental shift from CPU-bound to I/O-bound workload.

The breakthrough came when I explicitly asked about network bottlenecks. The AI immediately recognized the pattern once pointed in the right direction, but it needed human intuition to question whether the results made sense at a system level. This highlighted that AI excels at systematic analysis but needs human insight for "does this feel right?" moments.

**Methodology gaps:** The AI was focused on implementation and immediate results rather than establishing proper measurement methodology. It didn't initially suggest profiling, timing breakdowns, or systematic performance analysis.

I had to explicitly redirect the conversation toward measurement before optimization. Once I asked "shouldn't we profile where time is actually spent?", the AI immediately understood and created comprehensive timing instrumentation. But it needed human guidance to prioritize understanding over optimizing.

### Surprising AI Insights

The AI demonstrated unexpected attention to subtle configuration details that I would have overlooked. During performance testing, it noticed that the Python aiohttp client and Rust reqwest client had different default timeout behaviors. Rather than assuming this was intentional, the AI flagged it as a potential fairness issue and systematically aligned both implementations to use identical 30-second timeouts.

This level of systematic attention to detail was invaluable for maintaining experimental validity. The AI didn't just implement features - it actively looked for inconsistencies that could invalidate our performance comparison.

**Clean architecture emergence:** When the codebase became cluttered with experimental files and test variants, the AI's solution was surprisingly effective: complete reconstruction from scratch using lessons learned. Rather than incrementally cleaning up messy code, it proposed rebuilding the entire project with proper separation of concerns.

This "clean slate" approach led to much better architecture than gradual refactoring would have achieved. The AI synthesized all our experiments into a coherent structure with clear boundaries between the Python parser, Rust parser, and benchmark orchestration.

**Collaborative debugging effectiveness:** The most surprising aspect was how well human intuition combined with AI's systematic approach. I would notice when results "felt wrong" or didn't match expectations, then the AI would methodically investigate the discrepancy.

This partnership was more effective than either approach alone. Human intuition identified problems worth investigating, while AI's systematic analysis uncovered root causes and verified hypotheses through measurement.

## Technical Deep Dive: The Implementation

### Project Architecture

Here's what we built:

```
├── src/
│   ├── lib.rs          # PyO3 bindings and Python API
│   ├── parser.rs       # Core Rust implementation  
│   ├── robots.rs       # robots.txt parsing
│   └── sitemap.rs      # XML sitemap parsing
├── python_parser.py    # Pure Python implementation
├── benchmark.py        # Performance comparison script
└── pyproject.toml      # Maturin + Poetry configuration
```

The key design decisions were:
- **Identical APIs:** Both implementations expose the same function signatures
- **Matching concurrency:** Same semaphore limits, timeouts, and error handling  
- **Real-world testing:** 19 major news websites vs synthetic data

### Rust Implementation Deep Dive

The PyO3 bindings were surprisingly straightforward:

```rust
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
    // Implementation details...
}
```

Critical performance components included:
- `reqwest::Client` with connection pooling and keepalives
- `tokio::sync::Semaphore` for concurrency control (matching Python exactly)
- `quick-xml` for fast XML parsing vs Python's ElementTree
- Conservative error handling to match Python behavior

The maturin build process was crucial:

```bash
# Debug build (development)
maturin develop

# Release build (benchmarking) - CRITICAL difference
maturin build --release
```

That `--release` flag made a massive difference. Debug builds were 3-4x slower than release builds.

### Python Implementation Deep Dive

The Python implementation used familiar async patterns:

```python
class PythonSitemapParser:
    async def parse_multiple_sites(self, base_urls: List[str]) -> List[SitemapResult]:
        semaphore = asyncio.Semaphore(self.max_concurrent)
        # Identical concurrency pattern to Rust
```

Key libraries included:
- `aiohttp` for async HTTP (vs Rust's `reqwest`)
- `xml.etree.ElementTree` for XML parsing (vs Rust's `quick-xml`)
- `asyncio.gather()` for concurrent processing (vs Rust's `join_all`)

### Benchmark Methodology

Our test configuration:

```python
config = {
    'max_concurrent': 10,      # Concurrent sites  
    'max_sitemaps': 10,        # Sitemaps per site
    'max_depth': 2,            # Nested sitemap recursion
    'max_nested_per_level': 5, # Limit explosive growth
    'timeout_seconds': 30      # Per-request timeout
}
```

We tested against 19 major news websites: CNN, NYTimes, BBC, Guardian, Washington Post, Reuters, NPR, Al Jazeera, Fox News, Bloomberg, WSJ, Forbes, USA Today, LA Times, ABC News, CBS News, NBC News, Chicago Tribune, and Seattle Times.

This gave us a mix of sitemap architectures, network variability, and real HTTP error conditions.

## The Performance Plot Twist

### Initial Results: Rust Dominance

With a small dataset (3 websites), the results were impressive:
- Rust: 3,847 URLs in 0.213s
- Python: 1,832 URLs in 3.847s  
- **Result: 18x Rust advantage**

Why such a huge difference? CPU-bound XML parsing dominated execution time. Rust's `quick-xml` vs Python's `ElementTree`, release build optimizations vs Python interpreter overhead, and the small dataset made parsing bottlenecks visible.

### Scaling Up: The Great Convergence  

Then we scaled to our full dataset (19 websites):
- Python: 647,952 URLs in 30.558s (337 requests)
- Rust: 571,034 URLs in 30.399s (301 requests)
- **Result: 1.01x difference - essentially identical performance**

### What Happened? Network I/O Bottlenecks

The real bottleneck revealed itself:
- Both implementations spent 99% of time waiting for HTTP responses
- Network timeouts, 403/404/503 errors dominated execution (Washington Post and NPR had timeouts)
- The 30-second timeout limit meant both implementations hit the same wall
- CPU parsing time became insignificant compared to network latency

**Key insight:** Language choice matters for CPU-bound work, becomes irrelevant for I/O-bound work.

### The Performance Convergence: Why Rust's Advantage Vanished

**Small dataset: CPU-bound (18x Rust advantage)**
- XML parsing dominated execution time
- Rust's compiled performance vs Python interpretation
- `quick-xml` efficiency vs `ElementTree` overhead

**Large dataset: I/O-bound (1.01x - no advantage)**
- Network requests dominated execution time  
- Both implementations spent identical time waiting for servers
- CPU parsing became <1% of total execution time
- Language performance became statistically irrelevant

### Debugging Process

Our collaborative investigation:

1. **AI suggestion:** Compare small vs large dataset performance patterns
2. **Human insight:** "The 18x advantage completely disappeared - why?"  
3. **Collaborative analysis:** Profiling execution time breakdown
4. **Discovery:** System bottlenecks matter more than language performance

### Performance Lessons Learned

**When Rust wins:**
- CPU-intensive parsing and computation
- Small datasets where processing overhead dominates
- Memory-constrained environments  
- When predictable performance characteristics are required

**When language choice becomes irrelevant:**
- I/O-bound workloads (network, file system, database)
- Large datasets where external latency dominates
- Real-world applications with network dependencies
- Systems limited by external service response times

**The fundamental lesson:** **Profile your actual bottlenecks before choosing languages.** The fastest XML parser in the world doesn't matter if you're spending 99% of your time waiting for HTTP responses.

## Profiling First: The Critical Methodology

### The Premature Optimization Trap

The classic mistake: assuming language choice determines performance. The reality check: profile first, optimize second, choose languages third.

What profiling revealed:

```
Execution time breakdown (large dataset):
- Network I/O: ~95%
- HTTP client overhead: ~3% 
- XML parsing: ~1.5%
- Language runtime: ~0.5%
```

When network I/O dominates this heavily, optimizing XML parsing is like polishing the brass on the Titanic.

### Systematic Performance Investigation

Our AI-assisted methodology:

1. **Establish baseline:** Identical algorithms and configurations
2. **Isolate variables:** Same concurrency, timeouts, error handling
3. **Scale testing:** Small vs large datasets to find bottlenecks
4. **Error analysis:** Success cases vs failure patterns
5. **Root cause analysis:** Network vs CPU vs memory constraints

Tools and techniques included:
- Time profiling with consistent measurement points
- HTTP request counting and error categorization  
- Memory usage patterns during large sitemap processing
- Build configuration impact (debug vs release)

### When to Choose Rust Over Python

**Rust makes sense when:**
- CPU-bound algorithms dominate execution time
- Memory efficiency is critical
- Predictable performance required
- Existing ecosystem support available (crates)
- Team comfortable with ownership/borrowing concepts

**Python remains optimal when:**
- I/O-bound operations dominate
- Rapid iteration and development speed matter
- Complex business logic changes frequently
- Rich ecosystem and library support needed
- Team productivity and maintainability prioritized

## AI Pair Programming Insights

### What AI Excelled At

**Systematic implementation:**
- Maintaining identical patterns across languages
- Catching subtle configuration differences
- Generating comprehensive test scenarios
- Consistent error handling and logging

**Debugging partnership:**
- Methodical hypothesis testing
- Systematic performance measurement
- Code organization and cleanup
- Documentation and explanation generation

### Where Human Guidance Was Essential

**Performance intuition:**
- Recognizing when results "felt wrong"
- Understanding system-level bottlenecks
- Questioning assumptions about language performance
- Connecting implementation details to real-world constraints

**Strategic direction:**
- Deciding when to stop optimizing and start analyzing
- Choosing meaningful test datasets
- Balancing thoroughness with practical constraints
- Focusing on lessons learned vs pure performance numbers

### Collaborative Development Patterns

**Effective workflows:**
- Human: High-level goals and constraints
- AI: Rapid implementation and systematic testing
- Human: Results interpretation and strategy adjustment
- AI: Detailed analysis and alternative approaches

**Communication patterns that worked:**

The most effective interactions followed a pattern: I would provide high-level direction and constraints, the AI would implement systematically, then I would interpret results and adjust strategy based on what we learned.

When performance results didn't make sense, the most productive approach was explicit questioning rather than assuming the AI would notice discrepancies. Asking "these performance results don't make sense - can you help me figure out why?" triggered systematic analysis that uncovered the I/O bottleneck.

The key was treating the AI as a methodical partner rather than an oracle. Iterative refinement worked better than expecting perfect solutions immediately. Building, testing, analyzing, and adjusting created a feedback loop that led to deeper insights than either pure human intuition or pure AI implementation would have achieved.

## Practical Takeaways

### For Performance Optimization

1. **Profile before choosing tools:** Language performance depends entirely on bottlenecks
2. **Scale your testing:** Small dataset performance often misleads
3. **Measure the right things:** Total time, request counts, error patterns
4. **Consider the whole system:** Network, CPU, memory, and error handling

### For Language Choice Decisions

1. **Rust shines for CPU-bound work:** Parsing, computation, data transformation
2. **Python remains excellent for I/O-bound work:** Network requests, file operations, API integration
3. **Hybrid approaches work well:** Rust for hot paths, Python for business logic
4. **Build system complexity matters:** Maturin + Poetry creates manageable Rust+Python projects

### For AI-Assisted Development

1. **AI excels at systematic implementation:** Use for consistency and thoroughness
2. **Human insight drives investigation:** Use for questioning results and strategic direction
3. **Collaborative debugging is powerful:** Combine AI's methodology with human intuition
4. **Document the process:** AI helps capture decisions and trade-offs

### For Real-World Projects

1. **Start with profiling, not assumptions**
2. **Test with realistic datasets and network conditions**
3. **Consider maintenance costs alongside performance**
4. **Choose languages based on bottlenecks, not benchmarks**

## Conclusion

The journey from 18x speedup to 1.01x revealed fundamental truths about performance optimization: language choice matters for CPU-bound work but becomes irrelevant for I/O-bound work. Real-world performance depends more on system constraints than parsing speed. Profiling prevents premature optimization and wrong technology choices.

The AI collaboration was surprisingly effective. AI excelled at systematic implementation and caught configuration subtleties I would have missed. Human insight was essential for performance intuition and strategic direction. Together, we discovered that the best performance optimization is often not changing languages, but understanding where time is actually spent.

**Profile first, then choose your tools.**

---

*Try the complete working example in the [{{ site.baseurl }}/code/2025-08-02-sitemap-parser-rust-python/]({{ site.baseurl }}/code/2025-08-02-sitemap-parser-rust-python/) directory. Run your own benchmarks and share your results - I'd love to hear what bottlenecks you discover in your own projects.*
