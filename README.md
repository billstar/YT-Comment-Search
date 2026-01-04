# YouTube Comment Search

A Python command-line utility that downloads YouTube video comments and formats them for easy LLM consumption, search, and analysis.

## Features

- Download the top 1000 most relevant comments from any public YouTube video
- Store comments in structured markdown format
- Each comment includes a clickable link to view it on YouTube
- Include both top-level comments and their replies
- Perfect for analysis with Claude Code, Gemini CLI, or other LLM tools

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/YT-Comment-Search.git
cd YT-Comment-Search

# Install dependencies
pip install -r requirements.txt
```

## Setup

### 1. Get a YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Create credentials (API Key)
5. Copy your API key

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```
YOUTUBE_API_KEY=your_api_key_here
```

## Usage

### Basic Usage

Download comments from a YouTube video:

```bash
python yt_comment_search.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

The script accepts various YouTube URL formats:
```bash
# Standard URL
python yt_comment_search.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Short URL
python yt_comment_search.py "https://youtu.be/dQw4w9WgXcQ"

# URL with timestamp
python yt_comment_search.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=123s"
```

### Options

```bash
# Force re-fetch comments (overwrites existing data)
python yt_comment_search.py "VIDEO_URL" --force

# Specify maximum number of comments (default: 1000)
python yt_comment_search.py "VIDEO_URL" --max-comments 500

# Specify base directory for storing comments (default: /tmp)
python yt_comment_search.py "VIDEO_URL" --dir ~/Documents

# Combine multiple options
python yt_comment_search.py "VIDEO_URL" --dir . --max-comments 500 --force
```

## Output Structure

Comments are saved in the following directory structure (default location: `/tmp/youtube_comments/`):

```
/tmp/youtube_comments/
├── VIDEO_ID_1-canonical-video-title/
│   ├── metadata.md      # Video title, URL, stats
│   ├── comments.md      # All comments with links
│   ├── CLAUDE.md        # LLM search instructions for Claude
│   ├── GEMINI.md        # LLM search instructions for Gemini
│   └── AGENTS.md        # LLM search instructions for other agents
├── VIDEO_ID_2-another-video-title/
│   ├── metadata.md
│   ├── comments.md
│   ├── CLAUDE.md
│   ├── GEMINI.md
│   └── AGENTS.md
```

Directory names use the format `{VIDEO_ID}-{canonical-title}` where the canonical title is lowercase with all non-alphanumeric characters replaced by dashes. For example, "Rick Astley - Never Gonna Give You Up (Official Video)" becomes `dQw4w9WgXcQ-rick-astley-never-gonna-give-you-up-official-video`.

Each directory includes LLM instruction files that configure AI assistants to search through comments using a consistent, structured format.

You can change the base directory using the `--dir` option. For example, `--dir .` will create `./youtube_comments/` in your current directory.

### Example metadata.md
```markdown
# Video Metadata

**Title:** Amazing Video Title
**Video URL:** https://www.youtube.com/watch?v=VIDEO_ID
**Total Comments Fetched:** 1000
**Fetch Date:** 2026-01-03 14:30:22
**Video ID:** VIDEO_ID
```

### Example comments.md
```markdown
## Comment ID: UgxKREWJwBPtN8lgH6Z4AaABAg

**Author:** John Doe
**Posted:** 2 weeks ago
**Likes:** 42
**Link:** https://www.youtube.com/watch?v=VIDEO_ID&lc=UgxKREWJwBPtN8lgH6Z4AaABAg

This is the comment text...

---
```

## Using with LLMs

After downloading comments, navigate to the video directory and use your preferred LLM tool. The directory includes instruction files (CLAUDE.md, GEMINI.md, AGENTS.md) that configure AI assistants to search comments with a consistent format.

```bash
cd /tmp/youtube_comments/VIDEO_ID-canonical-title

# Use Claude Code (automatically reads CLAUDE.md)
claude "What are the main topics discussed in these comments?"
claude "Find all comments asking questions about the tutorial"
claude "Summarize the sentiment of these comments"

# Use Gemini CLI (automatically reads GEMINI.md if supported)
gemini "people who disagree with the main points"

# Or copy the content to use with any LLM
```

If you used a custom directory with `--dir`, navigate to that location instead (e.g., `cd ./youtube_comments/VIDEO_ID-title` if you used `--dir .`).

### LLM Search Instructions

Each video directory includes three instruction files:
- **CLAUDE.md** - For Claude Code and Claude-based tools
- **GEMINI.md** - For Gemini CLI and Gemini-based tools
- **AGENTS.md** - For GitHub Copilot, Cursor, and other AI assistants

These files configure the LLM to return search results in a structured format with:
- Complete comment text (never summarized)
- All metadata (author, timestamp, likes, clickable YouTube link)
- Relevance-sorted results
- Summary with key themes

The clickable comment links make it easy to view specific comments in their original context on YouTube.

## Requirements

- Python 3.8+
- YouTube Data API v3 access
- Dependencies listed in [requirements.txt](requirements.txt)

## License

MIT License