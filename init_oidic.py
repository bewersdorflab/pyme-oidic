#!/usr/bin/python

from PYME.Acquire.ExecTools import joinBGInit, init_gui, init_hardware

from PYME import config

@init_hardware('PcoEdge42LT')
def pco_cam(scope):
    from PYME.Acquire.Hardware.pco.pco_edge_42_lt import PcoEdge42LT

    import logging
    logger = logging.getLogger(__name__)

    cam = PcoEdge42LT(0, debuglevel='off')  #debuglevel='extra verbose')
    cam.Init()
    cam.SetIntegTime(0.025)  # 40 fps is max bandwidth for USB3.0 camera PcoEdge42LT
    # cam._mode = 0
    # flip and rotate on primary camera should always be false - make the stage match the camera reference frame instead
    # as it's much easierconda
    # TODO - make flip, rotate etc actually work for tiling in case we have two cameras
    scope.register_camera(cam, 'PcoEdge42LT', rotate=False, flipx=False, flipy=False)

    logger.debug('here')

@init_gui('sCMOS Camera controls')
def pco_cam_controls(MainFrame, scope):
    import wx
    # Generate an empty, dummy control panel
    # TODO - adapt PYME.Acquire.Hardware.AndorNeo.ZylaControlPanel or similar to allow options to be set.
    # As it stands, we just use the default gain and readout settings.
    scope.camControls['PcoEdge42LT'] = wx.Panel(MainFrame)
    MainFrame.camPanels.append((scope.camControls['PcoEdge42LT'], 'pco.edge 4.2 LT Properties'))

@init_hardware('XY Stage')  # FIXME - may need module-level locks if we add 'x' and 'y' of the xy stage as different piezos
def mz_stage(scope):
    from PYME.Acquire.Hardware.Tango.marzhauser_tango import MarzhauserTangoXY, MarzHauserJoystick
    scope.stage = MarzhauserTangoXY()  # FIXME - change to threaded
    # scope.stage.SetSoftLimits(0, [1.06, 20.7])
    # scope.stage.SetSoftLimits(1, [.8, 17.6])

    # the stage should match the camera reference frame - i.e. the 'x' channel should be the one which results in lateral
    # movement on the camera, and the y channel should result in vertical movement on the camera
    # multipliers should be set (+1 or -1) so that the direction also matches.
    scope.register_piezo(scope.stage, 'x', needCamRestart=False, channel=1, multiplier=1)
    scope.register_piezo(scope.stage, 'y', needCamRestart=False, channel=0, multiplier=-1)

    scope.joystick = MarzHauserJoystick(scope.stage)
    scope.joystick.Enable(True)

    scope.CleanupFunctions.append(scope.stage.close)

@init_hardware('Z Piezo')
def pz(scope):
    from PYME.Acquire.Hardware.Piezos import piezo_e816, offsetPiezoREST as opr

    # try and update the pifoc position roughly as often as the PID / camera, but a little faster if we can
    scope._piFoc = piezo_e816.piezo_e816T(portname='COM15', maxtravel=50.0, Osen=0.0)
    scope.CleanupFunctions.append(scope._piFoc.close)

    scope.piFoc = opr.generate_offset_piezo_server(opr.TargetOwningOffsetPiezo)(scope._piFoc)
    scope.register_piezo(scope.piFoc, 'z', needCamRestart=False)

@init_hardware('Liquid Crystals')
def liquid_crystals(scope):
    from PYME.Acquire.Hardware.ARCoptix import lcdriver
    from oidic import liquid_crystal_calibration

    scope.lc_driver = lcdriver.LCDriver()
    scope.channel_settings = liquid_crystal_calibration.LCCalibration(scope)
    # TODO: Do I need a close() function?

@init_gui('OIDIC')
def action_manager(MainFrame, scope):
    from oidic.pymeacquire_modules import oidic_acquisition_panel
    
    # OIDIC acquistion panel
    ap = oidic_acquisition_panel.OIDICAcquisitionPanel(MainFrame, scope)
    MainFrame.aqPanels.append((ap, 'OIDIC'))

    # Menu controls for liquid crystal calibration
    def launch_cal_frame(event=None):
        from oidic.pymeacquire_modules import oidic_calibration_frame
        frame = oidic_calibration_frame.OIDICCalibrationFrame(None,scope,scope.lc_driver)
        frame.Show()
    
    MainFrame.AddMenuItem('OIDIC', 'Calibration', launch_cal_frame)


joinBGInit() 

scope.initDone = True
