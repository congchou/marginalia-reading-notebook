# Marginalia iPhone PWA Implementation Plan

> **For agentic workers:** Implement tasks in order and verify each deliverable before publishing.

**Goal:** Ship a separate offline iPhone PWA with migration from the existing desktop app.

**Architecture:** Buildless HTML/CSS/ES modules in `docs/pwa/`; IndexedDB for records; a service worker for the shell; CSV import/export shared with the desktop schema.

**Tech Stack:** HTML, CSS, browser JavaScript, IndexedDB, Service Worker, Node built-in test runner, Streamlit/Python for desktop export.

## Global constraints

- Keep Streamlit app and local SQLite data intact.
- No remote runtime assets or accounts.
- Install through HTTPS; operate offline after initial load.
- Keep personal data on device and provide CSV backup/export.

### Task 1: Data format and persistence

- Add pure CSV and record validation functions in `docs/pwa/data.mjs`.
- Add IndexedDB wrapper in `docs/pwa/storage.mjs`.
- Test CSV quoting, mixed record import, duplicates, and export with `node --test docs/pwa/tests/*.test.mjs`.

### Task 2: Mobile app

- Add `docs/pwa/index.html`, `styles.css`, and `app.mjs`.
- Implement overview, capture, library search/filter/edit/delete, review reveal/status, and data import/export.
- Verify at narrow viewport and with keyboard/touch semantics.

### Task 3: Installable offline shell

- Add `manifest.webmanifest`, `sw.js`, and local icons.
- Verify manifest references, service worker registration, cached assets, and offline navigation.

### Task 4: Migration and publication

- Add desktop CSV export to the Streamlit app.
- Update README with desktop-to-iPhone migration and installation steps.
- Run existing Python tests, PWA Node tests, browser smoke checks, and publish `/docs` through GitHub Pages.
