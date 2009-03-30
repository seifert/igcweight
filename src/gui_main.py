" GUI - Main window "

import os

from os import remove
from os.path import isfile
from shutil import copy

import wx
from wx import GetTranslation as _

from sqlalchemy import or_
from sqlalchemy.orm import eagerload, join

import settings

from database import session
from models import GliderCard, Pilot, Organization, GliderType, Photo
from gui_widgets import error_message_dialog, VirtualListCtrl, GetPhotoBitmap
from gui_igchandicap import IgcHandicapList, IgcHandicapForm, GLIDER_TYPE_INSERT_ERROR
from gui_organizations import OrganizationList, OrganizationForm, ORGANIZATION_INSERT_ERROR
from gui_pilots import PilotList, PilotForm, PILOT_INSERT_ERROR

class Main(wx.Frame):
    " Main application window "
    def __init__(self, *args, **kwds):
        " __init__(self, Window parent, int id=-1) "
        
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        
        self.split_main = wx.SplitterWindow(self, -1, style=wx.SP_3D|wx.SP_BORDER)
        self.panel_card = wx.Panel(self.split_main, -1)
        self.sizer_photo_staticbox = wx.StaticBox(self.panel_card, -1, _("Photo"))
        self.panel_gliders = wx.Panel(self.split_main, -1)
        
        # Menu Bar
        self.main_menu = wx.MenuBar()
        self.menu_file = wx.Menu()
        self.menu_exit = wx.MenuItem(self.menu_file, wx.NewId(), _("E&xit\tAlt-F4"), _("Exit application"), wx.ITEM_NORMAL)
        self.menu_file.AppendItem(self.menu_exit)
        self.main_menu.Append(self.menu_file, _("&File"))
        self.menu_edit = wx.Menu()
        self.menu_coefficients = wx.MenuItem(self.menu_edit, wx.NewId(), _("&IGC handicap list..."), _("Edit gliders and IGC handicap list"), wx.ITEM_NORMAL)
        self.menu_edit.AppendItem(self.menu_coefficients)
        self.menu_pilots = wx.MenuItem(self.menu_edit, wx.NewId(), _("&Pilots..."), _("Edit pilots list"), wx.ITEM_NORMAL)
        self.menu_edit.AppendItem(self.menu_pilots)
        self.menu_organizations = wx.MenuItem(self.menu_edit, wx.NewId(), _("&Organizations or countries..."), _("Edit organizations or coutries list"), wx.ITEM_NORMAL)
        self.menu_edit.AppendItem(self.menu_organizations)
        self.main_menu.Append(self.menu_edit, _("&Edit"))
        self.menu_glider_card = wx.Menu()
        self.menu_glider_card_new = wx.MenuItem(self.menu_glider_card, wx.NewId(), _("&New...\tInsert"), _("Add new glider"), wx.ITEM_NORMAL)
        self.menu_glider_card.AppendItem(self.menu_glider_card_new)
        self.menu_glider_card_properties = wx.MenuItem(self.menu_glider_card, wx.NewId(), _("&Properties..."), _("Edit glider properties"), wx.ITEM_NORMAL)
        self.menu_glider_card.AppendItem(self.menu_glider_card_properties)
        self.menu_glider_card_delete = wx.MenuItem(self.menu_glider_card, wx.NewId(), _("&Delete"), _("Delete glider"), wx.ITEM_NORMAL)
        self.menu_glider_card.AppendItem(self.menu_glider_card_delete)
        self.main_menu.Append(self.menu_glider_card, _("&Glider card"))
        self.menu_help = wx.Menu()
        self.menu_about = wx.MenuItem(self.menu_help, wx.NewId(), _("&About\tF1"), _("About this application"), wx.ITEM_NORMAL)
        self.menu_help.AppendItem(self.menu_about)
        self.main_menu.Append(self.menu_help, _("&Help"))
        self.SetMenuBar(self.main_menu)
        # Menu Bar end
        self.statusbar = self.CreateStatusBar(1, wx.ST_SIZEGRIP)
        self.text_find = wx.SearchCtrl(self.panel_gliders, -1, style=wx.TE_PROCESS_ENTER)
        self.list_glider_card = VirtualListCtrl(self.panel_gliders, -1)
        self.button_glider_card_new = wx.Button(self.panel_gliders, wx.ID_NEW, "")
        self.button_glider_card_properties = wx.Button(self.panel_gliders, wx.ID_PROPERTIES, "")
        self.button_glider_card_delete = wx.Button(self.panel_gliders, wx.ID_DELETE, "")
        self.label_registration = wx.StaticText(self.panel_card, -1, _("Registration"))
        self.label_competition_number = wx.StaticText(self.panel_card, -1, _("Competition number"))
        self.text_registration = wx.StaticText(self.panel_card, -1, "")
        self.text_competition_number = wx.StaticText(self.panel_card, -1, "")
        self.label_glider_type = wx.StaticText(self.panel_card, -1, _("Glider type"))
        self.text_glider_type = wx.StaticText(self.panel_card, -1, "")
        self.label_pilot = wx.StaticText(self.panel_card, -1, _("Pilot"))
        self.text_pilot = wx.StaticText(self.panel_card, -1, "")
        self.label_organization = wx.StaticText(self.panel_card, -1, _("Organization or country"))
        self.text_organization = wx.StaticText(self.panel_card, -1, "")
        self.label_winglets = wx.StaticText(self.panel_card, -1, _("Winglets"))
        self.label_landing_gear = wx.StaticText(self.panel_card, -1, _("Landing gear"))
        self.text_winglets = wx.StaticText(self.panel_card, -1, "")
        self.text_landing_gear = wx.StaticText(self.panel_card, -1, "")
#        self.text_description = wx.TextCtrl(self.panel_card, -1, style=wx.NO_BORDER|wx.TE_MULTILINE|wx.TE_WORDWRAP)
#        self.text_description = wx.StaticText(self.panel_card, -1, "")
        self.photo = wx.StaticBitmap(self.panel_card, -1)
        self.button_show_photo = wx.Button(self.panel_card, wx.ID_ZOOM_IN, "")

        self.__set_properties()
        self.__do_layout()

        self.__sort_glider_card = 0
        self.__filtered = False

        self.text_find.ShowSearchButton(True)
        self.text_find.ShowCancelButton(True)
        
        # Set grid columns
        self.list_glider_card.InsertColumn(0, _("Nr."), 'competition_number', proportion=1)
        self.list_glider_card.InsertColumn(1, _("Registration"), 'registration', proportion=3)
        self.list_glider_card.InsertColumn(2, _("Glider type"), 'glider_type', proportion=3)
        self.list_glider_card.InsertColumn(3, _("Pilot"), 'pilot', proportion=4)

        # Open data source
        self.BASE_QUERY = session.query(GliderCard).join( (Pilot, GliderCard.pilot_id==Pilot.id), (GliderType, GliderCard.glider_type_id==GliderType.id) )
        self.datasource_glider_card = self.BASE_QUERY.all()

        # Bind events
        self.list_glider_card.Bind(wx.EVT_CONTEXT_MENU, self.__list_glider_card_popup_menu)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.ChangeGliderCard, self.list_glider_card)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.__sort_glider_card_list, self.list_glider_card)
        self.Bind(wx.EVT_CLOSE, self.Exit, self)
        self.Bind(wx.EVT_MENU, self.Exit, self.menu_exit)
        self.Bind(wx.EVT_MENU, self.About, self.menu_about)
        self.Bind(wx.EVT_MENU, self.IgcHandicapList, self.menu_coefficients)
        self.Bind(wx.EVT_MENU, self.Pilots, self.menu_pilots)
        self.Bind(wx.EVT_MENU, self.Organizations, self.menu_organizations)
        self.Bind(wx.EVT_MENU, self.GliderCardNew, self.menu_glider_card_new)
        self.Bind(wx.EVT_MENU, self.GliderCardProperties, self.menu_glider_card_properties)
        self.Bind(wx.EVT_MENU, self.GliderCardDelete, self.menu_glider_card_delete)
        self.Bind(wx.EVT_BUTTON, self.GliderCardNew, self.button_glider_card_new)
        self.Bind(wx.EVT_BUTTON, self.GliderCardProperties, self.button_glider_card_properties)
        self.Bind(wx.EVT_BUTTON, self.GliderCardDelete, self.button_glider_card_delete)
        self.Bind(wx.EVT_TEXT_ENTER, self.SearchGliderCard, self.text_find)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.SearchGliderCard, self.text_find)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.AllGliderCard, self.text_find)

    def __set_properties(self):
        self.SetTitle(_("IGC Weight"))

        self.statusbar.SetStatusWidths([-1])
        statusbar_fields = [""]
        for i in range(len(statusbar_fields)):
            self.statusbar.SetStatusText(statusbar_fields[i], i)
            
        self.list_glider_card.SetFocus()
        
        self.button_glider_card_new.SetToolTipString(_("Add new glider"))
        self.button_glider_card_new.Enable(False)
        self.button_glider_card_properties.SetToolTipString(_("Edit glider properties"))
        self.button_glider_card_properties.Enable(False)
        self.button_glider_card_delete.SetToolTipString(_("Delete glider"))
        self.button_glider_card_delete.Enable(False)
        self.button_show_photo.SetToolTipString(_("Show photo"))
        
        self.text_registration.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
        self.text_competition_number.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
        self.text_glider_type.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
        self.text_pilot.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
        self.text_organization.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
        self.text_winglets.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
        self.text_landing_gear.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
#        self.text_description.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))

        self.text_registration.SetFont(wx.Font(20, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.text_competition_number.SetFont(wx.Font(20, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.text_glider_type.SetFont(wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.text_pilot.SetFont(wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.text_organization.SetFont(wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.text_winglets.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.text_landing_gear.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
#        self.text_description.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        
        self.photo.SetMinSize((180, -1))
        self.split_main.SetSashGravity(0.33)
        self.split_main.SetMinimumPaneSize(375)

    def __do_layout(self):
        sizer_main = wx.BoxSizer(wx.HORIZONTAL)
        sizer_card = wx.BoxSizer(wx.VERTICAL)
        sizer_card_head = wx.BoxSizer(wx.HORIZONTAL)
        sizer_photo = wx.StaticBoxSizer(self.sizer_photo_staticbox, wx.VERTICAL)

        sizer_card_base = wx.GridBagSizer(0, 0)
        sizer_gliders = wx.BoxSizer(wx.VERTICAL)
        sizer_gliders_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_gliders.Add(self.text_find, 0, wx.LEFT|wx.TOP|wx.EXPAND, 4)
        sizer_gliders.Add(self.list_glider_card, 1, wx.LEFT|wx.TOP|wx.BOTTOM|wx.EXPAND, 4)
        sizer_gliders_buttons.Add(self.button_glider_card_new, 1, wx.RIGHT, 2)
        sizer_gliders_buttons.Add(self.button_glider_card_properties, 1, wx.LEFT|wx.RIGHT, 2)
        sizer_gliders_buttons.Add(self.button_glider_card_delete, 1, wx.LEFT, 2)
        sizer_gliders.Add(sizer_gliders_buttons, 0, wx.LEFT|wx.BOTTOM|wx.EXPAND, 4)
        self.panel_gliders.SetSizer(sizer_gliders)
        
        sizer_card_base.Add(self.label_competition_number, (0, 0), (1, 1), wx.LEFT|wx.BOTTOM|wx.EXPAND, 2)
        sizer_card_base.Add(self.label_registration, (0, 1), (1, 1), wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        sizer_card_base.Add(self.text_competition_number, (1, 0), (1, 1), wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        sizer_card_base.Add(self.text_registration, (1, 1), (1, 1), wx.LEFT|wx.BOTTOM|wx.EXPAND, 2)
        sizer_card_base.Add(self.label_glider_type, (2, 0), (1, 2), wx.BOTTOM|wx.EXPAND, 2)
        sizer_card_base.Add(self.text_glider_type, (3, 0), (1, 2), wx.BOTTOM|wx.EXPAND, 2)
        sizer_card_base.Add(self.label_pilot, (4, 0), (1, 2), wx.BOTTOM|wx.EXPAND, 2)
        sizer_card_base.Add(self.text_pilot, (5, 0), (1, 2), wx.BOTTOM|wx.EXPAND, 2)
        sizer_card_base.Add(self.label_organization, (6, 0), (1, 2), wx.BOTTOM|wx.EXPAND, 2)
        sizer_card_base.Add(self.text_organization, (7, 0), (1, 2), wx.BOTTOM|wx.EXPAND, 2)
        sizer_card_base.Add(self.label_landing_gear, (8, 0), (1, 1), wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        sizer_card_base.Add(self.label_winglets, (8, 1), (1, 1), wx.LEFT|wx.BOTTOM|wx.EXPAND, 2)
        sizer_card_base.Add(self.text_landing_gear, (9, 0), (1, 1), wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        sizer_card_base.Add(self.text_winglets, (9, 1), (1, 1), wx.LEFT|wx.BOTTOM|wx.EXPAND, 2)
#        sizer_card_base.Add(self.text_description, (10, 0), (1, 2), wx.TOP|wx.BOTTOM|wx.EXPAND, 2)
        sizer_card_base.Add(wx.StaticLine(self.panel_card), (10, 0), (1, 2), wx.TOP|wx.EXPAND, 4)
        sizer_card_base.AddGrowableRow(9)
        sizer_card_base.AddGrowableCol(0)
        sizer_card_base.AddGrowableCol(1)
        
        sizer_photo.Add(self.photo, 1, wx.ALL|wx.EXPAND, 4)
        sizer_photo.Add(self.button_show_photo, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 4)

        sizer_card_head.Add(sizer_card_base, 1, wx.TOP|wx.BOTTOM|wx.EXPAND, 4)
        sizer_card_head.Add(sizer_photo, 0, wx.ALL|wx.EXPAND, 4)
        
        sizer_card.Add(sizer_card_head, 0, wx.EXPAND, 0)
        sizer_card.Add(wx.Panel(self.panel_card, -1), 1, wx.ALL|wx.EXPAND, 4)

        self.panel_card.SetSizer(sizer_card)
        self.split_main.SplitVertically(self.panel_gliders, self.panel_card)
        sizer_main.Add(self.split_main, 1, wx.EXPAND, 0)
        
        self.SetSizer(sizer_main)
        sizer_main.Fit(self)
        self.Layout()
        
        self.SetSize( (950, 700) )
        self.split_main.SetSashPosition(375)
    
    def get_datasource_glider_card(self):
        " datasource_glider_card(self) -> list of db items (SQLAlchemy query) "
        return getattr(self.list_glider_card, 'datasource', None)
    def set_datasource_glider_card(self, value):
        " datasource_glider_card(self, list value) - set datasource, value is SQLAlchemy query "
        self.list_glider_card.datasource = value
        count = len(self.datasource_glider_card)
        self.list_glider_card.SetItemCount(count)
        if count > 0:
            self.SortGliderCardList(self.__sort_glider_card)
            self.list_glider_card.Select(0)
            self.list_glider_card.Focus(0)
            self.ChangeGliderCard()
        self.__set_enabled_disabled()
    datasource_glider_card = property(get_datasource_glider_card, set_datasource_glider_card)
    
    def __set_enabled_disabled(self):
        " __set_enabled_disabled(self) - enable or disable controls "
        if self.datasource_glider_card != None:
            glider_card_new = True
            count = len(self.datasource_glider_card)
            if count > 0 and self.list_glider_card.current_item:            
                glider_card_properties = True
                glider_card_delete = True
            else:
                glider_card_properties = False
                glider_card_delete =  False
        else:
            glider_card_new = False
            glider_card_properties = False
            glider_card_delete = False
        
        self.button_glider_card_new.Enable(glider_card_new)
        self.menu_glider_card_new.Enable(glider_card_new)
        self.button_glider_card_properties.Enable(glider_card_properties)
        self.menu_glider_card_properties.Enable(glider_card_properties)
        self.button_glider_card_delete.Enable(glider_card_delete)
        self.menu_glider_card_delete.Enable(glider_card_delete)
    
    def __list_glider_card_popup_menu(self, evt):
        " __list_glider_popup_menu(self, Event evt) - show pop-up menu "
        pos = evt.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu( self.menu_glider_card, pos )

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

    def GliderCardNew(self, evt=None):
        " GliderCardNew(self, Event evt=None) - add new glider card event handler "
        dlg = GliderCardForm(self)
        try:
            while True:
                try:
                    dlg.SetData()
                    if dlg.ShowModal() == wx.ID_OK:
                        try:
                            record = dlg.GetData()
                            session.add(record)
                            
                            # TODO: improve adding new photo
                            if dlg.is_photo_changed:
                                main_photo = Photo(main=True)
                                record.photos.append(main_photo)
                                session.flush()
                                copy( dlg.photo_fullpath, main_photo.full_path )
                            
                            session.commit()
                            self.datasource_glider_card.append(record)
                            count = len(self.datasource_glider_card)
                            self.list_glider_card.SetItemCount(count)
                            self.list_glider_card.Select(count-1)
                            self.list_glider_card.Focus(count-1)
                            self.ChangeGliderCard()
                        finally:
                            self.__set_enabled_disabled()
                    break
                except Exception, e:
                    session.rollback()
                    error_message_dialog( self, _("Glider card insert error"), e )
        finally:
            dlg.Destroy()

    def GliderCardProperties(self, evt=None):
        " GliderCardProperties(self, Event evt=None) - edit glider card event handler "
        dlg = GliderCardForm(self)
        try:
            record = self.list_glider_card.current_item
            main_photo = record.main_photo
            # Put data into dialog
            dlg.SetData(record)
            while True:
                try:
                    if dlg.ShowModal() == wx.ID_OK:
                        record = dlg.GetData()
                        
                        # TODO: improve change or delete photo
                        if dlg.is_photo_changed:
                            # Delete old photo
                            if main_photo != None:
                                full_path = main_photo.full_path
                                session.delete(main_photo)
                                session.flush()
                                if isfile(full_path):
                                    remove(full_path)
                            # Add new photo
                            if dlg.photo_fullpath != None:
                                main_photo = Photo(main=True)
                                record.photos.append(main_photo)
                                session.flush()
                                copy( dlg.photo_fullpath, main_photo.full_path )
                        
                        session.commit()
                        self.list_glider_card.RefreshItem( self.list_glider_card.GetFocusedItem() )
                        self.ChangeGliderCard()
                    break
                except Exception, e:
                    session.rollback()
                    error_message_dialog( self, _("Glider card edit error"), e )
        finally:
            dlg.Destroy()

    def GliderCardDelete(self, evt=None):
        " GliderCardDelete(self, Event evt=None) - delete glider card event handler "
        record = self.list_glider_card.current_item
        if wx.MessageDialog(self,
                            _("Are you sure to delete %s?") % record,
                            _("Delete %s?") % record,
                            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING
                           ).ShowModal() == wx.ID_YES:
            try:
                i = self.datasource_glider_card.index(record)
                try:
                    # TODO: improve delete photos
                    photos_path = [ photo.full_path for photo in record.photos ]
                    session.delete(record)
                    session.flush()
                    for path in photos_path:
                        remove(path)
                    
                    session.commit()
                    del( self.datasource_glider_card[i] )
                    i = i - 1
                    i = i >= 0 and i or 0
                    self.list_glider_card.SetItemCount( len(self.datasource_glider_card) )
                    self.list_glider_card.Select(i)
                    self.list_glider_card.Focus(i)
                    self.ChangeGliderCard()
                finally:
                    self.__set_enabled_disabled()
            except Exception, e:
                session.rollback()
                error_message_dialog( self, _("Glider card delete error"), e )

    def SearchGliderCard(self, evt=None):
        " SearchGliderCard(self, Event evt=None) - filter glider card according to competition number or registration "
        value = self.text_find.Value
        if value != '':
            value = '%%%s%%' % value
            self.datasource_glider_card = self.BASE_QUERY.filter(or_(
                    GliderCard.competition_number.ilike(value),
                    GliderCard.registration.ilike(value),
                    GliderType.name.ilike(value),
                    Pilot.firstname.ilike(value),
                    Pilot.surname.ilike(value)
                )).all()
            self.__filtered = True
            self.ChangeGliderCard()
        else:
            self.AllGliderCard()

    def AllGliderCard(self, evt=None):
        " AllGliderCard(self, Event evt=None) - cancel filter glider card and show all data "
        if self.__filtered:
            self.text_find.SetValue('')
            self.datasource_glider_card = self.BASE_QUERY.all()
            self.__filtered = False
            self.ChangeGliderCard()

    def ChangeGliderCard(self, evt=None):
        " ChangeGliderCard(self, Event evt=None) - this method is called when glider card is changed "
        record = self.list_glider_card.current_item
        if record != None:
            self.text_registration.SetLabel( record.column_as_str('registration') )
            self.text_competition_number.SetLabel( record.column_as_str('competition_number') )
            self.text_glider_type.SetLabel( record.column_as_str('glider_type') )
            self.text_pilot.SetLabel( record.column_as_str('pilot') )
            self.text_organization.SetLabel( record.column_as_str('organization') )
            self.text_winglets.SetLabel( record.column_as_str('winglets') )
            self.text_landing_gear.SetLabel( record.column_as_str('landing_gear') )
#            self.text_description.SetValue( record.column_as_str('description') )
#            self.text_description.SetLabel( record.short_description and record.short_description or '' )
#            if record.description:
#                self.text_description.SetToolTipString( record.column_as_str('description') )
#            else:
#                self.text_description.SetToolTipString('')
            if record.main_photo != None:
                self.photo.SetBitmap( GetPhotoBitmap( self.photo.ClientSize, record.main_photo.full_path ) )
                self.button_show_photo.Enable(True)
            else:
                self.photo.SetBitmap( GetPhotoBitmap(self.photo.ClientSize) )
                self.button_show_photo.Enable(False)
#            self.AddPendingEvent( wx.SizeEvent( self.GetClientSize() ) )
        else:
            self.text_registration.Label = ''
            self.text_competition_number.Label = ''
            self.text_glider_type.Label = ''
            self.text_pilot.Label = ''
            self.text_organization.Label = ''
            self.text_winglets.Label = ''
            self.text_landing_gear.Label = ''
            self.text_description.Label = ''
            self.text_description.SetToolTipString('')
            self.button_show_photo.Enable(False)
            self.photo.SetBitmap( GetPhotoBitmap(self.photo.ClientSize) )

class GliderCardForm(wx.Dialog):
    " Glider card insert/edit dialog "
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.THICK_FRAME
        wx.Dialog.__init__(self, *args, **kwds)
        
        self.sizer_picture_staticbox = wx.StaticBox(self, -1, _("Photo"))
        self.label_registration = wx.StaticText(self, -1, _("Registration"), style=wx.BORDER_SUNKEN)
        self.label_competition_number = wx.StaticText(self, -1, _("Competition number"))
        self.text_registration = wx.TextCtrl(self, -1, "")
        self.text_competition_number = wx.TextCtrl(self, -1, "")
        self.label_glider_type = wx.StaticText(self, -1, _("Glider type"))
        self.combo_glider_type = wx.ComboBox(self, -1, choices=[], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.button_add_glider_type = wx.Button(self, -1, _("Add..."), style=wx.BU_EXACTFIT)
        self.label_pilot = wx.StaticText(self, -1, _("Pilot"))
        self.combo_pilot = wx.ComboBox(self, -1, choices=[], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.button_add_pilot = wx.Button(self, -1, _("Add..."), style=wx.BU_EXACTFIT)
        self.label_organization = wx.StaticText(self, -1, _("Organization or country"))
        self.combo_organization = wx.ComboBox(self, -1, choices=[], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.button_add_organization = wx.Button(self, -1, _("Add..."), style=wx.BU_EXACTFIT)
        self.checkbox_winglets = wx.CheckBox(self, -1, _("Winglets"))
        self.checkbox_gear = wx.CheckBox(self, -1, _("Landing gear"))
        self.photo = wx.StaticBitmap(self, -1)
        self.button_open_photo = wx.Button(self, wx.ID_OPEN, "")
        self.button_clear_photo = wx.Button(self, wx.ID_CLEAR, "")
        self.label_description = wx.StaticText(self, -1, _("Description"))
        self.text_description = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE|wx.TE_WORDWRAP)
        self.button_ok = wx.Button(self, wx.ID_OK, "")
        self.button_cancel = wx.Button(self, wx.ID_CANCEL, "")

        self.__set_properties()
        self.__do_layout()

        # Bind events
        self.Bind(wx.EVT_TEXT, self.__text_ctrl_change, self.text_registration)
        self.Bind(wx.EVT_TEXT, self.__text_ctrl_change, self.text_competition_number)
        self.Bind(wx.EVT_BUTTON, self.__add_glider_type, self.button_add_glider_type)
        self.Bind(wx.EVT_BUTTON, self.__add_pilot, self.button_add_pilot)
        self.Bind(wx.EVT_BUTTON, self.__add_organization, self.button_add_organization)
        self.Bind(wx.EVT_BUTTON, self.__open_photo, self.button_open_photo)
        self.Bind(wx.EVT_BUTTON, self.__clear_photo, self.button_clear_photo)

        # Init combo-box data sources
        self.glider_type_items = session.query( GliderType ).all()
        self.pilot_items = session.query( Pilot ).all()
        self.organization_items = session.query( Organization ).all()
        # Fill combo-boxes
        self.__init_combo_glider_type()
        self.__init_combo_pilot()
        self.__init_combo_organization()

    def __set_properties(self):
        self.SetTitle(_("Glider card"))
        
        char_w = self.combo_glider_type.CharWidth
        self.combo_glider_type.SetMinSize( (char_w * 50, -1) )
        
        fontbold = self.label_registration.GetFont()
        fontbold.SetWeight(wx.FONTWEIGHT_BOLD)
        self.label_registration.SetFont(fontbold)
        self.label_competition_number.SetFont(fontbold)
        self.label_glider_type.SetFont(fontbold)
        self.label_pilot.SetFont(fontbold)
        self.label_organization.SetFont(fontbold)
        
        self.text_registration.SetMaxLength(10)
        self.text_competition_number.SetMaxLength(5)

        self.button_add_glider_type.SetToolTipString(_("Add glider type"))
        self.button_add_pilot.SetToolTipString(_("Add pilot"))
        self.button_add_organization.SetToolTipString(_("Add organization or country"))
        self.button_open_photo.SetToolTipString(_("Open picture from file"))
        self.button_clear_photo.SetToolTipString(_("Clear picture"))
        
        self.text_registration.SetFocus()
        self.button_ok.SetDefault()

    def __do_layout(self):
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_glider_card = wx.BoxSizer(wx.HORIZONTAL)
        sizer_description = wx.BoxSizer(wx.VERTICAL)
        sizer_data = wx.GridBagSizer(2, 2)
        sizer_photo = wx.StaticBoxSizer(self.sizer_picture_staticbox, wx.VERTICAL)
        sizer_photo_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_buttons = wx.StdDialogButtonSizer()
        # Glider data sizer
        sizer_data.Add(self.label_registration, (0, 0), (1, 1), wx.RIGHT|wx.EXPAND, 2)
        sizer_data.Add(self.label_competition_number, (0, 1), (1, 1), wx.LEFT|wx.EXPAND, 2)
        sizer_data.Add(self.text_registration, (1, 0), (1, 1), wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        sizer_data.Add(self.text_competition_number, (1, 1), (1, 1), wx.LEFT|wx.BOTTOM|wx.EXPAND, 2)
        sizer_data.Add(self.label_glider_type, (2, 0), (1, 3), wx.RIGHT|wx.EXPAND, 2)
        sizer_data.Add(self.combo_glider_type, (3, 0), (1, 2), wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        sizer_data.Add(self.button_add_glider_type, (3, 2), (1, 1), wx.LEFT|wx.BOTTOM, 2)
        sizer_data.Add(self.label_pilot, (4, 0), (1, 3), wx.RIGHT|wx.EXPAND, 2)
        sizer_data.Add(self.combo_pilot, (5, 0), (1, 2), wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        sizer_data.Add(self.button_add_pilot, (5, 2), (1, 1), wx.LEFT|wx.BOTTOM, 2)
        sizer_data.Add(self.label_organization, (6, 0), (1, 3), wx.RIGHT|wx.EXPAND, 2)
        sizer_data.Add(self.combo_organization, (7, 0), (1, 2), wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        sizer_data.Add(self.button_add_organization, (7, 2), (1, 1), wx.LEFT|wx.BOTTOM, 2)
        sizer_data.Add(self.checkbox_winglets, (8, 0), (1, 1), wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND, 2)
        sizer_data.Add(self.checkbox_gear, (8, 1), (1, 1), wx.LEFT|wx.TOP|wx.BOTTOM|wx.EXPAND, 2)
        sizer_data.AddGrowableCol(0)
        sizer_data.AddGrowableCol(1)
        # Photo sizer
        sizer_photo.Add(self.photo, 1, wx.ALL|wx.EXPAND, 4)
        sizer_photo_buttons.Add(self.button_open_photo, 1, wx.RIGHT|wx.EXPAND, 2)
        sizer_photo_buttons.Add(self.button_clear_photo, 1, wx.LEFT|wx.EXPAND, 2)
        sizer_photo.Add(sizer_photo_buttons, 0, wx.ALL|wx.EXPAND, 4)
        # Description sizer
        sizer_description.Add(self.label_description, 0, wx.BOTTOM|wx.EXPAND, 2)
        sizer_description.Add(self.text_description, 1, wx.BOTTOM|wx.EXPAND, 2)
        # Dialog buttons sizer
        sizer_buttons.AddButton(self.button_ok)
        sizer_buttons.AddButton(self.button_cancel)
        sizer_buttons.Realize()
        
        sizer_glider_card.Add(sizer_data, 1, wx.RIGHT|wx.TOP|wx.EXPAND, 4)
        sizer_glider_card.Add(sizer_photo, 0, wx.LEFT|wx.TOP|wx.EXPAND, 4)
        sizer_main.Add(sizer_glider_card, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 4)
        sizer_main.Add(sizer_description, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 4)
        sizer_main.Add(sizer_buttons, 0, wx.ALL|wx.ALIGN_RIGHT, 4)
        
        self.SetSizer(sizer_main)
        sizer_main.Fit(self)
        self.Layout()
        self.SetMinSize( self.GetSize() )
        self.CenterOnParent()

    def __init_combo_glider_type(self):
        " __init_combo_glider_type(self) - load data into combo_box_glider_type "
        self.glider_type_items.sort( lambda a, b: cmp( a.name.upper(), b.name.upper() ) )
        self.combo_glider_type.Clear()
        self.combo_glider_type.SetItems( [ i.name for i in self.glider_type_items ] )

    def __init_combo_pilot(self):
        " __init_combo_pilot(self) - load data into combo_box_pilot "
        self.pilot_items.sort( lambda a, b: cmp( a.fullname_rev.upper(), b.fullname_rev.upper() ) )
        self.combo_pilot.SetItems( [ i.fullname for i in self.pilot_items ] )

    def __init_combo_organization(self):
        " __init_combo_organization(self) - load data into combo_box_organization "
        self.organization_items.sort( lambda a, b: cmp( a.name.upper(), b.name.upper() ) )
        self.combo_organization.SetItems( [ "%s, %s" % (i.name, i.code,) for i in self.organization_items ] )

    def __text_ctrl_change(self, evt):
        " __text_ctrl_change(self, evt) - upper case value in the text control "
        ctrl = evt.GetEventObject()
        old = ctrl.GetValue()
        new = old.upper()
        if old != new:
            ctrl.ChangeValue(new)
            ctrl.SetInsertionPointEnd()
        evt.Skip()
        
    def __add_glider_type(self, evt):
        " __add_glider_type(self, evt) - add new glider type event handler "
        dlg = IgcHandicapForm(self)
        try:
            while True:
                try:
                    if dlg.ShowModal() == wx.ID_OK:
                        record = dlg.GetData()
                        session.add(record)
                        session.commit()
                        self.glider_type_items.append(record)
                        self.__init_combo_glider_type()
                        self.combo_glider_type.SetSelection( self.glider_type_items.index(record) )
                    break
                except Exception, e:
                    session.rollback()
                    error_message_dialog( self, GLIDER_TYPE_INSERT_ERROR, e )
        finally:
            dlg.Destroy()
        
    def __add_pilot(self, evt):
        " __add_pilot(self, evt) - add new pilot event handler "
        dlg = PilotForm(self)
        try:
            while True:
                try:
                    if dlg.ShowModal() == wx.ID_OK:
                        record = dlg.GetData()
                        session.add(record)
                        session.commit()
                        self.pilot_items.append(record)
                        self.__init_combo_pilot()
                        self.combo_pilot.SetSelection( self.pilot_items.index(record) )
                    break
                except Exception, e:
                    session.rollback()
                    error_message_dialog( self, PILOT_INSERT_ERROR, e )
        finally:
            dlg.Destroy()
        
    def __add_organization(self, evt):
        " __add_organization(self, evt) - add new organization event handler "
        dlg = OrganizationForm(self)
        try:
            while True:
                try:
                    if dlg.ShowModal() == wx.ID_OK:
                        record = dlg.GetData()
                        session.add(record)
                        session.commit()
                        self.organization_items.append(record)
                        self.__init_combo_organization()
                        self.combo_organization.SetSelection( self.organization_items.index(record) )
                    break
                except Exception, e:
                    session.rollback()
                    error_message_dialog( self, ORGANIZATION_INSERT_ERROR, e )
        finally:
            dlg.Destroy()
        
    def __open_photo(self, evt):
        " __open_photo(self, evt) - open photo event handler "
        dlg = wx.FileDialog( self, defaultDir=settings.LAST_OPEN_FILE_PATH, message=_("Open file"),
                             wildcard=_("JPEG files")+" (*.jpg;*.jpeg)|*.jpg;*.jpeg;*.JPG;*.JPEG",
                             style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST|wx.FD_PREVIEW )
        try:
            if dlg.ShowModal() == wx.ID_OK:
                self.__photo_changed = True
                self.photo_fullpath = os.path.join( dlg.Directory, dlg.Filename )
                settings.LAST_OPEN_FILE_PATH = dlg.Directory
                self.photo.SetBitmap( GetPhotoBitmap( self.photo.ClientSize, self.photo_fullpath ) )
        finally:
            dlg.Destroy()

    def __clear_photo(self, evt):
        " __clear_photo(self, evt) - clear photo event handler "
        if getattr(self, 'photo_fullpath', None) != None:
            self.__photo_changed = True
            self.photo_fullpath = None
            self.photo.SetBitmap( GetPhotoBitmap(self.photo.ClientSize) )
    
    def __init_photo(self, photo=None):
        " __init_photo(self, Photo photo=None) - show photo thumbnail or empty photo "
        self.__photo_changed = False
        if photo == None:
            # Show empty photo
            self.photo_fullpath = None
            self.photo.SetBitmap( GetPhotoBitmap(self.photo.ClientSize) )
        else:
            self.photo_fullpath = photo.full_path
            self.photo.SetBitmap( GetPhotoBitmap( self.photo.ClientSize, self.photo_fullpath ) )
    
    @property
    def is_photo_changed(self):
        return self.__photo_changed
        
    def GetData(self):
        " GetData(self) -> GliderCard - get cleaned form data "
        glidercard = getattr( self, 'glidercard', GliderCard() )
        glidercard.str_to_column( 'registration', self.text_registration.Value )
        glidercard.str_to_column( 'competition_number', self.text_competition_number.Value )
        glidercard.str_to_column( 'description', self.text_description.Value )
        glidercard.landing_gear = self.checkbox_gear.Value
        glidercard.winglets = self.checkbox_winglets.Value
        glidercard.glider_type = self.combo_glider_type.CurrentSelection >= 0 and self.glider_type_items[ self.combo_glider_type.CurrentSelection ] or None
        glidercard.pilot = self.combo_pilot.CurrentSelection >= 0 and self.pilot_items[ self.combo_pilot.CurrentSelection ] or None
        glidercard.organization = self.combo_organization.CurrentSelection >= 0 and self.organization_items[ self.combo_organization.CurrentSelection ] or None
        return glidercard
    
    def SetData(self, glidercard=None):
        " SetData(self, glidercard=None) - set form data "
        if glidercard != None:
            self.glidercard = glidercard
            self.text_registration.Value = glidercard.column_as_str('registration')
            self.text_competition_number.Value = glidercard.column_as_str('competition_number')
            self.text_description.Value = glidercard.column_as_str('description')
            self.checkbox_gear.Value = glidercard.landing_gear != None and glidercard.landing_gear or False 
            self.checkbox_winglets.Value = glidercard.winglets !=None and glidercard.winglets or False
            if glidercard.glider_type != None:
                self.combo_glider_type.SetSelection( self.glider_type_items.index( glidercard.glider_type ) )
            if glidercard.pilot != None:
                self.combo_pilot.SetSelection( self.pilot_items.index( glidercard.pilot ) )
            if glidercard.organization != None:
                self.combo_organization.SetSelection( self.organization_items.index( glidercard.organization ) )
            self.__init_photo(glidercard.main_photo)
        else:
            self.__init_photo()
