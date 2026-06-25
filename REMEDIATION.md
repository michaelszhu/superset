# Security Remediation

This fork of [Apache Superset](https://github.com/apache/superset) was used as
the target repository for automated security remediation powered by the
[Devin API](https://docs.devin.ai).

Eight security findings (SCA vulnerabilities and SAST rule violations) were
filed as GitHub issues with the `devin-remediate` label. Each issue triggered
an autonomous Devin session that analyzed the finding and either produced a fix
(PR), declined with a risk explanation, or classified it as a false positive.

## Issues and Outcomes

| # | Issue | Type | Outcome | PR / Response |
|---|-------|------|---------|---------------|
| 1 | [#89 — paramiko dependency risk](https://github.com/michaelszhu/superset/issues/89) | SCA | **Declined** | [False-positive analysis](https://github.com/michaelszhu/superset/issues/89#issuecomment-4803773618) |
| 2 | [#90 — PyJWT CVE-2022-29217](https://github.com/michaelszhu/superset/issues/90) | SCA | **False Positive** | [False-positive analysis](https://github.com/michaelszhu/superset/issues/90#issuecomment-4803776323) |
| 3 | [#91 — Hive column injection](https://github.com/michaelszhu/superset/issues/91) | SAST | **Fixed** | [PR #101](https://github.com/michaelszhu/superset/pull/101) |
| 4 | [#92 — apispec pinned below latest](https://github.com/michaelszhu/superset/issues/92) | SCA | **Fixed** | [PR #100](https://github.com/michaelszhu/superset/pull/100) |
| 5 | [#93 — DOMPurify sanitizer bypass](https://github.com/michaelszhu/superset/issues/93) | SCA | **Fixed** | [PR #99](https://github.com/michaelszhu/superset/pull/99) |
| 6 | [#94 — SQL injection in cancel_query](https://github.com/michaelszhu/superset/issues/94) | SAST | **Fixed** | [PR #102](https://github.com/michaelszhu/superset/pull/102) |
| 7 | [#95 — Unsafe YAML deserialization](https://github.com/michaelszhu/superset/issues/95) | SAST | **Fixed** | [PR #103](https://github.com/michaelszhu/superset/pull/103) |
| 8 | [#96 — Silenced exceptions](https://github.com/michaelszhu/superset/issues/96) | SAST | **Fixed** | [PR #104](https://github.com/michaelszhu/superset/pull/104) |

## Summary

- **6 findings fixed** with PRs containing tested code changes
- **1 declined** (paramiko upgrade would break transitive dependency `sshtunnel`)
- **1 false positive** (PyJWT already patched in pinned version)

## Finding Details

### #89 — paramiko dependency risk (SCA)

**Issue:** paramiko 3.5.1 flagged for CVE-2023-48795 (Terrapin Attack).

**Outcome:** Declined. The repository already uses paramiko 3.5.1 (>=3.4.0
enforced in pyproject.toml), which includes the fix. Additionally, upgrading
to paramiko 5.x would remove the deprecated `DSSKey` class that the transitive
dependency `sshtunnel` still imports, causing a runtime `ImportError`.

### #90 — PyJWT CVE-2022-29217 (SCA)

**Issue:** PyJWT flagged for algorithm confusion vulnerability.

**Outcome:** False positive. PyJWT is pinned at 2.12.0 (>=2.4.0 enforced in
pyproject.toml). The vulnerability only affects versions < 2.4.0, and all
`jwt.decode()` calls in the codebase already pass `algorithms` explicitly.

### #91 — Hive column injection (SAST)

**Issue:** Unsanitized column names passed to `Column()` in
`HiveEngineSpec.where_latest_partition()`.

**Outcome:** Fixed. PR validates partition column names against a strict
identifier regex before passing to `Column()`, preventing SQL injection via
crafted partition column names.

### #92 — apispec pinned below latest (SCA)

**Issue:** apispec pinned to `<6.7.0`, missing security and bug fixes in
newer versions.

**Outcome:** Fixed. Bumped the apispec pin from `<6.7.0` to `<7.0.0`,
upgrading from 6.6.1 to 6.10.0. Updated one integration test assertion
that changed with the new JSON-schema output format.

### #93 — DOMPurify sanitizer bypass (SCA)

**Issue:** DOMPurify 3.4.7 flagged for GHSA-vxr8-fq34-vvx9 (Trusted Types
policy bypass allowing HTML sanitization circumvention).

**Outcome:** Fixed. Bumped DOMPurify from 3.4.7 to 3.4.11 in the frontend
package, resolving the sanitizer-bypass advisory.

### #94 — SQL injection in cancel_query (SAST)

**Issue:** f-string SQL interpolation in `PostgresEngineSpec.cancel_query()`
and `RedshiftEngineSpec.cancel_query()`.

**Outcome:** Fixed. Replaced f-string SQL interpolation with parameterized
queries (`%s` + tuple) to prevent potential SQL injection.

### #95 — Unsafe YAML deserialization (SAST)

**Issue:** `yaml.Loader` used in `load_configs_from_directory()`, which
allows arbitrary code execution during YAML parsing.

**Outcome:** Fixed. Replaced `yaml.Loader` with `yaml.safe_load()`, which
only allows standard YAML types and blocks code execution.

### #96 — Silenced exceptions (SAST)

**Issue:** Multiple `except Exception: pass` blocks across core modules
silently swallow errors, making debugging impossible.

**Outcome:** Fixed. Added `logger.warning` with `exc_info=True` to silenced
exception handlers. Narrowed broad `except Exception` to specific types
(`ValueError`, `KeyError`, etc.) where the set of expected exceptions is clear.

## Orchestration Repository

The automation system that dispatched these sessions is at:
https://github.com/michaelszhu/remediation-automation
