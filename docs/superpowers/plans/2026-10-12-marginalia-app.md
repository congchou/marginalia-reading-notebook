# Marginalia App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a polished, local-first Streamlit academic reading notebook with SQLite storage, migration, library browsing, and review workflows.

**Architecture:** Keep Streamlit rendering in `app.py`, move persistence and validation into focused modules under `marginalia/`, and exercise those modules with pytest. CSS and UI helpers stay separate from persistence so the data behavior is testable without launching a browser.

**Tech Stack:** Python 3, Streamlit, SQLite, pandas, pytest

## Global Constraints

- Preserve existing vocabulary by importing `vocabulary.csv` exactly once.
- Store personal data only in `data/marginalia.db`, which is ignored by Git.
- Use the approved “academic card catalogue” visual direction.
- Provide dashboard, capture, library, and review pages.
- Publish as a public GitHub repository after local verification.

---

### Task 1: SQLite repository and migration

**Files:**
- Create: `marginalia/database.py`
- Create: `marginalia/__init__.py`
- Test: `tests/test_database.py`

**Interfaces:**
- Produces: `init_db`, `add_entry`, `update_entry`, `delete_entry`, `list_entries`, `get_stats`, `import_legacy_csv`.

- [ ] Write tests for schema creation, CRUD behavior, duplicate rejection, combined filtering, statistics, and idempotent CSV migration.
- [ ] Run `pytest tests/test_database.py -v` and confirm failures are caused by missing implementation.
- [ ] Implement the repository with parameterized SQL, normalized text, timestamps, and transactions.
- [ ] Run `pytest tests/test_database.py -v` and confirm all database tests pass.

### Task 2: Streamlit product interface

**Files:**
- Replace: `app.py`
- Create: `marginalia/ui.py`
- Create: `.streamlit/config.toml`

**Interfaces:**
- Consumes: all repository functions from Task 1.
- Produces: four navigable pages and reusable visual helpers.

- [ ] Add import-level tests that prove UI helpers escape user content and normalize tags.
- [ ] Run the focused tests and confirm they fail before helper implementation.
- [ ] Implement app configuration, custom CSS, navigation, dashboard, capture forms, library filters/cards/editor/delete confirmation, and review workflow.
- [ ] Run the focused tests and full pytest suite.

### Task 3: Packaging and product documentation

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `README.md`
- Create: `tests/test_smoke.py`

**Interfaces:**
- Consumes: application entry point and package modules.
- Produces: reproducible installation and startup instructions.

- [ ] Add a smoke test that compiles all Python modules and initializes a temporary database.
- [ ] Run it and confirm it fails until packaging gaps are resolved.
- [ ] Add dependencies, ignore rules, README features, screenshots placeholder, data-safety notes, and run instructions.
- [ ] Run `pytest -v` and `python -m compileall app.py marginalia`.

### Task 4: Runtime verification and GitHub publication

**Files:**
- Verify all files from Tasks 1–3.

**Interfaces:**
- Produces: verified public repository `marginalia-reading-notebook`.

- [ ] Start Streamlit headlessly and confirm its health endpoint returns HTTP 200.
- [ ] Inspect startup logs for tracebacks and deprecation warnings.
- [ ] Initialize Git, commit the verified source tree, create a public GitHub repository, and push the default branch.
- [ ] Confirm the remote repository URL and remote branch state.
