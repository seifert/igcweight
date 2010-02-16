#!/usr/bin/env python
# -*- coding: utf-8 -*-

" Main program module "

def main():
    " main() - start application "

    import wx
    app = wx.App()

    try:
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
        app.SetTopWindow(main)
        main.Show()

        app.SetAppName( main.GetTitle() )
        app.MainLoop()

    except Exception, e:
        from wx import GetTranslation as _

        message = u"%s\n\n%s" % (
            _("Some error during starting application"),
            unicode( str(e), 'utf-8' )
        )
        wx.MessageBox( message, _("Error"), wx.OK | wx.ICON_ERROR, None )

        raise

if __name__ == '__main__':
    main()
