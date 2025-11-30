---
title: Example Track
year: 2024
category: Electronic
status: draft
tags:
  - ambient
  - experimental
  - demo
created: 2024-11-30
modified: 2024-11-30
---

## Description

This is an example track that demonstrates the proper format for Giraffe.

Replace this directory with your own music tracks. Each track should have:
- A WAV audio file (source quality)
- A markdown file with YAML frontmatter (this file)
- A cover image (JPG, PNG, etc.)

## Notes

**To use Giraffe:**

1. Create a new subdirectory in `tracks/` with a descriptive name (e.g., `my-awesome-song`)
2. Add your WAV file, markdown file, and cover image to that directory
3. Run `python build.py` to generate your site
4. The generated site will be in the `docs/` folder

**Metadata fields:**

- `title` (required): The track title
- `year`: Year of creation
- `category`: Genre or category
- `status`: `draft`, `work-in-progress`, or `final`
- `tags`: List of tags for filtering
- `created`: Creation date
- `modified`: Last modified date

The markdown content below the frontmatter will be rendered on the track page.
