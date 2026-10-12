# CSV Import and Sidebar Polish Implementation Plan

**Goal:** Improve sidebar readability and add safe CSV batch import with preview, validation, templates, and duplicate reporting.

**Architecture:** Keep CSV parsing in a pure `marginalia/importer.py` module and render upload controls in the capture page. Reuse the existing database API for transactional row insertion and duplicate detection.

## Tasks

1. Write failing parser tests covering mixed content, UTF-8 BOM, aliases, required columns, and invalid rows.
2. Implement typed CSV parsing and a downloadable template.
3. Add upload, preview, validation, and confirmed import UI.
4. Increase sidebar typography and improve its information card.
5. Run unit, compile, Streamlit runtime, and browser visual checks; commit and push.
