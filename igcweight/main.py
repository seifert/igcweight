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
    from settings import LOCALE_DIR
    mylocale = wx.Locale(wx.LANGUAGE_DEFAULT)
    mylocale.AddCatalogLookupPathPrefix(LOCALE_DIR)
    mylocale.AddCatalog('igcweight')
    # MS Windows hack
    mylocale.AddCatalog('wxstd')

    # Init main window and application
    from gui_main import Main
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
    except:
        def _(s):
            return s
    try:
        from settings import DEBUG
    except:
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