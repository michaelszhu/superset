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
from collections import defaultdict

import pytest
from marshmallow import ValidationError

from superset.errors import ErrorLevel, SupersetError, SupersetErrorType
from superset.exceptions import (
    AcquireDistributedLockFailedException,
    AdvancedDataTypeResponseError,
    CacheLoadError,
    CertificateException,
    ColumnNotFoundException,
    DashboardImportException,
    DatabaseNotFound,
    DatabaseNotFoundException,
    DatasetInvalidPermissionEvaluationException,
    InvalidPayloadFormatError,
    InvalidPayloadSchemaError,
    InvalidPostProcessingError,
    MissingUserContextException,
    NoDataException,
    NullValueException,
    OAuth2Error,
    OAuth2RedirectError,
    OAuth2TokenRefreshError,
    QueryClauseValidationException,
    QueryNotFoundException,
    QueryObjectValidationError,
    ReleaseDistributedLockFailedException,
    ScreenshotImageNotAvailableException,
    SerializationError,
    SpatialException,
    SupersetCancelQueryException,
    SupersetDisallowedSQLFunctionException,
    SupersetDisallowedSQLTableException,
    SupersetDMLNotAllowedException,
    SupersetErrorException,
    SupersetErrorFromParamsException,
    SupersetErrorsException,
    SupersetException,
    SupersetGenericDBErrorException,
    SupersetGenericErrorException,
    SupersetInvalidCTASException,
    SupersetInvalidCVASException,
    SupersetMarshmallowValidationError,
    SupersetParseError,
    SupersetResultsBackendNotConfigureException,
    SupersetSecurityException,
    SupersetSyntaxErrorException,
    SupersetTemplateException,
    SupersetTemplateParamsErrorException,
    SupersetTimeoutException,
    SupersetVizException,
    TableNotFoundException,
)


def test_superset_exception_default_status() -> None:
    exc = SupersetException("test error")
    assert exc.status == 500
    assert exc.message == "test error"
    assert str(exc) == "test error"
    assert exc.exception is None
    assert exc.error_type is None


def test_superset_exception_with_nested_exception() -> None:
    inner = ValueError("inner problem")
    exc = SupersetException("outer", exception=inner)
    assert exc.exception is inner


def test_superset_exception_with_error_type() -> None:
    exc = SupersetException(
        "typed error",
        error_type=SupersetErrorType.GENERIC_BACKEND_ERROR,
    )
    assert exc.error_type == SupersetErrorType.GENERIC_BACKEND_ERROR


def test_superset_exception_to_dict() -> None:
    exc = SupersetException(
        "msg",
        error_type=SupersetErrorType.GENERIC_BACKEND_ERROR,
    )
    d = exc.to_dict()
    assert d["message"] == "msg"
    assert d["error_type"] == SupersetErrorType.GENERIC_BACKEND_ERROR


def test_superset_exception_to_dict_with_nested_exception_to_dict() -> None:
    """When the nested exception has a to_dict, its contents are merged."""

    class InnerError(Exception):  # noqa: N818
        def to_dict(self) -> dict[str, str]:
            return {"detail": "inner detail"}

    exc = SupersetException("outer", exception=InnerError())
    d = exc.to_dict()
    assert d["message"] == "outer"
    assert d["detail"] == "inner detail"


def test_superset_error_exception() -> None:
    error = SupersetError(
        message="err msg",
        error_type=SupersetErrorType.GENERIC_BACKEND_ERROR,
        level=ErrorLevel.ERROR,
    )
    exc = SupersetErrorException(error, status=400)
    assert exc.status == 400
    assert exc.error is error
    assert exc.to_dict() == error.to_dict()


def test_superset_error_exception_default_status() -> None:
    error = SupersetError(
        message="err msg",
        error_type=SupersetErrorType.GENERIC_BACKEND_ERROR,
        level=ErrorLevel.ERROR,
    )
    exc = SupersetErrorException(error)
    assert exc.status == 500


def test_superset_generic_error_exception() -> None:
    exc = SupersetGenericErrorException("something broke")
    assert exc.error.error_type == SupersetErrorType.GENERIC_BACKEND_ERROR
    assert exc.error.level == ErrorLevel.ERROR
    assert exc.error.message == "something broke"
    assert exc.status == 500


def test_superset_generic_error_exception_custom_status() -> None:
    exc = SupersetGenericErrorException("bad request", status=400)
    assert exc.status == 400


def test_superset_error_from_params_exception() -> None:
    exc = SupersetErrorFromParamsException(
        error_type=SupersetErrorType.SYNTAX_ERROR,
        message="parse fail",
        level=ErrorLevel.WARNING,
        extra={"line": 42},
    )
    assert exc.error.error_type == SupersetErrorType.SYNTAX_ERROR
    assert exc.error.message == "parse fail"
    assert exc.error.level == ErrorLevel.WARNING
    assert exc.error.extra is not None
    assert exc.error.extra["line"] == 42


def test_superset_errors_exception() -> None:
    errors = [
        SupersetError(
            message="err1",
            error_type=SupersetErrorType.SYNTAX_ERROR,
            level=ErrorLevel.ERROR,
        ),
        SupersetError(
            message="err2",
            error_type=SupersetErrorType.GENERIC_BACKEND_ERROR,
            level=ErrorLevel.WARNING,
        ),
    ]
    exc = SupersetErrorsException(errors, status=422)
    assert exc.status == 422
    assert len(exc.errors) == 2


def test_superset_syntax_error_exception() -> None:
    errors = [
        SupersetError(
            message="bad sql",
            error_type=SupersetErrorType.SYNTAX_ERROR,
            level=ErrorLevel.ERROR,
        ),
    ]
    exc = SupersetSyntaxErrorException(errors)
    assert exc.status == 422
    assert exc.error_type == SupersetErrorType.SYNTAX_ERROR


def test_superset_timeout_exception() -> None:
    exc = SupersetTimeoutException(
        error_type=SupersetErrorType.BACKEND_TIMEOUT_ERROR,
        message="timed out",
        level=ErrorLevel.ERROR,
    )
    assert exc.status == 408


def test_superset_generic_db_error_exception() -> None:
    exc = SupersetGenericDBErrorException(message="db error")
    assert exc.status == 400
    assert exc.error.error_type == SupersetErrorType.GENERIC_DB_ENGINE_ERROR
    assert exc.error.level == ErrorLevel.ERROR


def test_superset_generic_db_error_exception_custom_extra() -> None:
    exc = SupersetGenericDBErrorException(
        message="db error",
        extra={"engine": "postgres"},
    )
    assert exc.error.extra is not None
    assert exc.error.extra["engine"] == "postgres"


def test_superset_template_params_error_exception() -> None:
    exc = SupersetTemplateParamsErrorException(
        message="missing param",
        error=SupersetErrorType.MISSING_TEMPLATE_PARAMS_ERROR,
    )
    assert exc.status == 400
    assert exc.error.error_type == SupersetErrorType.MISSING_TEMPLATE_PARAMS_ERROR


def test_superset_security_exception() -> None:
    error = SupersetError(
        message="access denied",
        error_type=SupersetErrorType.DATASOURCE_SECURITY_ACCESS_ERROR,
        level=ErrorLevel.ERROR,
    )
    exc = SupersetSecurityException(error, payload={"dashboard_id": 1})
    assert exc.status == 403
    assert exc.payload == {"dashboard_id": 1}


def test_superset_viz_exception() -> None:
    exc = SupersetVizException(errors=[], status=400)
    assert exc.status == 400


@pytest.mark.parametrize(
    "exc_class,expected_status",
    [
        (NoDataException, 400),
        (NullValueException, 400),
        (SupersetTemplateException, 422),
        (DatabaseNotFound, 400),
        (MissingUserContextException, 422),
        (QueryObjectValidationError, 400),
        (AdvancedDataTypeResponseError, 400),
        (InvalidPostProcessingError, 400),
        (CacheLoadError, 404),
        (QueryClauseValidationException, 400),
        (SupersetCancelQueryException, 422),
        (QueryNotFoundException, 404),
        (ColumnNotFoundException, 404),
        (ScreenshotImageNotAvailableException, 404),
    ],
)
def test_simple_exception_status_codes(
    exc_class: type[SupersetException], expected_status: int
) -> None:
    exc = exc_class("test")
    assert exc.status == expected_status


def test_spatial_exception_inherits_superset_exception() -> None:
    exc = SpatialException("spatial error")
    assert isinstance(exc, SupersetException)
    assert exc.status == 500


def test_certificate_exception_default_message() -> None:
    exc = CertificateException()
    assert exc.message


def test_dashboard_import_exception() -> None:
    exc = DashboardImportException("import failed")
    assert isinstance(exc, SupersetException)


def test_dataset_invalid_permission_evaluation_exception() -> None:
    exc = DatasetInvalidPermissionEvaluationException("bad perms")
    assert isinstance(exc, SupersetException)


def test_serialization_error() -> None:
    exc = SerializationError("cannot serialize")
    assert isinstance(exc, SupersetException)


def test_invalid_payload_format_error() -> None:
    exc = InvalidPayloadFormatError()
    assert exc.status == 400
    assert exc.error.error_type == SupersetErrorType.INVALID_PAYLOAD_FORMAT_ERROR


def test_invalid_payload_format_error_custom_message() -> None:
    exc = InvalidPayloadFormatError("custom format error")
    assert exc.error.message == "custom format error"


def test_invalid_payload_schema_error() -> None:
    validation_error = ValidationError({"field": ["required"]})
    exc = InvalidPayloadSchemaError(validation_error)
    assert exc.status == 422
    assert exc.error.error_type == SupersetErrorType.INVALID_PAYLOAD_SCHEMA_ERROR
    assert exc.error.extra is not None
    assert "messages" in exc.error.extra


def test_invalid_payload_schema_error_with_defaultdict() -> None:
    """defaultdict values are converted to plain dicts."""
    msgs: dict[str, defaultdict[str, list[str]]] = {
        "nested": defaultdict(list, {"sub": ["error"]})
    }
    validation_error = ValidationError(msgs)
    exc = InvalidPayloadSchemaError(validation_error)
    assert exc.error.extra is not None
    assert isinstance(exc.error.extra["messages"]["nested"], dict)


def test_superset_marshmallow_validation_error() -> None:
    validation_error = ValidationError({"name": ["too short"]})
    exc = SupersetMarshmallowValidationError(validation_error, payload={"name": "x"})
    assert exc.status == 422
    assert exc.error.error_type == SupersetErrorType.MARSHMALLOW_ERROR
    assert exc.error.extra is not None
    assert exc.error.extra["payload"] == {"name": "x"}
    assert exc.error.extra["messages"] == {"name": ["too short"]}


def test_superset_parse_error_default_message() -> None:
    exc = SupersetParseError(sql="SELECT * FORM t")
    assert exc.status == 422
    assert exc.error.error_type == SupersetErrorType.INVALID_SQL_ERROR
    assert exc.error.extra is not None
    assert exc.error.extra["sql"] == "SELECT * FORM t"


def test_superset_parse_error_with_highlight_and_position() -> None:
    exc = SupersetParseError(
        sql="SELECT",
        engine="sqlite",
        highlight="FORM",
        line=1,
        column=10,
    )
    assert "FORM" in str(exc)
    assert exc.error.extra is not None
    assert exc.error.extra["engine"] == "sqlite"
    assert exc.error.extra["line"] == 1
    assert exc.error.extra["column"] == 10


def test_superset_parse_error_custom_message() -> None:
    exc = SupersetParseError(sql="bad", message="custom parse error")
    assert str(exc) == "custom parse error"


def test_oauth2_redirect_error() -> None:
    exc = OAuth2RedirectError(
        url="https://example.com/oauth",
        tab_id="tab-123",
        redirect_uri="https://superset.example.com/callback",
    )
    assert exc.status == 403
    assert exc.error.error_type == SupersetErrorType.OAUTH2_REDIRECT
    assert exc.error.extra is not None
    assert exc.error.extra["url"] == "https://example.com/oauth"
    assert exc.error.extra["tab_id"] == "tab-123"
    assert exc.error.extra["redirect_uri"] == "https://superset.example.com/callback"


def test_oauth2_token_refresh_error() -> None:
    exc = OAuth2TokenRefreshError("token expired")
    assert isinstance(exc, OAuth2RedirectError)
    assert exc.error.error_type == SupersetErrorType.OAUTH2_REDIRECT
    assert exc.error.extra is not None
    assert exc.error.extra["error"] == "token expired"


def test_oauth2_error() -> None:
    exc = OAuth2Error("something failed")
    assert exc.error.error_type == SupersetErrorType.OAUTH2_REDIRECT_ERROR
    assert exc.error.extra is not None
    assert exc.error.extra["error"] == "something failed"


def test_superset_disallowed_sql_function_exception() -> None:
    exc = SupersetDisallowedSQLFunctionException({"SLEEP", "BENCHMARK"})
    assert exc.error.error_type == SupersetErrorType.SYNTAX_ERROR
    assert "SLEEP" in exc.error.message or "BENCHMARK" in exc.error.message


def test_superset_disallowed_sql_table_exception() -> None:
    exc = SupersetDisallowedSQLTableException({"secrets_table"})
    assert exc.error.error_type == SupersetErrorType.SYNTAX_ERROR
    assert "secrets_table" in exc.error.message


def test_acquire_distributed_lock_failed_exception() -> None:
    exc = AcquireDistributedLockFailedException("lock fail")
    assert isinstance(exc, Exception)
    assert not isinstance(exc, SupersetException)


def test_release_distributed_lock_failed_exception() -> None:
    exc = ReleaseDistributedLockFailedException("release fail")
    assert isinstance(exc, Exception)
    assert not isinstance(exc, SupersetException)


def test_database_not_found_exception() -> None:
    exc = DatabaseNotFoundException("db missing")
    assert exc.status == 404
    assert exc.error.error_type == SupersetErrorType.DATABASE_NOT_FOUND_ERROR


def test_table_not_found_exception() -> None:
    exc = TableNotFoundException("table missing")
    assert exc.status == 404
    assert exc.error.error_type == SupersetErrorType.TABLE_NOT_FOUND_ERROR


def test_superset_dml_not_allowed_exception() -> None:
    exc = SupersetDMLNotAllowedException()
    assert exc.error.error_type == SupersetErrorType.DML_NOT_ALLOWED_ERROR


def test_superset_invalid_ctas_exception() -> None:
    exc = SupersetInvalidCTASException()
    assert exc.error.error_type == SupersetErrorType.INVALID_CTAS_QUERY_ERROR


def test_superset_invalid_cvas_exception() -> None:
    exc = SupersetInvalidCVASException()
    assert exc.error.error_type == SupersetErrorType.INVALID_CVAS_QUERY_ERROR


def test_superset_results_backend_not_configured_exception() -> None:
    exc = SupersetResultsBackendNotConfigureException()
    assert (
        exc.error.error_type == SupersetErrorType.RESULTS_BACKEND_NOT_CONFIGURED_ERROR
    )
