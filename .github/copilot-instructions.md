<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# GitHub Copilot Instructions for timwhite.ninja Blog

This is a Jekyll-based programming blog focused on AI coding, Python/Rust, Data Engineering, and Data Science.

## Project Structure

- `_posts/` - Blog posts in markdown format with Jekyll front matter
- `code/` - Complete code examples organized by blog post date
- `_config.yml` - Jekyll configuration
- `.github/workflows/` - GitHub Actions for automated deployment

## Blog Post Guidelines

When creating new blog posts:

1. **File naming**: Use format `YYYY-MM-DD-title-with-hyphens.md`
2. **Front matter**: Include layout, title, date, categories, tags, and excerpt
3. **Code examples**: Reference code in `/code/YYYY-MM-DD-post-title/` directory
4. **Categories**: Use [ai-coding, data-engineering, data-science, python, rust, mlops, cloud-data, performance]
5. **Links**: Use `{{ site.baseurl }}/code/folder-name/` for code references

## Code Example Structure

For each blog post with code:

1. Create directory: `/code/YYYY-MM-DD-post-title/`
2. Include: main implementation, tests, README, requirements/dependencies
    * For python, use **only** poetry for dependencies
    * For Rust, use `Cargo.toml` and cargo commands
3. Make code runnable and well-documented
4. Add type hints and docstrings for Python code
5. Include error handling and logging

## Writing Style

- Technical but accessible
- Include practical examples
- Focus on AI-assisted development workflows
- Emphasize real-world applications
- Include performance considerations

## Jekyll Specific

- Use Jekyll liquid tags for dynamic content
- Leverage kramdown markdown features
- Include syntax highlighting with language specifiers
- Use excerpts for post previews

## Development Workflow

- User gives description of blog post they want to make, with technical goals.
- AI helps user create working code in `/code/` directory (this will be an interactive process in concert with the user)
- AI creates an outline of a proposed blog post in `outlines/` directory based on the user's description and the code generated.
- User gives feedback to and modifies the outline.
- Only when User gives **explicit permission** write the blog post.

## Technical Requirements

- Test locally with `bundle exec jekyll serve`
- Code examples should be self-contained and runnable
- Include requirements.txt or Cargo.toml for dependencies
- Write tests for code examples when applicable
