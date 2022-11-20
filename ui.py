#!/usr/bin/env python

# In dieser definieren Sie wie eine grafische Benutzeroberfläche Ihres Plugin aussehen wird.

import gettext

from PyQt5.Qt import (QMenu, QDialog, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QMessageBox,
                       QTextEdit, QLineEdit, QFont, QComboBox, QCheckBox, QPushButton, QToolButton, QScrollArea)

from calibre.gui2.actions import InterfaceAction
from calibre_plugins.textdiff.main import TextDiffDialog

DEFAULT_ICON = 'images/icon.png'

# Load translations
_ = gettext.gettext
load_translations()

class TextDiffAction(InterfaceAction):

    name = 'TextDiff'

    # Declare the main action associated with this plugin
    # The keyboard shortcut can be None if you dont want to use a keyboard
    # shortcut. Remember that currently calibre has no central management for
    # keyboard shortcuts, so try to use an unusual/unused shortcut.
    # (text, icon_path, tooltip, keyboard shortcut or None)
    # icon_path isn't in the zip--icon loaded below.
    action_spec = (_('TextDiff'), None, _('Run the TextDiff Plugin.'), 'Ctrl+Shift+F12')
    popup_type = QToolButton.InstantPopup  # make button menu drop down only
    action_type = 'current'
    # action_type = 'global'

    # # disable when not in library. (main,carda,cardb)
    # def location_selected(self, loc):
    #     enabled = loc == 'library'
    #     self.qaction.setEnabled(enabled)
    #     self.menuless_qaction.setEnabled(enabled)
    #     for action in self.menu.actions():
    #         action.setEnabled(enabled)

    def genesis(self):

        # This method is called once per plugin, do initial setup here

        # Create our top-level menu/toolbar action (text, icon_path, tooltip, keyboard shortcut)

        # Set the icon for this interface action
        # The get_icons function is a builtin function defined for all your
        # plugin code. It loads icons from the plugin zip file. It returns
        # QIcon objects, if you want the actual data, use the analogous
        # get_resources builtin function.
        icon = get_icons('images/icon.png', 'TextDiff')
        # Note that if you are loading more than one icon, for performance, you
        # should pass a list of names to get_icons. In this case, get_icons
        # will return a dictionary mapping names to QIcons. Names that
        # are not found in the zip file will result in null QIcons.
        # Read the plugin icons and store for potential sharing with the config widget
        # icon_names = ['images/'+i for i in cfg.get_default_icon_names()]
        # icon_resources = self.load_resources(icon_names)
        # set_plugin_icon_resources(self.name, icon_resources)

        # # Assign our menu to this action
        self.menu = QMenu()
        self.load_menu()

        # The qaction is automatically created from the action_spec defined above
        self.qaction.setIcon(icon)
        self.qaction.triggered.connect(self.show_dialog)

    def load_menu(self):
        self.menu.clear()
        self.menu.addAction(_('Compyare...'), self.show_dialog)  # compare
        self.menu.addAction(_('Settings...'), self.show_configuration)
        self.menu.addAction(_('About...'), self.about)
        self.menu.addAction(_('Help...'), self.help)
        self.qaction.setMenu(self.menu)

    def show_dialog(self):
        # The base plugin object defined in __init__.py
        base_plugin_object = self.interface_action_base_plugin
        # Show the config dialog
        # The config dialog can also be shown from within
        # Preferences->Plugins, which is why the do_user_config
        # method is defined on the base plugin class
        do_user_config = base_plugin_object.do_user_config

        # self.gui is the main calibre GUI. It acts as the gateway to access
        # all the elements of the calibre user interface, it should also be the
        # parent of the dialog
        d = TextDiffDialog(self.gui, self.qaction.icon(), do_user_config)
        d.show()

    def apply_settings(self):
        from calibre_plugins.textdiff.config import prefs
        # In an actual non trivial plugin, you would probably need to
        # do something based on the settings in prefs
        prefs

    def close_dialog(self):
        # This is the main process (ToDo: -> main.py)
        pass

    def copy_dialog(self):
        # This is the main process (ToDo: -> main.py)
        pass

    def show_configuration(self):
        # Standard Calibre's method to show configuration window.
        # This method shows a configuration dialog for this plugin.
        # It returns True if the user clicks OK, False otherwise. The changes are automatically applied.
        self.interface_action_base_plugin.do_user_config(self.gui)

    def changeConfig(self):
        # Apply configuration when changed.
        from calibre_plugins.textdiff.gui.config import prefs

    def about(self):
        # "About" window display.

        # Get the about text from a file inside the plugin zip file
        # The get_resources function is a builtin function defined for all your
        # plugin code. It loads files from the plugin zip file. It returns
        # the bytes from the specified file.
        # Note that if you are loading more than one file, for performance, you
        # should pass a list of names to get_resources. In this case,
        # get_resources will return a dictionary mapping names to bytes. Names that
        # are not found in the zip file will not be in the returned dictionary.
        text = get_resources('about.txt')
        QMessageBox.about(self.gui, 'About the TextDiff Plugin', text.decode('utf-8'))

    def help(self):
        pass

    def progressbar(self, window_title, on_top=False):
        self.pb = ProgressBar(parent=self.gui, window_title=window_title, on_top=on_top)
        self.pb.show()

    def show_progressbar(self, maximum_count):
        if self.pb:
            self.pb.set_maximum(maximum_count)
            self.pb.set_value(0)
            self.pb.show()

    def set_progressbar_label(self, label):
        if self.pb:
            self.pb.set_label(label)

    def increment_progressbar(self):
        if self.pb:
            self.pb.increment()

    def hide_progressbar(self):
        if self.pb:
            self.pb.hide()
