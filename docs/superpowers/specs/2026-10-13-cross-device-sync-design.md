# Marginalia cross-device sync design

## Decision and scope

The user approved Supabase-backed sync for the existing Streamlit desktop app and offline iPhone PWA, then asked us to build the code before a Supabase project exists. The existing SQLite and IndexedDB stores remain usable without cloud configuration. No personal content or secret key enters GitHub.

## Cloud contract

Supabase Auth email/password identifies the same person on both devices. A `cards` table stores one row per card with UUID, owner, content, status, revision, and soft-delete flag. Row Level Security limits every read and write to the authenticated owner. The browser uses only a publishable key; never a service-role key. A SQL setup script creates the schema and policies.

## Sync protocol

Each device keeps a local copy. On login, startup, reconnect, and periodic foreground checks, it fetches cloud changes and uploads local edits. New cards receive a stable UUID; edits and deletions use a revision compare-and-swap so stale clients cannot silently overwrite newer data. A conflict stays local and is reported rather than discarded. Deletions are tombstones so offline deletes propagate. The first sync merges local and remote cards, matching identical content identities to avoid duplication. The CSV export remains an independent backup.

## Desktop and iPhone behavior

PWA session tokens are stored in browser storage and refreshed when online. Offline operations continue against IndexedDB and queue implicitly as dirty rows. Streamlit keeps its existing SQLite format, adds a sync-mapping table, and holds the login session in memory; it syncs on login, app interaction, and a periodic foreground refresh. The Mac need not stay online continuously; changes catch up when the app runs again. A missing or invalid cloud configuration is shown clearly without interrupting local use.

## Verification and deployment

Pure merge/conflict logic is unit-tested in JavaScript and Python. HTTP/auth code is exercised with fake transports. Existing tests must keep passing. The PWA is rechecked in a narrow viewport; once published, the GitHub Pages assets must load over HTTPS. A live two-device sync test requires the user's Supabase project and is explicitly not claimed before then.
