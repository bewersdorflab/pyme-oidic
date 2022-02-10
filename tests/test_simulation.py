from oidic import reconstruct
import numpy as np
from oidic import image_model, phase_objects

def test_reconstruct_phase_square():

    # Sampling parameters
    pixel_size = 64.5 
    chip_size = 500   

    # Simulated object parameters
    n2 = 1.56
    n1 = 1.52
    w = 6000
    full_thick = 800
    sample_thick = 500
    
    # Test for 10 times
    test_loop= 0
    deviation = []
    while test_loop<10:
        test_loop += 1
        
        # Imaging parameters randamized
        wl = np.random.randint(500, 600)                # wavelength [nm]
        NA = np.random.uniform(0.5, 1.5)                # numerical aperture
        n = np.random.uniform(1, 2)                   # refractive index surrounding the point source
        tau1 = np.random.uniform(0, 1)*2*np.pi            # shear angle 1 [rad]
        tau2 = tau1 - np.pi/2                            # shear angle 2 [rad]
        d = np.random.randint(50, 200)                   # shear distance [nm]
        bias = np.random.uniform(0.01, 0.5)             # bias in [wavelength]

        # Simulate image
        sm, bg = phase_objects.simulate_phase_square(pixel_size, chip_size, wl, w, n1, n2, \
                                full_thick, sample_thick)

        # Create image stacks
        image_stack = image_model.coherent(sm, pixel_size, chip_size, \
                                                    wl, NA, n, bias, d, tau1, tau2)
        bg_image_stack = image_model.coherent(bg, pixel_size, chip_size, \
                                                    wl, NA, n, bias, d, tau1, tau2)

        # Reconstruction
        opl = reconstruct.reconstruct(image_stack, wl, bias*wl, d, NA,
                        background_stack=bg_image_stack, n_frames=6, reconstruction_type='integrate',
                        shear_bias=tau2-np.pi)

        # Test
        bound1 = int(np.floor(chip_size/2) - np.ceil(w/pixel_size))
        bound2 = int(np.ceil(chip_size/2) + np.ceil(w/pixel_size))
        opl_bg = (np.mean(opl.squeeze()[bound1:bound2, bound1-10:bound1]) + \
                          np.mean(opl.squeeze()[bound1:bound2, bound2:bound2+10]) + \
                          np.mean(opl.squeeze()[bound1-10:bound1, bound1:bound2]) + \
                          np.mean(opl.squeeze()[bound2:bound2+10, bound1:bound2]))/4
        deviation.append(np.abs((np.max(opl.squeeze())-opl_bg)- (n2-n1)*sample_thick))

    return deviation

def test_answer():

    assert test_reconstruct_phase_square() < [4,4,4,4,4,4,4,4,4,4]
        

