from PYME.Acquire import xyztc
import PYME.config

class OIDICAcquisition(xyztc.XYZTCAcquisition):
    def __init__(self, scope, dim_order='XYCZT', stack_settings=None, 
                 time_settings=None, channel_settings=None, backend=xyztc.MemoryBackend):
        xyztc.XYZTCAcquisition.__init__(self, scope, dim_order, stack_settings, 
                                        time_settings, channel_settings, backend)

        # TODO: probably want to import the file in the calibration GUI and then pass the
        # per-session calibration here.
        self.liquid_crystal_calibration = PYME.config.get('OIDIC-liquid_crystal_cal_file', None)
        if self.liquid_crystal_calibration is None:
            raise AttributeError('Please configure a liquid crystal calibration file' \
                                 'under OIDIC-liquid_crystal_cal_file in ~/.PYME/config.yaml.')

    def _init_c(self, channel_settings):
        pass

    def set_c(self, c_idx):
        pass

    def _init_t(self, time_settings):
        pass

    def set_t(self, t_idx):
        pass