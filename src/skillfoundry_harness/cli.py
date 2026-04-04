"""Console entrypoints for the Skillfoundry harness."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
import sys

from .bootstrap import fork_context_lineage, init_context_lineage
from .runtime import Runtime
from .validation import ValidationError, validate_bundle_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skillfoundry")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a context repo or bundle")
    validate_parser.add_argument("path", nargs="?", default=".")
    validate_parser.add_argument(
        "--bundle",
        action="store_true",
        help="Interpret path as a single bundle JSON file instead of a context repo",
    )

    describe_parser = subparsers.add_parser("describe", help="Describe a validated context repo contract")
    describe_parser.add_argument("path", nargs="?", default=".")

    frontdoor_parser = subparsers.add_parser("frontdoor", help="Render the progressive-disclosure front door")
    frontdoor_parser.add_argument("path", nargs="?", default=".")
    frontdoor_parser.add_argument("--max-chars", type=int, default=200)

    init_context_parser = subparsers.add_parser("init-context", help="Initialize a local git-backed context lineage")
    init_context_parser.add_argument("path")
    init_context_parser.add_argument("--agent-id", required=True)
    init_context_parser.add_argument("--name", required=True)
    init_context_parser.add_argument("--mission", default="")

    fork_context_parser = subparsers.add_parser("fork-context", help="Fork one context lineage into another local checkout")
    fork_context_parser.add_argument("source_path")
    fork_context_parser.add_argument("target_path")
    fork_context_parser.add_argument("--agent-id")
    fork_context_parser.add_argument("--name")

    branch_parser = subparsers.add_parser("branch-describe", help="Describe a bounded branch-local workspace")
    branch_parser.add_argument("repo_path")
    branch_parser.add_argument("branch")

    validation_parser = subparsers.add_parser("record-validation", help="Create a durable validation artifact")
    validation_parser.add_argument("repo_path")
    validation_parser.add_argument("--kind", required=True)
    validation_parser.add_argument("--status", required=True)
    validation_parser.add_argument("--evidence-path", action="append", default=[])
    validation_parser.add_argument("--summary", default="")
    validation_parser.add_argument("--thread-id")
    validation_parser.add_argument("--turn-id")
    validation_parser.add_argument("--reviewer")

    list_bundles_parser = subparsers.add_parser("list-bundles", help="List validated bundles in a context repo")
    list_bundles_parser.add_argument("repo_path")

    show_bundle_parser = subparsers.add_parser("show-bundle", help="Show one validated bundle by bundle_id")
    show_bundle_parser.add_argument("repo_path")
    show_bundle_parser.add_argument("bundle_id")

    worktree_create_parser = subparsers.add_parser("worktree-create", help="Create a managed git worktree for isolated execution")
    worktree_create_parser.add_argument("repo_path")
    worktree_create_parser.add_argument("worktree_name")
    worktree_create_parser.add_argument("--base-ref", default="HEAD")
    worktree_create_parser.add_argument("--branch")

    worktree_list_parser = subparsers.add_parser("worktree-list", help="List managed git worktrees")
    worktree_list_parser.add_argument("repo_path")

    worktree_remove_parser = subparsers.add_parser("worktree-remove", help="Remove a managed git worktree")
    worktree_remove_parser.add_argument("repo_path")
    worktree_remove_parser.add_argument("worktree_name")
    worktree_remove_parser.add_argument("--force", action="store_true")

    propose_parser = subparsers.add_parser("propose-memory", help="Create an explicit proposal to update canonical memory")
    propose_parser.add_argument("repo_path")
    propose_parser.add_argument("target_path")
    propose_parser.add_argument("content_file")
    propose_parser.add_argument("--rationale", required=True)
    propose_parser.add_argument("--thread-id")
    propose_parser.add_argument("--turn-id")
    propose_parser.add_argument("--validation-id", action="append", default=[])

    branch_propose_parser = subparsers.add_parser(
        "propose-branch-memory",
        help="Create a proposal from branch-local draft memory into canonical memory",
    )
    branch_propose_parser.add_argument("repo_path")
    branch_propose_parser.add_argument("branch")
    branch_propose_parser.add_argument("branch_memory_path")
    branch_propose_parser.add_argument("target_path")
    branch_propose_parser.add_argument("--rationale", required=True)
    branch_propose_parser.add_argument("--thread-id")
    branch_propose_parser.add_argument("--turn-id")
    branch_propose_parser.add_argument("--validation-id", action="append", default=[])

    show_proposal_parser = subparsers.add_parser("show-proposal", help="Show proposal metadata and review artifact paths")
    show_proposal_parser.add_argument("repo_path")
    show_proposal_parser.add_argument("proposal_id")

    approve_parser = subparsers.add_parser("approve-proposal", help="Approve a memory proposal before apply")
    approve_parser.add_argument("repo_path")
    approve_parser.add_argument("proposal_id")
    approve_parser.add_argument("--reviewer", required=True)
    approve_parser.add_argument("--notes", default="")
    approve_parser.add_argument("--validation-id", action="append", default=[])
    approve_parser.add_argument("--thread-id")
    approve_parser.add_argument("--turn-id")

    apply_parser = subparsers.add_parser("apply-proposal", help="Apply an approved proposal into canonical memory")
    apply_parser.add_argument("repo_path")
    apply_parser.add_argument("proposal_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "validate":
            if args.bundle:
                result = validate_bundle_file(args.path)
                print(f"OK {result.path}: {result.message}")
                return 0

            runtime = Runtime.open(args.path)
            for result in runtime.validate():
                print(f"OK {result.path}: {result.message}")
            return 0
        if args.command == "describe":
            runtime = Runtime.open(args.path)
            runtime.validate()
            for key, value in runtime.describe().items():
                print(f"{key}={value}")
            return 0
        if args.command == "frontdoor":
            runtime = Runtime.open(args.path)
            runtime.validate()
            snapshot = runtime.frontdoor_snapshot(max_chars=args.max_chars)
            for entry in snapshot["pinned"]:
                print(f"[PINNED] {entry['path']}")
                print(entry["preview"])
            for path in snapshot["discoverable"]:
                print(f"[DISCOVERABLE] {path}")
            return 0
        if args.command == "init-context":
            repository = init_context_lineage(
                args.path,
                agent_id=args.agent_id,
                name=args.name,
                mission=args.mission or None,
            )
            print(f"root={repository.root}")
            print(f"agent_id={repository.config.agent_id}")
            print(f"name={repository.config.name}")
            return 0
        if args.command == "fork-context":
            repository = fork_context_lineage(
                args.source_path,
                args.target_path,
                agent_id=args.agent_id,
                name=args.name,
            )
            print(f"root={repository.root}")
            print(f"agent_id={repository.config.agent_id}")
            print(f"name={repository.config.name}")
            return 0
        if args.command == "branch-describe":
            runtime = Runtime.open(args.repo_path)
            runtime.validate()
            snapshot = runtime.branch_workspace(args.branch).snapshot()
            for key, value in snapshot.items():
                print(f"{key}={value}")
            return 0
        if args.command == "record-validation":
            runtime = Runtime.open(args.repo_path)
            runtime.validate()
            artifact = runtime.create_validation_artifact(
                kind=args.kind,
                status=args.status,
                evidence_paths=args.evidence_path,
                summary=args.summary,
                thread_id=args.thread_id,
                turn_id=args.turn_id,
                reviewer=args.reviewer,
            )
            print(f"validation_id={artifact.validation_id}")
            print(f"kind={artifact.kind}")
            print(f"status={artifact.status}")
            return 0
        if args.command == "list-bundles":
            runtime = Runtime.open(args.repo_path)
            runtime.validate()
            for bundle in runtime.list_bundles():
                snapshot = bundle.snapshot()
                print(f"bundle_id={snapshot['bundle_id']}")
                print(f"path={snapshot['path']}")
                print(f"promotion_status={snapshot['promotion_status']}")
            return 0
        if args.command == "show-bundle":
            runtime = Runtime.open(args.repo_path)
            runtime.validate()
            bundle = runtime.load_bundle(args.bundle_id)
            for key, value in bundle.snapshot().items():
                print(f"{key}={value}")
            return 0
        if args.command == "worktree-create":
            runtime = Runtime.open(args.repo_path)
            runtime.validate()
            worktree = runtime.create_worktree(args.worktree_name, base_ref=args.base_ref, branch=args.branch)
            for key, value in asdict(worktree).items():
                print(f"{key}={value}")
            return 0
        if args.command == "worktree-list":
            runtime = Runtime.open(args.repo_path)
            runtime.validate()
            for worktree in runtime.list_worktrees():
                print(f"worktree_name={worktree.worktree_name}")
                print(f"branch={worktree.branch}")
                print(f"path={worktree.path}")
                print(f"status={worktree.status}")
            return 0
        if args.command == "worktree-remove":
            runtime = Runtime.open(args.repo_path)
            runtime.validate()
            worktree = runtime.remove_worktree(args.worktree_name, force=args.force)
            for key, value in asdict(worktree).items():
                print(f"{key}={value}")
            return 0
        if args.command == "propose-memory":
            runtime = Runtime.open(args.repo_path)
            runtime.validate()
            content = Path(args.content_file).read_text()
            proposal = runtime.create_memory_proposal(
                target_path=args.target_path,
                content=content,
                rationale=args.rationale,
                thread_id=args.thread_id,
                turn_id=args.turn_id,
                validation_ids=args.validation_id,
            )
            print(f"proposal_id={proposal.proposal_id}")
            print(f"status={proposal.status}")
            print(f"target_path={proposal.target_path}")
            return 0
        if args.command == "propose-branch-memory":
            runtime = Runtime.open(args.repo_path)
            runtime.validate()
            proposal = runtime.create_memory_proposal_from_branch(
                branch=args.branch,
                branch_memory_path=args.branch_memory_path,
                target_path=args.target_path,
                rationale=args.rationale,
                thread_id=args.thread_id,
                turn_id=args.turn_id,
                validation_ids=args.validation_id,
            )
            print(f"proposal_id={proposal.proposal_id}")
            print(f"status={proposal.status}")
            print(f"target_path={proposal.target_path}")
            print(f"source_branch={proposal.source_branch}")
            return 0
        if args.command == "show-proposal":
            runtime = Runtime.open(args.repo_path)
            runtime.validate()
            proposal = runtime.load_proposal(args.proposal_id)
            for key, value in asdict(proposal).items():
                print(f"{key}={value}")
            return 0
        if args.command == "approve-proposal":
            runtime = Runtime.open(args.repo_path)
            runtime.validate()
            proposal = runtime.approve_proposal(
                args.proposal_id,
                reviewer=args.reviewer,
                notes=args.notes,
                validation_ids=args.validation_id,
                thread_id=getattr(args, "thread_id", None),
                turn_id=getattr(args, "turn_id", None),
            )
            print(f"proposal_id={proposal.proposal_id}")
            print(f"status={proposal.status}")
            return 0
        if args.command == "apply-proposal":
            runtime = Runtime.open(args.repo_path)
            runtime.validate()
            proposal = runtime.apply_proposal(args.proposal_id)
            print(f"proposal_id={proposal.proposal_id}")
            print(f"status={proposal.status}")
            print(f"target_path={proposal.target_path}")
            return 0
    except (ValidationError, FileNotFoundError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
