# Example Track

This directory shows the expected structure for a music track in Giraffe.

## Required Files

Each track directory should contain:

1. **Audio file** (`track.wav` or any `.wav` file)
   - Source quality WAV format
   - Will be automatically encoded to MP3 for streaming

2. **Metadata file** (`track.md` or any `.md` file)
   - YAML frontmatter with track metadata
   - Markdown content for description/notes

3. **Cover image** (`cover.jpg`, `cover.png`, or any image file)
   - Album art or cover image
   - Square format recommended (1:1 aspect ratio)
   - At least 600x600px recommended

## Example Structure

```
my-song/
├── track.wav          # Audio file
├── track.md           # Metadata + description
└── cover.jpg          # Cover art
```

## Getting Started

To add your own tracks:

1. Delete this example-track directory (or keep as reference)
2. Create a new directory with your track name (use lowercase and hyphens)
3. Add your three required files
4. Run `python build.py`
