#!/usr/bin/env python

# The class that all Interface Action plugin wrappers must inherit

import sys, os
import logging
import gettext

from calibre.constants import DEBUG
from calibre.customize import InterfaceActionBase

__license__   = 'GPL v3'
__copyright__ = '2022, Michael Detambel <info@michael-detambel.de>'
__docformat__ = 'restructuredtext en'

# Load translations
_ = gettext.gettext
load_translations()

# logger = logging.getLogger(__name__)
# loghandler=logging.StreamHandler()
# loghandler.setFormatter(logging.Formatter("textdiff: %(levelname)s: %(asctime)s: %(filename)s(%(lineno)d): %(message)s"))
# logger.addHandler(loghandler)
#
# if os.environ.get('CALIBRE_WORKER', None) is not None or DEBUG:
#     loghandler.setLevel(logging.DEBUG)
#     logger.setLevel(logging.DEBUG)
# else:
#     loghandler.setLevel(logging.CRITICAL)
#     logger.setLevel(logging.CRITICAL)


## Apparently the name for this class doesn't matter.
class TextDiffBase(InterfaceActionBase):
    '''
    This class is a simple wrapper that provides information about the
    actual plugin class. The actual interface plugin class is called
    textdiffPlugin and is defined in the ui.py file, as
    specified in the actual_plugin field below.

    The reason for having two classes is that it allows the command line
    calibre utilities to run without needing to load the GUI libraries.
    '''
    name                    = 'TextDiff'
    description             = _('A Calibre GUI plugin to find text differences in two book formats.')
    supported_platforms     = ['windows', 'osx', 'linux']
    author                  = 'Michael Detambel, <info@michael-detambel.de>'
    version                 = (1, 1, 0)
    # History
    # Version 1.1.0 - 11-25-2022
    # - Invert HTML back-color in dark mode
    # Version 1.0.0 - 11-17-2022
    # - Initial release
    minimum_calibre_version = (5, 0, 0)
    can_be_disabled         = True

    #: This field defines the GUI plugin class that contains all the code
    #: that actually does something. Its format is module_path:class_name
    #: The specified class must be defined in the specified module.
    actual_plugin = 'calibre_plugins.textdiff.ui:TextDiffAction'


    def is_customizable(self):
        '''
        This method must return True to enable customization via
        Preferences->Plugins
        '''
        return True

    def config_widget(self):
        '''
        Implement this method and :meth:`save_settings` in your plugin to
        use a custom configuration dialog.

        This method, if implemented, must return a QWidget. The widget can have
        an optional method validate() that takes no arguments and is called
        immediately after the user clicks OK. Changes are applied if and only
        if the method returns True.

        If for some reason you cannot perform the configuration at this time,
        return a tuple of two strings (message, details), these will be
        displayed as a warning dialog to the user and the process will be
        aborted.

        The base class implementation of this method raises NotImplementedError
        so by default no user configuration is possible.
        '''
        # It is important to put this import statement here rather than at the
        # top of the module as importing the config class will also cause the
        # GUI libraries to be loaded, which we do not want when using calibre
        # from the command line
        from calibre_plugins.textdiff.config import ConfigWidget
        return ConfigWidget(self.actual_plugin_)

    def save_settings(self, config_widget):
        '''
        Save the settings specified by the user with config_widget.

        :param config_widget: The widget returned by :meth:`config_widget`.
        '''
        config_widget.save_settings()

        # Apply the changes
        ac = self.actual_plugin_
        if ac is not None:
            ac.apply_settings()

    # def cli_main(self,argv):
    #     from calibre_plugins.textdiff.textdiff import main as textdiff_main
    #     textdiff_main(argv[1:],usage='%prog --run-plugin '+self.name+' --')
