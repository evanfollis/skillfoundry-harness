# ADR: Discovery adapter pure-parse interface

**Status**: proposed  
**Date**: 2026-04-23  
**Author**: tick session 2026-04-23T17-37-15Z  
**References**: adversarial review `.reviews/dcfd7e4-4d6050d-discovery-adapter-2026-04-23.md` Finding 3

---

## Problem

The current adapter (emit.py + migrate.py) conflates two concerns:

1. **Parsing** — extracting semantic structure from markdown text
2. **Filesystem operations** — hashing files, reading mtimes, resolving paths, writing to `.canon/`

Symptoms of the conflation:

- `_artifact_pointer(md_path)` calls `md_path.stat().st_mtime` — the "version" of a canonical envelope depends on when the file was last modified, not on its content.
- `migrate.py` hardcodes the venture-context directory layout (`memory/venture/assumptions`, `memory/venture/probes`, etc.) and the output path (`.canon/`).
- `parse_*` functions accept `Path` objects; testing requires real filesystem fixtures.
- If the source repo is restructured (e.g., `agentstack → synaplex` rename already happened; atlas canon paths will move similarly), the adapter breaks silently — no interface boundary to test against.

## Target interface

The stable interface the adapter should expose:

```python
def parse_assumption(text: str, meta: AdapterMeta) -> dict
def parse_probe(text: str, meta: AdapterMeta, decision_kind: str | None = None) -> list[dict]
def parse_evidence(text: str, meta: AdapterMeta) -> dict
def parse_decision(text: str, meta: AdapterMeta) -> dict
```

Where `AdapterMeta` carries what the adapter currently derives from the filesystem:

```python
@dataclass
class AdapterMeta:
    uri: str           # canonical source URI (e.g. "file:///path/to/file.md")
    content_hash: str  # sha256:… of the file content
    version: str       # explicit version string (not mtime)
    source_path: str   # for error messages only
```

`migrate.py` becomes the filesystem-aware caller:
- reads files, computes hashes, constructs `AdapterMeta`
- calls the pure-parse functions
- writes envelopes to `.canon/`

The adapter core (`emit.py`) imports no filesystem operations.

## Why not now

This is a structural refactor. The current test suite uses real-file fixtures;
switching to pure-text inputs would require rewriting all adapter tests.
The canon schema (v0.1.0) does not change — only the adapter calling convention.

This ADR is filed to document the target so the next session to touch
the adapter can refactor toward it incrementally.

## Defensive fix shipped this session

`migrate.py` already accepts `--venture` and `--schemas` path parameters.
No additional defensive changes were made to the parse interface this session
(the structural refactor is the right fix; partial measures add surface without
reducing coupling). This ADR is the follow-on action.

## Acceptance criteria for the full refactor

- `parse_*` functions in `emit.py` accept `text: str` and `meta: AdapterMeta`, not `Path`
- `emit.py` has no import of `pathlib`, `hashlib`, `os`, or any filesystem module
- `migrate.py` constructs `AdapterMeta` from path stat + hash before calling parse functions
- All existing tests pass with the new interface (fixtures provide text + meta, not paths)
- Adversarial review of the diff before merging
