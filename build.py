#!/usr/bin/env python3
"""
Giraffe - Music Portfolio Automation System

This script processes music tracks and generates a static GitHub Pages site.
It handles audio encoding, S3 uploads, and static site generation.
"""

import os
import re
import sys
import subprocess
import shutil
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

import yaml
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
import markdown2


# Load environment variables
load_dotenv()


class Config:
    """Configuration management"""

    def __init__(self):
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.s3_bucket = os.getenv('S3_BUCKET_NAME')
        self.s3_base_url = os.getenv('S3_BASE_URL')
        self.site_title = os.getenv('SITE_TITLE', 'My Music Portfolio')
        self.site_description = os.getenv('SITE_DESCRIPTION', 'A collection of my music tracks')
        self.site_author = os.getenv('SITE_AUTHOR', 'Artist')
        self.github_username = os.getenv('GITHUB_USERNAME', 'yourusername')
        self.mp3_bitrate = os.getenv('MP3_BITRATE', '192')
        self.mp3_quality = os.getenv('MP3_QUALITY', '2')

        # Validate required config
        if not self.s3_bucket or not self.s3_base_url:
            print("Warning: S3 configuration not complete. Audio files won't be uploaded.")
            print("Set S3_BUCKET_NAME and S3_BASE_URL in .env file")


class Track:
    """Represents a music track with metadata"""

    def __init__(self, directory: Path):
        self.directory = directory
        self.slug = directory.name
        self.metadata = {}
        self.content = ""
        self.wav_path = None
        self.mp3_path = None
        self.cover_path = None
        self.image_paths = []  # All images in the track folder
        self.mp3_url = ""
        self.wav_url = ""

    def load_metadata(self) -> bool:
        """Load metadata from markdown file"""
        md_files = list(self.directory.glob('*.md'))
        if not md_files:
            print(f"Warning: No .md file found in {self.directory}")
            return False

        md_file = md_files[0]

        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    self.metadata = yaml.safe_load(parts[1]) or {}
                    self.content = markdown2.markdown(parts[2].strip())
                else:
                    print(f"Warning: Invalid frontmatter in {md_file}")
                    return False
            else:
                print(f"Warning: No frontmatter found in {md_file}")
                return False

            # Validate required fields
            if 'title' not in self.metadata:
                print(f"Warning: No title in {md_file}")
                return False

            return True

        except Exception as e:
            print(f"Error reading {md_file}: {e}")
            return False

    def find_files(self) -> bool:
        """Find WAV and cover image files"""
        # Find WAV file
        wav_files = list(self.directory.glob('*.wav')) + list(self.directory.glob('*.WAV'))
        if wav_files:
            self.wav_path = wav_files[0]
        else:
            print(f"Warning: No WAV file found in {self.directory}")
            return False

        # Find all image files (for carousel support)
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'JPG', 'JPEG', 'PNG', 'GIF', 'WEBP']
        for ext in image_extensions:
            self.image_paths.extend(self.directory.glob(f'*.{ext}'))

        # Sort images by name for consistent ordering
        self.image_paths = sorted(self.image_paths, key=lambda p: p.name)

        # First image is the primary cover
        if self.image_paths:
            self.cover_path = self.image_paths[0]
        else:
            print(f"Warning: No cover image found in {self.directory}")
            return False

        return True

    @property
    def title(self) -> str:
        return self.metadata.get('title', self.slug)

    @property
    def year(self) -> str:
        return str(self.metadata.get('year', ''))

    @property
    def category(self) -> str:
        return self.metadata.get('category', '')

    @property
    def status(self) -> str:
        return self.metadata.get('status', 'final')

    @property
    def tags(self) -> List[str]:
        tags = self.metadata.get('tags', [])
        return tags if isinstance(tags, list) else []

    @property
    def created(self) -> str:
        return str(self.metadata.get('created', ''))

    @property
    def modified(self) -> str:
        return str(self.metadata.get('modified', ''))

    @property
    def cover_filename(self) -> str:
        """Get the filename of the primary cover image"""
        if self.cover_path:
            return f"{self.slug}-{self.cover_path.name}"
        return ""

    @property
    def image_filenames(self) -> List[str]:
        """Get filenames of all images for this track"""
        return [f"{self.slug}-{img.name}" for img in self.image_paths]


class GiraffeBuilder:
    """Main builder class"""

    def __init__(self, static_only=False):
        self.config = Config()
        self.static_only = static_only
        self.base_dir = Path(__file__).parent
        self.tracks_dir = self.base_dir / 'tracks'
        self.output_dir = self.base_dir / 'docs'
        self.templates_dir = self.base_dir / 'templates'
        self.assets_dir = self.base_dir / 'assets'

        # Initialize S3 client
        self.s3_client = None
        if self.config.aws_access_key and self.config.aws_secret_key:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.config.aws_access_key,
                    aws_secret_access_key=self.config.aws_secret_key,
                    region_name=self.config.aws_region
                )
            except Exception as e:
                print(f"Warning: Could not initialize S3 client: {e}")

        # Initialize Jinja2
        self.jinja_env = Environment(loader=FileSystemLoader(str(self.templates_dir)))

    def check_dependencies(self) -> bool:
        """Check if required tools are installed"""
        try:
            result = subprocess.run(['ffmpeg', '-version'],
                                  capture_output=True,
                                  text=True,
                                  timeout=5)
            if result.returncode != 0:
                print("Error: ffmpeg not found. Please install ffmpeg.")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("Error: ffmpeg not found. Please install ffmpeg.")
            print("Install with: sudo apt install ffmpeg")
            return False

        return True

    def scan_tracks(self) -> List[Track]:
        """Scan tracks directory and load all tracks"""
        tracks = []

        if not self.tracks_dir.exists():
            print(f"Error: Tracks directory not found: {self.tracks_dir}")
            return tracks

        for track_dir in sorted(self.tracks_dir.iterdir(), reverse=True):
            if not track_dir.is_dir():
                continue

            # Skip example track if it doesn't have real files
            if track_dir.name == 'example-track':
                continue

            print(f"Processing: {track_dir.name}")
            track = Track(track_dir)

            if not track.load_metadata():
                print(f"  Skipping due to metadata error")
                continue

            if not track.find_files():
                print(f"  Skipping due to missing files")
                continue

            tracks.append(track)
            print(f"  ✓ Loaded: {track.title}")

        return tracks

    def encode_mp3(self, track: Track) -> Optional[Path]:
        """Encode WAV to MP3 using ffmpeg"""
        mp3_path = track.directory / f"{track.slug}.mp3"

        # Skip if MP3 already exists and is newer than WAV
        if mp3_path.exists():
            if mp3_path.stat().st_mtime > track.wav_path.stat().st_mtime:
                print(f"  ✓ MP3 already exists and is up to date")
                return mp3_path

        print(f"  Encoding MP3...")

        cmd = [
            'ffmpeg',
            '-i', str(track.wav_path),
            '-codec:a', 'libmp3lame',
            '-b:a', f'{self.config.mp3_bitrate}k',
            '-q:a', self.config.mp3_quality,
            '-y',  # Overwrite output file
            str(mp3_path)
        ]

        try:
            result = subprocess.run(cmd,
                                  capture_output=True,
                                  text=True,
                                  timeout=300)
            if result.returncode == 0:
                print(f"  ✓ MP3 encoded successfully")
                return mp3_path
            else:
                print(f"  Error encoding MP3: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            print(f"  Error: ffmpeg timed out")
            return None
        except Exception as e:
            print(f"  Error: {e}")
            return None

    def calculate_md5(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def file_needs_upload(self, local_path: Path, s3_key: str) -> tuple[bool, Optional[str]]:
        """Check if local file needs to be uploaded to S3

        Returns:
            tuple: (needs_upload: bool, etag: Optional[str])
            - needs_upload: True if file should be uploaded, False to skip
            - etag: S3 ETag if file exists, None otherwise
        """
        if not self.s3_client:
            return (True, None)

        try:
            # Check if file exists in S3 and get its ETag
            response = self.s3_client.head_object(
                Bucket=self.config.s3_bucket,
                Key=s3_key
            )
            s3_etag = response['ETag'].strip('"')  # Remove quotes from ETag
            s3_size = response.get('ContentLength', 0)

            # Get local file size
            local_size = local_path.stat().st_size

            # Check if ETag indicates multipart upload (contains hyphen)
            if '-' in s3_etag:
                # Multipart upload - compare file sizes instead of MD5
                if s3_size == local_size:
                    return (False, s3_etag)  # Same size, likely unchanged
                else:
                    return (True, s3_etag)  # Different size, needs upload
            else:
                # Simple upload - compare MD5 hash
                local_md5 = self.calculate_md5(local_path)

                if s3_etag == local_md5:
                    return (False, s3_etag)  # Hash matches, skip upload
                else:
                    return (True, s3_etag)  # Hash differs, need upload

        except self.s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return (True, None)  # File doesn't exist, need upload
            else:
                # Other error, safer to attempt upload
                print(f"  ⚠ Error checking S3: {e}")
                return (True, None)

    def upload_to_s3(self, track: Track, mp3_path: Path) -> bool:
        """Upload WAV and MP3 files to S3"""
        if not self.s3_client or not self.config.s3_bucket:
            print(f"  ⚠ Skipping S3 upload (not configured)")
            return False

        try:
            # Upload MP3
            mp3_key = f"{track.slug}/{track.slug}.mp3"
            needs_upload, etag = self.file_needs_upload(mp3_path, mp3_key)

            if needs_upload:
                print(f"  Uploading MP3 to S3...")
                self.s3_client.upload_file(
                    str(mp3_path),
                    self.config.s3_bucket,
                    mp3_key,
                    ExtraArgs={'ContentType': 'audio/mpeg'}
                )
                print(f"  ✓ MP3 uploaded")
            else:
                etag_display = etag[:8] if etag else "unknown"
                comparison = "size" if etag and '-' in etag else "MD5"
                print(f"  ✓ MP3 already on S3 (unchanged, {comparison} match, ETag: {etag_display}...)")

            track.mp3_url = f"{self.config.s3_base_url}/{mp3_key}"

            # Upload WAV
            wav_key = f"{track.slug}/{track.slug}.wav"
            if not track.wav_path:
                print(f"  ⚠ WAV file path not found, skipping upload")
                return False

            needs_upload, etag = self.file_needs_upload(track.wav_path, wav_key)

            if needs_upload:
                print(f"  Uploading WAV to S3...")
                self.s3_client.upload_file(
                    str(track.wav_path),
                    self.config.s3_bucket,
                    wav_key,
                    ExtraArgs={'ContentType': 'audio/wav'}
                )
                print(f"  ✓ WAV uploaded")
            else:
                etag_display = etag[:8] if etag else "unknown"
                comparison = "size" if etag and '-' in etag else "MD5"
                print(f"  ✓ WAV already on S3 (unchanged, {comparison} match, ETag: {etag_display}...)")

            track.wav_url = f"{self.config.s3_base_url}/{wav_key}"

            return True

        except ClientError as e:
            print(f"  Error uploading to S3: {e}")
            return False
        except Exception as e:
            print(f"  Error: {e}")
            return False

    def generate_site(self, tracks: List[Track]) -> bool:
        """Generate static HTML site"""
        print("\nGenerating static site...")

        # Create output directories
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / 'tracks').mkdir(exist_ok=True)
        (self.output_dir / 'covers').mkdir(exist_ok=True)

        # Copy assets
        if self.assets_dir.exists():
            dest_assets = self.output_dir / 'assets'
            if dest_assets.exists():
                shutil.rmtree(dest_assets)
            shutil.copytree(self.assets_dir, dest_assets)
            print("  ✓ Copied assets")

        # Copy all track images
        image_count = 0
        for track in tracks:
            for img_path in track.image_paths:
                # Prefix with track slug to avoid naming collisions
                dest_img = self.output_dir / 'covers' / f"{track.slug}-{img_path.name}"
                shutil.copy2(img_path, dest_img)
                image_count += 1
        print(f"  ✓ Copied {image_count} image(s)")

        # Generate track pages
        track_template = self.jinja_env.get_template('track.html')
        for track in tracks:
            output_file = self.output_dir / 'tracks' / f"{track.slug}.html"

            html = track_template.render(
                track=track,
                site_title=self.config.site_title,
                site_description=self.config.site_description,
                github_username=self.config.github_username,
                is_track=True
            )

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

        print(f"  ✓ Generated {len(tracks)} track pages")

        # Generate index page
        index_template = self.jinja_env.get_template('index.html')
        index_html = index_template.render(
            tracks=tracks,
            site_title=self.config.site_title,
            site_description=self.config.site_description,
            github_username=self.config.github_username,
            is_track=False
        )

        with open(self.output_dir / 'index.html', 'w', encoding='utf-8') as f:
            f.write(index_html)

        print("  ✓ Generated index page")

        return True

    def build(self) -> bool:
        """Main build process"""
        print("=" * 60)
        print("Giraffe - Music Portfolio Builder")
        if self.static_only:
            print("(Static-only mode: skipping audio processing)")
        print("=" * 60)

        # Check dependencies (skip in static-only mode)
        if not self.static_only and not self.check_dependencies():
            return False

        # Scan tracks
        print("\nScanning tracks directory...")
        tracks = self.scan_tracks()

        if not tracks:
            print("\nNo valid tracks found to process.")
            print("Add tracks to the 'tracks/' directory and try again.")
            return False

        print(f"\nFound {len(tracks)} track(s) to process\n")

        # Process each track
        if not self.static_only:
            for i, track in enumerate(tracks, 1):
                print(f"[{i}/{len(tracks)}] {track.title}")

                # Encode MP3
                mp3_path = self.encode_mp3(track)
                if not mp3_path:
                    print(f"  ⚠ Skipping due to encoding error")
                    continue

                track.mp3_path = mp3_path

                # Upload to S3
                self.upload_to_s3(track, mp3_path)

                print()
        else:
            print("Skipping audio encoding and upload (static-only mode)\n")

        # Generate static site
        if not self.generate_site(tracks):
            return False

        print("\n" + "=" * 60)
        print("✓ Build complete!")
        print("=" * 60)
        print(f"\nGenerated site in: {self.output_dir}")
        print("\nNext steps:")
        print("1. Review the generated site in docs/index.html")
        print("2. Commit and push to GitHub")
        print("3. Enable GitHub Pages from the 'docs' folder")
        print()

        return True


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(
        description='Giraffe - Music Portfolio Automation System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py                    # Full build (encode, upload, generate)
  python build.py --static-only      # Only regenerate HTML/CSS (skip audio)
        """
    )
    parser.add_argument(
        '--static-only',
        action='store_true',
        help='Skip audio encoding and S3 upload, only regenerate static site'
    )

    args = parser.parse_args()

    builder = GiraffeBuilder(static_only=args.static_only)
    success = builder.build()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
