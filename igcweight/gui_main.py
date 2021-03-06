"""
GUI - Main window
"""

import os
import locale

from os import remove, system
from os.path import splitext, abspath, dirname
from os.path import join as joinpath
from shutil import copy
from hashlib import md5
from datetime import datetime
from math import fabs

import wx
from wx.lib.multisash import EmptyChild
from wx.html import HtmlEasyPrinting
from wx import GetTranslation as _

from sqlalchemy import or_, desc
from sqlalchemy.orm import eagerload, join

try:
    from mako.template import Template
except ImportError:
    Template = None

from igcweight import settings

from igcweight.database import session
from igcweight.models import (
    GliderCard, Pilot, Organization, GliderType, Photo, DailyWeight)
from igcweight.gui_widgets import (
    error_message_dialog, info_message_dialog, VirtualListCtrl, GetPhotoBitmap)
from igcweight.gui_igchandicap import (
    IgcHandicapList, IgcHandicapForm, GLIDER_TYPE_INSERT_ERROR)
from igcweight.gui_organizations import (
    OrganizationList, OrganizationForm, ORGANIZATION_INSERT_ERROR)
from igcweight.gui_pilots import PilotList, PilotForm, PILOT_INSERT_ERROR
from igcweight.gui_preferences import Preferences
from igcweight.importexport import patternt_tar, Export, Import, CleanDb

_fake_variable_1 = _('Glider card - club class')


class Main(wx.Frame):
    """
    Main application window
    """

    NON_LIFTING_OK = _("Non-lifting parts weight is OK.")
    NON_LIFTING_OVERWEIGHT = _("Non-lifting parts are overweight by %d kg!")
    NON_LIFTING_NO_DATA = _("No data for check non-lifting parts weight.")
    MTOW_OK = _("Maximum takeoff weight is OK.")
    MTOW_OVERWEIGHT = _("Maximum takeoff weight is overweight by %d kg!")
    MTOW_NO_DATA = _("No data for check maximum takeoff weight.")
    SEAT_OK = _("Seat weighting is OK.")
    SEAT_OVERWEIGHT = _("Seat weighting is overweight by %d kg!")
    SEAT_UNDERWEIGHT = _("Seat weighting is underweight by %d kg!")
    SEAT_NO_DATA = _("No data for check seat weighting.")
    REFERENTIAL_OK = _("Referential weight is OK.")
    REFERENTIAL_OVERWEIGHT = _("Referential weight is overweight by %d kg!")
    REFERENTIAL_UNDERWEIGHT = _("Referential weight is underweight by %d kg!")
    REFERENTIAL_NO_DATA = _("No data for check referential weight.")
    COEFFICIENT = _(
        "Competition coefficient is %(coefficient)s at weight %(weight)d kg.")
    COEFFICIENT_NO_DATA = _("No data for count coefficient.")
    TOW_BAR_OK = _("* In the limit")
    TOW_BAR_OVERWEIGHT = _("! Overweight by %d kg")
    TOW_BAR_UNDERWEIGHT = _("! Underweight by %d kg")
    TOW_BAR_UNDERWEIGHT_NO_CLUB = _("* Underweight by %d kg, OK")
    TOW_BAR_NO_DATA = _("? No data")
    NOT_USED = _("No club class, not used")
    COLOR_TEXT = wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOWTEXT)
    COLOR_OK = 'DARK GREEN'
    COLOR_OVERWEIGHT = 'RED'
    COLOR_UNDERWEIGHT = 'ORANGE'
    COLOR_NO_DATA = 'BLUE'

    def __init__(self, *args, **kwds):
        """
        __init__(self, Window parent, int id=-1)
        """

        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.__old_record = None
        self.__current_photo_index = None
        self.__photos = None

        self.split_main = wx.SplitterWindow(
            self, -1, style=wx.SP_3D | wx.SP_BORDER)
        self.panel_card = wx.Panel(self.split_main, -1)
        self.sizer_photo_staticbox = wx.StaticBox(
            self.panel_card, -1, _("Photo"))
        self.panel_gliders = wx.Panel(self.split_main, -1)

        # Menu Bar
        self.main_menu = wx.MenuBar()
        self.menu_file = wx.Menu()
        self.menu_import = wx.MenuItem(
            self.menu_file, wx.NewId(), _("&Import..."),
            _("Import data from archive file"), wx.ITEM_NORMAL)
        self.menu_file.AppendItem(self.menu_import)
        self.menu_export = wx.MenuItem(
            self.menu_file, wx.NewId(), _("&Export..."),
            _("Export data into archive file"), wx.ITEM_NORMAL)
        self.menu_file.AppendItem(self.menu_export)
        self.menu_clean = wx.MenuItem(
            self.menu_file, wx.NewId(), _("&Clean database..."),
            _("Clean old data from database"), wx.ITEM_NORMAL)
        self.menu_file.AppendItem(self.menu_clean)
        self.menu_file.AppendSeparator()
        self.menu_exit = wx.MenuItem(
            self.menu_file, wx.NewId(), _("E&xit\tAlt-F4"),
            _("Exit application"), wx.ITEM_NORMAL)
        self.menu_file.AppendItem(self.menu_exit)
        self.main_menu.Append(self.menu_file, _("&File"))
        self.menu_edit = wx.Menu()
        self.menu_coefficients = wx.MenuItem(
            self.menu_edit, wx.NewId(), _("IGC &handicap list..."),
            _("Edit gliders and IGC handicap list"), wx.ITEM_NORMAL)
        self.menu_edit.AppendItem(self.menu_coefficients)
        self.menu_pilots = wx.MenuItem(
            self.menu_edit, wx.NewId(), _("&Pilots..."),
            _("Edit pilots list"), wx.ITEM_NORMAL)
        self.menu_edit.AppendItem(self.menu_pilots)
        self.menu_organizations = wx.MenuItem(
            self.menu_edit, wx.NewId(), _("&Organizations or countries..."),
            _("Edit organizations or coutries list"), wx.ITEM_NORMAL)
        self.menu_edit.AppendItem(self.menu_organizations)
        self.menu_edit.AppendSeparator()
        self.menu_preferences = wx.MenuItem(
            self.menu_edit, wx.NewId(), _("Pr&eferences..."),
            _("Edit preferences"), wx.ITEM_NORMAL)
        self.menu_edit.AppendItem(self.menu_preferences)
        self.main_menu.Append(self.menu_edit, _("&Edit"))
        self.menu_glider_card = wx.Menu()
        self.menu_glider_card_new = wx.MenuItem(
            self.menu_glider_card, wx.NewId(), _("&New...\tInsert"),
            _("Add new glider"), wx.ITEM_NORMAL)
        self.menu_glider_card.AppendItem(self.menu_glider_card_new)
        self.menu_glider_card_properties = wx.MenuItem(
            self.menu_glider_card, wx.NewId(), _("&Edit..."),
            _("Edit glider properties"), wx.ITEM_NORMAL)
        self.menu_glider_card.AppendItem(self.menu_glider_card_properties)
        self.menu_glider_card_delete = wx.MenuItem(
            self.menu_glider_card, wx.NewId(), _("&Delete"),
            _("Delete glider"), wx.ITEM_NORMAL)
        self.menu_glider_card.AppendItem(self.menu_glider_card_delete)
        self.menu_glider_card.AppendSeparator()
        self.menu_glider_card_find = wx.MenuItem(
            self.menu_glider_card, wx.NewId(), _("&Find\tCtrl+F"),
            _("Find glider"), wx.ITEM_NORMAL)
        self.menu_glider_card.AppendItem(self.menu_glider_card_find)
        self.menu_glider_card.AppendSeparator()
        self.menu_glider_card_show_photo = wx.MenuItem(
            self.menu_glider_card, wx.NewId(), _("&Show photo\tAlt+V"),
            _("Show photo in the external application"), wx.ITEM_NORMAL)
        self.menu_glider_card.AppendItem(self.menu_glider_card_show_photo)
        self.menu_glider_card.AppendSeparator()
        self.menu_glider_card_print = wx.MenuItem(
            self.menu_glider_card, wx.NewId(), _("&Print...\tCtrl+P"),
            _("Print glider card"), wx.ITEM_NORMAL)
        self.menu_glider_card.AppendItem(self.menu_glider_card_print)
        self.menu_glider_card_print_preview = wx.MenuItem(
            self.menu_glider_card, wx.NewId(), _("Print pre&view..."),
            _("Print preview"), wx.ITEM_NORMAL)
        self.menu_glider_card.AppendItem(self.menu_glider_card_print_preview)
        self.main_menu.Append(self.menu_glider_card, _("&Glider card"))
        self.menu_daily_weight = wx.Menu()
        self.menu_daily_weight_new = wx.MenuItem(
            self.menu_daily_weight, wx.NewId(), _("&New...\tCtrl+Insert"),
            _("Add new daily weight"), wx.ITEM_NORMAL)
        self.menu_daily_weight.AppendItem(self.menu_daily_weight_new)
        self.menu_daily_weight_properties = wx.MenuItem(
            self.menu_daily_weight, wx.NewId(), _("&Edit..."),
            _("Edit daily weight properties"), wx.ITEM_NORMAL)
        self.menu_daily_weight.AppendItem(self.menu_daily_weight_properties)
        self.menu_daily_weight_delete = wx.MenuItem(
            self.menu_daily_weight, wx.NewId(), _("&Delete"),
            _("Delete daily weight"), wx.ITEM_NORMAL)
        self.menu_daily_weight.AppendItem(self.menu_daily_weight_delete)
        self.main_menu.Append(self.menu_daily_weight, _("&Daily weight"))
        self.menu_help = wx.Menu()
        self.menu_about = wx.MenuItem(
            self.menu_help, wx.NewId(), _("&About\tF1"),
            _("About this application"), wx.ITEM_NORMAL)
        self.menu_help.AppendItem(self.menu_about)
        self.main_menu.Append(self.menu_help, _("&Help"))
        self.SetMenuBar(self.main_menu)

        # Status bar
        self.statusbar = self.CreateStatusBar(1, wx.ST_SIZEGRIP)

        # Gliders list
        find_choices = (
            _('Competition number'),
            _('Registration'),
            _('Glider type'),
            _('Surname'),
        )
        self.text_find = wx.SearchCtrl(
            self.panel_gliders, -1, style=wx.TE_PROCESS_ENTER)
        self.combo_find = wx.ComboBox(
            self.panel_gliders, -1, choices=find_choices, style=wx.CB_READONLY)
        self.list_glider_card = VirtualListCtrl(self.panel_gliders, -1)
        self.button_glider_card_new = wx.Button(
            self.panel_gliders, wx.ID_NEW, "")
        self.button_glider_card_properties = wx.Button(
            self.panel_gliders, wx.ID_EDIT, "")
        self.button_glider_card_delete = wx.Button(
            self.panel_gliders, wx.ID_DELETE, "")

        # Glider card
        self.label_registration = wx.StaticText(
            self.panel_card, -1, _("Registration"))
        self.label_competition_number = wx.StaticText(
            self.panel_card, -1, _("Competition number"))
        self.text_registration = wx.StaticText(self.panel_card, -1, "")
        self.text_competition_number = wx.StaticText(self.panel_card, -1, "")
        self.label_glider_type = wx.StaticText(
            self.panel_card, -1, _("Glider type"))
        self.text_glider_type = wx.StaticText(self.panel_card, -1, "")
        self.label_glider_class = wx.StaticText(
            self.panel_card, -1, _("Glider class"))
        self.text_glider_class = wx.StaticText(self.panel_card, -1, "")
        self.label_pilot = wx.StaticText(self.panel_card, -1, _("Pilot"))
        self.text_pilot = wx.StaticText(self.panel_card, -1, "")
        self.label_organization = wx.StaticText(
            self.panel_card, -1, _("Organization or country"))
        self.text_organization = wx.StaticText(self.panel_card, -1, "")
        self.label_winglets = wx.StaticText(self.panel_card, -1, _("Winglets"))
        self.label_landing_gear = wx.StaticText(
            self.panel_card, -1, _("Landing gear"))
        self.text_winglets = wx.StaticText(self.panel_card, -1, "")
        self.text_landing_gear = wx.StaticText(self.panel_card, -1, "")
        # Photo
        self.photo = wx.StaticBitmap(self.panel_card, -1)
        self.button_photo_prev = wx.Button(
            self.panel_card, wx.NewId(), "<", style=wx.BU_EXACTFIT)
        self.button_photo_show = wx.Button(self.panel_card, wx.ID_ZOOM_IN, "")
        self.button_photo_next = wx.Button(
            self.panel_card, wx.NewId(), ">", style=wx.BU_EXACTFIT)
        # Certified weights
        self.label_certified_weights = wx.StaticText(
            self.panel_card, -1, _("Certified weights:"))
        self.label_non_lifting_weight = wx.StaticText(
            self.panel_card, -1, _("Non-lifting parts"))
        self.text_non_lifting_weight = wx.StaticText(self.panel_card, -1, "")
        self.label_empty_weight = wx.StaticText(
            self.panel_card, -1, _("Empty glider"))
        self.text_empty_weight = wx.StaticText(self.panel_card, -1, "")
        self.label_seat_min_weight = wx.StaticText(
            self.panel_card, -1, _("Seat min."))
        self.text_seat_min_weight = wx.StaticText(self.panel_card, -1, "")
        self.label_seat_max_weight = wx.StaticText(
            self.panel_card, -1, _("Seat max."))
        self.text_seat_max_weight = wx.StaticText(self.panel_card, -1, "")
        # Measured weights
        self.label_measured_weights = wx.StaticText(
            self.panel_card, -1, _("Measured weights:"))
        self.label_glider_weight = wx.StaticText(
            self.panel_card, -1, _("Glider weight"))
        self.text_glider_weight = wx.StaticText(self.panel_card, -1, "")
        self.label_pilot_weight = wx.StaticText(
            self.panel_card, -1, _("Pilot weight"))
        self.text_pilot_weight = wx.StaticText(self.panel_card, -1, "")
        self.label_tow_bar_weight = wx.StaticText(
            self.panel_card, -1, _("Tow bar weight"))
        self.text_tow_bar_weight = wx.StaticText(self.panel_card, -1, "")
        self.text_non_lifting_status = wx.StaticText(
            self.panel_card, -1, self.NON_LIFTING_NO_DATA)
        self.text_mtow_status = wx.StaticText(
            self.panel_card, -1, self.MTOW_NO_DATA)
        self.text_seat_status = wx.StaticText(
            self.panel_card, -1, self.SEAT_NO_DATA)
        self.text_referential_status = wx.StaticText(
            self.panel_card, -1, self.REFERENTIAL_NO_DATA)
        self.text_coefficient_status = wx.StaticText(
            self.panel_card, -1, self.COEFFICIENT_NO_DATA)
        # Daily weights
        self.label_daily_weight = wx.StaticText(
            self.panel_card, -1, _("Daily tow bar weight"))
        self.list_daily_weight = VirtualListCtrl(self.panel_card, -1)
        self.list_daily_weight.GetItemTextMethod = (
            self.__list_daily_weigh_get_item_text)
        self.list_daily_weight.GetItemAttrMethod = (
            self.__list_daily_weigh_get_item_attr)
        self.button_daily_weight_new = wx.Button(
            self.panel_card, wx.ID_NEW, "")
        self.button_daily_weight_properties = wx.Button(
            self.panel_card, wx.ID_EDIT, "")
        self.button_daily_weight_delete = wx.Button(
            self.panel_card, wx.ID_DELETE, "")
        # Print button
        self.button_glider_card_print = wx.Button(
            self.panel_card, wx.ID_PRINT, "")

        self.__set_properties()
        self.__do_layout()

        self.__sort_glider_card = 0
        self.__filtered = False

        # Set grid columns
        self.list_glider_card.InsertColumn(
            0, _("Nr."), 'competition_number', proportion=1)
        self.list_glider_card.InsertColumn(
            1, _("Registration"), 'registration', proportion=3)
        self.list_glider_card.InsertColumn(
            2, _("Glider type"), 'glider_type', proportion=3)
        self.list_glider_card.InsertColumn(
            3, _("Pilot"), 'pilot', proportion=4)

        self.list_daily_weight.InsertColumn(
            0, _("Date"), 'date', proportion=3)
        self.list_daily_weight.InsertColumn(
            1, _("Weight"), 'tow_bar_weight', proportion=2)
        self.list_daily_weight.InsertColumn(
            2, _("Status"), 'status', proportion=4)

        # Open data sources
        self.BASE_QUERY = session.query(
            GliderCard
        ).join(
            (Pilot, GliderCard.pilot_id == Pilot.id),
            (GliderType, GliderCard.glider_type_id == GliderType.id)
        )
        self.datasource_glider_card = self.BASE_QUERY.all()

        # Bind events
        self.Bind(
            wx.EVT_LIST_ITEM_SELECTED, self.GliderCardChange,
            self.list_glider_card)
        self.Bind(
            wx.EVT_LIST_COL_CLICK, self.__sort_glider_card_list,
            self.list_glider_card)
        self.Bind(wx.EVT_CLOSE, self.Exit, self)
        self.Bind(wx.EVT_MENU, self.Import, self.menu_import)
        self.Bind(wx.EVT_MENU, self.Export, self.menu_export)
        self.Bind(wx.EVT_MENU, self.CleanDb, self.menu_clean)
        self.Bind(wx.EVT_MENU, self.Exit, self.menu_exit)
        self.Bind(wx.EVT_MENU, self.About, self.menu_about)
        self.Bind(wx.EVT_MENU, self.IgcHandicapList, self.menu_coefficients)
        self.Bind(wx.EVT_MENU, self.Pilots, self.menu_pilots)
        self.Bind(wx.EVT_MENU, self.Organizations, self.menu_organizations)
        self.Bind(wx.EVT_MENU, self.Preferences, self.menu_preferences)
        self.Bind(wx.EVT_MENU, self.GliderCardNew, self.menu_glider_card_new)
        self.Bind(
            wx.EVT_MENU, self.GliderCardProperties,
            self.menu_glider_card_properties)
        self.Bind(
            wx.EVT_MENU, self.GliderCardDelete, self.menu_glider_card_delete)
        self.Bind(wx.EVT_MENU, self.GliderCardFind, self.menu_glider_card_find)
        self.Bind(
            wx.EVT_MENU, self.GliderCardPrint, self.menu_glider_card_print)
        self.Bind(
            wx.EVT_MENU, self.GliderCardPrintPreview,
            self.menu_glider_card_print_preview)
        self.Bind(
            wx.EVT_MENU, self.ShowPhoto, self.menu_glider_card_show_photo)
        self.Bind(wx.EVT_MENU, self.DailyWeightNew, self.menu_daily_weight_new)
        self.Bind(
            wx.EVT_MENU, self.DailyWeightProperties,
            self.menu_daily_weight_properties)
        self.Bind(
            wx.EVT_MENU, self.DailyWeightDelete, self.menu_daily_weight_delete)
        self.Bind(wx.EVT_BUTTON, self.PrevPhoto, self.button_photo_prev)
        self.Bind(wx.EVT_BUTTON, self.ShowPhoto, self.button_photo_show)
        self.Bind(wx.EVT_BUTTON, self.NextPhoto, self.button_photo_next)
        self.Bind(wx.EVT_TEXT_ENTER, self.SearchGliderCard, self.text_find)
        self.Bind(
            wx.EVT_SEARCHCTRL_SEARCH_BTN,
            self.SearchGliderCard, self.text_find)
        self.Bind(
            wx.EVT_SEARCHCTRL_CANCEL_BTN, self.AllGliderCard, self.text_find)
        self.list_glider_card.Bind(
            wx.EVT_CONTEXT_MENU, self.__list_glider_card_popup_menu)
        self.list_glider_card.Bind(
            wx.EVT_LEFT_DCLICK, self.GliderCardProperties)
        self.list_daily_weight.Bind(
            wx.EVT_CONTEXT_MENU, self.__list_daily_weight_popup_menu)
        self.list_daily_weight.Bind(
            wx.EVT_LEFT_DCLICK, self.DailyWeightProperties)
        self.button_glider_card_new.Bind(wx.EVT_BUTTON, self.GliderCardNew)
        self.button_glider_card_properties.Bind(
            wx.EVT_BUTTON, self.GliderCardProperties)
        self.button_glider_card_delete.Bind(
            wx.EVT_BUTTON, self.GliderCardDelete)
        self.button_glider_card_print.Bind(wx.EVT_BUTTON, self.GliderCardPrint)
        self.button_daily_weight_new.Bind(wx.EVT_BUTTON, self.DailyWeightNew)
        self.button_daily_weight_properties.Bind(
            wx.EVT_BUTTON, self.DailyWeightProperties)
        self.button_daily_weight_delete.Bind(
            wx.EVT_BUTTON, self.DailyWeightDelete)

    def __set_properties(self):
        self.SetTitle(_("IGC Weight"))

        self.statusbar.SetStatusWidths([-1])
        statusbar_fields = [""]
        for i in range(len(statusbar_fields)):
            self.statusbar.SetStatusText(statusbar_fields[i], i)

        self.list_glider_card.SetFocus()

        self.text_find.ShowSearchButton(True)
        self.text_find.ShowCancelButton(True)
        self.combo_find.SetSelection(0)

        self.button_glider_card_new.SetToolTipString(_("Add new glider"))
        self.button_glider_card_new.Enable(False)
        self.button_glider_card_properties.SetToolTipString(
            _("Edit glider properties"))
        self.button_glider_card_properties.Enable(False)
        self.button_glider_card_delete.SetToolTipString(_("Delete glider"))
        self.button_glider_card_delete.Enable(False)
        self.button_photo_prev.SetToolTipString(_("Previous photo"))
        self.button_photo_show.SetToolTipString(_("Show photo"))
        self.button_photo_next.SetToolTipString(_("Next photo"))
        self.button_daily_weight_new.SetToolTipString(
            _("Add new daily weight"))
        self.button_daily_weight_new.Enable(False)
        self.button_daily_weight_properties.SetToolTipString(
            _("Edit daily weight properties"))
        self.button_daily_weight_properties.Enable(False)
        self.button_daily_weight_delete.SetToolTipString(
            _("Delete daily weight"))
        self.button_daily_weight_delete.Enable(False)
        self.button_glider_card_print.SetToolTipString(
            _("Print glider card"))
        self.button_glider_card_print.Enable(False)

        fontbold = self.label_certified_weights.GetFont()
        fontbold.SetWeight(wx.FONTWEIGHT_BOLD)
        self.fontbold = fontbold
        self.fontnormal = self.label_certified_weights.GetFont()

        self.text_registration.SetFont(
            wx.Font(20, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.text_competition_number.SetFont(
            wx.Font(20, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.text_glider_type.SetFont(
            wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.text_glider_class.SetFont(
            wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.text_pilot.SetFont(
            wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.text_organization.SetFont(
            wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.text_winglets.SetFont(
            wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.text_landing_gear.SetFont(
            wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.label_certified_weights.SetFont(fontbold)
        self.text_non_lifting_weight.SetFont(fontbold)
        self.text_empty_weight.SetFont(fontbold)
        self.text_seat_min_weight.SetFont(fontbold)
        self.text_seat_max_weight.SetFont(fontbold)
        self.label_measured_weights.SetFont(fontbold)
        self.text_glider_weight.SetFont(fontbold)
        self.text_pilot_weight.SetFont(fontbold)
        self.text_tow_bar_weight.SetFont(fontbold)
        self.label_daily_weight.SetFont(fontbold)

        self.photo.SetMinSize((180, -1))
        self.split_main.SetSashGravity(0.33)
        self.split_main.SetMinimumPaneSize(375)

    def __do_layout(self):
        self.split_main.SplitVertically(self.panel_gliders, self.panel_card)

        # Glider buttons sizer
        sizer_gliders_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_gliders_buttons.Add(
            self.button_glider_card_new, 1, wx.RIGHT, 2)
        sizer_gliders_buttons.Add(
            self.button_glider_card_properties, 1, wx.LEFT | wx.RIGHT, 2)
        sizer_gliders_buttons.Add(
            self.button_glider_card_delete, 1, wx.LEFT, 2)
        # Glider (left panel) sizer
        sizer_find = wx.BoxSizer(wx.HORIZONTAL)
        sizer_find.Add(self.text_find, 3, wx.RIGHT | wx.EXPAND, 2)
        sizer_find.Add(self.combo_find, 2, wx.LEFT | wx.EXPAND, 2)
        # Glider (left panel) sizer
        sizer_gliders = wx.BoxSizer(wx.VERTICAL)
        sizer_gliders.Add(
            sizer_find, 0, wx.LEFT | wx.TOP | wx.EXPAND, 4)
        sizer_gliders.Add(
            self.list_glider_card, 1, wx.LEFT | wx.TOP | wx.BOTTOM | wx.EXPAND,
            4)
        sizer_gliders.Add(
            sizer_gliders_buttons, 0, wx.LEFT | wx.BOTTOM | wx.EXPAND, 4)
        self.panel_gliders.SetSizer(sizer_gliders)

        # Glider card base sizer
        sizer_card_base = wx.GridBagSizer(0, 0)
        sizer_card_base.Add(
            self.label_competition_number, (0, 0), (1, 1),
            wx.LEFT | wx.BOTTOM | wx.EXPAND, 2)
        sizer_card_base.Add(
            self.label_registration, (0, 1), (1, 1),
            wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)
        sizer_card_base.Add(
            self.text_competition_number, (1, 0), (1, 1),
            wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)
        sizer_card_base.Add(
            self.text_registration, (1, 1), (1, 1),
            wx.LEFT | wx.BOTTOM | wx.EXPAND, 2)
        sizer_card_base.Add(
            self.label_glider_type, (2, 0), (1, 1), wx.BOTTOM | wx.EXPAND, 2)
        sizer_card_base.Add(
            self.label_glider_class, (2, 1), (1, 1), wx.BOTTOM | wx.EXPAND, 2)
        sizer_card_base.Add(
            self.text_glider_type, (3, 0), (1, 1), wx.BOTTOM | wx.EXPAND, 2)
        sizer_card_base.Add(
            self.text_glider_class, (3, 1), (1, 1), wx.BOTTOM | wx.EXPAND, 2)
        sizer_card_base.Add(
            self.label_pilot, (4, 0), (1, 2), wx.BOTTOM | wx.EXPAND, 2)
        sizer_card_base.Add(
            self.text_pilot, (5, 0), (1, 2), wx.BOTTOM | wx.EXPAND, 2)
        sizer_card_base.Add(
            self.label_organization, (6, 0), (1, 2), wx.BOTTOM | wx.EXPAND, 2)
        sizer_card_base.Add(
            self.text_organization, (7, 0), (1, 2),
            wx.BOTTOM | wx.EXPAND, 2)
        sizer_card_base.Add(
            self.label_landing_gear, (8, 0), (1, 1),
            wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)
        sizer_card_base.Add(
            self.label_winglets, (8, 1), (1, 1),
            wx.LEFT | wx.BOTTOM | wx.EXPAND, 2)
        sizer_card_base.Add(
            self.text_landing_gear, (9, 0), (1, 1),
            wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)
        sizer_card_base.Add(
            self.text_winglets, (9, 1), (1, 1),
            wx.LEFT | wx.BOTTOM | wx.EXPAND, 2)
        sizer_card_base.Add(
            wx.StaticLine(self.panel_card), (10, 0), (1, 2),
            wx.TOP | wx.EXPAND, 4)
        sizer_card_base.AddGrowableRow(9)
        sizer_card_base.AddGrowableCol(0, 1)
        sizer_card_base.AddGrowableCol(1, 1)
        # Photo sizer
        sizer_photo_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_photo_buttons.Add(
            self.button_photo_prev, 0, wx.RIGHT | wx.EXPAND, 2)
        sizer_photo_buttons.Add(
            self.button_photo_show, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 2)
        sizer_photo_buttons.Add(
            self.button_photo_next, 0, wx.LEFT | wx.EXPAND, 2)
        sizer_photo = wx.StaticBoxSizer(
            self.sizer_photo_staticbox, wx.VERTICAL)
        sizer_photo.Add(self.photo, 1, wx.ALL | wx.EXPAND, 4)
        sizer_photo.Add(sizer_photo_buttons, 0, wx.ALL | wx.EXPAND, 4)
        # Card head (top) sizer
        sizer_card_head = wx.BoxSizer(wx.HORIZONTAL)
        sizer_card_head.Add(
            sizer_card_base, 1, wx.LEFT | wx.TOP | wx.BOTTOM | wx.EXPAND, 4)
        sizer_card_head.Add(sizer_photo, 0, wx.ALL | wx.EXPAND, 4)
        # Certified weights sizer
        sizer_weights = wx.GridBagSizer(2, 2)
        sizer_weights.Add(
            self.label_certified_weights, (0, 0), (1, 4),
            wx.BOTTOM | wx.EXPAND, 2)
        sizer_weights.Add(
            self.label_non_lifting_weight, (1, 0), (1, 1),
            wx.RIGHT | wx.EXPAND, 2)
        sizer_weights.Add(
            self.label_empty_weight, (1, 1), (1, 1),
            wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_weights.Add(
            self.label_seat_min_weight, (1, 2), (1, 1),
            wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_weights.Add(
            self.label_seat_max_weight, (1, 3), (1, 1),
            wx.LEFT | wx.EXPAND, 2)
        sizer_weights.Add(
            self.text_non_lifting_weight, (2, 0), (1, 1),
            wx.RIGHT | wx.EXPAND, 2)
        sizer_weights.Add(
            self.text_empty_weight, (2, 1), (1, 1),
            wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_weights.Add(
            self.text_seat_min_weight, (2, 2), (1, 1),
            wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_weights.Add(
            self.text_seat_max_weight, (2, 3), (1, 1), wx.LEFT | wx.EXPAND, 2)
        sizer_weights.Add(
            wx.StaticLine(self.panel_card), (3, 0), (1, 4),
            wx.TOP | wx.BOTTOM | wx.EXPAND, 2)
        sizer_weights.Add(
            self.label_measured_weights, (4, 0), (1, 4),
            wx.BOTTOM | wx.EXPAND, 2)
        sizer_weights.Add(
            self.label_glider_weight, (5, 0), (1, 1), wx.RIGHT | wx.EXPAND, 2)
        sizer_weights.Add(
            self.label_pilot_weight, (5, 1), (1, 1),
            wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_weights.Add(
            self.label_tow_bar_weight, (5, 2), (1, 2),
            wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_weights.Add(
            self.text_glider_weight, (6, 0), (1, 1), wx.RIGHT | wx.EXPAND, 2)
        sizer_weights.Add(
            self.text_pilot_weight, (6, 1), (1, 1),
            wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_weights.Add(
            self.text_tow_bar_weight, (6, 2), (1, 2),
            wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_weights.Add(
            wx.StaticLine(self.panel_card), (7, 0), (1, 4),
            wx.TOP | wx.BOTTOM | wx.EXPAND, 2)
        sizer_weights.Add(
            self.text_non_lifting_status, (8, 0), (1, 4),
            wx.BOTTOM | wx.EXPAND, 2)
        sizer_weights.Add(
            self.text_mtow_status, (9, 0), (1, 4), wx.BOTTOM | wx.EXPAND, 2)
        sizer_weights.Add(
            self.text_seat_status, (10, 0), (1, 4), wx.BOTTOM | wx.EXPAND, 2)
        sizer_weights.Add(
            self.text_referential_status, (11, 0), (1, 4),
            wx.BOTTOM | wx.EXPAND, 2)
        sizer_weights.Add(
            self.text_coefficient_status, (12, 0), (1, 4),
            wx.BOTTOM | wx.EXPAND, 2)
        sizer_weights.Add(
            wx.StaticLine(self.panel_card), (13, 0), (1, 4),
            wx.TOP | wx.BOTTOM | wx.EXPAND, 2)
        sizer_weights.AddGrowableCol(0, 1)
        sizer_weights.AddGrowableCol(1, 1)
        sizer_weights.AddGrowableCol(2, 1)
        sizer_weights.AddGrowableCol(3, 1)
        # Daily weight sizer
        sizer_daily_weight = wx.GridBagSizer(2, 2)
        sizer_daily_weight.Add(
            self.label_daily_weight, (0, 0), (1, 5), wx.EXPAND, 2)
        sizer_daily_weight.Add(
            self.list_daily_weight, (1, 0), (1, 5), wx.BOTTOM | wx.EXPAND, 2)
        sizer_daily_weight.Add(
            self.button_daily_weight_new, (2, 0), (1, 1), wx.EXPAND, 2)
        sizer_daily_weight.Add(
            self.button_daily_weight_properties, (2, 1), (1, 1), wx.EXPAND, 2)
        sizer_daily_weight.Add(
            self.button_daily_weight_delete, (2, 2), (1, 1), wx.EXPAND, 2)
        sizer_daily_weight.Add(
            EmptyChild(self.panel_card), (2, 3), (1, 1),
            wx.EXPAND | wx.LEFT | wx.RIGHT, 0)
        sizer_daily_weight.Add(
            self.button_glider_card_print, (2, 4), (1, 1), wx.EXPAND, 2)
        sizer_daily_weight.AddGrowableCol(0, 1)
        sizer_daily_weight.AddGrowableCol(1, 1)
        sizer_daily_weight.AddGrowableCol(2, 1)
        sizer_daily_weight.AddGrowableCol(4, 1)
        sizer_daily_weight.AddGrowableRow(1, 1)
        # Card sizer
        sizer_card = wx.BoxSizer(wx.VERTICAL)
        sizer_card.Add(sizer_card_head, 0, wx.EXPAND, 0)
        sizer_card.Add(
            sizer_weights, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 4)
        sizer_card.Add(sizer_daily_weight, 1, wx.ALL | wx.EXPAND, 4)
        self.panel_card.SetSizer(sizer_card)
        # Main sizer
        sizer_main = wx.BoxSizer(wx.HORIZONTAL)
        sizer_main.Add(self.split_main, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_main)

        sizer_main.Fit(self)
        self.Layout()
        self.SetSize((950, 725))
        self.split_main.SetSashPosition(375)

    def get_datasource_glider_card(self):
        """
        datasource_glider_card(self) -> list of db items (SQLAlchemy query)
        """
        return getattr(self.list_glider_card, 'datasource', None)

    def set_datasource_glider_card(self, value):
        """
        datasource_glider_card(self, list value) - set datasource, value is
        SQLAlchemy query
        """
        self.list_glider_card.datasource = value
        if value is not None:
            count = len(self.datasource_glider_card)
            self.list_glider_card.SetItemCount(count)
            if count > 0:
                self.SortGliderCardList(self.__sort_glider_card)
                self.list_glider_card.Select(0)
                self.list_glider_card.Focus(0)
        else:
            self.list_glider_card.SetItemCount(0)
        self.__set_enabled_disabled()
        self.RefreshGliderCard()
    datasource_glider_card = property(
        get_datasource_glider_card, set_datasource_glider_card)

    def __set_enabled_disabled(self):
        """
        __set_enabled_disabled(self) - enable or disable controls
        """
        if self.datasource_glider_card is not None:
            glider_card_new = True
            count = len(self.datasource_glider_card)
            if count > 0 and self.list_glider_card.current_item:
                glider_card_properties = True
                glider_card_delete = True
            else:
                glider_card_properties = False
                glider_card_delete = False
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

    def __set_enabled_disabled_daily(self):
        """
        __set_enabled_disabled_daily(self) - enable or disable daily
        weight controls
        """
        datasource = getattr(self.list_daily_weight, 'datasource', None)
        if datasource is not None:
            daily_weight_new = True
            glider_card_print = True
            count = len(datasource)
            if count > 0 and self.list_glider_card.current_item:
                daily_weight_properties = True
                daily_weight_delete = True
            else:
                daily_weight_properties = False
                daily_weight_delete = False
        else:
            daily_weight_new = False
            daily_weight_properties = False
            daily_weight_delete = False
            glider_card_print = False

        self.button_daily_weight_new.Enable(daily_weight_new)
        self.menu_daily_weight_new.Enable(daily_weight_new)
        self.button_daily_weight_properties.Enable(daily_weight_properties)
        self.menu_daily_weight_properties.Enable(daily_weight_properties)
        self.button_daily_weight_delete.Enable(daily_weight_delete)
        self.menu_daily_weight_delete.Enable(daily_weight_delete)
        self.menu_glider_card_print.Enable(glider_card_print)
        self.menu_glider_card_print_preview.Enable(glider_card_print)
        self.button_glider_card_print.Enable(glider_card_print)

    def __list_glider_card_popup_menu(self, evt):
        """
        __list_glider_popup_menu(self, Event evt) - show pop-up menu
        """
        pos = evt.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self.menu_glider_card, pos)

    def __list_daily_weight_popup_menu(self, evt):
        """
        __list_daily_weight_menu(self, Event evt) - show pop-up menu
        """
        pos = evt.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self.menu_daily_weight, pos)

    def __sort_glider_card_list(self, evt):
        """
        __sort_glider_card(self, evt) - sort glider cards, left-click
        column tile event handler
        """
        self.__sort_glider_card = evt.m_col
        self.SortGliderCardList(self.__sort_glider_card)

    def __set_status_label_data(self, control, colour, text, *args):
        """
        __set_status_label_data(self, control, colour, text, *args) - set
        wx.StaticText text and colour
        """
        args_len = len(args)
        if args_len > 1:
            params = args
        elif args_len == 1:
            params = args[0]
        else:
            params = ()
        control.SetLabel(text % params)
        control.SetForegroundColour(colour)

    def __list_daily_weigh_get_item_text(self, item, colname):
        """
        __list_daily_weigh_get_item_text(self, int item, str colname) -> str
        - get column data as text
        """
        record = self.list_glider_card.current_item
        daily_weight = record.daily_weight[item]

        if colname == 'status':
            difference = daily_weight.tow_bar_difference
            if difference is None:
                return self.TOW_BAR_NO_DATA
            difference_abs = fabs(difference)
            if difference_abs <= settings.configuration.allowed_difference:
                return self.TOW_BAR_OK
            elif difference > 0:
                return self.TOW_BAR_OVERWEIGHT % difference_abs
            elif difference < 0:
                t = (
                    self.TOW_BAR_UNDERWEIGHT if record.glider_type.club_class
                    else self.TOW_BAR_UNDERWEIGHT_NO_CLUB)
                return t % difference_abs
        else:
            return daily_weight.column_as_str(colname)

    def __list_daily_weigh_get_item_attr(self, item):
        """
        __list_daily_weigh_get_item_text(self, int item, str colname) -> str
        - get column data as text
        """
        record = self.list_glider_card.current_item
        daily_weight = record.daily_weight[item]
        difference = daily_weight.tow_bar_difference

        if difference is None:
            return wx.ListItemAttr(colText=self.COLOR_NO_DATA)
        difference_abs = fabs(difference)
        if difference_abs <= settings.configuration.allowed_difference:
            return wx.ListItemAttr(colText=self.COLOR_OK)
        elif difference > 0:
            return wx.ListItemAttr(colText=self.COLOR_OVERWEIGHT)
        elif difference < 0:
            c = (
                self.COLOR_OVERWEIGHT if record.glider_type.club_class
                else self.COLOR_OK)
            return wx.ListItemAttr(colText=c)

    def SortGliderCardList(self, col):
        """
        __sort_glider_card(self, evt) - sort glider cards, left-click column
        tile event handler
        """
        if self.datasource_glider_card is not None:
            count = len(self.datasource_glider_card)
            if count > 0:
                colname = self.list_glider_card.GetColumnFieldName(col)
                current_item = self.list_glider_card.current_item
                self.list_glider_card.SetItemCount(0)
                self.datasource_glider_card.sort(
                    lambda a, b: locale.strcoll(
                        a.column_as_str(colname), b.column_as_str(colname)
                    )
                )
                if current_item is None:
                    i = 0
                else:
                    i = self.datasource_glider_card.index(current_item)
                self.list_glider_card.SetItemCount(count)
                self.list_glider_card.Select(i)
                self.list_glider_card.Focus(i)

    def Import(self, evt):
        """
        Import(self, Event evt) - import data from archive file
        """
        try:
            dlg = wx.FileDialog(
                self, defaultDir=settings.USER_DIR, message=_("Import data"),
                wildcard=_("TAR files")+" (*.tar)|*.tar;*.TAR",
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
            try:
                if dlg.ShowModal() == wx.ID_OK:
                    self.datasource_glider_card = None
                    try:
                        fullpath = abspath(dlg.GetPath())
                        Import(fullpath)
                        info_message_dialog(
                            self, _("Data were succesfully imported"))
                    finally:
                        self.datasource_glider_card = self.BASE_QUERY.all()
            finally:
                dlg.Destroy()
        except Exception, e:
            error_message_dialog(self, _("Import data error"), e)
            if settings.DEBUG:
                raise

    def Export(self, evt):
        """
        Export(self, Event evt) - export data into archive file
        """
        try:
            dlg = wx.FileDialog(
                self, defaultDir=settings.USER_DIR, message=_("Export data"),
                wildcard=_("TAR files")+" (*.tar)|*.tar;*.TAR",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            try:
                if dlg.ShowModal() == wx.ID_OK:
                    fullpath = abspath(dlg.GetPath())
                    if not patternt_tar.search(fullpath):
                        fullpath = "%s.tar" % fullpath
                    Export(fullpath)
                    info_message_dialog(
                        self, _("Data were succesfully exported"))
            finally:
                dlg.Destroy()
        except Exception, e:
            error_message_dialog(self, _("Export data error"), e)
            if settings.DEBUG:
                raise

    def CleanDb(self, evt):
        """
        CleanDb(self, Event evt) - clean old data from database
        """
        dlg = wx.MessageDialog(self, _(
            "Do you really want clean database?\n\nWARNING! This option is "
            "undoable! Backup your data before database cleaning!"),
            _("Clean database?"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        try:
            if dlg.ShowModal() != wx.ID_YES:
                return
        finally:
            dlg.Destroy()

        dlg = CleanDatabaseForm(self)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                models = []

                if dlg.cb_daily_weights.Value:
                    models.append(DailyWeight)
                if dlg.cb_photos.Value:
                    models.append(Photo)
                if dlg.cb_glider_cards.Value:
                    models.append(GliderCard)
                if dlg.cb_organizations.Value:
                    models.append(Organization)
                if dlg.cb_pilots.Value:
                    models.append(Pilot)
                if dlg.cb_igc_handicaps.Value:
                    models.append(GliderType)

                if (
                        dlg.cb_measured_weights.Value and
                        not dlg.cb_glider_cards.Value):
                    measured_weights = True
                else:
                    measured_weights = False

                CleanDb(models, dlg.cb_preferences.Value, measured_weights)

                self.list_glider_card.SetItemCount(0)
                self.datasource_glider_card = self.BASE_QUERY.all()
                self.RefreshGliderCard()
        finally:
            dlg.Destroy()

    def Exit(self, evt=None):
        """
        Exit(self, Event evt=None) - exit application event handler
        """
        app = wx.GetApp()
        app.Exit()

    def About(self, evt=None):
        """
        About(self, Event evt=None) - show about dialog window event handler
        """
        about = wx.AboutDialogInfo()
        about.SetName("IGC Weight")
        about.SetDescription(_("IGC procedures for handicapped classes"))
        about.SetVersion(settings.VERSION)
        about.SetCopyright(_("Copyright (c) 2009 - 2017, Jan Seifert"))
        about.SetLicence("""BSD License 2.0

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.

    * Neither the name of the author nor the names of its contributors
      may be used to endorse or promote products derived from this
      software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL COPYRIGHT HOLDER BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.""")
        about.SetDevelopers(("Jan Seifert, jan.seifert@fotkyzcest.net",))
        about.SetWebSite("https://github.com/seifert/igcweight")
        wx.AboutBox(about)

    def IgcHandicapList(self, evt=None):
        """
        IgcHandicapList(self, Event evt=None) - open edit IGC handicap list
        window event handler
        """
        dlg = IgcHandicapList(self)
        try:
            dlg.ShowModal()
            self.RefreshGliderCard()
        finally:
            dlg.Destroy()

    def Pilots(self, evt=None):
        """
        Pilots(self, Event evt=None) - open edit pilots list window
        event handler
        """
        dlg = PilotList(self)
        try:
            dlg.ShowModal()
            self.RefreshGliderCard()
        finally:
            dlg.Destroy()

    def Organizations(self, evt=None):
        """
        Organizations(self, Event evt=None) - open edit organizations list
        window event handler
        """
        dlg = OrganizationList(self)
        try:
            dlg.ShowModal()
            self.RefreshGliderCard()
        finally:
            dlg.Destroy()

    def Preferences(self, evt=None):
        """
        Preferences(self, Event evt=None) - open preferences window
        event handler
        """
        dlg = Preferences(self)
        try:
            settings.configuration.read()
            dlg.gear_handicap = settings.configuration.gear_handicap
            dlg.winglets_handicap = settings.configuration.winglets_handicap
            dlg.overweight_handicap = (
                settings.configuration.overweight_handicap)
            dlg.overweight_step = settings.configuration.overweight_step
            dlg.underweight_handicap = (
                settings.configuration.underweight_handicap)
            dlg.underweight_step = settings.configuration.underweight_step
            dlg.allowed_difference = settings.configuration.allowed_difference
            while True:
                try:
                    if dlg.ShowModal() == wx.ID_OK:
                        settings.configuration.set_gear_handicap(
                            dlg.gear_handicap)
                        settings.configuration.set_winglets_handicap(
                            dlg.winglets_handicap)
                        settings.configuration.set_overweight_handicap(
                            dlg.overweight_handicap)
                        settings.configuration.set_overweight_step(
                            dlg.overweight_step)
                        settings.configuration.set_underweight_handicap(
                            dlg.underweight_handicap)
                        settings.configuration.set_underweight_step(
                            dlg.underweight_step)
                        settings.configuration.set_allowed_difference(
                            dlg.allowed_difference)
                        settings.configuration.save()
                        self.RefreshGliderCard()
                    break
                except Exception, e:
                    error_message_dialog(self, _("Preferences save error"), e)
        finally:
            dlg.Destroy()

    def __delete_photos(self, paths):
        """
        Remove deleted photos from file system
        """
        for p in paths:
            try:
                remove(p)
            except:
                pass

    def GliderCardNew(self, evt=None):
        """
        GliderCardNew(self, Event evt=None) - add new glider card event handler
        """
        dlg = GliderCardForm(self)
        try:
            while True:
                try:
                    dlg.SetData()
                    if dlg.ShowModal() == wx.ID_OK:
                        try:
                            record = dlg.GetData()
                            session.add(record)
                            session.commit()
# TODO:                           self.__delete_photos(dlg.deleted_photos)
                            self.list_glider_card.DeleteAllItems()
                            self.datasource_glider_card.append(record)
                            count = len(self.datasource_glider_card)
                            self.list_glider_card.SetItemCount(count)
                            self.list_glider_card.Select(count-1)
                            self.list_glider_card.Focus(count-1)
                            self.RefreshGliderCard()
                        finally:
                            self.__set_enabled_disabled()
                    break
                except Exception, e:
                    session.rollback()
                    error_message_dialog(
                        self, _("Glider card insert error"), e)
        finally:
            dlg.Destroy()

    def GliderCardProperties(self, evt=None):
        """
        GliderCardProperties(self, Event evt=None) - edit glider card
        event handler
        """
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
                        session.commit()
                        # TODO:
                        # self.__delete_photos(dlg.deleted_photos)
                        self.list_glider_card.RefreshItem(
                            self.list_glider_card.GetFocusedItem())
                        self.RefreshGliderCard()
                    else:
                        session.rollback()
                    break
                except Exception, e:
                    session.rollback()
                    error_message_dialog(self, _("Glider card edit error"), e)
        finally:
            dlg.Destroy()

    def GliderCardDelete(self, evt=None):
        """
        GliderCardDelete(self, Event evt=None) - delete glider card
        event handler
        """
        record = self.list_glider_card.current_item
        if wx.MessageDialog(
            self, _("Are you sure to delete %s?") % record,
            _("Delete %s?") % record,
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING
        ).ShowModal() == wx.ID_YES:
            try:
                i = self.datasource_glider_card.index(record)
                try:
                    photos_path = [photo.full_path for photo in record.photos]
                    session.delete(record)
                    session.commit()
                    self.list_glider_card.DeleteAllItems()
                    self.__delete_photos(photos_path)
                    del(self.datasource_glider_card[i])
                    i = i - 1
                    i = i >= 0 and i or 0
                    self.list_glider_card.SetItemCount(
                        len(self.datasource_glider_card))
                    self.list_glider_card.Select(i)
                    self.list_glider_card.Focus(i)
                    self.RefreshGliderCard()
                finally:
                    self.__set_enabled_disabled()
            except Exception, e:
                session.rollback()
                error_message_dialog(self, _("Glider card delete error"), e)

    def GliderCardChange(self, evt=None):
        """
        GliderCardChange(self, Event evt=None) - this method is called
        when glider card is changed
        """
        record = self.list_glider_card.current_item
        if record == self.__old_record:
            return
        self.RefreshGliderCard()

    def __glider_card_print(self, preview=False):
        """
        __glider_card_print(self, preview=False) - print glider card
        """
        if Template is None:
            raise Exception(_("Python Mako is not installed"))

        record = self.list_glider_card.current_item

        status = [
            self.text_non_lifting_status.Label,
            self.text_mtow_status.Label,
            self.text_seat_status.Label,
            self.text_referential_status.Label,
        ]
        coefficient_status = self.text_coefficient_status.Label

        daily_weight = []
        for i, item in enumerate(record.daily_weight):
            daily_weight.append({
                'date': self.__list_daily_weigh_get_item_text(
                    i, 'date'),
                'tow_bar_weight': self.__list_daily_weigh_get_item_text(
                    i, 'tow_bar_weight'),
                'status': self.__list_daily_weigh_get_item_text(
                    i, 'status')
            })
        report = HtmlEasyPrinting(name=_("Glider card"), parentWindow=self)
        template_name = (
            'glider-card-club.html'
            if record.glider_type.club_class else
            'glider-card.html')
        t = Template(
            filename=joinpath(settings.TEMPLATES_DIR, template_name),
            imports=['from wx import GetTranslation as _'])
        html = t.render_unicode(
            glider_card=record,
            status=status,
            coefficient_status=coefficient_status,
            daily_weight=daily_weight,
            allowed_difference=settings.configuration.allowed_difference
        )

        if preview:
            report.PreviewText(html)
        else:
            report.PrintText(html)

    def GliderCardFind(self, evt=None):
        """
        GliderCardFind(self, Event evt=None) - set text_find as active control
        """
        self.text_find.SetFocus()

    def GliderCardPrint(self, evt=None):
        """
        GliderCardPrint(self, Event evt=None) - print glider card event handler
        """
        self.__glider_card_print()

    def GliderCardPrintPreview(self, evt=None):
        """
        GliderCardPrintPreview(self, Event evt=None) - print glider card
        event handler
        """
        self.__glider_card_print(True)

    def DailyWeightNew(self, evt=None):
        """
        DailyWeightNew(self, Event evt=None) - add new daily weight event
        handler
        """
        dlg = DailyWeightForm(self)
        try:
            while True:
                try:
                    dlg.SetData()
                    dlg.SetNow()
                    if hasattr(self, 'daily_weight_position'):
                        dlg.SetPosition(self.daily_weight_position)
                    ret = dlg.ShowModal()
                    self.daily_weight_position = dlg.GetPosition()
                    if ret == wx.ID_OK:
                        try:
                            record = dlg.GetData()
                            glider_card = self.list_glider_card.current_item
                            glider_card.daily_weight.append(record)
                            session.commit()
                            self.list_daily_weight.DeleteAllItems()
                            self.list_daily_weight.datasource =\
                                glider_card.daily_weight
                            i = glider_card.daily_weight.index(record)
                            count = len(glider_card.daily_weight)
                            self.list_daily_weight.SetItemCount(count)
                            self.list_daily_weight.Select(i)
                            self.list_daily_weight.Focus(i)
                        finally:
                            self.__set_enabled_disabled_daily()
                    break
                except Exception, e:
                    session.rollback()
                    error_message_dialog(
                        self, _("Daily weight insert error"), e)
        finally:
            dlg.Destroy()

    def DailyWeightProperties(self, evt=None):
        """
        DailyWeightProperties(self, Event evt=None) - edit daily weight
        event handler
        """
        dlg = DailyWeightForm(self)
        try:
            dlg.text_tow_bar_weight.SetFocus()
            record = self.list_daily_weight.current_item
            dlg.SetData(record)
            while True:
                try:
                    if hasattr(self, 'daily_weight_position'):
                        dlg.SetPosition(self.daily_weight_position)
                    ret = dlg.ShowModal()
                    self.daily_weight_position = dlg.GetPosition()
                    if ret == wx.ID_OK:
                        record = dlg.GetData()
                        session.commit()
                        self.list_daily_weight.RefreshItem(self.list_daily_weight.GetFocusedItem())
                    else:
                        session.rollback()
                    break
                except Exception, e:
                    session.rollback()
                    error_message_dialog(self, _("Daily weight edit error"), e)
        finally:
            dlg.Destroy()

    def DailyWeightDelete(self, evt=None):
        """
        DailyWeightDelete(self, Event evt=None) - delete daily weight
        event handler
        """
        record = self.list_daily_weight.current_item
        if wx.MessageDialog(
            self, _("Are you sure to delete %s?") % record,
            _("Delete %s?") % record,
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING
        ).ShowModal() == wx.ID_YES:
            try:
                glider_card = self.list_glider_card.current_item
                i = glider_card.daily_weight.index(record)
                try:
                    session.delete(record)
                    session.commit()
                    i = i - 1
                    i = i >= 0 and i or 0
                    self.list_daily_weight.DeleteAllItems()
                    self.list_daily_weight.datasource =\
                        glider_card.daily_weight
                    self.list_daily_weight.SetItemCount(
                        len(glider_card.daily_weight))
                    self.list_daily_weight.Select(i)
                    self.list_daily_weight.Focus(i)
                finally:
                    self.__set_enabled_disabled_daily()
            except Exception, e:
                session.rollback()
                error_message_dialog(self, _("Daily weight delete error"), e)

    def SearchGliderCard(self, evt=None):
        """
        SearchGliderCard(self, Event evt=None) - filter glider card
        according to competition number or registration
        """
        value = self.text_find.Value
        field = self.combo_find.GetSelection()
        if value != '' and field != wx.NOT_FOUND:
            if field == 0:
                self.datasource_glider_card = self.BASE_QUERY.filter(
                    GliderCard.competition_number.ilike(value)).all()
            elif field == 1:
                self.datasource_glider_card = self.BASE_QUERY.filter(
                    GliderCard.registration.ilike('%%%s%%' % value)).all()
            elif field == 2:
                self.datasource_glider_card = self.BASE_QUERY.filter(
                    GliderType.name.ilike('%%%s%%' % value)).all()
            elif field == 3:
                self.datasource_glider_card = self.BASE_QUERY.filter(
                    Pilot.surname.ilike('%s%%' % value)).all()
            self.__filtered = True
            self.RefreshGliderCard()
        else:
            self.AllGliderCard()
        self.list_glider_card.SetFocus()

    def AllGliderCard(self, evt=None):
        """
        AllGliderCard(self, Event evt=None) - cancel filter glider card
        and show all data
        """
        if self.__filtered:
            self.text_find.SetValue('')
            self.datasource_glider_card = self.BASE_QUERY.all()
            self.__filtered = False
            self.RefreshGliderCard()

    def __set_photo(self, index=None):
        """
        __set_photo(self, int index) - show photo thumbnail or empty photo
        and enable or disable buttons
        """
        self.__current_photo_index = index
        if index is not None:
            self.photo.SetBitmap(
                GetPhotoBitmap(self.photo.ClientSize, self.__photos[index]))
        else:
            self.photo.SetBitmap(
                GetPhotoBitmap(self.photo.ClientSize))
        # Enable or disable prev and next buttons
        if index is None:
            self.button_photo_prev.Enable(False)
            self.button_photo_next.Enable(False)
            self.button_photo_show.Enable(False)
            self.menu_glider_card_show_photo.Enable(False)
        else:
            self.button_photo_show.Enable(True)
            self.menu_glider_card_show_photo.Enable(True)
            count = len(self.__photos)
            if count <= 1:
                self.button_photo_prev.Enable(False)
                self.button_photo_next.Enable(False)
            elif index == 0:
                self.button_photo_prev.Enable(False)
                self.button_photo_next.Enable(True)
            elif index == count - 1:
                self.button_photo_prev.Enable(True)
                self.button_photo_next.Enable(False)
            else:
                self.button_photo_prev.Enable(True)
                self.button_photo_next.Enable(True)

    def RefreshGliderCard(self):
        """
        RefreshGliderCard(self) - refresh data in the glider card
        """
        record = self.list_glider_card.current_item
        self.__old_record = record

        if record is not None:
            # Base data
            self.text_registration.SetLabel(
                record.column_as_str('registration'))
            self.text_competition_number.SetLabel(
                record.column_as_str('competition_number'))
            self.text_glider_type.SetLabel(record.column_as_str('glider_type'))
            self.text_glider_class.SetLabel(record.glider_type.club_class_str)
            self.text_pilot.SetLabel(record.column_as_str('pilot'))
            self.text_organization.SetLabel(
                record.column_as_str('organization'))
            self.text_winglets.SetLabel(
                record.winglets is True and _("True") or _("False"))
            self.text_landing_gear.SetLabel(
                record.landing_gear is True and _("True") or _("False"))
            # Certified weights
            if record.glider_type.club_class:
                self.text_non_lifting_weight.SetLabel(
                    record.column_as_str('certified_weight_non_lifting'))
                self.text_empty_weight.SetLabel(
                    record.column_as_str('certified_empty_weight'))
                self.text_seat_min_weight.SetLabel(
                    record.column_as_str('certified_min_seat_weight'))
                self.text_seat_max_weight.SetLabel(
                    record.column_as_str('certified_max_seat_weight'))
            # Measured weights
            self.text_glider_weight.SetLabel(
                record.column_as_str('glider_weight'))
            self.text_pilot_weight.SetLabel(
                record.column_as_str('pilot_weight'))
            self.text_tow_bar_weight.SetLabel(
                record.column_as_str('tow_bar_weight'))
            # Non-lifting parts weight status
            difference = record.non_lifting_difference
            if difference is not None:
                if difference > 0:
                    self.__set_status_label_data(
                        self.text_non_lifting_status, self.COLOR_OVERWEIGHT,
                        self.NON_LIFTING_OVERWEIGHT, difference)
                else:
                    self.__set_status_label_data(
                        self.text_non_lifting_status, self.COLOR_OK,
                        self.NON_LIFTING_OK)
            else:
                self.__set_status_label_data(
                    self.text_non_lifting_status, self.COLOR_NO_DATA,
                    self.NON_LIFTING_NO_DATA)
            # MTOW status
            difference = record.mtow_difference
            if difference is not None:
                if difference > 0:
                    self.__set_status_label_data(
                        self.text_mtow_status, self.COLOR_OVERWEIGHT,
                        self.MTOW_OVERWEIGHT, difference)
                else:
                    self.__set_status_label_data(
                        self.text_mtow_status, self.COLOR_OK, self.MTOW_OK)
            else:
                self.__set_status_label_data(
                    self.text_mtow_status, self.COLOR_NO_DATA,
                    self.MTOW_NO_DATA)
            # Seat weighting status
            difference = record.seat_weight_difference
            if difference is not None:
                if difference > 0:
                    self.__set_status_label_data(
                        self.text_seat_status, self.COLOR_OVERWEIGHT,
                        self.SEAT_OVERWEIGHT, difference)
                elif difference < 0:
                    self.__set_status_label_data(
                        self.text_seat_status, self.COLOR_OVERWEIGHT,
                        self.SEAT_UNDERWEIGHT, difference)
                else:
                    self.__set_status_label_data(
                        self.text_seat_status, self.COLOR_OK, self.SEAT_OK)
            else:
                self.__set_status_label_data(
                    self.text_seat_status, self.COLOR_NO_DATA,
                    self.SEAT_NO_DATA)
            # Referential weight status
            difference = record.referential_difference
            if difference is not None:
                if difference > 0:
                    self.__set_status_label_data(
                        self.text_referential_status, self.COLOR_OVERWEIGHT,
                        self.REFERENTIAL_OVERWEIGHT, difference)
                elif difference < 0:
                    self.__set_status_label_data(
                        self.text_referential_status, self.COLOR_UNDERWEIGHT,
                        self.REFERENTIAL_UNDERWEIGHT, abs(difference))
                else:
                    self.__set_status_label_data(
                        self.text_referential_status, self.COLOR_OK,
                        self.REFERENTIAL_OK)
            else:
                self.__set_status_label_data(
                    self.text_referential_status, self.COLOR_NO_DATA,
                    self.REFERENTIAL_NO_DATA)
            # Coefficient status
            if record.glider_type.club_class:
                coefficient = record.coefficient
                if coefficient is not None:
                    self.__set_status_label_data(
                        self.text_coefficient_status, self.COLOR_TEXT,
                        self.COEFFICIENT, {
                            'coefficient': record.column_as_str('coefficient'),
                            'weight': record.referential_weight
                        }
                    )
                    self.text_coefficient_status.SetFont(self.fontbold)
                else:
                    self.__set_status_label_data(
                        self.text_coefficient_status, self.COLOR_NO_DATA,
                        self.COEFFICIENT_NO_DATA)
                    self.text_coefficient_status.SetFont(self.fontnormal)
            # Photo
            self.__photos = session.query(
                Photo
            ).filter(
                Photo.glider_card == record
            ).order_by(
                desc(Photo.main)
            ).order_by(
                Photo.id
            ).all()
            count = len(self.__photos)
            if count > 0:
                self.__set_photo(0)
                self.list_glider_card.RefreshItems(0, count-1)
            else:
                self.__set_photo(None)
            # Enable or disable controls according to class
            ctrls = [
                'label_certified_weights', 'label_non_lifting_weight',
                'label_empty_weight', 'label_seat_min_weight',
                'label_seat_max_weight', 'text_empty_weight',
                'text_non_lifting_weight', 'text_seat_min_weight',
                'text_seat_max_weight', 'label_winglets',
                'label_landing_gear', 'text_winglets', 'text_landing_gear',
                'text_non_lifting_status', 'text_seat_status',
                'text_referential_status', 'text_coefficient_status',
            ]
            for ctrl_name in ctrls:
                ctrl = getattr(self, ctrl_name)
                if record.glider_type.club_class:
                    ctrl.Enable(True)
                else:
                    ctrl.Enable(False)
                    if ctrl_name == 'text_coefficient_status':
                        self.__set_status_label_data(
                            ctrl, self.COLOR_NO_DATA, self.NOT_USED)
                        self.text_coefficient_status.SetFont(self.fontnormal)
                    elif ctrl_name.startswith('text'):
                        ctrl.SetLabel(
                            self.NOT_USED
                            if ctrl_name.endswith('status') else
                            '')
            # Daily weight
            self.list_daily_weight.datasource = record.daily_weight
            count = len(record.daily_weight)
            if count > 0:
                self.list_daily_weight.DeleteAllItems()
                self.list_daily_weight.SetItemCount(count)
                self.list_daily_weight.Select(0)
                self.list_daily_weight.Focus(0)
            else:
                self.list_daily_weight.SetItemCount(0)
                self.list_daily_weight.DeleteAllItems()
            self.__set_enabled_disabled_daily()
        else:
            self.text_registration.Label = ''
            self.text_competition_number.Label = ''
            self.text_glider_type.Label = ''
            self.text_pilot.Label = ''
            self.text_organization.Label = ''
            self.text_winglets.Label = ''
            self.text_landing_gear.Label = ''
            self.text_non_lifting_weight.Label = ''
            self.text_empty_weight.Label = ''
            self.text_seat_min_weight.Label = ''
            self.text_seat_max_weight.Label = ''
            self.text_glider_weight.Label = ''
            self.text_pilot_weight.Label = ''
            self.text_tow_bar_weight.Label = ''
            self.__set_status_label_data(
                self.text_non_lifting_status, self.COLOR_TEXT, '')
            self.__set_status_label_data(
                self.text_mtow_status, self.COLOR_TEXT, '')
            self.__set_status_label_data(
                self.text_seat_status, self.COLOR_TEXT, '')
            self.__set_status_label_data(
                self.text_referential_status, self.COLOR_TEXT, '')
            self.__set_status_label_data(
                self.text_coefficient_status, self.COLOR_TEXT, '')
            self.__set_photo(None)
            self.list_daily_weight.DeleteAllItems()
            self.list_daily_weight.SetItemCount(0)
            self.list_daily_weight.datasource = None
            self.__set_enabled_disabled_daily()

    def PrevPhoto(self, evt=None):
        """
        PrevPhoto(self, Event evt=None) - show previous photo
        """
        index = self.__current_photo_index
        index = index - 1
        if index < 0:
            index = 0
        self.__set_photo(index)

    def NextPhoto(self, evt=None):
        """
        NextPhoto(self, Event evt=None) - show next photo
        """
        count = len(self.__photos)
        index = self.__current_photo_index
        index = index + 1
        if index >= count:
            index = count - 1
        self.__set_photo(index)

    def ShowPhoto(self, evt=None):
        """
        ShowPhoto(self, Event evt=None) - show photo in associated application
        """
        full_path = self.__photos[self.__current_photo_index].full_path

        try:
            os.startfile(full_path)
            return
        except:
            pass

        try:
            mime_man = wx.MimeTypesManager()
            mime_type = mime_man.GetFileTypeFromExtension(
                splitext(full_path)[1].replace('.', ''))
            command = mime_type.GetOpenCommand(full_path)
        except:
            command = None

        if command is None:
            if settings.SHOW_PHOTO_APP is None:
                dlg = wx.MessageBox(
                    # TODO: mime_type can be None
                    # _("No application is associated to open %s MIME type. "
                    #   "Please, choose the program.") % mime_type.MimeType,
                    _("No application is associated to open image. Please, "
                      "choose the program."),
                    _("Show photo"), wx.OK | wx.CANCEL | wx.ICON_QUESTION, self
                )
                if dlg == wx.OK:
                    dlg_open = wx.FileDialog(
                        self, defaultDir=settings.USER_DIR,
                        message=_("Open file"),
                        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
                    try:
                        if dlg_open.ShowModal() == wx.ID_OK:
                            settings.SHOW_PHOTO_APP = dlg_open.GetPath()
                        else:
                            return
                    finally:
                        dlg_open.Destroy()
                else:
                    return
            command = settings.SHOW_PHOTO_APP
        system("%s %s" % (command, full_path))


class GliderCardForm(wx.Dialog):
    """
    Glider card insert/edit dialog
    """

    def __init__(self, *args, **kwds):
        kwds["style"] = (
            wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.THICK_FRAME)
        wx.Dialog.__init__(self, *args, **kwds)

        self.__current_photo_index = None
        self.deleted_photos = []

        # Base data
        self.staticbox_picture = wx.StaticBox(self, -1, _("Photo"))
        self.staticbox_certified_weights = wx.StaticBox(
            self, -1, _("Certified weights"))
        self.staticbox_measured_weights = wx.StaticBox(
            self, -1, _("Measured weights"))
        self.label_competition_number = wx.StaticText(
            self, -1, _("Competition number"))
        self.label_registration = wx.StaticText(self, -1, _("Registration"))
        self.text_competition_number = wx.TextCtrl(self, -1, "")
        self.text_registration = wx.TextCtrl(self, -1, "")
        self.label_glider_type = wx.StaticText(self, -1, _("Glider type"))
        self.combo_glider_type = wx.ComboBox(
            self, -1, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.button_add_glider_type = wx.Button(
            self, -1, _("Add..."), style=wx.BU_EXACTFIT)
        self.label_pilot = wx.StaticText(self, -1, _("Pilot"))
        self.combo_pilot = wx.ComboBox(
            self, -1, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.button_add_pilot = wx.Button(
            self, -1, _("Add..."), style=wx.BU_EXACTFIT)
        self.label_organization = wx.StaticText(
            self, -1, _("Organization or country"))
        self.combo_organization = wx.ComboBox(
            self, -1, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.button_add_organization = wx.Button(
            self, -1, _("Add..."), style=wx.BU_EXACTFIT)
        self.checkbox_gear = wx.CheckBox(self, -1, _("Landing gear"))
        self.checkbox_winglets = wx.CheckBox(self, -1, _("Winglets"))
        # Photo box
        self.photo = wx.StaticBitmap(self, -1)
        self.button_photo_prev = wx.Button(
            self, wx.NewId(), "<", style=wx.BU_EXACTFIT)
        self.button_photo_add = wx.Button(self, wx.ID_ADD, "")
        self.button_photo_set_main = wx.Button(
            self, wx.NewId(), "*", style=wx.BU_EXACTFIT)
        self.button_photo_delete = wx.Button(self, wx.ID_DELETE, "")
        self.button_photo_next = wx.Button(
            self, wx.NewId(), ">", style=wx.BU_EXACTFIT)
        # Weights
        self.label_non_lifting_weight = wx.StaticText(
            self, -1, _("Non-lifting parts weight"))
        self.text_non_lifting_weight = wx.TextCtrl(self, -1, "")
        self.label_empty_weight = wx.StaticText(
            self, -1, _("Empty glider weight"))
        self.text_empty_weight = wx.TextCtrl(self, -1, "")
        self.label_seat_min_weight = wx.StaticText(
            self, -1, _("Seat minimum weight"))
        self.text_seat_min_weight = wx.TextCtrl(self, -1, "")
        self.label_seat_max_weight = wx.StaticText(
            self, -1, _("Seat maximum weight"))
        self.text_seat_max_weight = wx.TextCtrl(self, -1, "")
        self.label_glider_weight = wx.StaticText(self, -1, _("Glider weight"))
        self.text_glider_weight = wx.TextCtrl(self, -1, "")
        self.label_pilot_weight = wx.StaticText(self, -1, _("Pilot weight"))
        self.text_pilot_weight = wx.TextCtrl(self, -1, "")
        self.label_tow_bar_weight = wx.StaticText(
            self, -1, _("Tow bar weight"))
        self.text_tow_bar_weight = wx.TextCtrl(self, -1, "")
        # Description
        self.label_description = wx.StaticText(self, -1, _("Description"))
        self.text_description = wx.TextCtrl(
            self, -1, "", style=wx.TE_MULTILINE | wx.TE_WORDWRAP)
        # Buttons
        self.button_ok = wx.Button(self, wx.ID_OK, "")
        self.button_cancel = wx.Button(self, wx.ID_CANCEL, "")

        self.__set_properties()
        self.__do_layout()

        # Bind events
        self.Bind(
            wx.EVT_TEXT, self.__text_ctrl_change, self.text_registration)
        self.Bind(
            wx.EVT_TEXT, self.__text_ctrl_change, self.text_competition_number)
        self.Bind(
            wx.EVT_BUTTON, self.__add_glider_type, self.button_add_glider_type)
        self.Bind(
            wx.EVT_BUTTON, self.__add_pilot, self.button_add_pilot)
        self.Bind(
            wx.EVT_BUTTON, self.__add_organization,
            self.button_add_organization)
        self.Bind(
            wx.EVT_BUTTON, self.__photo_prev, self.button_photo_prev)
        self.Bind(
            wx.EVT_BUTTON, self.__photo_add, self.button_photo_add)
        self.Bind(
            wx.EVT_BUTTON, self.__photo_set_main, self.button_photo_set_main)
        self.Bind(
            wx.EVT_BUTTON, self.__photo_delete, self.button_photo_delete)
        self.Bind(
            wx.EVT_BUTTON, self.__photo_next, self.button_photo_next)
        self.Bind(
            wx.EVT_COMBOBOX, self.GliderTypeChange, self.combo_glider_type)

        # Init combo-box data sources
        self.glider_type_items = session.query(GliderType).all()
        self.pilot_items = session.query(Pilot).all()
        self.organization_items = session.query(Organization).all()
        # Fill combo-boxes
        self.__init_combo_glider_type()
        self.__init_combo_pilot()
        self.__init_combo_organization()

    def __set_properties(self):
        self.SetTitle(_("Glider card"))

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
        self.button_add_organization.SetToolTipString(
            _("Add organization or country"))
        self.button_photo_prev.SetToolTipString(_("Previous photo"))
        self.button_photo_add.SetToolTipString(_("Add new photo from file"))
        self.button_photo_set_main.SetToolTipString(_("Set as a main photo"))
        self.button_photo_delete.SetToolTipString(_("Delete photo"))
        self.button_photo_next.SetToolTipString(_("Next photo"))

        self.text_competition_number.SetFocus()
        self.button_ok.SetDefault()

    def __do_layout(self):
        # Glider base data sizer
        sizer_data = wx.GridBagSizer(2, 2)
        sizer_data.Add(
            self.label_competition_number, (0, 0), (1, 3),
            wx.RIGHT | wx.EXPAND, 2)
        sizer_data.Add(
            self.label_registration, (0, 3), (1, 3), wx.LEFT | wx.EXPAND, 2)
        sizer_data.Add(
            self.text_competition_number, (1, 0), (1, 3),
            wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)
        sizer_data.Add(
            self.text_registration, (1, 3), (1, 3),
            wx.LEFT | wx.BOTTOM | wx.EXPAND, 2)
        sizer_data.Add(
            self.label_glider_type, (2, 0), (1, 6), wx.RIGHT | wx.EXPAND, 2)
        sizer_data.Add(
            self.combo_glider_type, (3, 0), (1, 6),
            wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)
        sizer_data.Add(
            self.button_add_glider_type, (3, 6), (1, 1),
            wx.LEFT | wx.BOTTOM, 2)
        sizer_data.Add(
            self.label_pilot, (4, 0), (1, 6), wx.RIGHT | wx.EXPAND, 2)
        sizer_data.Add(
            self.combo_pilot, (5, 0), (1, 6),
            wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)
        sizer_data.Add(
            self.button_add_pilot, (5, 6), (1, 1), wx.LEFT | wx.BOTTOM, 2)
        sizer_data.Add(
            self.label_organization, (6, 0), (1, 6), wx.RIGHT | wx.EXPAND, 2)
        sizer_data.Add(
            self.combo_organization, (7, 0), (1, 6),
            wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)
        sizer_data.Add(
            self.button_add_organization, (7, 6), (1, 1),
            wx.LEFT | wx.BOTTOM, 2)
        sizer_data.Add(
            self.checkbox_gear, (8, 0), (1, 3),
            wx.RIGHT | wx.TOP | wx.BOTTOM | wx.EXPAND, 2)
        sizer_data.Add(
            self.checkbox_winglets, (8, 3), (1, 3),
            wx.LEFT | wx.TOP | wx.BOTTOM | wx.EXPAND, 2)
        sizer_data.AddGrowableCol(0, 1)
        sizer_data.AddGrowableCol(1, 1)
        sizer_data.AddGrowableCol(2, 1)
        sizer_data.AddGrowableCol(3, 1)
        sizer_data.AddGrowableCol(4, 1)
        sizer_data.AddGrowableCol(5, 1)
        # Photo sizer
        sizer_photo_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_photo_buttons.Add(
            self.button_photo_prev, 0, wx.RIGHT | wx.EXPAND, 2)
        sizer_photo_buttons.Add(
            self.button_photo_add, 1, wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_photo_buttons.Add(
            self.button_photo_set_main, 0, wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_photo_buttons.Add(
            self.button_photo_delete, 1, wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_photo_buttons.Add(
            self.button_photo_next, 0, wx.LEFT | wx.EXPAND, 2)
        sizer_photo = wx.StaticBoxSizer(self.staticbox_picture, wx.VERTICAL)
        sizer_photo.Add(self.photo, 1, wx.ALL | wx.EXPAND, 4)
        sizer_photo.Add(sizer_photo_buttons, 0, wx.ALL | wx.EXPAND, 4)
        # Base data and photos
        sizer_glider_card = wx.BoxSizer(wx.HORIZONTAL)
        sizer_glider_card.Add(sizer_data, 1, wx.RIGHT | wx.TOP | wx.EXPAND, 4)
        sizer_glider_card.Add(sizer_photo, 0, wx.TOP | wx.EXPAND, 4)
        # Certified weights sizer
        sizer_certified_weights = wx.GridBagSizer(2, 2)
        sizer_certified_weights.Add(
            self.label_non_lifting_weight, (0, 0), (1, 1),
            wx.RIGHT | wx.EXPAND, 2)
        sizer_certified_weights.Add(
            self.label_empty_weight, (0, 1), (1, 1),
            wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_certified_weights.Add(
            self.label_seat_min_weight, (0, 2), (1, 1),
            wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_certified_weights.Add(
            self.label_seat_max_weight, (0, 3), (1, 1),
            wx.LEFT | wx.EXPAND, 2)
        sizer_certified_weights.Add(
            self.text_non_lifting_weight, (1, 0), (1, 1),
            wx.RIGHT | wx.EXPAND, 2)
        sizer_certified_weights.Add(
            self.text_empty_weight, (1, 1), (1, 1),
            wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_certified_weights.Add(
            self.text_seat_min_weight, (1, 2), (1, 1),
            wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_certified_weights.Add(
            self.text_seat_max_weight, (1, 3), (1, 1),
            wx.LEFT | wx.EXPAND, 2)
        sizer_certified_weights.AddGrowableCol(0, 1)
        sizer_certified_weights.AddGrowableCol(1, 1)
        sizer_certified_weights.AddGrowableCol(2, 1)
        sizer_certified_weights.AddGrowableCol(3, 1)
        sizer_certified_weights_staticbox = wx.StaticBoxSizer(
            self.staticbox_certified_weights, wx.VERTICAL)
        sizer_certified_weights_staticbox.Add(
            sizer_certified_weights, 0, wx.ALL | wx.EXPAND, 4)
        # Measured weights sizer
        sizer_measured_weights = wx.GridBagSizer(2, 2)
        sizer_measured_weights.Add(
            self.label_glider_weight, (0, 0), (1, 1),
            wx.RIGHT | wx.EXPAND, 2)
        sizer_measured_weights.Add(
            self.label_pilot_weight, (0, 1), (1, 1),
            wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_measured_weights.Add(
            self.label_tow_bar_weight, (0, 2), (1, 1),
            wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_measured_weights.Add(
            self.text_glider_weight, (1, 0), (1, 1),
            wx.RIGHT | wx.EXPAND, 2)
        sizer_measured_weights.Add(
            self.text_pilot_weight, (1, 1), (1, 1),
            wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_measured_weights.Add(
            self.text_tow_bar_weight, (1, 2), (1, 1),
            wx.RIGHT | wx.LEFT | wx.EXPAND, 2)
        sizer_measured_weights.Add(
            EmptyChild(self), (1, 3), (1, 1), wx.LEFT | wx.EXPAND, 2)
        sizer_measured_weights.AddGrowableCol(0, 1)
        sizer_measured_weights.AddGrowableCol(1, 1)
        sizer_measured_weights.AddGrowableCol(2, 1)
        sizer_measured_weights.AddGrowableCol(3, 1)
        sizer_measured_weights_staticbox = wx.StaticBoxSizer(
            self.staticbox_measured_weights, wx.VERTICAL)
        sizer_measured_weights_staticbox.Add(
            sizer_measured_weights, 0, wx.ALL | wx.EXPAND, 4)
        # Description sizer
        sizer_description = wx.BoxSizer(wx.VERTICAL)
        sizer_description.Add(
            self.label_description, 0, wx.BOTTOM | wx.EXPAND, 2)
        sizer_description.Add(
            self.text_description, 1, wx.BOTTOM | wx.EXPAND, 2)
        # Dialog buttons sizer
        sizer_buttons = wx.StdDialogButtonSizer()
        sizer_buttons.AddButton(self.button_ok)
        sizer_buttons.AddButton(self.button_cancel)
        sizer_buttons.Realize()
        # Main sizer
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_main.Add(
            sizer_glider_card, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 4)
        sizer_main.Add(
            sizer_certified_weights_staticbox, 0,
            wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 4)
        sizer_main.Add(
            sizer_measured_weights_staticbox, 0,
            wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 4)
        sizer_main.Add(
            sizer_description, 1, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 4)
        sizer_main.Add(
            sizer_buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 4)

        self.SetSizer(sizer_main)
        self.SetMinSize((750, self.GetBestSize().height))
        sizer_main.Fit(self)
        self.Layout()
        self.CenterOnParent()

    def __init_combo_glider_type(self):
        """
        __init_combo_glider_type(self) - load data into combo_box_glider_type
        """
        self.glider_type_items.sort(
            lambda a, b: locale.strcoll(a.name, b.name))
        self.combo_glider_type.Clear()
        self.combo_glider_type.SetItems(
            [i.name for i in self.glider_type_items])

    def __init_combo_pilot(self):
        """
        __init_combo_pilot(self) - load data into combo_box_pilot
        """
        self.pilot_items.sort(
            lambda a, b: locale.strcoll(a.fullname_rev, b.fullname_rev))
        self.combo_pilot.SetItems(
            [i.fullname for i in self.pilot_items])

    def __init_combo_organization(self):
        """
        __init_combo_organization(self) - load data into
        combo_box_organization
        """
        self.organization_items.sort(
            lambda a, b: locale.strcoll(a.name, b.name))
        self.combo_organization.SetItems(
            ["%s, %s" % (i.name, i.code,) for i in self.organization_items])

    def __text_ctrl_change(self, evt):
        """
        __text_ctrl_change(self, evt) - upper case value in the text control
        """
        ctrl = evt.GetEventObject()
        old = ctrl.GetValue()
        new = old.upper()
        if old != new:
            ctrl.ChangeValue(new)
            ctrl.SetInsertionPointEnd()
        evt.Skip()

    def __add_glider_type(self, evt):
        """
        __add_glider_type(self, evt) - add new glider type event handler
        """
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
                        self.combo_glider_type.SetSelection(
                            self.glider_type_items.index(record))
                    break
                except Exception, e:
                    session.rollback()
                    error_message_dialog(self, GLIDER_TYPE_INSERT_ERROR, e)
        finally:
            dlg.Destroy()

    def __add_pilot(self, evt):
        """
        __add_pilot(self, evt) - add new pilot event handler
        """
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
                        self.combo_pilot.SetSelection(
                            self.pilot_items.index(record))
                    break
                except Exception, e:
                    session.rollback()
                    error_message_dialog(self, PILOT_INSERT_ERROR, e)
        finally:
            dlg.Destroy()

    def __add_organization(self, evt):
        """
        __add_organization(self, evt) - add new organization event handler
        """
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
                        self.combo_organization.SetSelection(
                            self.organization_items.index(record))
                    break
                except Exception, e:
                    session.rollback()
                    error_message_dialog(self, ORGANIZATION_INSERT_ERROR, e)
        finally:
            dlg.Destroy()

    def __photo_add(self, evt):
        """
        __add_photo(self, evt) - add photo event handler
        """
        dlg = wx.FileDialog(
            self, defaultDir=settings.LAST_OPEN_FILE_PATH,
            message=_("Open file"), wildcard=_("JPEG files") +
            " (*.jpg;*.jpeg)|*.jpg;*.jpeg;*.JPG;*.JPEG",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_PREVIEW)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                self.__photo_changed = True
                src_fullpath = abspath(dlg.GetPath())
                settings.LAST_OPEN_FILE_PATH = dirname(src_fullpath)
                # Sum MD5
                f = open(src_fullpath, 'rb')
                try:
                    photo_md5 = md5(f.read()).hexdigest()
                finally:
                    f.close()
                self.glidercard = getattr(self, 'glidercard', GliderCard())
                # Does photo exist?
                if [
                        p.md5 for p in self.glidercard.photos
                ].count(photo_md5) > 0:
                    error_message_dialog(self, _("Photo already exists!"))
                    return
                # Add photo into database
                photo = Photo(md5=photo_md5, main=False)
                self.glidercard.photos.append(photo)
                # Copy photo into photos dir
                copy(src_fullpath, photo.full_path)
                # Show thumbnail
                self.__set_photo(photo)
        finally:
            dlg.Destroy()

    def __photo_delete(self, evt):
        """
        __delete_photo(self, evt) - delete photo event handler
        """
        index = self.__current_photo_index
        photo = self.glidercard.photos[index]
        self.deleted_photos.append(photo.full_path)
        session.delete(photo)
        del(self.glidercard.photos[index])
        count = len(self.glidercard.photos)
        if count > 0:
            index = index - 1
            self.__set_photo(index=index >= 0 and index or 0)
        else:
            self.__set_photo(index=None)

    def __photo_set_main(self, evt):
        """
        __photo_set(self, evt) - set current photo as a main photo
        """
        for i, p in enumerate(self.glidercard.photos):
            if i == self.__current_photo_index:
                p.main = True
            else:
                p.main = False
        self.__set_photo(index=self.__current_photo_index)

    def __photo_prev(self, evt):
        """
        __photo_prev(self, evt) - show prev photo
        """
        index = self.__current_photo_index - 1
        if index < 0:
            index = 0
        self.__set_photo(index=index)

    def __photo_next(self, evt):
        """
        __photo_next(self, evt) - show next photo
        """
        index = self.__current_photo_index + 1
        count = len(self.glidercard.photos)
        if index > count - 1:
            index = count
        self.__set_photo(index=index)

    def __set_photo(self, photo=None, index=None):
        """
        __set_photo(self, Photo photo=None, int index=None) - show photo
        thumbnail or empty photo and enable or disable buttons
        """
        if photo is not None:
            self.__current_photo_index = [
                p.md5 for p in self.glidercard.photos].index(photo.md5)
            self.button_photo_set_main.Enable(not photo.main)
            self.button_photo_delete.Enable(True)
            self.photo.SetBitmap(GetPhotoBitmap(self.photo.ClientSize, photo))
        elif index is not None:
            self.__current_photo_index = index
            photo = self.glidercard.photos[index]
            self.button_photo_set_main.Enable(not photo.main)
            self.button_photo_delete.Enable(True)
            self.photo.SetBitmap(GetPhotoBitmap(self.photo.ClientSize, photo))
        else:
            self.__current_photo_index = None
            self.button_photo_set_main.Enable(False)
            self.button_photo_delete.Enable(False)
            self.photo.SetBitmap(GetPhotoBitmap(self.photo.ClientSize))
        # Enable or disable prev and next buttons
        if self.__current_photo_index is None:
            self.button_photo_prev.Enable(False)
            self.button_photo_next.Enable(False)
        else:
            count = len(self.glidercard.photos)
            if count <= 1:
                self.button_photo_prev.Enable(False)
                self.button_photo_next.Enable(False)
            elif self.__current_photo_index == 0:
                self.button_photo_prev.Enable(False)
                self.button_photo_next.Enable(True)
            elif self.__current_photo_index == count - 1:
                self.button_photo_prev.Enable(True)
                self.button_photo_next.Enable(False)
            else:
                self.button_photo_prev.Enable(True)
                self.button_photo_next.Enable(True)

    def GetData(self):
        """
        GetData(self) -> GliderCard - get cleaned form data
        """
        glidercard = getattr(self, 'glidercard', GliderCard())
        glidercard.str_to_column(
            'registration', self.text_registration.Value)
        glidercard.str_to_column(
            'competition_number', self.text_competition_number.Value)
        glidercard.str_to_column(
            'certified_weight_non_lifting', self.text_non_lifting_weight.Value)
        glidercard.str_to_column(
            'certified_empty_weight', self.text_empty_weight.Value)
        glidercard.str_to_column(
            'certified_min_seat_weight', self.text_seat_min_weight.Value)
        glidercard.str_to_column(
            'certified_max_seat_weight', self.text_seat_max_weight.Value)
        glidercard.str_to_column(
            'glider_weight', self.text_glider_weight.Value)
        glidercard.str_to_column(
            'pilot_weight', self.text_pilot_weight.Value)
        glidercard.str_to_column(
            'tow_bar_weight', self.text_tow_bar_weight.Value)
        glidercard.str_to_column(
            'description', self.text_description.Value)
        glidercard.landing_gear = self.checkbox_gear.Value
        glidercard.winglets = self.checkbox_winglets.Value
        glidercard.glider_type = (
            self.combo_glider_type.CurrentSelection >= 0 and
            self.glider_type_items[self.combo_glider_type.CurrentSelection] or
            None)
        glidercard.pilot = (
            self.combo_pilot.CurrentSelection >= 0 and
            self.pilot_items[self.combo_pilot.CurrentSelection] or
            None)
        glidercard.organization = (
            self.combo_organization.CurrentSelection >= 0 and
            self.organization_items[
                self.combo_organization.CurrentSelection] or
            None)
        return glidercard

    def SetData(self, glidercard=None):
        """
        SetData(self, glidercard=None) - set form data
        """
        if glidercard is not None:
            self.glidercard = glidercard
            # Labels
            self.text_registration.Value = glidercard.column_as_str(
                'registration')
            self.text_competition_number.Value = glidercard.column_as_str(
                'competition_number')
            self.text_non_lifting_weight.Value = glidercard.column_as_str(
                'certified_weight_non_lifting')
            self.text_empty_weight.Value = glidercard.column_as_str(
                'certified_empty_weight')
            self.text_seat_min_weight.Value = glidercard.column_as_str(
                'certified_min_seat_weight')
            self.text_seat_max_weight.Value = glidercard.column_as_str(
                'certified_max_seat_weight')
            self.text_glider_weight.Value = glidercard.column_as_str(
                'glider_weight')
            self.text_pilot_weight.Value = glidercard.column_as_str(
                'pilot_weight')
            self.text_tow_bar_weight.Value = glidercard.column_as_str(
                'tow_bar_weight')
            self.text_description.Value = glidercard.column_as_str(
                'description')
            # Checkboxes
            self.checkbox_gear.Value = (
                glidercard.landing_gear is not None and
                glidercard.landing_gear or
                False)
            self.checkbox_winglets.Value = (
                glidercard.winglets is not None and
                glidercard.winglets or
                False)
            # Combo boxes
            if glidercard.glider_type is not None:
                self.combo_glider_type.SetSelection(
                    self.glider_type_items.index(glidercard.glider_type))
            if glidercard.pilot is not None:
                self.combo_pilot.SetSelection(
                    self.pilot_items.index(glidercard.pilot))
            if glidercard.organization is not None:
                self.combo_organization.SetSelection(
                    self.organization_items.index(glidercard.organization))
            # Photos
            if len(glidercard.photos) > 0:
                self.__set_photo(index=0)
            else:
                self.__set_photo()
        else:
            self.__set_photo()
        self.GliderTypeChange()

    def GliderTypeChange(self, evt=None):
        """
        SetEnabledDisabled(self) - enable or disable controls
        """
        glider_type = (
            self.combo_glider_type.CurrentSelection >= 0 and
            self.glider_type_items[self.combo_glider_type.CurrentSelection] or
            None)
        if glider_type and glider_type.club_class:
            self.text_non_lifting_weight.Enable(True)
            self.text_empty_weight.Enable(True)
            self.text_seat_min_weight.Enable(True)
            self.text_seat_max_weight.Enable(True)
            self.checkbox_gear.Enable(True)
            self.checkbox_winglets.Enable(True)
        else:
            self.text_non_lifting_weight.Enable(False)
            self.text_empty_weight.Enable(False)
            self.text_seat_min_weight.Enable(False)
            self.text_seat_max_weight.Enable(False)
            self.checkbox_gear.Enable(False)
            self.checkbox_winglets.Enable(False)


class DailyWeightForm(wx.Dialog):

    def __init__(self, *args, **kwds):
        kwds["style"] = (
            wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.THICK_FRAME)
        wx.Dialog.__init__(self, *args, **kwds)
        self.label_date = wx.StaticText(self, -1, _("Date"))
        self.label_tow_bar_weight = wx.StaticText(
            self, -1, _("Tow bar weight"))
        self.text_date = wx.TextCtrl(self, -1, "")  # , style=wx.BORDER_NONE)
        self.button_now = wx.Button(self, -1, _("Today"), style=wx.BU_EXACTFIT)
        self.text_tow_bar_weight = wx.TextCtrl(self, -1, "")
        self.button_ok = wx.Button(self, wx.ID_OK, "")
        self.button_cancel = wx.Button(self, wx.ID_CANCEL, "")

        self.__set_properties()
        self.__do_layout()

        # Bind events
        self.Bind(wx.EVT_BUTTON, self.SetNow, self.button_now)

    def __set_properties(self):
        self.SetTitle(_("Daily weight"))
        self.button_now.SetToolTipString(_("Set today date"))
        self.label_date.SetFont(
            wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.label_tow_bar_weight.SetFont(
            wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.text_date.SetFocus()
        self.button_ok.SetDefault()

        self.text_date.SetEditable(False)
        self.text_date.Enable(False)
        self.button_now.Enable(False)

    def __do_layout(self):
        grid_sizer = wx.GridBagSizer(2, 2)
        grid_sizer.Add(
            self.label_date,  (0, 0), (1, 2), wx.RIGHT | wx.EXPAND, 2)
        grid_sizer.Add(
            self.label_tow_bar_weight,  (0, 2), (1, 1),
            wx.LEFT | wx.EXPAND, 2)
        grid_sizer.Add(
            self.text_date,  (1, 0), (1, 1), wx.BOTTOM | wx.EXPAND, 2)
        grid_sizer.Add(
            self.button_now,  (1, 1), (1, 1),
            wx.BOTTOM | wx.RIGHT | wx.EXPAND, 2)
        grid_sizer.Add(
            self.text_tow_bar_weight,  (1, 2), (1, 1),
            wx.LEFT | wx.BOTTOM | wx.EXPAND, 2)
        grid_sizer.AddGrowableCol(0, 1)
        grid_sizer.AddGrowableCol(2, 1)

        sizer_buttons = wx.StdDialogButtonSizer()
        sizer_buttons.AddButton(self.button_ok)
        sizer_buttons.AddButton(self.button_cancel)
        sizer_buttons.Realize()

        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_main.Add(grid_sizer, 0, wx.ALL | wx.EXPAND, 4)
        sizer_main.Add(
            sizer_buttons, 0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.TOP | wx.ALIGN_RIGHT, 4)

        self.SetSizer(sizer_main)
        self.SetMinSize((self.GetSize().width, self.GetBestSize().height))
        self.SetMaxSize((-1, self.GetBestSize().height))

        sizer_main.Fit(self)
        self.Layout()
        self.SetMinSize((500, -1))
        self.CenterOnParent()

    def SetNow(self, evt=None):
        """
        SetNow(self, evt=None) - put current date into text_date control
        """
        self.text_date.Value = datetime.now().strftime('%x %X')
        self.text_tow_bar_weight.SetFocus()

    def GetData(self):
        """
        GetData(self) -> DailyWeight - get cleaned form data
        """
        dailyweight = getattr(self, 'dailyweight', DailyWeight())
        dailyweight.str_to_column(
            'date', self.text_date.Value)
        dailyweight.str_to_column(
            'tow_bar_weight', self.text_tow_bar_weight.Value)
        return dailyweight

    def SetData(self, dailyweight=None):
        """
        SetData(self, DailyWeight dailyweight=None) - set form data
        """
        if dailyweight is not None:
            self.dailyweight = dailyweight
            self.text_date.Value = dailyweight.column_as_str('date')
            self.text_tow_bar_weight.Value = dailyweight.column_as_str(
                'tow_bar_weight')


class CleanDatabaseForm(wx.Dialog):

    def __init__(self, *args, **kwds):
        wx.Dialog.__init__(self, *args, **kwds)

        self.label = wx.StaticText(
            self, -1, _("Please, select what do you want to clean:"))
        self.cb_daily_weights = wx.CheckBox(self, -1, _("Daily weights"))
        self.cb_photos = wx.CheckBox(self, -1, _("Photos"))
        self.cb_measured_weights = wx.CheckBox(
            self, -1, _("Initial measurements"))
        self.cb_glider_cards = wx.CheckBox(self, -1, _("Glider cards"))
        self.cb_igc_handicaps = wx.CheckBox(self, -1, _("IGC handicap list"))
        self.cb_pilots = wx.CheckBox(self, -1, _("Pilots"))
        self.cb_organizations = wx.CheckBox(self, -1, _("Organizations"))
        self.cb_preferences = wx.CheckBox(self, -1, _("Preferences"))
        self.button_ok = wx.Button(self, wx.ID_OK, "")
        self.button_cancel = wx.Button(self, wx.ID_CANCEL, "")

        self.__set_properties()
        self.__do_layout()

        # Bind events
        self.Bind(wx.EVT_CHECKBOX, self.__cb_changed, self.cb_daily_weights)
        self.Bind(wx.EVT_CHECKBOX, self.__cb_changed, self.cb_photos)
        self.Bind(wx.EVT_CHECKBOX, self.__cb_changed, self.cb_measured_weights)
        self.Bind(wx.EVT_CHECKBOX, self.__cb_changed, self.cb_glider_cards)
        self.Bind(wx.EVT_CHECKBOX, self.__cb_changed, self.cb_igc_handicaps)
        self.Bind(wx.EVT_CHECKBOX, self.__cb_changed, self.cb_pilots)
        self.Bind(wx.EVT_CHECKBOX, self.__cb_changed, self.cb_organizations)
        self.Bind(wx.EVT_CHECKBOX, self.__cb_changed, self.cb_preferences)

    def __set_properties(self):
        self.SetTitle(_("Clean database"))
        self.button_ok.SetDefault()
        self.__cb_changed(None)

    def __do_layout(self):
        sizer_buttons = wx.StdDialogButtonSizer()
        sizer_buttons.AddButton(self.button_ok)
        sizer_buttons.AddButton(self.button_cancel)
        sizer_buttons.Realize()

        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_main.Add(self.label, 0, wx.ALL, 4)
        sizer_main.Add(self.cb_daily_weights, 0, wx.ALL, 4)
        sizer_main.Add(self.cb_photos, 0, wx.ALL, 4)
        sizer_main.Add(self.cb_measured_weights, 0, wx.ALL, 4)
        sizer_main.Add(self.cb_glider_cards, 0, wx.ALL, 4)
        sizer_main.Add(self.cb_igc_handicaps, 0, wx.ALL, 4)
        sizer_main.Add(self.cb_pilots, 0, wx.ALL, 4)
        sizer_main.Add(self.cb_organizations, 0, wx.ALL, 4)
        sizer_main.Add(self.cb_preferences, 0, wx.ALL, 4)
        sizer_main.Add(sizer_buttons, 0, wx.ALL | wx.ALIGN_RIGHT, 4)

        self.SetSizer(sizer_main)

        sizer_main.Fit(self)
        self.Layout()
        self.SetMinSize((self.GetSize().width * 1.1, self.GetSize().height))
        self.CenterOnParent()

    def __cb_changed(self, evt):
        if self.cb_igc_handicaps.Value or self.cb_pilots.Value or \
                                        self.cb_organizations.Value:
            self.cb_daily_weights.Value = True
            self.cb_photos.Value = True
            self.cb_measured_weights.Value = True
            self.cb_glider_cards.Value = True
            self.cb_photos.Value = True
            self.cb_daily_weights.Enable(False)
            self.cb_photos.Enable(False)
            self.cb_measured_weights.Enable(False)
            self.cb_glider_cards.Enable(False)
        else:
            self.cb_daily_weights.Enable(True)
            self.cb_photos.Enable(True)
            self.cb_measured_weights.Enable(True)
            self.cb_glider_cards.Enable(True)
        if self.cb_glider_cards.Value:
            self.cb_daily_weights.Value = True
            self.cb_photos.Value = True
            self.cb_measured_weights.Value = True
            self.cb_daily_weights.Enable(False)
            self.cb_photos.Enable(False)
            self.cb_measured_weights.Enable(False)
        else:
            self.cb_daily_weights.Enable(True)
            self.cb_photos.Enable(True)
            self.cb_measured_weights.Enable(True)

        if not (self.cb_igc_handicaps.Value or self.cb_pilots.Value or
                self.cb_organizations.Value or self.cb_glider_cards.Value or
                self.cb_photos.Value or self.cb_measured_weights.Value or
                self.cb_daily_weights.Value or self.cb_preferences.Value):
            self.button_ok.Enable(False)
        else:
            self.button_ok.Enable(True)
