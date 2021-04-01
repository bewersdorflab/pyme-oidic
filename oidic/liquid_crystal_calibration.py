from PYME.config import user_config_dir, update_yaml_keys
from PYME.Acquire.Hardware.ARCoptix import lcdriver
from PYME.IO import MetaDataHandler

import numpy as np
import pandas as pd
import yaml

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
               'wavelength']            # central wavelength, prism-specific rather than lc-specific
config_defaults = [None, 'mbl', 1.0, 8.0, 2.7, 2.7, 255.0, 546.0]  # default values for config_keys, respectively

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

        # Load the calibration file
        self.volts, self.ret = self.load_calibration_file()

        # see if we've established an OIDIC dictionary
        self._oidic_config = yaml.safe_load(config_file)

        # Set defaults
        for k, v in zip(config_keys, config_defaults):
            if k in self._oidic_config:
                self.__setattr__('_'+k,self._oidic_config.get('k'))
            else:
                self.__setattr__('_'+k,v)

        # Establish and zero out the minus and plus voltages
        self._lc_voltage_dir0_zero_minus = 0
        self._lc_voltage_dir0_zero_plus = 0
        self._lc_voltage_dir1_zero_minus = 0
        self._lc_voltage_dir1_zero_plus = 0

        # Empty lc channel voltages
        self._chan0 = []  # shear direction
        self._chan1 = []  # bias

        # Channel metadata
        self.mdh = MetaDataHandler.NestedClassMDHandler()
        MetaDataHandler.provideStartMetadata.append(self.provide_channel_metadata)

    @property
    def num_channels(self):
        # We can only do 4 or 6 DIC images per OIDIC image
        assert ((self._num_channels == 4) or (self._num_channels == 6))
        return self._num_channels

    def provide_channel_metadata(self):
        try:
            mdh.setEntry('OIDIC.Bias', self._lc_bias)
            mdh.setEntry('OIDIC.Wavelength', self._wavelength)
            mdh.setEntry('OIDIC.LCVoltageDir0', self._lc_voltage_dir0)
            mdh.setEntry('OIDIC.LCVoltageDir1', self._lc_voltage_dir1)
            mdh.setEntry('OIDIC.LCVoltageDir0Zero', self._lc_voltage_dir0_zero)
            mdh.setEntry('OIDIC.LCVoltageDir1Zero', self._lc_voltage_dir1_zero)
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
                                    ' under OIDIC-liquid_crystal_cal_file in' \
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
        # Set to minimum bias position (assumes user has manipulated condenser
        # polarizer to bias 0 for current sample)
        # Note we do not call set_c here in case we are in the self.num_channels==4 case
        self.lc_driver.set_dac_voltage(self._lc_voltage_dir0, 0)
        self.lc_driver.set_dac_voltage(self._lc_voltage_dir0_zero, 1)

    def populate_bias_voltages(self):
        self._lc_voltage_dir0_zero_minus = 0
        self._lc_voltage_dir0_zero_plus = 0
        self._lc_voltage_dir1_zero_minus = 0
        self._lc_voltage_dir1_zero_plus = 0

        if self._lc_bias and self._lc_voltage_dir0_zero:
            self._lc_voltage_dir0_zero_minus = self.interpolate_volts(self.interpolate_ret(self._lc_voltage_dir0_zero) - self._lc_bias)
            self._lc_voltage_dir0_zero_plus = self.interpolate_volts(self.interpolate_ret(self._lc_voltage_dir0_zero) + self._lc_bias)

        if self._lc_bias and self._lc_voltage_dir1_zero:
            self._lc_voltage_dir1_zero_minus = self.interpolate_volts(self.interpolate_ret(self._lc_voltage_dir1_zero) - self._lc_bias)
            self._lc_voltage_dir1_zero_plus = self.interpolate_volts(self.interpolate_ret(self._lc_voltage_dir1_zero) + self._lc_bias)

    def populate_chan_voltages(self):
        """
        Set liquid crystal voltages per imaging channel (4 or 6).
        """
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

        if not (c_idx < self.num_channels):
            raise RuntimeError(f"{c_idx} is larger than {self.num_channels-1}")

        self.lc_driver.set_dac_voltage(self._chan0[c_idx], 0)
        self.lc_driver.set_dac_voltage(self._chan1[c_idx], 1)

    def find_dir1_zero_bias(self):
        """
        Find the zero bias voltage in dir1 based on set dir0.
        """
        pass

