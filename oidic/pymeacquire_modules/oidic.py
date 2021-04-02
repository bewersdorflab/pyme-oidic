from PYME.Acquire import xyztc

class OIDICAcquisition(xyztc.XYZTCAcquisition):
    def __init__(self, scope, dim_order='XYCZT', stack_settings=None, 
                 time_settings=None, channel_settings=None, backend=xyztc.MemoryBackend,
                 background_image=False):
        """Acqusition object for OIDIC microscopy.

        Parameters
        ----------
        background_image : bool, optional
            Are we acquiring a sample (False) or a background (True) image, by default False
        """
        xyztc.XYZTCAcquisition.__init__(self, scope, dim_order, stack_settings, 
                                        time_settings, channel_settings, backend)

        # Set some metadata
        self.storage.mdh['BackgroundImage'] = background_image

    def _init_c(self, channel_settings):
        pass

    def set_c(self, c_idx):
        self.scope.channel_settings.set_c(c_idx)

    def _init_t(self, time_settings):
        pass

    def set_t(self, t_idx):
        pass
