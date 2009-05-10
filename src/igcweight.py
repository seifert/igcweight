#!/usr/bin/env python
# -*- coding: utf-8 -*-

" Main program module "

from os.path import join

def main():
    " main() - start application "
    
    import wx
    app = wx.App()

    try:
        from settings import BASE_DIR
        
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
        from wx import GetTranslation as _

        message = "%s\n\n%s" % ( _("Some error during starting application"),
                                 unicode(str(e), 'utf-8') )
        wx.MessageBox( message, _("Error"), wx.OK | wx.ICON_ERROR, None )
        raise

if __name__ == '__main__':
    main()
