from oidic import liquid_crystal

import wx
import matplotlib

class OIDICCalibrationFrame(wx.Frame):
    def __init__(self, parent, scope, lc_driver):
        """
        Calibrate settings for OIDIC acqusition. This is primarily focused on
        the liquid crystals, but also allows the user to set the central wavelength
        and shear distance of the DIC prisms.
        """
        wx.Frame.__init__(self, parent, title="OIDIC Calibration")
        
        self.scope = scope
        self.lc_driver = liquid_crystal.LCCalibration(scope, lc_driver)

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
        self.wavelength = wx.TextCtrl(pan, -1, value=self.lc_driver.get('wavelength'))
        hsizer.Add(self.wavelength, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # shear distance of the external DIC prism
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "Shear distance (nm):"), 0, wx.ALL, 2)
        self.shear = wx.TextCtrl(pan, -1, value='255')
        hsizer.Add(self.shear, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # bias 
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "Bias:"), 0, wx.ALL, 2)
        self.bias = wx.TextCtrl(pan, -1, value=self.lc_driver.get('lc_bias'))
        hsizer.Add(self.bias, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # TODO: Make the following collapsable?

        # shear direction 0 voltage
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "First shear direction voltage:"), 0, wx.ALL, 2)
        self.voltage_dir0 = wx.TextCtrl(pan, -1, value=self.lc_driver.get('_lc_voltage_dir0'))
        hsizer.Add(self.voltage_dir0, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # shear direction 1 voltage
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "Second shear direction voltage:"), 0, wx.ALL, 2)
        self.voltage_dir1 = wx.TextCtrl(pan, -1, value=self.lc_driver.get('_lc_voltage_dir1'))
        hsizer.Add(self.voltage_dir1, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # shear direction 0 bias zero voltage
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "First shear direction zero bias voltage:"), 0, wx.ALL, 2)
        self.voltage_dir0_zero = wx.TextCtrl(pan, -1, value=self.lc_driver.get('_lc_voltage_dir0_zero'))
        hsizer.Add(self.voltage_dir0_zero, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        # shear direction 1 bias zero voltage
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(pan, -1, "Second shear direction zero bias voltage:"), 0, wx.ALL, 2)
        self.voltage_dir1_zero = wx.TextCtrl(pan, -1, value=self.lc_driver.get('_lc_voltage_dir1_zero'))
        hsizer.Add(self.voltage_dir1_zero, 0, wx.ALL, 2)
        vsizer.Add(hsizer, 0, wx.ALL | wx.EXPAND, 0)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.b_calibrate = wx.Button(self, -1, 'Run calibration')
        self.b_calibrate.Bind(wx.EVT_BUTTON, self.on_calibrate)
        hsizer.Add(self.b_calibrate, 0, wx.ALL, 2)
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
        self.dir0.plot(self.lc_driver.volts, self.lc_driver.ret, c='k')
        self.dir1.plot(self.lc_driver.volts, self.lc_driver.ret, c='k')
        self.dir0.set_aspect('equal')
        self.dir1.set_aspect('equal')

        # Label the axes
        self.dir0.set_xlabel('Volts')
        self.dir0.set_ylabel('Path length shift as fraction of central wavelength')
        self.dir1.set_ylabel('Volts')
        self.dir1.set_ylabel('Path length shift as fraction of central wavelength')

        if biases:
            # Plot the locations of the minimum voltages in each direction
            self.dir0.scatter(self.lc_driver.get('lc_voltage_dir0_zero'), 
                              self.lc_driver.get('lc_ret_dir0_zero'),
                              s=80, facecolors='none', edgecolors='r')
            self.dir1.scatter(self.lc_driver.get('lc_voltage_dir1_zero'), 
                              self.lc_driver.get('lc_ret_dir1_zero'),
                              s=80, facecolors='none', edgecolors='r')

            # Plot the locations of +/- bias

    def on_calibrate(self, event=None):
        pass
