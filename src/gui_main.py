" GUI - Main window "

from os import remove
from os.path import join, isfile
from shutil import copy

import wx
from wx import GetTranslation as _

import gui_forms
import settings

from sqlalchemy.orm import eagerload

from database import session
from models import GliderCard, Pilot, Organization, GliderType, Photo
from gui_widgets import error_message_dialog
from gui_igchandicap import IgcHandicapList, IgcHandicapForm, GLIDER_TYPE_INSERT_ERROR
from gui_organizations import OrganizationList, OrganizationForm, ORGANIZATION_INSERT_ERROR
from gui_pilots import PilotList, PilotForm, PILOT_INSERT_ERROR

class Main(gui_forms.Main):
    " Main application window "
    def __init__(self, *args, **kwargs):
        " __init__(self, Window parent, int id=-1) "
        gui_forms.Main.__init__(self, *args, **kwargs)
        
        self.__sort_glider_card = 0

        self.split_main.SetSashGravity(0.33)
        self.split_main.SetMinimumPaneSize(375)
        self.SetSize( (900, 700) )

        self.text_find.ShowSearchButton(True)
        self.text_find.ShowCancelButton(True)
        
        # Set grid columns
        self.list_glider_card.InsertColumn(0, _("Nr."), 'competition_number', proportion=1)
        self.list_glider_card.InsertColumn(1, _("Registration"), 'registration', proportion=3)
        self.list_glider_card.InsertColumn(2, _("Glider type"), 'glider_type', proportion=3)
        self.list_glider_card.InsertColumn(3, _("Pilot"), 'pilot', proportion=4)

        # Open data source
        self.BASE_QUERY = session.query( GliderCard ).options( eagerload('pilot') ).options( eagerload('glider_type') )
        self.datasource_glider_card = self.BASE_QUERY.all()

        # Bind events
        self.list_glider_card.Bind(wx.EVT_CONTEXT_MENU, self.__list_glider_card_popup_menu)
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
                finally:
                    self.__set_enabled_disabled()
            except Exception, e:
                session.rollback()
                error_message_dialog( self, _("Glider card delete error"), e )

class GliderCardForm(wx.Dialog):
    " Glider card insert/edit dialog "
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.THICK_FRAME
        wx.Dialog.__init__(self, *args, **kwds)
        
        self.sizer_picture_staticbox = wx.StaticBox(self, -1, _("Photo"))
        self.label_registration = wx.StaticText(self, -1, _("Registration"))
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
                self.photo_fullpath = join( dlg.Directory, dlg.Filename )
                settings.LAST_OPEN_FILE_PATH = dlg.Directory
                self.__show_photo( self.photo_fullpath )
        finally:
            dlg.Destroy()

    def __clear_photo(self, evt):
        " __clear_photo(self, evt) - clear photo event handler "
        if getattr(self, 'photo_fullpath', None) != None:
            self.__photo_changed = True
            self.photo_fullpath = None
            self.__show_empty_photo()
    
    def __show_photo(self, full_path):
        " __show_photo(self, full_path) - load photo file and show it "
        # Create bitmap from file
        image = wx.Image( full_path, type=wx.BITMAP_TYPE_JPEG )
        
        image_w, image_h =  image.GetSize()
        ctrl_w, ctrl_h = self.photo.GetClientSize()
        if image_w > ctrl_w or image_h > ctrl_h:
            # Count thumbnail size
            image_proportion = float(image_w) / image_h
            image_w = ctrl_w
            image_h = int( image_w / image_proportion )
            if image_h > ctrl_h:
                image_h = ctrl_h
                image_w = int( image_h * image_proportion )
            # Scale photo thumbnail
            image.Rescale( image_w, image_h, quality=wx.IMAGE_QUALITY_HIGH )
        # Resize photo thumbnail
        image.Resize( (ctrl_w, ctrl_h), ( (ctrl_w-image_w)/2, (ctrl_h-image_h)/2 ) )

        self.photo.SetBitmap( image.ConvertToBitmap() )
        
    def __init_photo(self, photo=None):
        " __init_photo(self, Photo photo=None) - show photo thumbnail or empty photo "
        self.__photo_changed = False
        if photo == None:
            # Show empty photo
            self.photo_fullpath = None
            self.__show_empty_photo()
        else:
            self.photo_fullpath = photo.full_path
            self.__show_photo(self.photo_fullpath)
        
    def __show_empty_photo(self):
        " __show_empty_photo(self) - if no photo, show show empty photo icon "
        # Create bitmap from file
        image = wx.Image( join(settings.IMAGES_DIR, 'lphoto.png'), type=wx.BITMAP_TYPE_PNG )

        image_w, image_h =  image.GetSize()
        ctrl_w, ctrl_h = self.photo.GetClientSize()
        if image_w > ctrl_w or image_h > ctrl_h:
            # Count thumbnail size
            image_proportion = float(image_w) / image_h
            image_w = ctrl_w
            image_h = int( image_w / image_proportion )
            if image_h > ctrl_h:
                image_h = ctrl_h
                image_w = int( image_h * image_proportion )
            # Scale photo thumbnail
            image.Rescale( image_w, image_h, quality=wx.IMAGE_QUALITY_HIGH )
        # Resize photo thumbnail
        image.Resize( (ctrl_w, ctrl_h), ( (ctrl_w-image_w)/2, (ctrl_h-image_h)/2 ) )

        self.photo.SetBitmap( image.ConvertToBitmap() )
    
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
