# -*- coding: utf-8 -*-

"""
@author: zacsimile
"""
import PYME.ui.manualFoldPanel as afp
from PYME.Acquire.ui import seqdialog
from PYME.Acquire.xyztc import MemoryBackend

from . import oidic_acquisition
from PYME.Acquire import xyztc
from PYME.ui import cascading_layout

import wx
import logging

logger = logging.getLogger(__name__)

class OIDICAcquisitionPanel(wx.Panel, cascading_layout.CascadingLayoutMixin):
    def __init__(self, parent, scope, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        
        self.scope=scope
        if not hasattr(self.scope, 'oidic_acquisition_settings'):
            # TODO - should we be shoving this into the scope, or potentially the spool controller?
            self.scope.oidic_acquisition_settings = oidic_acquisition.OIDICAcquisitionSettings()

        self._background_image = False

        self._init_ctrls()

    def _oidic_pan(self):
        pan = wx.Panel(parent=self, style=wx.TAB_TRAVERSAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)

        # 6 or 4-image OIDIC protocol?
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "Mode:"), 0, wx.ALL | wx.EXPAND, 2)
        self.oidic_four = wx.RadioButton(pan, -1, '4', style=wx.RB_GROUP)
        self.oidic_four.Bind(wx.EVT_RADIOBUTTON, self.set_acquisition_four)
        hsizer.Add(self.oidic_four, 0, wx.ALL | wx.EXPAND, 2)
        self.oidic_six = wx.RadioButton(pan, -1, '6')
        self.oidic_six.Bind(wx.EVT_RADIOBUTTON, self.set_acquisition_six)
        hsizer.Add(self.oidic_six, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)
        self.oidic_six.SetValue(True)  # enable 6 images per acqusition by default

        # Sample or background image?
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sample = wx.RadioButton(pan, -1, 'Sample', style=wx.RB_GROUP)
        hsizer.Add(self.sample, 0, wx.ALL | wx.EXPAND, 2)
        self.background = wx.RadioButton(pan, -1, 'Background')
        hsizer.Add(self.background, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)
        self.sample.SetValue(True)  # enable sample acqusition by default (why?)
        self.background.Bind(wx.EVT_RADIOBUTTON, self.on_toggle_background)

        # bias (normalized to wavelength) applied to variable phase retarder
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "Bias:"), 0, wx.ALL, 2)
        self.bias = wx.TextCtrl(pan, -1, value='0.15')
        self.bias.Bind(wx.EVT_KILL_FOCUS, self.on_bias_change)
        hsizer.Add(self.bias, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # image averaging decides how many frames to average over per capture
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "# images to average:"), 0, wx.ALL, 2)
        self.images_to_average = wx.TextCtrl(pan, -1, value='1')
        self.images_to_average.Bind(wx.EVT_KILL_FOCUS, self.on_averaging_change)
        hsizer.Add(self.images_to_average, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "# Timepoints:"), 0, wx.ALL, 2)
        self.tcNumTimepoints = wx.TextCtrl(pan, -1, value='1')
        self.tcNumTimepoints.Bind(wx.EVT_KILL_FOCUS, self.on_timepoints_change)
        hsizer.Add(self.tcNumTimepoints, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # Z-stepped?
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.standard = wx.RadioButton(pan, -1, 'Standard', style=wx.RB_GROUP)
        self.standard.Bind(wx.EVT_RADIOBUTTON, self.toggle_z_stepped)
        hsizer.Add(self.standard, 0, wx.ALL | wx.EXPAND, 2)
        self.z_stepped = wx.RadioButton(pan, -1, 'Z-stepped')
        self.z_stepped.Bind(wx.EVT_RADIOBUTTON, self.toggle_z_stepped)
        hsizer.Add(self.z_stepped, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)
        self.standard.SetValue(True)  # non z-stepped by default
        self.scope.stackSettings.SetSeqLength(1)

        if not hasattr(self.scope, 'stackSettings'):
            self.z_stepped.Disable()

        

        # # Go/stop buttons
        # hsizer = wx.BoxSizer(wx.HORIZONTAL)
        # self.b_go = wx.Button(pan, -1, 'Acquire Stack')
        # self.b_go.Bind(wx.EVT_BUTTON, self.on_go)
        # hsizer.Add(self.b_go, 0, wx.ALL, 2)
        # self.b_stop = wx.Button(pan, -1, 'Stop')
        # self.b_stop.Disable()
        # self.b_stop.Bind(wx.EVT_BUTTON, self.on_stop)
        # hsizer.Add(self.b_stop, 0, wx.ALL, 2)
        # vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        pan.SetSizerAndFit(vsizer)

        return pan

    def _init_ctrls(self):

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(self._oidic_pan(), 0, wx.ALL | wx.EXPAND, 2)
        

        if hasattr(self.scope, 'stackSettings'):
            clp = afp.collapsingPane(self, caption='Z stepping ...')
            self._seq_panel = seqdialog.seqPanel(clp, self.scope, mode='sequence')
            clp.AddNewElement(self._seq_panel)
            vsizer.Add(clp, 0, wx.ALL | wx.EXPAND, 2)
            self.seq_pan = clp
            self.seq_pan.Show(self.scope.oidic_acquisition_settings.z_stepped)
        
        self.SetSizerAndFit(vsizer)

    def on_bias_change(self, event=None):
        self.scope.oidic_channel_settings.set_bias(float(self.bias.GetValue()))
        event.Skip()

    def set_acquisition_four(self, event=None):
        # Four images per OIDIC acqusition
        self.scope.oidic_channel_settings.set_num_channels(4)

    def set_acquisition_six(self, event=None):
        # Six images per OIDIC acqusition
        self.scope.oidic_channel_settings.set_num_channels(6)

    def toggle_z_stepped(self, event=None):
        # Display the z-stepping panel if we're z-stepping
        self.scope.oidic_acquisition_settings.z_stepped = self.z_stepped.GetValue()
        self.seq_pan.Show(self.scope.oidic_acquisition_settings.z_stepped)
        self.seq_pan.Fold(not self.scope.oidic_acquisition_settings.z_stepped)
        #self.seq_pan.cascading_layout()
        
    def on_averaging_change(self, event=None):
        self.scope.oidic_acquisition_settings.frames_to_average = int(self.images_to_average.GetValue())
        event.Skip()

    def on_timepoints_change(self, event=None):
        self.scope.oidic_acquisition_settings.num_timepoints = int(self.tcNumTimepoints.GetValue())
        event.Skip()

    def on_toggle_background(self, event=None):
        self.scope.oidic_acquisition_settings.background_image = self.background.GetValue()

class _OIDICAcquisitionPanel(afp.foldingPane):
    def __init__(self, parent, scope, **kwargs):
        afp.foldingPane.__init__(self, parent, caption='OIDIC', **kwargs)
        
        self.scope=scope
        self._background_image = False

        if hasattr(self.scope, 'stackSettings'):
            # Keep track of this for toggling purposes
            self._seq_length = self.scope.stackSettings.GetSeqLength()

        self._init_ctrls()

    def _oidic_pan(self):
        pan = wx.Panel(parent=self, style=wx.TAB_TRAVERSAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)

        # 6 or 4-image OIDIC protocol?
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "Mode:"), 0, wx.ALL | wx.EXPAND, 2)
        self.oidic_four = wx.RadioButton(pan, -1, '4', style=wx.RB_GROUP)
        self.oidic_four.Bind(wx.EVT_RADIOBUTTON, self.set_acquisition_four)
        hsizer.Add(self.oidic_four, 0, wx.ALL | wx.EXPAND, 2)
        self.oidic_six = wx.RadioButton(pan, -1, '6')
        self.oidic_six.Bind(wx.EVT_RADIOBUTTON, self.set_acquisition_six)
        hsizer.Add(self.oidic_six, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)
        self.oidic_six.SetValue(True)  # enable 6 images per acqusition by default

        # Sample or background image?
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sample = wx.RadioButton(pan, -1, 'Sample', style=wx.RB_GROUP)
        hsizer.Add(self.sample, 0, wx.ALL | wx.EXPAND, 2)
        self.background = wx.RadioButton(pan, -1, 'Background')
        hsizer.Add(self.background, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)
        self.sample.SetValue(True)  # enable sample acqusition by default (why?)

        # bias (normalized to wavelength) applied to variable phase retarder
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "Bias:"), 0, wx.ALL, 2)
        self.bias = wx.TextCtrl(pan, -1, value='0.15')
        self.bias.Bind(wx.EVT_KILL_FOCUS, self.on_bias_change)
        hsizer.Add(self.bias, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # image averaging decides how many frames to average over per capture
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "# images to average:"), 0, wx.ALL, 2)
        self.images_to_average = wx.TextCtrl(pan, -1, value='1')
        hsizer.Add(self.images_to_average, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # Z-stepped?
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.standard = wx.RadioButton(pan, -1, 'Standard', style=wx.RB_GROUP)
        self.standard.Bind(wx.EVT_RADIOBUTTON, self.toggle_z_stepped)
        hsizer.Add(self.standard, 0, wx.ALL | wx.EXPAND, 2)
        self.z_stepped = wx.RadioButton(pan, -1, 'Z-stepped')
        self.z_stepped.Bind(wx.EVT_RADIOBUTTON, self.toggle_z_stepped)
        hsizer.Add(self.z_stepped, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)
        self.standard.SetValue(True)  # non z-stepped by default
        self.scope.stackSettings.SetSeqLength(1)

        if not hasattr(self.scope, 'stackSettings'):
            self.z_stepped.Disable()

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "# Timepoints:"), 0, wx.ALL, 2)
        self.tcNumTimepoints = wx.TextCtrl(pan, -1, value='1')
        hsizer.Add(self.tcNumTimepoints, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # Go/stop buttons
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.b_go = wx.Button(pan, -1, 'Acquire Stack')
        self.b_go.Bind(wx.EVT_BUTTON, self.on_go)
        hsizer.Add(self.b_go, 0, wx.ALL, 2)
        self.b_stop = wx.Button(pan, -1, 'Stop')
        self.b_stop.Disable()
        self.b_stop.Bind(wx.EVT_BUTTON, self.on_stop)
        hsizer.Add(self.b_stop, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        pan.SetSizerAndFit(vsizer)

        return pan

    def _init_ctrls(self):

        self.AddNewElement(self._oidic_pan())

        if hasattr(self.scope, 'stackSettings'):
            clp = afp.collapsingPane(self, caption='Z stepping ...')
            self._seq_panel = seqdialog.seqPanel(clp, self.scope, mode='sequence')
            clp.AddNewElement(self._seq_panel)
            self.AddNewElement(clp)
            self.seq_pan = clp

    def on_go(self, event=None):

        self.scope.oidic = oidic_acquisition.OIDICAcquisition(self.scope,
                                                              images_to_average=float(self.images_to_average.GetValue()),
                                                              background_image=bool(self.background.GetValue()),
                                                              time_settings=xyztc.TimeSettings(num_timepoints=int(self.tcNumTimepoints.GetValue())))
        self.scope.oidic.on_series_end.connect(self.on_stack)

        self.scope.oidic.start()

        self.b_go.Disable()
        self.b_stop.Enable()

    def on_stop(self, event=None):
        self.scope.oidic.finish()

        self.b_go.Enable()
        self.b_stop.Disable()

    def on_stack(self, **kwargs):
        self.scope.oidic.on_series_end.disconnect(self.on_stack)

        # potentially redundant
        self.b_go.Enable()
        self.b_stop.Disable()

        wx.CallAfter(self.visualize_stack)

    def visualize_stack(self):
        from PYME.DSView import ViewIm3D
        ViewIm3D(self.scope.oidic.storage.image)

    def on_bias_change(self, event=None):
        self.scope.oidic_channel_settings.set_bias(float(self.bias.GetValue()))

    def set_acquisition_four(self, event=None):
        # Four images per OIDIC acqusition
        self.scope.oidic_channel_settings.set_num_channels(4)

    def set_acquisition_six(self, event=None):
        # Six images per OIDIC acqusition
        self.scope.oidic_channel_settings.set_num_channels(6)

    def toggle_z_stepped(self, event=None):
        # Display the z-stepping panel if we're z-stepping
        if self.z_stepped.GetValue():
            self.scope.stackSettings.SetSeqLength(self._seq_length)
            if self.seq_pan.folded:
                self.seq_pan.OnFold()
        else:
            if not self.seq_pan.folded:
                self.seq_pan.OnFold()
            # Save the current sequence length
            self._seq_length = self.scope.stackSettings.GetSeqLength()
            self.scope.stackSettings.SetSeqLength(1)

    