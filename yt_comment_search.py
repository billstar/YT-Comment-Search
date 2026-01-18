#!/usr/bin/env python3
"""
YouTube Comment Search - Download and format YouTube comments for LLM analysis
"""

import os
import sys
import argparse
import re
import shutil
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    TRANSCRIPT_AVAILABLE = True
except ImportError:
    TRANSCRIPT_AVAILABLE = False


def extract_video_id(url):
    """Extract video ID from various YouTube URL formats."""
    # Handle youtu.be short URLs
    if 'youtu.be' in url:
        path = urlparse(url).path
        return path.strip('/')

    # Handle youtube.com URLs
    parsed = urlparse(url)
    if 'youtube.com' in parsed.netloc:
        # Try to get from query parameters
        query_params = parse_qs(parsed.query)
        if 'v' in query_params:
            return query_params['v'][0]

    # If it's just the video ID itself
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url

    return None


def canonicalize_title(title):
    """Convert video title to canonical directory name format.

    Example: "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)"
    becomes: "rick-astley-never-gonna-give-you-up-official-video-4k-remaster"
    """
    # Convert to lowercase
    canonical = title.lower()

    # Replace all non-alphanumeric characters with dashes
    canonical = re.sub(r'[^a-z0-9]+', '-', canonical)

    # Remove leading/trailing dashes
    canonical = canonical.strip('-')

    return canonical


def copy_llm_instructions(video_dir):
    """Copy LLM search instruction template to the video directory."""
    # Get the script's directory
    script_dir = Path(__file__).parent
    template_path = script_dir / 'LLM-search-instructions-template.md'

    # Check if template exists
    if not template_path.exists():
        print(f"Warning: LLM instruction template not found at {template_path}")
        return

    # Read template content
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Copy to three different files
        for filename in ['CLAUDE.md', 'GEMINI.md', 'AGENTS.md']:
            target_path = video_dir / filename
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)

    except Exception as e:
        print(f"Warning: Could not copy LLM instruction files: {e}")


def create_directory_structure(video_id, base_path='/tmp'):
    """Create the directory structure for storing comments."""
    base_dir = Path(base_path) / 'youtube_comments'
    video_dir = base_dir / video_id

    base_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(exist_ok=True)

    # Copy LLM instruction files to the directory
    copy_llm_instructions(video_dir)

    return video_dir


def fetch_video_metadata(youtube, video_id):
    """Fetch video title and basic metadata."""
    try:
        request = youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        )
        response = request.execute()

        if not response['items']:
            return None

        video = response['items'][0]
        return {
            'title': video['snippet']['title'],
            'comment_count': video['statistics'].get('commentCount', 'N/A')
        }
    except HttpError as e:
        print(f"Error fetching video metadata: {e}")
        return None


def fetch_comments(youtube, video_id, max_comments=1000):
    """Fetch top comments from a YouTube video."""
    comments = []
    next_page_token = None

    print(f"Fetching comments for video {video_id}...")

    while len(comments) < max_comments:
        try:
            request = youtube.commentThreads().list(
                part='snippet,replies',
                videoId=video_id,
                maxResults=min(100, max_comments - len(comments)),
                order='relevance',
                pageToken=next_page_token,
                textFormat='plainText'
            )
            response = request.execute()

            for item in response['items']:
                # Top-level comment
                top_comment = item['snippet']['topLevelComment']
                comment_data = {
                    'id': top_comment['id'],
                    'author': top_comment['snippet']['authorDisplayName'],
                    'text': top_comment['snippet']['textDisplay'],
                    'likes': top_comment['snippet']['likeCount'],
                    'published': top_comment['snippet']['publishedAt'],
                    'updated': top_comment['snippet']['updatedAt']
                }
                comments.append(comment_data)

                # Add replies if they exist
                if 'replies' in item:
                    for reply in item['replies']['comments']:
                        reply_data = {
                            'id': reply['id'],
                            'author': reply['snippet']['authorDisplayName'],
                            'text': reply['snippet']['textDisplay'],
                            'likes': reply['snippet']['likeCount'],
                            'published': reply['snippet']['publishedAt'],
                            'updated': reply['snippet']['updatedAt'],
                            'is_reply': True
                        }
                        comments.append(reply_data)

            next_page_token = response.get('nextPageToken')
            print(f"Fetched {len(comments)} comments so far...")

            if not next_page_token:
                break

        except HttpError as e:
            if 'commentsDisabled' in str(e):
                print("Error: Comments are disabled for this video.")
                return None
            elif 'quotaExceeded' in str(e):
                print("Error: API quota exceeded. Please try again later.")
                return None
            else:
                print(f"Error fetching comments: {e}")
                return None

    return comments


def format_relative_time(timestamp):
    """Convert ISO timestamp to relative time (approximate)."""
    try:
        published = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now(published.tzinfo)
        delta = now - published

        if delta.days > 365:
            years = delta.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
        elif delta.days > 30:
            months = delta.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif delta.days > 0:
            if delta.days == 1:
                return "1 day ago"
            elif delta.days < 7:
                return f"{delta.days} days ago"
            else:
                weeks = delta.days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "just now"
    except:
        return "unknown"


def save_metadata(video_dir, video_id, metadata, comment_count, url):
    """Save video metadata to metadata.md."""
    metadata_path = video_dir / 'metadata.md'

    with open(metadata_path, 'w', encoding='utf-8') as f:
        f.write("# Video Metadata\n\n")
        f.write(f"**Title:** {metadata['title']}\n")
        f.write(f"**Video URL:** {url}\n")
        f.write(f"**Total Comments Fetched:** {comment_count}\n")
        f.write(f"**Fetch Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Video ID:** {video_id}\n")


def save_comments(video_dir, video_id, comments):
    """Save comments to comments.md."""
    comments_path = video_dir / 'comments.md'

    with open(comments_path, 'w', encoding='utf-8') as f:
        for comment in comments:
            f.write(f"## Comment ID: {comment['id']}\n\n")
            f.write(f"**Author:** {comment['author']}\n")
            f.write(f"**Posted:** {format_relative_time(comment['published'])}\n")
            f.write(f"**Likes:** {comment['likes']}\n")
            f.write(f"**Link:** https://www.youtube.com/watch?v={video_id}&lc={comment['id']}\n\n")
            f.write(f"{comment['text']}\n\n")
            f.write("---\n\n")


def format_timestamp(seconds):
    """Convert seconds to [M:SS] or [H:MM:SS] format."""
    seconds = int(seconds)
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"[{hours}:{minutes:02d}:{secs:02d}]"
    else:
        minutes = seconds // 60
        secs = seconds % 60
        return f"[{minutes}:{secs:02d}]"


def fetch_transcript(video_id):
    """Fetch transcript for a YouTube video."""
    if not TRANSCRIPT_AVAILABLE:
        return None, "youtube-transcript-api not installed"

    try:
        # Use the new instance-based API
        ytt_api = YouTubeTranscriptApi()
        transcript_entries = ytt_api.fetch(video_id)

        # Determine language from the transcript entries if available
        language = 'en'

        return {
            'entries': transcript_entries,
            'language': language
        }, None

    except Exception as e:
        error_str = str(e).lower()
        if 'disabled' in error_str:
            return None, "Transcripts are disabled for this video"
        elif 'no transcript' in error_str or 'not found' in error_str:
            return None, "No transcript found for this video"
        else:
            return None, f"Error fetching transcript: {e}"


def save_transcript(video_dir, video_id, metadata, transcript_data, url):
    """Save transcript to transcript.md."""
    transcript_path = video_dir / 'transcript.md'

    with open(transcript_path, 'w', encoding='utf-8') as f:
        f.write("# Video Transcript\n\n")
        f.write(f"**Video Title:** {metadata['title']}\n")
        f.write(f"**Video URL:** {url}\n")
        f.write(f"**Language:** {transcript_data['language']}\n\n")
        f.write("---\n\n")

        for entry in transcript_data['entries']:
            timestamp = format_timestamp(entry.start)
            text = entry.text.replace('\n', ' ')
            f.write(f"{timestamp} {text}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Download YouTube video comments for LLM analysis'
    )
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-fetch even if comments already exist'
    )
    parser.add_argument(
        '--max-comments',
        type=int,
        default=1000,
        help='Maximum number of comments to fetch (default: 1000)'
    )
    parser.add_argument(
        '--dir',
        type=str,
        default='/tmp',
        help='Base directory for storing comments (default: /tmp)'
    )
    parser.add_argument(
        '--transcript',
        action='store_true',
        help='Download video transcript (requires youtube-transcript-api)'
    )

    args = parser.parse_args()

    # Check if transcript requested but library not available
    if args.transcript and not TRANSCRIPT_AVAILABLE:
        print("Error: --transcript flag requires youtube-transcript-api")
        print("Install it with: pip install youtube-transcript-api")
        sys.exit(1)

    # Load API key from .env
    load_dotenv()
    api_key = os.getenv('YOUTUBE_API_KEY')

    if not api_key:
        print("Error: YOUTUBE_API_KEY not found in .env file")
        print("Please create a .env file with your YouTube API key:")
        print("  YOUTUBE_API_KEY=your_api_key_here")
        sys.exit(1)

    # Extract video ID
    video_id = extract_video_id(args.url)
    if not video_id:
        print(f"Error: Could not extract video ID from URL: {args.url}")
        sys.exit(1)

    print(f"Video ID: {video_id}")

    # Create directory structure
    video_dir = create_directory_structure(video_id, args.dir)

    # Check if already fetched
    if not args.force and (video_dir / 'comments.md').exists():
        print(f"Comments already exist in {video_dir}")
        print("Use --force flag to re-fetch")
        sys.exit(0)

    # Build YouTube API client
    youtube = build('youtube', 'v3', developerKey=api_key)

    # Fetch video metadata
    metadata = fetch_video_metadata(youtube, video_id)
    if not metadata:
        print("Error: Could not fetch video metadata. Check if video ID is valid.")
        sys.exit(1)

    print(f"Video: {metadata['title']}")

    # Rename directory to include canonicalized title
    canonical_title = canonicalize_title(metadata['title'])
    new_dir_name = f"{video_id}-{canonical_title}"
    base_dir = Path(args.dir) / 'youtube_comments'
    new_video_dir = base_dir / new_dir_name

    # Rename the directory if it doesn't already exist with the new name
    if video_dir != new_video_dir:
        if new_video_dir.exists():
            if not args.force:
                print(f"Comments already exist in {new_video_dir}")
                print("Use --force flag to re-fetch")
                sys.exit(0)
            else:
                # If force is true, remove the existing directory before renaming
                if new_video_dir.is_dir():
                    shutil.rmtree(new_video_dir)
                else:
                    new_video_dir.unlink()
        video_dir.rename(new_video_dir)
        video_dir = new_video_dir

    # Fetch comments
    comments = fetch_comments(youtube, video_id, args.max_comments)
    if comments is None:
        sys.exit(1)

    if not comments:
        print("No comments found for this video.")
        sys.exit(0)

    # Save metadata and comments
    save_metadata(video_dir, video_id, metadata, len(comments), args.url)
    save_comments(video_dir, video_id, comments)

    # Fetch and save transcript if requested
    transcript_saved = False
    if args.transcript:
        print("Fetching transcript...")
        transcript_data, error = fetch_transcript(video_id)
        if transcript_data:
            save_transcript(video_dir, video_id, metadata, transcript_data, args.url)
            transcript_saved = True
            print(f"Transcript saved ({transcript_data['language']})")
        else:
            print(f"Warning: {error}")

    print(f"\nSuccess! Fetched {len(comments)} comments to {video_dir}/")
    print(f"Files created:")
    print(f"  - {video_dir / 'metadata.md'}")
    print(f"  - {video_dir / 'comments.md'}")
    if transcript_saved:
        print(f"  - {video_dir / 'transcript.md'}")
    print(f"  - {video_dir / 'CLAUDE.md'}")
    print(f"  - {video_dir / 'GEMINI.md'}")
    print(f"  - {video_dir / 'AGENTS.md'}")


if __name__ == '__main__':
    main()
