from oidic import reconstruct
import matplotlib.pyplot as plt
import numpy as np
from oidic_simulator import image_model, phase_objects

def test_reconstruction_phase_square():

    # Sampling parameters
    pixel_size = 64.5 
    chip_size = 500   

    # Simulated object parameters
    n2 = 1.56
    n1 = 1.52
    w = 6000
    full_thick = 800
    sample_thick = 500

    # Imaging parameters
    wl = 530                           # wavelength [nm]
    NA = 1.35                           # numerical aperture
    n = 1.0                              # refractive index surrounding the point source
    tau1 = 3*np.pi/2                 # shear angle 1 [rad]
    tau2 = np.pi                         # shear angle 2 [rad]
    d = 70                           # shear distance [nm]
    bias = 0.15                     # bias in [wavelength]# Sampling parameters
    pixel_size = 64.5 
    chip_size = 500   

    # Simulated object parameters
    n2 = 1.56
    n1 = 1.52
    w = 6000
    full_thick = 800
    sample_thick = 500

    # Imaging parameters
    wl = 530                           # wavelength [nm]
    NA = 1.35                           # numerical aperture
    n = 1.0                              # refractive index surrounding the point source
    tau1 = 3*np.pi/2                 # shear angle 1 [rad]
    tau2 = np.pi                         # shear angle 2 [rad]
    d = 12                           # shear distance [nm]
    bias = 0.15                     # bias in [wavelength]

    # Simulate image
    sm, bg = phase_objects.simulate_phase_square(pixel_size, chip_size, wl, w, n1, n2, \
                            full_thick, sample_thick)

    # Create image stacks
    image_stack = image_model.coherent(sm, pixel_size, chip_size, \
                                                wl, NA, n, d, tau1, tau2, bias)
    bg_image_stack = image_model.coherent(bg, pixel_size, chip_size, \
                                                wl, NA, n, d, tau1, tau2, bias)

    # Reconstruction
    opl = reconstruct.reconstruct(image_stack, wl, bias*wl, d, NA,
                    background_stack=bg_image_stack, n_frames=6, reconstruction_type='integrate',
                    shear_bias=tau2-np.pi)

    # Test
    assert (np.max(opl.squeeze()) - (n2-n1)*sample_thick) < 6

test_reconstruction_phase_square()
print('Test is passed')
