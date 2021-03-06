#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Main program module
"""

import sys
import traceback

import wx


def main():
    """
    main() - start application
    """
    # Init wx app
    app = wx.App()

    # Set default exception handler
    sys.excepthook = _excepthook

    # Init locales
    from igcweight.settings import LOCALE_DIR
    mylocale = wx.Locale(wx.LANGUAGE_DEFAULT)
    mylocale.AddCatalogLookupPathPrefix(LOCALE_DIR)
    mylocale.AddCatalog('wxstd')  # MS Windows hack
    mylocale.AddCatalog('igcweight')

    # Init main window and application
    from igcweight.gui_main import Main
    main = Main(None, -1, "")
    app.SetAppName(main.GetTitle())
    app.SetTopWindow(main)
    main.Show()

    app.MainLoop()


def _excepthook(etype, value, tb):
    """
    Process unhandled exception
    """
    try:
        from wx import GetTranslation as _
    except ImportError:
        def _(s):
            return s
    try:
        from igcweight.settings import DEBUG
    except ImportError:
        DEBUG = True

    if DEBUG:
        tb_str = u"".join(traceback.format_exception(etype, value, tb))
        message = u"%s\n\n%s" % (value, tb_str)
    else:
        message = unicode(value)

    dlg = wx.MessageDialog(wx.GetApp().GetTopWindow(), message,
                           _("IGC Weight error"), wx.OK | wx.ICON_ERROR)
    try:
        dlg.ShowModal()
    finally:
        dlg.Close()

    if DEBUG:
        sys.__excepthook__(etype, value, tb)

if __name__ == '__main__':
    main()
