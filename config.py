#!/usr/bin/env python

# The code to manage configuration data in the demo plugin is in config.py:

from calibre.utils.config import JSONConfig
from PyQt5.Qt import (QMenu, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFont, QGridLayout,
                       QTextEdit, QComboBox, QCheckBox, QPushButton, QToolButton, QTabWidget, QScrollArea)

# This is where all preferences for this plugin will be stored
# Remember that this name (i.e. plugins/interface_demo) is also
# in a global namespace, so make it as unique as possible.
# You should always prefix your config file name with plugins/,
# so as to ensure you dont accidentally clobber a calibre config file
prefs = JSONConfig('plugins/textdiff')

# Set defaults
prefs.defaults['hello_world_msg'] = 'Hello, World!'


class ConfigWidget(QWidget):

    # def __init__(self):
    #     QWidget.__init__(self)
    #     self.layout = QHBoxLayout()
    #     self.setLayout(self.layout)
    #
    #     self.layoutabel = QLabel('Hello world &message:')
    #     self.layout.addWidget(self.layoutabel)
    #
    #     self.msg = QLineEdit(self)
    #     self.msg.setText(prefs['hello_world_msg'])
    #     self.layout.addWidget(self.msg)
    #     self.layoutabel.setBuddy(self.msg)

    def __init__(self, plugin_action):
         QWidget.__init__(self)
         self.plugin_action = plugin_action

         self.layout = QVBoxLayout()
         self.setLayout(self.layout)

         tab_widget = QTabWidget(self)
         self.layout.addWidget(tab_widget)

         self.config_tab = ConfigTab(self, plugin_action)
         tab_widget.addTab(self.config_tab, _('Config'))

         self.compare_tab = CompareTab(self, plugin_action)
         tab_widget.addTab(self.compare_tab, _('Compare'))

    def save_settings(self):
        # prefs['hello_world_msg'] = self.msg.text()

         # Config Tab
         prefs['flattentoc'] = self.config_tab.flattentoc.isChecked()
         prefs['includecomments'] = self.config_tab.includecomments.isChecked()
         prefs['titlenavpoints'] = self.config_tab.titlenavpoints.isChecked()
         prefs['originalnavpoints'] = self.config_tab.originalnavpoints.isChecked()
         prefs['keepmeta'] = self.config_tab.keepmeta.isChecked()

         # Compare tab
         prefs['firstseries'] = self.compare_tab.firstseries.isChecked()
         colsmap = {}
         for (col,combo) in six.iteritems(self.compare_tab.custcol_dropdowns):
             val = unicode(combo.itemData(combo.currentIndex()))
             if val != 'none':
                 colsmap[col] = val
                 #logger.debug("colsmap[%s]:%s"%(col,colsmap[col]))
         prefs['custom_cols'] = colsmap

         prefs.save_to_db()

    def edit_shortcuts(self):
         self.save_settings()
         d = KeyboardConfigDialog(self.plugin_action.gui, self.plugin_action.action_spec[0])
         if d.exec_() == d.Accepted:
             self.plugin_action.gui.keyboard.finalize()

    # Das prefs-Objekt ist nun überall im gesamten Erweiterungs-Code verfügbar über ein einfaches:
    # from calibre_plugins.interface_demo.config import prefs

class ConfigTab(QWidget):

    def __init__(self, parent_dialog, plugin_action):
        self.parent_dialog = parent_dialog
        self.plugin_action = plugin_action
        QWidget.__init__(self)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        label = QLabel(_('These settings control the basic features of the plugin.'))
        label.setWordWrap(True)
        self.layout.addWidget(label)
        self.layout.addSpacing(5)
#
#         no_toc_warning = _('''If both 'Insert Table of Contents entry' and 'Copy Table of Contents entries'
# are unchecked, there will be no Table of Contents in merged books.''')
#         self.titlenavpoints = QCheckBox(_('Insert Table of Contents entry for each title?'),self)
#         self.titlenavpoints.setToolTip(_('''If set, a new TOC entry will be made for each title and
# it's existing TOC nested underneath it.''')+'\n'+no_toc_warning)
#         self.titlenavpoints.setChecked(prefs['titlenavpoints'])
#         self.layout.addWidget(self.titlenavpoints)
#
#         self.originalnavpoints = QCheckBox(_('Copy Table of Contents entries from each title?'),self)
#         self.originalnavpoints.setToolTip(_('''If set, the original TOC entries will be included the new epub.''')+'\n'+no_toc_warning)
#         self.originalnavpoints.setChecked(prefs['originalnavpoints'])
#         self.layout.addWidget(self.originalnavpoints)
#
#         def f():
#             if not self.originalnavpoints.isChecked() and not self.titlenavpoints.isChecked():
#                 confirm("<br>"+no_toc_warning, # force HTML to get auto wrap.
#                         'textdiff_no_toc_warning_again',
#                         parent=self,
#                         show_cancel_button=False)
#         self.originalnavpoints.stateChanged.connect(f)
#         self.titlenavpoints.stateChanged.connect(f)
#
#         self.flattentoc = QCheckBox(_('Flatten Table of Contents?'),self)
#         self.flattentoc.setToolTip(_('Remove nesting and make TOC all on one level.'))
#         self.flattentoc.setChecked(prefs['flattentoc'])
#         self.layout.addWidget(self.flattentoc)
#
#         self.includecomments = QCheckBox(_("Include Books' Comments?"),self)
#         self.includecomments.setToolTip(_('''Include all the merged books' comments in the new book's comments.
# Default is a list of included titles only.'''))
#         self.includecomments.setChecked(prefs['includecomments'])
#         self.layout.addWidget(self.includecomments)
#
#         self.keepmeta = QCheckBox(_('Keep UnMerge Metadata?'),self)
#         self.keepmeta.setToolTip(_('''If set, a copy of the original metadata for each merged book will
# be included, allowing for UnMerge.  This includes your calibre custom
# columns.  Leave off if you plan to distribute the epub to others.'''))
#         self.keepmeta.setChecked(prefs['keepmeta'])
#         self.layout.addWidget(self.keepmeta)
#
# #         self.showunmerge = QCheckBox(_('Show UnMerge Option?'),self)
# #         self.showunmerge.setToolTip(_('''If set, the UnMerge Epub option will be shown on the textdiff menu.
# # Only Epubs merged with 'Keep UnMerge Metadata' can be UnMerged.'''))
# #         self.showunmerge.setChecked(prefs['showunmerge'])
# #         self.layout.addWidget(self.showunmerge)
#
#         horz = QHBoxLayout()
#         horz.addWidget(QLabel(_("Add tags to merged books:")))
#
#         self.mergetags = QLineEdit(self)
#         self.mergetags.setText(prefs['mergetags'])
#         self.mergetags.setToolTip(_('Tags you enter here will be added to all new merged books'))
#         horz.addWidget(self.mergetags)
#         self.layout.addLayout(horz)
#
#         horz = QHBoxLayout()
#         horz.addWidget(QLabel(_("Merged Book Word:")))
#
#         self.mergeword = QLineEdit(self)
#         self.mergeword.setText(prefs['mergeword'])
#         self.mergeword.setToolTip(_('''Word use to describe merged books in default title and summary.
# For people who don't like the word Anthology.'''))
# ## Defaults back to Anthology if cleared.
#
#         horz.addWidget(self.mergeword)
#         self.layout.addLayout(horz)
#
#         self.layout.addSpacing(15)
#
#         label = QLabel(_("These controls aren't plugin settings as such, but convenience buttons for setting Keyboard shortcuts and getting all the textdiff confirmation dialogs back again."))
#         label.setWordWrap(True)
#         self.layout.addWidget(label)
#         self.layout.addSpacing(5)
#
#         keyboard_shortcuts_button = QPushButton(_('Keyboard shortcuts...'), self)
#         keyboard_shortcuts_button.setToolTip(_('Edit the keyboard shortcuts associated with this plugin'))
#         keyboard_shortcuts_button.clicked.connect(parent_dialog.edit_shortcuts)
#         self.layout.addWidget(keyboard_shortcuts_button)
#
#         reset_confirmation_button = QPushButton(_('Reset disabled &confirmation dialogs'), self)
#         reset_confirmation_button.setToolTip(_('Reset all show me again dialogs for the textdiff plugin'))
#         reset_confirmation_button.clicked.connect(self.reset_dialogs)
#         self.layout.addWidget(reset_confirmation_button)
#
#         view_prefs_button = QPushButton(_('View library preferences...'), self)
#         view_prefs_button.setToolTip(_('View data stored in the library database for this plugin'))
#         view_prefs_button.clicked.connect(self.view_prefs)
#         self.layout.addWidget(view_prefs_button)
#
#         self.layout.insertStretch(-1)
#
#     def view_prefs(self):
#         d = PrefsViewerDialog(self.plugin_action.gui, PREFS_NAMESPACE)
#         d.exec_()
#
#     def reset_dialogs(self):
#         for key in dynamic.keys():
#             if key.startswith('textdiff_') and key.endswith('_again') \
#                                                   and dynamic[key] is False:
#                 dynamic[key] = True
#         info_dialog(self, _('Done'),
#                     _('Confirmation dialogs have all been reset'),
#                     show=True,
#                     show_copy_button=False)
#
# permitted_values = {
#     'int' : ['add', 'averageall', 'average', 'first', 'last'],
#     'float' : ['add', 'averageall', 'average', 'first', 'last'],
#     'bool' : ['and', 'or', 'first', 'last'],
#     'datetime' : ['newest', 'oldest', 'first', 'last', 'now'],
#     'enumeration' : ['first', 'last'],
#     'series' : ['first', 'last'],
#     'text' : ['union', 'concat', 'first', 'last'],
#     'comments' : ['concat', 'first', 'last']
#     }
#
# titleLabels = {
#     'first':_('Take value from first source book'),
#     'last':_('Take value from last source book'),
#     'add':_('Add values from all source books'),
#     'averageall':_('Average value from ALL source books'),
#     'average':_('Average value from source books with values'),
#     'and':_('True if true on all source books (and)'),
#     'or':_('True if true on any source books (or)'),
#     'newest':_('Take newest value from source books'),
#     'oldest':_('Take oldest value from source books'),
#     'union':_('Include values from all source books'),
#     'concat':_('Concatenate values from all source books'),
#     'now':_('Set to current time when created'),
#     }
#
# class CompareTab(QWidget):
#
#     def __init__(self, parent_dialog, plugin_action):
#         self.parent_dialog = parent_dialog
#         self.plugin_action = plugin_action
#         QWidget.__init__(self)
#
#         self.layout = QVBoxLayout()
#         self.setLayout(self.layout)
#
#         label = QLabel('<b>'+_('Standard Columns:')+'</b>')
#         label.setWordWrap(True)
#         self.layout.addWidget(label)
#         self.layout.addSpacing(5)
#
#         self.firstseries = QCheckBox(_('Take Series from first book'),self)
#         self.firstseries.setToolTip(_('''If set, the Series name and index from the first book will be set on the merged book.'''))
#         self.firstseries.setChecked(prefs['firstseries'])
#         self.layout.addWidget(self.firstseries)
#         self.layout.addSpacing(5)
#
#         label = QLabel('<b>'+_('Custom Columns:')+'</b>')
#         label.setWordWrap(True)
#         self.layout.addWidget(label)
#         label = QLabel(_("If you have custom columns defined, they will be listed below.  Choose how you would like these columns handled."))
#         label.setWordWrap(True)
#         self.layout.addWidget(label)
#         self.layout.addSpacing(5)
#
#         scrollable = QScrollArea()
#         scrollcontent = QWidget()
#         scrollable.setWidget(scrollcontent)
#         scrollable.setWidgetResizable(True)
#         self.layout.addWidget(scrollable)
#
#         self.sl = QVBoxLayout()
#         scrollcontent.setLayout(self.sl)
#
#         self.custcol_dropdowns = {}
#
#         custom_columns = self.plugin_action.gui.library_view.model().custom_columns
#
#         grid = QGridLayout()
#         self.sl.addLayout(grid)
#         row=0
#         ## sort by visible Column Name (vs #name)
#         for key, column in sorted(custom_columns.items(), key=lambda x: x[1]['name']):
#             if column['datatype'] in permitted_values:
#                 # logger.debug("\n============== %s ===========\n"%key)
#                 label = QLabel('%s(%s)'%(column['name'],key))
#                 label.setToolTip(_("Set this %s column on new merged books...")%column['datatype'])
#                 grid.addWidget(label,row,0)
#
#                 dropdown = QComboBox(self)
#                 dropdown.addItem('','none')
#                 for md in permitted_values[column['datatype']]:
#                     # tags-like column also 'text'
#                     if md == 'union' and not column['is_multiple']:
#                         continue
#                     if md == 'concat' and column['is_multiple']:
#                         continue
#                     dropdown.addItem(titleLabels[md],md)
#                 self.custcol_dropdowns[key] = dropdown
#                 if key in prefs['custom_cols']:
#                     dropdown.setCurrentIndex(dropdown.findData(prefs['custom_cols'][key]))
#                 dropdown.setToolTip(_("How this column will be populated by default."))
#                 grid.addWidget(dropdown,row,1)
#                 row+=1
#
#         self.sl.insertStretch(-1)
#
#         #logger.debug("prefs['custom_cols'] %s"%prefs['custom_cols'])


# import logging
# logger = logging.getLogger(__name__)
#
# import traceback, copy
# from PyQt5.Qt import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFont, QGridLayout,
#                       QTextEdit, QComboBox, QCheckBox, QPushButton, QTabWidget, QScrollArea)
# from calibre.gui2 import dynamic, info_dialog
# from calibre.gui2.dialogs.confirm_delete import confirm
# from calibre.utils.config import JSONConfig
# from calibre.gui2.ui import get_gui
#
# from calibre_plugins.textdiff.common_utils \
#     import ( get_library_uuid, KeyboardConfigDialog, PrefsViewerDialog )
#
# __license__   = 'GPL v3'
# __copyright__ = '2022, feuille'
# __docformat__ = 'restructuredtext en'
#
# # pulls in translation files for _() strings
# # load_translations()
#
# PREFS_NAMESPACE = 'textdiffPlugin'
# PREFS_KEY_SETTINGS = 'settings'
#
# # Set defaults used by all.  Library specific settings continue to
# # take from here.
# default_prefs = {}
# default_prefs['flattentoc'] = False
# default_prefs['includecomments'] = False
# default_prefs['titlenavpoints'] = True
# default_prefs['originalnavpoints'] = True
# default_prefs['keepmeta'] = True
# #default_prefs['showunmerge'] = True
# default_prefs['mergetags'] = ''
# default_prefs['mergeword'] = _('Anthology')
# default_prefs['firstseries'] = False
# default_prefs['custom_cols'] = {}
#
#
# def set_library_config(library_config):
#     get_gui().current_db.prefs.set_namespaced(PREFS_NAMESPACE,
#                                               PREFS_KEY_SETTINGS,
#                                               library_config)
#
#
# def get_library_config():
#     db = get_gui().current_db
#     library_id = get_library_uuid(db)
#     library_config = None
#     # Check whether this is a configuration needing to be migrated
#     # from json into database.  If so: get it, set it, wipe it from json.
#     if library_id in old_prefs:
#         # logger.debug("get prefs from old_prefs")
#         library_config = old_prefs[library_id]
#         set_library_config(library_config)
#         del old_prefs[library_id]
#
#     if library_config is None:
#         # logger.debug("get prefs from db")
#         library_config = db.prefs.get_namespaced(PREFS_NAMESPACE, PREFS_KEY_SETTINGS,
#                                                  copy.deepcopy(default_prefs))
#     return library_config
#
# # This is where all preferences for this plugin *were* stored
# # Remember that this name (i.e. plugins/textdiff) is also
# # in a global namespace, so make it as unique as possible.
# # You should always prefix your config file name with plugins/,
# # so as to ensure you dont accidentally clobber a calibre config file
# old_prefs = JSONConfig('plugins/textdiff')
#
# # fake out so I don't have to change the prefs calls anywhere.  The
# # Java programmer in me is offended by op-overloading, but it's very
# # tidy.
# class PrefsFacade():
#     def __init__(self,default_prefs):
#         self.default_prefs = default_prefs
#         self.layoutibraryid = None
#         self.current_prefs = None
#
#     def _get_prefs(self):
#         libraryid = get_library_uuid(get_gui().current_db)
#         if self.current_prefs == None or self.layoutibraryid != libraryid:
#             #logger.debug("self.current_prefs == None(%s) or self.layoutibraryid != libraryid(%s)"%(self.current_prefs == None,self.layoutibraryid != libraryid))
#             self.layoutibraryid = libraryid
#             self.current_prefs = get_library_config()
#         return self.current_prefs
#
#     def __getitem__(self,k):
#         prefs = self._get_prefs()
#         if k not in prefs:
#             # some users have old JSON, but have never saved all the
#             # options.
#             if k in self.default_prefs:
#                 return self.default_prefs[k]
#             else:
#                 return default_prefs[k]
#         return prefs[k]
#
#     def __setitem__(self,k,v):
#         prefs = self._get_prefs()
#         prefs[k]=v
#         # self._save_prefs(prefs)
#
#     def __delitem__(self,k):
#         prefs = self._get_prefs()
#         if k in prefs:
#             del prefs[k]
#
#     def save_to_db(self):
#         set_library_config(self._get_prefs())
#
# prefs = PrefsFacade(old_prefs)
#
# class ConfigWidget(QWidget):
#
#     def __init__(self, plugin_action):
#         QWidget.__init__(self)
#         self.plugin_action = plugin_action
#
#         self.layout = QVBoxLayout()
#         self.setLayout(self.layout)
#
#         tab_widget = QTabWidget(self)
#         self.layout.addWidget(tab_widget)
#
#         self.config_tab = ConfigTab(self, plugin_action)
#         tab_widget.addTab(self.config_tab, _('Basic'))
#
#         self.compare_tab = CompareTab(self, plugin_action)
#         tab_widget.addTab(self.compare_tab, _('Textdiff'))
#
#     def save_settings(self):
#         # basic
#         prefs['flattentoc'] = self.config_tab.flattentoc.isChecked()
#         prefs['includecomments'] = self.config_tab.includecomments.isChecked()
#         prefs['titlenavpoints'] = self.config_tab.titlenavpoints.isChecked()
#         prefs['originalnavpoints'] = self.config_tab.originalnavpoints.isChecked()
#         prefs['keepmeta'] = self.config_tab.keepmeta.isChecked()
#
#         # Columns tab
#         prefs['firstseries'] = self.compare_tab.firstseries.isChecked()
#         colsmap = {}
#         for (col,combo) in six.iteritems(self.compare_tab.custcol_dropdowns):
#             val = unicode(combo.itemData(combo.currentIndex()))
#             if val != 'none':
#                 colsmap[col] = val
#                 #logger.debug("colsmap[%s]:%s"%(col,colsmap[col]))
#         prefs['custom_cols'] = colsmap
#
#         prefs.save_to_db()
#
#     def edit_shortcuts(self):
#         self.save_settings()
#         d = KeyboardConfigDialog(self.plugin_action.gui, self.plugin_action.action_spec[0])
#         if d.exec_() == d.Accepted:
#             self.plugin_action.gui.keyboard.finalize()
#
# class ConfigTab(QWidget):
#
#     def __init__(self, parent_dialog, plugin_action):
#         self.parent_dialog = parent_dialog
#         self.plugin_action = plugin_action
#         QWidget.__init__(self)
#
#         self.layout = QVBoxLayout()
#         self.setLayout(self.layout)
#
#         label = QLabel(_('These settings control the basic features of the plugin.'))
#         label.setWordWrap(True)
#         self.layout.addWidget(label)
#         self.layout.addSpacing(5)
#
#         no_toc_warning = _('''If both 'Insert Table of Contents entry' and 'Copy Table of Contents entries'
# are unchecked, there will be no Table of Contents in merged books.''')
#         self.titlenavpoints = QCheckBox(_('Insert Table of Contents entry for each title?'),self)
#         self.titlenavpoints.setToolTip(_('''If set, a new TOC entry will be made for each title and
# it's existing TOC nested underneath it.''')+'\n'+no_toc_warning)
#         self.titlenavpoints.setChecked(prefs['titlenavpoints'])
#         self.layout.addWidget(self.titlenavpoints)
#
#         self.originalnavpoints = QCheckBox(_('Copy Table of Contents entries from each title?'),self)
#         self.originalnavpoints.setToolTip(_('''If set, the original TOC entries will be included the new epub.''')+'\n'+no_toc_warning)
#         self.originalnavpoints.setChecked(prefs['originalnavpoints'])
#         self.layout.addWidget(self.originalnavpoints)
#
#         def f():
#             if not self.originalnavpoints.isChecked() and not self.titlenavpoints.isChecked():
#                 confirm("<br>"+no_toc_warning, # force HTML to get auto wrap.
#                         'textdiff_no_toc_warning_again',
#                         parent=self,
#                         show_cancel_button=False)
#         self.originalnavpoints.stateChanged.connect(f)
#         self.titlenavpoints.stateChanged.connect(f)
#
#         self.flattentoc = QCheckBox(_('Flatten Table of Contents?'),self)
#         self.flattentoc.setToolTip(_('Remove nesting and make TOC all on one level.'))
#         self.flattentoc.setChecked(prefs['flattentoc'])
#         self.layout.addWidget(self.flattentoc)
#
#         self.includecomments = QCheckBox(_("Include Books' Comments?"),self)
#         self.includecomments.setToolTip(_('''Include all the merged books' comments in the new book's comments.
# Default is a list of included titles only.'''))
#         self.includecomments.setChecked(prefs['includecomments'])
#         self.layout.addWidget(self.includecomments)
#
#         self.keepmeta = QCheckBox(_('Keep UnMerge Metadata?'),self)
#         self.keepmeta.setToolTip(_('''If set, a copy of the original metadata for each merged book will
# be included, allowing for UnMerge.  This includes your calibre custom
# columns.  Leave off if you plan to distribute the epub to others.'''))
#         self.keepmeta.setChecked(prefs['keepmeta'])
#         self.layout.addWidget(self.keepmeta)
#
# #         self.showunmerge = QCheckBox(_('Show UnMerge Option?'),self)
# #         self.showunmerge.setToolTip(_('''If set, the UnMerge Epub option will be shown on the textdiff menu.
# # Only Epubs merged with 'Keep UnMerge Metadata' can be UnMerged.'''))
# #         self.showunmerge.setChecked(prefs['showunmerge'])
# #         self.layout.addWidget(self.showunmerge)
#
#         horz = QHBoxLayout()
#         horz.addWidget(QLabel(_("Add tags to merged books:")))
#
#         self.mergetags = QLineEdit(self)
#         self.mergetags.setText(prefs['mergetags'])
#         self.mergetags.setToolTip(_('Tags you enter here will be added to all new merged books'))
#         horz.addWidget(self.mergetags)
#         self.layout.addLayout(horz)
#
#         horz = QHBoxLayout()
#         horz.addWidget(QLabel(_("Merged Book Word:")))
#
#         self.mergeword = QLineEdit(self)
#         self.mergeword.setText(prefs['mergeword'])
#         self.mergeword.setToolTip(_('''Word use to describe merged books in default title and summary.
# For people who don't like the word Anthology.'''))
# ## Defaults back to Anthology if cleared.
#
#         horz.addWidget(self.mergeword)
#         self.layout.addLayout(horz)
#
#         self.layout.addSpacing(15)
#
#         label = QLabel(_("These controls aren't plugin settings as such, but convenience buttons for setting Keyboard shortcuts and getting all the textdiff confirmation dialogs back again."))
#         label.setWordWrap(True)
#         self.layout.addWidget(label)
#         self.layout.addSpacing(5)
#
#         keyboard_shortcuts_button = QPushButton(_('Keyboard shortcuts...'), self)
#         keyboard_shortcuts_button.setToolTip(_('Edit the keyboard shortcuts associated with this plugin'))
#         keyboard_shortcuts_button.clicked.connect(parent_dialog.edit_shortcuts)
#         self.layout.addWidget(keyboard_shortcuts_button)
#
#         reset_confirmation_button = QPushButton(_('Reset disabled &confirmation dialogs'), self)
#         reset_confirmation_button.setToolTip(_('Reset all show me again dialogs for the textdiff plugin'))
#         reset_confirmation_button.clicked.connect(self.reset_dialogs)
#         self.layout.addWidget(reset_confirmation_button)
#
#         view_prefs_button = QPushButton(_('View library preferences...'), self)
#         view_prefs_button.setToolTip(_('View data stored in the library database for this plugin'))
#         view_prefs_button.clicked.connect(self.view_prefs)
#         self.layout.addWidget(view_prefs_button)
#
#         self.layout.insertStretch(-1)
#
#     def view_prefs(self):
#         d = PrefsViewerDialog(self.plugin_action.gui, PREFS_NAMESPACE)
#         d.exec_()
#
#     def reset_dialogs(self):
#         for key in dynamic.keys():
#             if key.startswith('textdiff_') and key.endswith('_again') \
#                                                   and dynamic[key] is False:
#                 dynamic[key] = True
#         info_dialog(self, _('Done'),
#                     _('Confirmation dialogs have all been reset'),
#                     show=True,
#                     show_copy_button=False)
#
# permitted_values = {
#     'int' : ['add', 'averageall', 'average', 'first', 'last'],
#     'float' : ['add', 'averageall', 'average', 'first', 'last'],
#     'bool' : ['and', 'or', 'first', 'last'],
#     'datetime' : ['newest', 'oldest', 'first', 'last', 'now'],
#     'enumeration' : ['first', 'last'],
#     'series' : ['first', 'last'],
#     'text' : ['union', 'concat', 'first', 'last'],
#     'comments' : ['concat', 'first', 'last']
#     }
#
# titleLabels = {
#     'first':_('Take value from first source book'),
#     'last':_('Take value from last source book'),
#     'add':_('Add values from all source books'),
#     'averageall':_('Average value from ALL source books'),
#     'average':_('Average value from source books with values'),
#     'and':_('True if true on all source books (and)'),
#     'or':_('True if true on any source books (or)'),
#     'newest':_('Take newest value from source books'),
#     'oldest':_('Take oldest value from source books'),
#     'union':_('Include values from all source books'),
#     'concat':_('Concatenate values from all source books'),
#     'now':_('Set to current time when created'),
#     }
#
# class CompareTab(QWidget):
#
#     def __init__(self, parent_dialog, plugin_action):
#         self.parent_dialog = parent_dialog
#         self.plugin_action = plugin_action
#         QWidget.__init__(self)
#
#         self.layout = QVBoxLayout()
#         self.setLayout(self.layout)
#
#         label = QLabel('<b>'+_('Standard Columns:')+'</b>')
#         label.setWordWrap(True)
#         self.layout.addWidget(label)
#         self.layout.addSpacing(5)
#
#         self.firstseries = QCheckBox(_('Take Series from first book'),self)
#         self.firstseries.setToolTip(_('''If set, the Series name and index from the first book will be set on the merged book.'''))
#         self.firstseries.setChecked(prefs['firstseries'])
#         self.layout.addWidget(self.firstseries)
#         self.layout.addSpacing(5)
#
#         label = QLabel('<b>'+_('Custom Columns:')+'</b>')
#         label.setWordWrap(True)
#         self.layout.addWidget(label)
#         label = QLabel(_("If you have custom columns defined, they will be listed below.  Choose how you would like these columns handled."))
#         label.setWordWrap(True)
#         self.layout.addWidget(label)
#         self.layout.addSpacing(5)
#
#         scrollable = QScrollArea()
#         scrollcontent = QWidget()
#         scrollable.setWidget(scrollcontent)
#         scrollable.setWidgetResizable(True)
#         self.layout.addWidget(scrollable)
#
#         self.sl = QVBoxLayout()
#         scrollcontent.setLayout(self.sl)
#
#         self.custcol_dropdowns = {}
#
#         custom_columns = self.plugin_action.gui.library_view.model().custom_columns
#
#         grid = QGridLayout()
#         self.sl.addLayout(grid)
#         row=0
#         ## sort by visible Column Name (vs #name)
#         for key, column in sorted(custom_columns.items(), key=lambda x: x[1]['name']):
#             if column['datatype'] in permitted_values:
#                 # logger.debug("\n============== %s ===========\n"%key)
#                 label = QLabel('%s(%s)'%(column['name'],key))
#                 label.setToolTip(_("Set this %s column on new merged books...")%column['datatype'])
#                 grid.addWidget(label,row,0)
#
#                 dropdown = QComboBox(self)
#                 dropdown.addItem('','none')
#                 for md in permitted_values[column['datatype']]:
#                     # tags-like column also 'text'
#                     if md == 'union' and not column['is_multiple']:
#                         continue
#                     if md == 'concat' and column['is_multiple']:
#                         continue
#                     dropdown.addItem(titleLabels[md],md)
#                 self.custcol_dropdowns[key] = dropdown
#                 if key in prefs['custom_cols']:
#                     dropdown.setCurrentIndex(dropdown.findData(prefs['custom_cols'][key]))
#                 dropdown.setToolTip(_("How this column will be populated by default."))
#                 grid.addWidget(dropdown,row,1)
#                 row+=1
#
#         self.sl.insertStretch(-1)
#
#         #logger.debug("prefs['custom_cols'] %s"%prefs['custom_cols'])
