import numpy as np

def simulate_phase_square(pixel_size, chip_size, wl, w, n1, n2, \
                          full_thick, sample_thick):
    """
    Build a simulated phase object in a square shape, 
    consisting of a sample and background
   
    Parameters
    ----------
    pixel_size : float
        Effective pixel size of camera chip in nm
    chip_size : int
        How many pixels on the camera chip
    wl : float
        Wavelength of emitted light in nm   
    w: float
        Half width in x and y direction of the sample in nm
    n1: float
        Background refractive index
    n2: float
        Sample refractive index
    full_thick: float
        Full object thickness in nm
    sample_thick: float 
        Sample thickness in nm
    
    Returns
    -------
    sm : np.array
        Phase shift of light passing through the object
    bg: np.array
        Phase shift of light passing through only the background
    """
    
    duration = pixel_size * chip_size
    N = chip_size
    sample_rate = N / duration
    x = np.linspace(-duration/2, duration/2, N)
    y = x
    X, Y = np.meshgrid(x, y)
    
    sm = np.ones_like(X)*n1*2*np.pi*full_thick/wl
    sm[(Y>=-w)&(Y<=w)&(X>=-w)&(X<=w)] *= n2/n1*sample_thick/full_thick+\
                                            (1-sample_thick/full_thick)
    bg = np.ones_like(X)*n1*2*np.pi*full_thick/wl
    
    return sm, bg
    