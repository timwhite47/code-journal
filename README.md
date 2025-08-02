# timwhite.ninja - Programming Blog

A Jekyll-based programming blog focused on AI coding, Python/Rust, Data Engineering, and Data Science.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   bundle install
   ```

2. **Serve locally:**
   ```bash
   bundle exec jekyll serve
   ```

3. **Visit:** http://localhost:4000

## 📝 Writing Posts

Create new posts in `_posts/` using the format:
```
YYYY-MM-DD-title-with-hyphens.md
```

### Front Matter Template
```yaml
---
layout: post
title: "Your Post Title"
date: YYYY-MM-DD HH:MM:SS -0000
categories: [ai-coding, data-engineering, python]
tags: [specific, tags, here]
excerpt: "Brief description for previews"
---
```

### Code Examples

Store complete code examples in `/code/YYYY-MM-DD-post-title/`:
- Include runnable implementations
- Add comprehensive tests
- Provide clear documentation
- Include requirements/dependencies

Reference code in posts:
```markdown
Check out the [complete implementation]({{ site.baseurl }}/code/2025-08-02-example/).
```

## 🏗️ Project Structure

```
timwhite_ninja/
├── _posts/                 # Blog posts
├── code/                   # Code examples per post
│   └── YYYY-MM-DD-title/   # Organized by post date
├── _config.yml             # Jekyll configuration
├── .github/
│   ├── workflows/          # GitHub Actions
│   └── copilot-instructions.md
├── Gemfile                 # Ruby dependencies
└── index.md               # Homepage
```

## 🔧 Development

### Local Development
```bash
# Install Jekyll and dependencies
bundle install

# Serve with live reload
bundle exec jekyll serve --livereload

# Build for production
bundle exec jekyll build
```

### Testing Code Examples
Each code directory includes its own dependencies and tests:
```bash
cd code/YYYY-MM-DD-example/
pip install -r requirements.txt
pytest test_*.py
```

## 🚀 Deployment

Automatically deployed to GitHub Pages via GitHub Actions when pushing to `main` branch.

### Custom Domain Setup
1. Add `CNAME` file with domain name
2. Configure DNS A records for GitHub Pages
3. Enable HTTPS in repository settings

## 📋 Content Categories

- **ai-coding** - AI-assisted development, vibe coding
- **data-engineering** - Pipelines, ETL, data infrastructure  
- **data-science** - Analytics, ML, data insights
- **python** - Python-specific content
- **rust** - Rust programming topics
- **mlops** - ML operations and infrastructure
- **cloud-data** - Cloud platforms and data services
- **performance** - Optimization and profiling

## 🛠️ Tech Stack

- **Jekyll** - Static site generator
- **GitHub Pages** - Hosting
- **Kramdown** - Markdown processor
- **Rouge** - Syntax highlighting
- **Minima** - Base theme (customized)

## 📄 License

Blog content and code examples are available under MIT License.
