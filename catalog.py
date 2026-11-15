# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
"""Product catalog of Open AMB.

This module does NOT depend on QGIS: it only reads ``data/catalog.json``, validates
it and offers name search. That makes it testable outside QGIS (see ``tests/``).

To extend the catalog no code change is needed: edit the JSON file.

Product statuses
----------------
verified   Geoservice read and loadable (has ``sources``).
candidate  The Geoportal file lists a service (over http). It can be tried as an
           EXPERIMENTAL load, over https only; it is not verified.
pending    No geoservice identified. It is never loaded.
"""
import json
import os
import re
import unicodedata

from . import i18n

VERIFIED = "verified"
CANDIDATE = "candidate"
PENDING = "pending"
VALID_STATUSES = (VERIFIED, CANDIDATE, PENDING)

_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "data", "catalog.json")


class CatalogError(Exception):
    """The catalog file is not valid."""


def _names(value):
    """Accept the legacy plain string or a ``{"ca","en","es"}`` dict."""
    return {"ca": value, "en": value, "es": value} if isinstance(value, str) else dict(value)


class Product(object):
    def __init__(self, data, category):
        self.id = data["id"]
        self.names = _names(data["name"])
        self.status = data["status"]
        self.sources = data.get("sources", [])
        self.candidate = data.get("candidate")       # earlier, unverified observation on ide.amb.cat
        self.listed = data.get("listed")             # service as listed by the Geoportal file (never loaded)
        self.note_key = data.get("note_key")
        self.attribution = data.get("attribution", "")
        self.specs = data.get("specs", {})
        self.legends = data.get("legends", {})
        self.availability = data.get("availability", "")
        self.verified_by = data.get("verified_by")    # "team" = checked by hand by the project team
        sheets = data.get("sheets")
        self.sheet_cut = SheetCut(self, sheets) if sheets else None   # sheet index, a separate menu entry
        self.category = category

    @property
    def name(self):
        """Name in the active interface language."""
        return i18n.pick(self.names)

    @property
    def verified(self):
        """Hand-verified geoservice (has ``sources``)."""
        return self.status == VERIFIED and bool(self.sources)

    @property
    def listed_url(self):
        return (self.listed or {}).get("service_url")

    @property
    def experimental(self):
        """Candidate that can be tried: the Geoportal lists a public-host service. It is loaded over
        https only, after a pre-flight check, and is NOT verified."""
        return self.status == CANDIDATE and bool(self.listed_url) and self.note_key != "internal_service"

    @property
    def loadable(self):
        return self.verified or self.experimental

    def document_url(self, kind, lang=None):
        """URL of the specification ('specs') or legend ('legends') PDF/image for a language.

        Returns ``(url, is_fallback)``. When the requested language is missing, or points to
        the very same file as Catalan, ``is_fallback`` is True so the UI can say "Catalan only".
        """
        docs = getattr(self, kind)
        lang = lang or i18n.get_language()
        url = docs.get(lang) or ""
        ca = docs.get("ca") or ""
        if not url:
            return (ca, True) if ca else ("", False)
        return url, bool(lang != "ca" and ca and url == ca)


class SheetCut(object):
    """The sheet index (tall de fulls) of a product: a separate loadable entry shown under it.

    It quacks like a Product for the loader and the dialogs (name, sources, verified, ...)."""
    status = VERIFIED
    experimental = False
    candidate = None
    listed = None
    note_key = None
    specs = {}
    legends = {}
    availability = ""
    is_sheet_cut = True

    def __init__(self, product, data):
        self.product = product
        self.id = product.id + "#sheets"
        self.sources = data["sources"]
        self.verified_by = data.get("verified_by")

    @property
    def category(self):
        return self.product.category

    @property
    def attribution(self):
        return self.product.attribution

    @property
    def names(self):
        return {l: i18n.STRINGS["sheet_cut"][l].format(name=self.product.names[l]) for l in i18n.LANGS}

    @property
    def name(self):
        return i18n.tr("sheet_cut", name=self.product.name)

    @property
    def short_name(self):
        return i18n.tr("sheet_cut_short")

    verified = True
    loadable = True

    def document_url(self, kind, lang=None):
        return "", False


class Category(object):
    def __init__(self, data):
        self.id = data["id"]
        self.names = _names(data["name"])
        self.products = [Product(p, self) for p in data["products"]]

    @property
    def name(self):
        return i18n.pick(self.names)


class Catalog(object):
    def __init__(self, categories):
        self.categories = categories

    def all_products(self):
        for c in self.categories:
            for p in c.products:
                yield p

    def all_items(self):
        """Products and their sheet indices, in menu order."""
        for p in self.all_products():
            yield p
            if p.sheet_cut:
                yield p.sheet_cut

    def get(self, item_id):
        for p in self.all_items():
            if p.id == item_id:
                return p
        return None

    def search(self, query):
        return search_products(self.all_products(), query)


# --------------------------------------------------------------------------
# Loading and validation
# --------------------------------------------------------------------------
def validate(raw):
    """Validate the JSON structure. Raises CatalogError with a clear message."""
    if not isinstance(raw, dict) or "categories" not in raw:
        raise CatalogError("Missing key 'categories'.")
    seen = set()
    for c in raw["categories"]:
        for key in ("id", "name", "products"):
            if key not in c:
                raise CatalogError("Category without '%s': %r" % (key, c.get("name")))
        _validate_names(c["name"], "category %s" % c["id"])
        for p in c["products"]:
            for key in ("id", "name", "status"):
                if key not in p:
                    raise CatalogError("Product without '%s': %r" % (key, p.get("name")))
            label = _names(p["name"]).get("ca") or p["id"]
            _validate_names(p["name"], "product %s" % p["id"])
            if p["status"] not in VALID_STATUSES:
                raise CatalogError("Unknown status '%s' for %s" % (p["status"], label))
            if p["id"] in seen:
                raise CatalogError("Duplicated identifier: %s" % p["id"])
            seen.add(p["id"])
            listed = (p.get("listed") or {}).get("service_url")
            if listed and not listed.startswith(("http://", "https://")):
                raise CatalogError("%s: 'listed' service URL must be http(s)" % label)
            for kind in ("specs", "legends"):
                for lang, url in (p.get(kind) or {}).items():
                    if url and not url.startswith("https://"):
                        raise CatalogError("%s: %s/%s must be an https:// link (%s)" % (label, kind, lang, url))
            if p.get("availability") and not p["availability"].startswith("https://"):
                raise CatalogError("%s: availability must be an https:// link" % label)
            if p.get("sheets") is not None:
                if p["status"] != VERIFIED or not p["sheets"].get("sources"):
                    raise CatalogError("%s: 'sheets' needs a verified product and its own sources" % label)
                for s in p["sheets"]["sources"]:
                    _validate_source(label + " (sheets)", s)
            if p["status"] == VERIFIED:
                if not p.get("sources"):
                    raise CatalogError("%s is 'verified' but has no 'sources'" % label)
                for s in p["sources"]:
                    _validate_source(label, s)
            elif p.get("sources"):
                # Guarantees an unverified service can never be loaded by accident.
                raise CatalogError("%s is not 'verified' but has 'sources'" % label)


def _validate_names(value, where):
    if isinstance(value, str):
        return
    missing = [l for l in i18n.LANGS if not (value.get(l) or "").strip()]
    if missing:
        raise CatalogError("%s: missing name in %s" % (where, ", ".join(missing)))


def _validate_source(pname, s):
    t = s.get("type")
    if t == "arcgis":
        needed = ("url",)
    elif t == "wmts":
        needed = ("capabilities_url", "layer", "tile_matrix_set", "crs")
    elif t == "wms":
        needed = ("url", "layers", "crs", "format")
    else:
        raise CatalogError("%s: unknown source type %r" % (pname, t))
    for k in needed:
        if k not in s:
            raise CatalogError("%s: the %s source has no '%s'" % (pname, t, k))
    for k in ("capabilities_url", "url"):
        if k in s and not s[k].startswith("https://"):
            # Never fall back to plain HTTP silently.
            raise CatalogError("%s: the URL must be https:// (%s)" % (pname, s[k]))


def load_catalog(path=None):
    path = path or _DEFAULT_PATH
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError) as exc:
        raise CatalogError("Could not read the catalog (%s): %s" % (path, exc))
    validate(raw)
    return Catalog([Category(c) for c in raw["categories"]])


# --------------------------------------------------------------------------
# Search by name
# --------------------------------------------------------------------------
def _strip_accents(text):
    return "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))


def normalize(text):
    """Lower case, no accents, scales normalised (1:1.000 -> 1:1000)."""
    t = _strip_accents(text).lower()
    t = t.replace("·", "")  # Catalan "l·l" -> "ll"
    t = re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", t)  # thousands separator
    return t


def tokens(text):
    return [t for t in re.split(r"[^a-z0-9]+", normalize(text)) if t]


def _token_matches(qt, pt):
    if qt.isdigit():
        return qt == pt  # numbers match exactly (1000 must not find 10000)
    return pt.startswith(qt)


def search_products(products, query):
    """Products where ALL query words match the product name or its category."""
    qts = tokens(query)
    if not qts:
        return []
    results = []
    for p in products:
        # Match in all three languages, whatever the interface language is.
        pts = [t for n in p.names.values() for t in tokens(n)] + [t for n in p.category.names.values() for t in tokens(n)]
        if all(any(_token_matches(q, t) for t in pts) for q in qts):
            results.append(p)
    return results
