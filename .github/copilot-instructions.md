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

### Tone and Voice
- **Casual and clever**: Smart, witty, with energetic enthusiasm for solving technical problems
- **Conversational but technical**: Use "you" and first person, avoid overly formal academic tone
- **Problem-focused hooks**: Start with real pain points and frustrations developers actually face
- **Manic energy**: Show excitement about elegant solutions to annoying problems

### Content Structure and Flow
- **Problem → Practice → Theory**: Always start with practical examples, build to deeper technical concepts
- **Progressive complexity**: Begin punchy and accessible, get progressively more technical as the post develops
- **One complete example**: Build a single working project from setup to testing within each post
- **Real-world context**: Introduce concepts through actual scenarios and pain points developers encounter

### Code Integration
- **Show, don't just tell**: Include actual code snippets from the working examples throughout the narrative
- **Reference actual files**: Pull code directly from the `/code/` directory files being discussed
- **Incremental revelation**: Reveal code complexity gradually as the explanation deepens
- **Working examples**: Every code snippet should be from runnable, tested implementations

### Technical Approach
- **Assume basic competence**: Readers have fundamental knowledge of the tools/languages being used
- **Brief tool explanations**: Quick context on libraries/frameworks but don't over-explain basics
- **Focus on integration patterns**: Emphasize how different tools work together effectively
- **Learning-focused**: Code examples are for understanding, not production deployment

### Section Pacing
- **Intro sections**: Short, punchy, problem-statement focused (150-250 words)
- **Setup sections**: More detailed but still accessible (300-400 words)  
- **Implementation sections**: Full technical depth with detailed code walkthroughs (600-800 words)
- **Conclusion sections**: Lessons learned and practical takeaways (200-300 words)

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
