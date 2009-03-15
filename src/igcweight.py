#!/usr/bin/env python
# -*- coding: utf-8 -*-

" Main program module "

from os.path import abspath, dirname, join

BASE_DIR = abspath( join(dirname(__file__), '..') )

if __name__ == '__main__':
    
    import wx
    app = wx.App()

    mylocale = wx.Locale(wx.LANGUAGE_DEFAULT)
    mylocale.AddCatalogLookupPathPrefix( join(BASE_DIR, 'locale') )
    mylocale.AddCatalog('igcweight')
    
    wx.InitAllImageHandlers()

    from form_main import Main
    main = Main(None, -1, "")
    app.SetTopWindow(main)
    main.Show()
    
    app.SetAppName( main.GetTitle() )
    app.MainLoop()
