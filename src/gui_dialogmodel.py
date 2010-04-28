" GUI - DialogModel ancestor "

import locale

import wx
from wx import GetTranslation as _

import settings
import gui_forms

from database import session
from gui_widgets import error_message_dialog

class DialogModel(gui_forms.DialogModel):
    " IGC handicap list dialog "
    def __init__(self, *args, **kwargs):
        " __init__(self, Window parent, int id=-1) "
        gui_forms.DialogModel.__init__(self, *args, **kwargs)
        
        self.__edit_dialog = None
        self.message_insert_error = _("Insert error")
        self.message_edit_error   = _("Edit error")
        self.message_delete_error = _("Delete error")
        
        # Pop-up menu
        self.menu_popup = wx.Menu()
        self.menu_new = wx.MenuItem(self.menu_popup, wx.NewId(), _("&New...\tInsert"))
        self.menu_popup.AppendItem(self.menu_new)
        self.menu_properties = wx.MenuItem(self.menu_popup, wx.NewId(), _("&Edit...\tEnter"))
        self.menu_popup.AppendItem(self.menu_properties)
        self.menu_delete = wx.MenuItem(self.menu_popup, wx.NewId(), _("&Delete\tCtrl+Delete"))
        self.menu_popup.AppendItem(self.menu_delete)
        # Hot keys
        self.SetAcceleratorTable( wx.AcceleratorTable(
            [( wx.ACCEL_NORMAL, wx.WXK_INSERT, self.button_new.GetId() ),
             ( wx.ACCEL_NORMAL, wx.WXK_RETURN, self.button_properties.GetId() ),
             ( wx.ACCEL_CTRL, wx.WXK_DELETE, self.button_delete.GetId() ),
            ]
        ) )

        # Bind_events
        self.list_ctrl.Bind( wx.EVT_CONTEXT_MENU, self.__popup_menu )
        self.list_ctrl.Bind( wx.EVT_LEFT_UP, self.__list_ctrl_left_click )
        self.list_ctrl.Bind( wx.EVT_LEFT_DCLICK, self.__properties )
        self.Bind( wx.EVT_LIST_COL_CLICK, self.__sort_datasource, self.list_ctrl )
        self.Bind( wx.EVT_BUTTON, self.__exit, self.button_close )
        self.Bind( wx.EVT_BUTTON, self.__new, self.button_new )
        self.Bind( wx.EVT_BUTTON, self.__properties, self.button_properties )
        self.Bind( wx.EVT_BUTTON, self.__delete, self.button_delete )
        self.Bind( wx.EVT_MENU, self.__new, self.menu_new )
        self.Bind( wx.EVT_MENU, self.__properties, self.menu_properties )
        self.Bind( wx.EVT_MENU, self.__delete, self.menu_delete )
    
    def get_datasource(self):
        " datasource(self) -> list of db items (SQLAlchemy query) "
        return getattr(self.list_ctrl, 'datasource', None)
    def set_datasource(self, value):
        " datasource(self, list value) - set datasource, value is SQLAlchemy query "
        self.list_ctrl.datasource = value
        count = len(self.datasource)
        if count > 0:
            self.Sort(0)
            self.list_ctrl.SetItemCount(count)
            self.list_ctrl.Select(0)
            self.list_ctrl.Focus(0)
        self.__set_enabled_disabled()
    datasource = property(get_datasource, set_datasource)
    
    def get_edit_dialog(self):
        " edit_dialog(self) -> Window class - get edit dialog class "
        return self.__edit_dialog
    def set_edit_dialog(self, value):
        " edit_dialog(self, Window class value) - set edit dialog class "
        self.__edit_dialog = value
        self.__set_enabled_disabled()
    edit_dialog = property(get_edit_dialog, set_edit_dialog)

    def __set_enabled_disabled(self):
        " __set_enabled_disabled(self) - enable or disable controls "
        if self.datasource != None:
            new = True
            count = len(self.datasource)
            if count > 0 and self.list_ctrl.current_item:            
                properties = True
                delete = True
            else:
                properties = False
                delete =  False
        else:
            new = False
            properties = False
            delete = False
            
        self.button_new.Enable(new)
        self.menu_new.Enable(new)
        self.button_properties.Enable(properties)
        self.menu_properties.Enable(properties)
        self.button_delete.Enable(delete)
        self.menu_delete.Enable(delete)
    
    def __popup_menu(self, evt):
        " __on_popup_menu(self, Event evt) - show pop-up menu "
        self.menu_new.Enable( self.button_new.IsEnabled() )
        self.menu_properties.Enable( self.button_properties.IsEnabled() )
        self.menu_delete.Enable( self.button_delete.IsEnabled() )
        pos = evt.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu( self.menu_popup, pos )
    
    def __list_ctrl_left_click(self, evt):
        " __list_ctrl_left_click(self, Event evt) "
        self.__set_enabled_disabled()
        evt.Skip()
    
    def __sort_datasource(self, evt):
        " __sort_datasource(self, evt) - sort datasource, left-click column tile event handler "
        self.Sort( evt.m_col )
    
    def Sort(self, col):
        " Sort(self, long col) - sort list ctrl "
        if self.datasource != None:
            count = len(self.datasource)
            if count > 0:
                colname = self.list_ctrl.GetColumnFieldName( col )
                current_item = self.list_ctrl.current_item
                self.list_ctrl.SetItemCount(0)
                self.datasource.sort( lambda a, b: locale.strcoll( a.column_as_str(colname), b.column_as_str(colname) ) )
                if current_item == None:
                    i = 0
                else:
                    i = self.datasource.index(current_item)
                self.list_ctrl.SetItemCount(count)
                self.list_ctrl.Select(i)
                self.list_ctrl.Focus(i)

    def __exit(self, evt):
        " Exit(self, Event evt) - close button event handler "
        self.OnExit()

    def OnExit(self):
        " OnExit(self) - hide and leave dialog "
        self.Close()

    def __new(self, evt):
        " __new(self, Event evt) - new button event handler "
        if self.button_new.IsEnabled():
            self.OnNew()

    def OnNew(self):
        " OnNew(self) - add new record "
        dlg = self.edit_dialog(self)
        try:
            while True:
                try:
                    if dlg.ShowModal() == wx.ID_OK:
                        try:
                            record = dlg.GetData()
                            session.add(record)
                            session.commit()
                            self.list_ctrl.DeleteAllItems()
                            self.datasource.append(record)
                            count = len(self.datasource)
                            self.list_ctrl.SetItemCount(count)
                            self.list_ctrl.Select(count-1)
                            self.list_ctrl.Focus(count-1)
                        finally:
                            self.__set_enabled_disabled()
                    break
                except Exception, e:
                    session.rollback()
                    error_message_dialog( self, self.message_insert_error, e )
        finally:
            dlg.Destroy()

    def __properties(self, evt):
        " __properties(self, Event evt) - properties button event handler "
        if self.button_properties.IsEnabled():
            self.OnProperties()

    def OnProperties(self):
        " OnProperties(self) - edit record "
        dlg = self.edit_dialog(self)
        try:
            record = self.list_ctrl.current_item
            dlg.SetData(record)
            while True:
                try:
                    if dlg.ShowModal() == wx.ID_OK:
                        record = dlg.GetData()
                        session.commit()
                        self.list_ctrl.RefreshItem( self.list_ctrl.GetFocusedItem() )
                    break
                except Exception, e:
                    session.rollback()
                    error_message_dialog( self, self.message_edit_error, e )
        finally:
            dlg.Destroy()

    def __delete(self, evt):
        " __delete(self, Event evt) - delete button event handler "
        if self.button_delete.IsEnabled():
            self.OnDelete()

    def OnDelete(self):
        " OnDelete(self) - delete record "
        record = self.list_ctrl.current_item
        if wx.MessageDialog(self,
                            _("Are you sure to delete %s?") % record,
                            _("Delete %s?") % record,
                            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING
                           ).ShowModal() == wx.ID_YES:
            try:
                i = self.datasource.index(record)
                try:
                    session.delete(record)
                    session.commit()
                    self.list_ctrl.DeleteAllItems()
                    del( self.datasource[i] )
                    i = i - 1
                    i = i >= 0 and i or 0
                    self.list_ctrl.SetItemCount( len(self.datasource) )
                    self.list_ctrl.Select(i)
                    self.list_ctrl.Focus(i)
                finally:
                    self.__set_enabled_disabled()
            except Exception, e:
                session.rollback()
                error_message_dialog( self, self.message_delete_error, e )
