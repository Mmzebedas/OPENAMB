# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
"""Geoservice logic WITHOUT any QGIS dependency (so it can be tested outside QGIS).

Contains:
* builders for the QGIS WMS/WMTS provider URIs,
* tile arithmetic used by the pre-flight check,
* classification of network errors,
* a verified TLS handshake check using only the Python standard library.

Security note: this module never disables certificate verification. Reading the
certificate chain presented by a server (which requires an unverified handshake)
lives ONLY in ``tools/diagnose_tls.py``, which is not part of the plugin package.
"""
import json
import math
import socket
import ssl
from urllib.parse import urlparse

from .i18n import tr

# --------------------------------------------------------------------------
# QGIS provider URIs
# --------------------------------------------------------------------------


def _enc(value):
    """Escape characters that would break the 'key=value&key=value' provider string."""
    return value.replace("%", "%25").replace("&", "%26").replace("=", "%3D").replace("#", "%23")


def build_wmts_uri(src):
    """URI for ``QgsRasterLayer(uri, name, "wms")`` from a catalog ``wmts`` source."""
    parts = [
        "contextualWMSLegend=0",
        "crs=" + src["crs"],
        "dpiMode=7",
        "featureCount=10",
        "format=" + src.get("format", "image/png"),
        "layers=" + _enc(src["layer"]),
        "styles=" + _enc(src.get("style", "default")),
        "tileMatrixSet=" + _enc(src["tile_matrix_set"]),
        "url=" + _enc(src["capabilities_url"]),
    ]
    return "&".join(parts)


def build_wms_uri(src):
    """URI for a ``wms`` source: one ``layers=``/``styles=`` pair per sublayer."""
    parts = ["contextualWMSLegend=0", "crs=" + src["crs"], "dpiMode=7", "featureCount=10",
             "format=" + src["format"]]
    for lyr in src["layers"]:
        parts.append("layers=" + _enc(str(lyr)))
        parts.append("styles=")
    parts.append("url=" + _enc(src["url"]))
    return "&".join(parts)


def _q(value):
    """Quote a value for the ``key='value'`` style of the QGIS ArcGIS provider."""
    return value.replace("\\", "\\\\").replace("'", "\\'")


def arcgis_source(url):
    """Source for an ArcGIS REST ``MapServer`` listed by the Geoportal.

    The Geoportal file lists plain ``http://`` addresses. The https version of the SAME address
    is tried; plain http is never used, and there is no silent fallback to it.
    """
    if url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    if not url.startswith("https://"):
        raise ValueError("Unsupported service URL: %r" % url)
    return {"type": "arcgis", "url": url.rstrip("/"), "label_key": "src_arcgis", "note_key": "note_arcgis"}


def build_arcgis_uri(src):
    """URI for ``QgsRasterLayer(uri, name, "arcgismapserver")``."""
    parts = []
    if src.get("crs"):
        parts.append("crs='%s'" % _q(src["crs"]))
    parts.append("url='%s'" % _q(src["url"]))
    return " ".join(parts)


def parse_arcgis_metadata(content):
    """Interpret the ``?f=json`` answer of an ArcGIS MapServer.

    Returns ``(info, error_kind, message)``; ``info`` is None when it is not usable metadata.
    """
    try:
        data = json.loads(bytes(content).decode("utf-8", "replace"))
    except ValueError:
        return None, HTTP, "The answer is not JSON (it is probably not an ArcGIS service)."
    if not isinstance(data, dict):
        return None, HTTP, "Unexpected answer from the service."
    if "error" in data:
        err = data["error"] if isinstance(data["error"], dict) else {}
        code = err.get("code")
        kind = AUTH if code in (401, 403, 498, 499) else HTTP
        return None, kind, "Service error %s: %s" % (code, err.get("message", ""))
    if not any(k in data for k in ("layers", "mapName", "spatialReference", "fullExtent")):
        return None, HTTP, "The answer is not ArcGIS MapServer metadata."
    sr = data.get("spatialReference") or {}
    wkid = sr.get("latestWkid") or sr.get("wkid")
    if wkid == 102100:
        wkid = 3857
    return {"crs": "EPSG:%d" % wkid if isinstance(wkid, int) else None,
            "tiled": bool(data.get("singleFusedMapCache"))}, None, ""


def build_uri(src):
    if src["type"] == "arcgis":
        return build_arcgis_uri(src)
    if src["type"] == "wmts":
        return build_wmts_uri(src)
    if src["type"] == "wms":
        return build_wms_uri(src)
    raise ValueError("Unsupported source type: %r" % src.get("type"))


def capabilities_request_url(src):
    """GetCapabilities URL used by the pre-flight check (for ArcGIS: the ``?f=json`` metadata)."""
    if src["type"] == "arcgis":
        return src["url"] + "?f=json"
    if src["type"] == "wmts":
        return src["capabilities_url"]
    sep = "&" if "?" in src["url"] else "?"
    return src["url"] + sep + "SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.3.0"


def host_of(url):
    return urlparse(url).hostname


# --------------------------------------------------------------------------
# Tiles (pre-flight check of the cached WMTS service)
# --------------------------------------------------------------------------

def tile_for_point(x, y, origin, resolution, tile_size=256):
    """Row and column of the tile containing (x, y) for a top-left-origin tiling scheme."""
    span = resolution * tile_size
    col = int(math.floor((x - origin[0]) / span))
    row = int(math.floor((origin[1] - y) / span))
    return row, col


def tile_url(template, z, row, col):
    return template.replace("{z}", str(z)).replace("{row}", str(row)).replace("{col}", str(col))


PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def looks_like_png(data):
    return bool(data) and data[:8] == PNG_MAGIC


# --------------------------------------------------------------------------
# Error classification
# --------------------------------------------------------------------------
CERT = "certificat"
DNS = "dns"
TIMEOUT = "timeout"
PROXY = "proxy"
AUTH = "autenticacio"
HTTP = "http"
UNKNOWN = "desconegut"

# Keywords in English and in the languages Qt/OpenSSL may localise messages into.
_CERT_WORDS = ("certificat", "certificate", "ssl", "tls", "issuer", "emisor", "emissor",
               "handshake", "self signed", "autofirmat", "verify")
_DNS_WORDS = ("host not found", "name or service not known", "nodename nor servname",
              "getaddrinfo", "no se encuentra el host", "host no encontrado", "dns", "remote host")
_TIMEOUT_WORDS = ("timed out", "timeout", "tiempo de espera", "temps d'espera")
_PROXY_WORDS = ("proxy",)
_AUTH_WORDS = ("authentication", "autenticaci", "unauthorized", "forbidden", "token")


def classify_error(message, http_status=None):
    """Classify an error message. Heuristic: meant to guide the user, not to prove a cause."""
    m = (message or "").lower()
    if http_status in (401, 403, 407):
        return PROXY if http_status == 407 else AUTH
    if http_status and http_status >= 400:
        return HTTP
    if any(w in m for w in _CERT_WORDS):
        return CERT
    if any(w in m for w in _TIMEOUT_WORDS):
        return TIMEOUT
    if any(w in m for w in _PROXY_WORDS):
        return PROXY
    if any(w in m for w in _DNS_WORDS):
        return DNS
    if any(w in m for w in _AUTH_WORDS):
        return AUTH
    return UNKNOWN


def user_message(kind):
    """User-facing message (in the active interface language) for an error category."""
    key = "err_" + {CERT: "cert", DNS: "dns", TIMEOUT: "timeout", PROXY: "proxy", AUTH: "auth", HTTP: "http"}.get(kind, "unknown")
    return tr(key)


# --------------------------------------------------------------------------
# TLS diagnostics with plain Python (independent of QGIS)
# --------------------------------------------------------------------------

def python_tls_check(host, port=443, timeout=10.0):
    """VERIFIED TLS handshake using the system trust store as seen by Python.

    Returns ``{"ok": bool, "error": str|None, "verify_code": int|None}``.
    Verification is never disabled here.
    """
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as tls:
                return {"ok": True, "error": None, "verify_code": None, "version": tls.version()}
    except ssl.SSLCertVerificationError as exc:
        return {"ok": False, "error": exc.verify_message or str(exc), "verify_code": exc.verify_code}
    except (OSError, ssl.SSLError) as exc:
        return {"ok": False, "error": str(exc), "verify_code": None}


def interpret(qgis_kind, py_check, chain=None):
    """Orientation sentences (hypotheses, not conclusions) from the diagnostic results.

    ``chain`` is optional: it is only provided by the standalone tool, which can read
    the certificates the server presents.
    """
    lines = []
    py_ok = py_check.get("ok") if py_check else None
    if qgis_kind == CERT and py_ok is True:
        lines.append(tr("in_py_ok"))
    elif qgis_kind == CERT and py_ok is False:
        lines.append(tr("in_both_fail"))
        lines.append(tr("in_tool"))
        if chain and chain.get("certs"):
            first = chain["certs"][0]
            lines.append(tr("in_issuer", issuer=first.get("issuer", "?")))
            ca_urls = first.get("ca_issuers") or []
            if ca_urls and len(chain["certs"]) == 1:
                lines.append(tr("in_intermediate", urls=", ".join(ca_urls)))
    elif qgis_kind not in (None, CERT):
        lines.append(tr("in_not_cert", kind=qgis_kind))
    elif qgis_kind is None and py_ok:
        lines.append(tr("in_all_ok"))
    return lines
