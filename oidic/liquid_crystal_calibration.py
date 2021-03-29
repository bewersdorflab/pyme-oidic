import PYME.config

def load_calibration():
    """Load the OIDIC liquid crystal calibration curve.

    Returns
    -------
    volts : np.array
        Voltage applied to liquid crystals
    ret : np.array
        Normalized wavelength, referenced to ideal wavelength (usually 546 nm) 
        for OIDIC prisms. Value in [0,1].
    """
    # Grab the liquid crystal calibration file
    calibration_file = PYME.config.get('OIDIC-liquid_crystal_cal_file', None)
    if calibration_file is None:
        raise AttributeError('Please configure a liquid crystal calibration file' \
                                'under OIDIC-liquid_crystal_cal_file in ~/.PYME/config.yaml.')

    if calibration_file.split('.')[-1] != 'xls':
        raise NotImplementedError('We can only currently load XLS files.')

    calibration = pd.read_excel(calibration_file)

    # TODO: This is wildly specific to the calibration file from Michael Shribak
    volts, ret = (calibration.to_numpy()[1:,9]).astype(float), (calibration.to_numpy()[1:,10]).astype(float)

    return volts, ret

def interpolate_ret(vals, volts, ret):
    return np.interp(vals,volts,ret)

def interpolate_volts(vals, volts, ret):
    return np.interp(vals,ret,volts)
