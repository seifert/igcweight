" GUI widgets "

import os

from os.path import isfile

import wx

from wx import GetTranslation as _
from lrucache import LRUCache

import settings


thumbnails_cache = LRUCache( size=512 )


def error_message_dialog(parent, message, exception=None):
    " error_message_dialog(Window parent, str message, Exception exception=None) - show error message dialog "
    if settings.DEBUG and exception != None:
        if len(exception.args) > 0:
               message += "\n\n%s" % exception.args[0]
    wx.MessageBox( message, _("Error"), wx.OK | wx.ICON_ERROR, parent )

def info_message_dialog(parent, message):
    " info_message_dialog(Window parent, str message) - show information message dialog "
    wx.MessageBox( message, _("Information"), wx.OK | wx.ICON_INFORMATION, parent )

def GetPhotoBitmap(max_size, photo=None):
    " GetPhotoBitmap(self, Size max_size, Photo photo=None) -> Bitmap - load photo and return bitmap "
    ctrl_w, ctrl_h = max_size
    key_name = photo != None and '%dx%d-%s' % (ctrl_w, ctrl_h, photo.md5) or 'empty-photo'
    
    if key_name in thumbnails_cache:
        return thumbnails_cache[key_name]
    
    # Create bitmap from file
    if photo != None:
        thumbnail_path = os.path.join( settings.IMG_CACHE_DIR, '%s.jpg' % key_name )
        if not isfile(thumbnail_path):
            # if thumbnail doesn't exist, create it
            image = wx.Image( photo.full_path, type=wx.BITMAP_TYPE_JPEG )
            image_w, image_h =  image.GetSize()
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
                image.SaveFile( thumbnail_path, wx.BITMAP_TYPE_JPEG )
        else:
            # Load thumbnail from file
            image = wx.Image( thumbnail_path, type=wx.BITMAP_TYPE_JPEG )
            image_w, image_h =  image.GetSize()
    else:
        # Load empty photo
        image = wx.Image( os.path.join(settings.IMAGES_DIR, 'lphoto.png'), type=wx.BITMAP_TYPE_PNG )
        image_w, image_h =  image.GetSize()
    
    # Resize photo thumbnail
    image.Resize( (ctrl_w, ctrl_h), ( (ctrl_w-image_w)/2, (ctrl_h-image_h)/2 ) )

    bitmap = image.ConvertToBitmap()
    thumbnails_cache[key_name] = bitmap
    return bitmap

class VirtualListCtrl(wx.ListCtrl):
    " VirtualListCtrl(self, Window parent, int id=-1) "
    def __init__(self, parent, id):
        wx.ListCtrl.__init__(self, parent=parent, id=id, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_SINGLE_SEL|wx.SUNKEN_BORDER)
        
        self.GetItemAttrMethod = None
        self.GetItemTextMethod = None
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
        colname = self.__columns[col]['fieldname']
        if self.GetItemTextMethod != None:
            return self.GetItemTextMethod(item, colname)
        else:
            return self.datasource[item].column_as_str(colname)
    
    def OnGetItemAttr(self, item):
        " OnGetItemAttr(self, item) -> wx.ListItemAttr - get and return item attr "
        if self.GetItemAttrMethod != None:
            self.__attr = self.GetItemAttrMethod(item)
            return self.__attr
        else:
            return None
    
    @property
    def current_item(self):
        " current_item(self) -> db item - return currently selected item "
        if self.GetItemCount() > 0 and self.GetSelectedItemCount() == 1:
            return self.datasource[ self.GetFocusedItem() ]
        else:
            None
