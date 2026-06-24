# Security Remediation Summary

This fork of [Apache Superset](https://github.com/apache/superset) was used as
the target repository for the
[remediation-automation](https://github.com/michaelszhu/remediation-automation)
system. Three security findings were selected for automated remediation by
Devin.

## How Findings Were Discovered

Two types of scanners were run against this repository:

- **SCA (Software Composition Analysis)** -- `pip-audit` scanned Python
  dependencies in `requirements/base.txt` and `pyproject.toml` for known CVEs.
- **SAST (Static Application Security Testing)** -- Semgrep with
  `p/python` + `p/security-audit` rulesets scanned the `superset/` backend
  source for code-level vulnerabilities.

Each finding was filed as a GitHub issue with the `devin-remediate` label.

---

## Findings and Outcomes

### 1. `hive-column-injection` (SAST) -- Fixed

- **Issue:** [#52](https://github.com/michaelszhu/superset/issues/52)
- **PR:** [#53](https://github.com/michaelszhu/superset/pull/53)
- **Severity:** High
- **File:** `superset/db_engine_specs/hive.py:473`

**Problem:**
`HiveEngineSpec.where_latest_partition()` and
`PrestoEngineSpec.where_latest_partition()` pass unsanitized partition column
names directly into `sqlalchemy.Column()`, which renders them as unquoted
identifiers in the SQL text. A user with `sql_lab` permissions could create a
table with a maliciously crafted partition column name (e.g.,
`ds; DROP TABLE users--`). When another user views that table via `select_star`
with `latest_partition=True`, the column name flows unsanitized into query
construction.

**Fix:**
Devin added a `SAFE_IDENTIFIER_REGEX = re.compile(r"^[a-zA-Z0-9_]+$")`
validation check in both `PrestoEngineSpec.where_latest_partition()` and
`HiveEngineSpec.where_latest_partition()`. If a partition column name fails
validation, the method logs a warning and returns `None` (no partition filter
applied), preventing SQL injection through this path. Unit tests were added
to confirm malicious names are rejected and safe names continue to work.

**Files changed:**
- `superset/db_engine_specs/presto.py`
- `superset/db_engine_specs/hive.py`
- `tests/unit_tests/db_engine_specs/test_presto.py`
- `tests/unit_tests/db_engine_specs/test_hive.py`

---

### 2. `PyJWT` CVE-2022-29217 (SCA) -- False Positive

- **Issue:** [#51](https://github.com/michaelszhu/superset/issues/51)
- **Severity:** High
- **Package:** `PyJWT==2.12.0`

**Problem reported:**
PyJWT before 2.4.0 allows algorithm confusion when the caller does not pass an
explicit `algorithms` argument to `jwt.decode()`. An attacker could forge
tokens by exploiting HMAC/RSA confusion.

**Devin's analysis:**
Devin investigated all `jwt.decode()` call sites in the Superset codebase and
found three:

1. `superset/utils/oauth2.py` -- passes
   `algorithms=[app.config['DATABASE_OAUTH2_JWT_ALGORITHM']]`
2. `superset/async_events/async_query_manager.py` -- passes
   `algorithms=['HS256']`
3. `superset/mcp_service/jwt_verifier.py` -- uses `authlib.jose` (not PyJWT)

The installed version is 2.12.0 and the minimum constraint in `pyproject.toml`
is `>=2.4.0`, making the vulnerability impossible to exploit. All call sites
pass explicit `algorithms` arguments. **No code change was needed.**

---

### 3. `paramiko` Dependency Risk (SCA) -- False Positive

- **Issue:** [#50](https://github.com/michaelszhu/superset/issues/50)
- **Severity:** High
- **Package:** `paramiko==3.5.1`

**Problem reported:**
`paramiko >=3.0` removed `paramiko.DSSKey`. The `sshtunnel` package still
imports it, causing `ImportError` at runtime when SSH tunnels are used.

**Devin's analysis:**
The scanner incorrectly flagged `paramiko==3.5.1`. The `DSSKey` class was
removed in `paramiko 4.0`, not 3.x. The existing `<4.0` upper bound in
`pyproject.toml` (pinning `>=3.4.0,<4.0`) already prevents the breakage.
Additionally, `CVE-2023-48795` (Terrapin Attack) affects paramiko before 3.4.0,
and the pinned version 3.5.1 is above the fix threshold. **No code change was
needed.** Devin posted its analysis as a comment on the source issue.

---

## Summary

| Finding | Type | Decision | PR |
|---------|------|----------|----|
| hive-column-injection | SAST | Fixed | [#53](https://github.com/michaelszhu/superset/pull/53) |
| PyJWT CVE-2022-29217 | SCA | False positive | -- |
| paramiko dependency risk | SCA | False positive | -- |

The remediation system correctly identified one real vulnerability that
required a code fix and two false positives that required no action -- with
detailed reasoning for each decision.
