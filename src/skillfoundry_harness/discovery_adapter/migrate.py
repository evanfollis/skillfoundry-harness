"""One-shot backfill: skillfoundry-valuation-context markdown → canon envelopes.

Usage:
    python -m skillfoundry_harness.discovery_adapter.migrate \\
        --venture /opt/workspace/projects/skillfoundry/skillfoundry-valuation-context \\
        [--dry-run]

Reads every assumption, probe, evidence, decision markdown under
`memory/venture/` and emits canon envelopes to `.canon/`.

Validates every envelope against the L1 discovery-framework JSON Schemas at
`/opt/workspace/projects/context-repository/spec/discovery-framework/schemas/`.

Exit codes:
    0 — all envelopes valid
    1 — some envelopes failed validation
    2 — adapter / schema loading failure
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

from skillfoundry_harness.discovery_adapter.emit import (
    QUALITY_POLICY_ID,
    _DECISION_KIND_MAP,
    emit_policy_quality_note,
    parse_assumption,
    parse_decision,
    parse_evidence,
    parse_header,
    parse_probe,
)


DEFAULT_SCHEMA_DIR = Path(
    "/opt/workspace/projects/context-repository/spec/discovery-framework/schemas"
)


def _load_schema_registry(schema_dir: Path):
    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
    except Exception as exc:  # pragma: no cover
        print(f"FATAL: jsonschema + referencing required: {exc}", file=sys.stderr)
        raise

    resources = []
    schemas: dict[str, dict] = {}
    for p in sorted(schema_dir.glob("*.schema.json")):
        with open(p) as f:
            body = json.load(f)
        schemas[p.name] = body
        resources.append((body["$id"], Resource.from_contents(body)))
    for fname, body in schemas.items():
        resources.append((fname, Resource.from_contents(body)))

    registry = Registry().with_resources(resources)
    return {
        body["title"]: Draft202012Validator(body, registry=registry)
        for body in schemas.values()
        if "title" in body
    }


def _validate(envelope: dict, validators: dict, object_type: str) -> list[str]:
    v = validators.get(object_type)
    if not v:
        return [f"no validator for {object_type!r}"]
    errors = sorted(v.iter_errors(envelope), key=lambda e: e.path)
    return [
        f"{'/'.join(str(p) for p in err.absolute_path)}: {err.message}"
        for err in errors
    ]


def _write_envelope(envelope: dict, dest: Path, dry_run: bool) -> None:
    if dry_run:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(envelope, f, indent=2, sort_keys=True)
    tmp.replace(dest)


def _canon_dir(venture_root: Path) -> Path:
    d = venture_root / ".canon"
    d.mkdir(parents=True, exist_ok=True)
    for sub in ("claims", "evidence", "decisions", "event_log", "policies"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    return d


def migrate(venture_root: Path, schema_dir: Path, dry_run: bool) -> int:
    venture_root = Path(venture_root)
    memory_venture = venture_root / "memory" / "venture"
    if not memory_venture.is_dir():
        print(f"no memory/venture/ under {venture_root}", file=sys.stderr)
        return 2

    canon_root = _canon_dir(venture_root)
    validators = _load_schema_registry(schema_dir)

    counts = {"claims": [0, 0], "evidence": [0, 0],
              "decisions": [0, 0], "events": [0, 0], "policies": [0, 0]}

    # Pre-pass: build probe_id → decision_kind map from decision headers.
    # Used so parse_probe() only emits the probe→promotion closure event when
    # the matching Decision has kind=="promote". Headers-only read, non-fatal.
    decision_kind_for_probe: dict[str, str] = {}
    for dp in sorted((memory_venture / "decisions").glob("*.md")):
        if dp.name.upper() == "README.MD" or dp.name.startswith("TEMPLATE"):
            continue
        try:
            dh = parse_header(dp.read_text())
            pid = dh.get("probe_id")
            dt_raw = dh.get("decision_type", "")
            if pid and dt_raw:
                decision_kind_for_probe[pid] = _DECISION_KIND_MAP.get(dt_raw, "")
        except Exception:
            pass  # non-fatal; the main decisions pass will report the error

    # 1) Policy (quality-note)
    pol = emit_policy_quality_note()
    errs = _validate(pol, validators, "Policy")
    if errs:
        counts["policies"][1] += 1
        print(f"[POLICY] {QUALITY_POLICY_ID}: {errs}", file=sys.stderr)
    else:
        counts["policies"][0] += 1
        _write_envelope(
            pol, canon_root / "policies" / f"{QUALITY_POLICY_ID}.json", dry_run,
        )

    # 2) Claims
    for p in sorted((memory_venture / "assumptions").glob("*.md")):
        if p.name.upper() in {"README.MD"} or p.name.startswith("TEMPLATE"):
            continue
        try:
            env = parse_assumption(p)
        except Exception as exc:
            counts["claims"][1] += 1
            print(f"[CLAIM-PARSE] {p.name}: {exc}", file=sys.stderr)
            continue
        errs = _validate(env, validators, "Claim")
        if errs:
            counts["claims"][1] += 1
            print(f"[CLAIM] {env.get('id', p.name)}: {errs}", file=sys.stderr)
            continue
        counts["claims"][0] += 1
        _write_envelope(env, canon_root / "claims" / f"{env['id']}.json", dry_run)

    # 3) Probes → EventLogEntry
    for p in sorted((memory_venture / "probes").glob("*.md")):
        if p.name.upper() == "README.MD" or p.name.startswith("TEMPLATE"):
            continue
        try:
            # Look up the matching Decision kind so parse_probe only emits
            # the probe→promotion event for actual promote decisions.
            ph = parse_header(p.read_text())
            dk = decision_kind_for_probe.get(ph.get("probe_id", ""))
            events = parse_probe(p, decision_kind=dk)
        except Exception as exc:
            counts["events"][1] += 1
            print(f"[PROBE-PARSE] {p.name}: {exc}", file=sys.stderr)
            continue
        for env in events:
            errs = _validate(env, validators, "EventLogEntry")
            if errs:
                counts["events"][1] += 1
                print(f"[EVENT] {env.get('id', p.name)}: {errs}", file=sys.stderr)
                continue
            counts["events"][0] += 1
            _write_envelope(
                env, canon_root / "event_log" / f"{env['id']}.json", dry_run,
            )

    # 4) Evidence
    for p in sorted((memory_venture / "evidence").glob("*.md")):
        if p.name.upper() == "README.MD" or p.name.startswith("TEMPLATE"):
            continue
        try:
            env = parse_evidence(p)
        except Exception as exc:
            counts["evidence"][1] += 1
            print(f"[EVIDENCE-PARSE] {p.name}: {exc}", file=sys.stderr)
            continue
        errs = _validate(env, validators, "Evidence")
        if errs:
            counts["evidence"][1] += 1
            print(f"[EVIDENCE] {env.get('id', p.name)}: {errs}", file=sys.stderr)
            continue
        counts["evidence"][0] += 1
        _write_envelope(env, canon_root / "evidence" / f"{env['id']}.json", dry_run)

    # 5) Decisions
    for p in sorted((memory_venture / "decisions").glob("*.md")):
        if p.name.upper() == "README.MD" or p.name.startswith("TEMPLATE"):
            continue
        try:
            env = parse_decision(p)
        except Exception as exc:
            counts["decisions"][1] += 1
            print(f"[DECISION-PARSE] {p.name}: {exc}", file=sys.stderr)
            continue
        errs = _validate(env, validators, "Decision")
        if errs:
            counts["decisions"][1] += 1
            print(f"[DECISION] {env.get('id', p.name)}: {errs}", file=sys.stderr)
            continue
        counts["decisions"][0] += 1
        _write_envelope(env, canon_root / "decisions" / f"{env['id']}.json", dry_run)

    total_bad = sum(v[1] for v in counts.values())
    mode = "dry-run" if dry_run else "write"
    parts = ", ".join(
        f"{k}: {v[0]} ok / {v[1]} bad" for k, v in counts.items()
    )
    print(f"[{mode}] {parts}")
    return 0 if total_bad == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--venture", type=Path,
        default=Path(
            "/opt/workspace/projects/skillfoundry/skillfoundry-valuation-context"
        ),
    )
    ap.add_argument("--schemas", type=Path, default=DEFAULT_SCHEMA_DIR)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        return migrate(args.venture, args.schemas, args.dry_run)
    except Exception:
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
