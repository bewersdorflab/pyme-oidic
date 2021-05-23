# -*- coding: utf-8 -*-

"""
@author: zacsimile
"""
from . import liquid_crystal_calibration

import wx
import matplotlib

class OIDICCalibrationFrame(wx.Frame):
    def __init__(self, parent, scope):
        """
        Calibrate settings for OIDIC acqusition. This is primarily focused on
        the liquid crystals, but also allows the user to set the central wavelength
        and shear distance of the DIC prisms.
        """
        wx.Frame.__init__(self, parent, title="OIDIC Calibration")
        
        self.scope = scope
        self.lc_ch_set = scope.channel_settings
        self.lc_calibrator = liquid_crystal_calibration.LCCalibrator(self.scope)

        self._init_layout()
        self.plot_calibrations(biases=False)  # We haven't calculated the baises yet

    def _init_layout(self):
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(self._init_ctrls(), 0, wx.ALL | wx.EXPAND)
        vsizer.Add(self._init_plots(), 0, wx.ALL | wx.EXPAND)
        self.SetSizerAndFit(vsizer)

    def _init_ctrls(self):
        # Panel containing wavelength, bias, voltages
        pan = wx.Panel(parent=self, style=wx.TAB_TRAVERSAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)

        # wavelength (should not be edited often)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "Wavelength:"), 0, wx.ALL, 2)
        self.wavelength = wx.TextCtrl(pan, -1, value=str(self.lc_ch_set.get('wavelength')))
        hsizer.Add(self.wavelength, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # shear distance of the external DIC prism
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "Shear distance (nm):"), 0, wx.ALL, 2)
        self.shear_distance = wx.TextCtrl(pan, -1, value=str(self.lc_ch_set.get('shear_distance')))
        hsizer.Add(self.shear_distance, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # capture delay (ms) controls time between captures, a little longer
        # than the liquid crystal settling time
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "Liquid crystal settling time (ms):"), 0, wx.ALL, 2)
        self.settling_time = wx.TextCtrl(pan, -1, value='300')
        hsizer.Add(self.settling_time, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # TODO: Make the following collapsable?

        # shear direction 0 voltage
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "First shear direction voltage:"), 0, wx.ALL, 2)
        self.voltage_dir0 = wx.TextCtrl(pan, -1, value=str(self.lc_ch_set.get('lc_voltage_dir0')))
        hsizer.Add(self.voltage_dir0, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # shear direction 1 voltage
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "Second shear direction voltage:"), 0, wx.ALL, 2)
        self.voltage_dir1 = wx.TextCtrl(pan, -1, value=str(self.lc_ch_set.get('lc_voltage_dir1')))
        hsizer.Add(self.voltage_dir1, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # shear direction 0 bias zero voltage
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "First shear direction zero bias voltage:"), 0, wx.ALL, 2)
        self.voltage_dir0_zero = wx.TextCtrl(pan, -1, value=str(self.lc_ch_set.get('lc_voltage_dir0_zero')))
        hsizer.Add(self.voltage_dir0_zero, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # shear direction 1 bias zero voltage
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "Second shear direction zero bias voltage:"), 0, wx.ALL, 2)
        self.voltage_dir1_zero = wx.TextCtrl(pan, -1, value=str(self.lc_ch_set.get('lc_voltage_dir1_zero')))
        hsizer.Add(self.voltage_dir1_zero, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.b_initialize = wx.Button(pan, -1, 'Initialize calibration')
        self.b_initialize.Bind(wx.EVT_BUTTON, self.on_initialize)
        hsizer.Add(self.b_initialize, 0, wx.ALL, 2)
        self.b_calibrate = wx.Button(pan, -1, 'Run calibration')
        self.b_calibrate.Bind(wx.EVT_BUTTON, self.on_calibrate)
        hsizer.Add(self.b_calibrate, 0, wx.ALL, 2)
        self.b_save = wx.Button(pan, -1, 'Save calibration')
        self.b_save.Bind(wx.EVT_BUTTON, self.on_save)
        hsizer.Add(self.b_save, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        pan.SetSizerAndFit(vsizer)

        return pan

    def _init_plots(self):
        """Initialize the plots to show ret vs. volts for two OIDIC shear directions.
        """
        self.figure = matplotlib.figure.Figure()
        plot_panel  = matplotlib.backends.backend_wxagg.FigureCanvasWxAgg(self,-1,self.figure)
        self.dir0 = self.figure.add_subplot(1,2,1)  # first shear direction 
        self.dir1 = self.figure.add_subplot(1,2,2)  # second shear direction

        return plot_panel
    
    def plot_calibrations(self, biases=True):
        # Clear the axes
        self.dir0.clear()
        self.dir1.clear()

        # Plot the calibration curves
        self.dir0.plot(self.lc_ch_set.volts, self.lc_ch_set.ret, c='k')
        self.dir1.plot(self.lc_ch_set.volts, self.lc_ch_set.ret, c='k')
        # self.dir0.set_aspect('equal')
        # self.dir1.set_aspect('equal')

        # Label the axes
        self.dir0.set_xlabel('Volts')
        self.dir0.set_ylabel('Path length shift as fraction of central wavelength')
        self.dir1.set_ylabel('Volts')
        self.dir1.set_ylabel('Path length shift as fraction of central wavelength')

        if biases:
            # Plot the locations of the minimum voltages in each direction
            self.dir0.scatter(self.lc_ch_set.get('lc_voltage_dir0_zero'), 
                              self.lc_ch_set.get('lc_ret_dir0_zero'),
                              s=80, facecolors='none', edgecolors='r')
            self.dir1.scatter(self.lc_ch_set.get('lc_voltage_dir1_zero'), 
                              self.lc_ch_set.get('lc_ret_dir1_zero'),
                              s=80, facecolors='none', edgecolors='r')

            # Plot the locations of +/- bias

        self.figure.canvas.draw()

    def on_initialize(self, event=None):
        """
        Set the OIDIC state to shear direction 0, zero bias
        """
        # Grab the latest and greatest voltages we need
        self.lc_ch_set.set_lc_voltage_dir0(float(self.voltage_dir0.GetValue()))
        self.lc_ch_set.set_lc_voltage_dir0_zero(float(self.voltage_dir0_zero.GetValue()))

        # initialize
        self.lc_ch_set.initialize_calibration()

    def on_calibrate(self, event=None):
        self.set_calibration_values()

        self.lc_calibrator.on_calibrated.connect(self.on_calibrated)
        self.lc_calibrator.run()

    def on_calibrated(self, **kwargs):
        self.lc_calibrator.on_calibrated.disconnect(self.on_calibrated)

        self.voltage_dir1_zero.SetValue(str(self.lc_ch_set.get('lc_voltage_dir1_zero')))
        self.voltage_dir1_zero.Update()
        self.voltage_dir1_zero.Refresh()

        self.plot_calibrations()

        self.Update()
        self.Refresh()

    def set_calibration_values(self):
        # Grab the latest and greatest voltages/values we need
        self.lc_ch_set.set_lc_voltage_dir0(float(self.voltage_dir0.GetValue()))
        self.lc_ch_set.set_lc_voltage_dir0_zero(float(self.voltage_dir0_zero.GetValue()))
        self.lc_ch_set.set_lc_voltage_dir1(float(self.voltage_dir1.GetValue()))
        self.lc_ch_set.set_lc_voltage_dir1_zero(float(self.voltage_dir1_zero.GetValue()))
        self.lc_ch_set.set_bias(float(self.lc_ch_set.get('lc_bias')))
        self.lc_ch_set.set_delay(float(self.settling_time.GetValue()))

        # We don't strictly need these for calibration but they are associated
        self.lc_ch_set.set_wavelength(float(self.wavelength.GetValue()))
        self.lc_ch_set.set_shear_distance(float(self.shear_distance.GetValue()))

    def on_save(self, event=None):
        self.set_calibration_values()
        self.lc_ch_set.write_oidic_config()
        