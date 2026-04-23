Reading additional input from stdin...
OpenAI Codex v0.120.0 (research preview)
--------
workdir: /opt/workspace/projects/skillfoundry/skillfoundry-harness
model: gpt-5.4
provider: openai
approval: never
sandbox: read-only
reasoning effort: high
reasoning summaries: none
session id: 019dbb3e-13bf-7b03-bcdd-7b76da41010f
--------
user
Adversarial review of src/skillfoundry_harness/discovery_adapter/.

You are a skeptical reviewer. Read the target file carefully. Then produce a review with exactly these three sections:

1. **Most dangerous assumption** — the claim that if wrong, produces the largest blast radius.
2. **Missing failure mode** — what the design does not account for that is likely to happen in practice.
3. **Boundary most likely to be collapsed in practice** — where the nominal separation will erode under real use.

Cite specific line numbers. Be terse and concrete. End with a 1-2 sentence overall verdict. Under 500 words total. Do not edit any files.
codex
I’m inspecting `src/skillfoundry_harness/discovery_adapter/` to identify the concrete contract assumptions, failure paths, and boundary leaks, then I’ll give a terse adversarial review with line references only.
exec
/bin/bash -lc 'find src/skillfoundry_harness/discovery_adapter -maxdepth 2 -type f | sort' in /opt/workspace/projects/skillfoundry/skillfoundry-harness
 succeeded in 0ms:
src/skillfoundry_harness/discovery_adapter/MAPPING.md
src/skillfoundry_harness/discovery_adapter/__init__.py
src/skillfoundry_harness/discovery_adapter/__pycache__/__init__.cpython-312.pyc
src/skillfoundry_harness/discovery_adapter/__pycache__/emit.cpython-312.pyc
src/skillfoundry_harness/discovery_adapter/__pycache__/migrate.cpython-312.pyc
src/skillfoundry_harness/discovery_adapter/emit.py
src/skillfoundry_harness/discovery_adapter/migrate.py

exec
/bin/bash -lc 'rg --files src/skillfoundry_harness/discovery_adapter' in /opt/workspace/projects/skillfoundry/skillfoundry-harness
 succeeded in 0ms:
src/skillfoundry_harness/discovery_adapter/__init__.py
src/skillfoundry_harness/discovery_adapter/migrate.py
src/skillfoundry_harness/discovery_adapter/emit.py
src/skillfoundry_harness/discovery_adapter/MAPPING.md

codex
I found three source files and a mapping doc in the adapter. I’m reading the Python modules with line numbers now so the review can anchor on exact contract points rather than broad impressions.
exec
/bin/bash -lc 'nl -ba src/skillfoundry_harness/discovery_adapter/__init__.py' in /opt/workspace/projects/skillfoundry/skillfoundry-harness
 succeeded in 0ms:
     1	"""Canon adapter — emits discovery-framework canon envelopes from skillfoundry
     2	markdown records under `skillfoundry-valuation-context/memory/venture/`.
     3	
     4	The skillfoundry venture layer (CriticalAssumption / Probe / Evidence /
     5	Decision) is a markdown-first ontology: each object is a markdown file with
     6	a backtick-keyed header list (see README.md in each subdirectory). This
     7	adapter parses the markdown, extracts the structured metadata, and emits
     8	canon envelopes conforming to the L1 spec at
     9	/opt/workspace/projects/context-repository/spec/discovery-framework/ (v0.1.0).
    10	
    11	The adapter is additive — the markdown files remain the authoring surface
    12	and are unchanged.
    13	
    14	Public API:
    15	    parse_assumption(md_path)  -> canon Claim dict
    16	    parse_probe(md_path)       -> (phase_transition, methodology_log) events
    17	    parse_evidence(md_path)    -> canon Evidence dict
    18	    parse_decision(md_path)    -> canon Decision dict
    19	    emit_policy_quality_note() -> canon Policy capturing the quality-field note
    20	"""
    21	
    22	from .emit import (
    23	    EMITTER,
    24	    INSTANCE_ID,
    25	    LAYER,
    26	    SPEC_VERSION,
    27	    emit_policy_quality_note,
    28	    parse_assumption,
    29	    parse_decision,
    30	    parse_evidence,
    31	    parse_probe,
    32	)
    33	
    34	__all__ = [
    35	    "EMITTER",
    36	    "INSTANCE_ID",
    37	    "LAYER",
    38	    "SPEC_VERSION",
    39	    "emit_policy_quality_note",
    40	    "parse_assumption",
    41	    "parse_decision",
    42	    "parse_evidence",
    43	    "parse_probe",
    44	]

exec
/bin/bash -lc 'nl -ba src/skillfoundry_harness/discovery_adapter/emit.py' in /opt/workspace/projects/skillfoundry/skillfoundry-harness
 succeeded in 0ms:
     1	"""Parse skillfoundry venture markdown → canon envelopes.
     2	
     3	All four object types (CriticalAssumption, Probe, Evidence, Decision) use the
     4	same header shape: a markdown H1 title followed by a bulleted list of
     5	`- ``key``: ``value``` pairs, with optional prose sections below. This
     6	adapter extracts the header dict and maps to canon envelopes per MAPPING.md.
     7	
     8	No I/O — the caller writes envelopes to `.canon/` and runs the validator.
     9	"""
    10	
    11	from __future__ import annotations
    12	
    13	import hashlib
    14	import re
    15	from datetime import datetime, timezone
    16	from pathlib import Path
    17	from typing import Any
    18	
    19	
    20	SPEC_VERSION = "0.1.0"
    21	EMITTER = "L3:skillfoundry"
    22	LAYER = "L3"
    23	INSTANCE_ID = "skillfoundry-valuation-context"
    24	
    25	QUALITY_POLICY_ID = "skillfoundry.evidence_quality_note"
    26	QUALITY_POLICY_VERSION = "1"
    27	
    28	
    29	# --------------------------------------------------------------------------
    30	# Markdown header parser
    31	# --------------------------------------------------------------------------
    32	
    33	
    34	_HEADER_LINE = re.compile(
    35	    r"^\-\s+`(?P<key>[a-z_]+)`\s*:\s*`?(?P<val>[^`\n]*)`?\s*$"
    36	)
    37	_LIST_CONTINUATION = re.compile(r"^\s+\-\s+`?(?P<val>[^`\n]*)`?\s*$")
    38	
    39	
    40	def parse_header(md_text: str) -> dict[str, Any]:
    41	    """Extract `key: value` pairs from the markdown H1-adjacent bulleted list.
    42	
    43	    Supports list-valued fields (evidence_refs in decisions). Stops at the
    44	    first blank-after-list or the first H2 (`## `).
    45	
    46	    Returns a dict; unknown keys pass through.
    47	    """
    48	    lines = md_text.splitlines()
    49	    out: dict[str, Any] = {}
    50	    current_key: str | None = None
    51	    in_block = False
    52	
    53	    for line in lines:
    54	        # Start of header block: first bulleted key-value line
    55	        m = _HEADER_LINE.match(line)
    56	        if m:
    57	            in_block = True
    58	            current_key = m.group("key")
    59	            val = m.group("val").strip()
    60	            # Bare "(open)" / "(empty)" / etc. become None
    61	            if val in ("", "(open)", "(empty)", "(n/a)", "null"):
    62	                val = None
    63	            # Line with no value content (just the key and a colon on its own)
    64	            out[current_key] = val
    65	            continue
    66	
    67	        # Continuation inside a list-valued key
    68	        if in_block and current_key:
    69	            cm = _LIST_CONTINUATION.match(line)
    70	            if cm:
    71	                v = cm.group("val").strip()
    72	                if not isinstance(out.get(current_key), list):
    73	                    # Convert from singleton to list if needed
    74	                    prev = out[current_key]
    75	                    out[current_key] = [] if prev in (None, "", "(empty)") else [prev]
    76	                out[current_key].append(v)
    77	                continue
    78	
    79	        # Blank line during the block: keep going if the next line is a
    80	        # continuation or another header entry; break otherwise.
    81	        if in_block and line.strip() == "":
    82	            # Peek ahead isn't easy in a for-loop; just continue. The break
    83	            # is handled by the H2 check below.
    84	            continue
    85	
    86	        # End the block on H2
    87	        if in_block and line.startswith("## "):
    88	            break
    89	        if in_block and not line.startswith("-") and not line.startswith(" ") and line.strip() != "":
    90	            # First non-list non-blank non-H2 prose line ends the block.
    91	            break
    92	
    93	    return out
    94	
    95	
    96	# --------------------------------------------------------------------------
    97	# Envelope helpers
    98	# --------------------------------------------------------------------------
    99	
   100	
   101	def _iso(ts: str | datetime | None, default: str | None = None) -> str:
   102	    if ts is None and default is None:
   103	        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
   104	    if ts is None:
   105	        return default  # type: ignore[return-value]
   106	    if isinstance(ts, str):
   107	        try:
   108	            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
   109	        except ValueError:
   110	            return ts  # already in canonical form we can't reparse; trust
   111	    else:
   112	        dt = ts
   113	    if dt.tzinfo is None:
   114	        dt = dt.replace(tzinfo=timezone.utc)
   115	    return dt.isoformat().replace("+00:00", "Z")
   116	
   117	
   118	def _sha256_file(path: Path) -> str:
   119	    h = hashlib.sha256()
   120	    with open(path, "rb") as f:
   121	        for chunk in iter(lambda: f.read(65536), b""):
   122	            h.update(chunk)
   123	    return f"sha256:{h.hexdigest()}"
   124	
   125	
   126	def _sha256_str(s: str) -> str:
   127	    return f"sha256:{hashlib.sha256(s.encode('utf-8')).hexdigest()}"
   128	
   129	
   130	def _default_exposure() -> dict[str, Any]:
   131	    """Skillfoundry venture probes run with negligible operational exposure
   132	    pre-transaction. Capital-at-risk is bounded by the probe's build cost
   133	    (already sunk); external exposure is information, not capital."""
   134	    return {
   135	        "capital_at_risk": 0,
   136	        "reversibility": "reversible",
   137	        "correlation_tags": ["skillfoundry-valuation"],
   138	        "time_to_realization": "P14D",
   139	        "blast_radius": "local",
   140	    }
   141	
   142	
   143	def _common_envelope(object_type: str, id_: str, emitted_at: str,
   144	                     role_declared_at: str | None = None,
   145	                     binding: str = "binding") -> dict[str, Any]:
   146	    return {
   147	        "id": id_,
   148	        "spec_version": SPEC_VERSION,
   149	        "object_type": object_type,
   150	        "emitted_at": emitted_at,
   151	        "emitter": EMITTER,
   152	        "layer": LAYER,
   153	        "roles": [object_type],
   154	        "role_declared_at": role_declared_at or emitted_at,
   155	        "binding": binding,
   156	        "sources": [],
   157	        "instance_id": INSTANCE_ID,
   158	    }
   159	
   160	
   161	def _artifact_pointer(md_path: Path, uri_base: str | None = None) -> dict[str, Any]:
   162	    md_path = Path(md_path)
   163	    uri = uri_base or f"file://{md_path}"
   164	    return {
   165	        "uri": uri,
   166	        "content_hash": _sha256_file(md_path),
   167	        "version": str(int(md_path.stat().st_mtime)),
   168	        "media_type": "text/markdown",
   169	    }
   170	
   171	
   172	# --------------------------------------------------------------------------
   173	# CriticalAssumption → Claim
   174	# --------------------------------------------------------------------------
   175	
   176	
   177	def parse_assumption(md_path: Path | str) -> dict[str, Any]:
   178	    """skillfoundry CriticalAssumption markdown → canon Claim envelope.
   179	
   180	    Canon Claim has a single `statement`. Skillfoundry assumptions carry
   181	    three component claims (problem_claim, economic_claim, channel_claim)
   182	    which together form one buyer story. We use `problem_claim` as the
   183	    primary statement (it is the falsifiable commercial claim); the
   184	    economic and channel claims are preserved in the markdown artifact
   185	    via hash-bound ArtifactPointer.
   186	
   187	    The `falsification_rule` prose becomes the sole entry in
   188	    `falsification_criteria`.
   189	    """
   190	    md_path = Path(md_path)
   191	    header = parse_header(md_path.read_text())
   192	
   193	    if "assumption_id" not in header or "problem_claim" not in header:
   194	        raise ValueError(f"{md_path}: missing assumption_id or problem_claim")
   195	
   196	    emitted = _iso(header.get("created_at"))
   197	    role_at = emitted
   198	    envelope = _common_envelope(
   199	        "Claim", header["assumption_id"], emitted, role_at,
   200	    )
   201	    envelope["statement"] = header["problem_claim"]
   202	    envelope["falsification_criteria"] = [
   203	        header.get("falsification_rule", "(no falsification rule provided)")
   204	    ]
   205	    envelope["thresholds"] = {}
   206	    envelope["exposure"] = _default_exposure()
   207	    envelope["artifact"] = _artifact_pointer(md_path)
   208	    return envelope
   209	
   210	
   211	# --------------------------------------------------------------------------
   212	# Probe → EventLogEntry (phase_transition + methodology_log)
   213	# --------------------------------------------------------------------------
   214	
   215	
   216	def parse_probe(md_path: Path | str) -> list[dict[str, Any]]:
   217	    """Probe markdown → list of EventLogEntry envelopes.
   218	
   219	    Emits:
   220	      1. phase_transition (draft → probe) at probe start
   221	      2. methodology_log with ArtifactPointer to the probe markdown
   222	      3. phase_transition (probe → promotion) if status is 'closed' and the
   223	         matching Decision has kind in {promote, kill}
   224	
   225	    Returns a list (not single envelope) because a probe emits multiple
   226	    events.
   227	    """
   228	    md_path = Path(md_path)
   229	    header = parse_header(md_path.read_text())
   230	
   231	    if "probe_id" not in header or "assumption_id" not in header:
   232	        raise ValueError(f"{md_path}: missing probe_id or assumption_id")
   233	
   234	    probe_id = header["probe_id"]
   235	    claim_id = header["assumption_id"]
   236	    started = _iso(header.get("started_at"))
   237	    ended_raw = header.get("ended_at")
   238	    ended = _iso(ended_raw) if ended_raw else None
   239	
   240	    artifact = _artifact_pointer(md_path)
   241	    events: list[dict[str, Any]] = []
   242	
   243	    # 1. phase_transition draft → probe
   244	    pt1 = _common_envelope(
   245	        "EventLogEntry", f"pt-{probe_id}-draft-probe", started, started,
   246	    )
   247	    pt1["event_kind"] = "phase_transition"
   248	    pt1["subject_id"] = claim_id
   249	    pt1["phase_transition"] = {
   250	        "claim_id": claim_id,
   251	        "from_phase": "draft",
   252	        "to_phase": "probe",
   253	    }
   254	    events.append(pt1)
   255	
   256	    # 2. methodology_log at probe entry (canon.md Phase Invariants require this)
   257	    ml = _common_envelope(
   258	        "EventLogEntry", f"ml-{probe_id}", started, started,
   259	    )
   260	    ml["event_kind"] = "methodology_log"
   261	    ml["subject_id"] = claim_id
   262	    ml["methodology_log"] = {
   263	        "artifact": artifact,
   264	        "summary": header.get("probe_type", "manual probe"),
   265	    }
   266	    events.append(ml)
   267	
   268	    # 3. (Optional) phase_transition probe → promotion on probe close
   269	    status = header.get("status")
   270	    if status == "closed" and ended:
   271	        pt2 = _common_envelope(
   272	            "EventLogEntry", f"pt-{probe_id}-probe-promotion", ended, ended,
   273	        )
   274	        pt2["event_kind"] = "phase_transition"
   275	        pt2["subject_id"] = claim_id
   276	        pt2["phase_transition"] = {
   277	            "claim_id": claim_id,
   278	            "from_phase": "probe",
   279	            "to_phase": "promotion",
   280	        }
   281	        events.append(pt2)
   282	
   283	    return events
   284	
   285	
   286	# --------------------------------------------------------------------------
   287	# Evidence → Evidence
   288	# --------------------------------------------------------------------------
   289	
   290	
   291	_TIER_ALIASES = {
   292	    # Skillfoundry writes the same 4 strings canon uses natively.
   293	    "internal_operational": "internal_operational",
   294	    "external_conversation": "external_conversation",
   295	    "external_commitment": "external_commitment",
   296	    "external_transaction": "external_transaction",
   297	}
   298	
   299	
   300	_POLARITY_MAP = {
   301	    "supports_assumption": "supports",
   302	    "contradicts_assumption": "contradicts",
   303	    "neutral": "neutral",
   304	    # Looser values observed in real files:
   305	    "lane_activation_only": "neutral",
   306	    "lane_activation": "neutral",
   307	    "activation_only": "neutral",
   308	}
   309	
   310	
   311	def parse_evidence(md_path: Path | str) -> dict[str, Any]:
   312	    """skillfoundry Evidence markdown → canon Evidence envelope."""
   313	    md_path = Path(md_path)
   314	    header = parse_header(md_path.read_text())
   315	
   316	    for required in ("evidence_id", "assumption_id", "evidence_class"):
   317	        if required not in header:
   318	            raise ValueError(f"{md_path}: missing {required}")
   319	
   320	    emitted = _iso(header.get("observed_at"))
   321	    envelope = _common_envelope(
   322	        "Evidence", header["evidence_id"], emitted, emitted,
   323	    )
   324	    envelope["claim_id"] = header["assumption_id"]
   325	    envelope["evidence_type"] = header.get("source_type", "unspecified")
   326	
   327	    tier_raw = header["evidence_class"]
   328	    envelope["tier"] = _TIER_ALIASES.get(tier_raw, "internal_operational")
   329	
   330	    supports_raw = header.get("supports", "neutral")
   331	    envelope["polarity"] = _POLARITY_MAP.get(supports_raw, "neutral")
   332	    envelope["observed_at"] = emitted
   333	    envelope["artifact"] = _artifact_pointer(md_path)
   334	    return envelope
   335	
   336	
   337	# --------------------------------------------------------------------------
   338	# Decision → Decision
   339	# --------------------------------------------------------------------------
   340	
   341	
   342	_DECISION_KIND_MAP = {
   343	    "continue": "continue",
   344	    "tighten": "continue",  # skillfoundry-specific variant; flagged in rationale
   345	    "pivot": "pivot",
   346	    "pause": "continue",  # non-terminal pause preserves the claim; rationale carries the nuance
   347	    "kill": "kill",
   348	    "promote": "promote",
   349	}
   350	
   351	
   352	def parse_decision(md_path: Path | str) -> dict[str, Any]:
   353	    """skillfoundry Decision markdown → canon Decision envelope.
   354	
   355	    Skillfoundry's `decision_type` enum is richer than canon's (tighten,
   356	    pause); the mapping folds them into the closest canon kind and
   357	    preserves the nuance in `rationale` with an explicit "[skillfoundry-
   358	    type=tighten]" prefix marker.
   359	    """
   360	    md_path = Path(md_path)
   361	    text = md_path.read_text()
   362	    header = parse_header(text)
   363	
   364	    for required in ("decision_id", "assumption_id", "decision_type", "timestamp"):
   365	        if required not in header:
   366	            raise ValueError(f"{md_path}: missing {required}")
   367	
   368	    emitted = _iso(header["timestamp"])
   369	    decision_type_raw = header["decision_type"]
   370	    kind = _DECISION_KIND_MAP.get(decision_type_raw, "continue")
   371	
   372	    envelope = _common_envelope(
   373	        "Decision", header["decision_id"], emitted, emitted,
   374	    )
   375	    envelope["kind"] = kind
   376	    envelope["candidate_claims"] = [header["assumption_id"]]
   377	    envelope["chosen_claim_id"] = header["assumption_id"]
   378	
   379	    ev_refs = header.get("evidence_refs")
   380	    if isinstance(ev_refs, str):
   381	        ev_refs = [ev_refs] if ev_refs else []
   382	    elif ev_refs is None:
   383	        ev_refs = []
   384	    envelope["cited_evidence"] = ev_refs
   385	
   386	    rationale = header.get("rationale", "(no rationale provided)")
   387	    if decision_type_raw != kind:
   388	        rationale = f"[skillfoundry-type={decision_type_raw}] {rationale}"
   389	    envelope["rationale"] = rationale
   390	
   391	    envelope["policies_in_force"] = [
   392	        {
   393	            "policy_id": QUALITY_POLICY_ID,
   394	            "version": QUALITY_POLICY_VERSION,
   395	            "class": "operational",
   396	        }
   397	    ]
   398	    envelope["exposure"] = _default_exposure()
   399	
   400	    if kind == "promote":
   401	        # skillfoundry decisions don't carry an explicit promotion_id;
   402	        # synthesize one from the decision id.
   403	        envelope["promotion_id"] = f"prom-{header['decision_id']}"
   404	
   405	    return envelope
   406	
   407	
   408	# --------------------------------------------------------------------------
   409	# Policy — quality-field note
   410	# --------------------------------------------------------------------------
   411	
   412	
   413	def emit_policy_quality_note(effective_from: str | datetime | None = None) -> dict[str, Any]:
   414	    """Policy capturing the semantics of skillfoundry's evidence_quality
   415	    field (weak|moderate|strong), which has no direct canon field.
   416	
   417	    canon.Evidence has `tier` (bindingness axis) but no quality axis. The
   418	    quality label is preserved in the markdown artifact via ArtifactPointer;
   419	    this Policy documents that interpretation so consumers can find it
   420	    mechanically.
   421	    """
   422	    ts = effective_from or datetime.now(timezone.utc)
   423	    emitted = _iso(ts) if not isinstance(ts, str) else ts
   424	
   425	    envelope = _common_envelope(
   426	        "Policy", QUALITY_POLICY_ID, emitted, emitted,
   427	    )
   428	    # Policy schema forbids instance_id
   429	    envelope.pop("instance_id", None)
   430	    envelope["class"] = "operational"
   431	    envelope["scope"] = f"L3:{INSTANCE_ID}"
   432	    envelope["field_path"] = "evidence.quality_label"
   433	    envelope["value"] = {
   434	        "location": "artifact body of each Evidence envelope",
   435	        "values": ["weak", "moderate", "strong"],
   436	        "note": (
   437	            "Skillfoundry markdown Evidence records carry an "
   438	            "`evidence_quality` label that canon does not model directly "
   439	            "(canon.Evidence has `tier` for bindingness, not for quality). "
   440	            "The label is preserved in the ArtifactPointer-referenced "
   441	            "markdown and can be extracted by re-parsing the artifact if "
   442	            "needed. Promoting quality to a first-class canon field "
   443	            "requires a canon spec bump (v0.2.0)."
   444	        ),
   445	    }
   446	    envelope["version"] = QUALITY_POLICY_VERSION
   447	    envelope["issuer"] = EMITTER
   448	    envelope["amendment_authority"] = [EMITTER, "human:evan"]
   449	    envelope["ratification_rule"] = {
   450	        "kind": "principal_signoff",
   451	        "signatories": ["human:evan"],
   452	    }
   453	    envelope["rollback_rule"] = {
   454	        "rules": [
   455	            {
   456	                "id": "canon_gains_quality_field",
   457	                "condition": (
   458	                    "canon.spec_version advances to include an Evidence.quality "
   459	                    "field, at which point this Policy's note is obsolete"
   460	                ),
   461	            }
   462	        ],
   463	        "precedence": ["canon_gains_quality_field"],
   464	    }
   465	    envelope["provenance"] = [
   466	        {"version": QUALITY_POLICY_VERSION, "effective_from": emitted}
   467	    ]
   468	    envelope["effective_from"] = emitted
   469	    envelope["effective_until"] = None
   470	    return envelope

exec
/bin/bash -lc 'nl -ba src/skillfoundry_harness/discovery_adapter/migrate.py' in /opt/workspace/projects/skillfoundry/skillfoundry-harness
 succeeded in 0ms:
     1	"""One-shot backfill: skillfoundry-valuation-context markdown → canon envelopes.
     2	
     3	Usage:
     4	    python -m skillfoundry_harness.discovery_adapter.migrate \\
     5	        --venture /opt/workspace/projects/skillfoundry/skillfoundry-valuation-context \\
     6	        [--dry-run]
     7	
     8	Reads every assumption, probe, evidence, decision markdown under
     9	`memory/venture/` and emits canon envelopes to `.canon/`.
    10	
    11	Validates every envelope against the L1 discovery-framework JSON Schemas at
    12	`/opt/workspace/projects/context-repository/spec/discovery-framework/schemas/`.
    13	
    14	Exit codes:
    15	    0 — all envelopes valid
    16	    1 — some envelopes failed validation
    17	    2 — adapter / schema loading failure
    18	"""
    19	
    20	from __future__ import annotations
    21	
    22	import argparse
    23	import json
    24	import sys
    25	import traceback
    26	from pathlib import Path
    27	
    28	from skillfoundry_harness.discovery_adapter.emit import (
    29	    QUALITY_POLICY_ID,
    30	    emit_policy_quality_note,
    31	    parse_assumption,
    32	    parse_decision,
    33	    parse_evidence,
    34	    parse_probe,
    35	)
    36	
    37	
    38	DEFAULT_SCHEMA_DIR = Path(
    39	    "/opt/workspace/projects/context-repository/spec/discovery-framework/schemas"
    40	)
    41	
    42	
    43	def _load_schema_registry(schema_dir: Path):
    44	    try:
    45	        from jsonschema import Draft202012Validator
    46	        from referencing import Registry, Resource
    47	    except Exception as exc:  # pragma: no cover
    48	        print(f"FATAL: jsonschema + referencing required: {exc}", file=sys.stderr)
    49	        raise
    50	
    51	    resources = []
    52	    schemas: dict[str, dict] = {}
    53	    for p in sorted(schema_dir.glob("*.schema.json")):
    54	        with open(p) as f:
    55	            body = json.load(f)
    56	        schemas[p.name] = body
    57	        resources.append((body["$id"], Resource.from_contents(body)))
    58	    for fname, body in schemas.items():
    59	        resources.append((fname, Resource.from_contents(body)))
    60	
    61	    registry = Registry().with_resources(resources)
    62	    return {
    63	        body["title"]: Draft202012Validator(body, registry=registry)
    64	        for body in schemas.values()
    65	        if "title" in body
    66	    }
    67	
    68	
    69	def _validate(envelope: dict, validators: dict, object_type: str) -> list[str]:
    70	    v = validators.get(object_type)
    71	    if not v:
    72	        return [f"no validator for {object_type!r}"]
    73	    errors = sorted(v.iter_errors(envelope), key=lambda e: e.path)
    74	    return [
    75	        f"{'/'.join(str(p) for p in err.absolute_path)}: {err.message}"
    76	        for err in errors
    77	    ]
    78	
    79	
    80	def _write_envelope(envelope: dict, dest: Path, dry_run: bool) -> None:
    81	    if dry_run:
    82	        return
    83	    dest.parent.mkdir(parents=True, exist_ok=True)
    84	    tmp = dest.with_suffix(dest.suffix + ".tmp")
    85	    with open(tmp, "w") as f:
    86	        json.dump(envelope, f, indent=2, sort_keys=True)
    87	    tmp.replace(dest)
    88	
    89	
    90	def _canon_dir(venture_root: Path) -> Path:
    91	    d = venture_root / ".canon"
    92	    d.mkdir(parents=True, exist_ok=True)
    93	    for sub in ("claims", "evidence", "decisions", "event_log", "policies"):
    94	        (d / sub).mkdir(parents=True, exist_ok=True)
    95	    return d
    96	
    97	
    98	def migrate(venture_root: Path, schema_dir: Path, dry_run: bool) -> int:
    99	    venture_root = Path(venture_root)
   100	    memory_venture = venture_root / "memory" / "venture"
   101	    if not memory_venture.is_dir():
   102	        print(f"no memory/venture/ under {venture_root}", file=sys.stderr)
   103	        return 2
   104	
   105	    canon_root = _canon_dir(venture_root)
   106	    validators = _load_schema_registry(schema_dir)
   107	
   108	    counts = {"claims": [0, 0], "evidence": [0, 0],
   109	              "decisions": [0, 0], "events": [0, 0], "policies": [0, 0]}
   110	
   111	    # 1) Policy (quality-note)
   112	    pol = emit_policy_quality_note()
   113	    errs = _validate(pol, validators, "Policy")
   114	    if errs:
   115	        counts["policies"][1] += 1
   116	        print(f"[POLICY] {QUALITY_POLICY_ID}: {errs}", file=sys.stderr)
   117	    else:
   118	        counts["policies"][0] += 1
   119	        _write_envelope(
   120	            pol, canon_root / "policies" / f"{QUALITY_POLICY_ID}.json", dry_run,
   121	        )
   122	
   123	    # 2) Claims
   124	    for p in sorted((memory_venture / "assumptions").glob("*.md")):
   125	        if p.name.upper() in {"README.MD"} or p.name.startswith("TEMPLATE"):
   126	            continue
   127	        try:
   128	            env = parse_assumption(p)
   129	        except Exception as exc:
   130	            counts["claims"][1] += 1
   131	            print(f"[CLAIM-PARSE] {p.name}: {exc}", file=sys.stderr)
   132	            continue
   133	        errs = _validate(env, validators, "Claim")
   134	        if errs:
   135	            counts["claims"][1] += 1
   136	            print(f"[CLAIM] {env.get('id', p.name)}: {errs}", file=sys.stderr)
   137	            continue
   138	        counts["claims"][0] += 1
   139	        _write_envelope(env, canon_root / "claims" / f"{env['id']}.json", dry_run)
   140	
   141	    # 3) Probes → EventLogEntry
   142	    for p in sorted((memory_venture / "probes").glob("*.md")):
   143	        if p.name.upper() == "README.MD" or p.name.startswith("TEMPLATE"):
   144	            continue
   145	        try:
   146	            events = parse_probe(p)
   147	        except Exception as exc:
   148	            counts["events"][1] += 1
   149	            print(f"[PROBE-PARSE] {p.name}: {exc}", file=sys.stderr)
   150	            continue
   151	        for env in events:
   152	            errs = _validate(env, validators, "EventLogEntry")
   153	            if errs:
   154	                counts["events"][1] += 1
   155	                print(f"[EVENT] {env.get('id', p.name)}: {errs}", file=sys.stderr)
   156	                continue
   157	            counts["events"][0] += 1
   158	            _write_envelope(
   159	                env, canon_root / "event_log" / f"{env['id']}.json", dry_run,
   160	            )
   161	
   162	    # 4) Evidence
   163	    for p in sorted((memory_venture / "evidence").glob("*.md")):
   164	        if p.name.upper() == "README.MD" or p.name.startswith("TEMPLATE"):
   165	            continue
   166	        try:
   167	            env = parse_evidence(p)
   168	        except Exception as exc:
   169	            counts["evidence"][1] += 1
   170	            print(f"[EVIDENCE-PARSE] {p.name}: {exc}", file=sys.stderr)
   171	            continue
   172	        errs = _validate(env, validators, "Evidence")
   173	        if errs:
   174	            counts["evidence"][1] += 1
   175	            print(f"[EVIDENCE] {env.get('id', p.name)}: {errs}", file=sys.stderr)
   176	            continue
   177	        counts["evidence"][0] += 1
   178	        _write_envelope(env, canon_root / "evidence" / f"{env['id']}.json", dry_run)
   179	
   180	    # 5) Decisions
   181	    for p in sorted((memory_venture / "decisions").glob("*.md")):
   182	        if p.name.upper() == "README.MD" or p.name.startswith("TEMPLATE"):
   183	            continue
   184	        try:
   185	            env = parse_decision(p)
   186	        except Exception as exc:
   187	            counts["decisions"][1] += 1
   188	            print(f"[DECISION-PARSE] {p.name}: {exc}", file=sys.stderr)
   189	            continue
   190	        errs = _validate(env, validators, "Decision")
   191	        if errs:
   192	            counts["decisions"][1] += 1
   193	            print(f"[DECISION] {env.get('id', p.name)}: {errs}", file=sys.stderr)
   194	            continue
   195	        counts["decisions"][0] += 1
   196	        _write_envelope(env, canon_root / "decisions" / f"{env['id']}.json", dry_run)
   197	
   198	    total_bad = sum(v[1] for v in counts.values())
   199	    mode = "dry-run" if dry_run else "write"
   200	    parts = ", ".join(
   201	        f"{k}: {v[0]} ok / {v[1]} bad" for k, v in counts.items()
   202	    )
   203	    print(f"[{mode}] {parts}")
   204	    return 0 if total_bad == 0 else 1
   205	
   206	
   207	def main() -> int:
   208	    ap = argparse.ArgumentParser(description=__doc__)
   209	    ap.add_argument(
   210	        "--venture", type=Path,
   211	        default=Path(
   212	            "/opt/workspace/projects/skillfoundry/skillfoundry-valuation-context"
   213	        ),
   214	    )
   215	    ap.add_argument("--schemas", type=Path, default=DEFAULT_SCHEMA_DIR)
   216	    ap.add_argument("--dry-run", action="store_true")
   217	    args = ap.parse_args()
   218	
   219	    try:
   220	        return migrate(args.venture, args.schemas, args.dry_run)
   221	    except Exception:
   222	        traceback.print_exc()
   223	        return 2
   224	
   225	
   226	if __name__ == "__main__":
   227	    sys.exit(main())

exec
/bin/bash -lc 'nl -ba src/skillfoundry_harness/discovery_adapter/MAPPING.md' in /opt/workspace/projects/skillfoundry/skillfoundry-harness
 succeeded in 0ms:
     1	# Skillfoundry → canon mapping (v1)
     2	
     3	This document explains the skillfoundry-valuation-context markdown → L1
     4	discovery-framework canon mapping implemented in `emit.py`.
     5	
     6	Canon spec: **0.1.0** (`/opt/workspace/projects/context-repository/spec/discovery-framework/`).
     7	
     8	## Object mappings
     9	
    10	### CriticalAssumption → Claim
    11	
    12	Skillfoundry assumptions carry three component claims
    13	(`problem_claim`, `economic_claim`, `channel_claim`). Canon Claim has a
    14	single `statement`. Mapping: **statement = problem_claim** (the falsifiable
    15	commercial claim). The other two are preserved in the markdown artifact via
    16	hash-bound ArtifactPointer — downstream consumers who need the full buyer
    17	story re-parse the markdown.
    18	
    19	| Markdown key | Canon Claim field | Transform |
    20	|---|---|---|
    21	| `assumption_id` | `id` | identity (prose slug) |
    22	| `problem_claim` | `statement` | identity |
    23	| `falsification_rule` | `falsification_criteria` | wrap as `[str]` |
    24	| `created_at` | `emitted_at`, `role_declared_at` | ISO normalize |
    25	| `status` | (not on Claim) | emitted as EventLogEntry.phase_transition |
    26	| `economic_claim`, `channel_claim`, `buyer_role`, `owner`, `next_probe_id` | (not mapped) | preserved in artifact |
    27	
    28	**Adapter-supplied canon fields:**
    29	`spec_version=0.1.0`, `object_type=Claim`, `emitter=L3:skillfoundry`,
    30	`layer=L3`, `roles=[Claim]`, `binding=binding`, `sources=[]`,
    31	`exposure=_default_exposure()`, `artifact=ArtifactPointer` (sha256 of file),
    32	`instance_id=skillfoundry-valuation-context`.
    33	
    34	### Probe → EventLogEntry (multiple)
    35	
    36	Skillfoundry probes are operational events, not canon objects. Each probe
    37	emits up to three canon EventLogEntry envelopes:
    38	
    39	1. `phase_transition` (draft → probe) at `started_at`
    40	2. `methodology_log` with ArtifactPointer to the probe markdown (per
    41	   canon.md Phase Invariants: "Methodology log entry required on entry to probe")
    42	3. `phase_transition` (probe → promotion) at `ended_at`, only when `status=closed`
    43	
    44	| Markdown key | Canon field | Notes |
    45	|---|---|---|
    46	| `probe_id` | event id prefix (`pt-<probe_id>-…`, `ml-<probe_id>`) | |
    47	| `assumption_id` | `phase_transition.claim_id` + `subject_id` | |
    48	| `started_at` | first event `emitted_at` + `role_declared_at` | |
    49	| `ended_at` | second-transition `emitted_at` (if closed) | |
    50	| `probe_type` | `methodology_log.summary` | free-form summary |
    51	
    52	Probes fields not mapped (`probe_type` enum, `artifact_class`,
    53	`offer_presented`, `target_persona`, `target_evidence_class`,
    54	`minimum_evidence_quality`, `success_rule`, `falsification_rule`, `owner`)
    55	live in the artifact body.
    56	
    57	**Outlier**: `probes/preflight-distribution-signal.md` uses a prose/bold
    58	format rather than the canonical backtick-key-value header and does NOT
    59	parse. Skillfoundry PM action item: reformat that file to match the
    60	canonical probe header shape used by
    61	`probes/launch-compliance-intelligence-manual-offer.md` and
    62	`probes/launchpad-lint-agenticmarket-live-listing.md`.
    63	
    64	### Evidence → Evidence
    65	
    66	Skillfoundry's `evidence_class` enum is **identical** to canon's `tier`
    67	enum — canon inherited the 4-tier hierarchy from skillfoundry's earlier
    68	work. Direct map.
    69	
    70	| Markdown key | Canon Evidence field | Transform |
    71	|---|---|---|
    72	| `evidence_id` | `id` | identity |
    73	| `assumption_id` | `claim_id` | identity |
    74	| `evidence_class` | `tier` | identity (enum alias table in `_TIER_ALIASES`) |
    75	| `source_type` | `evidence_type` | identity (domain-owned free-form string) |
    76	| `supports` | `polarity` | `supports_assumption→supports`, `contradicts_assumption→contradicts`, `lane_activation_only→neutral`, else `neutral` |
    77	| `observed_at` | `emitted_at`, `observed_at`, `role_declared_at` | ISO normalize |
    78	
    79	Fields preserved in artifact only: `evidence_quality` (weak|moderate|
    80	strong), `source_identity`, `summary`, `raw_pointer`, `confidence`.
    81	
    82	### Decision → Decision
    83	
    84	Skillfoundry's `decision_type` enum is richer than canon's; the mapping
    85	folds skillfoundry-specific types into the closest canon kind and
    86	prepends a `[skillfoundry-type=<raw>]` marker to `rationale` so the
    87	nuance is mechanically discoverable.
    88	
    89	| `decision_type` | canon `kind` |
    90	|---|---|
    91	| `continue` | `continue` |
    92	| `tighten` | `continue` (rationale flagged `[skillfoundry-type=tighten]`) |
    93	| `pivot` | `pivot` |
    94	| `pause` | `continue` (rationale flagged `[skillfoundry-type=pause]`) |
    95	| `kill` | `kill` |
    96	| `promote` | `promote` |
    97	
    98	| Markdown key | Canon Decision field | Transform |
    99	|---|---|---|
   100	| `decision_id` | `id` | identity |
   101	| `assumption_id` | `candidate_claims[0]`, `chosen_claim_id` | identity |
   102	| `decision_type` | `kind` | via table above |
   103	| `evidence_refs` | `cited_evidence` | list pass-through |
   104	| `rationale` | `rationale` | prepended with type-marker if lossy |
   105	| `timestamp` | `emitted_at`, `role_declared_at` | ISO normalize |
   106	
   107	Adapter-supplied: `policies_in_force` references the quality-note Policy
   108	(`skillfoundry.evidence_quality_note` v1); `exposure` uses the default
   109	envelope; `promotion_id` synthesized as `prom-<decision_id>` when
   110	`kind=promote`.
   111	
   112	## Policy: the quality-field note
   113	
   114	Canon has no `quality` field on Evidence; skillfoundry's
   115	`evidence_quality` (weak|moderate|strong) is preserved in the artifact
   116	only. The adapter emits a Policy envelope documenting this so future
   117	consumers find the semantic locus mechanically.
   118	
   119	Rollback condition: canon spec gains a first-class quality field (spec
   120	v0.2.0+), at which point this Policy is obsolete and the adapter is
   121	updated to emit `Evidence.quality` directly.
   122	
   123	## Things deliberately not mapped
   124	
   125	- Skillfoundry's **promotion workflow** (`src/skillfoundry_harness/promotion.py`,
   126	  367 LOC of cryptographic memory-promotion) — that's a separate subsystem
   127	  (canonical-memory commit/approve/apply), distinct from canon Promotion.
   128	  Not touched by this adapter.
   129	- The **bundle layer** (`bundles/*.json`) — cross-repo coherence contracts;
   130	  canon doesn't model these.
   131	- `next_probe_id` and probe lineage — canon has no first-class
   132	  "claim-to-claim next-probe" edge. Lineage stays in the markdown.
   133	
   134	## Open questions (surfaced, not resolved)
   135	
   136	- **Assumption-as-three-claims**. Emitting three canon Claims per
   137	  skillfoundry assumption (problem/economic/channel) is architecturally
   138	  cleaner but canon has no native parent-child Claim link. Current choice
   139	  (one Claim with `statement=problem_claim`) is defensible but lossy. If
   140	  canon gains `related_claims[]` in a future version, revisit.
   141	- **Canon Promotion**. When a skillfoundry decision has `kind=promote`,
   142	  should the adapter also emit a canon Promotion envelope? Canon's
   143	  Promotion requires `external_validation` and `ceiling_check`; skillfoundry
   144	  decisions today don't carry structured external-validation attestation.
   145	  Deferred; see ADR-0026.

codex
1. **Most dangerous assumption**

`parse_probe()` assumes any closed probe with an `ended_at` has advanced the claim from `probe` to `promotion` and emits that phase transition unconditionally ([emit.py:268-281](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/emit.py:268)). The docstring claims this should depend on a matching Decision kind ([emit.py:220-223](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/emit.py:220)), but the code never looks at decisions. If that assumption is wrong, downstream phase state is systemically falsified: every merely “closed” probe becomes a promoted claim.

2. **Missing failure mode**

The adapter does not account for routine authoring/schema drift; it silently coerces unknown values into plausible defaults instead of failing. Unknown `evidence_class` becomes `internal_operational` ([emit.py:327-328](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/emit.py:327)), unknown `supports` becomes `neutral` ([emit.py:330-331](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/emit.py:330)), and unknown `decision_type` becomes `continue` ([emit.py:369-370](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/emit.py:369)). That is likely in practice because the parser already depends on a brittle header format ([emit.py:34-37](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/emit.py:34)), and the mapping doc admits at least one real probe file does not parse cleanly ([MAPPING.md:57-62](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/MAPPING.md:57)). The failure mode is not “adapter crashes”; it is “adapter emits valid-looking lies.”

3. **Boundary most likely to be collapsed in practice**

The nominal boundary between harness API and external context repository is already eroding into a filesystem contract. The “parse” layer is not pure parsing: it hashes files, reads mtimes as versions, and emits `file://` artifact URIs ([emit.py:118-123](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/emit.py:118), [emit.py:161-168](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/emit.py:161)). `migrate.py` then hardcodes the context repo layout and writes `.canon/` inside that workspace ([migrate.py:90-105](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/migrate.py:90)). In real use, the stable interface will stop being “canon envelopes from markdown” and become “this one repo’s path/layout/mtime semantics.”

Overall verdict: the adapter is compact, but it is currently more of a repo-specific transcoder than a stable harness boundary. The largest risk is silent semantic corruption: phase progression and enum coercion can both validate cleanly while being wrong.
tokens used
99,902
1. **Most dangerous assumption**

`parse_probe()` assumes any closed probe with an `ended_at` has advanced the claim from `probe` to `promotion` and emits that phase transition unconditionally ([emit.py:268-281](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/emit.py:268)). The docstring claims this should depend on a matching Decision kind ([emit.py:220-223](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/emit.py:220)), but the code never looks at decisions. If that assumption is wrong, downstream phase state is systemically falsified: every merely “closed” probe becomes a promoted claim.

2. **Missing failure mode**

The adapter does not account for routine authoring/schema drift; it silently coerces unknown values into plausible defaults instead of failing. Unknown `evidence_class` becomes `internal_operational` ([emit.py:327-328](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/emit.py:327)), unknown `supports` becomes `neutral` ([emit.py:330-331](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/emit.py:330)), and unknown `decision_type` becomes `continue` ([emit.py:369-370](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/emit.py:369)). That is likely in practice because the parser already depends on a brittle header format ([emit.py:34-37](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/emit.py:34)), and the mapping doc admits at least one real probe file does not parse cleanly ([MAPPING.md:57-62](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/MAPPING.md:57)). The failure mode is not “adapter crashes”; it is “adapter emits valid-looking lies.”

3. **Boundary most likely to be collapsed in practice**

The nominal boundary between harness API and external context repository is already eroding into a filesystem contract. The “parse” layer is not pure parsing: it hashes files, reads mtimes as versions, and emits `file://` artifact URIs ([emit.py:118-123](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/emit.py:118), [emit.py:161-168](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/emit.py:161)). `migrate.py` then hardcodes the context repo layout and writes `.canon/` inside that workspace ([migrate.py:90-105](/opt/workspace/projects/skillfoundry/skillfoundry-harness/src/skillfoundry_harness/discovery_adapter/migrate.py:90)). In real use, the stable interface will stop being “canon envelopes from markdown” and become “this one repo’s path/layout/mtime semantics.”

Overall verdict: the adapter is compact, but it is currently more of a repo-specific transcoder than a stable harness boundary. The largest risk is silent semantic corruption: phase progression and enum coercion can both validate cleanly while being wrong.
