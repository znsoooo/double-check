import os
import os.path as osp
import shutil
import hashlib
import datetime

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


def Md5(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def ApplyFilter(folder, dest_folder='', same_path=False, same_data=False):
    relpaths = Walk(folder)
    if not osp.isdir(dest_folder) or not same_path and not same_data:
        return relpaths
    if same_path and not same_data:
        return [relpath for relpath in relpaths if osp.exists(osp.join(dest_folder, relpath))]
    if same_path and same_data:
        return [relpath for relpath in relpaths if osp.exists(osp.join(dest_folder, relpath)) and Md5(osp.join(folder, relpath)) == Md5(osp.join(dest_folder, relpath))]
    if not same_path and same_data:
        Hash = lambda path: (osp.splitext(path)[1].lower(), Md5(path))
        hashes = {Hash(osp.join(dest_folder, relpath)) for relpath in Walk(dest_folder)}
        return [relpath for relpath in relpaths if Hash(osp.join(folder, relpath)) in hashes]


def DeleteFiles(folder, relpaths):
    for relpath in relpaths:
        os.remove(osp.join(folder, relpath))


def CopyFiles(folder, relpaths, dest_folder):
    for relpath in relpaths:
        shutil.copy(osp.join(folder, relpath), osp.join(dest_folder, relpath))


def MoveFiles(folder, relpaths, dest_folder):
    for relpath in relpaths:
        os.rename(osp.join(folder, relpath), osp.join(dest_folder, relpath))


def RenameFiles(folder, relpaths, fmt):
    for relpath in relpaths:
        path = osp.join(folder, relpath)
        stat = os.stat(path)
        date = datetime.datetime.fromtimestamp(stat.st_mtime)
        name2 = fmt
        name2 = name2.replace('$date$', date.strftime('%Y%m%d'))
        name2 = name2.replace('$time$', date.strftime('%H%M%S'))
        name2 = name2.replace('$size$', str(stat.st_size))
        if '$hash$' in name2:
            name2 = name2.replace('$hash$', Md5(path))
        base, ext = osp.splitext(path)
        new_file_path = osp.join(folder, name2 + ext)
        i = 2
        while osp.exists(new_file_path):
            new_file_path = osp.join(folder, name2 + f'({i})' + ext)
            i += 1
        os.rename(path, new_file_path)


def DeleteEmptyFolder(folder):
    for root, dirs, files in os.walk(folder, topdown=False):
        for dir_name in dirs:
            dir_path = osp.join(root, dir_name)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)


class FileListCore(wx.ListCtrl, ListCtrlAutoWidthMixin):
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


class FileList(FileListCore):
    def __init__(self, parent):
        FileListCore.__init__(self, parent)

        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyPressed)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OpenContextMenu)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, lambda e: self.OnExecute(None))

    def OnKeyPressed(self, evt):
        code = evt.GetKeyCode()
        modi = evt.GetModifiers()
        if (modi, code) == (wx.MOD_CONTROL, ord('A')):
            self.SelectAll()
        elif code == wx.WXK_ESCAPE:
            self.SelectNone()
        elif code == wx.WXK_TAB:
            self.SelectReverse()
        elif code == wx.WXK_F5:
            self.ResetFolder()
        elif code == wx.WXK_RETURN:
            self.OnExecute(None)
        elif (modi, code) == (wx.MOD_CONTROL, ord('C')):
            self.OnCopyPath(None)
        else:
            evt.Skip()

    def OpenContextMenu(self, ect):
        # Create a menu
        menu = wx.Menu()

        # Add items to the menu
        menu.Append(101, '打开')
        menu.AppendSeparator()
        menu.Append(102, '打开路径')
        menu.Append(103, '复制路径')
        menu.AppendSeparator()
        menu.Append(104, '删除')
        menu.Append(105, '拷贝到...')
        menu.Append(106, '移动到...')
        menu.Append(107, '重命名...')

        # Bind events to menu items
        self.Bind(wx.EVT_MENU, id=101, handler=self.OnExecute)
        self.Bind(wx.EVT_MENU, id=102, handler=self.OnOpenFolder)
        self.Bind(wx.EVT_MENU, id=103, handler=self.OnCopyPath)
        self.Bind(wx.EVT_MENU, id=104, handler=self.OnDelete)
        self.Bind(wx.EVT_MENU, id=105, handler=self.OnCopyTo)
        self.Bind(wx.EVT_MENU, id=106, handler=self.OnMoveTo)
        self.Bind(wx.EVT_MENU, id=107, handler=self.OnRename)

        # Popup the menu
        self.PopupMenu(menu)
        menu.Destroy()

    def OnExecute(self, evt):
        for path in self.GetSelectedAbsPaths():
            os.startfile(path)

    def OnOpenFolder(self, evt):
        for path in self.GetSelectedAbsPaths():
            os.startfile(osp.dirname(path))

    def OnCopyPath(self, evt):
        paths = self.GetSelectedAbsPaths()
        if paths:
            wx.TheClipboard.Open()
            data = wx.TextDataObject('\n'.join(paths) + '\n')
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()

    def OnDelete(self, evt):
        with wx.MessageDialog(None, '确认删除所选文件', '删除', style=wx.OK | wx.CANCEL) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                DeleteFiles(self.folder, self.GetSelectedRelPaths())
                self.ResetFolder()

    def OnCopyTo(self, evt):
        with wx.DirDialog(None, '选择目标文件夹') as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                target_folder = dlg.GetPath()
                CopyFiles(self.folder, self.GetSelectedRelPaths(), target_folder)
                self.ResetFolder()

    def OnMoveTo(self, evt):
        with wx.DirDialog(None, '选择目标文件夹') as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                target_folder = dlg.GetPath()
                MoveFiles(self.folder, self.GetSelectedRelPaths(), target_folder)
                self.ResetFolder()

    def OnRename(self, evt):
        with wx.TextEntryDialog(None, '输入新文件名:', '重命名', 'file_$date$_$time$$_id$') as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                fmt = dlg.GetValue()
                RenameFiles(self.folder, self.GetSelectedRelPaths(), fmt)
                self.ResetFolder()


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
