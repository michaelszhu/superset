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
from functools import partial
from typing import Optional

from sqlalchemy import update
from sqlalchemy.orm import InstrumentedAttribute

from superset.commands.base import BaseCommand
from superset.commands.theme.exceptions import ThemeNotFoundError
from superset.daos.theme import ThemeDAO
from superset.extensions import db
from superset.models.core import Theme
from superset.utils.decorators import on_error, transaction

logger = logging.getLogger(__name__)


class _SetSystemThemeCommand(BaseCommand):
    """Set a theme as the active theme for a given system role (default or dark)."""

    _column: InstrumentedAttribute
    _role_label: str

    def __init__(self, theme_id: int):
        self._theme_id = theme_id
        self._theme: Optional[Theme] = None

    @transaction(on_error=partial(on_error, reraise=Exception))
    def run(self) -> Theme:
        self.validate()
        assert self._theme

        db.session.execute(
            update(Theme)
            .where(self._column.is_(True))
            .values({self._column.key: False})
        )

        setattr(self._theme, self._column.key, True)
        db.session.add(self._theme)

        logger.info("Set theme %s as system %s", self._theme_id, self._role_label)

        return self._theme

    def validate(self) -> None:
        self._theme = ThemeDAO.find_by_id(self._theme_id)
        if not self._theme:
            raise ThemeNotFoundError()


class SetSystemDefaultThemeCommand(_SetSystemThemeCommand):
    _column = Theme.is_system_default
    _role_label = "default"


class SetSystemDarkThemeCommand(_SetSystemThemeCommand):
    _column = Theme.is_system_dark
    _role_label = "dark"


class _ClearSystemThemeCommand(BaseCommand):
    """Clear whichever theme is marked as the active theme for a system role."""

    _column: InstrumentedAttribute
    _role_label: str

    @transaction(on_error=partial(on_error, reraise=Exception))
    def run(self) -> None:
        db.session.execute(
            update(Theme)
            .where(self._column.is_(True))
            .values({self._column.key: False})
        )

        logger.info("Cleared system %s theme", self._role_label)

    def validate(self) -> None:
        pass


class ClearSystemDefaultThemeCommand(_ClearSystemThemeCommand):
    _column = Theme.is_system_default
    _role_label = "default"


class ClearSystemDarkThemeCommand(_ClearSystemThemeCommand):
    _column = Theme.is_system_dark
    _role_label = "dark"
