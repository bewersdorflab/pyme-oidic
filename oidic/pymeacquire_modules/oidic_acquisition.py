# -*- coding: utf-8 -*-

"""
@author: zacsimile
"""
from PYME.Acquire import xyztc

import numpy as np
import time

class OIDICAcquisitionSettings(object):
    def __init__(self):
        self.frames_to_average = 1
        self.z_stepped=False
        self.num_timepoints = 1

class OIDICAcquisition(xyztc.XYZTCAcquisition):
    def __init__(self, scope, dim_order='XYCZT', stack_settings=None, 
                 time_settings=None, channel_settings=None, backend=xyztc.MemoryBackend,
                 images_to_average=1, background_image=False):
        """Acqusition object for OIDIC microscopy.

        Parameters
        ----------
        images_to_average : int
            Number of images to average for a single OIDIC channel.
        background_image : bool, optional
            Are we acquiring a sample (False) or a background (True) image, by default False
        """
        if channel_settings is None:
            channel_settings = scope.oidic_channel_settings
            
        xyztc.XYZTCAcquisition.__init__(self, scope, dim_order, stack_settings, 
                                        time_settings, channel_settings, backend)

        self.channel_settings = channel_settings

        # How many images do we want to average per frame?
        self.images_to_average = images_to_average
        self.average_num = 0

        # Store images for image averaging
        self.frame_data = None

        # Set some metadata
        self.storage.mdh['OIDIC.BackgroundImage'] = background_image
        self.storage.mdh['NumChannels'] = self.channel_settings.num_channels  #FIXME - this should be saved automatically in the XTZTC metadata

    @classmethod
    def from_spool_settings(cls, scope, settings, backend, backend_kwargs={}, series_name=None, spool_controller=None):
        '''Create an OIDICAcquisition object from a spool_controller settings object'''

        backend_kwargs['series_name'] = series_name

        return cls(scope=scope, 
                   #dim_order=settings.dim_order, 
                   stack_settings=settings.get('stack_settings', None), 
                   time_settings=settings.get('time_settings', None), 
                   channel_settings=settings.get('channel_settings', scope.oidic_channel_settings), 
                   backend=backend, backend_kwargs=backend_kwargs,
                   images_to_average=settings.get('images_to_average', 1),
                   background_image=settings.get('background_image', False))


    def on_frame(self, sender, frameData, **kwargs):
        # Overload xyztc frame data to do image averaging
        # TODO - move out of OIDICAcquisition and into a more general class ???
        if self.images_to_average > 1:
            if self.average_num == 0:
                self.frame_data = np.zeros_like(frameData, dtype='uint16')

            if self.average_num < self.images_to_average:
                self.frame_data += (frameData/self.images_to_average).astype('uint16')  # only add 1/n_images_to_average to the frame
                self.average_num += 1
            else:
                self.average_num = 0
                xyztc.XYZTCAcquisition.on_frame(self, sender, self.frame_data, **kwargs)
        else:
            xyztc.XYZTCAcquisition.on_frame(self, sender, frameData, **kwargs)


    def _init_c(self, channel_settings):
        pass

    def set_c(self, c_idx):
        # self.scope.frameWrangler.stop()
        self.channel_settings.set_c(c_idx)
        # time.sleep(self.channel_settings._settling_time)
        # self.scope.frameWrangler.start()

    def _init_t(self, time_settings):
        pass

    def set_t(self, t_idx):
        pass
