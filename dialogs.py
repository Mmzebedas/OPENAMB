# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
"""Open AMB dialogs: catalog, search, help and connection diagnostics.

User-facing texts come from ``i18n.tr`` (English, Catalan, Spanish); code and comments are in English.
"""
import platform
import ssl
import sys
from html import escape

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QBrush, QColor, QGuiApplication
from qgis.PyQt.QtNetwork import QSslSocket
from qgis.PyQt.QtWidgets import (
    QApplication, QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPlainTextEdit, QPushButton, QSplitter, QTextBrowser, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout,
)
from qgis.core import Qgis, QgsApplication

from . import catalog as cat
from . import i18n, layer_loader, services
from .i18n import tr
from .compat import msg_success, msg_warning

ROLE = Qt.ItemDataRole.UserRole

_STATUS_KEY = {cat.VERIFIED: "st_verified", cat.CANDIDATE: "st_candidate", cat.PENDING: "st_pending"}
_TAG_KEY = {cat.CANDIDATE: "tag_candidate", cat.PENDING: "tag_pending"}


def status_key(p):
    return "st_experimental" if p.experimental else _STATUS_KEY[p.status]


def tag_key(p):
    return "tag_experimental" if p.experimental else _TAG_KEY[p.status]
_GREY = QBrush(QColor(130, 130, 130))


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------

def _link(url, label):
    return '<a href="%s">%s</a>' % (escape(url, quote=True), escape(label))


def _documents_html(p):
    """Specification, legend and availability links in the active language."""
    rows = []
    for kind, key in (("specs", "d_specs"), ("legends", "d_legend")):
        url, fallback = p.document_url(kind)
        if url:
            rows.append("<li>%s%s</li>" % (_link(url, tr(key)), " <small>%s</small>" % tr("d_only_ca") if fallback else ""))
    if p.availability:
        rows.append("<li>%s</li>" % _link(p.availability, tr("d_availability")))
    if not rows:
        return ""
    return "<p><b>%s</b></p><ul>%s</ul>" % (tr("d_documents"), "".join(rows))


def describe_product(p):
    """HTML with the status and details of a product."""
    h = ["<h3>%s</h3>" % escape(p.name),
         "<p><b>%s:</b> %s<br><b>%s:</b> %s</p>" % (tr("d_category"), escape(p.category.name),
                                                     tr("d_status"), tr(status_key(p)))]
    if p.attribution:
        h.append("<p><b>%s:</b> %s</p>" % (tr("d_attribution"), escape(p.attribution)))
    if p.verified:
        h.append("<p><b>%s:</b></p><ul>" % tr("d_sources"))
        for s_ in p.sources:
            target = s_.get("capabilities_url") or s_.get("url")
            note = "<br><i>%s</i>" % escape(tr(s_["note_key"])) if s_.get("note_key") else ""
            h.append("<li>%s<br><small>%s</small>%s</li>" % (escape(layer_loader.source_label(s_)), escape(target), note))
        h.append("</ul>")
    else:
        listed = (p.listed or {}).get("service_url")
        if listed:
            key = "d_internal" if p.note_key == "internal_service" else ("d_experimental" if p.experimental else "d_listed")
            h.append("<p>%s</p>" % tr(key, url=escape(listed)))
        if p.candidate:
            h.append("<p>%s</p>" % tr("d_candidate_ide", service=escape(p.candidate["service"])))
            h.append("<p><small>%s</small></p>" % escape(p.candidate["rest_url"]))
    if p.verified_by:
        h.append("<p><small>%s</small></p>" % tr("d_verified_by"))
    h.append(_documents_html(p))
    return "".join(h)


def load_and_report(iface, product, parent):
    """Load the product and report the result to the user in an understandable way."""
    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    try:
        outcome = layer_loader.load_product(iface, product)
    finally:
        QApplication.restoreOverrideCursor()

    if outcome.success:
        iface.messageBar().pushMessage("Open AMB", outcome.user_message, level=msg_success(), duration=12)
        return outcome

    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle("Open AMB")
    box.setText(outcome.user_message)
    box.setInformativeText(tr("ld_details"))
    box.setDetailedText("\n".join(outcome.technical))
    diag_btn = None
    if outcome.kind == services.CERT:
        diag_btn = box.addButton(tr("diag_btn"), QMessageBox.ButtonRole.ActionRole)
    box.addButton(QMessageBox.StandardButton.Close)
    box.exec() if hasattr(box, "exec") else box.exec_()
    if diag_btn is not None and box.clickedButton() is diag_btn:
        dlg = DiagnosticsDialog(parent, outcome.failed_url)
        dlg.show()
        dlg.run()
    iface.messageBar().pushMessage("Open AMB", outcome.user_message, level=msg_warning(), duration=8)
    return outcome


# --------------------------------------------------------------------------
# Catalog
# --------------------------------------------------------------------------

class CatalogDialog(QDialog):
    def __init__(self, iface, catalog, parent=None):
        super().__init__(parent)
        self.iface, self.catalog = iface, catalog
        self.setWindowTitle(tr("cat_title"))
        self.resize(900, 620)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([tr("cat_header")])
        self.detail = QTextBrowser()
        self.detail.setOpenExternalLinks(True)
        self.detail.setHtml("<p>%s</p>" % tr("cat_select"))
        self.load_btn = QPushButton(tr("load"))
        self.load_btn.setEnabled(False)
        close_btn = QPushButton(tr("close"))

        split = QSplitter()
        split.addWidget(self.tree)
        split.addWidget(self.detail)
        split.setStretchFactor(0, 2)
        split.setStretchFactor(1, 3)
        legend = QLabel("<small>%s</small>" % tr("cat_legend"))
        legend.setWordWrap(True)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self.load_btn)
        buttons.addWidget(close_btn)
        lay = QVBoxLayout(self)
        lay.addWidget(split)
        lay.addWidget(legend)
        lay.addLayout(buttons)

        self._fill()
        self.tree.currentItemChanged.connect(self._on_select)
        self.tree.itemDoubleClicked.connect(lambda *_: self._load())
        self.load_btn.clicked.connect(self._load)
        close_btn.clicked.connect(self.close)

    def _fill(self):
        self.tree.clear()
        for c in self.catalog.categories:
            ci = QTreeWidgetItem([c.name])
            font = ci.font(0)
            font.setBold(True)
            ci.setFont(0, font)
            for p in c.products:
                label = p.name if p.verified else "%s  (%s)" % (p.name, tr(tag_key(p)))
                pi = QTreeWidgetItem([label])
                pi.setData(0, ROLE, p.id)
                pi.setToolTip(0, tr(status_key(p)))
                if not p.verified:
                    pi.setForeground(0, _GREY)
                ci.addChild(pi)
                if p.sheet_cut:       # the sheet index, as a separate sub-entry under its product
                    si = QTreeWidgetItem(["↳ " + p.sheet_cut.short_name])
                    si.setData(0, ROLE, p.sheet_cut.id)
                    si.setToolTip(0, p.sheet_cut.name)
                    pi.addChild(si)
            self.tree.addTopLevelItem(ci)
        # Expand the first category so the user immediately sees an available product.
        if self.tree.topLevelItemCount():
            self.tree.topLevelItem(0).setExpanded(True)

    def _current_product(self):
        item = self.tree.currentItem()
        pid = item.data(0, ROLE) if item else None
        return self.catalog.get(pid) if pid else None

    def _on_select(self, *_):
        p = self._current_product()
        self.load_btn.setEnabled(bool(p and p.loadable))
        self.detail.setHtml(describe_product(p) if p else "<p>%s</p>" % tr("se_select"))

    def _load(self):
        p = self._current_product()
        if p and p.loadable:
            load_and_report(self.iface, p, self)


# --------------------------------------------------------------------------
# Search
# --------------------------------------------------------------------------

class SearchDialog(QDialog):
    def __init__(self, iface, catalog, parent=None):
        super().__init__(parent)
        self.iface, self.catalog = iface, catalog
        self.setWindowTitle(tr("se_title"))
        self.resize(620, 520)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(tr("se_placeholder"))
        self.edit.setClearButtonEnabled(True)
        self.results = QListWidget()
        self.detail = QTextBrowser()
        self.load_btn = QPushButton(tr("load"))
        self.load_btn.setEnabled(False)
        close_btn = QPushButton(tr("close"))
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self.load_btn)
        buttons.addWidget(close_btn)
        lay = QVBoxLayout(self)
        lay.addWidget(self.edit)
        lay.addWidget(self.results, 2)
        lay.addWidget(self.detail, 3)
        lay.addLayout(buttons)

        self.edit.textChanged.connect(self._search)
        self.results.currentItemChanged.connect(self._on_select)
        self.results.itemDoubleClicked.connect(lambda *_: self._load())
        self.load_btn.clicked.connect(self._load)
        close_btn.clicked.connect(self.close)
        self._search("")

    def showEvent(self, event):
        super().showEvent(event)
        self.edit.setFocus()

    def _search(self, text):
        self.results.clear()
        self.detail.clear()
        self.load_btn.setEnabled(False)
        if not text.strip():
            self.detail.setHtml("<p>%s</p>" % tr("se_hint"))
            return
        found = self.catalog.search(text)
        if not found:
            self.detail.setHtml("<p>%s</p>" % tr("se_none", query=escape(text)))
            return
        for p in found:
            suffix = "" if p.verified else "  (%s)" % tr(tag_key(p))
            item = QListWidgetItem("%s — %s%s" % (p.name, p.category.name, suffix))
            item.setData(ROLE, p.id)
            if not p.verified:
                item.setForeground(_GREY)
            self.results.addItem(item)
        self.results.setCurrentRow(0)

    def _current_product(self):
        item = self.results.currentItem()
        return self.catalog.get(item.data(ROLE)) if item else None

    def _on_select(self, *_):
        p = self._current_product()
        self.load_btn.setEnabled(bool(p and p.loadable))
        if p:
            self.detail.setHtml(describe_product(p))

    def _load(self):
        p = self._current_product()
        if p and p.loadable:
            load_and_report(self.iface, p, self)


# --------------------------------------------------------------------------
# Help
# --------------------------------------------------------------------------

class InfoDialog(QDialog):
    def __init__(self, title, html, parent=None, size=(640, 520)):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(*size)
        view = QTextBrowser()
        view.setOpenExternalLinks(True)
        view.setHtml(html)
        close_btn = QPushButton(tr("close"))
        close_btn.clicked.connect(self.close)
        lay = QVBoxLayout(self)
        lay.addWidget(view)
        row = QHBoxLayout()
        row.addStretch(1)
        self.extra_row = row
        row.addWidget(close_btn)
        lay.addLayout(row)


def help_html(catalog):
    prods = list(catalog.all_products())
    items = list(catalog.all_items())
    n_ok = sum(1 for p in items if p.loadable)
    return tr("help_html", n_total=len(prods), n_sheets=len(items) - len(prods), n_ok=n_ok, n_pend=len(items) - n_ok)


# --------------------------------------------------------------------------
# Connection diagnostics
# --------------------------------------------------------------------------

class DiagnosticsDialog(QDialog):
    def __init__(self, parent=None, url=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dg_title"))
        self.resize(760, 560)
        self.url = url or "https://ide.amb.cat/geoserveis/rest/services/topografia_1000_25831/MapServer/WMTS/1.0.0/WMTSCapabilities.xml"
        self.out = QPlainTextEdit()
        self.out.setReadOnly(True)
        self.out.setPlainText(tr("dg_press", host=services.host_of(self.url)))
        run_btn = QPushButton(tr("dg_run"))
        copy_btn = QPushButton(tr("dg_copy"))
        close_btn = QPushButton(tr("close"))
        row = QHBoxLayout()
        row.addWidget(run_btn)
        row.addWidget(copy_btn)
        row.addStretch(1)
        row.addWidget(close_btn)
        lay = QVBoxLayout(self)
        lay.addWidget(self.out)
        lay.addLayout(row)
        run_btn.clicked.connect(self.run)
        copy_btn.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.out.toPlainText()))
        close_btn.clicked.connect(self.close)

    def run(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.out.setPlainText(self.build_report())
        finally:
            QApplication.restoreOverrideCursor()

    def build_report(self):
        host = services.host_of(self.url)
        L = [tr("dg_report"), "=" * 40, "", tr("dg_env"),
             "  QGIS: %s" % Qgis.QGIS_VERSION,
             "  Python: %s (%s)" % (sys.version.split()[0], platform.platform()),
             "  %s: %s" % (tr("dg_py_ssl"), ssl.OPENSSL_VERSION),
             "  " + tr("dg_qt_ssl", ok=QSslSocket.supportsSsl(), lib=QSslSocket.sslLibraryVersionString())]
        try:
            from qgis.PyQt.QtNetwork import QSslConfiguration
            L.append("  " + tr("dg_roots", n=len(QSslConfiguration.systemCaCertificates())))
        except Exception:  # noqa: BLE001
            pass
        try:
            L.append("  " + tr("dg_added", n=len(QgsApplication.authManager().trustedCaCerts())))
        except Exception:  # noqa: BLE001
            pass
        L += ["", tr("dg_t1"), "  URL: %s" % self.url]
        res = layer_loader.fetch(self.url)
        if res.ok:
            L.append("  %s: OK (HTTP %s, %d bytes)" % (tr("dg_result"), res.http_status, len(res.content)))
            qkind = None
        else:
            L.append("  %s: ERROR [%s] %s" % (tr("dg_result"), res.kind, res.message))
            qkind = res.kind

        L += ["", tr("dg_t2")]
        py = services.python_tls_check(host)
        L.append("  %s: %s" % (tr("dg_result"), "OK (%s)" % py.get("version") if py["ok"] else "ERROR %s (code %s)" % (py["error"], py["verify_code"])))

        chain = None  # reading the presented chain needs an unverified handshake: only in tools/diagnose_tls.py
        L += ["", tr("dg_interp")]
        lines = services.interpret(qkind, py, chain) or [tr("dg_none")]
        L += ["  - " + s_ for s_ in lines]
        L += ["", tr("dg_footer")]
        return "\n".join(L)
