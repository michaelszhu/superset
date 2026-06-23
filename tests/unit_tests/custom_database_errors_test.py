# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import re

from superset.custom_database_errors import CUSTOM_DATABASE_ERRORS
from superset.errors import SupersetErrorType


def test_custom_database_errors_has_examples_key() -> None:
    assert "examples" in CUSTOM_DATABASE_ERRORS


def test_examples_patterns_are_compiled_regex() -> None:
    for pattern in CUSTOM_DATABASE_ERRORS["examples"]:
        assert isinstance(pattern, re.Pattern)


def test_examples_table_a_pattern_matches() -> None:
    patterns = CUSTOM_DATABASE_ERRORS["examples"]
    table_a_pattern = next(p for p in patterns if p.pattern == "no such table: a")
    assert table_a_pattern.search("no such table: a")
    assert table_a_pattern.search("OperationalError: no such table: a")
    assert not table_a_pattern.search("no such table: b")


def test_examples_table_a_error_type() -> None:
    patterns = CUSTOM_DATABASE_ERRORS["examples"]
    table_a_pattern = next(p for p in patterns if p.pattern == "no such table: a")
    message, error_type, extra = patterns[table_a_pattern]
    assert error_type == SupersetErrorType.GENERIC_DB_ENGINE_ERROR
    assert isinstance(message, str)


def test_examples_table_a_custom_doc_links() -> None:
    patterns = CUSTOM_DATABASE_ERRORS["examples"]
    table_a_pattern = next(p for p in patterns if p.pattern == "no such table: a")
    _, _, extra = patterns[table_a_pattern]
    assert "custom_doc_links" in extra
    links = extra["custom_doc_links"]
    assert len(links) >= 1
    assert "url" in links[0]
    assert "label" in links[0]
    assert extra.get("show_issue_info") is False


def test_examples_table_b_pattern_matches() -> None:
    patterns = CUSTOM_DATABASE_ERRORS["examples"]
    table_b_pattern = next(p for p in patterns if p.pattern == "no such table: b")
    assert table_b_pattern.search("no such table: b")
    assert not table_b_pattern.search("no such table: a")


def test_examples_table_b_show_issue_info() -> None:
    patterns = CUSTOM_DATABASE_ERRORS["examples"]
    table_b_pattern = next(p for p in patterns if p.pattern == "no such table: b")
    _, error_type, extra = patterns[table_b_pattern]
    assert error_type == SupersetErrorType.GENERIC_DB_ENGINE_ERROR
    assert extra.get("show_issue_info") is True


def test_custom_database_errors_tuple_structure() -> None:
    """Each entry is a 3-tuple: (message_str, SupersetErrorType, dict)."""
    for db_name, patterns in CUSTOM_DATABASE_ERRORS.items():
        for pattern, value in patterns.items():
            assert isinstance(pattern, re.Pattern), (
                f"Key for {db_name} is not a compiled regex"
            )
            assert len(value) == 3, (
                f"Value for {db_name}/{pattern.pattern} is not a 3-tuple"
            )
            message, error_type, extra = value
            assert isinstance(message, str)
            assert isinstance(error_type, SupersetErrorType)
            assert isinstance(extra, dict)
