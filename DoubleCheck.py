import os
import os.path as osp

import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin


__title__ = 'Double Check'
__version__ = 'v0.1.0'


def Walk(path):
    relpaths = []
    for root, dirs, files in os.walk(path):
        for file in files:
            relpath = osp.relpath(osp.join(root, file), path)
            relpaths.append(relpath)
    return relpaths


class FileList(wx.ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT)
        ListCtrlAutoWidthMixin.__init__(self)

        self.folder = None
        self.relpaths = []

        self.InsertColumn(0, '文件')

    def SetFolder(self, path):
        self.folder = path
        self.DeleteAllItems()
        self.relpaths = Walk(self.folder)
        for relpath in self.relpaths:
            self.Append([relpath])

    def ResetFolder(self):
        self.SetFolder(self.folder)

    def GetSelectedRows(self):
        row = self.GetFirstSelected()
        rows = []
        while row != -1:
            rows.append(row)
            row = self.GetNextSelected(row)
        return rows

    def GetSelectedRelPaths(self):
        return [self.relpaths[row] for row in self.GetSelectedRows()]

    def GetSelectedAbsPaths(self):
        return [osp.join(self.folder, self.relpaths[row]) for row in self.GetSelectedRows()]

    def SelectAll(self):
        self.Select(-1)

    def SelectNone(self):
        self.Select(-1, False)

    def SelectReverse(self):
        for i in range(self.GetItemCount()):
            self.Select(i, not self.IsSelected(i))


border = 4

class FolderBrowser(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.folder = wx.DirPickerCtrl(self)
        self.filelist = FileList(self)

        self.cb_path = wx.CheckBox(self, -1, '路径相同')
        self.cb_data = wx.CheckBox(self, -1, '内容相同')

        self.btn_delete = wx.Button(self, -1, '删除')
        self.btn_move   = wx.Button(self, -1, '移动')
        self.btn_rename = wx.Button(self, -1, '复制')
        self.btn_rename = wx.Button(self, -1, '重命名')
        self.btn_deldir = wx.Button(self, -1, '删除空目录')

        box2 = wx.BoxSizer()
        box2.Add((1, 1),          1, wx.EXPAND)
        box2.Add(self.cb_path,    0, wx.EXPAND | wx.LEFT, border)
        box2.Add(self.cb_data,    0, wx.EXPAND | wx.LEFT, border)
        box2.Add(self.btn_delete, 0, wx.EXPAND | wx.LEFT, border)
        box2.Add(self.btn_move,   0, wx.EXPAND | wx.LEFT, border)
        box2.Add(self.btn_rename, 0, wx.EXPAND | wx.LEFT, border)
        box2.Add(self.btn_deldir, 0, wx.EXPAND | wx.LEFT, border)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.folder,   0, wx.EXPAND)
        box.Add(self.filelist, 1, wx.EXPAND | wx.TOP, border)
        box.Add(box2,          0, wx.EXPAND | wx.TOP, border)

        self.SetSizer(box)

        self.folder.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnSetFolder)
        self.Bind(wx.EVT_CHECKBOX, self.OnFilter)

    def OnSetFolder(self, evt):
        self.filelist.SetFolder(self.folder.GetPath())

    def OnFilter(self, evt):
        pass


class MyPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # - Init widgets ----------

        self.left = FolderBrowser(self)
        self.right = FolderBrowser(self)

        # - Set layout ----------

        box = wx.BoxSizer()
        box.Add(self.left,  1, wx.EXPAND | wx.ALL,           border)
        box.Add(self.right, 1, wx.EXPAND | wx.ALL - wx.LEFT, border)

        self.SetSizer(box)
        self.Layout()


class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, f'{__title__} - {__version__}', size=(1200, 800))
        self.panel = MyPanel(self)
        self.Center()
        self.Show()


if __name__ == '__main__':
    app = wx.App()
    frame = MyFrame()
    app.MainLoop()
