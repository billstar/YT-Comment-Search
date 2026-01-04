# YouTube Comment Search - Project Specification

## Project Overview
A Python command-line utility that downloads YouTube video comments and formats them for easy LLM consumption, search and analysis.

**Note:** When the utility downloads comments, it automatically copies LLM search instruction templates (CLAUDE.md, GEMINI.md, AGENTS.md) into each video directory. These files help configure AI assistants to search through comments with consistent formatting.

## Core Functionality

### Command Line Interface
```bash
python yt_comment_search.py "https://www.youtube.com/watch?v=VIDEO_ID"
```
- Single argument: YouTube URL (any valid format)
- Should work with various URL formats:
  - `https://www.youtube.com/watch?v=VIDEO_ID`
  - `https://youtu.be/VIDEO_ID`
  - `https://www.youtube.com/watch?v=VIDEO_ID&t=123s`

### Comment Retrieval
- Fetch the **top 1000 most relevant comments** using YouTube Data API v3
- Use the `commentThreads.list` endpoint with `order=relevance`
- Handle pagination automatically (max 100 comments per API call = 10 requests)
- Include both top-level comments and their replies

### Data Storage Structure

#### Directory Organization
```
/tmp/youtube_comments/
├── VIDEO_ID_1-canonical-title/
│   ├── metadata.md
│   ├── comments.md
│   ├── CLAUDE.md
│   ├── GEMINI.md
│   └── AGENTS.md
├── VIDEO_ID_2-another-title/
│   ├── metadata.md
│   ├── comments.md
│   ├── CLAUDE.md
│   ├── GEMINI.md
│   └── AGENTS.md
```

- Parent directory: `youtube_comments/` (default: `/tmp`, configurable with `--dir`)
- Sub-directory per video: Named as `{VIDEO_ID}-{canonical-title}` where canonical title is lowercase with non-alphanumeric characters replaced by dashes
- Files per video:
  - `metadata.md`: Video title, URL, comment count, fetch timestamp
  - `comments.md`: All comments in structured markdown format
  - `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`: LLM search instruction templates

#### Comment Format (comments.md)
Each comment should be formatted as:

```markdown
## Comment ID: COMMENT_ID_HERE

**Author:** Channel Name  
**Posted:** 2 weeks ago  
**Likes:** 42  
**Link:** https://www.youtube.com/watch?v=VIDEO_ID&lc=COMMENT_ID

Comment text goes here...

---
```

#### Metadata Format (metadata.md)
```markdown
# Video Metadata

**Title:** Video Title Here  
**Video URL:** https://www.youtube.com/watch?v=VIDEO_ID  
**Total Comments Fetched:** 1000  
**Fetch Date:** 2026-01-03 14:30:22  
**Video ID:** VIDEO_ID
```

### Comment ID Requirements
- Each comment must include its unique comment ID
- Format the clickable link as: `https://www.youtube.com/watch?v=VIDEO_ID&lc=COMMENT_ID`
- This `lc` parameter highlights the specific comment when clicked
- The comment ID should be extracted from the API response field: `comment['id']`

## Technical Requirements

### Dependencies
- Python 3.8+
- `google-api-python-client` for YouTube Data API v3
- `python-dotenv` for API key management
- Standard library: `os`, `json`, `argparse`, `datetime`, `urllib.parse`

### API Authentication
- Use YouTube Data API v3
- API key stored in `.env` file (never commit to git)
- `.env` format:
  ```
  YOUTUBE_API_KEY=your_api_key_here
  ```

### Error Handling
- Gracefully handle invalid URLs
- Handle API quota exceeded errors
- Handle videos with comments disabled
- Handle network errors
- Provide clear error messages to the user

### Best Practices
- Extract video ID from various URL formats
- Create directories if they don't exist
- Don't re-fetch if directory already exists (add `--force` flag to override)
- Display progress indicator during API calls
- Log summary after completion (e.g., "Fetched 1000 comments to ./youtube_comments/VIDEO_ID/")

## Use Case
After running the tool, users can:
1. Navigate to the video's comment directory
2. Use Claude Code, Gemini CLI, or other LLM CLI tools to analyze comments
3. Ask questions like:
   - "What are the main topics discussed in these comments?"
   - "Summarize the sentiment of these comments"
   - "Find all comments asking questions about X"
   - "Which comments mention [specific topic]?"
4. Click generated URLs to view specific comments in context on YouTube

## File Structure
```
project_root/
├── .env                    # API key (git-ignored)
├── .gitignore             # Ignore .env, youtube_comments/, etc.
├── yt_comment_search.py    # Main script
├── requirements.txt       # Python dependencies
├── CLAUDE.md             # This file
└── README.md             # User documentation
```

## Future Enhancements (Optional)
- Add flag to specify number of comments (default 1000)
- Add flag to sort by different criteria (top, newest)
- Export to JSON format option
- Include comment replies in nested format
- Add caching to avoid re-fetching
- Support for comment threads (replies to replies)