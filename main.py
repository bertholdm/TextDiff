# Die aktuelle Logik um das Benutzerinterface für einen Plugin Demo Dialog zu implementieren.

import time, os
from pathlib import Path
import difflib
from PyQt5.Qt import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFont, QGridLayout, QSize,
                      QTextEdit, QComboBox, QCheckBox, QPushButton, QTabWidget, QScrollArea, QMessageBox, QMainWindow)
#                      QWebEngineWidgets)
from calibre.gui2 import gprefs, error_dialog, info_dialog
from calibre.ebooks.conversion.config import (get_input_format_for_book, sort_formats_by_preference)
from calibre.ebooks.oeb.iterator import EbookIterator
from calibre_plugins.textdiff.config import prefs
from calibre.utils.logging import Log as log
from calibre.library import db
from calibre.ptempfile import PersistentTemporaryFile, PersistentTemporaryDirectory


class TextDiffDialog(QDialog):

    def __init__(self, gui, icon, do_user_config):
        QDialog.__init__(self, gui)
        self.gui = gui
        self.do_user_config = do_user_config
        book_ids = []

        # The current database shown in the GUI
        # db is an instance of the class LibraryDatabase from db/legacy.py
        # This class has many, many methods that allow you to do a lot of
        # things. For most purposes you should use db.new_api, which has
        # a much nicer interface from db/cache.py
        self.db = gui.current_db

        self.grid_layout = QGridLayout()

        self.file_1_label = QLabel(_('1st file (left):'))
        self.file_2_label = QLabel(_('2nd file (right):'))
        self.fileinfo_1_label = QLabel(_('(1st file info)'))
        self.fileinfo_2_label = QLabel(_('2nd file info)'))

        self.file_1_combo = QComboBox()
        self.file_1_combo.setObjectName("file_1_combo")
        # self.cb.currentIndexChanged.connect(self.selectionchange)
        self.file_2_combo = QComboBox()
        self.file_2_combo.setObjectName("file_2_combo")
        # self.cb.currentIndexChanged.connect(self.selectionchange)

        self.compare_output_label = QLabel(_('Display format:'))
        self.compare_output_combo = QComboBox()
        self.compare_output_combo.setObjectName("compare_output_combo")
        output_formats = ['HTML', 'Unified']
        self.compare_output_combo.addItems(x for x in output_formats)

        self.cancel_button = QPushButton(_('Cancel'), self)
        self.cancel_button.clicked.connect(self.close_dialog)
        self.compare_button = QPushButton(_('Compare'), self)
        self.compare_button.clicked.connect(self.compare)

        self.result_text = QTextEdit()
        # self.setEditable(False)  # ToDo: richtige Syntax

        self.copy_button = QPushButton(_('Copy to Clipboard'), self)
        self.copy_button.clicked.connect(self.copy)

        # addWidget(*Widget, row, column, rowspan, colspan)
        # row 0
        self.grid_layout.addWidget(self.file_1_label, 0, 0, 1, 1);
        self.grid_layout.addWidget(self.file_2_label, 0, 1, 1, 1);
        # row 1
        self.grid_layout.addWidget(self.fileinfo_1_label, 1, 0, 1, 1)
        self.grid_layout.addWidget(self.fileinfo_2_label, 1, 1, 1, 1)
        # row 2
        self.grid_layout.addWidget(self.file_1_combo, 2, 0, 1, 1)
        self.grid_layout.addWidget(self.file_2_combo, 2, 1, 1, 1)
        # row 3
        self.grid_layout.addWidget(self.compare_output_label, 3, 0, 1, 1)
        self.grid_layout.addWidget(self.compare_output_combo, 3, 1, 1, 1)
        # row 4
        self.grid_layout.addWidget(self.cancel_button, 4, 0, 1, 1)
        self.grid_layout.addWidget(self.compare_button, 4, 1, 1, 1)
        # row 5
        self.grid_layout.addWidget(self.result_text, 5, 0, 1, 2)
        # row 6
        self.grid_layout.addWidget(self.copy_button, 6, 0, 1, 2)

        self.setLayout(self.grid_layout)

        self.setWindowTitle(_('TextDiff Plugin'))
        self.setWindowIcon(icon)

        self.resize(self.sizeHint())

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
            mi1 = db.get_metadata(self.book_ids[0])
            # title, formats = mi.title, mi.formats
            self.fileinfo_1_label.setText(str(self.book_ids[0]) + '=' + mi1.title)
            mi2 = db.get_metadata(self.book_ids[1])
            self.fileinfo_2_label.setText(str(self.book_ids[1]) + '=' + mi2.title)
            #
            # input_format, input_formats = get_input_format_for_book(db, self.book_ids[0])
            self.file_1_combo.addItems(str(x.upper()) for x in mi1.formats)
            # self.file_1_combo.setCurrentIndex(self.file_1_combo.index(input_format))
            # input_format, input_formats = get_input_format_for_book(db, self.book_ids[1])
            self.file_2_combo.addItems(str(x.upper()) for x in mi2.formats)
            # self.file_2_combo.setCurrentIndex(self.file_2_combo.index(input_format))
        else:
            # One book with at least two formats
            mi1 = db.get_metadata(self.book_ids[0])
            self.fileinfo_1_label.setText(str(self.book_ids[0]) + '=' + mi1.title)
            self.fileinfo_2_label.setText(str(self.book_ids[0]) + '=' + mi1.title)
            #
            # input_format, input_formats = get_input_format_for_book(db, self.book_ids[0])
            self.file_1_combo.addItems(str(x.upper()) for x in mi1.formats)
            # self.file_1_combo.setCurrentIndex(self.file_1_combo.index(input_format))
            # input_format, input_formats = get_input_format_for_book(db, self.book_ids[0])
            self.file_2_combo.addItems(str(x.upper()) for x in mi1.formats)
            # self.file_2_combo.setCurrentIndex(self.file_2_combo.index(input_format))


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

    def copy(self):
        pass

    def create_diff(self, first_file: Path, second_file: Path, diff_file: Path = None):

        # https://docs.python.org/3/library/difflib.html

        print('first_file=' + first_file.name)
        print('second_file=' + second_file.name)
        file_1 = open(first_file).readlines()
        file_2 = open(second_file).readlines()

        # ToDo: Options for select Diff Mode (unified_diff, HTMLDiff, ...)
        # If diff_mode == 'HTMLDiff':
        # If diff_mode == 'unified_diff':

        print('Beginning compare...')

        if diff_file:

            delta = difflib.HtmlDiff().make_file(file_1, file_2, first_file.name, second_file.name)

            # ToDo: ggf. make_table verwenden:
            # make_table(fromlines, tolines, fromdesc='', todesc='', context=False, numlines=5)
            # Compares fromlines and tolines (lists of strings) and returns a string which is a complete HTML table showing line by line differences with inter-line and intra-line changes highlighted.
            # The arguments for this method are the same as those for the make_file() method

            # ToDo: Fortschrittsanzeige

            with open(diff_file, "w") as f:
                f.write(delta)
        else:
            delta = difflib.unified_diff(file_1, file_2, first_file.name, second_file.name)
            sys.stdout.writelines(delta)


    def compare(self):
        # This is the main process
        log('Starting compare...')


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

        paths_for_formats = []
        for book_id in book_ids:
            print(book_id)
            mi = db.get_metadata(book_id, index_is_id=True, get_user_categories=False)
            title, formats = mi.title, mi.formats
            fi = 0
            for format in formats:
                print(format)
                if fi == 0 and format == str(self.file_1_combo.currentText()).upper():
                    paths_for_formats.append((book_id, format, db.format_abspath(book_id, format, index_is_id=True)))
                if fi == 1 and format == str(self.file_2_combo.currentText()).upper():
                    paths_for_formats.append((book_id, format, db.format_abspath(book_id, format, index_is_id=True)))
                fi = fi + 1
                print(paths_for_formats)
        print('**********')
        print('paths_for_formats=')
        print(paths_for_formats)
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
        selected_formats.append(str(self.file_1_combo.currentText()).upper())
        selected_formats.append(str(self.file_2_combo.currentText()).upper())
        print('selected_formats=')  # ['EPUB', 'PDF']
        print(selected_formats)  # ['EPUB', 'PDF']

        # Are the formats to be converted

        # Kovid says:
        # If you want to extract text the easiest way to do it is to convert to txt.
        # If you want to do it using calibre APIs then you will need to spend the time
        # to familiarize yourself with them.
        # You basically need to run the input format plugin on the file, then you can use
        # calibre.ebooks.oeb.polish.container.Container object to access the contents of the result
        # of running the input format plugin

        # Test: Use calibre's ebook-convert command line
        # tdir = PersistentTemporaryDirectory(prefix='textdiff_')
        # print(tdir)  # c:\windows\temp\calibre_l31q79f6\textdiff_gmy83dy_

        # book information so far:
        # List of book ids (book_ids): [285, 286]
        # Book #1
        # Book id: 285
        # Selected Format (selected_formats index 0): EPUB
        # Paths (paths_for_formats index 0):
        # [('EPUB', 'E:\\Bibliotheken\\Abenteuer\\Jules Verne\\Meister Antifers wunderbare Abenteu (285)\\Meister Antifers wunderbare Abe - Jules Verne.epub'),
        # ('PDF', 'E:\\Bibliotheken\\Abenteuer\\Jules Verne\\Meister Antifers wunderbare Abenteu (285)\\Meister Antifers wunderbare Abe - Jules Verne.pdf')]
        # Book #2
        # Book id: 286
        # Selected Format (selected_formats index 1): PDF
        # Paths (paths_for_formats index 1):
        # [('PDF', 'E:\\Bibliotheken\\Abenteuer\\Sven Hedin\\Abenteuer in Tibet. 1899 - 1902_ (286)\\Abenteuer in Tibet. 1899 - 1902 - Sven Hedin.pdf')]

        # Filter paths_for_formats list with the formats in the combo box
        # Using the Python filter() function to filter a list of tuples

        # filtered_paths = filter(lambda path: path[1] in selected_formats, paths_for_formats)
        # filtered_paths = list(filtered_paths)
        filtered_paths = paths_for_formats
        print('filtered_paths=')
        print(filtered_paths)

        # There is actually a clever way to do this that is useful for any list of tuples where the size of each tuple is 2:
        # you can convert your list into a single dictionary.
        # paths_for_formats_dict = dict(filtered_paths)
        # print(paths_for_formats_dict)

        text_formats = []
        # convert_options = ' -v -v –enable-heuristics '
        convert_options = ' -v -v '
        for filtered_path in filtered_paths:

            # ToDo: Convert format only when not TXT format

            txt_format_path = filtered_path[2]  # path for converted text format
            txt_format_path = '_'.join(txt_format_path.rsplit('.', 1))
            txt_format_path = txt_format_path + '.txt'  # path for converted text format
            text_formats.append(txt_format_path)
            print('Text path=' + txt_format_path)

            # ToDo: Remove soft hyphens
            # ebook-polish [options] input_file [output_file]
            # --remove-soft-hyphens

            os.system('ebook-convert ' + '"' + filtered_path[2]  + '"' + ' "' +
                      txt_format_path + '"' +
                      convert_options)

            # Erzeugte TXT Datei in Calibre bekanntmachen
            # fpath = Path(' "' + filtered_path[2] + '.txt' + '"')
            # fpath = Path(txt_format_path)
            # fmtf = fpath.name
            # print('fmtf=' + fmtf)
            # if os.path.getsize(fpath) < 1:
            #     raise Exception(_('Empty output file, probably the conversion process crashed'))
            # with open(fpath, 'rb') as data:
            #     db.add_format(filtered_path[0], 'TXT', data, index_is_id=True)  # book_if, format, stream, replace=True, run_hooks=False
            # self.gui.book_converted.emit(book_id, fmt)
            # self.gui.status_bar.show_message(job.description + ' ' + _('Convesion completed'), 2000)

        print('text_formats=')
        print(text_formats)
        first_file = Path(text_formats[0])  # Path('my_shopping_list.txt')
        second_file = Path(text_formats[1])  # Path('friends_shopping_list.txt')
        diff_file = Path(os.path.dirname(os.path.abspath(first_file)) + '\\diff_file.html')  # Path('diff_shopping_list.html')
        print('first_file=' + first_file.name)
        print('second_file=' + second_file.name)
        print('diff_file=' + diff_file.name)

        # ToDo: Fenster in den Vordergrund bringen

        print('Beginning compare...')

        # self.create_diff(first_file, second_file, diff_file)

        # https://docs.python.org/3/library/difflib.html

        file_1 = open(first_file).readlines()
        file_2 = open(second_file).readlines()

        # ToDo: Options for select Diff Mode (unified_diff, HTMLDiff, ...)
        # If diff_mode == 'HTMLDiff':
        # If diff_mode == 'unified_diff':

        if str(self.compare_output_combo.currentText()).upper() == 'HTML':

            d = difflib.HtmlDiff()

            # Overwrite Difflib file template (remove legend)
            d._file_template =  """
            <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
            "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
            <html>
            <head>
                <meta http-equiv="Content-Type"
                      content="text/html; charset=%(charset)s" />
                <title></title>
                <style type="text/css">%(styles)s
                </style>
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

            d._styles = d._styles + """
            table.diff {
                width: 100%;
                table-layout: fixed;
            }
            td {
                width:45%;
            }
            td.diff_next {
                display: none;
            }
            td.diff_header {
                width:5%;
            }
            """

            delta = d.make_file(file_1, file_2, first_file.name, second_file.name)
            # difflöib.HmlDiff.__init__()

            # Erzeugte TXT Datei in Calibre bekanntmachen
            # with open(fpath, 'rb') as data:
            #     db.add_format(diff_file, 'HTML', delta, index_is_id=True)  # book_if, format, stream, replace=True, run_hooks=False

            # d = difflib.HtmlDiff()#wrapcolumn=10)
            # html = d.make_file(lines1, lines2)
            # delta = difflib.HtmlDiff().make_table(file_1, file_2, first_file.name, second_file.name)
            # ToDo: Direkt speichern geht nicht. delta ist bei make_table ein generator!!!!!!!!!!!

            print('delta=' + delta[:800])

            # ToDo: ggf. make_table verwenden:
            # make_table(fromlines, tolines, fromdesc='', todesc='', context=False, numlines=5)
            # Compares fromlines and tolines (lists of strings) and returns a string which is a complete HTML table showing line by line differences with inter-line and intra-line changes highlighted.
            # The arguments for this method are the same as those for the make_file() method

            # ToDo: Fortschrittsanzeige

            # Show Diff in GUI

            with open(diff_file, "w") as f:
                f.write(delta)
                # Show Diff in GUI
                with open(diff_file) as f:
                    self.result_text.setHtml(f.read())

            # self.result_text.setHtml(delta)

            # ToDo: Warum ist das linke Teil-Fenster schmaler? Legende!?

        elif str(self.compare_output_combo.currentText()).upper() == 'UNIFIED':
            delta = difflib.unified_diff(file_1, file_2, first_file.name, second_file.name)
            print('delta=' + delta[:100])
            # Show Diff in GUI
            self.result_text.setHtml(delta)
        else:
            self.result_text.setHtml('Unknown compare outputoption!')

        return

    def make_diff(self, old, new):
        """
        Render in HTML the diff between two texts
        """
        df = HtmlDiff()
        old_lines = old.splitlines(1)
        new_lines = new.splitlines(1)
        html = df.make_table(old_lines, new_lines, context=True)
        html = html.replace(' nowrap="nowrap"', '')
        return html

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