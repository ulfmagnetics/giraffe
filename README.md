# Giraffe

Giraffe is a tool for automating the posting of music tracks (or drafts of those tracks!) to GitHub Pages. The goal is to reproduce something akin to SoundCloud for a single musician who just wants to share some music with friends, family, or the folks they collaborate with.

## Features

- **Simple workflow**: Add a directory with WAV, markdown, and cover art → run build script → deploy
- **Automatic audio encoding**: Converts WAV to MP3 for streaming (preserves WAV for downloads)
- **Cloud hosting**: Upload audio files to AWS S3 for reliable delivery
- **Static site generation**: Creates a beautiful, responsive portfolio site
- **Search and filtering**: Client-side search, tag filtering, and draft/final status toggles
- **Mobile-friendly**: Responsive design works on all devices
- **No server required**: Pure static site hosted on GitHub Pages

## Prerequisites

Before installing Giraffe, ensure you have the following installed on Ubuntu 24.04:

### 1. Python 3.12+

Python should be pre-installed on Ubuntu 24.04. Verify with:

```bash
python3 --version
```

If not installed:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 2. ffmpeg

Required for audio encoding (WAV → MP3):

```bash
sudo apt update
sudo apt install ffmpeg
```

Verify installation:

```bash
ffmpeg -version
```

### 3. AWS Account (for S3 hosting)

You'll need an AWS account to host audio files. The free tier includes 5GB of S3 storage.

### 4. GitHub Account

For hosting the static site on GitHub Pages.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/giraffe.git
cd giraffe
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
nano .env
```

See the [Configuration](#configuration) section below for details.

## Configuration

### AWS S3 Setup

#### Step 1: Create an S3 Bucket

1. Log in to [AWS Console](https://console.aws.amazon.com/)
2. Navigate to **S3** service
3. Click **Create bucket**
4. Enter a bucket name (e.g., `my-music-portfolio`)
5. Choose a region (e.g., `us-east-1`)
6. **Uncheck** "Block all public access" (we need public read access for audio files)
7. Acknowledge the warning about public access
8. Click **Create bucket**

#### Step 2: Configure CORS Policy

To allow your GitHub Pages site to access audio files from S3:

1. Open your S3 bucket
2. Go to the **Permissions** tab
3. Scroll to **Cross-origin resource sharing (CORS)**
4. Click **Edit** and add this configuration:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "HEAD"],
        "AllowedOrigins": [
            "https://yourusername.github.io",
            "http://localhost:*"
        ],
        "ExposeHeaders": [],
        "MaxAgeSeconds": 3600
    }
]
```

Replace `yourusername.github.io` with your actual GitHub Pages domain.

#### Step 3: Create IAM User

For security, create a dedicated IAM user with limited S3 permissions:

1. Navigate to **IAM** service in AWS Console
2. Click **Users** → **Add users**
3. Username: `giraffe-uploader`
4. Select **Access key - Programmatic access**
5. Click **Next: Permissions**
6. Click **Attach existing policies directly**
7. Click **Create policy** → **JSON** tab
8. Paste this policy (replace `YOUR-BUCKET-NAME`):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR-BUCKET-NAME",
                "arn:aws:s3:::YOUR-BUCKET-NAME/*"
            ]
        }
    ]
}
```

9. Name the policy `giraffe-s3-upload`
10. Attach the policy to your new user
11. **Save the Access Key ID and Secret Access Key** (you'll need these for `.env`)

#### Step 4: Update .env File

Add your AWS credentials to `.env`:

```bash
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
S3_BASE_URL=https://your-bucket-name.s3.amazonaws.com
```

For `S3_BASE_URL`, use this format:
```
https://BUCKET-NAME.s3.REGION.amazonaws.com
```

For example:
```
https://my-music-portfolio.s3.us-east-1.amazonaws.com
```

### GitHub Pages Setup

#### Step 1: Push to GitHub

```bash
git add .
git commit -m "Initial Giraffe setup"
git push origin main
```

#### Step 2: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under **Source**, select **Deploy from a branch**
4. Under **Branch**, select `main` and `/docs` folder
5. Click **Save**

Your site will be available at `https://yourusername.github.io/giraffe/` within a few minutes.

## Usage

### Adding a New Track

1. **Create a track directory** in `tracks/`:

```bash
mkdir tracks/my-awesome-song
```

2. **Add three required files**:

   - **Audio file** (`.wav`): Your source-quality audio
   - **Metadata file** (`.md`): Track information and description
   - **Cover image** (`.jpg`, `.png`, etc.): Album art

Example:

```bash
tracks/my-awesome-song/
├── track.wav
├── track.md
└── cover.jpg
```

3. **Create the metadata file** (`track.md`):

```markdown
---
title: My Awesome Song
year: 2024
category: Electronic
status: final
tags:
  - ambient
  - experimental
created: 2024-11-30
modified: 2024-11-30
---

## Description

This is a description of my track. You can use **markdown** formatting here.

## Notes

Production notes, influences, or any other information about the track.
```

### Metadata Fields

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Track title (displayed everywhere) |
| `year` | No | Year of creation |
| `category` | No | Genre or category |
| `status` | No | `draft`, `work-in-progress`, or `final` (default: `final`) |
| `tags` | No | List of tags for filtering |
| `created` | No | Creation date |
| `modified` | No | Last modified date |

### Building the Site

Run the build script:

```bash
python build.py
```

The script will:
1. ✓ Scan the `tracks/` directory
2. ✓ Encode WAV files to MP3 (192kbps VBR)
3. ✓ Upload audio files to S3
4. ✓ Generate static HTML pages
5. ✓ Copy assets and cover images

Generated site will be in `docs/` folder.

### Deploying to GitHub Pages

After building:

```bash
git add docs/
git commit -m "Update music portfolio"
git push origin main
```

GitHub Pages will automatically deploy your updated site within 1-2 minutes.

## Project Structure

```
giraffe/
├── tracks/                    # Your music tracks (gitignored)
│   └── my-song/
│       ├── track.wav         # Source audio
│       ├── track.md          # Metadata + description
│       └── cover.jpg         # Cover art
├── docs/                      # Generated site (gitignored until built)
│   ├── index.html            # Main page with track grid
│   ├── tracks/               # Individual track pages
│   ├── covers/               # Cover images
│   └── assets/               # CSS/JS
├── templates/                 # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   └── track.html
├── assets/                    # Static assets (CSS/JS)
│   ├── style.css
│   └── app.js
├── build.py                   # Main automation script
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (gitignored)
├── .env.example              # Environment template
└── README.md                  # This file
```

## Troubleshooting

### ffmpeg not found

**Error**: `Error: ffmpeg not found`

**Solution**:
```bash
sudo apt update
sudo apt install ffmpeg
```

### S3 upload fails

**Error**: `Error uploading to S3`

**Possible causes**:
- Incorrect AWS credentials in `.env`
- IAM user doesn't have S3 permissions
- Bucket name is incorrect

**Solution**:
1. Verify credentials in `.env`
2. Check IAM policy allows `s3:PutObject` and `s3:PutObjectAcl`
3. Verify bucket name matches exactly

### Audio doesn't play on GitHub Pages

**Possible causes**:
- CORS policy not configured on S3 bucket
- Audio files not public in S3

**Solution**:
1. Add CORS policy (see [Configuration](#configuration))
2. Ensure files are uploaded with `public-read` ACL (build script does this automatically)

### Tracks not appearing

**Possible causes**:
- Missing required files (WAV, markdown, or cover image)
- Missing `title` field in frontmatter
- Track directory name contains special characters

**Solution**:
1. Verify all three files exist in track directory
2. Check that frontmatter has `title` field
3. Use lowercase letters and hyphens only for directory names

## Advanced Configuration

### Custom MP3 Encoding Settings

Edit `.env` to change encoding quality:

```bash
# Bitrate in kbps (128, 192, 256, 320)
MP3_BITRATE=192

# VBR quality (0-9, lower is better)
MP3_QUALITY=2
```

### Site Customization

Edit `.env` to customize site metadata:

```bash
SITE_TITLE=My Music Portfolio
SITE_DESCRIPTION=A collection of my music tracks and experiments
SITE_AUTHOR=Your Name
```

### Template Customization

Modify templates in `templates/` directory:
- `base.html` - Overall layout and structure
- `index.html` - Track listing page
- `track.html` - Individual track pages

Modify styles in `assets/style.css` to change colors, fonts, and layout.

## Tips

- **Use descriptive directory names**: Use kebab-case (e.g., `ambient-sunrise-2024`)
- **Square cover images**: 1:1 aspect ratio works best (e.g., 1000x1000px)
- **WAV quality**: 48kHz/24-bit or 44.1kHz/16-bit recommended
- **Draft status**: Use `status: draft` while working, change to `final` when ready to share
- **Tags for organization**: Add descriptive tags to enable filtering (e.g., `ambient`, `upbeat`, `remix`)

## License

MIT License - feel free to use and modify for your own music portfolio.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

---

Built with Python, ffmpeg, AWS S3, and GitHub Pages.
