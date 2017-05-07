"""
GUI - Preferences dialog window
"""

import re
import locale
import decimal

import wx
from wx import GetTranslation as _

pat = re.compile(r"\%s" % locale.localeconv()['decimal_point'])


def str_to_decimal(val):
    """
    str_to_decimal(str val) -> Decimal - convert string to Decimal
    """
    return decimal.Decimal(pat.sub('.', val))


class Preferences(wx.Dialog):

    def __init__(self, *args, **kwds):
        kwds["style"] = (
            wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.THICK_FRAME)
        wx.Dialog.__init__(self, *args, **kwds)
        self.label_gear_handicap = wx.StaticText(
            self, -1, _("Gear handicap:"))
        self.text_gear_handicap = wx.TextCtrl(self, -1, "")
        self.label_winglets_handicap = wx.StaticText(
            self, -1, _("Winglets handicap:"))
        self.text_winglets_handicap = wx.TextCtrl(self, -1, "")
        self.label_overweight_handicap = wx.StaticText(
            self, -1, _("Overweight handicap:"))
        self.text_overweight_handicap = wx.TextCtrl(self, -1, "")
        self.label_step = wx.StaticText(self, -1, _("/"))
        self.text_overweight_step = wx.TextCtrl(self, -1, "")
        self.label_unit = wx.StaticText(self, -1, _("kg"))
        self.label_allowed_difference = wx.StaticText(
            self, -1, _("Allowed difference:"))
        self.text_allowed_difference = wx.TextCtrl(self, -1, "")
        self.button_ok = wx.Button(self, wx.ID_OK, "")
        self.button_cancel = wx.Button(self, wx.ID_CANCEL, "")

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetTitle(_("Preferences"))
        self.button_ok.SetDefault()

        self.text_gear_handicap.SetFocus()

    def __do_layout(self):
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_buttons = wx.StdDialogButtonSizer()
        grid_sizer = wx.FlexGridSizer(5, 2, 4, 4)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer.Add(
            self.label_gear_handicap, 0,
            wx.RIGHT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 4)
        grid_sizer.Add(
            self.text_gear_handicap, 0, wx.EXPAND, 0)
        grid_sizer.Add(
            self.label_winglets_handicap, 0,
            wx.RIGHT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 4)
        grid_sizer.Add(
            self.text_winglets_handicap, 0, wx.EXPAND, 0)
        grid_sizer.Add(
            self.label_overweight_handicap, 0,
            wx.RIGHT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_1.Add(
            self.text_overweight_handicap, 1, 0, 0)
        sizer_1.Add(
            self.label_step, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
            4)
        sizer_1.Add(
            self.text_overweight_step, 1, 0, 0)
        sizer_1.Add(
            self.label_unit, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 4)
        grid_sizer.Add(
            sizer_1, 1, wx.EXPAND, 0)
        grid_sizer.Add(
            self.label_allowed_difference, 0,
            wx.RIGHT | wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 4)
        grid_sizer.Add(
            self.text_allowed_difference, 0, wx.EXPAND, 0)
        grid_sizer.AddGrowableCol(1)
        sizer_main.Add(grid_sizer, 1, wx.ALL | wx.EXPAND, 4)
        sizer_buttons.AddButton(self.button_ok)
        sizer_buttons.AddButton(self.button_cancel)
        sizer_buttons.Realize()
        sizer_main.Add(
            sizer_buttons, 0,
            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.TOP | wx.ALIGN_RIGHT, 4)

        self.SetSizer(sizer_main)
        self.SetMinSize(self.BestSize)
        self.SetMaxSize((-1, self.GetBestSize().height))
        sizer_main.Fit(self)
        self.Layout()
        self.CenterOnParent()

    def __get_gear_handicap(self):
        return str_to_decimal(self.text_gear_handicap.Value)

    def __set_gear_handicap(self, value):
        self.text_gear_handicap.Value = locale.str(value)

    gear_handicap = property(__get_gear_handicap, __set_gear_handicap)

    def __get_winglets_handicap(self):
        return str_to_decimal(self.text_winglets_handicap.Value)

    def __set_winglets_handicap(self, value):
        self.text_winglets_handicap.Value = locale.str(value)

    winglets_handicap = property(
        __get_winglets_handicap, __set_winglets_handicap)

    def __get_overweight_handicap(self):
        return str_to_decimal(self.text_overweight_handicap.Value)

    def __set_overweight_handicap(self, value):
        self.text_overweight_handicap.Value = locale.str(value)

    overweight_handicap = property(
        __get_overweight_handicap, __set_overweight_handicap)

    def __get_overweight_step(self):
        return int(self.text_overweight_step.Value)

    def __set_overweight_step(self, value):
        self.text_overweight_step.Value = locale.format('%d', value)

    overweight_step = property(__get_overweight_step, __set_overweight_step)

    def __get_allowed_difference(self):
        return int(self.text_allowed_difference.Value)

    def __set_allowed_difference(self, value):
        self.text_allowed_difference.Value = locale.format('%d', value)

    allowed_difference = property(__get_allowed_difference, __set_allowed_difference)
