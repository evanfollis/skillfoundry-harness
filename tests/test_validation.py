from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from skillfoundry_harness import Runtime, fork_context_lineage, init_context_lineage
from skillfoundry_harness.validation import ValidationError, validate_bundle_file


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_REPO = REPO_ROOT / "tests" / "fixtures" / "minimal_context_repo"
FIXTURE_BUNDLE = FIXTURE_REPO / "bundles" / "minimal-context.json"
ROOT_SCHEMA = REPO_ROOT / "schemas" / "context-bundle.schema.json"
PACKAGE_SCHEMA = REPO_ROOT / "src" / "skillfoundry_harness" / "schemas" / "context-bundle.schema.json"


class ValidationTests(unittest.TestCase):
    def test_validate_bundle_file(self) -> None:
        result = validate_bundle_file(FIXTURE_BUNDLE)
        self.assertEqual(result.message, "bundle is valid")

    def test_runtime_validate_repo(self) -> None:
        runtime = Runtime.open(FIXTURE_REPO)
        results = runtime.validate()
        self.assertGreaterEqual(len(results), 2)
        self.assertEqual(runtime.repository.memory_dir.name, "memory")
        self.assertEqual(runtime.repository.artifacts_dir.name, "artifacts")
        self.assertEqual(runtime.repository.runs_dir.name, "runs")
        self.assertEqual(len(runtime.repository.writable_roots), 3)
        self.assertEqual(runtime.repository.config.frontdoor.pinned_paths, ("README.md", "memory/mission.md"))
        self.assertEqual(runtime.repository.config.promotion_policy.required_validation_kinds, ("canon-safe", "frontdoor-reviewed"))

    def test_frontdoor_snapshot(self) -> None:
        runtime = Runtime.open(FIXTURE_REPO)
        snapshot = runtime.frontdoor_snapshot(max_chars=80)
        self.assertEqual(snapshot["pinned"][0]["path"], "README.md")
        self.assertIn("Minimal Context Repo", snapshot["pinned"][0]["preview"])
        self.assertEqual(snapshot["discoverable"], ["bundles", "memory", "artifacts"])

    def test_init_context_lineage_creates_valid_git_backed_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "researcher-context"
            repository = init_context_lineage(
                repo_root,
                agent_id="researcher",
                name="Researcher Context",
                mission="Gather grounded evidence and refine current-state canon.",
            )

            self.assertEqual(repository.config.agent_id, "researcher")
            self.assertEqual((repo_root / "memory" / "mission.md").read_text(), "# Mission\n\nGather grounded evidence and refine current-state canon.\n")
            result = subprocess.run(
                ["git", "-C", str(repo_root), "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(result.stdout.strip(), "true")
            self.assertEqual(
                subprocess.run(
                    ["git", "-C", str(repo_root), "status", "--short"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip(),
                "",
            )

    def test_fork_context_lineage_clones_locally_without_origin(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source_root = Path(tmpdir) / "source"
            target_root = Path(tmpdir) / "forked"
            init_context_lineage(source_root, agent_id="researcher", name="Researcher Context")

            repository = fork_context_lineage(
                source_root,
                target_root,
                agent_id="designer",
                name="Designer Context",
            )

            self.assertEqual(repository.config.agent_id, "designer")
            self.assertEqual(repository.config.name, "Designer Context")
            origin_result = subprocess.run(
                ["git", "-C", str(target_root), "remote"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(origin_result.stdout.strip(), "")
            self.assertEqual(
                subprocess.run(
                    ["git", "-C", str(target_root), "status", "--short"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip(),
                "",
            )

    def test_repository_bounded_write_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            repository = Runtime.open(repo_root).repository

            artifact_path = repository.write_artifact_text("reports/summary.md", "artifact\n")

            self.assertEqual(artifact_path.read_text(), "artifact\n")
            self.assertFalse(hasattr(repository, "write_memory_text"))
            with self.assertRaises(ValueError):
                repository.resolve_memory_path("../escape.md")

    def test_validation_artifact_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            runtime = Runtime.open(repo_root)
            runtime.repository.write_artifact_text("checks/frontdoor.txt", "frontdoor ok\n")

            artifact = runtime.create_validation_artifact(
                kind="frontdoor-reviewed",
                status="passed",
                evidence_paths=["checks/frontdoor.txt"],
                summary="Front door remains concise.",
                reviewer="reviewer@example.com",
            )
            payload = json.loads((repo_root / "artifacts" / "validations" / f"{artifact.validation_id}.json").read_text())
            self.assertEqual(payload["kind"], "frontdoor-reviewed")
            self.assertEqual(payload["status"], "passed")

    def test_validation_artifact_requires_existing_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            runtime = Runtime.open(repo_root)
            with self.assertRaises(ValueError):
                runtime.create_validation_artifact(
                    kind="frontdoor-reviewed",
                    status="passed",
                    evidence_paths=["checks/missing.txt"],
                )

    def test_bundle_store_list_and_load(self) -> None:
        runtime = Runtime.open(FIXTURE_REPO)
        bundles = runtime.list_bundles()
        self.assertEqual(len(bundles), 1)
        self.assertEqual(bundles[0].bundle_id, "product-brief-v1")
        bundle = runtime.load_bundle("product-brief-v1")
        self.assertEqual(bundle.promotion.status, "candidate")
        self.assertEqual(bundle.content[0].entry_id, "goal")

    def test_branch_workspace_snapshot_and_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            branch = Runtime.open(repo_root).branch_workspace("research_branch")

            branch_memory_path = branch.write_memory_text("notes/hypothesis.md", "# Hypothesis\n\nTest the branch substrate.\n")
            branch_artifact_path = branch.write_artifact_text("logs/summary.md", "branch artifact\n")
            snapshot = branch.snapshot()

            self.assertEqual(branch_memory_path.read_text(), "# Hypothesis\n\nTest the branch substrate.\n")
            self.assertEqual(branch_artifact_path.read_text(), "branch artifact\n")
            self.assertEqual(snapshot["branch"], "research_branch")
            self.assertIn("artifacts/branches/research_branch/memory", snapshot["memory_dir"])
            with self.assertRaises(ValueError):
                branch.write_memory_text("../escape.md", "bad\n")

    def test_memory_promotion_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            runtime = Runtime.open(repo_root)
            validation_ids = self._create_required_validations(runtime)

            proposal = runtime.create_memory_proposal(
                target_path="notes/priority.md",
                content="# Priority\n\nShip the narrow front door.\n",
                rationale="Promote the clarified current priority into canon.",
                thread_id="thread_demo",
                turn_id="turn_demo",
                validation_ids=[validation_ids["frontdoor-reviewed"]],
            )
            self.assertEqual(proposal.status, "draft")
            candidate_path = repo_root / "artifacts" / proposal.candidate_artifact_path
            current_path = repo_root / "artifacts" / proposal.current_artifact_path
            diff_path = repo_root / "artifacts" / proposal.diff_artifact_path
            self.assertTrue(candidate_path.exists())
            self.assertTrue(current_path.exists())
            self.assertTrue(diff_path.exists())
            self.assertEqual(current_path.read_text(), "")
            self.assertIn("candidate/notes/priority.md", diff_path.read_text())

            approved = runtime.approve_proposal(
                proposal.proposal_id,
                reviewer="reviewer@example.com",
                notes="Looks consistent with current objective.",
                validation_ids=[validation_ids["frontdoor-reviewed"], validation_ids["canon-safe"]],
            )
            self.assertEqual(approved.status, "approved")
            self.assertEqual(len(approved.approval_refs), 1)

            applied = runtime.apply_proposal(proposal.proposal_id)
            self.assertEqual(applied.status, "applied")
            self.assertEqual(
                (repo_root / "memory" / "notes" / "priority.md").read_text(),
                "# Priority\n\nShip the narrow front door.\n",
            )
            proposal_payload = json.loads((repo_root / "artifacts" / "promotions" / proposal.proposal_id / "proposal.json").read_text())
            self.assertEqual(proposal_payload["status"], "applied")
            self.assertEqual(proposal_payload["reviewer"], "reviewer@example.com")
            self.assertEqual(
                {entry["artifact_id"] for entry in proposal_payload["validation_refs"]},
                {validation_ids["frontdoor-reviewed"], validation_ids["canon-safe"]},
            )
            self.assertEqual(proposal_payload["current_artifact_path"], proposal.current_artifact_path)
            self.assertEqual(proposal_payload["diff_artifact_path"], proposal.diff_artifact_path)
            approval_payload = json.loads(
                (repo_root / "artifacts" / "approvals" / f"{approved.approval_refs[0].artifact_id}.json").read_text()
            )
            self.assertEqual(approval_payload["proposal_id"], proposal.proposal_id)
            self.assertEqual(approval_payload["status"], "approved")
            self.assertEqual(approval_payload["proposal_change_sha256"], proposal_payload["change_sha256"])

    def test_proposal_snapshot_and_diff_for_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            runtime = Runtime.open(repo_root)
            existing_path = runtime.repository.resolve_memory_path("notes/existing.md")
            existing_path.parent.mkdir(parents=True, exist_ok=True)
            existing_path.write_text("old value\n")

            proposal = runtime.create_memory_proposal(
                target_path="notes/existing.md",
                content="new value\n",
                rationale="Update existing canon.",
            )
            current_path = repo_root / "artifacts" / proposal.current_artifact_path
            diff_path = repo_root / "artifacts" / proposal.diff_artifact_path

            self.assertEqual(current_path.read_text(), "old value\n")
            diff_text = diff_path.read_text()
            self.assertIn("-old value", diff_text)
            self.assertIn("+new value", diff_text)

    def test_apply_requires_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            runtime = Runtime.open(repo_root)
            validation_ids = self._create_required_validations(runtime)

            proposal = runtime.create_memory_proposal(
                target_path="notes/priority.md",
                content="priority\n",
                rationale="Need explicit approval first.",
                validation_ids=[validation_ids["canon-safe"], validation_ids["frontdoor-reviewed"]],
            )
            with self.assertRaises(ValueError):
                runtime.apply_proposal(proposal.proposal_id)

    def test_apply_requires_policy_validations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            runtime = Runtime.open(repo_root)

            proposal = runtime.create_memory_proposal(
                target_path="notes/policy.md",
                content="policy\n",
                rationale="Should fail without required validation set.",
                validation_ids=[],
            )
            runtime.approve_proposal(proposal.proposal_id, reviewer="reviewer@example.com")
            with self.assertRaises(ValueError):
                runtime.apply_proposal(proposal.proposal_id)

    def test_apply_requires_approval_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            runtime = Runtime.open(repo_root)
            validation_ids = self._create_required_validations(runtime)

            proposal = runtime.create_memory_proposal(
                target_path="notes/no-approval.md",
                content="no approval\n",
                rationale="Missing explicit approval artifact.",
                validation_ids=[validation_ids["canon-safe"], validation_ids["frontdoor-reviewed"]],
            )
            proposal_payload = json.loads((repo_root / "artifacts" / "promotions" / proposal.proposal_id / "proposal.json").read_text())
            proposal_payload["status"] = "approved"
            proposal_payload["reviewer"] = "reviewer@example.com"
            proposal_payload["approval_refs"] = []
            (repo_root / "artifacts" / "promotions" / proposal.proposal_id / "proposal.json").write_text(
                json.dumps(proposal_payload, indent=2, sort_keys=True) + "\n"
            )

            with self.assertRaises(ValueError):
                runtime.apply_proposal(proposal.proposal_id)

    def test_apply_rejects_non_promotable_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            runtime = Runtime.open(repo_root)
            validation_ids = self._create_required_validations(runtime)

            proposal = runtime.create_memory_proposal(
                target_path="mission.md",
                content="restricted\n",
                rationale="Top-level memory path is outside promotable roots.",
                validation_ids=[validation_ids["canon-safe"], validation_ids["frontdoor-reviewed"]],
            )
            runtime.approve_proposal(
                proposal.proposal_id,
                reviewer="reviewer@example.com",
                validation_ids=[validation_ids["canon-safe"], validation_ids["frontdoor-reviewed"]],
            )
            with self.assertRaises(ValueError):
                runtime.apply_proposal(proposal.proposal_id)

    def test_apply_rejects_stale_canon(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            runtime = Runtime.open(repo_root)
            validation_ids = self._create_required_validations(runtime)

            proposal = runtime.create_memory_proposal(
                target_path="notes/stale.md",
                content="v1\n",
                rationale="Should fail if canon moves before apply.",
                validation_ids=[validation_ids["canon-safe"], validation_ids["frontdoor-reviewed"]],
            )
            runtime.approve_proposal(
                proposal.proposal_id,
                reviewer="reviewer@example.com",
                validation_ids=[validation_ids["canon-safe"], validation_ids["frontdoor-reviewed"]],
            )
            target = runtime.repository.resolve_memory_path("notes/stale.md")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("v2\n")

            with self.assertRaises(ValueError):
                runtime.apply_proposal(proposal.proposal_id)

    def test_apply_rejects_candidate_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            runtime = Runtime.open(repo_root)
            validation_ids = self._create_required_validations(runtime)

            proposal = runtime.create_memory_proposal(
                target_path="notes/drift.md",
                content="candidate\n",
                rationale="Candidate artifact should be immutable after approval.",
                validation_ids=[validation_ids["canon-safe"], validation_ids["frontdoor-reviewed"]],
            )
            runtime.approve_proposal(
                proposal.proposal_id,
                reviewer="reviewer@example.com",
                validation_ids=[validation_ids["canon-safe"], validation_ids["frontdoor-reviewed"]],
            )
            (repo_root / "artifacts" / proposal.candidate_artifact_path).write_text("mutated\n")

            with self.assertRaises(ValueError):
                runtime.apply_proposal(proposal.proposal_id)

    def test_apply_rejects_validation_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            runtime = Runtime.open(repo_root)
            validation_ids = self._create_required_validations(runtime)

            proposal = runtime.create_memory_proposal(
                target_path="notes/validation-drift.md",
                content="candidate\n",
                rationale="Validation evidence should stay pinned after approval.",
                validation_ids=[validation_ids["canon-safe"], validation_ids["frontdoor-reviewed"]],
            )
            runtime.approve_proposal(
                proposal.proposal_id,
                reviewer="reviewer@example.com",
                validation_ids=[validation_ids["canon-safe"], validation_ids["frontdoor-reviewed"]],
            )
            validation_path = repo_root / "artifacts" / "validations" / f"{validation_ids['canon-safe']}.json"
            validation_payload = json.loads(validation_path.read_text())
            validation_payload["summary"] = "mutated after approval"
            validation_path.write_text(json.dumps(validation_payload, indent=2, sort_keys=True) + "\n")

            with self.assertRaises(ValueError):
                runtime.apply_proposal(proposal.proposal_id)

    def test_branch_memory_promotion_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            runtime = Runtime.open(repo_root)
            branch = runtime.branch_workspace("research_branch")
            branch.write_memory_text("notes/hypothesis.md", "# Hypothesis\n\nPromote from branch.\n")
            validation_ids = self._create_required_validations(runtime, include_branch=True)

            proposal = runtime.create_memory_proposal_from_branch(
                branch="research_branch",
                branch_memory_path="notes/hypothesis.md",
                target_path="notes/hypothesis.md",
                rationale="Branch-local draft is ready for canon.",
                validation_ids=[validation_ids["branch-reviewed"]],
            )
            self.assertEqual(proposal.source_branch, "research_branch")
            self.assertEqual(proposal.source_branch_memory_path, "notes/hypothesis.md")
            self.assertFalse((repo_root / "memory" / "notes" / "hypothesis.md").exists())

            runtime.approve_proposal(
                proposal.proposal_id,
                reviewer="reviewer@example.com",
                validation_ids=[
                    validation_ids["branch-reviewed"],
                    validation_ids["canon-safe"],
                    validation_ids["frontdoor-reviewed"],
                ],
            )
            runtime.apply_proposal(proposal.proposal_id)
            self.assertEqual((repo_root / "memory" / "notes" / "hypothesis.md").read_text(), "# Hypothesis\n\nPromote from branch.\n")

    def test_cli_validate_repo(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "skillfoundry_harness.cli", "validate", str(FIXTURE_REPO)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OK", result.stdout)

    def test_cli_describe_repo(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "skillfoundry_harness.cli", "describe", str(FIXTURE_REPO)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("repository.agent_id=minimal-agent", result.stdout)
        self.assertIn("layout.artifacts_dir=", result.stdout)
        self.assertIn("worktrees.managed_root=", result.stdout)
        self.assertIn("promotion_policy.required_validation_kinds=canon-safe,frontdoor-reviewed", result.stdout)

    def test_cli_frontdoor(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "skillfoundry_harness.cli", "frontdoor", str(FIXTURE_REPO), "--max-chars", "60"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[PINNED] README.md", result.stdout)
        self.assertIn("[DISCOVERABLE] bundles", result.stdout)

    def test_cli_init_and_fork_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source_root = Path(tmpdir) / "source"
            target_root = Path(tmpdir) / "forked"

            init_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "skillfoundry_harness.cli",
                    "init-context",
                    str(source_root),
                    "--agent-id",
                    "researcher",
                    "--name",
                    "Researcher Context",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init_result.returncode, 0, init_result.stderr)
            self.assertIn("agent_id=researcher", init_result.stdout)

            fork_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "skillfoundry_harness.cli",
                    "fork-context",
                    str(source_root),
                    str(target_root),
                    "--agent-id",
                    "designer",
                    "--name",
                    "Designer Context",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(fork_result.returncode, 0, fork_result.stderr)
            self.assertIn("agent_id=designer", fork_result.stdout)

    def test_cli_branch_describe(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "skillfoundry_harness.cli",
                    "branch-describe",
                    str(repo_root),
                    "research_branch",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("branch=research_branch", result.stdout)

    def test_cli_show_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            runtime = Runtime.open(repo_root)
            proposal = runtime.create_memory_proposal(
                target_path="notes/show.md",
                content="show\n",
                rationale="Inspect proposal metadata.",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "skillfoundry_harness.cli",
                    "show-proposal",
                    str(repo_root),
                    proposal.proposal_id,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"proposal_id={proposal.proposal_id}", result.stdout)
            self.assertIn("diff_artifact_path=", result.stdout)

    def test_cli_record_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            (repo_root / "artifacts" / "checks").mkdir(parents=True, exist_ok=True)
            (repo_root / "artifacts" / "checks" / "frontdoor.txt").write_text("ok\n")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "skillfoundry_harness.cli",
                    "record-validation",
                    str(repo_root),
                    "--kind",
                    "frontdoor-reviewed",
                    "--status",
                    "passed",
                    "--evidence-path",
                    "checks/frontdoor.txt",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("validation_id=", result.stdout)

    def test_cli_bundle_commands(self) -> None:
        list_result = subprocess.run(
            [sys.executable, "-m", "skillfoundry_harness.cli", "list-bundles", str(FIXTURE_REPO)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(list_result.returncode, 0, list_result.stderr)
        self.assertIn("bundle_id=product-brief-v1", list_result.stdout)

        show_result = subprocess.run(
            [sys.executable, "-m", "skillfoundry_harness.cli", "show-bundle", str(FIXTURE_REPO), "product-brief-v1"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(show_result.returncode, 0, show_result.stderr)
        self.assertIn("promotion_status=candidate", show_result.stdout)

    def test_cli_promotion_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            content_file = repo_root / "proposal.md"
            content_file.write_text("# Canon\n\nPromoted through CLI.\n")
            validation_ids = self._create_required_validations(Runtime.open(repo_root))

            propose_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "skillfoundry_harness.cli",
                    "propose-memory",
                    str(repo_root),
                    "notes/cli.md",
                    str(content_file),
                    "--rationale",
                    "Exercise CLI proposal flow.",
                    "--thread-id",
                    "thread_cli",
                    "--turn-id",
                    "turn_cli",
                    "--validation-id",
                    validation_ids["canon-safe"],
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(propose_result.returncode, 0, propose_result.stderr)
            proposal_id = next(
                line.split("=", 1)[1]
                for line in propose_result.stdout.splitlines()
                if line.startswith("proposal_id=")
            )

            approve_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "skillfoundry_harness.cli",
                    "approve-proposal",
                    str(repo_root),
                    proposal_id,
                    "--reviewer",
                    "cli-reviewer@example.com",
                    "--validation-id",
                    validation_ids["canon-safe"],
                    "--validation-id",
                    validation_ids["frontdoor-reviewed"],
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(approve_result.returncode, 0, approve_result.stderr)

            apply_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "skillfoundry_harness.cli",
                    "apply-proposal",
                    str(repo_root),
                    proposal_id,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(apply_result.returncode, 0, apply_result.stderr)
            self.assertIn("status=applied", apply_result.stdout)
            self.assertEqual((repo_root / "memory" / "notes" / "cli.md").read_text(), "# Canon\n\nPromoted through CLI.\n")

    def test_cli_branch_promotion_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            branch_file = repo_root / "artifacts" / "branches" / "research_branch" / "memory" / "notes" / "branch.md"
            branch_file.parent.mkdir(parents=True, exist_ok=True)
            branch_file.write_text("# Branch Draft\n\nCLI sourced proposal.\n")
            validation_ids = self._create_required_validations(Runtime.open(repo_root), include_branch=True)

            propose_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "skillfoundry_harness.cli",
                    "propose-branch-memory",
                    str(repo_root),
                    "research_branch",
                    "notes/branch.md",
                    "notes/branch.md",
                    "--rationale",
                    "Promote branch-local draft.",
                    "--validation-id",
                    validation_ids["branch-reviewed"],
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(propose_result.returncode, 0, propose_result.stderr)
            self.assertIn("source_branch=research_branch", propose_result.stdout)

    def test_worktree_manager_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            self._init_git_repo(repo_root)
            runtime = Runtime.open(repo_root)

            worktree = runtime.create_worktree("review_branch")
            self.assertTrue(Path(worktree.path).exists())
            self.assertEqual(worktree.branch, "review_branch")
            self.assertIsNone(worktree.latest_run_id)

            listed = runtime.list_worktrees()
            self.assertEqual(len(listed), 1)
            self.assertEqual(listed[0].status, "active")
            self.assertEqual(listed[0].worktree_name, "review_branch")

            removed = runtime.remove_worktree("review_branch")
            self.assertEqual(removed.status, "removed")
            self.assertFalse(Path(removed.path).exists())

    def test_cli_worktree_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            self._init_git_repo(repo_root)

            create_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "skillfoundry_harness.cli",
                    "worktree-create",
                    str(repo_root),
                    "cli_review",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(create_result.returncode, 0, create_result.stderr)
            self.assertIn("worktree_name=cli_review", create_result.stdout)

            list_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "skillfoundry_harness.cli",
                    "worktree-list",
                    str(repo_root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(list_result.returncode, 0, list_result.stderr)
            self.assertIn("worktree_name=cli_review", list_result.stdout)

            remove_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "skillfoundry_harness.cli",
                    "worktree-remove",
                    str(repo_root),
                    "cli_review",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(remove_result.returncode, 0, remove_result.stderr)
            self.assertIn("status=removed", remove_result.stdout)

    def test_rejects_layout_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "bundles").mkdir()
            (repo_root / "memory").mkdir()
            (repo_root / "artifacts").mkdir()
            (repo_root / "runs").mkdir()
            (repo_root / "README.md").write_text("escape\n")
            (repo_root / "memory" / "mission.md").write_text("mission\n")
            (repo_root / "skillfoundry.toml").write_text(
                "\n".join(
                    [
                        "[repository]",
                        'schema_version = "1"',
                        'name = "Escape Test"',
                        'agent_id = "escape-test"',
                        "",
                        "[layout]",
                        'runs_dir = "../outside"',
                        "",
                        "[frontdoor]",
                        'pinned_paths = ["README.md", "memory/mission.md"]',
                        'discoverable_paths = ["bundles", "memory", "artifacts"]',
                    ]
                )
            )
            with self.assertRaises(ValidationError):
                Runtime.open(repo_root).validate()

    def test_rejects_missing_frontdoor(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            for name in ("bundles", "memory", "artifacts", "runs"):
                (repo_root / name).mkdir()
            (repo_root / "skillfoundry.toml").write_text(
                "\n".join(
                    [
                        "[repository]",
                        'schema_version = "1"',
                        'name = "No Frontdoor"',
                        'agent_id = "no-frontdoor"',
                    ]
                )
            )
            with self.assertRaises(ValidationError):
                Runtime.open(repo_root)

    def test_rejects_missing_promotion_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            for name in ("bundles", "memory", "artifacts", "runs"):
                (repo_root / name).mkdir()
            (repo_root / "README.md").write_text("repo\n")
            (repo_root / "memory" / "mission.md").write_text("mission\n")
            (repo_root / "skillfoundry.toml").write_text(
                "\n".join(
                    [
                        "[repository]",
                        'schema_version = "1"',
                        'name = "No Policy"',
                        'agent_id = "no-policy"',
                        "",
                        "[frontdoor]",
                        'pinned_paths = ["README.md", "memory/mission.md"]',
                        'discoverable_paths = ["bundles", "memory", "artifacts"]',
                    ]
                )
            )
            with self.assertRaises(ValidationError):
                Runtime.open(repo_root)

    def test_run_recorder_writes_durable_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            runtime = Runtime.open(repo_root)
            recorder = runtime.start_run(thread_id="thread_demo", task="Inspect current objective")
            recorder.append_item(kind="message", status="started", payload={"role": "user", "text": "Inspect current objective"})
            recorder.append_item(kind="approval", status="pending_approval", payload={"reason": "publish artifact"})
            compaction_path = recorder.write_compaction("Condensed continuation state.")
            record = recorder.complete()

            self.assertEqual(record.status, "completed")
            self.assertTrue(compaction_path.exists())
            run_payload = json.loads((recorder.run_dir / "run.json").read_text())
            self.assertEqual(run_payload["thread_id"], "thread_demo")
            self.assertEqual(run_payload["item_count"], 3)
            items = (recorder.run_dir / "items.jsonl").read_text().strip().splitlines()
            self.assertEqual(len(items), 3)
            self.assertEqual((repo_root / "runs" / "LATEST_RUN").read_text().strip(), record.run_id)
            thread_payload = json.loads((repo_root / "runs" / "threads" / "thread_demo" / "thread.json").read_text())
            turn_payload = json.loads((repo_root / "runs" / "threads" / "thread_demo" / "turns" / f"{record.turn_id}.json").read_text())
            self.assertEqual(thread_payload["latest_turn_id"], record.turn_id)
            self.assertEqual(thread_payload["turn_count"], 1)
            self.assertEqual(turn_payload["latest_run_id"], record.run_id)
            self.assertEqual(turn_payload["status"], "completed")

    def test_run_recorder_binds_worktree_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            self._init_git_repo(repo_root)
            runtime = Runtime.open(repo_root)
            worktree = runtime.create_worktree("subagent_review")

            recorder = runtime.start_run(
                thread_id="thread_worktree",
                task="Review branch-local hypothesis",
                worktree_name="subagent_review",
            )
            record = recorder.complete()

            run_payload = json.loads((recorder.run_dir / "run.json").read_text())
            turn_payload = json.loads((repo_root / "runs" / "threads" / "thread_worktree" / "turns" / f"{record.turn_id}.json").read_text())
            worktree_payload = json.loads((repo_root / "artifacts" / "worktrees" / "subagent_review.json").read_text())

            self.assertEqual(run_payload["worktree_name"], "subagent_review")
            self.assertEqual(run_payload["worktree_path"], worktree.path)
            self.assertEqual(run_payload["branch"], "subagent_review")
            self.assertEqual(turn_payload["worktree_name"], "subagent_review")
            self.assertEqual(worktree_payload["latest_thread_id"], "thread_worktree")
            self.assertEqual(worktree_payload["latest_turn_id"], record.turn_id)
            self.assertEqual(worktree_payload["latest_run_id"], record.run_id)
            self.assertEqual(worktree_payload["head_sha"], run_payload["worktree_head_sha"])

    def test_existing_thread_increments_turn_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._copy_fixture_repo(repo_root)
            runtime = Runtime.open(repo_root)

            first = runtime.start_run(thread_id="thread_demo", task="First task")
            first.complete()
            second = runtime.start_run(thread_id="thread_demo", task="Second task")
            second.complete()

            thread_payload = json.loads((repo_root / "runs" / "threads" / "thread_demo" / "thread.json").read_text())
            self.assertEqual(thread_payload["turn_count"], 2)
            self.assertEqual(thread_payload["latest_turn_id"], second.record.turn_id)

    def test_schema_copies_match(self) -> None:
        self.assertEqual(ROOT_SCHEMA.read_text(), PACKAGE_SCHEMA.read_text())

    def _copy_fixture_repo(self, destination: Path) -> None:
        for path in FIXTURE_REPO.rglob("*"):
            relative = path.relative_to(FIXTURE_REPO)
            target = destination / relative
            if path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(path.read_text())

    def _create_required_validations(self, runtime: Runtime, include_branch: bool = False) -> dict[str, str]:
        runtime.repository.write_artifact_text("checks/canon-safe.txt", "canon ok\n")
        runtime.repository.write_artifact_text("checks/frontdoor.txt", "frontdoor ok\n")
        validation_ids = {
            "canon-safe": runtime.create_validation_artifact(
                kind="canon-safe",
                status="passed",
                evidence_paths=["checks/canon-safe.txt"],
            ).validation_id,
            "frontdoor-reviewed": runtime.create_validation_artifact(
                kind="frontdoor-reviewed",
                status="passed",
                evidence_paths=["checks/frontdoor.txt"],
            ).validation_id,
        }
        if include_branch:
            runtime.repository.write_artifact_text("checks/branch.txt", "branch ok\n")
            validation_ids["branch-reviewed"] = runtime.create_validation_artifact(
                kind="branch-reviewed",
                status="passed",
                evidence_paths=["checks/branch.txt"],
            ).validation_id
        return validation_ids

    def _init_git_repo(self, destination: Path) -> None:
        subprocess.run(["git", "init"], cwd=destination, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "tests@skillfoundry.dev"], cwd=destination, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.name", "Skillfoundry Tests"], cwd=destination, check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "."], cwd=destination, check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=destination, check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
