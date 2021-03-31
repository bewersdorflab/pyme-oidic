from oidic import liquid_crystal

import wx
import matplotlib

class LCCalibrationFrame(wx.Frame):
    def __init__(self, parent, scope, lc_driver):
        wx.Frame.__init__(self, parent, title="OIDIC Liquid Crystal Calibration")
        
        self.scope = scope
        self.lc_cal = liquid_crystal.LCCalibration(scope, lc_driver)

        self._init_layout()
        self.plot_calibrations(biases=False)  # We haven't calculated the baises yet

    def _init_layout(self):
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(self._init_plots(), 0, wx.ALL | wx.EXPAND)

        self.SetSizerAndFit(vsizer)

    def _init_ctrls(self):
        # Panel containing wavelength, bias, voltages
        pass

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
        self.dir0.plot(self.lc_cal.volts, self.lc_cal.ret, c='k')
        self.dir1.plot(self.lc_cal.volts, self.lc_cal.ret, c='k')
        self.dir0.set_aspect('equal')
        self.dir1.set_aspect('equal')

        # Label the axes
        self.dir0.set_xlabel('Volts')
        self.dir0.set_ylabel('Path length shift as fraction of central wavelength')
        self.dir1.set_ylabel('Volts')
        self.dir1.set_ylabel('Path length shift as fraction of central wavelength')

        if biases:
            # Plot the locations of the minimum voltages in each direction
            self.dir0.scatter(self.lc_cal.get_dir0_min_volts(), 
                            self.lc_cal.get_dir0_min_ret(),
                            s=80, facecolors='none', edgecolors='r')
            self.dir1.scatter(self.lc_cal.get_dir1_min_volts(), 
                            self.lc_cal.get_dir1_min_ret(),
                            s=80, facecolors='none', edgecolors='r')

            # Plot the locations of +/- bias
