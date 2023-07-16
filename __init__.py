import os
from typing import Optional

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QListWidget, QDialog, QHBoxLayout, QFileDialog, QMessageBox, QErrorMessage, \
    QApplication, QLabel, QBoxLayout
from anki.lang import _
from aqt import mw, gui_hooks, qconnect
from aqt.editor import Editor
from aqt.reviewer import Reviewer
from aqt.utils import tooltip

Highlights = list()
Imported = False
Add_cards_editor: Optional[Editor] = None
OldRevHTML = Reviewer.revHtml
MainList: Optional[QListWidget] = None

IndexLabel: Optional[QLabel] = None

# ----- CONFIG -----
Config = None

Kindle_file = ""
Snippets_file = ""
# Show_list_key = 75
Truncate_length = 300
Insert_fields = [0]
Copy_to_clipboard = False


# ----- END CONFIG -----


def read_config():
    global Config, Kindle_file, Truncate_length, Insert_fields, Copy_to_clipboard, Snippets_file

    Config = mw.addonManager.getConfig(__name__)
    if Config is not None:
        Kindle_file = Config["Kindle Clippings File"]
        Snippets_file = Config["Snippets File"]
        Truncate_length = Config["Max Clippings To Import"]
        Insert_fields = Config["Insert Clipping Into Fields"]
        Copy_to_clipboard = Config["Copy Clipping To Clipboard"]


def import_snippets():
    global Highlights, Imported

    if Snippets_file == "":
        input_snippets_file_path()

    tooltip(_("Importing Snippets..."), period=1000)

    if not os.path.exists(Snippets_file):
        QErrorMessage(mw).showMessage("Error: Snippets file not found!")
        return

    Highlights = list()

    with open(Snippets_file, 'r', encoding="utf-8") as snippets_file:
        for line in snippets_file:
            stripped = line.strip().replace("\n", "")
            if not (stripped.startswith("-------") or stripped == ""):
                Highlights.append(stripped)

    snippets_file.close()

    if len(Highlights) == 0:
        QErrorMessage(mw).showMessage("Error: No clippings were imported. Did you select the correct file?")
        return

    orig_len = len(Highlights)
    if Truncate_length > 0:
        del Highlights[Truncate_length:]

    tooltip(_("Imported " + str(len(Highlights)) + " out of " + str(orig_len) + " clippings!"), period=2000)

    Imported = True


def import_clippings():
    if Kindle_file == "":
        if not input_clippings_file_path():
            return

    tooltip(_("Importing Kindle Clippings..."), period=1000)

    global Highlights, Imported

    if not os.path.exists(Kindle_file):
        QErrorMessage(mw).showMessage("Error: Kindle clippings file not found!")
        return

    Highlights = list()
    with open(Kindle_file, 'r', encoding="utf-8") as clippings_file:
        lines = clippings_file.readlines()

        for i in range(1, len(lines)):
            prev_line = lines[i - 1]
            cur_line = lines[i]
            if cur_line.strip() == "==========":
                Highlights.insert(0, prev_line)

    clippings_file.close()

    if len(Highlights) == 0:
        QErrorMessage(mw).showMessage("Error: No clippings were imported. Did you select the correct file?")
        return

    orig_len = len(Highlights)
    if Truncate_length > 0:
        del Highlights[Truncate_length:]

    tooltip(_("Imported " + str(len(Highlights)) + " out of " + str(orig_len) + " clippings!"), period=2000)

    Imported = True


def insert_highlight_text(text):
    if len(Insert_fields) > 0:
        note = Add_cards_editor.note
        for f in Insert_fields:
            note.fields[f] = text
        # Add_cards_editor.focus
        Add_cards_editor.set_note(note, focusTo=Insert_fields[-1])


def show_clippings_importer(_):
    global Add_cards_editor, MainList, IndexLabel

    if not Imported:
        tooltip(_("Error: No Highlights Imported"), period=3000)
        return

    d = QDialog(Add_cards_editor.widget)
    d.setWindowTitle("Kindle Clippings Importer")
    d.resize(400, 800)

    MainList = QListWidget()
    MainList.addItems(Highlights)
    qconnect(MainList.itemDoubleClicked, on_item_double_clicked)

    qconnect(MainList.itemSelectionChanged, on_item_selected)
    MainList.setStyleSheet("background-color: color(105,105,105);")

    layout = QHBoxLayout()
    layout.setDirection(QBoxLayout.Direction.Down)
    layout.addWidget(QLabel("Double click a clipping below to import it."))
    layout.addWidget(MainList)

    IndexLabel = QLabel()
    layout.addWidget(IndexLabel)
    on_item_selected()

    d.setLayout(layout)
    d.show()


def on_item_double_clicked(item):
    text = item.text()
    insert_highlight_text(text)

    if Copy_to_clipboard:
        QApplication.clipboard().setText(text)


def on_item_selected(_=None):
    IndexLabel.setText("Selected Item Index: " + str(MainList.currentIndex().row() + 1))


def input_snippets_file_path():
    global Snippets_file, Config

    ok = QMessageBox.information(mw, "Clippings Importer",
                                 "In the next dialog, please input your Snippets file path.",
                                 QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Cancel)

    if ok == QMessageBox.StandardButton.Ok:

        file, x = QFileDialog.getOpenFileName(mw, caption="Snippets File", filter="Text files (*.txt)")
        if file:
            tooltip(_("File Selected: " + file), period=5000)
            Snippets_file = file
            if Config is None:
                Config = {"Snippets File": Snippets_file}
            Config["Snippets File"] = Snippets_file
            mw.addonManager.writeConfig(__name__, Config)
            return True
        else:
            tooltip(_("Operation Aborted."), period=4000)

    return False


def input_clippings_file_path():
    global Kindle_file, Config

    ok = QMessageBox.information(mw, "Clippings Importer",
                                 "In the next dialog, please input your Kindle clippings file path. The file "
                                 "can be found on your Kindle device as '<kindle root>/documents/My Clippings.txt'",
                                 QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Cancel)

    if ok == QMessageBox.StandardButton.Ok:

        file, x = QFileDialog.getOpenFileName(mw, caption="Kindle Clippings File", filter="Text files (*.txt)")
        if file:
            tooltip(_("File Selected: " + file), period=5000)
            Kindle_file = file
            if Config is None:
                Config = {"Kindle Clippings File": Kindle_file}
            Config["Kindle Clippings File"] = Kindle_file
            mw.addonManager.writeConfig(__name__, Config)
            return True
        else:
            tooltip(_("Operation Aborted."), period=4000)

    return False


def build_menu():
    menu = mw.form.menuTools.addMenu("Clippings Importer")
    import_snippets_action = QAction("Import Snippets", mw)
    qconnect(import_snippets_action.triggered, import_snippets)
    menu.addAction(import_snippets_action)

    import_clippings_action = QAction("Import Kindle Clippings", mw)
    qconnect(import_clippings_action.triggered, import_clippings)
    menu.addAction(import_clippings_action)

    input_clippings_path_action = QAction("Select Kindle Clippings File", mw)
    qconnect(input_clippings_path_action.triggered, input_clippings_file_path)
    menu.addAction(input_clippings_path_action)

    input_snippets_path_action = QAction("Select Snippets File", mw)
    qconnect(input_snippets_path_action.triggered, input_snippets_file_path)
    menu.addAction(input_snippets_path_action)


def setup_buttons(buttons, editor: Editor):
    global Add_cards_editor

    Add_cards_editor = editor

    btn = editor.addButton(None,
                           'K.I.',
                           show_clippings_importer,
                           tip='Import clippings from kindle')
    buttons.append(btn)


# def on_editor_init(editor: Editor):
#     editor.widget

gui_hooks.editor_did_init_buttons.append(setup_buttons)
# gui_hooks.editor_did_init.append(on_editor_init)

read_config()
build_menu()
