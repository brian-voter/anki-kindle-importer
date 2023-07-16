import os

from anki.hooks import wrap

from PyQt5.QtWidgets import QAction, QListWidget, QDialog, QHBoxLayout, QFileDialog, QMessageBox, QErrorMessage, \
    QApplication, QLabel, QBoxLayout

from anki.lang import _
from aqt.reviewer import Reviewer
from aqt.utils import tooltip
from aqt.addcards import AddCards

from aqt import mw

Highlights = list()
Imported = False
Addcards_dialog = None
OldRevHTML = Reviewer.revHtml
MainList = None

IndexLabel = None

####   CONFIG   ####
Config = None

Kindle_file = ""
Snippets_file = ""
Show_list_key = 75
Truncate_length = 300
Insert_fields = [0]
Copy_to_clipboard = False
#### END CONFIG ####


def read_config():
    global Config, Kindle_file, Show_list_key, Truncate_length, Insert_fields, Copy_to_clipboard, Snippets_file

    Config = mw.addonManager.getConfig(__name__)
    if Config is not None:
        Kindle_file = Config["Kindle Clippings File"]
        Snippets_file = Config["Snippets File"]
        Show_list_key = Config["Insert Clippings Shortcut"]
        Truncate_length = Config["Max Clippings To Import"]
        Insert_fields = Config["Insert Clipping Into Fields"]
        Copy_to_clipboard = Config["Copy Clipping To Clipboard"]


def snippet_import():
    global Highlights, Imported

    if Snippets_file == "":
        input_snippets_file_path()

    tooltip(_("Importing Snippets..."), period=1000)

    if not os.path.exists(Snippets_file):
        QErrorMessage(mw).showMessage("Error: Snippets file not found!")
        return

    Highlights = list()

    with open(Snippets_file, 'r', encoding="utf-8") as kfile:
        for line in kfile:
            stripped = line.strip().replace("\n", "")
            if not (stripped.startswith("-------") or stripped == ""):
                Highlights.append(stripped)

    kfile.close()

    if len(Highlights) == 0:
        QErrorMessage(mw).showMessage("Error: No clippings were imported. Did you select the correct file?")
        return

    orig_len = len(Highlights)
    if Truncate_length > 0:
        del Highlights[Truncate_length:]

    tooltip(_("Imported " + str(len(Highlights)) + " out of " + str(orig_len) + " clippings!"), period=2000)

    Imported = True


def kindle_import():
    if Kindle_file == "":
        input_kindle_file_path()

    tooltip(_("Importing Kindle Clippings..."), period=1000)

    global Highlights, Imported

    if not os.path.exists(Kindle_file):
        QErrorMessage(mw).showMessage("Error: Kindle clippings file not found!")
        return

    Highlights = list()
    with open(Kindle_file, 'r', encoding="utf-8") as kfile:
        lines = kfile.readlines()

        for i in range(1, len(lines)):
            prev_line = lines[i - 1]
            cur_line = lines[i]
            if cur_line.strip() == "==========":
                Highlights.insert(0, prev_line)

    kfile.close()

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
        note = Addcards_dialog.editor.note
        for f in Insert_fields:
            note.fields[f] = text
        Addcards_dialog.setAndFocusNote(note)


def custom_key_press(caller, evt):
    global Addcards_dialog, MainList, IndexLabel

    if evt.key() == Show_list_key:

        if not Imported:
            tooltip(_("Error: No Highlights Imported"), period=2000)
            evt.accept()
            return

        Addcards_dialog = caller

        d = QDialog(Addcards_dialog)
        d.setWindowTitle("Kindle Clippings Importer")
        d.resize(400, 800)

        MainList = QListWidget()
        MainList.addItems(Highlights)
        MainList.itemDoubleClicked.connect(item_double_clicked)
        MainList.itemSelectionChanged.connect(item_selected)
        MainList.setStyleSheet("background-color: gray")

        layout = QHBoxLayout()
        layout.setDirection(QBoxLayout.Down)
        layout.addWidget(QLabel("Double click a clipping below to import it."))
        layout.addWidget(MainList)

        IndexLabel = QLabel()
        layout.addWidget(IndexLabel)
        item_selected()

        d.setLayout(layout)
        d.show()

        evt.accept()


def item_double_clicked(item):
    text = item.text()
    insert_highlight_text(text)

    if Copy_to_clipboard:
        QApplication.clipboard().setText(text)


def item_selected(item = None):
    IndexLabel.setText("Selected Item Index: " + str(MainList.currentIndex().row() + 1))


def input_snippets_file_path():
    global Snippets_file, Config

    ok = QMessageBox.information(mw, "Clippings Importer",
                                 "In the next dialog, please input your Snippets file path.",
                                 QMessageBox.Ok, QMessageBox.Cancel)

    if ok == QMessageBox.Ok:

        file, x = QFileDialog.getOpenFileName(mw, caption="Snippets File", filter="Text files (*.txt)")
        if file:
            tooltip(_("File Selected: " + file), period=5000)
            Snippets_file = file
            if Config is None:
                Config = {"Snippets File": Snippets_file}
            Config["Snippets File"] = Snippets_file
            mw.addonManager.writeConfig(__name__, Config)
        else:
            tooltip(_("Operation Aborted."), period=4000)


def input_kindle_file_path():
    global Kindle_file, Config

    ok = QMessageBox.information(mw, "Clippings Importer",
                                 "In the next dialog, please input your Kindle clippings file path. The file "
                                 "can be found on your Kindle device as '<kindle root>/documents/My Clippings.txt'",
                                 QMessageBox.Ok, QMessageBox.Cancel)

    if ok == QMessageBox.Ok:

        file, x = QFileDialog.getOpenFileName(mw, caption="Kindle Clippings File", filter="Text files (*.txt)")
        if file:
            tooltip(_("File Selected: " + file), period=5000)
            Kindle_file = file
            if Config is None:
                Config = {"Kindle Clippings File": Kindle_file}
            Config["Kindle Clippings File"] = Kindle_file
            mw.addonManager.writeConfig(__name__, Config)
        else:
            tooltip(_("Operation Aborted."), period=4000)


def build_menu():
    menu = mw.form.menuTools.addMenu("Clippings Importer")
    import_snippets_action = QAction("Import Snippets", mw)
    import_snippets_action.triggered.connect(snippet_import)
    menu.addAction(import_snippets_action)
    import_kindle_action = QAction("Import Kindle Clippings", mw)
    import_kindle_action.triggered.connect(kindle_import)
    menu.addAction(import_kindle_action)
    input_file_path = QAction("Select Kindle Clippings File", mw)
    input_file_path.triggered.connect(input_kindle_file_path)
    menu.addAction(input_file_path)
    input_snippets_path = QAction("Select Snippets File", mw)
    input_snippets_path.triggered.connect(input_snippets_file_path)
    menu.addAction(input_snippets_path)

# TODO: improve:
AddCards.keyPressEvent = wrap(AddCards.keyPressEvent, custom_key_press, "before")

read_config()
build_menu()