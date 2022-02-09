import numpy as np
import matplotlib.pyplot as plt  
from mpl_toolkits.mplot3d import Axes3D
import scipy.special as sp
from scipy import signal
from oidic import reconstruct
from PYME.IO.image import ImageStack
from PYME.IO.DataSources.BaseDataSource import XYZTCWrapper
from PYME.IO.DataSources.ArrayDataSource import XYZTCArrayDataSource

def pupil(fx, fy, wl, NA, n):
    """
    Theoretically construct the pupil function.
    
    Parameters
    ----------
    x, y : float
        Coordinates
    wl : float
        Wavelength of emitted light in nm
    n : float
        Refractive index surrounding point source
    NA : float
        Numerical aperture of the optical system
    
    Returns
    -------
    p: np.array
        Array of real values describing the pupil function.
    """
    
    fc = NA/(n*wl)   # cutoff frequency
    p = np.select([fx*fx+fy*fy<=fc*fc, fx*fx+fy*fy>fc*fc], [1, 0])
    
    return p

def coherent_amplitude_psf(x, y, wl, NA, n):
    """
    Theoretically construct the electric field for coherent amplitude PSF in 2D.
    
    Coherent amplitude PSF is the inverse Fourier transform of the pupil function.
    
    Parameters
    ----------
    x, y : float
        Coordinates
    wl : float
        Wavelength of emitted light in nm
    n : float
        Refractive index surrounding point source
    NA : float
        Numerical aperture of the optical system
    
    Returns
    -------
    k : np.array
        Array of np.complex values describing electric field of the PSF
    """
    
    fc = NA/(n*wl)    # cutoff frequency
    k = fc*sp.jv(1, 2*np.pi*fc*np.sqrt(x**2+y**2))/np.sqrt(x**2+y**2)
    
    return k

def amplitude_dic_psf(x, y, wl, NA, n, shear_distance, shear_angle, bias):
    """
    Theoretically construct the electric field for an amplitude DIC PSF in 2D.
    
    DIC PSF consists of two coherent amplitude PSF 
    subtracting each other separated by a shear distance.
    
    Parameters
    ----------
    x, y : float
        Coordinates
    wl : float
        Wavelength of emitted light in nm
    n : float
        Refractive index surrounding point source
    NA : float
        Numerical aperture of the optical system
    shear_distance : float
        Shear distance of a single recombinging prism in nm
    shear_angle : float
        Shear angle in rad
    bias : float
        Bias in wavelength
        
    Returns
    -------
    h : np.array
        Array of np.complex values describing electric field of the PSF
    """
    
    d = shear_distance
    tau = shear_angle
    gama = bias * 2*np.pi  # bias in rad
    k1 = coherent_amplitude_psf(x*np.cos(tau)-y*np.sin(tau)-d/2, x*np.sin(tau)+y*np.cos(tau),\
                                wl, NA, n)
    k2 = coherent_amplitude_psf(x*np.cos(tau)-y*np.sin(tau)+d/2, x*np.sin(tau)+y*np.cos(tau),\
                                wl, NA, n)
    h = 0.5*np.exp(-1j*gama/2)*k1 - 0.5*np.exp(1j*gama/2)*k2  
    
    return h

def amplitude_dic_otf(fx, fy, wl, NA, n, shear_distance, shear_angle, bias):
    """
    Theoretically construct the electric field for DIC OTF in 2D.
    DIC OTF are expected to have only imaginary part.
    
    Parameters
    ----------
    x, y : float
        Coordinates
    wl : float
        Wavelength of emitted light in nm
    n : float
        Refractive index surrounding point source
    NA : float
        Numerical aperture of the optical system
    shear_distance : float
        Shear distance of a single recombinging prism in nm
    shear_angle : float
        Shear angle in rad
    bias : float
        Bias in wavelength
    
    Returns
    -------
    H: np.array
        Array of np.complex values describing electric field of the DIC OTF.
    """
    
    gama = bias * 2*np.pi   # bias in rad
    H = -1j*\
    np.sin(2*np.pi*(fx*np.cos(shear_angle)-fy*np.sin(shear_angle))*shear_distance/2 + gama/2)*\
    pupil(fx,fy,wl,NA,n)
    
    return H

def sampled_amplitude_dic_psf_2d(pixel_size, chip_size,\
                              wl, NA, n, shear_distance, shear_angle, bias):
    """
    Construct the electric field for an amplitude DIC PSF in 2D
    based on the camera we have.
    
    Parameters
    ----------
    wl : float
        Wavelength of emitted light in nm.
    NA : float
        Numerical aperture of the optical system
    n : float
        Refractive index surrounding point source
    pixel_size : float
        Effective pixel size of camera chip in nm
    chip_size : int
        How many pixels on the camera chip
        
    Returns
    -------
    psf : np.array
        Array of np.complex value of the PSF
    """
    
    # Sampling
    duration = pixel_size * chip_size
    N = chip_size
    sample_rate = N / duration
    x = np.linspace(-duration/2, duration/2, N)
    y = x
    X, Y = np.meshgrid(x, y)
    
    # Get the PSF
    psf = amplitude_dic_psf(X, Y, wl, NA, n, shear_distance, shear_angle, bias)
    
    return psf

def sampled_amplitude_dic_otf_2d(pixel_size, chip_size,\
                              wl, NA, n, shear_distance, shear_angle, bias):
    """
    Construct the electric field for an amplitude DIC PSF in 2D
    based on the camera we have.
    
    Parameters
    ----------
    wl : float
        Wavelength of emitted light in nm.
    NA : float
        Numerical aperture of the optical system
    n : float
        Refractive index surrounding point source
    pixel_size : float
        Effective pixel size of camera chip in nm
    chip_size : int
        How many pixels on the camera chip
        
    Returns
    -------
    otf : np.array 
        Array of np.complex value of the PSF
    """
    
    # Sampling
    duration = pixel_size * chip_size
    N = chip_size
    sample_rate = N / duration
    fx = np.arange(-sample_rate/2, sample_rate/2, 1/duration)
    fy = fx
    FX, FY = np.meshgrid(fx, fy)
    
    # Get the OTF
    otf = amplitude_dic_otf(FX, FY, wl, NA, n, shear_distance, shear_angle, bias)
    
    return otf

def coherent(phase_func, pixel_size, chip_size, wl, NA, n, \
                         shear_distance, shear_angle_1, shear_angle_2, bias):
    """
    Using fft method to convolve the phase object with the DIC PSF
    to get its DIC image intensity profile.
    
    Simulated DIC image stacks are expected to have the following 
    order in the channel column.
    
    6-frame
    c    dir        bias
    --------------------
    0    +3pi/2    -bias
    1    +3pi/2    0
    2    +3pi/2    +bias
    3    +pi       -bias
    4    +pi       0
    5    +pi       +bias
    
    Parameters
    ----------
    phase_func : complex
        Phase function of the sample object 
    pixel_size : float
        Effective pixel size of camera chip in nm
    chip_size : int
        How many pixels on the camera chip
    wl : float
        Wavelength of emitted light in nm
    n : float
        Refractive index surrounding point source
    NA : float
        Numerical aperture of the optical system
    shear_distance : float
        Shear distance of a single recombinging prism in nm
    shear_angle_1 : float
        First shear angle in rad
    shear_angle_2 : float
        Second shear angle in rad
    bias : float
        Bias in wavelength
    
    Returns
    -------
    image_stack : PYME.IO.image.ImageStack
        A stack of 6-frame simulated DIC images
    """
    
    # Sampling
    duration = pixel_size * chip_size
    N = chip_size
    sample_rate = N / duration
    x = np.linspace(-duration/2, duration/2, N)
    y = x
    X, Y = np.meshgrid(x, y)
    fact = ((x[1]-x[0])*(y[1]-y[0]))**2    # scaling factor of the convolution
    
    # Generate 6-frame images
    shear_angle_1 = 3*np.pi/2
    shear_angle_2 = np.pi    # use the value our system has for simulation
    gama = bias * 2*np.pi   # bias in rad
    a = 1                  # normalized light source intensity
    h0 = amplitude_dic_psf(X, Y, wl, NA, n, \
                           np.sqrt(2)*shear_distance, shear_angle_1, -bias)
    h1 = amplitude_dic_psf(X, Y, wl, NA, n, \
                           np.sqrt(2)*shear_distance, shear_angle_1, 0)
    h2 = amplitude_dic_psf(X, Y, wl, NA, n, \
                           np.sqrt(2)*shear_distance, shear_angle_1, bias)
    h3 = amplitude_dic_psf(X, Y, wl, NA, n, \
                           np.sqrt(2)*shear_distance, shear_angle_2, -bias)
    h4 = amplitude_dic_psf(X, Y, wl, NA, n, \
                           np.sqrt(2)*shear_distance, shear_angle_2, 0)
    h5 = amplitude_dic_psf(X, Y, wl, NA, n, \
                           np.sqrt(2)*shear_distance, shear_angle_2, bias)
    
    image_amplitude0 = signal.fftconvolve(np.exp(-1j*phase_func), h0, mode='same')
    I0 = a * np.abs(image_amplitude0)**2 * fact
    
    image_amplitude1 = signal.fftconvolve(np.exp(-1j*phase_func), h1, mode='same')
    I1 = a * np.abs(image_amplitude1)**2 * fact
    
    image_amplitude2 = signal.fftconvolve(np.exp(-1j*phase_func), h2, mode='same')
    I2 = a * np.abs(image_amplitude2)**2 * fact
    
    image_amplitude3 = signal.fftconvolve(np.exp(-1j*phase_func), h3, mode='same')
    I3 = a * np.abs(image_amplitude3)**2 * fact
    
    image_amplitude4 = signal.fftconvolve(np.exp(-1j*phase_func), h4, mode='same')
    I4 = a * np.abs(image_amplitude4)**2 * fact
    
    image_amplitude5 = signal.fftconvolve(np.exp(-1j*phase_func), h5, mode='same')
    I5 = a * np.abs(image_amplitude5)**2 * fact
    
    # Stack those images
    stack = np.zeros([chip_size,chip_size,6])
    stack[:,:,0] = I0
    stack[:,:,1] = I1
    stack[:,:,2] = I2
    stack[:,:,3] = I3
    stack[:,:,4] = I4
    stack[:,:,5] = I5

    stack = XYZTCWrapper(XYZTCArrayDataSource(stack))
    stack.set_dim_order_and_size('XYCZT',size_z=1,size_t=1,size_c=6)
    image_stack = ImageStack(stack)
    
    # Set the metadata
    image_stack.mdh.setEntry('voxelsize.x', pixel_size/1e3)
    image_stack.mdh.setEntry('voxelsize.y', pixel_size/1e3)
    
    return image_stack
    