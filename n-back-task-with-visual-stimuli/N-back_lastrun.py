#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This experiment was created using PsychoPy3 Experiment Builder (v2026.1.3),
    on June 01, 2026, at 11:25
If you publish work using this script the most relevant publication is:

    Peirce J, Gray JR, Simpson S, MacAskill M, Höchenberger R, Sogo H, Kastman E, Lindeløv JK. (2019) 
        PsychoPy2: Experiments in behavior made easy Behav Res 51: 195. 
        https://doi.org/10.3758/s13428-018-01193-y

"""

# --- Import packages ---
from psychopy import locale_setup
from psychopy import prefs
from psychopy import plugins
plugins.activatePlugins()
from psychopy import sound, gui, visual, core, data, event, logging, clock, colors, layout, hardware
from psychopy.tools import environmenttools
from psychopy.constants import (
    NOT_STARTED, STARTED, PLAYING, PAUSED, STOPPED, STOPPING, FINISHED, PRESSED, 
    RELEASED, FOREVER, priority
)

import numpy as np  # whole numpy lib is available, prepend 'np.'
from numpy import (sin, cos, tan, log, log10, pi, average,
                   sqrt, std, deg2rad, rad2deg, linspace, asarray)
from numpy.random import random, randint, normal, shuffle, choice as randchoice
import os  # handy system and path functions
import sys  # to get file system encoding

from psychopy.hardware import keyboard

# --- Setup global variables (available in all functions) ---
# create a device manager to handle hardware (keyboards, mice, mirophones, speakers, etc.)
deviceManager = hardware.DeviceManager()
# ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))
# store info about the experiment session
psychopyVersion = '2026.1.3'
expName = 'untitled'  # from the Builder filename that created this script
expVersion = ''
# a list of functions to run when the experiment ends (starts off blank)
runAtExit = []
# information about this experiment
expInfo = {
    'participant': '',
    'session': '001',
    'date|hid': data.getDateStr(),
    'expName|hid': expName,
    'expVersion|hid': expVersion,
    'psychopyVersion|hid': psychopyVersion,
}

# --- Define some variables which will change depending on pilot mode ---
'''
To run in pilot mode, either use the run/pilot toggle in Builder, Coder and Runner, 
or run the experiment with `--pilot` as an argument. To change what pilot 
#mode does, check out the 'Pilot mode' tab in preferences.
'''
# work out from system args whether we are running in pilot mode
PILOTING = core.setPilotModeFromArgs()
# start off with values from experiment settings
_fullScr = True
_winSize = (1024, 768)
# if in pilot mode, apply overrides according to preferences
if PILOTING:
    # force windowed mode
    if prefs.piloting['forceWindowed']:
        _fullScr = False
        # set window size
        _winSize = prefs.piloting['forcedWindowSize']
    # replace default participant ID
    if prefs.piloting['replaceParticipantID']:
        expInfo['participant'] = 'pilot'

def showExpInfoDlg(expInfo):
    """
    Show participant info dialog.
    Parameters
    ==========
    expInfo : dict
        Information about this experiment.
    
    Returns
    ==========
    dict
        Information about this experiment.
    """
    # show participant info dialog
    dlg = gui.DlgFromDict(
        dictionary=expInfo, sortKeys=False, title=expName, alwaysOnTop=True
    )
    if dlg.OK == False:
        core.quit()  # user pressed cancel
    # return expInfo
    return expInfo


def setupData(expInfo, dataDir=None):
    """
    Make an ExperimentHandler to handle trials and saving.
    
    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    dataDir : Path, str or None
        Folder to save the data to, leave as None to create a folder in the current directory.    
    Returns
    ==========
    psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    """
    # remove dialog-specific syntax from expInfo
    for key, val in expInfo.copy().items():
        newKey, _ = data.utils.parsePipeSyntax(key)
        expInfo[newKey] = expInfo.pop(key)
    
    # data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
    if dataDir is None:
        dataDir = _thisDir
    filename = u'data/%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])
    # make sure filename is relative to dataDir
    if os.path.isabs(filename):
        dataDir = os.path.commonprefix([dataDir, filename])
        filename = os.path.relpath(filename, dataDir)
    
    # an ExperimentHandler isn't essential but helps with data saving
    thisExp = data.ExperimentHandler(
        name=expName, version=expVersion,
        extraInfo=expInfo, runtimeInfo=None,
        originPath='C:\\Users\\jshin\\OW_closedloopLIFU\\n-back-task-with-visual-stimuli\\N-back_lastrun.py',
        savePickle=True, saveWideText=True,
        dataFileName=dataDir + os.sep + filename, sortColumns='time'
    )
    # store pilot mode in data file
    thisExp.addData('piloting', PILOTING, priority=priority.LOW)
    thisExp.setPriority('thisRow.t', priority.CRITICAL)
    thisExp.setPriority('expName', priority.LOW)
    # return experiment handler
    return thisExp


def setupLogging(filename):
    """
    Setup a log file and tell it what level to log at.
    
    Parameters
    ==========
    filename : str or pathlib.Path
        Filename to save log file and data files as, doesn't need an extension.
    
    Returns
    ==========
    psychopy.logging.LogFile
        Text stream to receive inputs from the logging system.
    """
    # set how much information should be printed to the console / app
    if PILOTING:
        logging.console.setLevel(
            prefs.piloting['pilotConsoleLoggingLevel']
        )
    else:
        logging.console.setLevel('warning')
    # save a log file for detail verbose info
    logFile = logging.LogFile(filename+'.log')
    if PILOTING:
        logFile.setLevel(
            prefs.piloting['pilotLoggingLevel']
        )
    else:
        logFile.setLevel(
            logging.getLevel('exp')
        )
    
    return logFile


def setupWindow(expInfo=None, win=None):
    """
    Setup the Window
    
    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    win : psychopy.visual.Window
        Window to setup - leave as None to create a new window.
    
    Returns
    ==========
    psychopy.visual.Window
        Window in which to run this experiment.
    """
    if PILOTING:
        logging.debug('Fullscreen settings ignored as running in pilot mode.')
    
    if win is None:
        # if not given a window to setup, make one
        win = visual.Window(
            size=_winSize, fullscr=_fullScr, screen=0,
            winType='pyglet', allowGUI=False, allowStencil=False,
            monitor='testMonitor', color=[0,0,0], colorSpace='rgb',
            backgroundImage='', backgroundFit='none',
            blendMode='avg', useFBO=True,
            units='height',
            checkTiming=False  # we're going to do this ourselves in a moment
        )
    else:
        # if we have a window, just set the attributes which are safe to set
        win.color = [0,0,0]
        win.colorSpace = 'rgb'
        win.backgroundImage = ''
        win.backgroundFit = 'none'
        win.units = 'height'
    if expInfo is not None:
        # get/measure frame rate if not already in expInfo
        if win._monitorFrameRate is None:
            win._monitorFrameRate = win.getActualFrameRate(infoMsg='Attempting to measure frame rate of screen, please wait...')
        expInfo['frameRate'] = win._monitorFrameRate
    win.hideMessage()
    if PILOTING:
        # show a visual indicator if we're in piloting mode
        if prefs.piloting['showPilotingIndicator']:
            win.showPilotingIndicator()
        # always show the mouse in piloting mode
        if prefs.piloting['forceMouseVisible']:
            win.mouseVisible = True
    
    return win


def setupDevices(expInfo, thisExp, win):
    """
    Setup whatever devices are available (mouse, keyboard, speaker, eyetracker, etc.) and add them to 
    the device manager (deviceManager)
    
    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    win : psychopy.visual.Window
        Window in which to run this experiment.
    Returns
    ==========
    bool
        True if completed successfully.
    """
    # --- Setup input devices ---
    ioConfig = {}
    ioSession = ioServer = eyetracker = None
    
    # store ioServer object in the device manager
    deviceManager.ioServer = ioServer
    
    # create a default keyboard (e.g. to check for escape)
    if deviceManager.getDevice('defaultKeyboard') is None:
        deviceManager.addDevice(
            deviceClass='keyboard', deviceName='defaultKeyboard', backend='ptb'
        )
    # return True if completed successfully
    return True

def pauseExperiment(thisExp, win=None, timers=[], currentRoutine=None):
    """
    Pause this experiment, preventing the flow from advancing to the next routine until resumed.
    
    Parameters
    ==========
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    win : psychopy.visual.Window
        Window for this experiment.
    timers : list, tuple
        List of timers to reset once pausing is finished.
    currentRoutine : psychopy.data.Routine
        Current Routine we are in at time of pausing, if any. This object tells PsychoPy what Components to pause/play/dispatch.
    """
    # if we are not paused, do nothing
    if thisExp.status != PAUSED:
        return
    
    # start a timer to figure out how long we're paused for
    pauseTimer = core.Clock()
    # pause any playback components
    if currentRoutine is not None:
        for comp in currentRoutine.getPlaybackComponents():
            comp.pause()
    # make sure we have a keyboard
    defaultKeyboard = deviceManager.getDevice('defaultKeyboard')
    if defaultKeyboard is None:
        defaultKeyboard = deviceManager.addKeyboard(
            deviceClass='keyboard',
            deviceName='defaultKeyboard',
            backend='PsychToolbox',
        )
    # run a while loop while we wait to unpause
    while thisExp.status == PAUSED:
        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=['escape']):
            endExperiment(thisExp, win=win)
        # dispatch messages on response components
        if currentRoutine is not None:
            for comp in currentRoutine.getDispatchComponents():
                comp.device.dispatchMessages()
        # sleep 1ms so other threads can execute
        clock.time.sleep(0.001)
    # if stop was requested while paused, quit
    if thisExp.status == FINISHED:
        endExperiment(thisExp, win=win)
    # resume any playback components
    if currentRoutine is not None:
        for comp in currentRoutine.getPlaybackComponents():
            comp.play()
    # reset any timers
    for timer in timers:
        timer.addTime(-pauseTimer.getTime())


def run(expInfo, thisExp, win, globalClock=None, thisSession=None):
    """
    Run the experiment flow.
    
    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    psychopy.visual.Window
        Window in which to run this experiment.
    globalClock : psychopy.core.clock.Clock or None
        Clock to get global time from - supply None to make a new one.
    thisSession : psychopy.session.Session or None
        Handle of the Session object this experiment is being run from, if any.
    """
    # mark experiment as started
    thisExp.status = STARTED
    # update experiment info
    expInfo['date'] = data.getDateStr()
    expInfo['expName'] = expName
    expInfo['expVersion'] = expVersion
    expInfo['psychopyVersion'] = psychopyVersion
    # make sure window is set to foreground to prevent losing focus
    win.winHandle.activate()
    # make sure variables created by exec are available globally
    exec = environmenttools.setExecEnvironment(globals())
    # get device handles from dict of input devices
    ioServer = deviceManager.ioServer
    # get/create a default keyboard (e.g. to check for escape)
    defaultKeyboard = deviceManager.getDevice('defaultKeyboard')
    if defaultKeyboard is None:
        deviceManager.addDevice(
            deviceClass='keyboard', deviceName='defaultKeyboard', backend='PsychToolbox'
        )
    eyetracker = deviceManager.getDevice('eyetracker')
    # make sure we're running in the directory for this experiment
    os.chdir(_thisDir)
    # get filename from ExperimentHandler for convenience
    filename = thisExp.dataFileName
    frameTolerance = 0.001  # how close to onset before 'same' frame
    endExpNow = False  # flag for 'escape' or other condition => quit the exp
    # get frame duration from frame rate in expInfo
    if 'frameRate' in expInfo and expInfo['frameRate'] is not None:
        frameDur = 1.0 / round(expInfo['frameRate'])
    else:
        frameDur = 1.0 / 60.0  # could not measure, so guess
    
    # Start Code - component code to be run after the window creation
    
    # --- Initialize components for Routine "Instructions_2" ---
    instructions_2 = visual.TextStim(win=win, name='instructions_2',
        text='In this 2‑back task, you will see a series of squares appear one at a time on the screen. Your job is to press the match key whenever the current square is the same as the one shown two squares earlier, and do nothing otherwise. Respond as quickly and accurately as you can throughout the sequence.\n\nFor example if the square appeared in left down corner on trial 1, you should press space if the square appears in the left down corner on trial 3. Press space to continue.',
        font='Arial',
        pos=(0, 0), draggable=False, height=0.05, wrapWidth=None, ori=0, 
        color='white', colorSpace='rgb', opacity=1, 
        languageStyle='LTR',
        depth=0.0);
    key_resp_2 = keyboard.Keyboard(deviceName='defaultKeyboard')
    
    # --- Initialize components for Routine "Fixation" ---
    fixation_1 = visual.TextStim(win=win, name='fixation_1',
        text='+',
        font='Arial',
        pos=(0, 0), draggable=False, height=0.05, wrapWidth=None, ori=0, 
        color='white', colorSpace='rgb', opacity=1, 
        languageStyle='LTR',
        depth=0.0);
    
    # --- Initialize components for Routine "N_back_2_trials" ---
    grid_lines_2 = visual.ImageStim(
        win=win,
        name='grid_lines_2', 
        image='grid', mask=None, anchor='center',
        ori=0, pos=(0, 0), draggable=False, size=(0.6, 0.6),
        color=[1,1,1], colorSpace='rgb', opacity=1,
        flipHoriz=False, flipVert=False,
        texRes=128, interpolate=True, depth=0.0)
    target_square_2 = visual.Rect(
        win=win, name='target_square_2',
        width=(0.15, 0.15)[0], height=(0.15, 0.15)[1],
        ori=0, pos=[0,0], draggable=False, anchor='center',
        lineWidth=1,
        colorSpace='rgb', lineColor=None, fillColor=[1.000,1.000,1.000],
        opacity=1, depth=-1.0, interpolate=True)
    fixation_3 = visual.TextStim(win=win, name='fixation_3',
        text='+',
        font='Arial',
        pos=(0, 0), draggable=False, height=0.05, wrapWidth=None, ori=0, 
        color='white', colorSpace='rgb', opacity=1, 
        languageStyle='LTR',
        depth=-2.0);
    response_2 = keyboard.Keyboard(deviceName='defaultKeyboard')
    # Run 'Begin Experiment' code from code_2
    from pylsl import StreamInlet, resolve_byprop
    
    print("Searching for LIFUEvents stream...")
    streams = resolve_byprop('name', 'PsychoPy_numeric', timeout=30)
    if len(streams) == 0:
        print("ERROR: No psychopy stream found.")
        lifu_inlet = None
    else:
        lifu_inlet = StreamInlet(streams[0])
        print("Connected to psychopy stream.")
    
    
    # --- Initialize components for Routine "End" ---
    thank_you = visual.TextStim(win=win, name='thank_you',
        text='This is the end of the experiment.\nThank you for your time.',
        font='Arial',
        pos=(0, 0), draggable=False, height=0.1, wrapWidth=None, ori=0, 
        color='white', colorSpace='rgb', opacity=1, 
        languageStyle='LTR',
        depth=0.0);
    
    # create some handy timers
    
    # global clock to track the time since experiment started
    if globalClock is None:
        # create a clock if not given one
        globalClock = core.Clock()
    if isinstance(globalClock, str):
        # if given a string, make a clock accoridng to it
        if globalClock == 'float':
            # get timestamps as a simple value
            globalClock = core.Clock(format='float')
        elif globalClock == 'iso':
            # get timestamps in ISO format
            globalClock = core.Clock(format='%Y-%m-%d_%H:%M:%S.%f%z')
        else:
            # get timestamps in a custom format
            globalClock = core.Clock(format=globalClock)
    if ioServer is not None:
        ioServer.syncClock(globalClock)
    logging.setDefaultClock(globalClock)
    if eyetracker is not None:
        eyetracker.enableEventReporting()
    # routine timer to track time remaining of each (possibly non-slip) routine
    routineTimer = core.Clock()
    win.flip()  # flip window to reset last flip timer
    # store the exact time the global clock started
    expInfo['expStart'] = data.getDateStr(
        format='%Y-%m-%d %Hh%M.%S.%f %z', fractionalSecondDigits=6
    )
    
    # --- Prepare to start Routine "Instructions_2" ---
    # create an object to store info about Routine Instructions_2
    Instructions_2 = data.Routine(
        name='Instructions_2',
        components=[instructions_2, key_resp_2],
    )
    Instructions_2.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # create starting attributes for key_resp_2
    key_resp_2.keys = []
    key_resp_2.rt = []
    _key_resp_2_allKeys = []
    # store start times for Instructions_2
    Instructions_2.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    Instructions_2.tStart = globalClock.getTime(format='float')
    Instructions_2.status = STARTED
    thisExp.addData('Instructions_2.started', Instructions_2.tStart)
    Instructions_2.maxDuration = None
    # keep track of which components have finished
    Instructions_2Components = Instructions_2.components
    for thisComponent in Instructions_2.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1
    
    # --- Run Routine "Instructions_2" ---
    thisExp.currentRoutine = Instructions_2
    Instructions_2.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *instructions_2* updates
        
        # if instructions_2 is starting this frame...
        if instructions_2.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            instructions_2.frameNStart = frameN  # exact frame index
            instructions_2.tStart = t  # local t and not account for scr refresh
            instructions_2.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(instructions_2, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'instructions_2.started')
            # update status
            instructions_2.status = STARTED
            instructions_2.setAutoDraw(True)
        
        # if instructions_2 is active this frame...
        if instructions_2.status == STARTED:
            # update params
            pass
        
        # *key_resp_2* updates
        waitOnFlip = False
        
        # if key_resp_2 is starting this frame...
        if key_resp_2.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            key_resp_2.frameNStart = frameN  # exact frame index
            key_resp_2.tStart = t  # local t and not account for scr refresh
            key_resp_2.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(key_resp_2, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'key_resp_2.started')
            # update status
            key_resp_2.status = STARTED
            # keyboard checking is just starting
            waitOnFlip = True
            win.callOnFlip(key_resp_2.clock.reset)  # t=0 on next screen flip
            win.callOnFlip(key_resp_2.clearEvents, eventType='keyboard')  # clear events on next screen flip
        if key_resp_2.status == STARTED and not waitOnFlip:
            theseKeys = key_resp_2.getKeys(keyList=['space'], ignoreKeys=["escape"], waitRelease=False)
            _key_resp_2_allKeys.extend(theseKeys)
            if len(_key_resp_2_allKeys):
                key_resp_2.keys = _key_resp_2_allKeys[-1].name  # just the last key pressed
                key_resp_2.rt = _key_resp_2_allKeys[-1].rt
                key_resp_2.duration = _key_resp_2_allKeys[-1].duration
                # a response ends the routine
                continueRoutine = False
        
        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=["escape"]):
            thisExp.status = FINISHED
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[routineTimer, globalClock], 
                currentRoutine=Instructions_2,
            )
            # skip the frame we paused on
            continue
        
        # has a Component requested the Routine to end?
        if not continueRoutine:
            Instructions_2.forceEnded = routineForceEnded = True
        # has the Routine been forcibly ended?
        if Instructions_2.forceEnded or routineForceEnded:
            break
        # has every Component finished?
        continueRoutine = False
        for thisComponent in Instructions_2.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # --- Ending Routine "Instructions_2" ---
    for thisComponent in Instructions_2.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for Instructions_2
    Instructions_2.tStop = globalClock.getTime(format='float')
    Instructions_2.tStopRefresh = tThisFlipGlobal
    thisExp.addData('Instructions_2.stopped', Instructions_2.tStop)
    # check responses
    if key_resp_2.keys in ['', [], None]:  # No response was made
        key_resp_2.keys = None
    thisExp.addData('key_resp_2.keys',key_resp_2.keys)
    if key_resp_2.keys != None:  # we had a response
        thisExp.addData('key_resp_2.rt', key_resp_2.rt)
        thisExp.addData('key_resp_2.duration', key_resp_2.duration)
    thisExp.nextEntry()
    # the Routine "Instructions_2" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # --- Prepare to start Routine "Fixation" ---
    # create an object to store info about Routine Fixation
    Fixation = data.Routine(
        name='Fixation',
        components=[fixation_1],
    )
    Fixation.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # store start times for Fixation
    Fixation.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    Fixation.tStart = globalClock.getTime(format='float')
    Fixation.status = STARTED
    thisExp.addData('Fixation.started', Fixation.tStart)
    Fixation.maxDuration = None
    # keep track of which components have finished
    FixationComponents = Fixation.components
    for thisComponent in Fixation.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1
    
    # --- Run Routine "Fixation" ---
    thisExp.currentRoutine = Fixation
    Fixation.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine and routineTimer.getTime() < 1.0:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *fixation_1* updates
        
        # if fixation_1 is starting this frame...
        if fixation_1.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            fixation_1.frameNStart = frameN  # exact frame index
            fixation_1.tStart = t  # local t and not account for scr refresh
            fixation_1.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(fixation_1, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'fixation_1.started')
            # update status
            fixation_1.status = STARTED
            fixation_1.setAutoDraw(True)
        
        # if fixation_1 is active this frame...
        if fixation_1.status == STARTED:
            # update params
            pass
        
        # if fixation_1 is stopping this frame...
        if fixation_1.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > fixation_1.tStartRefresh + 1.0-frameTolerance:
                # keep track of stop time/frame for later
                fixation_1.tStop = t  # not accounting for scr refresh
                fixation_1.tStopRefresh = tThisFlipGlobal  # on global time
                fixation_1.frameNStop = frameN  # exact frame index
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'fixation_1.stopped')
                # update status
                fixation_1.status = FINISHED
                fixation_1.setAutoDraw(False)
        
        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=["escape"]):
            thisExp.status = FINISHED
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[routineTimer, globalClock], 
                currentRoutine=Fixation,
            )
            # skip the frame we paused on
            continue
        
        # has a Component requested the Routine to end?
        if not continueRoutine:
            Fixation.forceEnded = routineForceEnded = True
        # has the Routine been forcibly ended?
        if Fixation.forceEnded or routineForceEnded:
            break
        # has every Component finished?
        continueRoutine = False
        for thisComponent in Fixation.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # --- Ending Routine "Fixation" ---
    for thisComponent in Fixation.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for Fixation
    Fixation.tStop = globalClock.getTime(format='float')
    Fixation.tStopRefresh = tThisFlipGlobal
    thisExp.addData('Fixation.stopped', Fixation.tStop)
    # using non-slip timing so subtract the expected duration of this Routine (unless ended on request)
    if Fixation.maxDurationReached:
        routineTimer.addTime(-Fixation.maxDuration)
    elif Fixation.forceEnded:
        routineTimer.reset()
    else:
        routineTimer.addTime(-1.000000)
    thisExp.nextEntry()
    
    # set up handler to look after randomisation of conditions etc
    trials_2 = data.TrialHandler2(
        name='trials_2',
        nReps=1, 
        method='sequential', 
        extraInfo=expInfo, 
        originPath=-1, 
        trialList=data.importConditions('N-back-2.xlsx'), 
        seed=None, 
        isTrials=True, 
    )
    thisExp.addLoop(trials_2)  # add the loop to the experiment
    thisTrial_2 = trials_2.trialList[0]  # so we can initialise stimuli with some values
    # abbreviate parameter names if possible (e.g. rgb = thisTrial_2.rgb)
    if thisTrial_2 != None:
        for paramName in thisTrial_2:
            globals()[paramName] = thisTrial_2[paramName]
    if thisSession is not None:
        # if running in a Session with a Liaison client, send data up to now
        thisSession.sendExperimentData()
    
    for thisTrial_2 in trials_2:
        trials_2.status = STARTED
        if hasattr(thisTrial_2, 'status'):
            thisTrial_2.status = STARTED
        currentLoop = trials_2
        thisExp.timestampOnFlip(win, 'thisRow.t', format=globalClock.format)
        if thisSession is not None:
            # if running in a Session with a Liaison client, send data up to now
            thisSession.sendExperimentData()
        # abbreviate parameter names if possible (e.g. rgb = thisTrial_2.rgb)
        if thisTrial_2 != None:
            for paramName in thisTrial_2:
                globals()[paramName] = thisTrial_2[paramName]
        
        # --- Prepare to start Routine "N_back_2_trials" ---
        # create an object to store info about Routine N_back_2_trials
        N_back_2_trials = data.Routine(
            name='N_back_2_trials',
            components=[grid_lines_2, target_square_2, fixation_3, response_2],
        )
        N_back_2_trials.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        target_square_2.setPos(location)
        # create starting attributes for response_2
        response_2.keys = []
        response_2.rt = []
        _response_2_allKeys = []
        # Run 'Begin Routine' code from code_2
        last_lifu_event= None
        last_lifu_time = None
        # store start times for N_back_2_trials
        N_back_2_trials.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        N_back_2_trials.tStart = globalClock.getTime(format='float')
        N_back_2_trials.status = STARTED
        thisExp.addData('N_back_2_trials.started', N_back_2_trials.tStart)
        N_back_2_trials.maxDuration = None
        # keep track of which components have finished
        N_back_2_trialsComponents = N_back_2_trials.components
        for thisComponent in N_back_2_trials.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1
        
        # --- Run Routine "N_back_2_trials" ---
        thisExp.currentRoutine = N_back_2_trials
        N_back_2_trials.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine and routineTimer.getTime() < 2.0:
            # if trial has changed, end Routine now
            if hasattr(thisTrial_2, 'status') and thisTrial_2.status == STOPPING:
                continueRoutine = False
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            
            # *grid_lines_2* updates
            
            # if grid_lines_2 is starting this frame...
            if grid_lines_2.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                grid_lines_2.frameNStart = frameN  # exact frame index
                grid_lines_2.tStart = t  # local t and not account for scr refresh
                grid_lines_2.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(grid_lines_2, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'grid_lines_2.started')
                # update status
                grid_lines_2.status = STARTED
                grid_lines_2.setAutoDraw(True)
            
            # if grid_lines_2 is active this frame...
            if grid_lines_2.status == STARTED:
                # update params
                pass
            
            # if grid_lines_2 is stopping this frame...
            if grid_lines_2.status == STARTED:
                # is it time to stop? (based on global clock, using actual start)
                if tThisFlipGlobal > grid_lines_2.tStartRefresh + 2-frameTolerance:
                    # keep track of stop time/frame for later
                    grid_lines_2.tStop = t  # not accounting for scr refresh
                    grid_lines_2.tStopRefresh = tThisFlipGlobal  # on global time
                    grid_lines_2.frameNStop = frameN  # exact frame index
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'grid_lines_2.stopped')
                    # update status
                    grid_lines_2.status = FINISHED
                    grid_lines_2.setAutoDraw(False)
            
            # *target_square_2* updates
            
            # if target_square_2 is starting this frame...
            if target_square_2.status == NOT_STARTED and tThisFlip >= 0-frameTolerance:
                # keep track of start time/frame for later
                target_square_2.frameNStart = frameN  # exact frame index
                target_square_2.tStart = t  # local t and not account for scr refresh
                target_square_2.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(target_square_2, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'target_square_2.started')
                # update status
                target_square_2.status = STARTED
                target_square_2.setAutoDraw(True)
            
            # if target_square_2 is active this frame...
            if target_square_2.status == STARTED:
                # update params
                pass
            
            # if target_square_2 is stopping this frame...
            if target_square_2.status == STARTED:
                # is it time to stop? (based on global clock, using actual start)
                if tThisFlipGlobal > target_square_2.tStartRefresh + 1.0-frameTolerance:
                    # keep track of stop time/frame for later
                    target_square_2.tStop = t  # not accounting for scr refresh
                    target_square_2.tStopRefresh = tThisFlipGlobal  # on global time
                    target_square_2.frameNStop = frameN  # exact frame index
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'target_square_2.stopped')
                    # update status
                    target_square_2.status = FINISHED
                    target_square_2.setAutoDraw(False)
            
            # *fixation_3* updates
            
            # if fixation_3 is starting this frame...
            if fixation_3.status == NOT_STARTED and tThisFlip >= 1-frameTolerance:
                # keep track of start time/frame for later
                fixation_3.frameNStart = frameN  # exact frame index
                fixation_3.tStart = t  # local t and not account for scr refresh
                fixation_3.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(fixation_3, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'fixation_3.started')
                # update status
                fixation_3.status = STARTED
                fixation_3.setAutoDraw(True)
            
            # if fixation_3 is active this frame...
            if fixation_3.status == STARTED:
                # update params
                pass
            
            # if fixation_3 is stopping this frame...
            if fixation_3.status == STARTED:
                # is it time to stop? (based on global clock, using actual start)
                if tThisFlipGlobal > fixation_3.tStartRefresh + 1-frameTolerance:
                    # keep track of stop time/frame for later
                    fixation_3.tStop = t  # not accounting for scr refresh
                    fixation_3.tStopRefresh = tThisFlipGlobal  # on global time
                    fixation_3.frameNStop = frameN  # exact frame index
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'fixation_3.stopped')
                    # update status
                    fixation_3.status = FINISHED
                    fixation_3.setAutoDraw(False)
            
            # *response_2* updates
            waitOnFlip = False
            
            # if response_2 is starting this frame...
            if response_2.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                response_2.frameNStart = frameN  # exact frame index
                response_2.tStart = t  # local t and not account for scr refresh
                response_2.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(response_2, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'response_2.started')
                # update status
                response_2.status = STARTED
                # keyboard checking is just starting
                waitOnFlip = True
                win.callOnFlip(response_2.clock.reset)  # t=0 on next screen flip
                win.callOnFlip(response_2.clearEvents, eventType='keyboard')  # clear events on next screen flip
            
            # if response_2 is stopping this frame...
            if response_2.status == STARTED:
                # is it time to stop? (based on global clock, using actual start)
                if tThisFlipGlobal > response_2.tStartRefresh + 2-frameTolerance:
                    # keep track of stop time/frame for later
                    response_2.tStop = t  # not accounting for scr refresh
                    response_2.tStopRefresh = tThisFlipGlobal  # on global time
                    response_2.frameNStop = frameN  # exact frame index
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'response_2.stopped')
                    # update status
                    response_2.status = FINISHED
                    response_2.status = FINISHED
            if response_2.status == STARTED and not waitOnFlip:
                theseKeys = response_2.getKeys(keyList=['space'], ignoreKeys=["escape"], waitRelease=False)
                _response_2_allKeys.extend(theseKeys)
                if len(_response_2_allKeys):
                    response_2.keys = _response_2_allKeys[-1].name  # just the last key pressed
                    response_2.rt = _response_2_allKeys[-1].rt
                    response_2.duration = _response_2_allKeys[-1].duration
                    # was this correct?
                    if (response_2.keys == str(corrAns)) or (response_2.keys == corrAns):
                        response_2.corr = 1
                    else:
                        response_2.corr = 0
            # Run 'Each Frame' code from code_2
            if lifu_inlet is not None: 
                sample, ts = lifu_inlet.pull_sample(timeout = 0.0)
                if sample is not None: 
                    last_lifu_event = sample[0]
                    last_lifu_time = ts
            
            # check for quit (typically the Esc key)
            if defaultKeyboard.getKeys(keyList=["escape"]):
                thisExp.status = FINISHED
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp, 
                    win=win, 
                    timers=[routineTimer, globalClock], 
                    currentRoutine=N_back_2_trials,
                )
                # skip the frame we paused on
                continue
            
            # has a Component requested the Routine to end?
            if not continueRoutine:
                N_back_2_trials.forceEnded = routineForceEnded = True
            # has the Routine been forcibly ended?
            if N_back_2_trials.forceEnded or routineForceEnded:
                break
            # has every Component finished?
            continueRoutine = False
            for thisComponent in N_back_2_trials.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # --- Ending Routine "N_back_2_trials" ---
        for thisComponent in N_back_2_trials.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for N_back_2_trials
        N_back_2_trials.tStop = globalClock.getTime(format='float')
        N_back_2_trials.tStopRefresh = tThisFlipGlobal
        thisExp.addData('N_back_2_trials.stopped', N_back_2_trials.tStop)
        # check responses
        if response_2.keys in ['', [], None]:  # No response was made
            response_2.keys = None
            # was no response the correct answer?!
            if str(corrAns).lower() == 'none':
               response_2.corr = 1;  # correct non-response
            else:
               response_2.corr = 0;  # failed to respond (incorrectly)
        # store data for trials_2 (TrialHandler)
        trials_2.addData('response_2.keys',response_2.keys)
        trials_2.addData('response_2.corr', response_2.corr)
        if response_2.keys != None:  # we had a response
            trials_2.addData('response_2.rt', response_2.rt)
            trials_2.addData('response_2.duration', response_2.duration)
        # Run 'End Routine' code from code_2
        thisExp.addData('LIFU_marker', last_lifu_event)
        thisExp.addData('LSL_Time', last_lifu_time)
        # using non-slip timing so subtract the expected duration of this Routine (unless ended on request)
        if N_back_2_trials.maxDurationReached:
            routineTimer.addTime(-N_back_2_trials.maxDuration)
        elif N_back_2_trials.forceEnded:
            routineTimer.reset()
        else:
            routineTimer.addTime(-2.000000)
        # mark thisTrial_2 as finished
        if hasattr(thisTrial_2, 'status'):
            thisTrial_2.status = FINISHED
        # if awaiting a pause, pause now
        if trials_2.status == PAUSED:
            thisExp.status = PAUSED
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[globalClock], 
            )
            # once done pausing, restore running status
            trials_2.status = STARTED
        thisExp.nextEntry()
        
    # completed 1 repeats of 'trials_2'
    trials_2.status = FINISHED
    
    if thisSession is not None:
        # if running in a Session with a Liaison client, send data up to now
        thisSession.sendExperimentData()
    
    # --- Prepare to start Routine "End" ---
    # create an object to store info about Routine End
    End = data.Routine(
        name='End',
        components=[thank_you],
    )
    End.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # store start times for End
    End.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    End.tStart = globalClock.getTime(format='float')
    End.status = STARTED
    thisExp.addData('End.started', End.tStart)
    End.maxDuration = None
    # keep track of which components have finished
    EndComponents = End.components
    for thisComponent in End.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1
    
    # --- Run Routine "End" ---
    thisExp.currentRoutine = End
    End.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine and routineTimer.getTime() < 3.0:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *thank_you* updates
        
        # if thank_you is starting this frame...
        if thank_you.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            thank_you.frameNStart = frameN  # exact frame index
            thank_you.tStart = t  # local t and not account for scr refresh
            thank_you.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(thank_you, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'thank_you.started')
            # update status
            thank_you.status = STARTED
            thank_you.setAutoDraw(True)
        
        # if thank_you is active this frame...
        if thank_you.status == STARTED:
            # update params
            pass
        
        # if thank_you is stopping this frame...
        if thank_you.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > thank_you.tStartRefresh + 3-frameTolerance:
                # keep track of stop time/frame for later
                thank_you.tStop = t  # not accounting for scr refresh
                thank_you.tStopRefresh = tThisFlipGlobal  # on global time
                thank_you.frameNStop = frameN  # exact frame index
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'thank_you.stopped')
                # update status
                thank_you.status = FINISHED
                thank_you.setAutoDraw(False)
        
        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=["escape"]):
            thisExp.status = FINISHED
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[routineTimer, globalClock], 
                currentRoutine=End,
            )
            # skip the frame we paused on
            continue
        
        # has a Component requested the Routine to end?
        if not continueRoutine:
            End.forceEnded = routineForceEnded = True
        # has the Routine been forcibly ended?
        if End.forceEnded or routineForceEnded:
            break
        # has every Component finished?
        continueRoutine = False
        for thisComponent in End.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # --- Ending Routine "End" ---
    for thisComponent in End.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for End
    End.tStop = globalClock.getTime(format='float')
    End.tStopRefresh = tThisFlipGlobal
    thisExp.addData('End.stopped', End.tStop)
    # using non-slip timing so subtract the expected duration of this Routine (unless ended on request)
    if End.maxDurationReached:
        routineTimer.addTime(-End.maxDuration)
    elif End.forceEnded:
        routineTimer.reset()
    else:
        routineTimer.addTime(-3.000000)
    thisExp.nextEntry()
    
    # mark experiment as finished
    endExperiment(thisExp, win=win)


def saveData(thisExp):
    """
    Save data from this experiment
    
    Parameters
    ==========
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    """
    filename = thisExp.dataFileName
    # these shouldn't be strictly necessary (should auto-save)
    thisExp.saveAsWideText(filename + '.csv', delim='auto')
    thisExp.saveAsPickle(filename)


def endExperiment(thisExp, win=None):
    """
    End this experiment, performing final shut down operations.
    
    This function does NOT close the window or end the Python process - use `quit` for this.
    
    Parameters
    ==========
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    win : psychopy.visual.Window
        Window for this experiment.
    """
    # stop any playback components
    if thisExp.currentRoutine is not None:
        for comp in thisExp.currentRoutine.getPlaybackComponents():
            comp.stop()
    if win is not None:
        # remove autodraw from all current components
        win.clearAutoDraw()
        # Flip one final time so any remaining win.callOnFlip() 
        # and win.timeOnFlip() tasks get executed
        win.flip()
    # return console logger level to WARNING
    logging.console.setLevel(logging.WARNING)
    # mark experiment handler as finished
    thisExp.status = FINISHED
    # run any 'at exit' functions
    for fcn in runAtExit:
        fcn()
    logging.flush()


def quit(thisExp, win=None, thisSession=None):
    """
    Fully quit, closing the window and ending the Python process.
    
    Parameters
    ==========
    win : psychopy.visual.Window
        Window to close.
    thisSession : psychopy.session.Session or None
        Handle of the Session object this experiment is being run from, if any.
    """
    thisExp.abort()  # or data files will save again on exit
    # make sure everything is closed down
    if win is not None:
        # Flip one final time so any remaining win.callOnFlip() 
        # and win.timeOnFlip() tasks get executed before quitting
        win.flip()
        win.close()
    logging.flush()
    if thisSession is not None:
        thisSession.stop()
    # terminate Python process
    core.quit()


# if running this experiment as a script...
if __name__ == '__main__':
    # call all functions in order
    expInfo = showExpInfoDlg(expInfo=expInfo)
    thisExp = setupData(expInfo=expInfo)
    logFile = setupLogging(filename=thisExp.dataFileName)
    win = setupWindow(expInfo=expInfo)
    setupDevices(expInfo=expInfo, thisExp=thisExp, win=win)
    run(
        expInfo=expInfo, 
        thisExp=thisExp, 
        win=win,
        globalClock='float'
    )
    saveData(thisExp=thisExp)
    quit(thisExp=thisExp, win=win)
