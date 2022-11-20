# The code to manage configuration data in the TextDiff plugin

###############
# Not used yet!
###############

import gettext
from calibre.utils.config import JSONConfig
from PyQt5.Qt import (QMenu, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFont, QGridLayout,
                       QTextEdit, QComboBox, QCheckBox, QPushButton, QToolButton, QTabWidget, QScrollArea)

# Load translations
_ = gettext.gettext
load_translations()

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

    def save_settings(self):
        pass
        # # prefs['hello_world_msg'] = self.msg.text()
        #
        #  # Config Tab
        #  prefs['flattentoc'] = self.config_tab.flattentoc.isChecked()
        #  prefs['includecomments'] = self.config_tab.includecomments.isChecked()
        #  prefs['titlenavpoints'] = self.config_tab.titlenavpoints.isChecked()
        #  prefs['originalnavpoints'] = self.config_tab.originalnavpoints.isChecked()
        #  prefs['keepmeta'] = self.config_tab.keepmeta.isChecked()
        #
        #  # Compare tab
        #  prefs['firstseries'] = self.compare_tab.firstseries.isChecked()
        #  colsmap = {}
        #  for (col,combo) in six.iteritems(self.compare_tab.custcol_dropdowns):
        #      val = unicode(combo.itemData(combo.currentIndex()))
        #      if val != 'none':
        #          colsmap[col] = val
        #          #logger.debug("colsmap[%s]:%s"%(col,colsmap[col]))
        #  prefs['custom_cols'] = colsmap
        #
        #  prefs.save_to_db()

    def edit_shortcuts(self):
        pass
         # self.save_settings()
         # d = KeyboardConfigDialog(self.plugin_action.gui, self.plugin_action.action_spec[0])
         # if d.exec_() == d.Accepted:
         #     self.plugin_action.gui.keyboard.finalize()

    # Das prefs-Objekt ist nun überall im gesamten Erweiterungs-Code verfügbar über ein einfaches:
    # from calibre_plugins.interface_demo.config import prefs

class ConfigTab(QWidget):

    def __init__(self, parent_dialog, plugin_action):
        self.parent_dialog = parent_dialog
        self.plugin_action = plugin_action
        QWidget.__init__(self)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        label = QLabel(_('These settings control the basic features of the plugin. Not used yet!'))
        label.setWordWrap(True)
        self.layout.addWidget(label)
        self.layout.addSpacing(5)
