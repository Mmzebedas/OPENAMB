# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
"""Small helpers to work with both QGIS 3 (Qt5) and QGIS 4 (Qt6).

Qt is always imported through ``qgis.PyQt`` (never ``PyQt5`` directly) and scoped
enums are used (``Qt.ItemDataRole.UserRole``), which Qt6 requires.
"""
from qgis.core import Qgis


def _level(name):
    enum = getattr(Qgis, "MessageLevel", Qgis)  # QGIS >= 3.30: Qgis.MessageLevel.X
    return getattr(enum, name)


def msg_info():
    return _level("Info")


def msg_warning():
    return _level("Warning")


def msg_critical():
    return _level("Critical")


def msg_success():
    return _level("Success")


def exec_dialog(dialog):
    """exec_() on Qt5 / exec() on Qt6."""
    return dialog.exec() if hasattr(dialog, "exec") else dialog.exec_()


def is_ok(error_code):
    """Compare a QgsBlockingNetworkRequest.ErrorCode with NoError (=0) without relying on the enum."""
    return int(getattr(error_code, "value", error_code)) == 0
