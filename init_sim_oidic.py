#!/usr/bin/python

from PYME.Acquire.ExecTools import joinBGInit, init_gui, init_hardware

from PYME import config

scope.microscope_name = 'PYMESimulator'

# set some defaults for PYMEAcquire
# uncomment the line below for high-thoughput style directory hashing
# config.config['acquire-spool_subdirectories'] = True

@init_hardware('Fake Piezos')
def pz(scope):
    from PYME.Acquire.Hardware.Simulator import fakePiezo
    scope.fakePiezo = fakePiezo.FakePiezo(100)
    scope.register_piezo(scope.fakePiezo, 'z', needCamRestart=True)
    
    scope.fakeXPiezo = fakePiezo.FakePiezo(10000)
    scope.register_piezo(scope.fakeXPiezo, 'x')
    
    scope.fakeYPiezo = fakePiezo.FakePiezo(10000)
    scope.register_piezo(scope.fakeYPiezo, 'y')

pz.join() #piezo must be there before we start camera

@init_hardware('Fake Camera')
def cm(scope):
    import numpy as np
    from PYME.Acquire.Hardware.Simulator import fakeCam
    cam = fakeCam.FakeCamera(256, #70*np.arange(0.0, 4*256.0),
                                             256, #70*np.arange(0.0, 256.0),
                                             fakeCam.NoiseMaker(),
                                             scope.fakePiezo, xpiezo = scope.fakeXPiezo,
                                             ypiezo = scope.fakeYPiezo,
                                             pixel_size_nm=70.,
                                             )
    cam.SetEMGain(150)
    scope.register_camera(cam,'Fake Camera')

#scope.EnableJoystick = 'foo'

#InitBG('Should Fail', """
#raise Exception, 'test error'
#time.sleep(1)
#""")
#
#InitBG('Should not be there', """
#raise HWNotPresent, 'test error'
#time.sleep(1)
#""")


# @init_gui('Simulation UI')
# def sim_controls(MainFrame, scope):
#     from PYME.Acquire.Hardware.Simulator import dSimControl
#     dsc = dSimControl.dSimControl(MainFrame, scope)
#     MainFrame.AddPage(page=dsc, select=False, caption='Simulation Settings')
#
#     scope.dsc = dsc


@init_gui('Simulation UI')
def sim_controls(MainFrame, scope):
    from PYME.Acquire.Hardware.Simulator import simcontrol, simui_wx
    scope.simcontrol = simcontrol.SimController(scope)
    dsc = simui_wx.dSimControl(MainFrame, scope.simcontrol)
    MainFrame.AddPage(page=dsc, select=False, caption='Simulation Settings')
    
    scope.dsc = dsc

@init_gui('Camera controls')
def cam_controls(MainFrame, scope):
    from PYME.Acquire.Hardware.AndorIXon import AndorControlFrame
    scope.camControls['Fake Camera'] = AndorControlFrame.AndorPanel(MainFrame, scope.cam, scope)
    MainFrame.camPanels.append((scope.camControls['Fake Camera'], 'EMCCD Properties', False))

@init_gui('Sample database')
def samp_db(MainFrame, scope):
    from PYME.Acquire import sampleInformation
    from PYME.IO import MetaDataHandler
    
    MetaDataHandler.provideStartMetadata.append(lambda mdh: sampleInformation.getSampleDataFailsafe(MainFrame, mdh))
    
    sampPan = sampleInformation.slidePanel(MainFrame)
    MainFrame.camPanels.append((sampPan, 'Current Slide'))

# @init_gui('Analysis settings')
# def anal_settings(MainFrame, scope):
#     from PYME.Acquire.ui import AnalysisSettingsUI
#     AnalysisSettingsUI.Plug(scope, MainFrame)

@init_gui('Fake DMD')
def fake_dmd(MainFrame, scope):
    from PYMEnf.Hardware import FakeDMD
    from PYME.Acquire.Hardware import DMDGui
    scope.LC = FakeDMD.FakeDMD(scope)
    
    LCGui = DMDGui.DMDPanel(MainFrame,scope.LC, scope)
    MainFrame.camPanels.append((LCGui, 'DMD Control', False))


#InitGUI("""
#from PYME.Acquire.Hardware import ccdAdjPanel
##import wx
##f = wx.Frame(None)
#snrPan = ccdAdjPanel.sizedCCDPanel(notebook1, scope, acf)
#notebook1.AddPage(page=snrPan, select=False, caption='Image SNR')
##camPanels.append((snrPan, 'SNR etc ...'))
##f.Show()
##time1.WantNotification.append(snrPan.ccdPan.draw)
#""")

cm.join()

@init_hardware('Lasers')
def lasers(scope):
    from PYME.Acquire.Hardware import lasers
    scope.l488 = lasers.FakeLaser('l488',scope.cam,1, initPower=10)
    scope.l488.register(scope)
    scope.l405 = lasers.FakeLaser('l405',scope.cam,0, initPower=10)
    scope.l405.register(scope)
    

@init_gui('Laser controls')
def laser_controls(MainFrame, scope):
    from PYME.Acquire.ui import lasersliders
    
    #lcf = lasersliders.LaserToggles(MainFrame.toolPanel, scope.state)
    #MainFrame.time1.WantNotification.append(lcf.update)
    #MainFrame.camPanels.append((lcf, 'Laser Control'))
    
    lsf = lasersliders.LaserSliders(MainFrame.toolPanel, scope.state)
    MainFrame.time1.WantNotification.append(lsf.update)
    MainFrame.camPanels.append((lsf, 'Laser Control'))

@init_gui('Focus Keys')
def focus_keys(MainFrame, scope):
    from PYME.Acquire.Hardware import focusKeys
    fk = focusKeys.FocusKeys(MainFrame, scope.piezos[0])


#InitGUI("""
#from PYME.Acquire.Hardware import splitter
#splt = splitter.Splitter(MainFrame, None, scope, scope.cam)
#""")

@init_gui('Action manager')
def action_manager(MainFrame, scope):
    from PYME.Acquire.ui import actionUI
    
    ap = actionUI.ActionPanel(MainFrame, scope.actions, scope)
    MainFrame.AddPage(ap, caption='Queued Actions')


@init_gui('Tiling')
def action_manager(MainFrame, scope):
    from PYME.Acquire.ui import tile_panel
    
    ap = tile_panel.TilePanel(MainFrame, scope)
    MainFrame.aqPanels.append((ap, 'Tiling'))

@init_hardware('Liquid Crystals')
def liquid_crystals(scope):
    #from PYME.Acquire.Hardware.ARCoptix import lcdriver
    #from oidic.pymeacquire_modules import liquid_crystal_calibration

    class SpoofedChannelSettings(object):
        def __init__(self):
            self._num_channels = 6
            self._lc_bias = 0

        def set_c(self, c_idx):
            pass

        def set_bias(self, bias):
            self._lc_bias = bias

        def set_num_channels(self, num_channels):
            self._num_channels = num_channels

        @property
        def num_channels(self):
            return self._num_channels

    #scope.lc_driver = lcdriver.LCDriver()
    scope.oidic_channel_settings = SpoofedChannelSettings()
    #scope.hardwareChecks.append(scope.oidic_channel_settings.c_on_target)
    # TODO: Do I need a close() function?

@init_hardware('OIDIC')
def oidic(scope):
    from oidic.pymeacquire_modules import oidic_acquisition 
    scope.spoolController.register_acquisition_type('OIDIC', oidic_acquisition.OIDICAcquisition)

@init_gui('OIDIC')
def oidic(MainFrame, scope):
    from oidic.pymeacquire_modules import oidic_acquisition_panel
    
    # OIDIC acquistion panel
    ap = oidic_acquisition_panel.OIDICAcquisitionPanel(MainFrame, scope)
    MainFrame.register_acquisition_ui('OIDIC', (ap, 'OIDIC'))

    # # Menu controls for liquid crystal calibration
    # def launch_cal_frame(event=None):
    #     from oidic.pymeacquire_modules import oidic_calibration_frame
    #     frame = oidic_calibration_frame.OIDICCalibrationFrame(None,scope)
    #     frame.Show()
    
    # MainFrame.AddMenuItem('OIDIC', 'Calibration', launch_cal_frame)


joinBGInit() 

scope.initDone = True
