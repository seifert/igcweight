" GUI widgets "

import os

import wx
from wx import GetTranslation as _

import settings

def error_message_dialog(parent, message, exception=None):
    " error_message_dialog(Window parent, str message, Exception exception=None) - show error message dialog "
    if settings.DEBUG and exception != None:
        if len(exception.args) > 0:
               message += "\n\n%s" % exception.args[0]
    wx.MessageBox( message, _("Error"), wx.OK | wx.ICON_ERROR, parent )

class VirtualListCtrl(wx.ListCtrl):
    " VirtualListCtrl(self, Window parent, int id=-1) "
    def __init__(self, parent, id):
        wx.ListCtrl.__init__(self, parent=parent, id=id, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_SINGLE_SEL|wx.SUNKEN_BORDER)
        
        self.__columns = {}
        self.__column_sum = 0
        
        # Get vertical scroll-bar width
        scroll = wx.ScrollBar(self, -1, style=wx.SB_VERTICAL)
        self.__scroll_w = scroll.GetSize().width
        scroll.Destroy()
        
        # Bind_events
        self.Bind(wx.EVT_SIZE, self.__OnResize)
    
    def InsertColumn(self, col, heading, fieldname, format=wx.LIST_FORMAT_LEFT, proportion=1):
        " InsertColumn(self, long col, str heading, str fieldname, int format=wx.LIST_FORMAT_LEFT, int proportion=0) "
        if proportion < 1:
            raise ValueError("'width' attribute must be least then 0")
        self.__columns[col] = { 'proportion': proportion, 'fieldname': fieldname }
        self.__column_sum += proportion
        wx.ListCtrl.InsertColumn(self, col, heading, format)
        # Re-count columns - call self.__OnResize
        self.GetEventHandler().ProcessEvent( wx.SizeEvent( self.GetSize() ) )
    
    def GetColumnFieldName(self, col):
        " InsertColumn(self, long col) -> str - get column db field name "
        return self.__columns[col]['fieldname']
    
    def __OnResize(self, evt):
        " __OnResize(self, Event evt) - re-count grid columns size "
        if self.__column_sum > 0:
            # Get client size
            client_w = self.GetClientSize().width
            # Different re-count on Windows and Linux
            if os.name == 'posix':
                client_w = client_w - self.__scroll_w
            # Count proportion
            s = client_w / self.__column_sum
            # Count columns width
            total_w = 0
            for i in range( len(self.__columns) ):
                col_w = s * self.__columns[i]['proportion']
                total_w += col_w
                self.SetColumnWidth( i, col_w )
            # Re-count last column (can be round inaccuracy) 
            self.SetColumnWidth( i, col_w + client_w - total_w )
        evt.Skip()

    def OnGetItemText(self, item, col):
        " OnGetItemText(self, int item, int col) -> str - get column data from datasource "
        return self.datasource[item].column_as_str( self.__columns[col]['fieldname'] )
    
    @property
    def current_item(self):
        " current_item(self) -> db item - return currently selected item "
        return self.GetSelectedItemCount()==1 and self.datasource[ self.GetFocusedItem() ] or None
