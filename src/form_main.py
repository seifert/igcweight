" GUI - Main window "

import wx
from wx import GetTranslation as _

import forms
import settings

from sqlalchemy.orm import eagerload

from database import session
from models import GliderCard, Pilot, Organization, GliderType, Photo
from widgets import error_message_dialog
from form_igchandicap import IgcHandicapList
from form_organizations import OrganizationList
from form_pilots import PilotList

class Main(forms.Main):
    " Main application window "
    def __init__(self, *args, **kwargs):
        " __init__(self, Window parent, int id=-1) "
        forms.Main.__init__(self, *args, **kwargs)
        
        self.__sort_glider_card = 0

        self.split_main.SetSashGravity(0.33)
        self.split_main.SetMinimumPaneSize(375)
        self.SetSize( (900, 700) )

        self.text_find.ShowSearchButton(True)
        self.text_find.ShowCancelButton(True)
        
        # Set grid columns
        self.list_glider_card.InsertColumn(0, _("Nr."), 'competition_number', proportion=1)
        self.list_glider_card.InsertColumn(1, _("Registration"), 'registration', proportion=3)
        self.list_glider_card.InsertColumn(2, _("Glider type"), 'glider_type.name', proportion=3)
        self.list_glider_card.InsertColumn(3, _("Pilot"), 'pilot.fullname_rev', proportion=4)

        # Open data source
        self.BASE_QUERY = session.query( GliderCard ).options( eagerload('pilot') ).options( eagerload('glider_type') )
        self.datasource_glider_card = self.BASE_QUERY.all()

        # Bind events
        self.menu_glider_card.Bind(wx.EVT_MENU_OPEN, self.__menu_glider_card_open)
        self.list_glider_card.Bind(wx.EVT_CONTEXT_MENU, self.__list_glider_card_popup_menu)
        self.Bind(wx.EVT_CLOSE, self.Exit, self)
        self.Bind(wx.EVT_MENU, self.Exit, self.menu_exit)
        self.Bind(wx.EVT_MENU, self.About, self.menu_about)
        self.Bind(wx.EVT_MENU, self.IgcHandicapList, self.menu_coefficients)
        self.Bind(wx.EVT_MENU, self.Pilots, self.menu_pilots)
        self.Bind(wx.EVT_MENU, self.Organizations, self.menu_organizations)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.__sort_glider_card_list, self.list_glider_card)
    
    @property
    def datasource_glider_card(self):
        " datasource_glider_card(self) -> list of db items (SQLAlchemy query) "
        return getattr(self.list_glider_card, 'datasource', None)
    @datasource_glider_card.setter
    def datasource_glider_card(self, value):
        " datasource_glider_card(self, list value) - set datasource, value is SQLAlchemy query "
        self.list_glider_card.datasource = value
        count = len(self.datasource_glider_card)
        self.list_glider_card.SetItemCount(count)
        if count > 0:            
            self.SortGliderCardList(self.__sort_glider_card)
            self.list_glider_card.Select(0)
            self.list_glider_card.Focus(0)
        self.__set_enabled_disabled()
    
    def __set_enabled_disabled(self):
        " __set_enabled_disabled(self) - enable or disable controls "
        if self.datasource_glider_card != None:
            self.button_glider_card_new.Enable(True)
            count = len(self.datasource_glider_card)
            if count > 0 and self.list_glider_card.current_item:            
                self.button_glider_card_properties.Enable(True)
                self.button_glider_card_delete.Enable(True)
            else:
                self.button_glider_card_properties.Enable(False)
                self.button_glider_card_delete.Enable(False)
        else:
            self.button_glider_card_new.Enable(False)
            self.button_glider_card_properties.Enable(False)
            self.button_glider_card_delete.Enable(False)
    
    def __list_glider_card_popup_menu(self, evt):
        " __list_glider_popup_menu(self, Event evt) - show pop-up menu "
        pos = evt.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu( self.menu_glider_card, pos )
    
    def __menu_glider_card_open(self, evt):
        " __menu_glider_card_open(self, Event evt) - menu glider type has been opened "
        self.menu_glider_card_new.Enable( self.button_glider_card_new.IsEnabled() )
        self.menu_glider_card_properties.Enable( self.button_glider_card_properties.IsEnabled() )
        self.menu_glider_card_delete.Enable( self.button_glider_card_delete.IsEnabled() )
    
    def __sort_glider_card_list(self, evt):
        " __sort_glider_card(self, evt) - sort glider cards, left-click column tile event handler "
        self.__sort_glider_card = evt.m_col
        self.SortGliderCardList( self.__sort_glider_card )
    
    def SortGliderCardList(self, col):
        " __sort_glider_card(self, evt) - sort glider cards, left-click column tile event handler "
        if self.datasource_glider_card != None:
            count = len(self.datasource_glider_card)
            if count > 0:
                colname = self.list_glider_card.GetColumnFieldName( col )
                current_item = self.list_glider_card.current_item
                self.list_glider_card.SetItemCount(0)
                self.datasource_glider_card.sort( lambda a, b: cmp( a.column_as_str(colname).upper(), b.column_as_str(colname).upper() ) )
                if current_item == None:
                    i = 0
                else:
                    i = self.datasource_glider_card.index(current_item)
                self.list_glider_card.SetItemCount(count)
                self.list_glider_card.Select(i)
                self.list_glider_card.Focus(i)
    
    def Exit(self, evt=None):
        " Exit(self, Event evt=None) - exit application event handler "
        app = wx.GetApp()
        if settings.DEBUG:
            # Don't ask in DEBUG mode
            app.Exit()
        else:
            # Show confirm dialog window
            dlg = wx.MessageDialog(self, _("Exit application?"), _("Exit?"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
            try:
                if dlg.ShowModal() == wx.ID_YES:
                    wx.GetApp().Exit()
            finally:
                dlg.Destroy()
    
    def About(self, evt=None):
        " About(self, Event evt=None) - show about dialog window event handler "
        about = wx.AboutDialogInfo()
        about.SetName( "IGC Weight" )
        about.SetVersion( settings.VERSION )
        about.SetCopyright( _("This program is licensed under GNU General Public License version 2") )
        about.SetDevelopers( ("Jan Seifert, jan.seifert@fotkyzcest.net",) )
        wx.AboutBox(about)

    def IgcHandicapList(self, evt=None):
        " IgcHandicapList(self, Event evt=None) - open edit IGC handicap list window event handler "
        dlg = IgcHandicapList(self)
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()

    def Pilots(self, evt=None):
        " Pilots(self, Event evt=None) - open edit pilots list window event handler "
        dlg = PilotList(self)
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()

    def Organizations(self, evt=None):
        " Organizations(self, Event evt=None) - open edit organizations list window event handler "
        dlg = OrganizationList(self)
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()
