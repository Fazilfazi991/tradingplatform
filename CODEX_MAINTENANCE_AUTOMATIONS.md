# Codex Maintenance Automations

Status date: 2026-09-08

Codex scheduled tasks are review assistants, not Verified Edge production workers. They may inspect
repository evidence and return findings for human review, but they do not collect market data,
operate the intelligence scheduler, issue forward predictions, mutate release gates, or deploy the
product.

## Installed tasks

### Daily runtime triage

| Field | Current state |
|---|---|
| Automation ID | `verified-edge-daily-runtime-triage` |
| Name | Verified Edge daily runtime triage |
| Status | `ACTIVE` |
| Schedule | Daily at 08:30 in the desktop scheduler's local timezone |
| Execution | Heartbeat attached to the readiness task |

The daily task inspects authoritative persisted status, manifests, ledgers, incident records, and
existing safe status commands for the platform-owned collectors, intelligence worker, Research
Operator, market-data EOD job, and forward-paper pipeline. It reports only meaningful regressions,
recoveries, completed milestones, failed jobs, stale evidence, or owner actions. An unchanged,
non-actionable state remains quiet.

### Weekly readiness audit

| Field | Current state |
|---|---|
| Automation ID | `verified-edge-weekly-readiness-audit` |
| Name | Verified Edge weekly readiness audit |
| Status | `ACTIVE` |
| Schedule | Monday at 09:00 in the desktop scheduler's local timezone |
| Project | Trading Platform Prediction |
| Working directory | `C:\Users\User\Desktop\Projects\Trading Platform` |
| Execution environment | Local saved project |
| Model | `gpt-5.6-luna` |
| Reasoning effort | Medium |

The weekly task reads the master plan, release-gate manifest, blocker and owner registers, promotion report,
and predictive-readiness report. It compares the current branch and `origin/main`, inspects the
hosted quality run for the exact SHA, runs the existing gate audit where useful, and reports only
material drift, failures, stale evidence, dependency/security concerns, and newly actionable owner
items.

Its prompt explicitly prohibits:

- editing files or changing release decisions;
- exposing credentials or values;
- activating market-data, intelligence, or forward-prediction runtimes;
- issuing predictions or treating Codex as the platform scheduler;
- committing, pushing, deploying, or publishing promotion.

## Verification and operation

The authoritative task definition is stored by the Codex desktop app under the user's automations
directory, outside this Git repository. Review its card and run history in the app's Scheduled view.
This repository records the expected ID and safety contract so drift can be detected; it does not
copy personal app state or credentials into Git.

The tasks have been installed, but no scheduled-run result is claimed yet. A future run is evidence of
Codex review activity only. It cannot satisfy web uptime, provider continuity, collector freshness,
incident delivery, production worker supervision, or any other platform-owned operational gate.

Official OpenAI documentation describes scheduled tasks as background runs managed from the app and
notes that local-project tasks require the computer and app to remain available. See
[Scheduled tasks](https://learn.chatgpt.com/docs/automations).
