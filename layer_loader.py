# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
"""Loading of products into QGIS (the part that DOES depend on QGIS).

Design decisions (details in docs/DECISIONS.md):

* All network traffic goes through the QGIS stack (``QgsBlockingNetworkRequest``,
  which uses QgsNetworkAccessManager), the same one the WMS/WMTS provider uses. This
  honours the proxy, certificate authorities and authentication configured in QGIS and
  makes the pre-flight check representative of what the layer will do. ``requests`` or
  ``urllib`` are never used to download data.
* Before creating the layer a pre-flight check is made (GetCapabilities and, for WMTS,
  one real tile). If it fails, the error is classified and explained instead of leaving
  an invalid layer in the layer panel.
* Certificate verification is never disabled and no SSL exceptions are made.
"""
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.core import (
    QgsBlockingNetworkRequest, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsPointXY, QgsProject, QgsRasterLayer, QgsMessageLog,
)

from . import services
from .i18n import tr
from .compat import is_ok, msg_info, msg_warning

LOG_TAG = "Open AMB"
TIMEOUT_MS = 15000
GROUP_NAME = "Open AMB"
# Plaça de Catalunya (approx.), used to centre the map where there is data.
_CENTER_LONLAT = (2.1700, 41.3870)


def log(message, level=None):
    QgsMessageLog.logMessage(message, LOG_TAG, level if level is not None else msg_info())


class ProbeResult(object):
    def __init__(self, ok, kind=None, message="", http_status=None, content=b"", url=""):
        self.ok = ok
        self.kind = kind
        self.message = message
        self.http_status = http_status
        self.content = content
        self.url = url


def fetch(url, timeout_ms=TIMEOUT_MS):
    """GET through the QGIS network stack. Returns a ProbeResult (never raises network errors)."""
    request = QNetworkRequest(QUrl(url))
    if hasattr(request, "setTransferTimeout"):
        request.setTransferTimeout(timeout_ms)
    blocking = QgsBlockingNetworkRequest()
    err = blocking.get(request)
    reply = blocking.reply()
    status = None
    try:
        attr = getattr(QNetworkRequest, "Attribute", QNetworkRequest).HttpStatusCodeAttribute
        status = reply.attribute(attr)
    except Exception:  # noqa: BLE001
        status = None
    if is_ok(err) and (status is None or int(status) < 400):
        return ProbeResult(True, http_status=status, content=bytes(reply.content()), url=url)
    message = blocking.errorMessage() or reply.errorString() or ""
    kind = services.classify_error(message, int(status) if status else None)
    return ProbeResult(False, kind=kind, message=message, http_status=status, url=url)


def probe_source(src):
    """Check the service answers before creating the layer. Returns (ProbeResult, [log lines])."""
    notes = []
    caps = fetch(services.capabilities_request_url(src))
    notes.append("GetCapabilities %s -> %s" % (caps.url, "OK" if caps.ok else "ERROR (%s) %s" % (caps.kind, caps.message)))
    if not caps.ok:
        return caps, notes
    if src["type"] == "arcgis":
        info, kind, message = services.parse_arcgis_metadata(caps.content)
        if info is None:
            notes.append("ArcGIS metadata not usable (%s): %s" % (kind, message))
            return ProbeResult(False, kind, message, caps.http_status, url=caps.url), notes
        if info["crs"]:
            src["crs"] = info["crs"]
        notes.append("ArcGIS service: crs=%s tiled=%s" % (info["crs"], info["tiled"]))
        return caps, notes
    if src["type"] == "wmts" and src.get("preflight_tile") and src.get("tile_template"):
        pt = src["preflight_tile"]
        x, y = _center_in_crs(src["crs"])
        row, col = services.tile_for_point(x, y, pt["origin"], pt["resolution"], pt.get("tile_size", 256))
        url = services.tile_url(src["tile_template"], pt["z"], row, col)
        tile = fetch(url)
        if tile.ok and not services.looks_like_png(tile.content):
            tile = ProbeResult(False, services.HTTP, "The tile response is not a PNG image.", tile.http_status, url=url)
        notes.append("Tile %s -> %s" % (url, "OK" if tile.ok else "ERROR (%s) %s" % (tile.kind, tile.message)))
        if not tile.ok:
            return tile, notes
    return caps, notes


def _center_in_crs(crs_authid):
    src = QgsCoordinateReferenceSystem("EPSG:4326")
    dst = QgsCoordinateReferenceSystem(crs_authid)
    p = QgsCoordinateTransform(src, dst, QgsProject.instance()).transform(QgsPointXY(*_CENTER_LONLAT))
    return p.x(), p.y()


class LoadOutcome(object):
    def __init__(self):
        self.success = False
        self.layer = None
        self.source = None
        self.kind = None            # error category (services.CERT, ...)
        self.user_message = ""
        self.technical = []         # technical lines (for the log and the diagnostics)
        self.failed_url = None
        self.experimental = False   # loaded from an unverified (candidate) service


def source_label(src):
    """Name of a source in the active interface language."""
    return tr(src["label_key"]) if src.get("label_key") else src.get("type", "?")


def attribution_for(product, src):
    """Attribution as declared by the Geoportal for the product; the licence is added only when
    the service itself declares it (``license`` in the source), never assumed."""
    parts = [product.attribution] if product.attribution else []
    if src.get("license"):
        parts.append(src["license"])
    return " — ".join(parts)


def load_product(iface, product):
    """Load a verified product. Sources are tried in order; a certificate error stops at once."""
    out = LoadOutcome()
    if not product.loadable:
        out.user_message = tr("ld_not_verified", name=product.name)
        return out

    # Verified products use their hand-checked sources; experimental candidates use the ArcGIS
    # service listed by the Geoportal, over https only.
    sources = product.sources if product.verified else [services.arcgis_source(product.listed_url)]
    out.experimental = not product.verified

    for src in sources:
        src = dict(src)       # the pre-flight may add the CRS: never modify the catalogue data
        probe, notes = probe_source(src)
        out.technical.extend(notes)
        if not probe.ok:
            out.kind, out.failed_url = probe.kind, probe.url
            out.user_message = services.user_message(probe.kind)
            out.technical.append("Detall: " + (probe.message or "(no message)"))
            if probe.kind == services.CERT:
                break  # another service on the same host would fail the same way
            continue

        provider = "arcgismapserver" if src["type"] == "arcgis" else "wms"
        layer = QgsRasterLayer(services.build_uri(src), product.name, provider)
        if not layer.isValid():
            detail = ""
            try:
                detail = layer.error().summary()
            except Exception:  # noqa: BLE001
                pass
            out.kind = services.UNKNOWN
            out.user_message = tr("ld_invalid_layer")
            out.technical.append("Invalid QgsRasterLayer (%s). URI: %s. %s" % (source_label(src), services.build_uri(src), detail))
            continue

        try:
            layer.setAttribution(attribution_for(product, src))
        except Exception:  # noqa: BLE001
            pass
        _add_to_project(layer)
        _zoom(iface, layer, src)
        out.success, out.layer, out.source, out.kind = True, layer, src, None
        out.user_message = tr("ld_loaded", name=product.name, source=source_label(src))
        if src.get("note_key"):
            out.user_message += " " + tr(src["note_key"])
        if out.experimental:
            out.user_message += " " + tr("ld_experimental")
        out.technical.append("Layer added from source: " + source_label(src))
        break

    for line in out.technical:
        log(line, msg_info() if out.success else msg_warning())
    return out


def _add_to_project(layer):
    project = QgsProject.instance()
    root = project.layerTreeRoot()
    group = root.findGroup(GROUP_NAME) or root.addGroup(GROUP_NAME)
    project.addMapLayer(layer, False)
    group.insertLayer(0, layer)


def _zoom(iface, layer, src):
    canvas = iface.mapCanvas()
    dest = canvas.mapSettings().destinationCrs()
    if src["type"] == "arcgis":
        # Unknown coverage (coast, historic flights...): zoom to the layer, not to a fixed point.
        extent = layer.extent()
        if extent is not None and not extent.isEmpty():
            canvas.setExtent(QgsCoordinateTransform(layer.crs(), dest, QgsProject.instance()).transformBoundingBox(extent))
            canvas.refresh()
            return
    transform = QgsCoordinateTransform(QgsCoordinateReferenceSystem("EPSG:4326"), dest, QgsProject.instance())
    center = transform.transform(QgsPointXY(*_CENTER_LONLAT))
    canvas.setCenter(center)
    # The dynamic WMS only draws at scales larger than ~1:4,700: zoom in for it.
    canvas.zoomScale(2000 if src["type"] == "wms" else 5000)
    canvas.refresh()
