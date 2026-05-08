from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget


def sanitize_filename(name: str, max_length: int = 180) -> str:
    """Make a string safe for Windows filenames."""
    name = str(name).strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name.strip(". ")
    if len(name) > max_length:
        name = name[:max_length].rstrip(". ")
    return name or "video"


def _noodlemagazine_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host == "noodlemagazine.com" or host.endswith(".noodlemagazine.com")


def _prompt_download_mode() -> str:
    print()
    print("Select download type:")
    print("  1) MP4 video")
    print("  2) MP3 audio only")
    print("  3) Both MP4 and MP3 (same title, two files; needs ffmpeg)")
    print()
    while True:
        try:
            choice = input("Enter 1, 2, or 3: ").strip()
        except EOFError:
            print("\nNo input; defaulting to MP4.", file=sys.stderr)
            return "mp4"
        if choice == "1":
            return "mp4"
        if choice == "2":
            return "mp3"
        if choice == "3":
            return "both"
        print("Invalid choice. Type 1, 2, or 3.", file=sys.stderr)


def _resolve_download_mode(args: argparse.Namespace) -> str:
    if args.mode:
        return args.mode
    if sys.stdin.isatty():
        return _prompt_download_mode()
    print("stdin is not a terminal; use --mode mp4|mp3|both (default: mp4).", file=sys.stderr)
    return "mp4"


def _build_ydl_opts_for_mode(mode: str, outtmpl: str, base: dict, impersonate_target: ImpersonateTarget | None = None) -> dict:
    opts = {**base, "outtmpl": outtmpl}
    if mode == "mp4":
        opts["format"] = "bv*+ba/b"
        opts["merge_output_format"] = "mp4"
    elif mode == "mp3":
        opts["format"] = "ba/b"
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
    elif mode == "both":
        opts["format"] = "bv*+ba/b"
        opts["merge_output_format"] = "mp4"
        opts["keepvideo"] = True
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
    else:
        raise ValueError(mode)

    # Configure impersonation as extractor args for generic extractor (needed for Cloudflare sites)
    # and also as global option for other extractors
    if impersonate_target:
        opts["impersonate"] = impersonate_target
        # For generic extractor, impersonation must be passed via extractor_args
        opts["extractor_args"] = {
            "generic": {
                "impersonate": str(impersonate_target)
            }
        }

    return opts


def main() -> int:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass

    parser = argparse.ArgumentParser(description="Download videos from CSV Name + URL columns.")
    parser.add_argument(
        "csv_file",
        nargs="?",
        default="list.csv",
        help="Path to .csv file (default: list.csv)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="downloads",
        help="Folder for downloaded files (default: downloads)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be downloaded without downloading",
    )
    parser.add_argument(
        "--mode",
        choices=("mp4", "mp3", "both"),
        default=None,
        help="Skip the menu: mp4, mp3, or both (MP4+MP3). If omitted, you are prompted when stdin is a TTY.",
    )
    parser.add_argument(
        "--cookies-from-browser",
        metavar="BROWSER",
        help="e.g. chrome, edge — helps when sites return 403",
    )
    parser.add_argument(
        "--cookies",
        metavar="FILE",
        help="Path to cookies file (JSON/Netscape format). Overrides --cookies-from-browser.",
    )
    parser.add_argument(
        "--impersonate",
        metavar="TARGET",
        nargs="?",
        const="chrome",
        default=None,
        help="Browser TLS fingerprint for every row (default target with no arg: chrome). "
        "If omitted, chrome impersonation is used automatically only for noodlemagazine.com URLs.",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    if not csv_path.is_file():
        print(f"CSV not found: {csv_path.resolve()}", file=sys.stderr)
        return 1

    df = pd.read_csv(csv_path)
    col_name = next((c for c in df.columns if str(c).strip().lower() == "name"), None)
    col_url = next((c for c in df.columns if str(c).strip().lower() == "url"), None)
    if col_name is None or col_url is None:
        print("Expected columns 'Name' and 'URL' (case-insensitive). Found:", list(df.columns), file=sys.stderr)
        return 1
    
    # Add Status column if it doesn't exist
    col_status = next((c for c in df.columns if str(c).strip().lower() == "status"), None)
    if col_status is None:
        col_status = "Status"
        df[col_status] = ""
    
    # Ensure Status column is string type (object dtype) to avoid pandas type errors
    df[col_status] = df[col_status].astype(str).replace('nan', '')

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    mode = _resolve_download_mode(args)
    mode_label = {"mp4": "MP4 video", "mp3": "MP3 audio", "both": "MP4 + MP3"}[mode]
    print(f"\nDownload mode: {mode_label}")

    base_opts: dict = {
        "quiet": False,
        "no_warnings": False,
        "ignoreerrors": False,
        "retries": 3,
        "fragment_retries": 3,
    }
    if args.cookies:
        base_opts["cookiefile"] = args.cookies
    elif args.cookies_from_browser:
        base_opts["cookiesfrombrowser"] = (args.cookies_from_browser,)

    ok, failed, skipped = 0, 0, 0
    for idx, row in df.iterrows():
        raw_name = row[col_name]
        raw_url = row[col_url]
        
        # Skip if already successfully downloaded
        current_status = str(row.get(col_status, "")).strip()
        if current_status.lower() == "success":
            print(f"Row {idx + 2}: skip (already downloaded)")
            skipped += 1
            continue
        
        if pd.isna(raw_url) or not str(raw_url).strip():
            print(f"Row {idx + 2}: skip (empty URL)")
            continue
        url = str(raw_url).strip()
        if pd.isna(raw_name):
            base = f"video_{idx}"
        else:
            base = sanitize_filename(raw_name)
        outtmpl = str(out_dir / f"{base}.%(ext)s")

        print(f"\n--- [{idx + 1}/{len(df)}] {base}")
        print(f"    {url}")

        if args.dry_run:
            ok += 1
            continue

        # Determine impersonation target for this URL
        impersonate_target = None
        if args.impersonate:
            impersonate_target = ImpersonateTarget.from_str(args.impersonate.lower())
        elif _noodlemagazine_url(url):
            impersonate_target = ImpersonateTarget.from_str("chrome")

        ydl_opts = _build_ydl_opts_for_mode(mode, outtmpl, base_opts, impersonate_target)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            df.at[idx, col_status] = "Success"
            ok += 1
        except yt_dlp.utils.DownloadError as e:
            print(f"    ERROR: {e}", file=sys.stderr)
            df.at[idx, col_status] = "Failed"
            failed += 1
    
    # Save the updated DataFrame back to CSV
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"\nStatus saved to {csv_path}")
    print(f"Done. OK: {ok}, failed: {failed}, skipped: {skipped}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
