# Marginalia iPhone PWA design

## Scope

Build a separate installable iPhone web app under `docs/pwa/`. Preserve the existing Streamlit app. The PWA works without a running Python server after its first successful online load and installation.

## User experience

The interface keeps the paper colored Marginalia identity. A compact top bar, four bottom navigation items, large touch targets, safe area padding, and single column cards suit iPhone portrait use. The main flows are overview, capture, library, and review. A data panel provides CSV import, CSV backup export, installation guidance, and offline state.

## Data and migration

IndexedDB stores vocabulary and sentence records in one `entries` store. Each record has an ID, kind, content fields, source, tags, review status, and timestamps. The import parser accepts the desktop CSV columns (`type,word,meaning,sentence,translation,structure,source,tags,status`), validates required fields and status, previews valid rows, and skips duplicates. Export uses the same columns with a UTF-8 BOM so Numbers and Excel open Chinese text correctly. The desktop app gains a CSV export control so existing SQLite records can be moved to the phone. Nothing in the PWA sends personal records to the host.

## Offline behavior

A web manifest uses `display: standalone`, relative scope and start URL, and local icons. A same-origin service worker precaches the HTML, CSS, JavaScript, manifest, and icons. Navigation uses a cached shell fallback. No runtime font or JavaScript CDN is required. First installation needs an HTTPS connection; later launches and CRUD use cached assets and IndexedDB. An in-app backup reminder explains that device/browser storage can still be cleared.

## Hosting and verification

GitHub Pages serves the existing public repository's `/docs` folder, making the PWA available at `/marginalia-reading-notebook/pwa/`. Validate CSV parser and data functions with Node tests, exercise the mobile UI in a browser, inspect service worker and cache state, and check the published HTTPS URL. Physical iPhone installation remains for the user to confirm on their device.
