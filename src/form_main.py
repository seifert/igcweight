" GUI - Main window "

import wx
from wx import GetTranslation as _

import forms
import settings

from form_igchandicap import IgcHandicapList
from form_organizations import OrganizationList
from form_pilots import PilotList

class Main(forms.Main):
    " Main application window "
    def __init__(self, *args, **kwargs):
        " __init__(self, Window parent, int id=-1) "
        forms.Main.__init__(self, *args, **kwargs)

        self.text_find.ShowSearchButton(True)
        self.text_find.ShowCancelButton(True)

        self.SetSize( (900, 700) )

        # Bind events
        self.Bind(wx.EVT_MENU, self.Exit, self.menu_exit)
        self.Bind(wx.EVT_MENU, self.About, self.menu_about)
        self.Bind(wx.EVT_MENU, self.IgcHandicapList, self.menu_coefficients)
        self.Bind(wx.EVT_MENU, self.Pilots, self.menu_pilots)
        self.Bind(wx.EVT_MENU, self.Organizations, self.menu_organizations)
    
    def Exit(self, evt):
        " Exit(self, Event evt) - exit application event handler "
        wx.Exit()
    
    def About(self, evt):
        " About(self, Event evt) - show about dialog window event handler "
        about = wx.AboutDialogInfo()
        about.SetName( "IGC Weight" )
        about.SetVersion( settings.VERSION )
        about.SetCopyright( _("This program is licensed under GNU General Public License version 2") )
        about.SetDevelopers( ("Jan Seifert, jan.seifert@fotkyzcest.net",) )
        wx.AboutBox(about)

    def IgcHandicapList(self, evt):
        " IgcHandicapList(self, Event evt) - open edit IGC handicap list window event handler "
        dlg = IgcHandicapList(self)
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()

    def Pilots(self, evt):
        " Pilots(self, Event evt) - open edit pilots list window event handler "
        dlg = PilotList(self)
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()

    def Organizations(self, evt):
        " Organizations(self, Event evt) - open edit organizations list window event handler "
        dlg = OrganizationList(self)
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()
