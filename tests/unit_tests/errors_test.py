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
import pytest

from superset.errors import (
    ERROR_TYPES_TO_ISSUE_CODES_MAPPING,
    ErrorLevel,
    ISSUE_CODES,
    SupersetError,
    SupersetErrorType,
)


def test_superset_error_type_values() -> None:
    """SupersetErrorType enum members have the expected string values."""
    assert SupersetErrorType.FRONTEND_CSRF_ERROR == "FRONTEND_CSRF_ERROR"
    assert SupersetErrorType.GENERIC_DB_ENGINE_ERROR == "GENERIC_DB_ENGINE_ERROR"
    assert SupersetErrorType.SYNTAX_ERROR == "SYNTAX_ERROR"
    assert (
        SupersetErrorType.CONNECTION_INVALID_PASSWORD_ERROR  # noqa: S105
        == "CONNECTION_INVALID_PASSWORD_ERROR"  # noqa: S105
    )


def test_error_level_values() -> None:
    """ErrorLevel enum members have the expected string values."""
    assert ErrorLevel.INFO == "info"
    assert ErrorLevel.WARNING == "warning"
    assert ErrorLevel.ERROR == "error"


def test_superset_error_basic_construction() -> None:
    """SupersetError can be constructed with basic fields."""
    error = SupersetError(
        message="Something went wrong",
        error_type=SupersetErrorType.GENERIC_BACKEND_ERROR,
        level=ErrorLevel.ERROR,
    )
    assert error.message == "Something went wrong"
    assert error.error_type == SupersetErrorType.GENERIC_BACKEND_ERROR
    assert error.level == ErrorLevel.ERROR


def test_superset_error_post_init_adds_issue_codes() -> None:
    """__post_init__ populates extra with issue_codes for mapped error types."""
    error = SupersetError(
        message="test",
        error_type=SupersetErrorType.GENERIC_DB_ENGINE_ERROR,
        level=ErrorLevel.ERROR,
    )
    assert error.extra is not None
    assert "issue_codes" in error.extra
    codes = [ic["code"] for ic in error.extra["issue_codes"]]
    assert (
        codes
        == ERROR_TYPES_TO_ISSUE_CODES_MAPPING[SupersetErrorType.GENERIC_DB_ENGINE_ERROR]
    )


def test_superset_error_post_init_preserves_existing_extra() -> None:
    """__post_init__ merges issue_codes into an already-supplied extra dict."""
    error = SupersetError(
        message="test",
        error_type=SupersetErrorType.SYNTAX_ERROR,
        level=ErrorLevel.ERROR,
        extra={"custom_key": "custom_value"},
    )
    assert error.extra is not None
    assert error.extra["custom_key"] == "custom_value"
    assert "issue_codes" in error.extra


def test_superset_error_post_init_no_issue_codes_for_unmapped_type() -> None:
    """__post_init__ does not add issue_codes for error types not in the mapping."""
    error = SupersetError(
        message="test",
        error_type=SupersetErrorType.FRONTEND_CSRF_ERROR,
        level=ErrorLevel.ERROR,
    )
    assert error.extra is None


def test_superset_error_to_dict_basic() -> None:
    """to_dict returns message and error_type, omitting extra when None."""
    error = SupersetError(
        message="test msg",
        error_type=SupersetErrorType.FRONTEND_CSRF_ERROR,
        level=ErrorLevel.WARNING,
    )
    result = error.to_dict()
    assert result["message"] == "test msg"
    assert result["error_type"] == SupersetErrorType.FRONTEND_CSRF_ERROR
    assert "extra" not in result


def test_superset_error_to_dict_with_extra() -> None:
    """to_dict includes extra when it is populated."""
    error = SupersetError(
        message="test",
        error_type=SupersetErrorType.GENERIC_DB_ENGINE_ERROR,
        level=ErrorLevel.ERROR,
        extra={"detail": "more info"},
    )
    result = error.to_dict()
    assert "extra" in result
    assert "detail" in result["extra"]


def test_issue_codes_mapping_completeness() -> None:
    """Every issue code referenced in the mapping exists in ISSUE_CODES."""
    for error_type, codes in ERROR_TYPES_TO_ISSUE_CODES_MAPPING.items():
        for code in codes:
            assert code in ISSUE_CODES, (
                f"Issue code {code} (for {error_type}) missing from ISSUE_CODES"
            )


def test_superset_error_post_init_issue_code_message_format() -> None:
    """Issue code entries follow the 'Issue NNNN - <description>' format."""
    error = SupersetError(
        message="test",
        error_type=SupersetErrorType.CONNECTION_PORT_CLOSED_ERROR,
        level=ErrorLevel.ERROR,
    )
    assert error.extra is not None
    for ic in error.extra["issue_codes"]:
        assert isinstance(ic["code"], int)
        assert ic["message"].startswith(f"Issue {ic['code']} - ")


@pytest.mark.parametrize(
    "error_type,expected_codes",
    [
        (SupersetErrorType.BACKEND_TIMEOUT_ERROR, [1000, 1001]),
        (SupersetErrorType.CONNECTION_ACCESS_DENIED_ERROR, [1014, 1015]),
        (SupersetErrorType.RESULTS_BACKEND_ERROR, [1031, 1032, 1033]),
        (SupersetErrorType.DATABASE_NOT_FOUND_ERROR, [1011, 1036]),
    ],
)
def test_error_type_to_issue_codes_mapping(
    error_type: SupersetErrorType, expected_codes: list[int]
) -> None:
    """Specific error types map to the correct issue codes."""
    assert ERROR_TYPES_TO_ISSUE_CODES_MAPPING[error_type] == expected_codes


def test_error_level_is_str_enum() -> None:
    """ErrorLevel values are usable as plain strings."""
    assert f"level: {ErrorLevel.ERROR}" == "level: error"
    assert f"level: {ErrorLevel.WARNING}" == "level: warning"
    assert f"level: {ErrorLevel.INFO}" == "level: info"


def test_superset_error_type_is_str_enum() -> None:
    """SupersetErrorType values are usable as plain strings."""
    assert (
        f"type: {SupersetErrorType.GENERIC_BACKEND_ERROR}"
        == "type: GENERIC_BACKEND_ERROR"
    )
