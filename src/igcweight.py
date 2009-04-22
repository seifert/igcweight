#!/usr/bin/env python
# -*- coding: utf-8 -*-

" Main program module "

from os.path import join

from settings import BASE_DIR, DEBUG

def main():
    " main() - start application "
    
    import wx
    app = wx.App()

    try:
        
        mylocale = wx.Locale(wx.LANGUAGE_DEFAULT)
        mylocale.AddCatalogLookupPathPrefix( join(BASE_DIR, 'locale') )
        mylocale.AddCatalog('igcweight')
        mylocale.AddCatalog('wxstd')
        
        wx.InitAllImageHandlers()
    
        from gui_main import Main
        main = Main(None, -1, "")
        app.SetTopWindow(main)
        main.Show()
    
        app.SetAppName( main.GetTitle() )
        app.MainLoop()
        
    except Exception, e:
        from gui_widgets import error_message_dialog
        from wx import GetTranslation as _
        
        error_message_dialog(None, _("Some error during starting application"), e)
        
        if DEBUG:
            raise

if __name__ == '__main__':
    main()
