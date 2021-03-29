from PYME.Acquire import xyztc

class OIDICAcquisition(xyztc.XYZTCAcquisition):
    def __init__(self, scope, dim_order='XYCZT', stack_settings=None, 
                 time_settings=None, channel_settings=None, backend=xyztc.MemoryBackend,
                 images_per_acquisition=6, background_image=False):
        """Acqusition object for OIDIC microscopy.

        Parameters
        ----------
        images_per_acquisition : int, optional
            Acquire 4 or 6 images to create a DIC image, by default 6
        background_image : bool, optional
            Are we acquiring a sample (False) or a background (True) image, by default False
        """
        xyztc.XYZTCAcquisition.__init__(self, scope, dim_order, stack_settings, 
                                        time_settings, channel_settings, backend)

        # We can only do 4 or 6 DIC images per OIDIC image
        assert ((images_per_acquisition == 4) or (images_per_acquisition == 6))

        # Set some metadata
        self.storage.mdh['NumImages'] = images_per_acquisition
        self.storage.mdh['BackgroundImage'] = background_image

    def _init_c(self, channel_settings):
        pass

    def set_c(self, c_idx):
        pass

    def _init_t(self, time_settings):
        pass

    def set_t(self, t_idx):
        pass