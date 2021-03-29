from oidic import liquid_crystal_calibration

import wx
import matplotlib

class LCCalibrationFrame(wx.Frame):
    def __init__(self, scope):
        wx.Frame.__init__(self, None, title="OIDIC Liquid Crystal Calibration")
        
        self.scope = scope

        self.volts, self.ret = liquid_crystal_calibration.load_calibration()

        self.wavelength = 546.0  # optimal wavelength for prisms (nm)
        self.bias = 0.15  # bias introduced by variable retarder (multiple of lambda)

        self.dir0_min = 2.7  # minimum voltage value for first shear direction (V)
        self.dir1_min = 0.0  # minimum voltage value for second shear direction (V)

    def _init_layout(self):
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(self._init_plots(), 0, wx.ALL | wx.EXPAND)

        self.SetSizerAndFit(vsizer)

    def _init_plots(self):
        """Initialize the plots to show ret vs. volts for two OIDIC shear directions.
        """
        self.figure = matplotlib.figure.Figure()
        plot_panel  = matplotlib.backends.backend_wxagg.FigureCanvasWxAgg(self,-1,self.figure)
        self.dir0 = self.figure.add_subplot(1,2,1)  # first shear direction 
        self.dir1 = self.figure.add_subplot(1,2,2)  # second shear direction

        return plot_panel
    
    def plot_calibrations(self):
        # Clear the axes
        self.dir0.clear()
        self.dir1.clear()

        # Plot the calibration curves
        self.dir0.plot(self.volts, self.ret, c='k')
        self.dir1.plot(self.volts, self.ret, c='k')

        # Label the axes
        self.dir0.set_xlabel('Volts')
        self.dir0.set_ylabel('Normalized wavelength')
        self.dir1.set_ylabel('Volts')
        self.dir1.set_ylabel('Normalized wavelength')

        # Plot the locations of the minimum voltages in each direction
        self.dir0.scatter(self.dir0_min, interpolate_volts(self.dir0_min, self.volts, self.ret),
                          s=80, facecolors='none', edgecolors='r')
        self.dir1.scatter(self.dir1_min, interpolate_volts(self.dir1_min, self.volts, self.ret),
                          s=80, facecolors='none', edgecolors='r')

        # Plot the locations of +/- bias (c='m')
        self.dir0.scatter(self.dir0_min+self.bias, interpolate_volts(self.dir0_min, self.volts, self.ret),
                          s=80, facecolors='none', edgecolors='r')