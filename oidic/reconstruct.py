from matplotlib.pyplot import axes
import numpy as np

EPS = 1

def calculate_A(image_stack, wavelength, bias, n_frames=6):
    """
    Calculate A terms (see references).

    Parameters
    ----------
    image_stack : PYME.io.image.ImageStack
        Image stack containing raw DIC images for OIDIC stack
    wavelength : float
        Central wavelength used in imaging (nm).
    bias : float
        Bias used in imaging (nm).
    n_frames : int, optional
        Number of frames (4 or 6), by default 6

    Returns
    -------
    A0 : np.array
        XYZT array representing gradient component of shear direction 0 (+45)
    A1 : np.array
        XYZT array representing gradient component of shear direction 1 (-45)
    """
    assert ((n_frames == 4) or (n_frames == 6))

    scale = np.tan(np.pi*bias/wavelength)
    
    # unsigned integers mess up during subtraction, so cast to float
    if n_frames == 4:
        num0 = image_stack.data_xyztc[:,:,:,:,1].astype(float) \
               - image_stack.data_xyztc[:,:,:,:,0].astype(float)
        denom0 = image_stack.data_xyztc[:,:,:,:,1].astype(float) \
                 + image_stack.data_xyztc[:,:,:,:,0].astype(float)
        num1 = image_stack.data_xyztc[:,:,:,:,3].astype(float) \
               - image_stack.data_xyztc[:,:,:,:,2].astype(float)
        denom1 = image_stack.data_xyztc[:,:,:,:,3].astype(float) \
                 + image_stack.data_xyztc[:,:,:,:,2].astype(float)
    elif n_frames == 6:
        num0 = image_stack.data_xyztc[:,:,:,:,2].astype(float) \
               - image_stack.data_xyztc[:,:,:,:,0].astype(float)
        denom0 = image_stack.data_xyztc[:,:,:,:,2].astype(float) \
                 + image_stack.data_xyztc[:,:,:,:,0].astype(float) \
                 - 2.0*image_stack.data_xyztc[:,:,:,:,1].astype(float)
        num1 = image_stack.data_xyztc[:,:,:,:,5].astype(float) \
               - image_stack.data_xyztc[:,:,:,:,3].astype(float)
        denom1 = image_stack.data_xyztc[:,:,:,:,5].astype(float) \
                 + image_stack.data_xyztc[:,:,:,:,3].astype(float) \
                 - 2.0*image_stack.data_xyztc[:,:,:,:,4].astype(float)

    A0 = (num0/denom0)*scale
    A0[denom0 == 0] = 0
    A1 = (num1/denom1)*scale
    A1[denom1 == 0] = 0
    return A0, A1

def calculate_magnitude_gradient(A0, A1, wavelength, shear_distance):
    """
    Calculate OIDIC gradient magnitude and azimuth.

    Parameters
    ----------
    A0 : np.array
        XYZT array representing gradient component of shear direction 0 (+45)
    A1 : np.array
        XYZT array representing gradient component of shear direction 1 (-45)
    wavelength : float
        Central wavelength used in imaging (nm).
    shear_distance : float
        Shear distance of recombining prism used in imaging (nm).

    Returns
    -------
    mag : np.array
        Magnitude of OPL gradient
    azim : np.array
        Azimuth of OPL gradient
    """

    scale = wavelength/(2*np.sqrt(2)*np.pi*shear_distance)  #*np.sqrt(2)?
    atan_A0 = np.arctan(A0)  
    atan_A1 = np.arctan(A1)  
    mag = scale*np.sqrt(atan_A0*atan_A0+atan_A1*atan_A1)
    azim = np.arctan2(atan_A0,atan_A1)

    return mag, azim

def reconstruct(image_stack, wavelength, bias, shear_distance, numerical_aperture,
                background_stack=None, n_frames=6, reconstruction_type='integrate',
                shear_bias=0):
    """
    Reconstruct OIDIC images--either OPL or Riesz transform.
    
    Image stacks are expected to have the following order in the channel column.

    4-frame
    c    dir     bias
    -----------------
    0    +45    -bias
    1    +45    +bias
    2    -45    -bias
    3    -45    +bias

    6-frame
    c    dir     bias
    -----------------
    0    +45    -bias
    1    +45    0
    2    +45    +bias
    3    -45    -bias
    4    -45    0
    5    -45    +bias

    Parameters
    ----------
    image_stack : PYME.io.image.ImageStack
        Image stack containing raw sample DIC images for OIDIC stack
    wavelength : float
        Central wavelength used in imaging (nm).
    bias : float
        Bias used in imaging (nm).
    shear_distance : float
        Shear distance of recombining prism used in imaging (nm).
    numerical_aperture : float
        Numerical aperture of the acquiring system.
    background_stack : PYME.io.image.ImageStack
        Image stack containing raw background DIC images for OIDIC stack
    n_frames : int, optional
        Number of frames (4 or 6), by default 6
    reconstruction_type : string, optional
        Method to use to reconstruct the OIDIC image: 'integrate' or 
        'riesz', by default 'integrate'
    shear_bias : float
        Angle between second shear direction and the starting axis for
        measuring azimuth (rad)

    Returns
    -------
    oidic : np.array
        4D XYZT array of reconstructed OIDIC image.
    """
    assert ((reconstruction_type=='integrate') or (reconstruction_type=='riesz'))
    
    A0, A1 = calculate_A(image_stack, wavelength, bias, n_frames)
    if background_stack is not None:
        A0_bg, A1_bg = calculate_A(background_stack, wavelength, bias, n_frames)
        A0 -= A0_bg
        A1 -= A1_bg
    mag, azim = calculate_magnitude_gradient(A0, A1, wavelength, shear_distance)
    
    ft_grad = np.fft.fft2(mag*np.exp(1j*(azim+shear_bias)), axes=(0,1))
    
    lx, ly = image_stack.data_xyztc.shape[0], image_stack.data_xyztc.shape[1]
    dx, dy = image_stack.voxelsize_nm.x, image_stack.voxelsize_nm.y
    # otf_scale_x = wavelength/(2.0*numerical_aperture*dx)  # dx and dy here are assumed to include
    # otf_scale_y = wavelength/(2.0*numerical_aperture*dy)  # binning*pixel_size/magnification
    otf_scale_x = 2.0*np.pi/dx
    otf_scale_y = 2.0*np.pi/dy
    fx = np.fft.fftfreq(lx)*otf_scale_x
    fy = np.fft.fftfreq(ly)*otf_scale_y
    wx, wy = np.meshgrid(fx, fy)

    """
    # lowpass
    # NOTE: hard stop, apodize??
    R = (wx*wx+wy*wy)
    M = R > (2.0*numerical_aperture/wavelength)**2
    wx[M], wy[M] = 0, 0
    """

    # Avoid wx = wy = 0 simutaneously
    wx[(wx == 0) & (wy == 0)] = EPS
    wy[(wx == 0) & (wy == 0)] = EPS

    if reconstruction_type == 'integrate':
        fact = 1.0/(1j * (wx - 1j * wy))
    elif reconstruction_type == 'riesz':
        fact = (wx + 1j*wy)/(1j*np.sqrt(wx*wx+wy*wy))
    
    integrated = ft_grad*fact[:,:,None,None]
    oidic = np.real(np.fft.ifft2(integrated, axes=(0,1)))
    oidic -= np.min(oidic)

    return oidic
