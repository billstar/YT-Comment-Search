# Installation Guide for macOS

This guide explains how to install the YouTube Comment Search utility in a canonical per-user location on macOS.

## Installation Options

### Option 1: Install to `~/.local/bin` (Recommended)

This follows the XDG Base Directory specification and is the modern standard for user-installed executables.

#### 1. Create the installation directory

```bash
mkdir -p ~/.local/bin
```

#### 2. Ensure `~/.local/bin` is in your PATH

Add this to your shell configuration file (`~/.zshrc` for zsh or `~/.bash_profile` for bash):

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then reload your shell configuration:

```bash
# For zsh (default on macOS)
source ~/.zshrc

# For bash
source ~/.bash_profile
```

#### 3. Clone the repository to a permanent location

```bash
mkdir -p ~/.local/share
cd ~/.local/share
git clone https://github.com/yourusername/YT-Comment-Search.git
cd YT-Comment-Search
```

#### 4. Install Python dependencies

```bash
pip3 install -r requirements.txt
```

Alternatively, use a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 5. Create a wrapper script

Create a wrapper script at `~/.local/bin/yt-comment-search`:

```bash
cat > ~/.local/bin/yt-comment-search << 'EOF'
#!/bin/bash

# Path to the installation directory
INSTALL_DIR="$HOME/.local/share/YT-Comment-Search"

# Activate virtual environment if it exists
if [ -d "$INSTALL_DIR/venv" ]; then
    source "$INSTALL_DIR/venv/bin/activate"
fi

# Run the script with all arguments passed through
python3 "$INSTALL_DIR/yt_comment_search.py" "$@"
EOF
```

#### 6. Make the wrapper script executable

```bash
chmod +x ~/.local/bin/yt-comment-search
```

#### 7. Configure your API key

```bash
cd ~/.local/share/YT-Comment-Search
cp .env.example .env
```

Edit `~/.local/share/YT-Comment-Search/.env` and add your YouTube API key:

```bash
nano ~/.local/share/YT-Comment-Search/.env
```

#### 8. Test the installation

```bash
yt-comment-search "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

---

### Option 2: Install to `/usr/local/bin` (System-wide)

This is the traditional location for user-installed system-wide executables.

#### 1. Clone the repository

```bash
sudo mkdir -p /usr/local/share
cd /usr/local/share
sudo git clone https://github.com/yourusername/YT-Comment-Search.git
cd YT-Comment-Search
```

#### 2. Install dependencies system-wide

```bash
sudo pip3 install -r requirements.txt
```

#### 3. Create a symlink or wrapper script

```bash
sudo ln -s /usr/local/share/YT-Comment-Search/yt_comment_search.py /usr/local/bin/yt-comment-search
```

Or create a wrapper script:

```bash
sudo cat > /usr/local/bin/yt-comment-search << 'EOF'
#!/bin/bash
python3 /usr/local/share/YT-Comment-Search/yt_comment_search.py "$@"
EOF

sudo chmod +x /usr/local/bin/yt-comment-search
```

#### 4. Configure your API key

```bash
cd /usr/local/share/YT-Comment-Search
sudo cp .env.example .env
sudo nano .env
```

**Note:** With this approach, all users will share the same API key and quota.

---

### Option 3: Install via Homebrew (Future)

In the future, this utility could be packaged as a Homebrew formula for easier installation:

```bash
# Future installation method
brew tap yourusername/tap
brew install yt-comment-search
```

---

## Getting a YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **YouTube Data API v3**:
   - Go to "APIs & Services" > "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy your API key
5. (Optional but recommended) Restrict the API key:
   - Click on your API key to edit it
   - Under "API restrictions", select "Restrict key"
   - Choose "YouTube Data API v3"
   - Save

## Verifying Installation

After installation, verify it works:

```bash
# Check the command is available
which yt-comment-search

# Test with a video (this will create youtube_comments/ in your current directory)
yt-comment-search "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Check available options
yt-comment-search --help
```

## Uninstallation

### For Option 1 (~/.local/bin):

```bash
rm ~/.local/bin/yt-comment-search
rm -rf ~/.local/share/YT-Comment-Search
```

### For Option 2 (/usr/local/bin):

```bash
sudo rm /usr/local/bin/yt-comment-search
sudo rm -rf /usr/local/share/YT-Comment-Search
```

## Troubleshooting

### Command not found

Ensure `~/.local/bin` is in your PATH:

```bash
echo $PATH | grep -q "$HOME/.local/bin" && echo "✓ In PATH" || echo "✗ Not in PATH"
```

### Python module not found

Ensure dependencies are installed:

```bash
pip3 list | grep google-api-python-client
pip3 list | grep python-dotenv
pip3 list | grep youtube-transcript-api
```

Or activate the virtual environment if you used one:

```bash
source ~/.local/share/YT-Comment-Search/venv/bin/activate
```

### API quota exceeded

The YouTube Data API has a default quota of 10,000 units per day. Each comment fetch uses approximately 1 unit per request (10 requests for 1000 comments = 10 units). If you exceed the quota, wait until the next day or request a quota increase in Google Cloud Console.

### Transcript not available

If you use the `--transcript` flag and see a warning that the transcript is unavailable, this could mean:
- The video doesn't have captions/subtitles
- The video owner has disabled transcript access
- The video is too new and transcripts haven't been generated yet

The `--transcript` flag is optional; comments will still be downloaded even if the transcript fails.

### Permission denied

Ensure the wrapper script is executable:

```bash
chmod +x ~/.local/bin/yt-comment-search
```

## Updating

### For Option 1:

```bash
cd ~/.local/share/YT-Comment-Search
git pull
pip3 install -r requirements.txt --upgrade
```

### For Option 2:

```bash
cd /usr/local/share/YT-Comment-Search
sudo git pull
sudo pip3 install -r requirements.txt --upgrade
```
