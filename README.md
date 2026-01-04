# Youtube Comment Search

A Python utility to download all comments from a given Youtube video and use the content of those comments as context for LLM-based search.

## Features

- Download all comments from any public YouTube video
- Store comments in a searchable format
- Use natural language queries to search through comments using LLM-powered semantic search
- Find specific discussions, opinions, or topics mentioned across thousands of comments

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/YT-Comment-Search.git
cd YT-Comment-Search

# Install dependencies
pip install -r requirements.txt
```

## Usage

### 1. Download Comments

First, download all comments from a YouTube video:

```bash
python yt_comment_search.py <VIDEO_URL>
```

Example:
```bash
python yt_comment_search.py download https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

## Configuration

You'll need to configure:

- **YouTube API Key**: Set your API key in `.env` file or as an environment variable

Create a `.env` file:
```
YOUTUBE_API_KEY=your_api_key_here
```

## Requirements

- Python 3.8+
- YouTube Data API v3 access

## License

MIT License