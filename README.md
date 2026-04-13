# Excel Video Downloader

A Python-based batch video downloader that reads URLs from an Excel spreadsheet and downloads them using [yt-dlp](https://github.com/yt-dlp/yt-dlp). Supports multiple output formats (MP4, MP3, or both) with automatic filename sanitization for Windows.

## Features

- 📊 **Excel-based batch processing** - Manage download lists in spreadsheets
- 🎥 **Multiple output formats** - MP4 video, MP3 audio, or both simultaneously
- 🔐 **Cookie authentication** - Access member-only or high-quality content
- 🌐 **Browser impersonation** - Bypass 403 errors with TLS fingerprinting
- 🚀 **Automation-ready** - Non-interactive mode for scheduled tasks
- 🪟 **Windows-optimized** - Automatic filename sanitization
- 🎯 **Site-specific handling** - Special support for sites like noodlemagazine.com

## Prerequisites

Before you begin, ensure you have:

1. **Python 3.10 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify: `python --version`

2. **ffmpeg** (Required for audio extraction and stream merging)
   - Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Add to your system `PATH`
   - Verify: `ffmpeg -version`
   - **Why needed:**
     - Merging separate video + audio streams for best quality MP4
     - Extracting MP3 audio from video files
     - Required for "Both" mode (MP4 + MP3)

## Installation

1. **Clone or download this repository**
   ```powershell
   git clone https://github.com/yourusername/video-downloader.git
   cd video-downloader
   ```

2. **Install Python dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Prepare your Excel file**
   - Create or use `List.xlsx` with two columns:
     - **Name** - The desired filename (will be sanitized automatically)
     - **URL** - The video URL to download
   - Column names are case-insensitive
   
   Example format:
   ```
   | Name              | URL                                    |
   |-------------------|----------------------------------------|
   | Tutorial Part 1   | https://example.com/video1             |
   | Conference Talk   | https://youtube.com/watch?v=abc123     |
   ```

## Quick Start

```powershell
# Basic usage with default settings
python download_videos.py

# Specify a different Excel file
python download_videos.py "D:\MyLists\videos.xlsx"

# Download to a specific folder
python download_videos.py -o "D:\Downloads\Videos"
```

## Usage

### Interactive Mode

When you run the script without mode flags, an interactive menu appears:

```powershell
python download_videos.py
```

**Menu Options:**

| Choice | Mode       | Output Description                                              |
|--------|------------|-----------------------------------------------------------------|
| **1**  | MP4 video  | Downloads video in MP4 format (merges streams if needed)        |
| **2**  | MP3 audio  | Extracts audio only in MP3 format                               |
| **3**  | Both       | Downloads both MP4 video and MP3 audio with the same base name  |

### Non-Interactive Mode

For automation, scheduled tasks, or scripts:

```powershell
# Download as MP4 (default)
python download_videos.py --mode mp4

# Download as MP3 audio only
python download_videos.py --mode mp3

# Download both MP4 and MP3
python download_videos.py --mode both
```

### Command-Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `[excel_file]` | Path to Excel file (default: `List.xlsx`) | `python download_videos.py "D:\lists\videos.xlsx"` |
| `--mode {mp4\|mp3\|both}` | Download mode (skips interactive menu) | `--mode mp3` |
| `-o, --output FOLDER` | Output directory (default: `downloads`) | `-o "D:\Videos"` |
| `--dry-run` | Preview downloads without downloading | `--dry-run` |
| `--cookies FILE` | Path to cookies file (JSON/Netscape) | `--cookies cookies.json` |
| `--cookies-from-browser BROWSER` | Extract cookies from browser | `--cookies-from-browser chrome` |
| `--impersonate [BROWSER]` | Browser TLS impersonation | `--impersonate chrome` |

**Complete Example:**
```powershell
python download_videos.py "D:\Lists\mylist.xlsx" -o "D:\Media" --mode mp4 --cookies-from-browser edge
```

## Authentication

Many sites restrict high-quality content to logged-in users. Use cookies to authenticate and access premium content.

### Method 1: Browser Cookie Extraction (Recommended)

Extract cookies directly from your browser:

```powershell
# Chrome
python download_videos.py --cookies-from-browser chrome

# Microsoft Edge
python download_videos.py --cookies-from-browser edge

# Firefox
python download_videos.py --cookies-from-browser firefox

# Safari (macOS)
python download_videos.py --cookies-from-browser safari
```

**⚠️ Important:** Close the browser completely before running the command, otherwise cookies may be locked.

### Method 2: Manual Cookie Export

1. **Log into the website** in your browser
2. **Install a cookie export extension:**
   - Chrome/Edge: [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/)
   - Firefox: [Cookie Quick Manager](https://addons.mozilla.org/en-US/firefox/addon/cookie-quick-manager/)
3. **Export cookies** to a JSON or Netscape format file
4. **Use the cookies file:**
   ```powershell
   python download_videos.py --cookies "C:\path\to\cookies.json"
   ```

### Advanced: Combine Authentication with Impersonation

For maximum compatibility with restricted sites:

```powershell
python download_videos.py --cookies-from-browser chrome --impersonate chrome
```

This combination:
- ✅ Provides authentication via cookies
- ✅ Mimics browser TLS fingerprint
- ✅ Bypasses most anti-bot protections

## Troubleshooting

### 403 Forbidden Errors

**Problem:** Site returns 403 error (access denied)

**Solutions:**
1. Use browser impersonation:
   ```powershell
   python download_videos.py --impersonate chrome
   ```
2. Add authentication:
   ```powershell
   python download_videos.py --cookies-from-browser chrome --impersonate chrome
   ```
3. For **noodlemagazine.com**: Chrome impersonation is automatic, but try adding cookies if it still fails

### Missing ffmpeg

**Problem:** Error about ffmpeg not found

**Solution:**
1. Download ffmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Add to system PATH
3. Restart terminal and verify: `ffmpeg -version`

### Locked Cookie Files

**Problem:** "Could not load cookies" error

**Solution:** Close all browser windows completely before running with `--cookies-from-browser`

### Excel File Not Found

**Problem:** "File not found" error

**Solution:**
- Ensure `List.xlsx` exists in the current directory, or
- Specify the full path: `python download_videos.py "C:\path\to\file.xlsx"`

## Site-Specific Notes

### Noodlemagazine.com
- Automatic Chrome impersonation enabled
- Uses `curl_cffi` for TLS fingerprinting
- If downloads fail, add: `--cookies-from-browser chrome`

### YouTube
- Works without authentication for public videos
- For age-restricted content, use `--cookies-from-browser`
- Supports playlists and channels

## Project Structure

```
video-downloader/
├── download_videos.py    # Main script
├── requirements.txt      # Python dependencies
├── List.xlsx            # Example Excel template
├── README.md            # This file
├── .gitignore           # Git ignore rules
└── downloads/           # Default output directory (created automatically)
```

## Dependencies

- **pandas** (≥2.0) - Excel file processing
- **openpyxl** (≥3.1) - Excel file reading
- **yt-dlp** (≥2024.1) - Video downloading engine
- **curl_cffi** (≥0.10, <0.15) - Browser impersonation support

## Tips & Best Practices

1. **Test with `--dry-run`** before downloading large batches
2. **Use descriptive names** in the Excel Name column
3. **Close browsers** before using `--cookies-from-browser`
4. **Organize downloads** with `-o` to specify output folders
5. **Combine authentication methods** for stubborn sites
6. **Check ffmpeg** is installed for MP3 and Both modes

## License

This project is licensed under the MIT License.

## Disclaimer

This tool is for personal use only. Respect copyright laws and terms of service of the websites you download from. The authors are not responsible for any misuse of this software.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The powerful video download engine
- [curl_cffi](https://github.com/yifeikong/curl_cffi) - Browser impersonation support