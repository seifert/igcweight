" GUI - Pilots list "

import wx
from wx import GetTranslation as _

import gui_dialogmodel

from database import session
from models import Pilot

PILOT_INSERT_ERROR = _("Pilot insert error")
PILOT_EDIT_ERROR   = _("Pilot edit error")
PILOT_DELETE_ERROR = _("Pilot delete error")

class PilotList(gui_dialogmodel.DialogModel):
    " Pilots list dialog "
    def __init__(self, *args, **kwargs):
        " __init__(self, Window parent, int id=-1) "
        gui_dialogmodel.DialogModel.__init__(self, *args, **kwargs)

        self.SetTitle( _("Pilots") )
        
        # Set grid columns
        self.list_ctrl.InsertColumn(0, _("Degree"), 'degree', proportion=2)
        self.list_ctrl.InsertColumn(1, _("Name"), 'firstname', proportion=3)
        self.list_ctrl.InsertColumn(2, _("Surname"), 'surname', proportion=4)
        self.list_ctrl.InsertColumn(3, _("Year of birth"), 'year_of_birth', format=wx.LIST_FORMAT_RIGHT, proportion=1.5)
        self.list_ctrl.InsertColumn(4, _("Sex"), 'sex', proportion=1)
        
        # Open data source
        self.datasource = session.query( Pilot ).all()
        count = len(self.datasource)
        if count > 0:
            self.Sort(2)
            self.list_ctrl.SetItemCount(count)
            self.list_ctrl.Select(0)
            self.list_ctrl.Focus(0)
        # Assign edit dialog
        self.edit_dialog = PilotForm
        # Assign error messages
        self.message_insert_error = PILOT_INSERT_ERROR
        self.message_edit_error   = PILOT_EDIT_ERROR
        self.message_delete_error = PILOT_DELETE_ERROR

        self.SetSize( (750, 450) )
        self.SetMinSize( self.GetSize() )
        self.CenterOnParent()

class PilotForm(wx.Dialog):
    " Pilots insert/edit dialog "
    def __init__(self, *args, **kwds):
        " __init__(self, Window parent, int id=-1) "
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.THICK_FRAME
        wx.Dialog.__init__(self, *args, **kwds)
        self.label_degree = wx.StaticText(self, -1, _("Degree"))
        self.label_firstname = wx.StaticText(self, -1, _("Name"))
        self.label_surname = wx.StaticText(self, -1, _("Surname"))
        self.text_degree = wx.TextCtrl(self, -1, "")
        self.text_name = wx.TextCtrl(self, -1, "")
        self.text_surname = wx.TextCtrl(self, -1, "")
        self.label_year_of_birth = wx.StaticText(self, -1, _("Year of birth"))
        self.label_sex = wx.StaticText(self, -1, _("Sex"))
        self.text_year_of_birth = wx.TextCtrl(self, -1, "")
        self.text_sex = wx.TextCtrl(self, -1, "")
        self.label_description = wx.StaticText(self, -1, _("Description"))
        self.text_description = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE|wx.TE_WORDWRAP)
        self.button_ok = wx.Button(self, wx.ID_OK, "")
        self.button_cancel = wx.Button(self, wx.ID_CANCEL, "")

        self.__set_properties()
        self.__do_layout()

        # Bind events
        self.Bind(wx.EVT_TEXT, self.__text_ctrl_change, self.text_sex)

    def __set_properties(self):
        self.SetTitle(_("Pilot"))
        
        fontbold = self.label_firstname.GetFont()
        fontbold.SetWeight(wx.FONTWEIGHT_BOLD)
        self.label_firstname.SetFont(fontbold)
        self.label_surname.SetFont(fontbold)
        
        self.text_degree.SetMinSize((100,-1))
        self.text_name.SetMinSize((200,-1))
        self.text_surname.SetMinSize((200,-1))
        
        self.text_degree.SetMaxLength(15)
        self.text_name.SetMaxLength(24)
        self.text_surname.SetMaxLength(35)
        self.text_year_of_birth.SetMaxLength(4)
        self.text_sex.SetMaxLength(1)
        
        self.text_degree.SetFocus()
        self.button_ok.SetDefault()

    def __do_layout(self):
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_buttons = wx.StdDialogButtonSizer()
        grid_sizer = wx.GridBagSizer(2, 2)
        grid_sizer.Add(self.label_degree, (0, 0), (1, 2), wx.RIGHT|wx.EXPAND, 2)
        grid_sizer.Add(self.label_firstname, (0, 2), (1, 3), wx.LEFT|wx.RIGHT|wx.EXPAND, 2)
        grid_sizer.Add(self.label_surname, (0, 5), (1, 3), wx.LEFT|wx.EXPAND, 2)
        grid_sizer.Add(self.text_degree, (1, 0), (1, 2), wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        grid_sizer.Add(self.text_name, (1, 2), (1, 3), wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        grid_sizer.Add(self.text_surname, (1, 5), (1, 3), wx.LEFT|wx.BOTTOM|wx.EXPAND, 2)
        grid_sizer.Add(self.label_year_of_birth, (2, 0), (1, 2), wx.RIGHT|wx.EXPAND, 2)
        grid_sizer.Add(self.label_sex, (2, 2), (1, 1), wx.LEFT|wx.RIGHT|wx.EXPAND, 2)
        grid_sizer.Add(self.text_year_of_birth, (3, 0), (1, 2), wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        grid_sizer.Add(self.text_sex, (3, 2), (1, 1), wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        grid_sizer.Add(self.label_description, (4, 0), (1, 8), wx.RIGHT|wx.EXPAND, 2)
        grid_sizer.Add(self.text_description, (5, 0), (1, 8), wx.BOTTOM|wx.EXPAND, 2)
        grid_sizer.AddGrowableRow(5)
        grid_sizer.AddGrowableCol(0)
        grid_sizer.AddGrowableCol(1)
        grid_sizer.AddGrowableCol(2)
        grid_sizer.AddGrowableCol(3)
        grid_sizer.AddGrowableCol(4)
        grid_sizer.AddGrowableCol(5)
        grid_sizer.AddGrowableCol(6)
        grid_sizer.AddGrowableCol(7)
        sizer_main.Add(grid_sizer, 1, wx.ALL|wx.EXPAND, 4)
        sizer_buttons.AddButton(self.button_ok)
        sizer_buttons.AddButton(self.button_cancel)
        sizer_buttons.Realize()
        sizer_main.Add(sizer_buttons, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.ALIGN_RIGHT, 4)
        self.SetSizer(sizer_main)
        sizer_main.Fit(self)
        self.Layout()
        self.SetMinSize(self.GetSize())
        self.CenterOnParent()
        
    def __text_ctrl_change(self, evt):
        " __text_ctrl_change(self, evt) - upper case value in the text control "
        ctrl = evt.GetEventObject()
        old = ctrl.GetValue()
        new = old.upper()
        if old != new:
            ctrl.ChangeValue(new)
            ctrl.SetInsertionPointEnd()
        evt.Skip()
    
    def GetData(self):
        " GetData(self) -> Pilot - get cleaned form data "
        if hasattr(self, 'pilot'):
            pilot = self.pilot
        else:
            pilot = Pilot()
        pilot.str_to_column( 'degree', self.text_degree.Value )
        pilot.str_to_column( 'firstname', self.text_name.Value )
        pilot.str_to_column( 'surname', self.text_surname.Value )
        pilot.str_to_column( 'sex', self.text_sex.Value )
        pilot.str_to_column( 'year_of_birth', self.text_year_of_birth.Value )
        pilot.str_to_column( 'description', self.text_description.Value )
        return pilot
    
    def SetData(self, pilot):
        " SetData(self, glidertype) - set form data "
        self.pilot = pilot
        self.text_degree.Value = pilot.column_as_str('degree')
        self.text_name.Value = pilot.column_as_str('firstname')
        self.text_surname.Value = pilot.column_as_str('surname')
        self.text_sex.Value = pilot.column_as_str('sex')
        self.text_year_of_birth.Value = pilot.column_as_str('year_of_birth')
        self.text_description.Value = pilot.column_as_str('description')
