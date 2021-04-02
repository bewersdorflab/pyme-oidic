from PYME.recipes.base import register_module, ModuleBase
from PYME.recipes.traits import Input, Output, Float

@register_module('ReconstructOPL')
class ReconstructOPL(ModuleBase):
    """
    Reconstruct an optical path length map from an OIDIC image stack.
    """

    image = Input('oidic_stack')
    output = Output('opl')

    # Optical path length ceiling and floor
    # -1.0 implies auto-calculation
    ceil = Float(-1.0)
    floor = Float(-1.0)

    def execute(self, namespace):
        # image = namespace[self.image]
        #
        #
        # opl = ImageStack(processed_data)  # optical path length map
        # opl.mdh.copyEntriesFrom(image.mdh)
        # opl.mdh['Parent'] = image.filename
        # self.complete_metadata(opl)
        # self.namespace[output] = opl
        pass

    def complete_metadata(self, im):
        # im.mdh['OIDIC.opl_ceil'] = self.ceil
        # im.mdh['OIDIC.opl_floor'] = self.floor
        pass