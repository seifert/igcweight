#!/usr/bin/env python
# -*- coding: utf-8 -*-

" Main program module "

from os.path import join

from settings import BASE_DIR

if __name__ == '__main__':
    
    import wx
    app = wx.App()

    mylocale = wx.Locale(wx.LANGUAGE_DEFAULT)
    mylocale.AddCatalogLookupPathPrefix( join(BASE_DIR, 'locale') )
    mylocale.AddCatalog('igcweight')
    
    wx.InitAllImageHandlers()

    from gui_main import Main
    main = Main(None, -1, "")
    app.SetTopWindow(main)
    main.Show()
    
    app.SetAppName( main.GetTitle() )
    app.MainLoop()
