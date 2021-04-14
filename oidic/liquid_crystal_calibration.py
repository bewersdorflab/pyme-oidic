from PYME.config import user_config_dir, update_yaml_keys
from PYME.Acquire.Hardware.ARCoptix import lcdriver
from PYME.IO import MetaDataHandler

import numpy as np
import pandas as pd
import yaml
import os

import logging
logger = logging.getLogger(__name__)

config_file = os.path.join(user_config_dir, 'oidic_config.yaml')
config_keys = ['lc_cal_file',           # xls file containing path length shift as fraction of central wavelength vs. volts
               'lc_cal_file_source',    # origin of the calibration file
               'lc_voltage_dir0',       # voltage for shear direction 0
               'lc_voltage_dir1',       # voltage for shear direciton 1
               'lc_voltage_dir0_zero',  # zero-bias voltage in direction 0
               'lc_voltage_dir1_zero',  # zero-bias voltage in direction 1
               'lc_bias',               # bias shift
               'wavelength',            # central wavelength, prism-specific rather than lc-specific
               'shear_distance']        # shear distance of prism
config_defaults = [None, 'mbl', 1.0, 8.0, 2.7, 2.7, 0.15, 546.0, 255.0]  # default values for config_keys, respectively

if not os.path.isfile(config_file):
    try:
        #touch our config file
        open(config_file, 'a').close()
    except OSError:
        #we might not be able to write to the home directory
        pass

class LCCalibration(object):
    def __init__(self, scope):
        """
        Channel settings object that operates on and stores the liquid crystal 
        calibration and controls for the OIDIC microscope.

        Parameters
        ----------
        scope : PYME.Acquire.microscope.microscope
            PYME microscope object
        """
        
        # attach scope and liquid crystal controller
        self.scope = scope
        self.lc_driver = scope.lc_driver
        self._num_channels = 6

        # see if we've established an OIDIC dictionary
        with open(config_file,'r') as config_data:
            try:
                self._oidic_config = yaml.safe_load(config_data)
            except:
                self._oidic_config = {}

        # Set defaults
        for k, v in zip(config_keys, config_defaults):
            if k in self._oidic_config:
                self.__setattr__('_'+k,self._oidic_config.get(k))
            else:
                self.__setattr__('_'+k,v)

        # Load the calibration file
        self.volts, self.ret = self.load_calibration_file()

        # Establish and zero out the minus and plus voltages
        self.populate_bias_voltages()

        # Empty lc channel voltages
        self.populate_chan_voltages()

        # Channel metadata
        self.mdh = MetaDataHandler.NestedClassMDHandler()
        MetaDataHandler.provideStartMetadata.append(self.provide_channel_metadata)

    @property
    def num_channels(self):
        # We can only do 4 or 6 DIC images per OIDIC image
        assert ((self._num_channels == 4) or (self._num_channels == 6))
        return self._num_channels

    def get(self, k):
        # This may seem weird but we need some of the attributes we create
        # on the fly for plotting in the liquid crystal calibration GUI
        # that we don't need at all in the saved liquid crystal properties
        # dictionary
        return self.__getattribute__('_'+k)

    def set_num_channels(self, n):
        if ((n == 4) or (n == 6)):
            self._num_channels = n
        else:
            raise RuntimeError('Please choose the number of channels as 4 or 6.')

    def provide_channel_metadata(self):
        try:
            self.mdh.setEntry('OIDIC.Bias', self._lc_bias)
            self.mdh.setEntry('OIDIC.Wavelength', self._wavelength)
            self.mdh.setEntry('OIDIC.LCVoltageDir0', self._lc_voltage_dir0)
            self.mdh.setEntry('OIDIC.LCVoltageDir1', self._lc_voltage_dir1)
            self.mdh.setEntry('OIDIC.LCVoltageDir0Zero', self._lc_voltage_dir0_zero)
            self.mdh.setEntry('OIDIC.LCVoltageDir1Zero', self._lc_voltage_dir1_zero)
        except:
            logger.exception('Error writing liquid crystal metadata.')

    def load_calibration_file(self):
        """Load the OIDIC liquid crystal calibration curve.

        Returns
        -------
        volts : np.array
            Voltage applied to liquid crystals
        ret : np.array
            Normalized bias, as a fraction of central wavelength (usually 546 nm) 
            for OIDIC prisms. Value in [0,1].
        """
        # Grab the liquid crystal calibration file
        calibration_file = self._lc_cal_file
        if calibration_file is None:
            raise AttributeError('Please configure a liquid crystal calibration file' \
                                    ' under lc_cal_file in' \
                                    ' ~/.PYME/oidic_config.yaml.')

        calibration_file_source = self._lc_cal_file_source
        if calibration_file_source is None:
            calibration_file_source = 'mbl'
            logger.warning('Defaulted to calibration file source of mbl.')

        # TODO: Currently only mbl (Marine Biological Lab) is supported.
        if calibration_file_source == 'mbl':
            if calibration_file.split('.')[-1] != 'xls':
                raise NotImplementedError('We can only load XLS files from MBL.')

            calibration = pd.read_excel(calibration_file)

            # Specific to the calibration file from Michael Shribak
            volts = (calibration.to_numpy()[1:,9]).astype(float)
            ret = (calibration.to_numpy()[1:,10]).astype(float)
        else:
            raise NotImplementedError('File source not supported.')

        return volts, ret

    def update_oidic_config(self):
        d = {}
        for k in config_keys:
            d[k] = self.__getattribute__('_'+k)
        self._oidic_config = d

    def write_oidic_config(self):
        self.update_oidic_config()
        update_yaml_keys(config_file, self._oidic_config)

    def interpolate_ret(self, vals):
        # Get a ret value from the calibration curve based on volts
        return np.interp(vals,self.volts,self.ret)

    def interpolate_volts(self, vals):
        # Get a volts value from the interpolation curve based on ret
        return np.interp(vals,self.ret,self.volts)

    def initialize_calibration(self):
        """
        Set to minimum bias position (assumes user has manipulated condenser
        polarizer to bias 0 for current sample) in shear direction 0. Assumes
        user will follow by setting physical optical components to match before
        hitting run calibration.

        Note we do not call set_c here in case we are in the self.num_channels==4 case
        """
        self.lc_driver.set_dac_voltage(self._lc_voltage_dir0, 0)
        self.lc_driver.set_dac_voltage(self._lc_voltage_dir0_zero, 1)

    def populate_bias_voltages(self):
        self._lc_voltage_dir0_zero_minus = 0
        self._lc_voltage_dir0_zero_plus = 0
        self._lc_voltage_dir1_zero_minus = 0
        self._lc_voltage_dir1_zero_plus = 0

        if self._lc_bias and self._lc_voltage_dir0_zero:
            self._lc_ret_dir0_zero = self.interpolate_ret(self._lc_voltage_dir0_zero)
            self._lc_ret_dir0_zero_minus = self._lc_ret_dir0_zero - self._lc_bias
            self._lc_ret_dir0_zero_plus = self._lc_ret_dir0_zero + self._lc_bias
            self._lc_voltage_dir0_zero_minus = self.interpolate_volts(self._lc_ret_dir0_zero_minus)
            self._lc_voltage_dir0_zero_plus = self.interpolate_volts(self._lc_ret_dir0_zero_plus)

        if self._lc_bias and self._lc_voltage_dir1_zero:
            self._lc_ret_dir1_zero = self.interpolate_ret(self._lc_voltage_dir1_zero)
            self._lc_ret_dir1_zero_minus = self._lc_ret_dir1_zero - self._lc_bias
            self._lc_ret_dir1_zero_plus = self._lc_ret_dir1_zero + self._lc_bias
            self._lc_voltage_dir1_zero_minus = self.interpolate_volts(self._lc_ret_dir1_zero_minus)
            self._lc_voltage_dir1_zero_plus = self.interpolate_volts(self._lc_ret_dir1_zero_plus)

    def populate_chan_voltages(self):
        """
        Set liquid crystal voltages per imaging channel (4 or 6).
        """
        self._chan0 = []  # shear direction
        self._chan1 = []  # bias

        if self.num_channels == 4:
            self._chan0 = [self._lc_voltage_dir0,self._lc_voltage_dir0,
                           self._lc_voltage_dir1,self._lc_voltage_dir1]
            self._chan1 = [self._lc_voltage_dir0_zero_minus,
                           self._lc_voltage_dir0_zero_plus,
                           self._lc_voltage_dir1_zero_minus,
                           self._lc_voltage_dir1_zero_plus]
        elif self.num_channels == 6:
            self._chan0 = [self._lc_voltage_dir0,self._lc_voltage_dir0,self._lc_voltage_dir0,
                           self._lc_voltage_dir1,self._lc_voltage_dir1,self._lc_voltage_dir1]
            self._chan1 = [self._lc_voltage_dir0_zero_minus,
                           self._lc_voltage_dir0_zero,
                           self._lc_voltage_dir0_zero_plus,
                           self._lc_voltage_dir1_zero_minus,
                           self._lc_voltage_dir1_zero,
                           self._lc_voltage_dir1_zero_plus]
        else:
            raise NotImplementedError(f"{self.num_channels} channels not supported")

    def set_c(self, c_idx):
        """
        Move the liquid crystals into the current channel configuration.
        """
        if (not self._chan0) or (not self._chan1):
            raise RuntimeError('Please call populate_chan_voltages first.')

        if c_idx < 0:
            raise RuntimeError('What are you doing???')

        if not (c_idx < self.num_channels):
            raise RuntimeError(f"{c_idx} is larger than {self.num_channels-1}")

        self.lc_driver.set_dac_voltage(self._chan0[c_idx], 0)
        self.lc_driver.set_dac_voltage(self._chan1[c_idx], 1)

    def set_bias(self, bias):
        self._lc_bias = bias
        self.populate_bias_voltages()
        self.populate_chan_voltages()

    def set_wavelength(self, wavelength):
        self._wavelength = wavelength

    def set_shear_distance(self, shear_distance):
        self._shear_distance = shear_distance

    def set_lc_voltage_dir0(self, v):
        self._lc_voltage_dir0 = v
        self.populate_bias_voltages()
        self.populate_chan_voltages()

    def set_lc_voltage_dir1(self, v):
        self._lc_voltage_dir1 = v
        self.populate_bias_voltages()
        self.populate_chan_voltages()

    def set_lc_voltage_dir0_zero(self, v):
        self._lc_voltage_dir0_zero = v
        self.populate_bias_voltages()
        self.populate_chan_voltages()

    def set_lc_voltage_dir1_zero(self, v):
        self._lc_voltage_dir1_zero = v
        self.populate_bias_voltages()
        self.populate_chan_voltages()

    def find_dir1_zero_bias(self, time_delay=0.3):
        """
        Find the zero bias voltage in dir1 based on set dir0.

        Parameters
        ----------
        time_delay : float
            Time to wait after applying lc_voltage. 0.3 s is usually
            safe, but this can be optionally modified.
        """

        import time
        
        # We should already be initialized but double check
        self.initialize_calibration()
        # Grab this mean as a sanity check
        dir0_zero_mean = scope.frameWrangler.currentFrame.mean()

        # Switch to the other shear direction and grid search for the minimum mean
        self.lc_driver.set_dac_voltage(self._lc_voltage_dir1, 1)
        volts_to_check = np.linspace(self._lc_voltage_dir0_zero-1.5, self._lc_voltage_dir0_zero+1.5, 10)
        means = np.zeros_like(volts_to_check)
        for i, v in enumerate(volts_to_check):
            self.lc_driver.set_dac_voltage(v, 0)
            time.sleep(time_delay)
            means[i] = scope.frameWrangler.currentFrame.mean()

        # Fit a quadratic to find the minimum voltage
        res = np.polyfit(volts_to_check,means,2)
        min_v = -res[1]/(2*res[0])  # should be analytic, single zero

        # record the minimum voltage
        self.set_lc_voltage_dir1_zero(min_v)

        # Grab the mean values
        self.lc_driver.set_dac_voltage(min_v, 0)
        time.sleep(time_delay)
        dir1_zero_mean = scope.frameWrangler.currentFrame.mean()

        # Alert the user to the mean values (should be equal)
        dialog = wx.MessageDialog(None, 
                                  f"Dir 0 Mean: {dir0_zero_mean}    "\
                                  f"Dir 1 Mean: {dir1_zero_mean}", 
                                  "Mean values should be roughly equivalent", wx.OK)
        dialog.ShowModal()
