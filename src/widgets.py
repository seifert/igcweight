" GUI widgets "

import os

import wx
from wx import GetTranslation as _

import settings

def error_message_dialog(parent, message, exception=None):
    " error_message_dialog(parent, message, exception=None) - show error message dialog "
    if settings.DEBUG and exception != None:
        message += "\n\n%s" % str(exception)
    wx.MessageBox( message, _("Error"), wx.OK | wx.ICON_ERROR, parent )

class VirtualListCtrl(wx.ListCtrl):
    " VirtualListCtrl(self, parent, id) "
    def __init__(self, parent, id):
        wx.ListCtrl.__init__(self, parent=parent, id=id, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_SINGLE_SEL|wx.SUNKEN_BORDER)
        
        self.__columns = {}
        self.__column_sum = 0
        
        # Get vertical scroll-bar width
        scroll = wx.ScrollBar(self, -1, style=wx.SB_VERTICAL)
        self.__scroll_w = scroll.GetSize().width
        scroll.Destroy()
        
        self.Bind(wx.EVT_SIZE, self.__OnResize)
    
    def InsertColumn(self, col, heading, fieldname, format=wx.LIST_FORMAT_LEFT, proportion=1):
        " InsertColumn(self, col, heading, fieldname, format=wx.LIST_FORMAT_LEFT, proportion=0) "
        if proportion < 1:
            raise ValueError("'width' attribute must be least then 0")
        self.__columns[col] = { 'proportion': proportion, 'fieldname': fieldname }
        self.__column_sum += proportion
        wx.ListCtrl.InsertColumn(self, col, heading, format)
        # Re-count columns - call self.__OnResize
        self.GetEventHandler().ProcessEvent( wx.SizeEvent( self.GetSize() ) )
    
    def __OnResize(self, evt):
        " Re-count grid columns size "
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
        " Get column data from datasource "
        return self.datasource[item].column_as_str( self.__columns[col]['fieldname'] )
    
    @property
    def current_item(self):
        " current_item(self) - return currently selected item "
        i = self.GetFocusedItem()
        return i > -1 and self.datasource[i] or None
