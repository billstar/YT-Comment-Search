#!/usr/bin/env python3
"""
YouTube Comment Search - Download and format YouTube comments for LLM analysis
"""

import os
import sys
import argparse
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


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


def create_directory_structure(video_id, base_path='/tmp'):
    """Create the directory structure for storing comments."""
    base_dir = Path(base_path) / 'youtube_comments'
    video_dir = base_dir / video_id

    base_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(exist_ok=True)

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

    args = parser.parse_args()

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
        if new_video_dir.exists() and not args.force:
            print(f"Comments already exist in {new_video_dir}")
            print("Use --force flag to re-fetch")
            sys.exit(0)
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

    print(f"\nSuccess! Fetched {len(comments)} comments to {video_dir}/")
    print(f"Files created:")
    print(f"  - {video_dir / 'metadata.md'}")
    print(f"  - {video_dir / 'comments.md'}")


if __name__ == '__main__':
    main()
