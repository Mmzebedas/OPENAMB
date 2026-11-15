# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
"""Open AMB: QGIS plugin to access the cartographic geoservices of the AMB."""


def classFactory(iface):  # noqa: N802 - name required by QGIS
    from .plugin import OpenAMBPlugin
    return OpenAMBPlugin(iface)
