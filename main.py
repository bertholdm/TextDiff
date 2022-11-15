# Die aktuelle Logik um das Benutzerinterface für einen Plugin Demo Dialog zu implementieren.

import time, os, math
from pathlib import Path
import difflib  # https://github.com/python/cpython/blob/3.11/Lib/difflib.py

from bs4 import BeautifulSoup

from PyQt5.QtCore import Qt
from PyQt5.Qt import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFont, QGridLayout, QSize,
                      QTextEdit, QComboBox, QCheckBox, QPushButton, QTabWidget, QScrollArea, QMessageBox, QMainWindow,
                      QApplication, QClipboard, QTextBlock, QTextBrowser, QIntValidator, QFileDialog)  # QDocument,

from calibre.gui2 import gprefs, error_dialog, info_dialog
from calibre.ebooks.conversion.config import (get_input_format_for_book, sort_formats_by_preference)
from calibre.ebooks.oeb.iterator import EbookIterator
from calibre.utils.logging import Log as log
from calibre.library import db
from calibre.ptempfile import PersistentTemporaryFile, PersistentTemporaryDirectory

from calibre_plugins.textdiff.config import prefs
# from calibre_plugins.textdiff.ui import progressbar, show_progressbar, set_progressbar_label, \
#    increment_progressbar, hide_progressbar


class TextDiffDialog(QDialog):

    def __init__(self, gui, icon, do_user_config):
        QDialog.__init__(self, gui)
        self.gui = gui
        self.do_user_config = do_user_config
        book_ids = []
        diff = ''
        diff_strict = ''
        diff_lines = ['class="diff_add"', 'class="diff_sub"', 'class="diff_chg"']
        diff_classes = ['diff_add', 'diff_sub', 'diff_chg']

        # Overwrite Difflib table and file templates (remove legend and modernize html and css)

        #     <table class="diff" id="difflib_chg_%(prefix)s_top"
        #            cellspacing="0" cellpadding="0" rules="groups" >
        #         <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>
        #         <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>
        #         %(header_row)s
        #         <tbody>%(data_rows)s</tbody>
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
        .diff_next {text-align:center; background-color:#c0c0c0}
        .diff_add {background-color:#aaffaa}
        .diff_chg {background-color:#ffff77}
        .diff_sub {background-color:#ffaaaa}
        """

        self.before_table_template = """
        <!DOCTYPE html>
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=%(charset)s" />
                <title>TextDiff</title>
                <style>""" + self.styles + """</style>
            </head>
            <body>"""

        self.after_table_template = """
            </body>
        </html>"""

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

        self.refresh_formats_button = QPushButton(_('Refresh book formats list'), self)
        self.refresh_formats_button.clicked.connect(self.refresh_formats)

        # linejunk=None, charjunk=IS_CHARACTER_JUNK (difflib.ndiff)

        self.compare_output_label = QLabel(_('Display format:'))
        self.compare_output_label.setAlignment(Qt.AlignRight)
        self.compare_output_combo = QComboBox()
        self.compare_output_combo.setObjectName("compare_output_combo")
        output_formats = ['HTML', 'Context', 'Unified', 'ndiff']
        self.compare_output_combo.addItems(x for x in output_formats)
        self.compare_output_combo.currentTextChanged.connect(self.on_compare_output_combo_changed)
        self.compare_output_combo.setToolTip('See https://docs.python.org/3/library/difflib.html')

        self.fontfamily_label = QLabel(_('Font family for output:'))
        self.fontfamily_label.setAlignment(Qt.AlignRight)
        self.fontfamily_combo = QComboBox()
        self.fontfamily_combo.setObjectName("fontfamily_combo")
        fontfamilies = ['sans-serif', 'serif', 'monospace', 'system-ui', 'ui-serif', 'ui-sans-serif', 'ui-monospace']
        self.fontfamily_combo.addItems(x for x in fontfamilies)

        # The table can be generated in either full or contextual difference mode
        # Only for HtmlDiff! context=True, numlines=10
        self.context = QCheckBox(_('Reduce number of lines around different lines'))
        # # Set context to True when contextual differences are to be shown, else the default is False to show the full files.
        self.context.setEnabled(True)  # HtmlDiff ist selected by default, so enable context flag
        self.context.setChecked(False)
        self.context.stateChanged.connect(self.on_context_ChangedState)
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
        self.numlines.setText('5')   # HtmlDiff ist selected by default, so enable context flag and numlines and set default to 5
        # if initial_value != None:
        #     self.lnumines.setText(str(initial_value))
        self.numlines.setEnabled(True)  # HtmlDiff ist selected by default, so enable context flag and numlines

        self.tabsize_label = QLabel(_('Tabsize (HtmlDiff):'))
        self.tabsize_label.setAlignment(Qt.AlignRight)
        self.tabsize = QLineEdit(self)
        self.tabsize.setFixedWidth(30)
        self.tabsize.setAlignment(Qt.AlignRight)
        self.tabsize.setValidator(QIntValidator())
        self.tabsize.setMaxLength(2)
        self.tabsize.setText('4')
        self.tabsize.setToolTip('Specify tab stop spacing.')

        self.wrapcolumn_label = QLabel(_('Wrap columns at (HtmlDiff):'))
        self.wrapcolumn_label.setAlignment(Qt.AlignRight)
        self.wrapcolumn = QLineEdit(self)
        self.wrapcolumn.setFixedWidth(30)
        self.wrapcolumn.setAlignment(Qt.AlignRight)
        self.wrapcolumn.setValidator(QIntValidator())
        self.wrapcolumn.setMaxLength(2)
        self.wrapcolumn.setText('60')
        self.wrapcolumn.setToolTip('Specify column number where lines are broken and wrapped. 0 for not to break.')

        self.compare_button = QPushButton(_('Compare'), self)
        self.compare_button.clicked.connect(self.compare)

        self.text_browser = QTextBrowser()
        self.text_browser.setAcceptRichText(True)
        self.text_browser.setOpenExternalLinks(False)

        self.ratio_label = QLabel('Ratio is:')
        self.ratio_label.setObjectName('ratio_label')
        self.ratio = QLineEdit(self)
        # self.ratio.setEnabled(False)

        self.copy_diff_file_button = QPushButton(_('Copy output to clipboard.'), self)
        self.copy_diff_file_button.clicked.connect(self.copy_diff_file)
        self.save_diff_file_button = QPushButton(_('Save output to file'), self)
        self.save_diff_file_button.clicked.connect(self.save_diff_file)
        self.add_book_button = QPushButton(_('Save output as book'), self)
        self.add_book_button.clicked.connect(self.add_book)

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

        # Rows 4 to 6 with 4 widgets each wrapped in horizontal box format
        # row 4
        self.option_box1 = QHBoxLayout()
        self.option_box1.addWidget(self.compare_output_label)
        self.option_box1.addWidget(self.compare_output_combo)
        self.option_box1.addWidget(self.fontfamily_label)
        self.option_box1.addWidget(self.fontfamily_combo)
        self.grid_layout.addLayout(self.option_box1, 4, 0, 1, 2)
        # row 5:
        self.option_box2= QHBoxLayout()
        self.option_box2.addWidget(self.context)   # Only for HtmlDiff
        self.option_box2.addWidget(self.numlines_label)
        self.option_box2.addWidget(self.numlines)
        self.grid_layout.addLayout(self.option_box2, 5, 0, 1, 2)
        # row 6
        self.option_box3= QHBoxLayout()
        self.option_box3.addWidget(self.tabsize_label)
        self.option_box3.addWidget(self.tabsize)
        self.option_box3.addWidget(self.wrapcolumn_label)
        self.option_box3.addWidget(self.wrapcolumn)
        self.grid_layout.addLayout(self.option_box3, 6, 0, 1, 2)
        # row 7
        self.grid_layout.addWidget(self.compare_button, 7, 0, 1, 2)
        # row 9
        # row 10
        self.grid_layout.addWidget(self.ratio_label, 10, 0, 1, 1)
        self.grid_layout.addWidget(self.ratio, 10, 1, 1, 1)
        # row 11
        self.grid_layout.addWidget(self.text_browser, 11, 0, 1, 2)
        # row 12
        self.save_layout = QHBoxLayout()
        self.save_layout.addWidget(self.copy_diff_file_button)
        self.save_layout.addWidget(self.save_diff_file_button)
        self.save_layout.addWidget(self.add_book_button)
        self.grid_layout.addLayout(self.save_layout, 12, 0, 1, 2)

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


    # def on_hide_equals_ChangedState(self, checked):
    #     if self.hide_equals.isChecked():
    #         self.text_browser.setHtml(self.diff_strict)
    #     else:
    #         self.text_browser.setHtml(self.diff)


    # Only for HtmlDiff
    def on_context_ChangedState(self, checked):
        if self.context.isChecked():
            self.numlines.setEnabled(True)
        else:
            self.numlines.setEnabled(False)


    def on_compare_output_combo_changed(self, value):
        value = value.upper()
        if value == 'NDIFF':
            self.numlines.setEnabled(False)
        else:
            self.numlines.setEnabled(True)
            self.numlines.setText('3')
        if 'HTMLDIFF' not in value:
            self.fontfamily_combo.setCurrentText('monospace')
            font = QFont()
            font.setFamily('monospace')
            self.text_browser.setFont(font)
            self.context.setChecked(False)
            self.context.setEnabled(False)
        else:
            font = QFont()
            font.setFamily(self.fontfamily_combo.CurrentText())
            self.text_browser.setFont(font)
            self.context.setEnabled(True)
            self.numlines.setText('5')


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

        # Clear output widgets
        self.ratio.setText('')
        self.text_browser.clear()


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


    # ToDo: compare(txt_file_path[0], txt_file_path[1], options). convert separat!
    def compare(self):
        # This is the main process
        log('Starting compare...')
        self.gui.status_bar.showMessage(_('Starting compare...'))

        # ToDo: with busy_cursor():

        # ToDo: Check if formats already converted (if user has only selected another output option)

        # Get the book id(s) of selected book(s)
        db = self.gui.library_view.model().db  # db = self.gui.current_db.new_api
        book_ids = self.gui.library_view.get_selected_ids()  # Get a list of book ids
        print('book_ids: {0}'.format(book_ids))  # [285, 286]
        book_count = len(book_ids)
        if book_count == 0:
            return error_dialog(self.gui, _('No books selected'),
                            _('You must select one book with more than one format or two books to perform this action.'), show=True)
        if book_count > 2:
            return error_dialog(self.gui, _('Too much books selected'),
                                _('You must select one book with more than one format or two books to perform this action.'), show=True)

        available_formats = []
        books_metadata = []
        book_formats_info = []
        # finding the content of current item in combo box and save as input formats
        # (output format is always txt)
        selected_formats = []
        selected_formats.append(str(self.txt_file_content_combo_0.currentText()).upper())
        selected_formats.append(str(self.txt_file_content_combo_1.currentText()).upper())
        print('selected_formats: {0}'.format(selected_formats))  # ['PDF', 'PDF']
        for book_id in book_ids:
            print('Fetching metadata from book_id {0}...'.format(book_id))
            mi = db.get_metadata(book_id, index_is_id=True, get_user_categories=False)
            books_metadata.append(mi)
            available_formats.append({'book_id': book_id, 'formats': mi.formats})
        print('available_formats={0}'.format(available_formats))  # [[book, [fromat, format]], [book, [fromat]]]

        # Fetch title and path info for the selected book formats

        # dataList = [{'a': 1}, {'b': 3}, {'c': 5}]
        for index in range(len(available_formats)):
            print('The values for the keys in index {0} are:'.format(index))
            for key in available_formats[index]:
                print('available_formats[{0}][{1}]={2}'.format(index, key, available_formats[index][key]))

        # for format in available_formats[i][1]:  # Loop thru formats list for this book
        print('selected_formats={0}'.format(selected_formats))
        for i in range(2):  # ToDo: len(selected_formats)?
            print('Fetching info for selected format #{0}'.format(i))
            if selected_formats[i] in available_formats[i]['formats']:
                book_id = available_formats[i]['book_id']
                title = books_metadata[i].title
                format = selected_formats[i]
                book_formats_info.append((book_id, title, format, db.format_abspath(book_id, format, index_is_id=True)))
        print('book_formats_info={0}'.format(book_formats_info))
        # [(285, 'Meister Antifers wunderbare Abenteuer', 'EPUB', 'E:\\Bibliotheken\\Abenteuer\\Jules Verne\\Meister Antifers wunderbare Abenteu (285)\\Meister Antifers wunderbare Abe - Jules Verne.epub'),
        # (285, 'Meister Antifers wunderbare Abenteuer', 'PDF', 'E:\\Bibliotheken\\Abenteuer\\Jules Verne\\Meister Antifers wunderbare Abenteu (285)\\Meister Antifers wunderbare Abe - Jules Verne.pdf')]

        if len(book_formats_info) < 2:
            return error_dialog(self.gui, _('Not enough formats to compare'),
                                _('The selected book(s) must have at least two formats to compare.'),
                                show=True)

        # Start progressbar
        size = 0
        for book_format_info in book_formats_info:
            fmt_metadata = self.db.format_metadata(book_format_info[0], book_format_info[2])
            size = size + fmt_metadata['size']
        print('size={0}'.format(size))
        # self.progressbar(_("Starting compare..."), on_top=True)
        # self.show_progressbar(size)
        # self.set_progressbar_label(_("Compare"))
        # # ToDo: nach unten
        # self.increment_progressbar()

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

        text_lines = []  # List of text lines for each converted format
        for book_format_info in book_formats_info:
            # [(285, 'eister Antifers wunderbare Abenteuer', 'EPUB', 'E:\\Bibliotheken\\Abenteuer\\Jules Verne\\Meister Antifers wunderbare Abenteu (285)\\Meister Antifers wunderbare Abe - Jules Verne.epub'),
            # Convert the input format to text format, even if format is already TXT to apply convert options
            # The function returns a list of strings
            text_lines.append(self.ebook_convert(book_format_info, convert_options))
            print('First 10 text lines: {0}'.format(text_lines[:10]))

        print('Format conversion finished. Beginning compare...')
        self.gui.status_bar.showMessage(_('Format conversion finished. Beginning compare...'))

        diff_options = {}
        diff_options['difftype'] = str(self.compare_output_combo.currentText()).upper()  # HTML, UNIFIED, CONTEXT, NDIFF
        diff_options['context'] = self.context.isChecked()  # True or False. Only for HtmlDiff
        diff_options['numlines'] = int(self.numlines.text())  # default 3
        diff_options['tabsize'] = int(self.tabsize.text())
        diff_options['wrapcolumn'] = int(self.wrapcolumn.text())
        if diff_options['wrapcolumn'] == 0:
            diff_options['wrapcolumn'] = 'None'
        diff_options['font'] = str(self.fontfamily_combo.currentText())
        # ToDo: tabsize=4, wrapcolumn=60
        # HtmlDiff.make_table: context=False, numlines=5
        # context_diff: numlines=3
        # unified_diff: numlines=3
        # ndiff: linejunk=None, charjunk=IS_CHARACTER_JUNK)
        # SequenceMatcher: ratio

        result = self.create_diff(text_lines, book_formats_info, diff_options)
        self.diff = result[0]
        # self.diff_strict = result[1]
        ratio = result[1]
        if ratio is not None:
            self.ratio.setText(str(ratio))

        # Show diff result in GUI

        # ToDo: Check:
        #             if context:
        #                 fromlist = ['<td></td><td>&nbsp;No Differences Found&nbsp;</td>']
        #                 tolist = fromlist
        #             else:
        #                 fromlist = tolist = ['<td></td><td>&nbsp;Empty File&nbsp;</td>']

        # ToDo: self.hide_progressbar()

        self.text_browser.clear()
        if 'HTMLDIFF' not in diff_options['difftype']:
            font = QFont()
            font.setFamily('monospace')
            self.text_browser.setFont(font)
        else:
            font = QFont()
            font.setFamily(self.fontfamily_combo.CurrentText())
            self.text_browser.setFont(font)

        if self.diff is None:
            self.text_browser.setPlainText(
                _('No diff result! Please report this.'))
        elif '<td>&nbsp;No Differences Found&nbsp;</td>' in self.diff or ratio == 1.0:
            self.text_browser.setPlainText(
                _('No differences found in text. However, there may be differences in formatting or MIME content.'))
        elif diff_options['difftype'] == 'HTML':
            # if self.hide_equals.isChecked():
            #     self.text_browser.setHtml(self.diff_strict)
            # else:
            #     self.text_browser.setHtml(self.diff)
            self.text_browser.setHtml(self.diff)
        elif diff_options['difftype'] in ['CONTEXT', 'NDIFF', 'UNIFIED']:
            # context_diff, ndiff and unified_diff returns a gerator, but is already converted to string in make_diff function
            self.text_browser.setPlainText(self.diff)
        else:
            self.text_browser.setPlainText(_('Unknown difftype or result:\\n') + self.diff)


    def remove_soft_hyphens(self, input_file, output_file, options):
        # ToDo: Remove soft hyphens
        # ebook-polish [options] input_file [output_file]
        # --remove-soft-hyphens
        pass


    def ebook_convert(self, book_format_info, convert_options):
        # Convert the input format to text format, even if format is already TXT to apply convert options

        # Kovid says:
        # If you want to extract text the easiest way to do it is to convert to txt.
        # You basically need to run the input format plugin on the file, then you can use
        # calibre.ebooks.oeb.polish.container.Container object to access the contents of the result
        # of running the input format plugin

        print('book_format_info={0}'.format(book_format_info))

        # Generate a path for the text file
        txt_format_path = self.get_txt_format_path(book_format_info)
        print('txt_format_path={0}'.format(txt_format_path))

        # ToDo: Remove soft hyphens in input file?
        # self.remove_soft_hyphens(input_file, output_file, options)

        print('Starting ebook-convert...')
        self.gui.status_bar.showMessage(_('Starting ebook-convert...'))

        # Remove any old file
        if os.path.exists(txt_format_path):
            os.remove(txt_format_path)

        os.system('ebook-convert ' + '"' + book_format_info[3] + '"' + ' "' +
                  txt_format_path + '"' + convert_options)

        # "readlines" returns a list containing the lines.
        # with open(txt_file_path[0]) as f:
        #     txt_file_content[0] = list(line for line in (l.strip() for l in f) if line)
        # with open(txt_file_path[1]) as f:
        #     txt_file_content[1] = list(line for line in (l.strip() for l in f) if line)
        if os.path.exists(txt_format_path):
            print('Reading {0} content in list...'.format(txt_format_path))
            with open(txt_format_path) as f:
                # Read text file line by line and get rid of empty lines
                # If you use the None as a function argument, the filter method will remove any element
                # from the iterable that it considers to be false.
                txt_file_content = list(filter(None, (line.rstrip() for line in f)))
            print('File {0} has {1} lines.'.format(txt_format_path, len(txt_file_content)))
            print('The first 10 items are: {0}'.format(txt_file_content[:10]))
        else:
            return error_dialog(self.gui, _('TextDiff plugin'),
                                _('The file {0} don\'t exist. Probably conversion to text format failed.'.format(txt_format_path)),
                                show=True)

        # Delete the generated text file
        print('Deleting temp file...')
        if os.path.exists(txt_format_path):
            os.remove(txt_format_path)

        return txt_file_content


    def create_diff(self, text_lines, book_formats_info, diff_options):

        print('Enter create_diff...')
        print('diff_options={0}'.format(diff_options))

        diff = None
        # diff_strict = None

        # Calculate ratio
        ratio = None
        # First argument is a function to return 'junk':
        # lambda x: x == ' ' ignores blanks
        ratio = difflib.SequenceMatcher(None, text_lines[0], text_lines[1]).ratio()
        ratio = round(ratio, 4)
        print('ratio={0}'.format(ratio))

        # html_diff and context: numlines=5
        # context_diff: numlines=3
        # unified_diff: numlines=3
        # ndiff: linejunk=None, charjunk=IS_CHARACTER_JUNK)
        # SequenceMatcher: ratio

        txt_format_paths = []
        for book_format_info in book_formats_info:
            txt_format_paths.append(self.get_txt_format_path(book_format_info))

        # https://docs.python.org/3/library/difflib.html
        if diff_options['difftype'] == 'HTML':

            # ToDo: wrapcolumn, linejunk, charjunk as parm
            print('Instantiate HtmlDiff...')
            # This class can be used to create an HTML table (or a complete HTML file containing the table) showing
            # a side by side, line by line comparison of text with inter-line and intra-line change highlights.
            # The table can be generated in either full or contextual difference mode.
            # d = difflib.HtmlDiff(tabsize=4, wrapcolumn=60, linejunk=None, charjunk=TextDiffDialog.IS_CHARACTER_JUNK)
            if diff_options['wrapcolumn'] == 'None':
                d = difflib.HtmlDiff(tabsize=diff_options['tabsize'], wrapcolumn=None,
                                     linejunk=None, charjunk=TextDiffDialog.IS_CHARACTER_JUNK)
            else:
                d = difflib.HtmlDiff(tabsize=diff_options['tabsize'], wrapcolumn=diff_options['wrapcolumn'],
                                     linejunk=None, charjunk=TextDiffDialog.IS_CHARACTER_JUNK)

            # Overwrite Difflib table and file templates (remove legend and modernize html and css)
            d._table_template = self.table_template
            d._file_template = self.file_template
            styles = self.styles
            styles.replace('sans-serif', diff_options['font'])
            d._styles = styles

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

            # context and numlines are both optional keyword arguments. Set context to True when contextual differences
            # are to be shown, else the default is False to show the full files. numlines defaults to 5.
            # When context is True numlines controls the number of context lines which surround the difference
            # highlights. When context is False numlines controls the number of lines which are shown before a
            # difference highlight when using the “next” hyperlinks (setting to zero would cause the “next” hyperlinks
            # to place the next difference highlight at the top of the browser without any leading context).

            print('Calling HtmlDiff.make_table...')

            # make_table(fromlines, tolines, fromdesc='', todesc='', context=False, numlines=5)
            # Compares fromlines and tolines (lists of strings) and returns a string which is a complete HTML table showing line by line differences with inter-line and intra-line changes highlighted.
            # The arguments for this method are the same as those for the make_file() method
            # The table can be generated in either full or contextual difference mode
            # showing line by line differences with inter-line and intra-line changes highlighted.

            book_attributes = []
            for book_format_info in book_formats_info:
                book_attributes.append(str(book_format_info[0]) + '-' + book_format_info[1] + '-' + book_format_info[2])

            # Compares fromlines and tolines (lists of strings) and returns a string which is a complete HTML table
            # showing line by line differences with inter-line and intra-line changes highlighted.
            diff = d.make_table(text_lines[0], text_lines[1], book_attributes[0], book_attributes[1],
                                context=diff_options['context'], numlines=diff_options['numlines'])\
            # nur für make_file: charset='utf-8'

            # Caution: if no differences found, make_file returns a table with an appropriate message text,
            # make_table returns the complete text (with no differences marked of course).

            # To check for differences found, use ratio (1.0 if no differences)
            # and/or a non-empty list of rows with differences (see below)

            print('Diff finished, diff[:1000] + diff[-200:]=' + diff[:1000] + diff[-200:])
            self.gui.status_bar.showMessage(_('Diff finished.'))

            # Wrap html around diff table
            diff_table = diff
            diff = self.before_table_template + diff + self.after_table_template

            # Make a shadow table with differences

            # Row with no differences:
            # <tr>
            # <td class="diff_next"></td>
            # <td class="diff_header" id="from0_5">5</td>
            # <td nowrap="nowrap">„Warum&nbsp;hast&nbsp;du&nbsp;vier&nbsp;Arme&nbsp;und&nbsp;ich&nbsp;nur&nbsp;zwei?“</td>
            # <td class="diff_next"></td>
            # <td class="diff_header" id="to0_21">21</td>
            # <td nowrap="nowrap">„Warum&nbsp;hast&nbsp;du&nbsp;vier&nbsp;Arme&nbsp;und&nbsp;ich&nbsp;nur&nbsp;zwei?“</td>
            # </tr>
            # Row with difference:
            # <tr>
            # <td class="diff_next"></td>
            # <td class="diff_header"></td>
            # <td nowrap="nowrap">&nbsp;</td>
            # <td class="diff_next"></td>
            # <td class="diff_header"></td>
            # <td nowrap="nowrap"><span class="diff_add">en&nbsp;Fähigkeiten&nbsp;unseres&nbsp;Unterbewußtseins&nbsp;die&nbsp;Rede&nbsp;sein.)</span></td>
            # </tr>

            # Here we go: Find all rows without a inner span tag:
            diff_list = []
            table_soup = BeautifulSoup(diff_table, 'lxml')
            # build a list of different rows
            for span in table_soup.find_all('span'):
                tr = span.find_parent('tr')
                diff_list.append(tr)
            if len(diff_list) == 0:
                print(_('diff list is empty - no differences found!'))
                diff = self.before_table_template + \
                              '<tr>><td>' + _('No differences found!') + '</td></tr>' + \
                              self.after_table_template
            # else:
                # print('First 10 entries in diff_list:{0}'.format(diff_list[:10]))
                # print_equals = True
                # row_soup = table_soup.find_all('tr')
                # if row_soup is not None:
                #     for tr in row_soup:
                #         if tr not in diff_list:
                #             if print_equals:
                #                 print('tr not in diff_list: assuming equal lines:{0} '.format(tr))
                #                 print_equals = False
                #             table_soup.extract()
                # print('table_soup[:2000]:{0}'.format(str(table_soup)[:2000]))
                # diff_strict = self.before_table_template + str(table_soup) + self.after_table_template

        elif diff_options['difftype'] == 'CONTEXT':
            # Compare a and b (lists of strings); return a delta (a generator generating the delta lines)
            # in context diff format.
            # Context diffs are a compact way of showing just the lines that have changed plus a few lines
            # of context. The changes are shown in a before/after style. The number of context lines is set
            # by n which defaults to three.
            # difflib.context_diff(a, b, fromfile='', tofile='', fromfiledate='', tofiledate='', n=3, lineterm='\n')
            diff = difflib.context_diff(text_lines[0], text_lines[1],
                                        fromfile=book_formats_info[0][1], tofile=book_formats_info[1][1],
                                        n=diff_options['numlines'], lineterm='\n')
            text = ''
            newline = '\n'
            for line in diff:
                text += line
                # Work around missing newline (http://bugs.python.org/issue2142).
                if text and not line.endswith(newline):
                    text += newline
            diff = text
            print('diff[:1000]={0}'.format(diff[:1000]))

        elif diff_options['difftype'] == 'NDIFF':
            # difflib.ndiff(a, b, linejunk=None, charjunk=IS_CHARACTER_JUNK)
            # Compare a and b (lists of strings); return a Differ-style delta (a generator generating the delta lines).
            diff = difflib.ndiff(text_lines[0], text_lines[1], linejunk=None, charjunk=TextDiffDialog.IS_CHARACTER_JUNK)
            text = ''
            newline = '\n'
            for line in diff:
                text += line
                # Work around missing newline (http://bugs.python.org/issue2142).
                if text and not line.endswith(newline):
                    text += newline
            diff = text
            print('diff[:1000]={0}'.format(diff[:1000]))

        elif diff_options['difftype'] == 'UNIFIED':
            # Compare a and b (lists of strings); return a delta (a generator generating the delta lines) in unified diff format.
            diff = difflib.unified_diff(text_lines[0], text_lines[1], book_formats_info[0][1], book_formats_info[1][1])
            text = ''
            newline = '\n'
            for line in diff:
                text += line
                # Work around missing newline (http://bugs.python.org/issue2142).
                if text and not line.endswith(newline):
                    text += newline
            diff = text
            print('diff[:1000]={0}'.format(diff[:1000]))

        else:
            diff = (_('Unknown compare option!'))

        return diff, ratio


    def get_txt_format_path(self, book_format_info):
        # Generate a path for the text file
        # [(285, 'Meister Antifers wunderbare Abenteuer', 'EPUB', 'E:\\Bibliotheken\\Abenteuer\\Jules Verne\\Meister Antifers wunderbare Abenteu (285)\\Meister Antifers wunderbare Abe - Jules Verne.epub'),
        book_id = book_format_info[0]
        book_title = book_format_info[1]
        book_format = book_format_info[2]
        book_format_path = book_format_info[3]
        txt_format_path = book_format_path  # path for converted text format
        txt_format_path = '_'.join(txt_format_path.rsplit('.', 1))
        txt_format_path = txt_format_path + '_' + str(book_id)  # Qualify text file name with book_id
        txt_format_path = txt_format_path + '.txt'  # path for converted text format
        print('txt_format_path={0}'.format(txt_format_path))
        return txt_format_path


    def copy_diff_file(self):
        # paste entire text in compare result to clipboard
        txt = self.text_browser.selectAll()
        QApplication.clipboard().setText(txt)


    def save_diff_file(self):
        # Schreiben erst wenn "Speichern"-Button gedrückt

        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setViewMode(QFileDialog.Detail)

        file_name = 'diff_file_' + str(self.book_ids[0])  + '_' + str(self.book_ids[1])
        if self.compare_output_combo.currentText() == 'HTML':
            file_name = file_name + '.htnl'
            dialog.setNameFilter(_("HTML file (*.html"))
        else:
            file_name = file_name + '.txt'
            dialog.setNameFilter("Text (*.txt)")

        file_path = dialog.getSaveFileName(None, _('Save File'), file_name)
        file = open(file_path, 'w')
        file.write(self.diff)
        file.close()


    def add_book(self):

        #     db = self.gui.current_db

        # # set default cover to same as first book
        #             coverdata = db.cover(book_list[0]['calibre_id'], index_is_id=True)
        # realmi = db.get_metadata(book_id, index_is_id=True)
        # coverdata = cal_generate_cover(realmi)
        #             if coverdata:
        #                 db.set_cover(book_id, coverdata)
        #
        # def generate_covers(self, book_ids, generate_cover_opts):
        #         from calibre.ebooks.covers import generate_cover
        #         for book_id in book_ids:
        #             mi = self.db.get_metadata(book_id, index_is_id=True)
        #             cdata = generate_cover(mi, generate_cover_opts)
        #             self.db.new_api.set_cover({book_id:cdata})

        # from calibre.ebooks.covers import generate_cover
        # from calibre.utils.img import image_from_data

        #         if mi == None:
        #             mi = self.make_mi_from_book(book)
        #
        #         book_id = book['calibre_id']
        #         if book_id == None:
        #             book_id = db.create_book_entry(mi,
        #                                            add_duplicates=True)
        #             book['calibre_id'] = book_id
        #             book['added'] = True
        #         else:
        #             book['added'] = False

        # db.add_format_with_hooks(book_id,
        #                                         options['fileform'],
        #                                         book['outfile'], index_is_id=True):

        # db.set_metadata(book_id,mi)

        # db.commit()
        pass


    def save_current_file(self):
        # ToDo: Save as html or txt, depending on output format combo
        if not self.file_path:
            new_file_path, filter_type = QFileDialog.getSaveFileName(self, "Save this file as...", "",
                                                                     "All files (*)")
            if new_file_path:
                self.file_path = new_file_path
            else:
                self.invalid_path_alert_message()
                return False
        file_contents = self.scrollable_text_area.toPlainText()
        with open(self.file_path, "w") as f:
            f.write(file_contents)
        self.title.setText(self.file_path)

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
