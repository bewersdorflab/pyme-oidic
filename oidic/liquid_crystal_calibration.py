from PYME.config import user_config_dir, update_yaml_keys
from PYME.Acquire.Hardware.ARCoptix import lcdriver

import numpy as np
import pandas as pd
import yaml

config_file = os.path.join(user_config_dir, 'oidic_config.yaml')
config_keys = ['lc_cal_file',           
               'lc_voltage_dir0',
               'lc_voltage_dir1',
               'lc_voltage_dir0_zero',  # zero-bias voltage in direction 0
               'lc_voltage_dir1_zero',  # zero-bias voltage in direction 1
               'lc_bias']               # bias shift
config_defaults = [None, 1.0, 8.0, 2.7, 2.7, 255]

if not os.path.isfile(config_file):
    try:
        #touch our config file
        open(config_file, 'a').close()
    except OSError:
        #we might not be able to write to the home directory
        pass

class LCCalibration(object):
    def __init__(self, scope, lc_driver):
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
        self.lc_driver = lc_driver
        self._num_channels = 6

        # Load the calibration file
        self.volts, self.ret = self.load_calibration_file()

        # Set defaults
        for k, v in zip(config_keys, config_defaults):
            self.__setattr__(k,v)

        # see if we've established an OIDIC dictionary
        self._oidic_config = yaml.safe_load(config_file)

        for k, v in self._oidic_cal:
            self.__setattr__('_'+k,v)

        # Establish and zero out the minus and plus voltages
        self._lc_voltage_dir0_zero_minus = 0
        self._lc_voltage_dir0_zero_plus = 0
        self._lc_voltage_dir1_zero_minus = 0
        self._lc_voltage_dir1_zero_plus = 0

    @property
    def num_channels(self):
        # We can only do 4 or 6 DIC images per OIDIC image
        assert ((self._num_channels == 4) or (self._num_channels == 6))
        return self._num_channels

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
                                    ' under OIDIC-liquid_crystal_cal_file in' \
                                    ' ~/.PYME/oidic_config.yaml.')

        if calibration_file.split('.')[-1] != 'xls':
            raise NotImplementedError('We can only load XLS files.')

        calibration = pd.read_excel(calibration_file)

        # TODO: This is wildly specific to the calibration file from Michael Shribak
        volts = (calibration.to_numpy()[1:,9]).astype(float)
        ret = (calibration.to_numpy()[1:,10]).astype(float)

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
        # Set to minimum bias position (assumes user has manipulated condenser
        # polarizer to bias 0 for current sample)
        self.lc_driver.set_dac_voltage(self._lc_voltage_dir0, 0)
        self.lc_driver.set_dac_voltage(self._lc_voltage_dir0_zero, 1)

    def chan_voltages(self):
        """
        Return liquid crystal voltages per imaging channel (4 or 6).
        """
        chan0 = []  # liquid crystal channel 0 (different than imaging channel)
        chan1 = []  # liquid crystal channel 1
        if self.num_channels == 4:
            chan0 = [self._lc_voltage_dir0,self._lc_voltage_dir0,
                     self._lc_voltage_dir1,self._lc_voltage_dir1]
            chan1 = [self._lc_voltage_dir0_zero_minus,
                    self._lc_voltage_dir0_zero_plus,
                    self._lc_voltage_dir1_zero_minus,
                    self._lc_voltage_dir1_zero_plus]
        elif self.num_channels == 6:
            chan0 = [self._lc_voltage_dir0,self._lc_voltage_dir0,self._lc_voltage_dir0,
                     self._lc_voltage_dir1,self._lc_voltage_dir1,self._lc_voltage_dir1]
            chan1 = [self._lc_voltage_dir0_zero_minus,
                    self._lc_voltage_dir0_zero,
                    self._lc_voltage_dir0_zero_plus,
                    self._lc_voltage_dir1_zero_minus,
                    self._lc_voltage_dir1_zero,
                    self._lc_voltage_dir1_zero_plus]
        return chan0, chan1

    def find_dir1_min(self):
        """
        Find the minimum in dir1 based on set dir0.
        """
        pass

