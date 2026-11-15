# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
"""Main plugin class: toolbar, actions and life cycle (load / unload)."""
import os

from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QComboBox, QLabel, QMenu, QPushButton, QToolButton
from qgis.core import QgsApplication

from . import catalog as catalog_mod
from . import dialogs, i18n
from .compat import msg_critical
from .i18n import tr

PLUGIN_DIR = os.path.dirname(__file__)
MENU = "&Open AMB"
TOOLBAR_NAME = "Open AMB"


SETTING_LANG = "OpenAMB/language"      # "auto" | "en" | "ca" | "es"


def qgis_locale():
    try:
        return QgsApplication.locale()
    except Exception:  # noqa: BLE001
        return str(QSettings().value("locale/userLocale", "en") or "en")


def apply_language():
    """Set the interface language from the saved choice ("auto" follows QGIS)."""
    choice = str(QSettings().value(SETTING_LANG, "auto") or "auto")
    return i18n.set_language(qgis_locale() if choice == "auto" else choice)


def icon(name):
    return QIcon(os.path.join(PLUGIN_DIR, "icons", name))


class OpenAMBPlugin(object):
    def __init__(self, iface):
        self.iface = iface
        self.toolbar = None
        self.actions = []
        self.catalog = None
        self._dialogs = {}
        self._menu_button = None
        self._menu_widget_action = None
        self._menu = None

    # -- life cycle ----------------------------------------------------------
    def initGui(self):  # noqa: N802 - name required by QGIS
        apply_language()
        try:
            self.catalog = catalog_mod.load_catalog()
        except catalog_mod.CatalogError as exc:
            self.iface.messageBar().pushMessage("Open AMB", tr("catalog_invalid", error=exc), level=msg_critical())
            return

        self.toolbar = self.iface.addToolBar(TOOLBAR_NAME)
        self.toolbar.setObjectName("OpenAMBToolbar")

        # Image 1: graphic identifier with no function (enabled so it is not greyed out).
        self._logo = QAction(icon("icon_1_logo.png"), "Open AMB", self.iface.mainWindow())
        self.toolbar.addAction(self._logo)
        self.actions.append(self._logo)
        self.toolbar.addSeparator()

        # Image 2: drop-down menu (category > product, with the sheet index under each product), like Open ICGC.
        self._menu_button = QToolButton()
        self._menu_button.setIcon(icon("icon_2_cataleg.png"))
        mode = getattr(QToolButton, "ToolButtonPopupMode", QToolButton)
        self._menu_button.setPopupMode(mode.InstantPopup)
        self._menu_widget_action = self.toolbar.addWidget(self._menu_button)

        self._buttons = []   # (action, text key), so a language change can refresh the texts
        self._add_action("icon_3_cercador.png", "tb_search", self.show_search)
        self._add_action("icon_5_ajuda.png", "tb_help", self.show_help)
        self._retranslate()

    def _add_action(self, icon_name, text_key, slot):
        action = QAction(icon(icon_name), tr(text_key), self.iface.mainWindow())
        action.triggered.connect(lambda _checked=False: slot())
        self.toolbar.addAction(action)
        self.iface.addPluginToMenu(MENU, action)
        self.actions.append(action)
        self._buttons.append((action, text_key))

    def _retranslate(self):
        self._logo.setToolTip(tr("tb_logo"))
        for action, key in self._buttons:
            action.setText(tr(key))
            action.setToolTip(tr(key))
        self._menu_button.setToolTip(tr("tb_menu"))
        self._rebuild_menu()

    def _rebuild_menu(self):
        """category > product, and under each product its sheet index as a separate entry."""
        menu = QMenu(self.iface.mainWindow())
        for category in self.catalog.categories:
            sub = menu.addMenu(category.name)
            for product in category.products:
                self._add_item(sub, product.name, product)
                if product.sheet_cut:
                    self._add_item(sub, "      ↳ " + product.sheet_cut.short_name, product.sheet_cut, product.sheet_cut.name)
        menu.addSeparator()
        window = menu.addAction(tr("menu_window"))
        window.triggered.connect(lambda _checked=False: self.show_catalog())
        old, self._menu = self._menu, menu
        self._menu_button.setMenu(menu)
        if old is not None:
            old.deleteLater()

    def _add_item(self, menu, label, item, tooltip=None):
        action = menu.addAction(label)
        action.setToolTip(tooltip or label)
        action.setEnabled(bool(item.loadable))
        action.triggered.connect(lambda _checked=False, it=item: self.load_item(it))

    def load_item(self, item):
        dialogs.load_and_report(self.iface, item, self.iface.mainWindow())

    def set_language(self, choice):
        """Save the language choice, apply it and discard the open dialogs (rebuilt on demand)."""
        QSettings().setValue(SETTING_LANG, choice)
        apply_language()
        self._retranslate()
        for dlg in list(self._dialogs.values()):
            dlg.close()
            dlg.deleteLater()
        self._dialogs.clear()

    def unload(self):
        # Undo everything initGui created, otherwise reloading duplicates toolbars and buttons.
        for dlg in list(self._dialogs.values()):
            dlg.close()
            dlg.deleteLater()
        self._dialogs.clear()
        for action in self.actions:
            self.iface.removePluginMenu(MENU, action)
            if self.toolbar is not None:
                self.toolbar.removeAction(action)
        self.actions = []
        if self.toolbar is not None and self._menu_widget_action is not None:
            self.toolbar.removeAction(self._menu_widget_action)
        self._menu_widget_action = None
        if self._menu_button is not None:
            self._menu_button.setMenu(None)
            self._menu_button.deleteLater()
            self._menu_button = None
        if self._menu is not None:
            self._menu.deleteLater()
            self._menu = None
        if self.toolbar is not None:
            self.iface.mainWindow().removeToolBar(self.toolbar)
            self.toolbar.deleteLater()
            self.toolbar = None

    # -- actions -------------------------------------------------------------
    def _show(self, key, factory):
        """Create a dialog once and reuse it afterwards."""
        dlg = self._dialogs.get(key)
        if dlg is None:
            dlg = factory()
            self._dialogs[key] = dlg
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    def show_catalog(self):
        self._show("catalog", lambda: dialogs.CatalogDialog(self.iface, self.catalog, self.iface.mainWindow()))

    def show_search(self):
        self._show("search", lambda: dialogs.SearchDialog(self.iface, self.catalog, self.iface.mainWindow()))

    def show_help(self):
        # Not reused: the text depends on the catalog state and the dialog is cheap to create.
        dlg = dialogs.InfoDialog(tr("help_title"), dialogs.help_html(self.catalog), self.iface.mainWindow())
        btn = QPushButton(tr("diag_btn"))
        btn.clicked.connect(lambda: self._open_diagnostics(dlg))
        dlg.extra_row.insertWidget(0, btn)
        # Language selector: "auto" follows the QGIS language.
        combo = QComboBox()
        combo.addItem(tr("lang_auto"), "auto")
        for code in i18n.LANGS:
            combo.addItem(i18n.LANG_NAMES[code], code)
        current = str(QSettings().value(SETTING_LANG, "auto") or "auto")
        combo.setCurrentIndex(max(0, combo.findData(current)))
        combo.activated.connect(lambda _i: self._on_language_chosen(combo.currentData()))
        dlg.extra_row.insertWidget(1, QLabel(tr("lang_label")))
        dlg.extra_row.insertWidget(2, combo)
        self._dialogs["help"] = dlg
        dlg.show()

    def _on_language_chosen(self, choice):
        self.set_language(choice)
        self.show_help()      # reopen the help dialog already in the new language

    def _open_diagnostics(self, parent):
        diag = dialogs.DiagnosticsDialog(parent)
        self._dialogs["diag"] = diag
        diag.show()
