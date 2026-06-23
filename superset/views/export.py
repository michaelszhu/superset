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
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Callable, Iterator
from zipfile import ZipFile

from flask import request, send_file
from werkzeug.wrappers import Response

from superset.utils.core import sanitize_cookie_token


def export_as_zip(
    resource_name: str,
    export_command_runner: Iterator[tuple[str, Callable[[], str]]],
) -> Response:
    """Build a ZIP archive from an export command and return it as a response.

    :param resource_name: used to form the ZIP filename, e.g. ``"chart"``
    :param export_command_runner: iterator yielded by an export command's
        ``run()`` method, producing ``(file_name, content_callable)`` pairs
    :returns: a Flask response streaming the ZIP file
    """
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    root = f"{resource_name}_export_{timestamp}"
    filename = f"{root}.zip"

    buf = BytesIO()
    with ZipFile(buf, "w") as bundle:
        for file_name, file_content in export_command_runner:
            with bundle.open(f"{root}/{file_name}", "w") as fp:
                fp.write(file_content().encode())
    buf.seek(0)

    response = send_file(
        buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name=filename,
    )
    if token := sanitize_cookie_token(request.args.get("token")):
        response.set_cookie(token, "done", max_age=600)
    return response
