# Die aktuelle Logik um das Benutzerinterface für einen Plugin Demo Dialog zu implementieren.

import time, os, math
from pathlib import Path
import difflib  # https://github.com/python/cpython/blob/3.11/Lib/difflib.py

# ToDo: Use Beautifulsoup

from lxml import etree
from lxml.etree import tostring
import lxml.html

from PyQt5.QtCore import Qt
from PyQt5.Qt import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFont, QGridLayout, QSize,
                      QTextEdit, QComboBox, QCheckBox, QPushButton, QTabWidget, QScrollArea, QMessageBox, QMainWindow,
                      QApplication, QClipboard, QTextBlock, QTextBrowser, QIntValidator)  # QDocument,

from calibre.gui2 import gprefs, error_dialog, info_dialog
from calibre.ebooks.conversion.config import (get_input_format_for_book, sort_formats_by_preference)
from calibre.ebooks.oeb.iterator import EbookIterator
from calibre.utils.logging import Log as log
from calibre.library import db
from calibre.ptempfile import PersistentTemporaryFile, PersistentTemporaryDirectory

from calibre_plugins.textdiff.config import prefs


class TextDiffDialog(QDialog):

    def __init__(self, gui, icon, do_user_config):
        QDialog.__init__(self, gui)
        self.gui = gui
        self.do_user_config = do_user_config
        book_ids = []

        # Overwrite Difflib table and file templates (remove legend and modernize html and css)

        #     <table class="diff" id="difflib_chg_%(prefix)s_top"
        #            cellspacing="0" cellpadding="0" rules="groups" >
        #         <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>
        #         <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>
        #         %(header_row)s
        #         <tbody>
        # %(data_rows)s        </tbody>
        #     </table>"""

        self.table_template = """
            <table class="diff" id="difflib_chg_%(prefix)s_top"
                   cellspacing="0" cellpadding="0">
               <colgroup>
                   <col style="width:2%%">
                   <col style="width:4%%">
                   <col style="width:44%%">
                   <col style="width:2%%">
                   <col style="width:4%%">
                   <col style="width:44%%">
               </colgroup>
               %(header_row)s
               <tbody>
                    %(data_rows)s
               </tbody>
            </table>"""

        self.file_template =  """
        <!DOCTYPE html>
        <html>
            <head>
                <meta http-equiv="Content-Type"
                      content="text/html; charset=%(charset)s" />
                <title>TextDiff</title>
                <style>%(styles)s</style>
            </head>
            <body>  
                %(table)s
            </body>
        </html>
        """

        # New CSS for table cols
        # <tr>
        # <td class="diff_next"></td>
        # <td class="diff_header" id="from0_4">4</td>
        # <td nowrap="nowrap">(some text or blank line from file 1</td>
        # <td class="diff_next"></td>
        # <td class="diff_header" id="to0_32">32</td>
        # <td nowrap="nowrap">(some text or blank line from file 1)</td>
        # </tr>

        self.styles = """
        table.diff {
            width: 100%;
            table-layout: fixed;
            border-spacing: 0;
            font-family: sans-serif; 
            border: none;
            border-collapse: collapse;
        }
        th, td {
            white-space:nowrap;
        }
        .diff_header {background-color:#e0e0e0}
        td.diff_header {text-align:right}
        .diff_next {background-color:#c0c0c0}
        .diff_add {background-color:#aaffaa}
        .diff_chg {background-color:#ffff77}
        .diff_sub {background-color:#ffaaaa}
        """


        # The current database shown in the GUI
        # db is an instance of the class LibraryDatabase from db/legacy.py
        # This class has many, many methods that allow you to do a lot of
        # things. For most purposes you should use db.new_api, which has
        # a much nicer interface from db/cache.py
        self.db = gui.current_db

        self.grid_layout = QGridLayout()
        # GridLayout layout = new GridLayout(2,5);  # Java

        # ToDo: Generell auf ereignisse reagieren (single form interface)

        #         self.checkbox = QtWidgets.QCheckBox("Use This Config File")
        #         self.checkbox.setMinimumHeight(30)
        #         self.checkbox.stateChanged.connect(self.use_config_file)
        #         self.checkbox.setToolTip(msg)
        #         self.gl7.addWidget(self.checkbox, 1, 0, 1, 1)
        #         if ui.use_custom_config_file:
        #             self.checkbox.setChecked(True)

        #         self.checkbox = QtWidgets.QCheckBox("Use This Config File")
        #         self.checkbox.setMinimumHeight(30)
        #         self.checkbox.stateChanged.connect(self.use_config_file)
        #         self.checkbox.setToolTip(msg)
        #         self.gl7.addWidget(self.checkbox, 1, 0, 1, 1)
        #         if ui.use_custom_config_file:
        #             self.checkbox.setChecked(True)
        
        # Header for file info
        self.file_header_0 = QLabel(_('1st file (left):'))
        self.file_header_0.setObjectName(f"file_header_0")
        self.file_header_1 = QLabel(_('2nd file (right):'))
        self.file_header_1.setObjectName(f"file_header_1")
        
        # File info
        # ToDo: Widgets with variable name?
        # for i in range(2):
        #     self.file_info_widgets[i] = QLabel()
        #     self.file_info_widgets[i].setObjectName('file_info_{0}'.format(i))
        self.file_info_0 = QLabel()
        self.file_info_0.setObjectName('file_info_0')
        self.file_info_1 = QLabel()
        self.file_info_1.setObjectName('file_info_1')

        self.txt_file_content_combo_0 = QComboBox()
        self.txt_file_content_combo_0.setObjectName("txt_file_content_combo_0")
        # self.cb.currentIndexChanged.connect(self.selectionchange)
        # self.input.editingFinished.connect(self.input_changed)
        self.txt_file_content_combo_1 = QComboBox()
        self.txt_file_content_combo_1.setObjectName("txt_file_content_combo_1")
        # self.cb.currentIndexChanged.connect(self.selectionchange)

        self.refresh_formats_button = QPushButton(_('Refresh formats list.'), self)
        self.refresh_formats_button.clicked.connect(self.refresh_formats)

        # linejunk=None, charjunk=IS_CHARACTER_JUNK (difflib.ndiff)

        self.compare_output_label = QLabel(_('Display format:'))
        self.compare_output_label.setAlignment(Qt.AlignRight)
        self.compare_output_combo = QComboBox()
        self.compare_output_combo.setObjectName("compare_output_combo")
        output_formats = ['HTML', 'Unified']
        self.compare_output_combo.addItems(x for x in output_formats)
        self.compare_output_combo.currentTextChanged.connect(self.on_compare_output_combo_changed)

        # Nur bei unified_diff!
        # Unified diffs are a compact way of showing just the lines that have changed plus a few lines of context.
        # The changes are shown in an inline style (instead of separate before/after blocks).
        # The number of context lines is set by n which defaults to three.
        self.context_lines_label = QLabel(_('Number of context lines for unified diff:'))
        self.context_lines_label.setAlignment(Qt.AlignRight)
        self.context_lines = QLineEdit(self)
        self.context_lines.setFixedWidth(30)
        self.context_lines.setAlignment(Qt.AlignRight)
        self.context_lines.setValidator(QIntValidator())
        self.context_lines.setMaxLength(2)
        self.context_lines.setText('3')
        self.context_lines.setEnabled(False)  # enabled only when compare_output_combo is 'HTML''


        # ToDo: Rahmen um zusammengehörige widgets
        # groupbox = QGroupBox("GroupBox Example")
        # groupbox.setCheckable(True)
        # layout.addWidget(groupbox)
        #
        # vbox = QVBoxLayout()
        # groupbox.setLayout(vbox)
        # Individual widgets can then be added to the QVBoxLayout.
        # vbox.addWidget(radiobutton)
        # vbox.addWidget(radiobutton)
        # vbox.addWidget(radiobutton)

        # Nur bei HtmlDiff! context=True, numlines=10
        # ToDo: ebenfalls combo prüfen, wie oben
        self.context_diff = QCheckBox(_('Only contextual diffs'))
        # Set context to True when contextual differences are to be shown, else the default is False to show the full files.
        self.context_diff.setChecked(False)
        self.context_diff.stateChanged.connect(self.oncontext_diffChangedState)

        # numlines defaults to 5. When context is True numlines controls the number of context lines which surround
        # the difference highlights. When context is False numlines controls the number of lines which are shown
        # before a difference highlight when using the “next” hyperlinks (setting to zero would cause the “next”
        # hyperlinks to place the next difference highlight at the top of the browser without any leading context).
        self.numlines_label = QLabel(_('Number of context lines:'))
        self.numlines_label.setAlignment(Qt.AlignRight)
        self.numlines = QLineEdit(self)
        self.numlines.setFixedWidth(30)
        self.numlines.setAlignment(Qt.AlignRight)
        self.numlines.setValidator(QIntValidator())
        self.numlines.setMaxLength(2)
        self.numlines.setText('5')
        # if initial_value != None:
        #     self.lnumines.setText(str(initial_value))
        self.numlines.setEnabled(False)  # enabled only when context_diff is checked


        self.compare_button = QPushButton(_('Compare'), self)
        self.compare_button.clicked.connect(self.compare)

        self.text_browser = QTextBrowser()
        self.text_browser.setAcceptRichText(True)
        self.text_browser.setOpenExternalLinks(False)
        # self.text_browser.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        # self.text_browser.setFont(QFontDatabase.systemFont(QFontDatabase.xxxxxxxxxxxxxxxx  non FixedFont))

        self.hide_equals = QCheckBox(_('Hide equal lines'))
        self.hide_equals.setChecked(False)

        # ToDo: calculate similarity (SequenceMatcher)
        self.calculate_ratio = QCheckBox(_('Calculate ratio (similarity)'))
        self.calculate_ratio.setChecked(False)

        self.save_diff_file_button = QPushButton(_('Save diff to file.'), self)
        self.save_diff_file_button.clicked.connect(self.save_diff_file)

        # addWidget(*Widget, row, column, rowspan, colspan)
        # row 0
        self.grid_layout.addWidget(self.file_header_0, 0, 0, 1, 1);
        self.grid_layout.addWidget(self.file_header_1, 0, 1, 1, 1);
        # row 1
        self.grid_layout.addWidget(self.file_info_0, 1, 0, 1, 1)
        self.grid_layout.addWidget(self.file_info_1, 1, 1, 1, 1)
        # row 2
        self.grid_layout.addWidget(self.txt_file_content_combo_0, 2, 0, 1, 1)
        self.grid_layout.addWidget(self.txt_file_content_combo_1, 2, 1, 1, 1)
        # row 3
        self.grid_layout.addWidget(self.refresh_formats_button, 3, 0, 1, 2)
        # row 4
        self.grid_layout.addWidget(self.compare_output_label, 4, 0, 1, 1)
        self.grid_layout.addWidget(self.compare_output_combo, 4, 1, 1, 1)
        # row 5: nur bei unified_diff
        self.grid_layout.addWidget(self.context_lines_label, 5, 0, 1, 1)
        self.grid_layout.addWidget(self.context_lines, 5, 1, 1, 1)
        # row 6: Nur bei HtmlDiff
        self.grid_layout.addWidget(self.context_diff, 6, 1, 1, 1)
        # row 7
        self.grid_layout.addWidget(self.numlines_label, 7, 0, 1, 1)
        self.grid_layout.addWidget(self.numlines, 7, 1, 1, 1)
        # row 8
        self.grid_layout.addWidget(self.compare_button, 8, 0, 1, 2)
        # row 9
        self.grid_layout.addWidget(self.hide_equals, 9, 0, 1, 1)
        self.grid_layout.addWidget(self.calculate_ratio, 9, 1, 1, 1)
        # row 10
        self.grid_layout.addWidget(self.text_browser, 10, 0, 1, 2)
        # row 11
        self.grid_layout.addWidget(self.save_diff_file_button, 11, 0, 1, 2)

        # Two column grid that fills the width of the page, each column taking up one half the space
        # If you want two columns to have the same width, you must set their minimum widths and stretch factors
        # to be the same yourself. You do this using addColSpacing() and setColStretch().
        self.grid_layout.setColumnMinimumWidth(0, 200)
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnMinimumWidth(1, 200)
        self.grid_layout.setColumnStretch(1, 1)

        self.setLayout(self.grid_layout)

        self.setWindowTitle(_('TextDiff Plugin'))
        self.setWindowIcon(icon)
        # Initialize a statusbar for the window
        # self.statusbar = self.statusBar()

        self.resize(self.sizeHint())

        self.refresh_formats()


    def IS_CHARACTER_JUNK(ch, ws=" \t"):
        r"""
        Return True for ignorable character: iff `ch` is a space or tab.
        Examples:
        >>> IS_CHARACTER_JUNK(' ')
        True
        >>> IS_CHARACTER_JUNK('\t')
        True
        >>> IS_CHARACTER_JUNK('\n')
        False
        >>> IS_CHARACTER_JUNK('x')
        False
        """
        return ch in ws

    def oncontext_diffChangedState(self, checked):
        if self.context_diff.isChecked():
            self.numlines.setEnabled(True)
        else:
            self.numlines.setEnabled(False)

    def on_compare_output_combo_changed(self, value):
        if value == 'Unified':
            self.context_lines.setEnabled(True)
        else:
            self.context_lines.setEnabled(False)


    def sizeHint(self):
        # notwendig? (stammt aus single.py)
        geom = self.screen().availableSize()
        nh, nw = max(300, geom.height() - 400), max(400, geom.width() - 400)
        return QSize(nw, nh)

    @property
    def input_format(self):
        return str(self.input_formats.currentText()).lower()

    # def setup_input_formats(self, db, book_id):
    #     input_format, input_formats = get_input_format_for_book(db, book_id)
    #     self.input_formats.addItems(str(x.upper()) for x in input_formats)
    #     self.input_formats.setCurrentIndex(input_formats.index(input_format))


    def close_dialog(self):
        pass


    def refresh_formats(self):

        # refresh formats list (e. g. after marked new books)

        # Check the number of books that are marked
        db = self.gui.current_db.new_api
        self.book_ids = self.gui.library_view.get_selected_ids()  # Get a list of book ids
        print(self.book_ids)
        book_count = len(self.book_ids)
        if book_count == 0 or book_count > 2:
            d = error_dialog(self.gui,
                             _('TextDiff error'),
                             _('One or two books (with at least total two formats) must be marked.'),
                             show_copy_button=False)
            d.exec_()
            return None

        # # Fill the files and formats fields
        # # and check the number of formats
        # input_formats = []
        # db = self.gui.library_view.model().db
        # for book_id in book_ids:
        #     input_formats.append(get_input_format_for_book(db, self.book_id))
        # print('input_formats=')
        # print(input_formats)
        # format_count = len(input_formats)
        # if format_count < 2:
        #     d = error_dialog(self.gui,
        #                      _('TextDiff error'),
        #                      _('Two formats are needed.'),
        #                      show_copy_button=False)
        #     d.exec_()
        #     return None

        if book_count == 2:
            # Two books with at least two formats in sum
            for i in range(2):
                mi = db.get_metadata(self.book_ids[i])
                title, formats = mi.title, mi.formats
                # ToDo: How name widgets for looping?
                if i == 0:
                    self.file_info_0.setText(str(self.book_ids[i]) + '=' + mi.title)
                    self.txt_file_content_combo_0.clear()
                    self.txt_file_content_combo_0.addItems(str(x.upper()) for x in mi.formats)
                else:
                    self.file_info_1.setText(str(self.book_ids[i]) + '=' + mi.title)
                    self.txt_file_content_combo_1.clear()
                    self.txt_file_content_combo_1.addItems(str(x.upper()) for x in mi.formats)
        else:
            # One book with at least two formats
            mi = db.get_metadata(self.book_ids[0])
            for i in range(2):
                if i == 0:
                    self.file_info_0.setText(str(self.book_ids[0]) + '=' + mi.title)
                    self.txt_file_content_combo_0.clear()
                    self.txt_file_content_combo_0.addItems(str(x.upper()) for x in mi.formats)
                else:
                    self.file_info_1.setText(str(self.book_ids[0]) + '=' + mi.title)
                    self.txt_file_content_combo_1.clear()
                    self.txt_file_content_combo_1.addItems(str(x.upper()) for x in mi.formats)


    def save_current_file(self):
        # ToDo: Save as html or txt, depending on output format combo
        if not self.file_path:
            new_file_path, filter_type = QFileDialog.getSaveFileName(self, "Save this file as...", "", "All files (*)")
            if new_file_path:
                self.file_path = new_file_path
            else:
                self.invalid_path_alert_message()
                return False
        file_contents = self.scrollable_text_area.toPlainText()
        with open(self.file_path, "w") as f:
            f.write(file_contents)
        self.title.setText(self.file_path)


    def closeEvent(self, event):

        event.accept()

        # messageBox = QMessageBox()
        # title = _("Quit Application?")
        # message = "WARNING !!\n\nIf you quit without saving, any changes made to the file will be lost.\n\nSave file before quitting?"
        # reply = messageBox.question(self, title, message, messageBox.Yes | messageBox.No | messageBox.Cancel, messageBox.Cancel)
        # if reply == messageBox.Yes:
        #     return_value = self.save_current_file()
        #     if return_value == False:
        #         event.ignore()
        # elif reply == messageBox.No:
        #     event.accept()
        # else:
        #     event.ignore()


    def copy_all(self):
        # paste entire text in compare result to clipboard
        txt = self.result_text.selectAll()
        QApplication.clipboard().setText(txt)


    # ToDo: compare(txt_file_path[0], txt_file_path[1], options). convert separat!
    def compare(self):
        # This is the main process
        log('Starting compare...')
        self.gui.status_bar.showMessage(_('Starting compare...'))

        # db = self.gui.current_db.new_api
        db = self.gui.library_view.model().db
        book_ids = self.gui.library_view.get_selected_ids()  # Get a list of book ids
        print('book_ids:')
        print(book_ids)  # [285, 286]
        book_count = len(book_ids)
        # rows = self.gui.library_view.selectionModel().selectedRows()
        # if not rows or len(rows) == 0:
        if book_count == 0:
            return error_dialog(self.gui, _('No rows selected'),
                            _('You must select one book with more than one format or two books to perform this action.'), show=True)
        if book_count > 2:
            return error_dialog(self.gui, _('Too much rows selected'),
                                _('You must select one book with more than one format or two books to perform this action.'), show=True)
        # show_copy_button=False

        # ToDo: refactoring doubled code

        paths_for_formats = []
        for book_id in book_ids:
            print(book_id)
            mi = db.get_metadata(book_id, index_is_id=True, get_user_categories=False)
            title, formats = mi.title, mi.formats
            fi = 0
            for format in formats:
                print(format)
                if fi == 0 and format == str(self.txt_file_content_combo_0.currentText()).upper():
                    paths_for_formats.append((book_id, format, db.format_abspath(book_id, format, index_is_id=True)))
                if fi == 1 and format == str(self.txt_file_content_combo_1.currentText()).upper():
                    paths_for_formats.append((book_id, format, db.format_abspath(book_id, format, index_is_id=True)))
                fi = fi + 1
                print(paths_for_formats)
        print('**********')
        print('paths_for_formats={0}'.format(paths_for_formats))
        # [(285, 'EPUB', 'E:\\Bibliotheken\\Abenteuer\\Jules Verne\\Meister Antifers wunderbare Abenteu (285)\\Meister Antifers wunderbare Abe - Jules Verne.epub'),
        # (285, 'PDF', 'E:\\Bibliotheken\\Abenteuer\\Jules Verne\\Meister Antifers wunderbare Abenteu (285)\\Meister Antifers wunderbare Abe - Jules Verne.pdf')]
        # [(286, 'PDF', 'E:\Bibliotheken\Abenteuer\\Sven Hedin\Abenteuer in Tibet. 1899 - 1902_ (286)\\Abenteuer in Tibet. 1899 - 1902 - Sven Hedin.pdf')]

        if len(paths_for_formats) < 2:
            return error_dialog(self.gui, _('Not enough formats to compare'),
                                _('The selected book(s) must have at least two formats to compare.'),
                                show=True)

        # finding the content of current item in combo box and save as input formats
        # (output format is always txt)
        selected_formats = []
        selected_formats.append(str(self.txt_file_content_combo_0.currentText()).upper())
        selected_formats.append(str(self.txt_file_content_combo_1.currentText()).upper())
        print('selected_formats: {0}'.format(selected_formats))  # ['EPUB', 'PDF']

        # Kovid says:
        # If you want to extract text the easiest way to do it is to convert to txt.
        # You basically need to run the input format plugin on the file, then you can use
        # calibre.ebooks.oeb.polish.container.Container object to access the contents of the result
        # of running the input format plugin

        filtered_paths = paths_for_formats
        print('filtered_paths: {0}'.format(filtered_paths))

        text_formats = []
        # convert_options = ' -v -v –enable-heuristics '
        convert_options = ' -v -v '
        convert_options = convert_options + ' --sr1-search (?m)^\s*$ --sr1-replace ""'
        # if re.match(r'^\s*$', line):
        #     # line is empty (has only the following: \t\n\r and whitespace)
        # --sr1-replace
        # Ersatz zum Ersetzen des mit "sr1-search" gefundenen Textes.
        # --sr1-search
        # Suchmuster (regulärer Ausdruck), das durch "sr1-replace" ersetzt werden soll.

        for filtered_path in filtered_paths:
            # Convert the input format to text format, even if format is already TXT to apply convert options
            result = self.ebook_convert(filtered_path, convert_options)
            print('result={0}'.format(result))
            qualifier = str(result[0])
            txt_format_path = str(result[1])
            text_formats.append(txt_format_path)

        print('text_formats={0}'.format(text_formats))
        txt_file_path = []
        for i, text_format in enumerate(text_formats):
            txt_file_path.append(Path(text_format))

        # Qualify diff file with book id(s)
        # ToDo: Generate diff_file only when appropiate button is pressed.
        # if os.path.exists(diff_file):
        #     os.remove(diff_file)
        diff_file = Path(os.path.dirname(os.path.abspath(txt_file_path[0])) + '\\diff_file' + qualifier + '.html')
        print('txt_file_path[0]=' + txt_file_path[0].name)
        print('txt_file_path[1]=' + txt_file_path[1].name)
        print('diff_file=' + diff_file.name)

        # ToDo: Fenster in den Vordergrund bringen

        print('Beginning compare...')
        self.gui.status_bar.showMessage(_('Beginning compare...'))

        # delta = self.create_diff(txt_file_path[0], txt_file_path[1], diff_file, diff_options)
        
        # ToDo: move code to function and activate call
        # https://docs.python.org/3/library/difflib.html

        # "readlines" returns a list containing the lines.

        txt_file_content = [None, None]
        for i in range(2):
            if os.path.exists(txt_file_path[i]):
                print('Reading file {0} in list...'.format(i + 1))
                with open(txt_file_path[i]) as f:
                    # Get rid of empty lines
                    # If you use the None as a function argument, the filter method will remove any element
                    # from the iterable that it considers to be false.
                    txt_file_content[i] = list(filter(None, (line.rstrip() for line in f)))
                print('File {0} has {1} lines.'.format(i + 1, len(txt_file_content[i])))
                print('The first 10 items are:')
                print(txt_file_content[i][:10])
                # txt_file_content[i] = open(txt_file_path[i]).readlines()
            else:
                return error_dialog(self.gui, _('TextDiff plugin'),
                                    _('The file {0} don\'t exist. Probably conversion to text format failed.'.format(txt_file_path[i])),
                                    show=True)

        # with open(txt_file_path[0]) as f:
        #     txt_file_content[0] = list(line for line in (l.strip() for l in f) if line)
        # with open(txt_file_path[1]) as f:
        #     txt_file_content[1] = list(line for line in (l.strip() for l in f) if line)

        # ToDo: code nach folgendem call in create_diff auslagern:
        #delta = self.create_diff(txt_file_path[0], txt_file_path[1], diff_file)

        # https://docs.python.org/3/library/difflib.html
        # ToDo: wrapcolumn, linejunk, charjunk as parm
        print('Instantiate HtmlDiff...')
        d = difflib.HtmlDiff(tabsize=4, wrapcolumn=60, linejunk=None, charjunk=TextDiffDialog.IS_CHARACTER_JUNK)

        if str(self.compare_output_combo.currentText()).upper() == 'HTML':

            # Overwrite Difflib table and file templates (remove legend and modernize html and css)
            d._table_template = self.table_template
            d._file_template = self.file_template
            d._styles = self.styles

            #     """For producing HTML side by side comparison with change highlights.
            #     This class can be used to create an HTML table (or a complete HTML file
            #     containing the table) showing a side by side, line by line comparison
            #     of text with inter-line and intra-line change highlights.  The table can
            #     be generated in either full or contextual difference mode.
            #     The following methods are provided for HTML generation:
            #     make_table -- generates HTML for a single side by side table
            #     make_file -- generates complete HTML file with a single side by side table
            #     See tools/scripts/diff.py for an example usage of this class.
            #     """

            #         Arguments:
            #         fromlines -- list of "from" lines
            #         tolines -- list of "to" lines
            #         fromdesc -- "from" file column header string
            #         todesc -- "to" file column header string
            #         context -- set to True for contextual differences (defaults to False
            #             which shows full differences).
            #         numlines -- number of context lines.  When context is set True,
            #             controls number of lines displayed before and after the change.
            #             When context is False, controls the number of lines to place
            #             the "next" link anchors before the next change (so click of
            #             "next" link jumps to just before the change).
            #         charset -- charset of the HTML document
            #         """

            # ToDo: ggf.nur make_table verwenden:
            # make_table(fromlines, tolines, fromdesc='', todesc='', context=False, numlines=5)
            # Compares fromlines and tolines (lists of strings) and returns a string which is a complete HTML table showing line by line differences with inter-line and intra-line changes highlighted.
            # The arguments for this method are the same as those for the make_file() method

            print('Calling HtmlDiff.make_file...')
            # ToDO: Muss weiter nach unten!!!
            #  kein make_file, nur noch make_table, bei html bzw. unified_diff
            delta = d.make_file(txt_file_content[0], txt_file_content[1], txt_file_path[0].name, txt_file_path[1].name,
                                context=self.context_diff.isChecked(), numlines=int(self.numlines.text()), charset='utf-8')
            # difflöib.HmlDiff.__init__()

            # d = difflib.HtmlDiff()#wrapcolumn=10)
            # html = d.make_file(lines1, lines2)
            # delta = difflib.HtmlDiff().make_table(txt_file_content[0], txt_file_content[1], txt_file_path[0].name, txt_file_path[1].name)
            # ToDo: Direkt speichern geht nicht. delta ist bei make_table ein generator!!!!!!!!!!!

            print('Compare finished, delta[:2000]=' + delta[:2000])
            self.gui.status_bar.showMessage(_('Compare finished.'))

            # ToDo: ggf. make_table verwenden:
            # make_table(fromlines, tolines, fromdesc='', todesc='', context=False, numlines=5)
            # Compares fromlines and tolines (lists of strings) and returns a string which is a complete HTML table showing line by line differences with inter-line and intra-line changes highlighted.
            # The arguments for this method are the same as those for the make_file() method

            # ToDo: Fortschrittsanzeige

            # Show Diff in GUI

            # Check if differences found
            # <tr>
            # <td class="diff_next"><a href="#difflib_chg_to2__top">t</a></td>
            # <td></td>
            # <td>&nbsp;No Differences Found&nbsp;</td>
            # <td class="diff_next"><a href="#difflib_chg_to2__top">t</a></td>
            # <td></td>
            # <td>&nbsp;No Differences Found&nbsp;</td>
            # </tr>

            # ToDo: delta in Abhängigkeit von compare_output_combo ermitteln, und dann erst den output prüfen!
            if '<td>&nbsp;No Differences Found&nbsp;</td>' in delta:
                self.result_text.setPlainText(_('No differences found in text. However, there may be differences in formatting or MIME content.'))

            else:

                # Remove colspan:
                # <thead><tr>
                # <th class="diff_next"><br /></th><th colspan="2" class="diff_header">(left file path)</th>
                # <th class="diff_next"><br /></th><th colspan="2" class="diff_header">(right file path)</th>
                # </tr></thead>
                # thead = etree.HTML(delta).find("body/table/thead/tr")
                # thead.set('<th colspan="2" class="diff_header">',
                #           '<th class="diff_header"></th> <th class="diff_header"></th>')

                # ToDo: keine Block-Tabelle bauen, sondern zwei Versionen der html-Tabelle!
                # Build <tbody><tr><td> list for hide/unhide equal blocks in text browser
                # table = etree.HTML(delta).find("body/table/tbody")
                # rows = iter(table)
                # headers = [col.text for col in next(rows)]
                # diff_rows = ['class="diff_add">', 'class="diff_sub">', 'class="diff_chg">']
                # equal_rows = []
                # row_no = 0
                # for row in rows:
                #     print('row[:200]={0}'.format(tostring(row)[:200]))
                #     row_no = row_no + 1
                #     # add row number to equal rows list, wenn not in rows with differences:
                #     # if any(diff_str in row.iter() for diff_str in diff_rows):
                #     if any(diff_str in row for diff_str in diff_rows):
                #         print('Row with differences - row[:200]={0}'.format(tostring(row.text)[:200]))
                #         continue
                #     print('Row without differences - row[:200]={0}'.format(tostring(row.text)[:200]))
                #     equal_rows.append(row_no)
                # print('equal_rows={0}'.format(equal_rows))

                # self write_diff_file(diff_file, delta)
                with open(diff_file, 'w') as f:
                    f.write(delta)
                    # Show Diff in GUI
                    # with open(diff_file, 'r') as f:
                    #     self.result_text.clear()
                    #     self.result_text.setHtml(f.read())
                    # ToDo: Schreiben erst wenn "Speichern"-Button gedrückt?
                    #  (Dann direkt diff_file in text_browser kippen)
                    with open(diff_file, 'r') as f:
                        # self.text_browser.setSource(QtCore.QUrl.fromLocalFile(diff_file))
                        self.text_browser.clear()
                        self.text_browser.insertHtml(f.read())

                # self.result_text.setHtml(delta)

                # doc = self.result_text.document()
                doc = self.text_browser.document()
                # Check if equal lines are to suppressed
                if self.hide_equals.isChecked():
                    for blockIndex in range(doc.blockCount()):
                        # for blockIndex in range(100):
                        block = doc.findBlockByNumber(blockIndex)
                        # DEBUG: Print the first 600 blcks (100 rows in html output)
                        if block.blockNumber() < 600:
                            print('Block # {0} has a lengt of {1}:'.format(block.blockNumber(), block.length()))
                            print('The text content is: {0}'.format(block.text()))
                        # check if block is in equal_rows list (ignore 4 block for header)
                        if math.ceil((block.blockNumber() - 4) / 6) in equal_rows:
                            block.setVisible(False)

        elif str(self.compare_output_combo.currentText()).upper() == 'UNIFIED':
            delta = difflib.unified_diff(txt_file_content[0], txt_file_content[1], txt_file_path[0].name, txt_file_path[1].name)
            text = ''
            newline = '\n'
            for line in delta:
                text += line
                # Work around missing newline (http://bugs.python.org/issue2142).
                if text and not line.endswith(newline):
                    text += newline
            print('delta=' + text[:800])
            # Show Diff in GUI
            self.result_text.clear()
            self.result_text.setPlainText(text)

        else:
            self.result_text.clear()
            self.result_text.setPlainText(_('Unknown compare output option!'))

        # Delete the generated files
        print('Deleting temp files...')
        if os.path.exists(text_formats[0]):
            os.remove(text_formats[0])
        if os.path.exists(text_formats[1]):
            os.remove(text_formats[1])
        # if os.path.exists(diff_file):
        #     os.remove(diff_file)

        return


    def remove_soft_hyphens(self, input_file, output_file, options):
        # ToDo: Remove soft hyphens
        # ebook-polish [options] input_file [output_file]
        # --remove-soft-hyphens

        pass


    def ebook_convert(self, filtered_path, convert_options):
        # Convert the input format to text format, even if format is already TXT to apply convert options
        qualifier = ''  # ToDo: warum diese variable. wird eigentlich nix mit gemacht (außer zuweisung unten)
        txt_format_path = filtered_path[2]  # path for converted text format
        txt_format_path = '_'.join(txt_format_path.rsplit('.', 1))
        txt_format_path = txt_format_path + '_' + str(filtered_path[0])  # Qualify text file name with book_id
        qualifier = qualifier + '_' + str(filtered_path[0])
        txt_format_path = txt_format_path + '.txt'  # path for converted text format
        print('txt_format_path={0}'.format(txt_format_path))

        # self.remove_soft_hyphens(input_file, output_file, options)

        print('Starting ebook-convert...')
        self.gui.status_bar.showMessage(_('Starting ebook-convert...'))
        # Remove any old file
        if os.path.exists(txt_format_path):
            os.remove(txt_format_path)

        os.system('ebook-convert ' + '"' + filtered_path[2] + '"' + ' "' +
                  txt_format_path + '"' +
                  convert_options)

        return qualifier, txt_format_path


    def create_diff(self, txt_file_path: Path, diff_file: Path = None):

        delta = None






        # # https://docs.python.org/3/library/difflib.html
        #
        # print('txt_file_path[0]=' + txt_file_path[0].name)
        # print('txt_file_path[1]=' + txt_file_path[1].name)
        # txt_file_content[0] = open(txt_file_path[0]).readlines()
        # txt_file_content[1] = open(txt_file_path[1]).readlines()
        #
        # print('Beginning compare...')
        # self.gui.status_bar.showMessage(_('Starting compare...'))
        #
        # if str(self.compare_output_combo.currentText()).upper() == 'HTML':
        #
        #     delta = difflib.HtmlDiff().make_file(txt_file_content[0], txt_file_content[1], txt_file_path[0].name, txt_file_path[1].name)
        #
        #     # ToDo: ggf. make_table verwenden:
        #     # make_table(fromlines, tolines, fromdesc='', todesc='', context=False, numlines=5)
        #     # Compares fromlines and tolines (lists of strings) and returns a string which is a complete HTML table showing line by line differences with inter-line and intra-line changes highlighted.
        #     # The arguments for this method are the same as those for the make_file() method
        #
        #     # ToDo: Fortschrittsanzeige
        #
        #     with open(diff_file, "w") as f:
        #         f.write(delta)
        # elif str(self.compare_output_combo.currentText()).upper() == 'UNIFIED':
        #     delta = difflib.unified_diff(txt_file_content[0], txt_file_content[1], txt_file_path[0].name, txt_file_path[1].name)
        #     sys.stdout.writelines(delta)
        # else:
        #     delta = None

        return delta


    def save_diff_file(self, diff_file, delta):
        # Schreiben erst wenn "Speichern"-Button gedrückt

        # ToDo: HTML ergänzen, wenn htmldiff mit table_diff  (delta enthält nur Tabelle)
        with open(diff_file, 'w') as f:
            f.write(delta)


    def get_book_info_from_book_id(self, book_id):
        book = {}
        book['calibre_id'] = book_id
        # ToDo:
        book['title'] = _('Unknown')
        book['author'] = _('Unknown')
        return book

    def populate_book_from_calibre_id(self, book, db=None, tdir=None):
        mi = db.get_metadata(book['calibre_id'], index_is_id=True)

        # from https://github.com/kovidgoyal/calibre/blob/master/src/calibre/gui2/convert/metadata.py
        # mi = self.db.get_metadata(self.book_id, index_is_id=True)
        # self.title.setText(mi.title), self.title.home(False)

        #book = {}
        book['good'] = True
        book['calibre_id'] = mi.id
        book['title'] = mi.title
        book['authors'] = mi.authors
        book['author_sort'] = mi.author_sort
        book['tags'] = mi.tags
        book['series'] = mi.series
        book['comments'] = mi.comments
        book['publisher'] = mi.publisher
        book['pubdate'] = mi.pubdate
        if book['series']:
            book['series_index'] = mi.series_index
        else:
            book['series_index'] = None
        book['languages'] = mi.languages
        book['error'] = ''
        if db.has_format(mi.id,'EPUB',index_is_id=True):
            # don't need metadata, use epub directly
            book['epub'] = db.format_abspath(mi.id,'EPUB',index_is_id=True)
        else:
            book['good'] = False;
            book['error'] = _("%s by %s doesn't have an EPUB.")%(mi.title,', '.join(mi.authors))

    def get_calibre_books():
        """Get the list of books and authors from my Calibre eBook library."""
        # First open the Calibre library and get a list of the book IDs
        calibre_db = calibre.library.db(
            ebooksconf.CALIBRE_LIBRARY_LOCATION
        ).new_api
        book_ids = calibre_db.all_book_ids()
        print("Got {} book IDs from Calibre library".format(len(book_ids)))


    def marked(self):
        ''' Show books with only one format '''
        db = self.db.new_api
        matched_ids = {book_id for book_id in db.all_book_ids() if len(db.formats(book_id)) == 1}
        # Mark the records with the matching ids
        # new_api does not know anything about marked books, so we use the full
        # db object
        self.db.set_marked_ids(matched_ids)

        # Tell the GUI to search for all marked records
        self.gui.search.setEditText('marked:true')
        self.gui.search.do_search()

    def view(self):
        ''' View the most recently added book '''
        most_recent = most_recent_id = None
        db = self.db.new_api
        for book_id, timestamp in db.all_field_for('timestamp', db.all_book_ids()).items():
            if most_recent is None or timestamp > most_recent:
                most_recent = timestamp
                most_recent_id = book_id

        if most_recent_id is not None:
            # Get a reference to the View plugin
            view_plugin = self.gui.iactions['View']
            # Ask the view plugin to launch the viewer for row_number
            view_plugin._view_calibre_books([most_recent_id])

    def update_metadata(self):
        '''
        Set the metadata in the files in the selected book's record to
        match the current metadata in the database.
        '''
        from calibre.ebooks.metadata.meta import set_metadata
        from calibre.gui2 import error_dialog, info_dialog

        # Get currently selected books
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows or len(rows) == 0:
            return error_dialog(self.gui, 'Populate format combo boxes',
                             'No books selected', show=True)
        # Map the rows to book ids
        ids = list(map(self.gui.library_view.model().id, rows))
        db = self.db.new_api
        for book_id in ids:
            # Get the current metadata for this book from the db
            mi = db.get_metadata(book_id, get_cover=True, cover_as_data=True)
            fmts = db.formats(book_id)
            if not fmts:
                continue
            for fmt in fmts:
                fmt = fmt.lower()
                # Get a python file object for the format. This will be either
                # an in memory file or a temporary on disk file
                ffile = db.format(book_id, fmt, as_file=True)
                ffile.seek(0)
                # Set metadata in the format
                set_metadata(ffile, mi, fmt)
                ffile.seek(0)
                # Now replace the file in the calibre library with the updated
                # file. We dont use add_format_with_hooks as the hooks were
                # already run when the file was first added to calibre.
                db.add_format(book_id, fmt, ffile, run_hooks=False)

        info_dialog(self, 'Updated files',
                'Updated the metadata in the files of %d book(s)'%len(ids),
                show=True)

    def config(self):
        self.do_user_config(parent=self)
        # Apply the changes
        self.label.setText(prefs['hello_world_msg'])

    def about(self):
        # Get the about text from a file inside the plugin zip file
        # The get_resources function is a builtin function defined for all your
        # plugin code. It loads files from the plugin zip file. It returns
        # the bytes from the specified file.

        text = get_resources('about.txt')
        # box = QMessageBox()
        # box.about(self, 'About the Recoll Full Text Search \t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t',text.decode('utf-8'))
        # self.resize(600, self.height())

        self.box = AboutWindow()
        self.box.setWindowTitle("About the Recoll Full Text Search Plugin")
        self.box.textWindow.setText(text)
        self.box.textWindow.setReadOnly(True)
        self.box.resize(600, 500)
        self.box.show()

        
class FileFormatComboBox(QComboBox):

    def __init__(self, parent, file_formats, selected_format):
        QComboBox.__init__(self, parent)
        self.populate_combo(file_formats, selected_format)

    def populate_combo(self, file_formats, selected_format):
        self.clear()
        selected_idx = 0
        for idx, value in enumerate(file_formats):
            if value == selected_format:
                selected_idx = idx
        for key in sorted(file_formats.keys()):
            self.column_names.append(key)
            self.addItem('%s (%s)'%(key, file_formats[key]['name']))
            if key == selected_format:
                selected_idx = len(self.column_names) - 1
        self.setCurrentIndex(selected_idx)

    def get_selected_format(self):
        return self.column_names[self.currentIndex()]

class AboutWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.create_main_frame()

    def create_main_frame(self):
        page = QWidget()

        self.button = QPushButton('OK', page)
        self.textWindow = QTextEdit()

        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.textWindow)
        vbox1.addWidget(self.button)
        page.setLayout(vbox1)
        self.setCentralWidget(page)

        self.button.clicked.connect(self.clicked)

    def clicked(self):
        self.close()


class MyHTML(difflib.HtmlDiff):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # append new styles inside new class
        self._styles = self._styles + """
table.diff {width: 300px}
.diff_sub {display: inline-block; word-break: break-word;}
.diff_add {display: inline-block; word-break: break-word;}
"""

    # function from source code - I remove only `nowrap="nowrap"`
    def _format_line(self, side, flag, linenum, text):
        """Returns HTML markup of "from" / "to" text lines
        side -- 0 or 1 indicating "from" or "to" text
        flag -- indicates if difference on line
        linenum -- line number (used for line number column)
        text -- line text to be marked up
        """
        try:
            linenum = '%d' % linenum
            id = ' id="%s%s"' % (self._prefix[side], linenum)
        except TypeError:
            # handle blank lines where linenum is '>' or ''
            id = ''
        # replace those things that would get confused with HTML symbols
        text = text.replace("&", "&amp;").replace(">", "&gt;").replace("<", "&lt;")

        # make space non-breakable so they don't get compressed or line wrapped
        text = text.replace(' ', '&nbsp;').rstrip()

        return '<td class="diff_header"%s>%s</td><td>%s</td>' \
               % (id, linenum, text)
