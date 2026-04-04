## Summary

- What stable harness surface changed?
- Why does the change belong in `skillfoundry-harness`?

## Boundary Check

- [ ] No agent workspace state added
- [ ] Behavior depends only on explicit repository contracts
- [ ] Tests cover the new or changed interface

## Validation

- [ ] `python3 -m venv .venv && source .venv/bin/activate && python3 -m pip install -e .`
- [ ] `python3.12 scripts/check_repo_hygiene.py`
- [ ] `python3.12 -m unittest discover -s tests`

## Review Notes

- Repository contract introduced or changed:
- CLI or API surface introduced or changed:
- Risks or open questions:
