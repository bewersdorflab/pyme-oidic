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
        self.background_image = False # TODO - do we really want this in the settings??

class OIDICAcquisition(xyztc.XYZTCAcquisition):
    def __init__(self, scope, dim_order='XYCZT', stack_settings=None, 
                 time_settings=None, channel_settings=None, backend=xyztc.MemoryBackend, backend_kwargs={},
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
                                        time_settings, channel_settings, backend, backend_kwargs=backend_kwargs)

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

        z_stepped = settings.get('z_stepped', scope.oidic_acquisition_settings.z_stepped)
        if z_stepped:
            stack_settings = settings.get('stack_settings', scope.stackSettings)
        else:
            stack_settings = None

        return cls(scope=scope, 
                   #dim_order=settings.dim_order,        
                   stack_settings=settings.get('stack_settings', stack_settings), 
                   time_settings=settings.get('time_settings', xyztc.TimeSettings(num_timepoints=scope.oidic_acquisition_settings.num_timepoints)),
                   channel_settings=settings.get('channel_settings', scope.oidic_channel_settings), 
                   backend=backend, backend_kwargs=backend_kwargs,
                   images_to_average=settings.get('images_to_average', scope.oidic_acquisition_settings.frames_to_average),
                   background_image=settings.get('background_image', scope.oidic_acquisition_settings.background_image))


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


from PYME.IO.acquisition_backends import MemoryBackend
class TiledOIDICAcquisition(xyztc.TiledXYZTCMixin, OIDICAcquisition):
    def __init__(self, scope, dim_order='XYCZT', stack_settings=None, tile_settings=None, channel_settings=None, return_to_start=True, backend=MemoryBackend, backend_kwargs={}, **kwargs):
        """
        """
        
        xyztc.TiledXYZTCMixin.__init__(self, scope, tile_settings)        
        OIDICAcquisition.__init__(self, scope, dim_order=dim_order, stack_settings=stack_settings, 
                                  time_settings={'num_timepoints' : self._scanner.num_tiles}, channel_settings=channel_settings, 
                                  backend=backend, backend_kwargs=backend_kwargs, **kwargs)
        self._return_to_start = return_to_start
    @classmethod
    def from_spool_settings(cls, scope, settings, backend, backend_kwargs={}, series_name=None, spool_controller=None):
        '''Create an XYZTCAcquisition object from a spool_controller settings object'''
    
        backend_kwargs['series_name'] = series_name

        z_stepped = settings.get('z_stepped', scope.oidic_acquisition_settings.z_stepped)
        if z_stepped:
            stack_settings = settings.get('stack_settings', scope.stackSettings)
        else:
            stack_settings = None

        #fix timing when using fake camera
        #TODO - move logic into backend?
        if scope.cam.__class__.__name__ == 'FakeCamera':
            backend_kwargs['spoof_timestamps'] = True
            backend_kwargs['cycle_time'] = scope.cam.GetIntegTime()

        tiling_settings = settings.get('tiling_settings', scope.tile_settings)
    
        return cls(scope=scope, 
                    #dim_order=settings.dim_order, 
                    stack_settings=settings.get('stack_settings', stack_settings), 
                    tile_settings=tiling_settings, 
                    channel_settings=settings.get('channel_settings', scope.oidic_channel_settings), 
                    backend=backend, backend_kwargs=backend_kwargs,
                    images_to_average=settings.get('images_to_average', scope.oidic_acquisition_settings.frames_to_average),
                    background_image=settings.get('background_image', scope.oidic_acquisition_settings.background_image))
    
    
    @classmethod
    def get_frozen_settings(cls, scope, spool_controller=None):
        if scope.oidic_acquisition_settings.z_stepped:
            stack_settings = scope.stack_settings
        else:
            stack_settings = None

        return {'stack_settings' : stack_settings,
            'tiling_settings': getattr(scope, 'tile_settings', {})}