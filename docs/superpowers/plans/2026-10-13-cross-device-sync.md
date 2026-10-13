# Marginalia Cross-Device Sync Implementation Plan

**Goal:** Add optional Supabase sync to Streamlit and the offline PWA without losing local data.

**Architecture:** Shared cloud schema with per-user RLS, revision-based optimistic writes, and local dirty metadata. Each client keeps its native store and uploads/downloads through Supabase REST Auth and PostgREST.

**Tech Stack:** Python standard library, SQLite, Streamlit, browser ES modules, IndexedDB, Supabase Auth/PostgREST.

## Tasks

1. Define and test the cloud row contract, revision conflict behavior, and schema policies. Keep the setup SQL in the repository, never a secret key.
2. Extend the PWA local store with dirty/tombstone metadata; test offline edits, deletes, and remote merge before connecting HTTP.
3. Implement PWA login/session refresh and sync transport; connect login and status controls to the UI and precache new assets.
4. Add a desktop sync-mapping table and Python sync engine with tests for initial migration, update, deletion, remote changes, and conflicts. Connect it to Streamlit's sidebar.
5. Document project creation and configuration. Run the full tests and browser smoke checks, then publish the code. Reserve the live two-device verification for when Supabase is configured.
