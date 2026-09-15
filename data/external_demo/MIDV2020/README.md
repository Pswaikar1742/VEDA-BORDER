# Optional MIDV-2020 demo media

The image files for this curated MIDV-2020 demo subset are intentionally not stored in the Git repository because they are large. The tracked `manifest.json` records the expected relative paths and allowlist metadata.

To use this optional demo locally, place the licensed sample images at the paths listed in `manifest.json`. The core synthetic VEDA fixtures in `data/integrated_fixtures/` do not require MIDV-2020 media.

Do not commit the images. The repository `.gitignore` excludes JPG/JPEG/PNG files in this directory.
