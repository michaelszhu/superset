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
import logging
from unittest.mock import MagicMock

import pytest

from superset.stats_logger import BaseStatsLogger, DummyStatsLogger


def test_base_stats_logger_key_with_prefix() -> None:
    logger = BaseStatsLogger(prefix="myapp")
    assert logger.key(".requests") == "myapp.requests"


def test_base_stats_logger_key_without_prefix() -> None:
    logger = BaseStatsLogger(prefix="")
    assert logger.key(".requests") == ".requests"


def test_base_stats_logger_default_prefix() -> None:
    logger = BaseStatsLogger()
    assert logger.prefix == "superset"
    assert logger.key(".metric") == "superset.metric"


def test_base_stats_logger_incr_not_implemented() -> None:
    logger = BaseStatsLogger()
    with pytest.raises(NotImplementedError):
        logger.incr("counter")


def test_base_stats_logger_decr_not_implemented() -> None:
    logger = BaseStatsLogger()
    with pytest.raises(NotImplementedError):
        logger.decr("counter")


def test_base_stats_logger_timing_not_implemented() -> None:
    logger = BaseStatsLogger()
    with pytest.raises(NotImplementedError):
        logger.timing("timer", 1.0)


def test_base_stats_logger_gauge_not_implemented() -> None:
    logger = BaseStatsLogger()
    with pytest.raises(NotImplementedError):
        logger.gauge("gauge_metric", 42.0)


def test_dummy_stats_logger_incr(caplog: pytest.LogCaptureFixture) -> None:
    stats = DummyStatsLogger()
    with caplog.at_level(logging.DEBUG, logger="superset.stats_logger"):
        stats.incr("test_counter")
    assert any(
        "(incr)" in r.message and "test_counter" in r.message for r in caplog.records
    )


def test_dummy_stats_logger_decr(caplog: pytest.LogCaptureFixture) -> None:
    stats = DummyStatsLogger()
    with caplog.at_level(logging.DEBUG, logger="superset.stats_logger"):
        stats.decr("test_counter")
    assert any(
        "(decr)" in r.message and "test_counter" in r.message for r in caplog.records
    )


def test_dummy_stats_logger_timing(caplog: pytest.LogCaptureFixture) -> None:
    stats = DummyStatsLogger()
    with caplog.at_level(logging.DEBUG, logger="superset.stats_logger"):
        stats.timing("request_time", 123.45)
    assert any(
        "(timing)" in r.message and "request_time" in r.message for r in caplog.records
    )


def test_dummy_stats_logger_gauge(caplog: pytest.LogCaptureFixture) -> None:
    stats = DummyStatsLogger()
    with caplog.at_level(logging.DEBUG, logger="superset.stats_logger"):
        stats.gauge("active_connections", 5.0)
    assert any(
        "(gauge)" in r.message and "active_connections" in r.message
        for r in caplog.records
    )


def test_dummy_stats_logger_does_not_raise() -> None:
    """All DummyStatsLogger methods complete without error."""
    stats = DummyStatsLogger()
    stats.incr("k")
    stats.decr("k")
    stats.timing("k", 0.0)
    stats.gauge("k", 0.0)


def test_statsd_stats_logger_with_pre_constructed_client() -> None:
    """StatsdStatsLogger delegates to a pre-constructed StatsClient."""
    from superset.stats_logger import StatsdStatsLogger

    mock_client = MagicMock()
    try:
        stats = StatsdStatsLogger(statsd_client=mock_client)
    except Exception:
        pytest.skip("statsd package not available or fallback class active")
        return

    stats.incr("req")
    mock_client.incr.assert_called_once_with("req")

    stats.decr("req")
    mock_client.decr.assert_called_once_with("req")

    stats.timing("latency", 50.0)
    mock_client.timing.assert_called_once_with("latency", 50.0)

    stats.gauge("conns", 10.0)
    mock_client.gauge.assert_called_once_with("conns", 10.0)
