# -*- coding: utf-8 -*-

"""
@author: zacsimile
"""
from os import name
from PYME.recipes.base import register_module, ModuleBase
from PYME.recipes.traits import Input, Output, Float, Int, Enum

@register_module('ReconstructOIDIC')
class ReconstructOIDIC(ModuleBase):
    """
    Reconstruct an optical path length map (or Riesz image) from an OIDIC image stack.
    """

    image = Input('oidic_stack')
    background_image = Input('background_oidic_stack')
    output = Output('oidic')

    wavelength=Float(530.0)
    bias=Float(0.15)
    shear_distance = Float(172.0)
    numerical_aperture = Float(1.35)
    n_frames = Int(6)
    reconstruction_type = Enum(['integrate', 'riesz'])

    def execute(self, namespace):
        from oidic import reconstruct
        from PYME.IO.image import ImageStack

        image = namespace[self.image]
        if self.background_image is not None:
            background_image = namespace[self.background_image]
        else:
            background_image = None
        
        processed_data = reconstruct.reconstruct(image, self.wavelength, self.bias*self.wavelength,
                                                 self.shear_distance, self.numerical_aperture,
                                                 background_image, self.n_frames,
                                                 self.reconstruction_type)
        
        opl = ImageStack(data=processed_data)  # TODO: add PYME.IO.DataSources.BaseDataSource.XYZTCWrapper?
                                               # XYZTCWrapper(ArrayDataSource(processed_data), 'XYZTC', processed_data.shape[2], processed_data.shape[3], 1)
        
        opl.mdh.copyEntriesFrom(image.mdh)
        opl.mdh['Parent'] = image.filename
        opl.mdh['OIDIC.BackgroundParent'] = background_image.filename
        self.complete_metadata(opl)
        
        namespace[self.output] = opl

    def complete_metadata(self, im):
        im.mdh['OIDIC.ReconstructionWavelength'] = self.wavelength
        im.mdh['OIDIC.ReconstructionBias'] = self.bias
        im.mdh['OIDIC.ReconstructionShear'] = self.wavelength
        im.mdh['OIDIC.ReconstructionNumericalAperture'] = self.numerical_aperture
        im.mdh['OIDIC.ReconstructionNumChannels'] = self.n_frames
        im.mdh['OIDIC.ReconstructionType'] = self.reconstruction_type
