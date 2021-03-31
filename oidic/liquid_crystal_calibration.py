import PYME.config
from PYME.Acquire.Hardware.ARCoptix import lcdriver

import numpy as np
import pandas as pd

class LCCalibration(object):
    def __init__(self, scope, lc_driver):
        """
        Object that operates on and stores the liquid crystal calibration and
        controls for the OIDIC microscope.

        Parameters
        ----------
        scope : PYME.Acquire.microscope.microscope
            PYME microscope object
        """
        
        # attach scope and liquid crystal controller
        self.scope = scope
        self.lc_driver = lc_driver

        # Load the calibration file
        self.volts, self.ret = self.load_calibration_file()

        # Load previously-stored shear direction voltages (lc channel 0)
        self._dir0_volts = PYME.config.get('OIDIC-lc_voltage_dir0', None)
        self._dir1_volts = PYME.config.get('OIDIC-lc_voltage_dir1', None)

        # If there are no previously-stored shear direction voltages, set them
        if self._dir0_volts is None:
            self.set_dir0_volts(1.0)
        if self._dir1_volts is None:
            self.set_dir1_volts(8.0)

        # Load previously-stored bias voltages (lc channel 1)
        self._dir0_min_volts = PYME.config.get('OIDIC-lc_voltage_dir0_min', None)
        self._dir1_min_volts = PYME.config.get('OIDIC-lc_voltage_dir1_min', None)

        # If there are no previously-stored bias voltages, set them
        if self._dir0_min_volts is None:
            self.set_dir0_min_volts(2.7)
        if self._dir1_min_volts is None:
            self.set_dir1_min_volts(2.7)

        # Wavelength and bias parameters
        # optimal wavelength for prisms (nm)
        self.wavelength = PYME.config.get('OIDIC-lc_wavelength', None)
        # bias introduced by variable retarder (multiple of lambda)
        self.bias = PYME.config.get('OIDIC-lc_bias', None)

        if self.wavelength = None:


    def load_calibration_file(self):
        """Load the OIDIC liquid crystal calibration curve.

        Returns
        -------
        volts : np.array
            Voltage applied to liquid crystals
        ret : np.array
            Normalized wavelength, referenced to ideal wavelength (usually 546 nm) 
            for OIDIC prisms. Value in [0,1].
        """
        # Grab the liquid crystal calibration file
        calibration_file = PYME.config.get('OIDIC-liquid_crystal_cal_file', None)
        if calibration_file is None:
            raise AttributeError('Please configure a liquid crystal calibration file' \
                                    'under OIDIC-liquid_crystal_cal_file in ~/.PYME/config.yaml.')

        if calibration_file.split('.')[-1] != 'xls':
            raise NotImplementedError('We can only currently load XLS files.')

        calibration = pd.read_excel(calibration_file)

        # TODO: This is wildly specific to the calibration file from Michael Shribak
        volts, ret = (calibration.to_numpy()[1:,9]).astype(float), (calibration.to_numpy()[1:,10]).astype(float)

        return volts, ret

    def interpolate_ret(self, vals):
        # Get a ret value from the calibration curve based on volts
        return np.interp(vals,self.volts,self.ret)

    def interpolate_volts(self, vals):
        # Get a volts value from the interpolation curve based on ret
        return np.interp(vals,self.ret,self.volts)

    def set_wavelength(self, wvl):
        PYME.config.update_config({'OIDIC-lc_voltage_dir0_min': v})
        self.wavelength = wvl

    def get_dir0_volts(self):
        # voltage value to set first shear direction (V)
        return self._dir0_volts

    def get_dir1_volts(self):
        # voltage value to set second shear direction (V)
        return self._dir1_volts

    def get_dir0_min_volts(self):
        # minimum bias voltage value for first shear direction (V)
        return self._dir0_min_volts

    def get_dir1_min_volts(self):
        # minimum bias voltage value for second shear direction (V)
        return self._dir1_min_volts

    def set_dir0_min_volts(self, v):
        # set minimum bias voltage value for first shear direction (V)
        PYME.config.update_config({'OIDIC-lc_voltage_dir0_min': v})
        self._dir0_min_volts = v

    def set_dir1_min_volts(self, v):
        # set minimum bias voltage value for second shear direction (V)
        PYME.config.update_config({'OIDIC-lc_voltage_dir1_min': v})
        self._dir1_min_volts = v

    def set_dir0_volts(self, v):
        # set voltage value for first shear direction (V)
        PYME.config.update_config({'OIDIC-lc_voltage_dir0': v})
        self._dir0_volts = v

    def set_dir1_volts(self, v):
        # set voltage value for second shear direction (V)
        PYME.config.update_config({'OIDIC-lc_voltage_dir1': v})
        self._dir1_volts = v

    def get_dir0_min_ret(self):
        # minimum ret value for first shear direction
        return self.interpolate_ret(self.get_dir0_min_volts())

    def get_dir1_min_ret(self):
        # minimum ret value for second shear direction
        return self.interpolate_ret(self.get_dir1_min_volts())

    def initialize_calibration(self):
        # Set to minimum bias position (assumes user has manipulated condenser
        # polarizer to bias 0 for current sample)
        self.lc_driver.set_dac_voltage(self.get_dir0_volts(), 0)
        self.lc_driver.set_dac_voltage(self.get_dir0_min_volts(), 1)

    def find_dir1_min(self):
        """
        Find the minimum in dir1 based on set dir0.
        """
        pass

