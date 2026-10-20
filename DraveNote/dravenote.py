#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DraveNote - lokale, offline markdown-notities.
Dravenlock-huisstijl. Notities zijn gewone .md-bestanden in een map naast de app.
"""
import os
import sys
import json
import re
import shutil
import datetime

from PyQt6.QtCore import Qt, QTimer, QLocale, QUrl, pyqtSignal
from PyQt6.QtGui import (QPixmap, QIcon, QDesktopServices, QFont, QTextCursor,
                         QPainter, QColor, QBrush, QPen, QPalette)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QSplitter, QListWidget, QListWidgetItem, QLineEdit,
    QPlainTextEdit, QTextBrowser, QFileDialog, QMessageBox, QDialog,
    QToolButton, QFrame, QStatusBar, QComboBox, QInputDialog, QSpinBox,
    QStackedWidget)

APP_NAME = "DraveNote"
APP_VERSION = "0.7"
DONATE_URL = "https://paypal.me/roger076"
SUPPORT_MAIL = "service@dravenlock.nl"

# ---- Dravenlock-huisstijl ----
BG = "#0e0e11"
PANEL = "#16161b"
PANEL2 = "#1c1c22"
SILVER = "#d4d4d4"
MUTE = "#8a8a94"
ACCENT = "#6fa3d6"
LINE = "#23232b"


# ---------------------------------------------------------------------------
# Pad-helpers (frozen-bewust)
# ---------------------------------------------------------------------------
def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _config_path():
    return os.path.join(_app_dir(), "dravenote_config.json")


def _default_notes_dir():
    return os.path.join(_app_dir(), "notities")


DEFAULT_CONFIG = {"lang": "", "notes_dir": "", "font_size": 15, "view": "split"}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(_config_path(), "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    if not cfg.get("notes_dir"):
        cfg["notes_dir"] = _default_notes_dir()
    return cfg


def save_config(cfg):
    try:
        with open(_config_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Taal (NL basis + OS-detectie + handmatige keuze)
# ---------------------------------------------------------------------------
_LANG = "nl"

TRANSLATIONS = {
    "en": {
        "Nieuw": "New", "Hernoemen": "Rename", "Verwijderen": "Delete",
        "Map openen": "Open folder", "Zoeken\u2026": "Search\u2026",
        "Instellingen\u2026": "Settings\u2026", "Snelgids": "Quick guide",
        "Over": "About", "Sluiten": "Close", "Taal:": "Language:",
        "Automatisch (OS)": "Automatic (OS)", "Nederlands": "Dutch",
        "Engels": "English", "Notitiemap:": "Notes folder:",
        "Wijzigen\u2026": "Change\u2026", "Lettergrootte:": "Font size:",
        "Bewerken": "Edit", "Gesplitst": "Split", "Voorbeeld": "Preview",
        "Ongedaan": "Undo", "Opnieuw": "Redo",
        "Vet": "Bold", "Cursief": "Italic", "Kop": "Heading", "Lijst": "List",
        "Taak": "Task", "Citaat": "Quote", "Code": "Code", "Link": "Link",
        "Lijn": "Line", "Tabel": "Table",
        "Naamloos": "Untitled", "woorden": "words", "tekens": "characters",
        "Donatie": "Donate",
        "Nieuwe notitie": "New note", "Titel:": "Title:", "Naam:": "Name:",
        "Prullenbak": "Trash", "Openen": "Open", "Legen\u2026": "Empty\u2026",
        "Prullenbak legen": "Empty trash",
        "Alles in de prullenbak permanent verwijderen?":
            "Permanently delete everything in the trash?",
        "Prullenbak is al leeg.": "Trash is already empty.",
        "Prullenbak geleegd.": "Trash emptied.",
        "%d in prullenbak": "%d in trash",
        "Notitie hernoemen": "Rename note", "Nieuwe titel:": "New title:",
        "Notitie verwijderen": "Delete note",
        "Naar de prullenbak verplaatsen?": "Move to the trash folder?",
        "Geen notitie geselecteerd": "No note selected",
        "Kies een notitiemap": "Choose a notes folder",
        "Opgeslagen": "Saved",
        "snelgids_titel": "DraveNote - quick guide",
        "URL:": "URL:", "Tekst:": "Text:",
        "Nog geen notities. Maak er een met 'Nieuw'.":
            "No notes yet. Create one with 'New'.",
    }
}


def detect_lang(cfg):
    forced = (cfg.get("lang") or "").strip().lower()
    if forced in ("nl", "en"):
        return forced
    try:
        if QLocale.system().name().lower().startswith("nl"):
            return "nl"
        return "en"
    except Exception:
        return "nl"


def t(s, lang=None):
    lg = lang or _LANG
    if lg == "nl":
        return s
    return TRANSLATIONS.get(lg, {}).get(s, s)


# ---------------------------------------------------------------------------
# Logo / icoon
# ---------------------------------------------------------------------------
def _logo_path():
    return os.path.join(_app_dir(), "logo.png")


def make_logo(size=32):
    """Geladen drakenlogo, anders een eenvoudig getekend notitie-icoon."""
    p = _logo_path()
    if os.path.exists(p):
        pm = QPixmap(p)
        if not pm.isNull():
            return pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    pt = QPainter(pm)
    pt.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    pt.setBrush(QBrush(QColor(ACCENT)))
    pt.setPen(Qt.PenStyle.NoPen)
    m = s * 0.16
    pt.drawRoundedRect(int(m), int(m * 0.7), int(s - 2 * m), int(s - 1.4 * m),
                       int(s * 0.1), int(s * 0.1))
    pt.setPen(QPen(QColor(BG), max(1, int(s * 0.05))))
    for i in range(3):
        yy = int(s * 0.36 + i * s * 0.16)
        pt.drawLine(int(s * 0.30), yy, int(s * 0.70), yy)
    pt.end()
    return pm


def app_icon():
    p = os.path.join(_app_dir(), "logo.ico")
    if os.path.exists(p):
        return QIcon(p)
    return QIcon(make_logo(64))


# ---------------------------------------------------------------------------
# Bestandshelpers
# ---------------------------------------------------------------------------
def sanitize_filename(name, fallback="notitie"):
    name = (name or "").strip()
    for ch in '<>:"/\\|?*\n\r\t':
        name = name.replace(ch, " ")
    name = " ".join(name.split())
    name = name.strip(" .")
    if not name:
        name = fallback
    return name[:80]


def note_title(text, fallback):
    for line in (text or "").splitlines():
        s = line.strip()
        if s:
            return s.lstrip("#").strip() or fallback
    return fallback


def unique_path(folder, base, ext=".md"):
    cand = os.path.join(folder, base + ext)
    i = 2
    while os.path.exists(cand):
        cand = os.path.join(folder, "%s %d%s" % (base, i, ext))
        i += 1
    return cand


# ---------------------------------------------------------------------------
# Markdown-editor (met Tab-invoeging en handige sneltoetsen)
# ---------------------------------------------------------------------------
class MarkdownEditor(QPlainTextEdit):
    # markering aan het begin van een regel: opsomming, taak, genummerd of citaat
    _LIST_RE = re.compile(
        r"^(?P<indent>\s*)(?:"
        r"(?P<bullet>[-*+])[ \t]+(?P<task>\[[ xX]\][ \t]+)?"
        r"|(?P<num>\d+)\.[ \t]+"
        r"|(?P<quote>>+)[ \t]+"
        r")")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("editor")
        self.setTabChangesFocus(False)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)

    def keyPressEvent(self, e):
        # Tab voegt twee spaties in (geen tab-teken)
        if e.key() == Qt.Key.Key_Tab and not (e.modifiers()
                                               & Qt.KeyboardModifier.ControlModifier):
            self.insertPlainText("  ")
            return
        # Enter: lijst/taak/citaat automatisch doorzetten (Shift+Enter = gewone regel)
        if (e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
                and not (e.modifiers() & Qt.KeyboardModifier.ShiftModifier)):
            cur = self.textCursor()
            line = cur.block().text()
            m = self._LIST_RE.match(line)
            if m:
                rest = line[m.end():]
                if rest.strip() == "":
                    # lege lijstregel -> stop de lijst: markering weg, geen nieuwe regel
                    c = self.textCursor()
                    c.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                    c.movePosition(QTextCursor.MoveOperation.EndOfBlock,
                                   QTextCursor.MoveMode.KeepAnchor)
                    c.removeSelectedText()
                    return
                marker = self._next_marker(m)
                super().keyPressEvent(e)
                self.insertPlainText(m.group("indent") + marker)
                return
        super().keyPressEvent(e)

    @staticmethod
    def _next_marker(m):
        if m.group("bullet"):
            mk = m.group("bullet") + " "
            if m.group("task"):
                mk += "[ ] "   # nieuwe taak begint onafgevinkt
            return mk
        if m.group("num"):
            try:
                return "%d. " % (int(m.group("num")) + 1)
            except Exception:
                return "1. "
        if m.group("quote"):
            return m.group("quote") + " "
        return ""


# ---------------------------------------------------------------------------
# Snelgids
# ---------------------------------------------------------------------------
GUIDE_NL = """DraveNote - Snelgids

DraveNote bewaart je notities als gewone Markdown-bestanden (.md) in een map
naast de app (standaard 'notities'). Je kunt die bestanden dus altijd ook
buiten DraveNote openen of meenemen.

Aan de slag
- Klik op 'Nieuw' en geef je notitie meteen een naam.
- Typ links in de editor. Rechts zie je meteen het opgemaakte voorbeeld.
- Kies bovenaan 'Bewerken', 'Gesplitst' of 'Voorbeeld'.
- De naam in de lijst is de bestandsnaam. Met 'Hernoemen' geef je een
  notitie een andere naam.

Opmaak (Markdown) - of gebruik de knoppen
- # Kop 1, ## Kop 2, ### Kop 3
- **vet**, *cursief*, `code`
- - lijst   of   1. genummerd
- - [ ] taak (afvinken met - [x])
- > citaat
- [tekst](https://adres) voor een link, of plak gewoon een kale URL
  (https://...) - die wordt in het voorbeeld vanzelf klikbaar
- --- voor een scheidingslijn

Lijsten doorzetten
- Begin een lijst, taak of citaat (knop of typen) en druk Enter: de volgende
  regel krijgt automatisch dezelfde markering. Bij een genummerde lijst telt
  hij door (1. 2. 3.).
- Stoppen? Druk op een LEGE lijstregel nog eens Enter; de markering verdwijnt.

Ongedaan / Opnieuw
- Gebruik de knoppen linksboven, of Ctrl+Z (ongedaan) en Ctrl+Y (opnieuw).

Opslaan
- DraveNote slaat automatisch op terwijl je typt.
- 'Map openen' opent de notitiemap in de verkenner.

Toegankelijkheid
- Stel de lettergrootte in via Instellingen (geldt voor editor en voorbeeld).

Vragen of een tip? service@dravenlock.nl
"""

GUIDE_EN = """DraveNote - Quick guide

DraveNote stores your notes as plain Markdown files (.md) in a folder next to
the app ('notities' by default). You can always open or move those files
outside DraveNote too.

Getting started
- Click 'New' and give your note a name right away.
- Type in the editor on the left. The formatted preview appears on the right.
- Choose 'Edit', 'Split' or 'Preview' at the top.
- The name in the list is the file name. Use 'Rename' to give a note a
  different name.

Formatting (Markdown) - or use the buttons
- # Heading 1, ## Heading 2, ### Heading 3
- **bold**, *italic*, `code`
- - list   or   1. numbered
- - [ ] task (check with - [x])
- > quote
- [text](https://address) for a link, or just paste a bare URL (https://...)
  which becomes clickable in the preview
- --- for a separator line

Continuing lists
- Start a list, task or quote and press Enter: the next line automatically gets
  the same marker. Numbered lists keep counting (1. 2. 3.).
- To stop, press Enter again on an EMPTY list line; the marker disappears.

Undo / Redo
- Use the buttons at the top left, or Ctrl+Z (undo) and Ctrl+Y (redo).

Saving
- DraveNote saves automatically while you type.
- 'Open folder' opens the notes folder in your file manager.

Accessibility
- Set the font size in Settings (applies to editor and preview).

Questions or feedback? service@dravenlock.nl
"""


class GuideDialog(QDialog):
    def __init__(self, parent, lang):
        super().__init__(parent)
        self.setWindowTitle(t("snelgids_titel", lang))
        self.resize(580, 560)
        lay = QVBoxLayout(self)
        box = QTextBrowser()
        box.setObjectName("guide")
        box.setOpenExternalLinks(True)
        box.setPlainText(GUIDE_NL if lang == "nl" else GUIDE_EN)
        lay.addWidget(box)
        row = QHBoxLayout()
        donate = QPushButton("\u2665 " + t("Donatie", lang))
        donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DONATE_URL)))
        row.addWidget(donate)
        row.addStretch(1)
        close = QPushButton(t("Sluiten", lang))
        close.clicked.connect(self.accept)
        row.addWidget(close)
        lay.addLayout(row)


# ---------------------------------------------------------------------------
# Instellingen
# ---------------------------------------------------------------------------
class SettingsDialog(QDialog):
    def __init__(self, parent, cfg, lang):
        super().__init__(parent)
        self.cfg = dict(cfg)
        self.lang = lang
        self.setWindowTitle(t("Instellingen\u2026", lang))
        self.resize(480, 300)
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel(t("Taal:", lang)))
        self.langbox = QComboBox()
        self.langbox.addItem(t("Automatisch (OS)", lang), "")
        self.langbox.addItem(t("Nederlands", lang), "nl")
        self.langbox.addItem(t("Engels", lang), "en")
        self.langbox.setCurrentIndex({"": 0, "nl": 1, "en": 2}
                                     .get(cfg.get("lang", ""), 0))
        lay.addWidget(self.langbox)

        lay.addWidget(QLabel(t("Notitiemap:", lang)))
        row = QHBoxLayout()
        self.dirlbl = QLineEdit(cfg.get("notes_dir", ""))
        self.dirlbl.setReadOnly(True)
        row.addWidget(self.dirlbl, 1)
        b = QPushButton(t("Wijzigen\u2026", lang))
        b.clicked.connect(self._pick_dir)
        row.addWidget(b)
        lay.addLayout(row)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel(t("Lettergrootte:", lang)))
        self.fs = QSpinBox()
        self.fs.setRange(10, 30)
        self.fs.setValue(int(cfg.get("font_size", 15)))
        row2.addWidget(self.fs)
        row2.addStretch(1)
        lay.addLayout(row2)

        # prullenbak
        row3 = QHBoxLayout()
        self.trash_lbl = QLabel("")
        row3.addWidget(self.trash_lbl, 1)
        b_open = QPushButton(t("Openen", lang))
        b_open.clicked.connect(self._open_trash)
        row3.addWidget(b_open)
        self.b_empty = QPushButton(t("Legen\u2026", lang))
        self.b_empty.clicked.connect(self._empty_trash)
        row3.addWidget(self.b_empty)
        lay.addLayout(row3)
        self._update_trash_lbl()

        hint = QLabel(t("Sommige instellingen gaan pas in na herstarten.", lang)
                      if lang == "nl" else "Some settings apply after a restart.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addStretch(1)

        rr = QHBoxLayout()
        rr.addStretch(1)
        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        rr.addWidget(ok)
        lay.addLayout(rr)

    def _pick_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, t("Kies een notitiemap", self.lang), self.dirlbl.text())
        if d:
            self.dirlbl.setText(d)
            self._update_trash_lbl()

    def _trash_dir(self):
        base = self.dirlbl.text() or _default_notes_dir()
        return os.path.join(base, "prullenbak")

    def _trash_files(self):
        try:
            return [os.path.join(self._trash_dir(), f)
                    for f in os.listdir(self._trash_dir())
                    if not f.startswith(".")]
        except Exception:
            return []

    def _update_trash_lbl(self):
        n = len(self._trash_files())
        self.trash_lbl.setText("%s: %d" % (t("Prullenbak", self.lang), n))
        self.b_empty.setEnabled(n > 0)

    def _open_trash(self):
        d = self._trash_dir()
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass
        QDesktopServices.openUrl(QUrl.fromLocalFile(d))

    def _empty_trash(self):
        files = self._trash_files()
        if not files:
            QMessageBox.information(self, t("Prullenbak legen", self.lang),
                                    t("Prullenbak is al leeg.", self.lang))
            return
        r = QMessageBox.question(
            self, t("Prullenbak legen", self.lang),
            t("Alles in de prullenbak permanent verwijderen?", self.lang))
        if r != QMessageBox.StandardButton.Yes:
            return
        for p in files:
            try:
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    os.remove(p)
            except Exception:
                pass
        self._update_trash_lbl()
        QMessageBox.information(self, t("Prullenbak legen", self.lang),
                                t("Prullenbak geleegd.", self.lang))

    def result_cfg(self):
        self.cfg["lang"] = self.langbox.currentData()
        self.cfg["notes_dir"] = self.dirlbl.text()
        self.cfg["font_size"] = self.fs.value()
        return self.cfg


# ---------------------------------------------------------------------------
# Hoofdvenster
# ---------------------------------------------------------------------------
class DraveNote(QMainWindow):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.lang = _LANG
        self.notes_dir = cfg.get("notes_dir") or _default_notes_dir()
        self.font_size = int(cfg.get("font_size", 15))
        self.current_path = None
        self._dirty = False
        self._loading = False

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(app_icon())
        self.resize(1100, 760)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._header())

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(self._sidebar())
        split.addWidget(self._editor_area())
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([300, 800])
        outer.addWidget(split, 1)

        sb = QStatusBar()
        self.setStatusBar(sb)
        self.count_lbl = QLabel("")
        self.count_lbl.setObjectName("muted")
        sb.addWidget(self.count_lbl)
        sb.addPermanentWidget(QLabel("v" + APP_VERSION))
        donate = QToolButton()
        donate.setText("\u2665 " + t("Donatie", self.lang))
        donate.setObjectName("donate")
        donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DONATE_URL)))
        sb.addPermanentWidget(donate)

        # auto-opslaan met kleine vertraging
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(600)
        self._save_timer.timeout.connect(self._save_current)
        # voorbeeld bijwerken met kleine vertraging
        self._prev_timer = QTimer(self)
        self._prev_timer.setSingleShot(True)
        self._prev_timer.setInterval(250)
        self._prev_timer.timeout.connect(self._update_preview)

        self._apply_fonts()
        self._set_view(cfg.get("view", "split"))
        self._ensure_dir()
        self.reload_list()

    # ---- UI-opbouw ----
    def _header(self):
        w = QWidget()
        w.setObjectName("header")
        w.setFixedHeight(56)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(14, 8, 14, 8)
        logo = QLabel()
        logo.setPixmap(make_logo(32))
        lay.addWidget(logo)
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        lay.addWidget(title)
        ver = QLabel("v" + APP_VERSION)
        ver.setObjectName("ver")
        lay.addWidget(ver)
        lay.addStretch(1)
        for label, slot in [(t("Instellingen\u2026", self.lang), self._settings),
                            (t("Snelgids", self.lang), self._guide),
                            (t("Over", self.lang), self._about)]:
            b = QPushButton(label)
            b.clicked.connect(lambda _=False, s=slot: s())
            lay.addWidget(b)
        return w

    def _sidebar(self):
        w = QWidget()
        w.setObjectName("sidebar")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 10, 8, 10)
        lay.setSpacing(8)

        self.search = QLineEdit()
        self.search.setPlaceholderText(t("Zoeken\u2026", self.lang))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._apply_filter)
        lay.addWidget(self.search)

        self.list = QListWidget()
        self.list.setObjectName("notelist")
        # selectiekleur ook leesbaar als de lijst geen focus heeft
        lp = self.list.palette()
        for grp in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
            lp.setColor(grp, QPalette.ColorRole.Highlight, QColor(ACCENT))
            lp.setColor(grp, QPalette.ColorRole.HighlightedText, QColor("#08131f"))
        self.list.setPalette(lp)
        self.list.currentItemChanged.connect(self._on_select)
        lay.addWidget(self.list, 1)

        row = QHBoxLayout()
        row.setSpacing(6)
        b_new = QPushButton(t("Nieuw", self.lang))
        b_new.setObjectName("primary")
        b_new.clicked.connect(self.new_note)
        row.addWidget(b_new)
        b_ren = QPushButton(t("Hernoemen", self.lang))
        b_ren.clicked.connect(self.rename_note)
        row.addWidget(b_ren)
        b_del = QPushButton(t("Verwijderen", self.lang))
        b_del.clicked.connect(self.delete_note)
        row.addWidget(b_del)
        lay.addLayout(row)

        b_open = QPushButton(t("Map openen", self.lang))
        b_open.clicked.connect(self._open_folder)
        lay.addWidget(b_open)
        return w

    def _editor_area(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._toolbar())

        self.editor = MarkdownEditor()
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.undoAvailable.connect(self.b_undo.setEnabled)
        self.editor.redoAvailable.connect(self.b_redo.setEnabled)
        self.preview = QTextBrowser()
        self.preview.setObjectName("preview")
        self.preview.setOpenExternalLinks(True)
        # links (ook 'bezocht') leesbaar houden op de donkere achtergrond
        pal = self.preview.palette()
        pal.setColor(QPalette.ColorRole.Link, QColor(ACCENT))
        pal.setColor(QPalette.ColorRole.LinkVisited, QColor(ACCENT))
        self.preview.setPalette(pal)

        self.panes = QSplitter(Qt.Orientation.Horizontal)
        self.panes.addWidget(self.editor)
        self.panes.addWidget(self.preview)
        self.panes.setSizes([500, 500])
        lay.addWidget(self.panes, 1)
        return w

    def _toolbar(self):
        w = QWidget()
        w.setObjectName("toolbar")
        w.setFixedHeight(92)
        outer = QVBoxLayout(w)
        outer.setContentsMargins(10, 6, 10, 6)
        outer.setSpacing(6)

        # --- rij 1: ongedaan/opnieuw links, weergavekiezer rechts ---
        row1 = QHBoxLayout()
        row1.setSpacing(6)
        self.b_undo = QToolButton()
        self.b_undo.setText("\u21b6 " + t("Ongedaan", self.lang))
        self.b_undo.setObjectName("md")
        self.b_undo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.b_undo.setEnabled(False)
        self.b_undo.clicked.connect(lambda: self.editor.undo())
        row1.addWidget(self.b_undo)
        self.b_redo = QToolButton()
        self.b_redo.setText("\u21b7 " + t("Opnieuw", self.lang))
        self.b_redo.setObjectName("md")
        self.b_redo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.b_redo.setEnabled(False)
        self.b_redo.clicked.connect(lambda: self.editor.redo())
        row1.addWidget(self.b_redo)
        row1.addStretch(1)
        self.v_edit = QToolButton()
        self.v_edit.setText(t("Bewerken", self.lang))
        self.v_edit.setCheckable(True)
        self.v_edit.setObjectName("viewbtn")
        self.v_edit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.v_edit.clicked.connect(lambda: self._set_view("edit"))
        row1.addWidget(self.v_edit)
        self.v_split = QToolButton()
        self.v_split.setText(t("Gesplitst", self.lang))
        self.v_split.setCheckable(True)
        self.v_split.setObjectName("viewbtn")
        self.v_split.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.v_split.clicked.connect(lambda: self._set_view("split"))
        row1.addWidget(self.v_split)
        self.v_prev = QToolButton()
        self.v_prev.setText(t("Voorbeeld", self.lang))
        self.v_prev.setCheckable(True)
        self.v_prev.setObjectName("viewbtn")
        self.v_prev.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.v_prev.clicked.connect(lambda: self._set_view("preview"))
        row1.addWidget(self.v_prev)
        outer.addLayout(row1)

        # --- rij 2: markdown-knoppen ---
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        def tool(label, slot, name=None):
            b = QToolButton()
            b.setText(label)
            if name:
                b.setObjectName(name)
            # opmaakknoppen pakken de focus NIET van de editor af
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.clicked.connect(slot)
            row2.addWidget(b)
            return b

        tool(t("Kop", self.lang), self._md_heading, "md")
        tool(t("Vet", self.lang), lambda: self._wrap("**", "**"), "md")
        tool(t("Cursief", self.lang), lambda: self._wrap("*", "*"), "md")
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setObjectName("sep")
        row2.addWidget(sep)
        tool(t("Lijst", self.lang), lambda: self._md_prefix("- "), "md")
        tool(t("Taak", self.lang), lambda: self._md_prefix("- [ ] "), "md")
        tool(t("Citaat", self.lang), lambda: self._md_prefix("> "), "md")
        tool(t("Link", self.lang), self._insert_link, "md")
        tool(t("Code", self.lang), lambda: self._wrap("`", "`"), "md")
        tool(t("Lijn", self.lang), self._insert_hr, "md")
        row2.addStretch(1)
        outer.addLayout(row2)
        return w

    # ---- weergave ----
    def _set_view(self, mode):
        self.view_mode = mode
        self.editor.setVisible(mode in ("edit", "split"))
        self.preview.setVisible(mode in ("preview", "split"))
        if mode == "split":
            self.panes.setSizes([500, 500])
        for b, m in ((self.v_edit, "edit"), (self.v_split, "split"),
                     (self.v_prev, "preview")):
            b.setChecked(m == mode)
        self.cfg["view"] = mode
        if mode in ("preview", "split"):
            self._update_preview()

    def _apply_fonts(self):
        ef = QFont("Cascadia Code, Consolas, monospace")
        ef.setStyleHint(QFont.StyleHint.Monospace)
        ef.setPointSize(self.font_size)
        self.editor.setFont(ef)
        self._update_preview_style()

    def _update_preview_style(self):
        self.preview.document().setDefaultStyleSheet(
            "body { color: %s; font-size: %dpt; } "
            "h1,h2,h3,h4 { color: %s; } "
            "a { color: %s; } "
            "a:visited { color: %s; } "
            "code, pre { background: %s; color: #e6e6ea; }"
            "blockquote { color: %s; border-left: 3px solid %s; }"
            % (SILVER, self.font_size, SILVER, ACCENT, ACCENT, PANEL2, MUTE, ACCENT))

    # ---- notitielijst ----
    def _ensure_dir(self):
        try:
            os.makedirs(self.notes_dir, exist_ok=True)
        except Exception:
            pass
        # welkomstnotitie bij een lege map
        try:
            mds = [f for f in os.listdir(self.notes_dir) if f.lower().endswith(".md")]
        except Exception:
            mds = []
        if not mds:
            self._write_welcome()

    def _write_welcome(self):
        body = (GUIDE_NL if self.lang == "nl" else GUIDE_EN)
        intro = ("# Welkom bij DraveNote\n\n"
                 "Dit is je eerste notitie. Je notities staan als **.md**-bestanden "
                 "in de map naast de app.\n\n"
                 if self.lang == "nl" else
                 "# Welcome to DraveNote\n\n"
                 "This is your first note. Your notes live as **.md** files in the "
                 "folder next to the app.\n\n")
        try:
            p = os.path.join(self.notes_dir,
                             ("Welkom bij DraveNote.md" if self.lang == "nl"
                              else "Welcome to DraveNote.md"))
            with open(p, "w", encoding="utf-8") as f:
                f.write(intro + "> " + t("Snelgids", self.lang)
                        + "\n\n" + "\n".join("    " + ln for ln in body.splitlines()))
        except Exception:
            pass

    def reload_list(self, select_path=None):
        self.list.blockSignals(True)
        self.list.clear()
        items = []
        try:
            for f in os.listdir(self.notes_dir):
                if f.lower().endswith(".md"):
                    full = os.path.join(self.notes_dir, f)
                    # naam in de lijst = bestandsnaam (zo klopt 'Hernoemen' meteen)
                    title = os.path.splitext(f)[0]
                    mtime = os.path.getmtime(full)
                    items.append((mtime, title, full))
        except Exception:
            pass
        items.sort(key=lambda x: x[0], reverse=True)
        for _m, title, full in items:
            it = QListWidgetItem(title)
            it.setData(Qt.ItemDataRole.UserRole, full)
            self.list.addItem(it)
        self.list.blockSignals(False)
        if not items:
            self.editor.setPlainText("")
            self.current_path = None
            self.count_lbl.setText(t("Nog geen notities. Maak er een met 'Nieuw'.",
                                     self.lang))
            self._update_preview()
            return
        target = select_path or (self.current_path if any(
            i[2] == self.current_path for i in items) else items[0][2])
        self._select_path(target)
        self._apply_filter(self.search.text())

    def _select_path(self, path):
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.ItemDataRole.UserRole) == path:
                self.list.setCurrentRow(i)
                return

    def _on_select(self, cur, _prev):
        if not cur:
            return
        self._save_current()  # bewaar de vorige
        path = cur.data(Qt.ItemDataRole.UserRole)
        self._load_path(path)

    def _load_path(self, path):
        self.current_path = path
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception:
            text = ""
        self._loading = True
        self.editor.setPlainText(text)
        self._loading = False
        self._dirty = False
        self.setWindowTitle("%s \u2014 %s" % (APP_NAME, os.path.basename(path)))
        self._update_counts()
        self._update_preview()

    # ---- bewerken / opslaan ----
    def _on_text_changed(self):
        if self._loading:
            return
        self._dirty = True
        self._save_timer.start()
        self._prev_timer.start()
        self._update_counts()

    def _save_current(self):
        if not self.current_path or not self._dirty:
            return
        try:
            with open(self.current_path, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
            self._dirty = False
            self.statusBar().showMessage(t("Opgeslagen", self.lang), 1500)
        except Exception as e:
            self.statusBar().showMessage(str(e), 4000)

    def _update_preview(self):
        if not self.preview.isVisible():
            return
        self._update_preview_style()
        self.preview.setMarkdown(self.editor.toPlainText())

    def _update_counts(self):
        text = self.editor.toPlainText()
        words = len(text.split())
        chars = len(text)
        self.count_lbl.setText("%d %s \u00b7 %d %s"
                               % (words, t("woorden", self.lang),
                                  chars, t("tekens", self.lang)))

    # ---- markdown-knoppen ----
    def _wrap(self, pre, post):
        cur = self.editor.textCursor()
        sel = cur.selectedText()
        if sel:
            cur.insertText(pre + sel + post)
        else:
            cur.insertText(pre + post)
            cur.movePosition(QTextCursor.MoveOperation.Left,
                             QTextCursor.MoveMode.MoveAnchor, len(post))
            self.editor.setTextCursor(cur)
        self.editor.setFocus()

    def _md_prefix(self, prefix):
        doc = self.editor.document()
        cur = self.editor.textCursor()
        b1 = doc.findBlock(cur.selectionStart()).blockNumber()
        b2 = doc.findBlock(cur.selectionEnd()).blockNumber()
        edit = self.editor.textCursor()
        edit.beginEditBlock()
        for bn in range(b1, b2 + 1):
            blk = doc.findBlockByNumber(bn)
            edit.setPosition(blk.position())
            edit.insertText(prefix)
        edit.endEditBlock()
        self.editor.setFocus()

    def _md_heading(self):
        cur = self.editor.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cur.insertText("# ")
        self.editor.setFocus()

    def _insert_hr(self):
        cur = self.editor.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        cur.insertText("\n\n---\n")
        self.editor.setFocus()

    def _insert_link(self):
        cur = self.editor.textCursor()
        sel = cur.selectedText()
        url, ok = QInputDialog.getText(self, t("Link", self.lang),
                                       t("URL:", self.lang), text="https://")
        if not ok or not url.strip() or url.strip() == "https://":
            return
        url = url.strip()
        if sel and sel != url:
            # eigen tekst voor de link: [tekst](url)
            cur.insertText("[%s](%s)" % (sel, url))
        else:
            # geen aparte tekst: gewoon de URL (wordt in het voorbeeld klikbaar)
            cur.insertText(url)
        self.editor.setFocus()

    # ---- notitie-acties ----
    def new_note(self):
        self._save_current()
        self._ensure_dir()
        name, ok = QInputDialog.getText(
            self, t("Nieuwe notitie", self.lang), t("Naam:", self.lang),
            text=t("Naamloos", self.lang))
        if not ok:
            return
        base = sanitize_filename(name, t("Naamloos", self.lang))
        path = unique_path(self.notes_dir, base)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("")
        except Exception as e:
            QMessageBox.warning(self, APP_NAME, str(e))
            return
        self.current_path = path
        self.reload_list(select_path=path)
        self.editor.setFocus()
        cur = self.editor.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        self.editor.setTextCursor(cur)

    def rename_note(self):
        if not self.current_path:
            QMessageBox.information(self, APP_NAME,
                                    t("Geen notitie geselecteerd", self.lang))
            return
        old = os.path.splitext(os.path.basename(self.current_path))[0]
        name, ok = QInputDialog.getText(self, t("Notitie hernoemen", self.lang),
                                        t("Nieuwe titel:", self.lang), text=old)
        if not ok or not name.strip():
            return
        self._save_current()
        new_path = unique_path(self.notes_dir, sanitize_filename(name))
        try:
            os.replace(self.current_path, new_path)
        except Exception as e:
            QMessageBox.warning(self, APP_NAME, str(e))
            return
        self.current_path = new_path
        self.reload_list(select_path=new_path)

    def delete_note(self):
        if not self.current_path:
            QMessageBox.information(self, APP_NAME,
                                    t("Geen notitie geselecteerd", self.lang))
            return
        r = QMessageBox.question(
            self, t("Notitie verwijderen", self.lang),
            t("Naar de prullenbak verplaatsen?", self.lang))
        if r != QMessageBox.StandardButton.Yes:
            return
        try:
            trash = os.path.join(self.notes_dir, "prullenbak")
            os.makedirs(trash, exist_ok=True)
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            base = os.path.basename(self.current_path)
            os.replace(self.current_path,
                       os.path.join(trash, stamp + "_" + base))
        except Exception as e:
            QMessageBox.warning(self, APP_NAME, str(e))
            return
        self.current_path = None
        self.reload_list()

    def _open_folder(self):
        self._ensure_dir()
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.notes_dir))

    def _apply_filter(self, text=None):
        q = (text if text is not None else self.search.text()).strip().lower()
        for i in range(self.list.count()):
            it = self.list.item(i)
            show = True
            if q:
                title = it.text().lower()
                path = it.data(Qt.ItemDataRole.UserRole) or ""
                body = ""
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        body = f.read().lower()
                except Exception:
                    pass
                show = (q in title) or (q in body)
            it.setHidden(not show)

    # ---- dialogen ----
    def _settings(self):
        dlg = SettingsDialog(self, self.cfg, self.lang)
        if dlg.exec():
            new = dlg.result_cfg()
            self.cfg = new
            save_config(self.cfg)
            self.font_size = int(new.get("font_size", 15))
            self._apply_fonts()
            self._update_preview()
            if new.get("notes_dir") and new["notes_dir"] != self.notes_dir:
                self._save_current()
                self.notes_dir = new["notes_dir"]
                self.current_path = None
                self._ensure_dir()
                self.reload_list()

    def _guide(self):
        GuideDialog(self, self.lang).exec()

    def _about(self):
        QMessageBox.information(
            self, t("Over", self.lang),
            "%s v%s\n\nLokale markdown-notities.\nDravenlock\n%s\n%s"
            % (APP_NAME, APP_VERSION, SUPPORT_MAIL, DONATE_URL))

    def closeEvent(self, ev):
        self._save_current()
        self.cfg["font_size"] = self.font_size
        save_config(self.cfg)
        ev.accept()


QSS = """
* { font-family: 'Segoe UI', sans-serif; font-size: 14px; color: %(silver)s; }
QMainWindow, QWidget { background: %(bg)s; }
#header { background: %(panel)s; border-bottom: 1px solid %(line)s; }
#title { font-size: 19px; font-weight: 700; color: %(silver)s; }
#ver { color: %(mute)s; font-size: 12px; }
#sidebar { background: %(panel)s; border-right: 1px solid %(line)s; }
#toolbar { background: %(bg)s; border-bottom: 1px solid %(line)s; }
QPushButton { background: %(panel2)s; border: 1px solid #2c2c36; border-radius: 8px;
              padding: 7px 12px; color: %(silver)s; }
QPushButton:hover { border-color: %(accent)s; }
QPushButton:pressed { background: #2a2a33; color: %(silver)s; }
QPushButton:disabled { color: #595962; background: #131318; border-color: #202028; }
QPushButton#primary { background: %(accent)s; color: #08131f; font-weight: 700;
                      border: none; }
QPushButton#primary:hover { background: #87b6e3; }
QPushButton#primary:pressed { background: #5e93c6; color: #08131f; }
QToolButton { background: %(panel2)s; border: 1px solid #2c2c36; border-radius: 7px;
              padding: 5px 9px; color: %(silver)s; }
QToolButton:hover { border-color: %(accent)s; }
QToolButton:pressed { background: #2a2a33; color: %(silver)s; }
QToolButton:disabled { color: #595962; background: #131318; border-color: #202028; }
QToolButton#md { font-weight: 600; min-width: 18px; }
QToolButton#viewbtn:checked { background: %(accent)s; color: #08131f; border: none;
                              font-weight: 700; }
QToolButton#donate { border: none; background: transparent; color: %(accent)s; }
QFrame#sep { color: #2c2c36; }
QLineEdit { background: %(panel2)s; border: 1px solid #2c2c36; border-radius: 8px;
            padding: 7px 9px; color: %(silver)s; }
QLineEdit:focus { border-color: %(accent)s; }
QSpinBox { background: %(panel2)s; border: 1px solid #2c2c36; border-radius: 6px;
           padding: 3px 6px; min-width: 54px; color: %(silver)s; }
QListWidget#notelist { background: %(panel)s; border: 1px solid %(line)s;
                       border-radius: 8px; padding: 4px; outline: none;
                       selection-background-color: %(accent)s; selection-color: #08131f; }
QListWidget#notelist::item { padding: 9px 8px; border-radius: 6px; color: %(silver)s; }
QListWidget#notelist::item:selected { background: %(accent)s; color: #08131f; }
QListWidget#notelist::item:hover:!selected { background: %(panel2)s; }
QPlainTextEdit#editor { background: #101015; color: #e8e8ee; border: none;
                        padding: 12px; selection-background-color: %(accent)s; }
QTextBrowser#preview { background: %(bg)s; border: none; border-left: 1px solid %(line)s;
                       padding: 8px 14px; }
QTextBrowser#guide { background: %(panel)s; border: 1px solid #2c2c36;
                     border-radius: 8px; padding: 10px; }
#muted, #hint { color: %(mute)s; font-size: 12px; }
QDialog { background: %(bg)s; }
QStatusBar { background: %(panel)s; border-top: 1px solid %(line)s; }
QSplitter::handle { background: %(line)s; }
QScrollBar:vertical { background: %(bg)s; width: 12px; }
QScrollBar::handle:vertical { background: #2c2c36; border-radius: 5px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: %(accent)s; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
""" % {"bg": BG, "panel": PANEL, "panel2": PANEL2, "silver": SILVER,
       "mute": MUTE, "accent": ACCENT, "line": LINE}


def _install_excepthook():
    import traceback

    def hook(exctype, value, tb):
        msg = "".join(traceback.format_exception(exctype, value, tb))
        try:
            with open(os.path.join(_app_dir(), "dravenote-fout.txt"),
                      "w", encoding="utf-8") as f:
                f.write(msg)
        except Exception:
            pass
        try:
            if QApplication.instance():
                QMessageBox.critical(None, "DraveNote - fout",
                                     "Er ging iets mis bij het starten:\n\n"
                                     + msg[-1500:]
                                     + "\n\n(Ook opgeslagen in dravenote-fout.txt)")
        except Exception:
            pass
        sys.__excepthook__(exctype, value, tb)

    sys.excepthook = hook


def main():
    global _LANG
    _install_excepthook()
    app = QApplication(sys.argv)
    try:
        cfg = load_config()
        _LANG = detect_lang(cfg)
        app.setStyleSheet(QSS)
        win = DraveNote(cfg)
        win.show()
    except Exception:
        sys.excepthook(*sys.exc_info())
        return
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
