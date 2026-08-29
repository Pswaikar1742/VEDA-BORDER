# Codex Runbook

Execute prompts in order. Do not skip acceptance tests to chase UI polish.

1. `prompts/01_scaffold.md`
2. `prompts/02_synthetic_fixtures.md`
3. `prompts/03_document_mrz_rules.md`
4. `prompts/04_consistency_and_intelligence.md`
5. `prompts/05_forensics_biometrics.md`
6. `prompts/06_governor_autopsy.md`
7. `prompts/07_web_demo_and_golden_suite.md`

After every task:
- run all tests,
- update `docs/DECISION_LOG.md` only for actual new decisions,
- write a short `TASK_REPORT.md` with files changed, tests, known limitations, and next blockers,
- do not claim untested accuracy.
