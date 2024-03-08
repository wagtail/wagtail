# pyenchant
#
# Copyright (C) 2004-2008, Ryan Kelly
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
#
# In addition, as a special exception, you are
# given permission to link the code of this program with
# non-LGPL Spelling Provider libraries (eg: a MSFT Office
# spell checker backend) and distribute linked combinations including
# the two.  You must obey the GNU Lesser General Public License in all
# respects for all of the code used other than said providers.  If you modify
# this file, you may extend this exception to your version of the
# file, but you are not obligated to do so.  If you do not wish to
# do so, delete this exception statement from your version.
#
# Major code cleanup and re-write thanks to Phil Mayes, 2007
#
"""

    enchant.checker.wxSpellCheckerDialog: wxPython spellchecker interface

    This module provides the class wxSpellCheckerDialog, which provides
    a wxPython dialog that can be used as an interface to a spell checking
    session.  Currently it is intended as a proof-of-concept and demonstration
    class, but it should be suitable for general-purpose use in a program.

    The class must be given an enchant.checker.SpellChecker object with
    which to operate.  It can (in theory...) be used in modal and non-modal
    modes.  Use Show() when operating on an array of characters as it will
    modify the array in place, meaning other work can be done at the same
    time.  Use ShowModal() when operating on a static string.

"""
_DOC_ERRORS = ["ShowModal"]

import wx


class wxSpellCheckerDialog(wx.Dialog):
    """Simple spellcheck dialog for wxPython

    This class implements a simple spellcheck interface for wxPython,
    in the form of a dialog.  It's intended mainly of an example of
    how to do this, although it should be useful for applications that
    just need a simple graphical spellchecker.

    To use, a SpellChecker instance must be created and passed to the
    dialog before it is shown:

        >>> dlg = wxSpellCheckerDialog(None,-1,"")
        >>> chkr = SpellChecker("en_AU",text)
        >>> dlg.SetSpellChecker(chkr)
        >>> dlg.Show()

    This is most useful when the text to be checked is in the form of
    a character array, as it will be modified in place as the user
    interacts with the dialog.  For checking strings, the final result
    will need to be obtained from the SpellChecker object:

        >>> dlg = wxSpellCheckerDialog(None,-1,"")
        >>> chkr = SpellChecker("en_AU",text)
        >>> dlg.SetSpellChecker(chkr)
        >>> dlg.ShowModal()
        >>> text = dlg.GetSpellChecker().get_text()

    Currently the checker must deal with strings of the same type as
    returned by wxPython - unicode or normal string depending on the
    underlying system.  This needs to be fixed, somehow...
    """

    _DOC_ERRORS = [
        "dlg",
        "chkr",
        "dlg",
        "SetSpellChecker",
        "chkr",
        "dlg",
        "dlg",
        "chkr",
        "dlg",
        "SetSpellChecker",
        "chkr",
        "dlg",
        "ShowModal",
        "dlg",
        "GetSpellChecker",
    ]

    # Remember dialog size across invocations by storing it on the class
    sz = (300, 70)

    def __init__(self, parent=None, id=-1, title="Checking Spelling..."):
        super().__init__(
            parent,
            id,
            title,
            size=wxSpellCheckerDialog.sz,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._numContext = 40
        self._checker = None
        self._buttonsEnabled = True
        self.error_text = wx.TextCtrl(
            self, -1, "", style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH
        )
        self.replace_text = wx.TextCtrl(self, -1, "", style=wx.TE_PROCESS_ENTER)
        self.replace_list = wx.ListBox(self, -1, style=wx.LB_SINGLE)
        self.InitLayout()
        wx.EVT_LISTBOX(self, self.replace_list.GetId(), self.OnReplSelect)
        wx.EVT_LISTBOX_DCLICK(self, self.replace_list.GetId(), self.OnReplace)

    def InitLayout(self):
        """Lay out controls and add buttons."""
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        txtSizer = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.VERTICAL)
        replaceSizer = wx.BoxSizer(wx.HORIZONTAL)
        txtSizer.Add(
            wx.StaticText(self, -1, "Unrecognised Word:"), 0, wx.LEFT | wx.TOP, 5
        )
        txtSizer.Add(self.error_text, 1, wx.ALL | wx.EXPAND, 5)
        replaceSizer.Add(
            wx.StaticText(self, -1, "Replace with:"),
            0,
            wx.ALL | wx.ALIGN_CENTER_VERTICAL,
            5,
        )
        replaceSizer.Add(self.replace_text, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        txtSizer.Add(replaceSizer, 0, wx.EXPAND, 0)
        txtSizer.Add(self.replace_list, 2, wx.ALL | wx.EXPAND, 5)
        sizer.Add(txtSizer, 1, wx.EXPAND, 0)
        self.buttons = []
        for label, action, tip in (
            ("Ignore", self.OnIgnore, "Ignore this word and continue"),
            (
                "Ignore All",
                self.OnIgnoreAll,
                "Ignore all instances of this word and continue",
            ),
            ("Replace", self.OnReplace, "Replace this word"),
            ("Replace All", self.OnReplaceAll, "Replace all instances of this word"),
            ("Add", self.OnAdd, "Add this word to the dictionary"),
            ("Done", self.OnDone, "Finish spell-checking and accept changes"),
        ):
            btn = wx.Button(self, -1, label)
            btn.SetToolTip(wx.ToolTip(tip))
            btnSizer.Add(btn, 0, wx.ALIGN_RIGHT | wx.ALL, 4)
            btn.Bind(wx.EVT_BUTTON, action)
            self.buttons.append(btn)
        sizer.Add(btnSizer, 0, wx.ALL | wx.EXPAND, 5)
        self.SetAutoLayout(True)
        self.SetSizer(sizer)
        sizer.Fit(self)

    def Advance(self):
        """Advance to the next error.

        This method advances the SpellChecker to the next error, if
        any.  It then displays the error and some surrounding context,
        and well as listing the suggested replacements.
        """
        # Disable interaction if no checker
        if self._checker is None:
            self.EnableButtons(False)
            return False
        # Advance to next error, disable if not available
        try:
            self._checker.next()
        except StopIteration:
            self.EnableButtons(False)
            self.error_text.SetValue("")
            self.replace_list.Clear()
            self.replace_text.SetValue("")
            if self.IsModal():  # test needed for SetSpellChecker call
                # auto-exit when checking complete
                self.EndModal(wx.ID_OK)
            return False
        self.EnableButtons()
        # Display error context with erroneous word in red.
        # Restoring default style was misbehaving under win32, so
        # I am forcing the rest of the text to be black.
        self.error_text.SetValue("")
        self.error_text.SetDefaultStyle(wx.TextAttr(wx.BLACK))
        lContext = self._checker.leading_context(self._numContext)
        self.error_text.AppendText(lContext)
        self.error_text.SetDefaultStyle(wx.TextAttr(wx.RED))
        self.error_text.AppendText(self._checker.word)
        self.error_text.SetDefaultStyle(wx.TextAttr(wx.BLACK))
        tContext = self._checker.trailing_context(self._numContext)
        self.error_text.AppendText(tContext)
        # Display suggestions in the replacements list
        suggs = self._checker.suggest()
        self.replace_list.Set(suggs)
        self.replace_text.SetValue(suggs and suggs[0] or "")
        return True

    def EnableButtons(self, state=True):
        """Enable the checking-related buttons"""
        if state != self._buttonsEnabled:
            for btn in self.buttons[:-1]:
                btn.Enable(state)
            self._buttonsEnabled = state

    def GetRepl(self):
        """Get the chosen replacement string."""
        repl = self.replace_text.GetValue()
        return repl

    def OnAdd(self, evt):
        """Callback for the "add" button."""
        self._checker.add()
        self.Advance()

    def OnDone(self, evt):
        """Callback for the "close" button."""
        wxSpellCheckerDialog.sz = self.error_text.GetSizeTuple()
        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.Close()

    def OnIgnore(self, evt):
        """Callback for the "ignore" button.
        This simply advances to the next error.
        """
        self.Advance()

    def OnIgnoreAll(self, evt):
        """Callback for the "ignore all" button."""
        self._checker.ignore_always()
        self.Advance()

    def OnReplace(self, evt):
        """Callback for the "replace" button."""
        repl = self.GetRepl()
        if repl:
            self._checker.replace(repl)
        self.Advance()

    def OnReplaceAll(self, evt):
        """Callback for the "replace all" button."""
        repl = self.GetRepl()
        self._checker.replace_always(repl)
        self.Advance()

    def OnReplSelect(self, evt):
        """Callback when a new replacement option is selected."""
        sel = self.replace_list.GetSelection()
        if sel == -1:
            return
        opt = self.replace_list.GetString(sel)
        self.replace_text.SetValue(opt)

    def GetSpellChecker(self):
        """Get the spell checker object."""
        return self._checker

    def SetSpellChecker(self, chkr):
        """Set the spell checker, advancing to the first error.
        Return True if error(s) to correct, else False."""
        self._checker = chkr
        return self.Advance()


def _test():
    class TestDialog(wxSpellCheckerDialog):
        def __init__(self, *args):
            super().__init__(*args)
            wx.EVT_CLOSE(self, self.OnClose)

        def OnClose(self, evnt):
            chkr = dlg.GetSpellChecker()
            if chkr is not None:
                print(["AFTER:", chkr.get_text()])
            self.Destroy()

    from enchant.checker import SpellChecker

    text = "This is sme text with a fw speling errors in it. Here are a fw more to tst it ut."
    print(["BEFORE:", text])
    app = wx.App(False)
    dlg = TestDialog()
    chkr = SpellChecker("en_US", text)
    dlg.SetSpellChecker(chkr)
    dlg.Show()
    app.MainLoop()


if __name__ == "__main__":
    _test()
