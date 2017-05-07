"""
GUI - IGC handicap list
"""

import wx
from wx import GetTranslation as _

import gui_dialogmodel

from database import session
from models import GliderType

GLIDER_TYPE_INSERT_ERROR = _("Glider type insert error")
GLIDER_TYPE_EDIT_ERROR = _("Glider type edit error")
GLIDER_TYPE_DELETE_ERROR = _("Glider type delete error")


class IgcHandicapList(gui_dialogmodel.DialogModel):
    """
    IGC handicap list dialog
    """

    def __init__(self, *args, **kwargs):
        """
        __init__(self, Window parent, int id=-1)
        """
        gui_dialogmodel.DialogModel.__init__(self, *args, **kwargs)

        self.SetTitle(_("IGC handicap list"))

        # Set grid columns
        self.list_ctrl.InsertColumn(
            0, _("Name"), 'name', proportion=2)
        self.list_ctrl.InsertColumn(
            1, _("Class"), 'club_class_str', proportion=1)
        self.list_ctrl.InsertColumn(
            2, _("Coefficient"), 'coefficient',
            format=wx.LIST_FORMAT_RIGHT, proportion=1)
        self.list_ctrl.InsertColumn(
            3, _("Non lifting w."), 'weight_non_lifting',
            format=wx.LIST_FORMAT_RIGHT, proportion=1)
        self.list_ctrl.InsertColumn(
            4, _("Without water"), 'mtow_without_water',
            format=wx.LIST_FORMAT_RIGHT, proportion=1)
        self.list_ctrl.InsertColumn(
            5, _("MTOW"), 'mtow', format=wx.LIST_FORMAT_RIGHT, proportion=1)
        self.list_ctrl.InsertColumn(
            6, _("Referential w."), 'weight_referential',
            format=wx.LIST_FORMAT_RIGHT, proportion=1)

        # Open data source
        self.datasource = session.query( GliderType ).all()
        # Assign edit dialog
        self.edit_dialog = IgcHandicapForm
        # Assign error messages
        self.message_insert_error = GLIDER_TYPE_INSERT_ERROR
        self.message_edit_error = GLIDER_TYPE_EDIT_ERROR
        self.message_delete_error = GLIDER_TYPE_DELETE_ERROR

        self.SetSize((750, 450))
        self.SetMinSize(self.GetSize())
        self.CenterOnParent()


class IgcHandicapForm(wx.Dialog):
    """
    IGC handicat insert/edit dialog
    """

    def __init__(self, *args, **kwds):
        """
        __init__(self, Window parent, int id=-1)
        """
        kwds["style"] = (
            wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.THICK_FRAME)
        wx.Dialog.__init__(self, *args, **kwds)
        self.label_name = wx.StaticText(self, -1, _("Name"))
        self.label_coefficient = wx.StaticText(self, -1, _("Coefficient"))
        self.text_name = wx.TextCtrl(self, -1, "")
        self.checkbox_club = wx.CheckBox(self, -1, _("Club class"))
        self.text_coefficient = wx.TextCtrl(self, -1, "")
        self.label_weight_non_lifting = wx.StaticText(
            self, -1, _("Weight non-lifting"))
        self.label_mtow_without_water = wx.StaticText(
            self, -1, _("MTOW without water"))
        self.label_mtow = wx.StaticText(self, -1, _("MTOW"))
        self.label_weight_referential = wx.StaticText(
            self, -1, _("Weight referential"))
        self.text_weight_non_lifting = wx.TextCtrl(self, -1, "")
        self.text_mtow_without_water = wx.TextCtrl(self, -1, "")
        self.text_mtow = wx.TextCtrl(self, -1, "")
        self.text_weight_referential = wx.TextCtrl(self, -1, "")
        self.label_description = wx.StaticText(self, -1, _("Description"))
        self.text_description = wx.TextCtrl(
            self, -1, "", style=wx.TE_MULTILINE | wx.TE_WORDWRAP)
        self.button_ok = wx.Button(self, wx.ID_OK, "")
        self.button_cancel = wx.Button(self, wx.ID_CANCEL, "")

        # Bind events
        self.Bind(wx.EVT_CHECKBOX, self.ClubClassChange, self.checkbox_club)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetTitle(_("Glider type"))

        fontbold = self.label_name.GetFont()
        fontbold.SetWeight(wx.FONTWEIGHT_BOLD)
        self.label_name.SetFont(fontbold)

        self.text_weight_non_lifting.SetMinSize((150, -1))
        self.text_mtow_without_water.SetMinSize((150, -1))
        self.text_mtow.SetMinSize((150, -1))
        self.text_weight_referential.SetMinSize((150, -1))

        self.text_name.SetMaxLength(50)

        self.text_name.SetFocus()
        self.button_ok.SetDefault()
        self.ClubClassChange()

    def __do_layout(self):
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_buttons = wx.StdDialogButtonSizer()
        grid_sizer = wx.GridBagSizer(2, 2)
        grid_sizer.Add(
            self.label_name, (0, 0), (1, 2), wx.RIGHT | wx.EXPAND, 2)
        grid_sizer.Add(
            self.label_coefficient, (0, 3), (1, 1), wx.LEFT | wx.EXPAND, 2)
        grid_sizer.Add(
            self.text_name, (1, 0), (1, 2),
            wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)
        grid_sizer.Add(
            self.checkbox_club, (1, 2), (1, 1),
            wx.LEFT | wx.BOTTOM | wx.EXPAND, 2)
        grid_sizer.Add(
            self.text_coefficient, (1, 3), (1, 1),
            wx.LEFT | wx.BOTTOM | wx.EXPAND, 2)
        grid_sizer.Add(
            self.label_weight_non_lifting, (2, 0), (1, 1),
            wx.RIGHT | wx.EXPAND, 2)
        grid_sizer.Add(
            self.label_mtow_without_water, (2, 1), (1, 1),
            wx.LEFT | wx.RIGHT | wx.EXPAND, 2)
        grid_sizer.Add(
            self.label_mtow, (2, 2), (1, 1),
            wx.LEFT | wx.RIGHT | wx.EXPAND, 2)
        grid_sizer.Add(
            self.label_weight_referential, (2, 3), (1, 1),
            wx.LEFT | wx.EXPAND, 2)
        grid_sizer.Add(
            self.text_weight_non_lifting, (3, 0), (1, 1),
            wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)
        grid_sizer.Add(
            self.text_mtow_without_water, (3, 1), (1, 1),
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)
        grid_sizer.Add(
            self.text_mtow,  (3, 2), (1, 1),
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)
        grid_sizer.Add(
            self.text_weight_referential,  (3, 3), (1, 1),
            wx.LEFT | wx.BOTTOM | wx.EXPAND, 2)
        grid_sizer.Add(
            self.label_description, (4, 0), (1, 4), wx.EXPAND, 0)
        grid_sizer.Add(
            self.text_description, (5, 0), (1, 4), wx.BOTTOM | wx.EXPAND, 2)
        grid_sizer.AddGrowableRow(5)
        grid_sizer.AddGrowableCol(0)
        grid_sizer.AddGrowableCol(1)
        grid_sizer.AddGrowableCol(2)
        grid_sizer.AddGrowableCol(3)
        sizer_main.Add(grid_sizer, 1, wx.ALL | wx.EXPAND, 4)
        sizer_buttons.AddButton(self.button_ok)
        sizer_buttons.AddButton(self.button_cancel)
        sizer_buttons.Realize()
        sizer_main.Add(
            sizer_buttons, 0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, 4)
        self.SetSizer(sizer_main)
        sizer_main.Fit(self)
        self.Layout()
        self.SetMinSize(self.GetSize())
        self.CenterOnParent()

    def GetData(self):
        """
        GetData(self) -> GliderType - get cleaned form data
        """
        if hasattr(self, 'glidertype'):
            glidertype = self.glidertype
        else:
            glidertype = GliderType()
        glidertype.str_to_column(
            'name', self.text_name.Value)
        glidertype.str_to_column(
            'coefficient', self.text_coefficient.Value)
        glidertype.str_to_column(
            'weight_non_lifting', self.text_weight_non_lifting.Value)
        glidertype.str_to_column(
            'mtow_without_water', self.text_mtow_without_water.Value)
        glidertype.str_to_column(
            'mtow', self.text_mtow.Value)
        glidertype.str_to_column(
            'weight_referential', self.text_weight_referential.Value)
        glidertype.str_to_column(
            'description', self.text_description.Value)
        glidertype.club_class = self.checkbox_club.Value
        return glidertype

    def SetData(self, glidertype):
        """
        SetData(self, glidertype) - set form data
        """
        self.glidertype = glidertype
        self.text_name.Value = glidertype.column_as_str('name')
        self.text_coefficient.Value = glidertype.column_as_str('coefficient')
        self.text_weight_non_lifting.Value = glidertype.column_as_str(
            'weight_non_lifting')
        self.text_mtow_without_water.Value = glidertype.column_as_str(
            'mtow_without_water')
        self.text_mtow.Value = glidertype.column_as_str('mtow')
        self.text_weight_referential.Value = glidertype.column_as_str(
            'weight_referential')
        self.text_description.Value = glidertype.column_as_str('description')
        self.checkbox_club.Value = (
            glidertype.club_class is not None and
            glidertype.club_class or
            False)
        self.ClubClassChange()

    def ClubClassChange(self, evt=None):
        """
        ClubClassChange(self) - enable or disable controls
        """
        if self.checkbox_club.Value:
            self.text_weight_non_lifting.Enable(True)
            self.text_mtow_without_water.Enable(True)
            self.text_weight_referential.Enable(True)
            self.text_coefficient.Enable(True)
            self.text_mtow.Enable(False)
        else:
            self.text_weight_non_lifting.Enable(False)
            self.text_mtow_without_water.Enable(False)
            self.text_weight_referential.Enable(False)
            self.text_coefficient.Enable(False)
            self.text_mtow.Enable(True)
