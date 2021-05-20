# -*- coding: utf-8 -*-

"""
@author: zacsimile

See references below for descriptions of notations used.

References
----------
M. Shribak, “Differential Interference Microscopy,” in Biomedical 
Optical Phase Microscopy and Nanoscopy, 2012.

M. Shribak, “Quantitative orientation-independent differential 
interference contrast microscope with fast switching shear 
direction and bias modulation,” J. Opt. Soc. Am. A, vol. 30, 
no. 4, p. 769, 2013.

M. Shribak, K. G. Larkin, and D. Biggs, “Mapping optical path length 
and image enhancement using quantitative orientation-independent 
differential interference contrast microscopy,” J. Biomed. Opt., vol. 
22, no. 1, p. 016006, 2017.
"""
import numpy as np

def calculate_A(image_stack, wavelength, bias, n_frames=6):
    """
    Calculate A terms (see references).

    Image stacks are expected to have the following order in the channel column.

    4-frame
    c    dir     bias
    -----------------
    0    -45    -bias
    1    -45    +bias
    2    +45    -bias
    3    +45    +bias

    6-frame
    c    dir     bias
    -----------------
    0    -45    -bias
    1    -45    0
    2    -45    +bias
    3    +45    -bias
    4    +45    0
    5    +45    +bias

    Parameters
    ----------
    image_stack : PYME.io.image.ImageStack
        Image stack containing raw DIC images for OIDIC stack
    wavelength : float
        Central wavelength used in imaging (nm).
    bias : float
        Bias used in imaging (fraction of central wavelength).
    n_frames : int, optional
        Number of frames (4 or 6), by default 6

    Returns
    -------
    A0 : np.array
        XYZT array representing gradient component of shear direction 0 (-45)
    A1 : np.array
        XYZT array representing gradient component of shear direction 1 (-45)
    """
    assert ((n_frames == 4) or (n_frames == 6))

    scale = np.tan(np.pi*bias/wavelength)

    if n_frames == 4:
        num0 = image_stack.data_xyztc[:,:,:,:,1] - image_stack.data_xyztc[:,:,:,:,0]
        denom0 = image_stack.data_xyztc[:,:,:,:,1] + image_stack.data_xyztc[:,:,:,:,0]
        num1 = image_stack.data_xyztc[:,:,:,:,3] - image_stack.data_xyztc[:,:,:,:,2]
        denom1 = image_stack.data_xyztc[:,:,:,:,3] + image_stack.data_xyztc[:,:,:,:,2]
    elif n_frames == 6:
        num0 = image_stack.data_xyztc[:,:,:,:,2] - image_stack.data_xyztc[:,:,:,:,0]
        denom0 = image_stack.data_xyztc[:,:,:,:,2] + image_stack.data_xyztc[:,:,:,:,0] \
                 - 2.0*image_stack.data_xyztc[:,:,:,:,1]
        num1 = image_stack.data_xyztc[:,:,:,:,5] - image_stack.data_xyztc[:,:,:,:,3]
        denom1 = image_stack.data_xyztc[:,:,:,:,5] + image_stack.data_xyztc[:,:,:,:,3] \
                 - 2.0*image_stack.data_xyztc[:,:,:,:,4]


    A0 = (num0/denom0)*scale
    A1 = (num1/denom1)*scale
    return A0, A1

def calculate_magnitude_gradient(A0, A1, wavelength, shear_distance, A0_bg=None, A1_bg=None):
    """
    Calculate OIDIC gradient magnitude and azimuth.

    Parameters
    ----------
    A0 : np.array
        XYZT array representing gradient component of shear direction 0 (-45)
    A1 : np.array
        XYZT array representing gradient component of shear direction 1 (-45)
    wavelength : float
        Central wavelength used in imaging (nm).
    shear_distance : float
        Shear distance of recombining prism used in imaging (nm).
    A0_bg : np.array, optional
        [description], by default None
    A1_bg : np.array, optional
        [description], by default None

    Returns
    -------
    [type]
        [description]
    """
    if A0_bg is not None:
        A0 = A0 - A0_bg
    if A1_bg is not None:
        A1 = A1 - A1_bg

    scale = wavelength/(2*np.sqrt(2)*np.pi*shear_distance)
    atan_A0 = np.arctan(A0)  # TODO: should we pass A0 and A1 as num*scale and denom so 
    atan_A1 = np.arctan(A1)  #       we can use np.arctan2 here?
    mag = scale*np.sqrt(atan_A0*atan_A0+atan_A1*atan_A1)
    azim = np.arctan2(atan_A1,atan_A0)

    return mag, azim

def reconstruct6(image_stack, wavelength, bias, floor, ceil):
    pass