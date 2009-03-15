" GUI - Main window "

import wx
from wx import GetTranslation as _

import forms
from form_igchandicap import IgcHandicapList

class Main(forms.Main):
    " Main application window "
    def __init__(self, *args, **kwargs):
        forms.Main.__init__(self, *args, **kwargs)
    
        self.text_find.ShowSearchButton(True)
        self.text_find.ShowCancelButton(True)
        
        self.SetSize((900, 700))

        self.__bind_events()

    def __bind_events(self):
        self.Bind(wx.EVT_MENU, self.Exit, self.menu_exit)
        self.Bind(wx.EVT_MENU, self.About, self.menu_about)
        self.Bind(wx.EVT_MENU, self.IgcHandicapList, self.menu_coefficients)

    def IgcHandicapList(self, evt):
        " Coefficients(self, evt) - open edit IGC handicap list window "
        dlg = IgcHandicapList(self)
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()
    
    def Exit(self, evt):
        " Exit(self, evt) - exit application "
        wx.Exit()
    
    def About(self, evt):
        " About(self, evt) - show about dialog window "
        about = wx.AboutDialogInfo()
        about.SetName( "IGC Weight" )
        about.SetVersion( "0.1" )
        about.SetCopyright( _("This program is licensed under GNU General Public License version 2") )
        about.SetDevelopers( ("Jan Seifert, jan.seifert@fotkyzcest.net",) )
        wx.AboutBox(about)
