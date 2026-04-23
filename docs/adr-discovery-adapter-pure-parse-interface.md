# ADR: Discovery adapter pure-parse interface

**Status**: accepted, pending scheduling
**Date**: 2026-04-23
**Author**: tick session 2026-04-23T17-37-15Z; status updated by session 65447b9d-3cb7-4584-bcf2-c058fd025791 on 2026-04-23 after post-fix review Finding C validated the premise.
**References**:
- adversarial review `.reviews/dcfd7e4-4d6050d-discovery-adapter-2026-04-23.md` Finding 3 (initial motivation)
- post-fix review `supervisor/.reviews/discovery-adapter-2f63ae5-post-fix-2026-04-23T17-59Z.md` Finding C (boundary already leaking; cross-file join in migrate.py)
- scope-expansion handoff `runtime/.handoff/skillfoundry-scope-expansion-plus-tail-items-2026-04-23T18-45Z.md`
- post-review-triage handoff `runtime/.handoff/skillfoundry-discovery-adapter-post-review-findings-2026-04-23T19-00Z.md`

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

## Status update — 2026-04-23 post-fix review

Post-fix review Finding C validated the premise: the boundary is already
leaking, not just at risk of leaking. `parse_probe()` only emits the
correct closure event when the caller injects `decision_kind` from a
separate decision file, and `migrate.py` compensates via a cross-directory
join before calling `parse_probe()`. The "parse one markdown file" API
is already a repository adapter masquerading as a file parser. Finding B
(pre-pass swallowing decision-header parse failures) is a second symptom
of the same leak — a cross-file dependency in a layer nominally owned by
the parse core.

The ADR is therefore upgraded from `proposed` to `accepted, pending
scheduling`. The refactor is the right direction; scheduling depends on
principal capacity to sequence it alongside the Finding A
(3-claims-per-assumption) spec pressure-test, which may change the parse
interface signature anyway.

## Why not immediately

This is a structural refactor. The current test suite uses real-file fixtures;
switching to pure-text inputs would require rewriting all adapter tests.
The canon schema (v0.1.0) does not change — only the adapter calling convention.

**Interim**: until this refactor lands, every cross-file dependency added
to the adapter (pre-passes, join maps, shared lookups) is ADR-class. Don't
add new file-spanning logic without either (a) implementing this ADR first
or (b) documenting the new cross-file dependency explicitly so it can be
untangled later. The Finding B pre-pass is grandfathered.

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
