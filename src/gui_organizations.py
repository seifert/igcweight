" GUI - Organizations list "

import wx
from wx import GetTranslation as _

import gui_dialogmodel

from database import session
from models import Organization

class OrganizationList(gui_dialogmodel.DialogModel):
    " Organizations or countries list dialog "
    def __init__(self, *args, **kwargs):
        " __init__(self, Window parent, int id=-1) "
        gui_dialogmodel.DialogModel.__init__(self, *args, **kwargs)

        self.SetTitle( _("Organizations or countries") )
        
        # Set grid columns
        self.list_ctrl.InsertColumn(0, _("Name"), 'name', proportion=4)
        self.list_ctrl.InsertColumn(1, _("Code"), 'code', proportion=1)
        
        # Open data source
        self.datasource = session.query( Organization ).order_by( Organization.name ).all()
        # Assign edit dialog
        self.edit_dialog = OrganizationForm
        # Assign error messages
        self.message_insert_error = _("Organization insert error")
        self.message_edit_error   = _("Organization edit error")
        self.message_delete_error = _("Organization delete error")

        self.SetSize( (750, 450) )
        self.SetMinSize( self.GetSize() )
        self.CenterOnParent()

class OrganizationForm(wx.Dialog):
    " Organization/country insert/edit dialog "
    def __init__(self, *args, **kwds):
        " __init__(self, Window parent, int id=-1) "
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.THICK_FRAME
        wx.Dialog.__init__(self, *args, **kwds)
        self.label_name = wx.StaticText(self, -1, _("Name"))
        self.label_code = wx.StaticText(self, -1, _("Code"))
        self.text_name = wx.TextCtrl(self, -1, "")
        self.text_code = wx.TextCtrl(self, -1, "")
        self.label_description = wx.StaticText(self, -1, _("Description"))
        self.text_description = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE|wx.TE_WORDWRAP)
        self.button_ok = wx.Button(self, wx.ID_OK, "")
        self.button_cancel = wx.Button(self, wx.ID_CANCEL, "")

        self.__set_properties()
        self.__do_layout()

        # Bind events
        self.Bind(wx.EVT_TEXT, self.__text_ctrl_change, self.text_code)
        
        self.SetMinSize(self.GetSize())
        self.CenterOnParent()

    def __set_properties(self):
        self.SetTitle(_("Organization or country"))
        
        fontbold = self.label_name.GetFont()
        fontbold.SetWeight(wx.FONTWEIGHT_BOLD)
        self.label_name.SetFont(fontbold)
        self.label_code.SetFont(fontbold)
        
        self.text_name.SetMinSize((400,-1))
        self.text_code.SetMinSize((100,-1))
        
        self.text_name.SetMaxLength(50)
        self.text_code.SetMaxLength(4)
        
        self.text_name.SetFocus()
        self.button_ok.SetDefault()

    def __do_layout(self):
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_buttons = wx.StdDialogButtonSizer()
        grid_sizer = wx.GridBagSizer(2, 2)
        grid_sizer.Add(self.label_name, (0, 0), (1, 1), wx.RIGHT|wx.EXPAND, 2)
        grid_sizer.Add(self.label_code, (0, 1), (1, 1), wx.LEFT|wx.RIGHT|wx.EXPAND, 2)
        grid_sizer.Add(self.text_name, (1, 0), (1, 1), wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        grid_sizer.Add(self.text_code, (1, 1), (1, 1), wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 2)
        grid_sizer.Add(self.label_description, (2, 0), (1, 2), wx.RIGHT|wx.EXPAND, 2)
        grid_sizer.Add(self.text_description, (3, 0), (1, 2), wx.BOTTOM|wx.EXPAND, 2)
        grid_sizer.AddGrowableRow(3)
        grid_sizer.AddGrowableCol(0)
        grid_sizer.AddGrowableCol(1)
        sizer_main.Add(grid_sizer, 1, wx.ALL|wx.EXPAND, 4)
        sizer_buttons.AddButton(self.button_ok)
        sizer_buttons.AddButton(self.button_cancel)
        sizer_buttons.Realize()
        sizer_main.Add(sizer_buttons, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.ALIGN_RIGHT, 4)
        self.SetSizer(sizer_main)
        sizer_main.Fit(self)
        self.Layout()
        
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
        " GetData(self) -> Organization - get cleaned form data "
        if hasattr(self, 'organization'):
            organization = self.organization
        else:
            organization = Organization()
        organization.str_to_column( 'name', self.text_name.Value )
        organization.str_to_column( 'code', self.text_code.Value )
        organization.str_to_column( 'description', self.text_description.Value )
        return organization
    
    def SetData(self, organization):
        " SetData(self, organization) - set form data "
        self.organization = organization
        self.text_name.Value = organization.column_as_str('name')
        self.text_code.Value = organization.column_as_str('code')
        self.text_description.Value = organization.column_as_str('description')
