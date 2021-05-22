# -*- coding: utf-8 -*-

"""
@author: zacsimile
"""
from PYME.DSView.modules._base import Plugin
from PYME.DSView import dsviewer
from PYME.IO.image import ImageStack
import PYME.ui.manualFoldPanel as afp

from traits.api import HasTraits, Float, Int, Enum
import wx

import logging
logger = logging.getLogger(__name__)

class ReconstructOIDIC(Plugin):

    def __init__(self, dsviewer):
        Plugin.__init__(self, dsviewer)
        dsviewer.AddMenuItem("OIDIC", "Reconstruct", self.on_reconstruct)
        try:
           self.wavelength = self.dsviewer.image.mdh['OIDIC.Wavelength']
           self.bias = self.dsviewer.image.mdh['OIDIC.Bias']
           self.shear_distance = self.dsviewer.image.mdh['OIDIC.ShearDistance']
           self.numerical_aperture = self.dsviewer.image.mdh['OIDIC.Bias']
           self.n_frames = self.dsviewer.image.mdh['NumChannels']
        except:
            self.wavelength = 546.0
            self.bias = 0.15
            self.shear_distance = 255.0
            self.numerical_aperture = 1.0
            self.n_frames = 6
            logger.warning('No OIDIC metadata found, using defaults.')
        

    def on_reconstruct(self, event=None, sender=None, **kwargs):
        from PYME.DSView import ViewIm3D
        from oidic.recipe_modules import reconstruct

        try:
            background_image = ImageStack(filename=self.dsviewer.image.mdh['OIDIC.BackgroundImage'])
        except:
            import os
            dlg = wx.FileDialog(self.dsviewer, message="Open a Background Image...", 
                                defaultDir=os.getcwd(), defaultFile="", style=wx.FD_OPEN)
            if dlg.ShowModal() == wx.ID_OK:
                background_image = ImageStack(filename=dlg.GetPath())
            else:
                background_image = None

        mod = reconstruct.ReconstructOIDIC(wavelength=self.wavelength, bias=self.bias,
                                           shear_distance=self.shear_distance, 
                                           numerical_aperture=self.numerical_aperture,
                                           n_frames=self.n_frames)
        if mod.configure_traits(kind='modal'):
            namespace = {'oidic_stack': self.dsviewer.image, 
                         'background_oidic_stack': background_image}
            mod.execute(namespace)

            ViewIm3D(namespace['oidic'])

def Plug(dsviewer):
    return ReconstructOIDIC(dsviewer)
