/***************** 
 * Untitled *
 *****************/


// store info about the experiment session:
let expName = 'untitled';  // from the Builder filename that created this script
let expInfo = {
    'participant': '',
    'session': '001',
};
let PILOTING = util.getUrlParameters().has('__pilotToken');

// Start code blocks for 'Before Experiment'
// init psychoJS:
const psychoJS = new PsychoJS({
  debug: true
});

// open window:
psychoJS.openWindow({
  fullscr: true,
  color: new util.Color([0, 0, 0]),
  units: 'height',
  waitBlanking: true,
  backgroundImage: '',
  backgroundFit: 'none',
});
// schedule the experiment:
psychoJS.schedule(psychoJS.gui.DlgFromDict({
  dictionary: expInfo,
  title: expName
}));

const flowScheduler = new Scheduler(psychoJS);
const dialogCancelScheduler = new Scheduler(psychoJS);
psychoJS.scheduleCondition(function() { return (psychoJS.gui.dialogComponent.button === 'OK'); },flowScheduler, dialogCancelScheduler);

// flowScheduler gets run if the participants presses OK
flowScheduler.add(updateInfo); // add timeStamp
flowScheduler.add(experimentInit);
flowScheduler.add(Instructions_2RoutineBegin());
flowScheduler.add(Instructions_2RoutineEachFrame());
flowScheduler.add(Instructions_2RoutineEnd());
flowScheduler.add(FixationRoutineBegin());
flowScheduler.add(FixationRoutineEachFrame());
flowScheduler.add(FixationRoutineEnd());
const trials_2LoopScheduler = new Scheduler(psychoJS);
flowScheduler.add(trials_2LoopBegin(trials_2LoopScheduler));
flowScheduler.add(trials_2LoopScheduler);
flowScheduler.add(trials_2LoopEnd);


flowScheduler.add(EndRoutineBegin());
flowScheduler.add(EndRoutineEachFrame());
flowScheduler.add(EndRoutineEnd());
flowScheduler.add(quitPsychoJS, 'Thank you for your patience.', true);

// quit if user presses Cancel in dialog box:
dialogCancelScheduler.add(quitPsychoJS, 'Thank you for your patience.', false);

psychoJS.start({
  expName: expName,
  expInfo: expInfo,
  });
  
psychoJS.experimentLogger.setLevel(core.Logger.ServerLevel.EXP);

async function updateInfo() {
  currentLoop = psychoJS.experiment;  // right now there are no loops
  expInfo['date'] = util.MonotonicClock.getDateStr();  // add a simple timestamp
  expInfo['expName'] = expName;
  expInfo['psychopyVersion'] = '2026.1.3';
  expInfo['OS'] = window.navigator.platform;


  // store frame rate of monitor if we can measure it successfully
  expInfo['frameRate'] = psychoJS.window.getActualFrameRate();
  if (typeof expInfo['frameRate'] !== 'undefined')
    frameDur = 1.0 / Math.round(expInfo['frameRate']);
  else
    frameDur = 1.0 / 60.0; // couldn't get a reliable measure so guess

  // add info from the URL:
  util.addInfoFromUrl(expInfo);
  

  
  psychoJS.experiment.dataFileName = (("." + "/") + `data/${expInfo["participant"]}_${expName}_${expInfo["date"]}`);
  psychoJS.experiment.field_separator = '\t';


  return Scheduler.Event.NEXT;
}

async function experimentInit() {
  // Initialize components for Routine "Instructions_2"
  Instructions_2Clock = new util.Clock();
  instructions_2 = new visual.TextStim({
    win: psychoJS.window,
    name: 'instructions_2',
    text: 'In this 2‑back task, you will see a series of squares appear one at a time on the screen. Your job is to press the match key whenever the current square is the same as the one shown two squares earlier, and do nothing otherwise. Respond as quickly and accurately as you can throughout the sequence.\n\nFor example if the square appeared in left down corner on trial 1, you should press space if the square appears in the left down corner on trial 3. Press space to continue.',
    font: 'Arial',
    units: undefined, 
    pos: [0, 0], draggable: false, height: 0.05,  wrapWidth: undefined, ori: 0,
    languageStyle: 'LTR',
    color: new util.Color('white'),  opacity: 1,
    depth: 0.0 
  });
  
  key_resp_2 = new core.Keyboard({psychoJS: psychoJS, clock: new util.Clock(), waitForStart: true});
  
  // Run 'Begin Experiment' code from code
  import {StreamInlet, resolve_stream} from 'pylsl';
  console.log("Looking for LIFU marker stream...");
  lifu_streams = resolve_stream("name", "LIFU_Markers");
  lifu_inlet = new StreamInlet(lifu_streams[0]);
  console.log("Connected to LIFU marker stream.");
  stim_active = false;
  
  // Initialize components for Routine "Fixation"
  FixationClock = new util.Clock();
  fixation_1 = new visual.TextStim({
    win: psychoJS.window,
    name: 'fixation_1',
    text: '+',
    font: 'Arial',
    units: undefined, 
    pos: [0, 0], draggable: false, height: 0.05,  wrapWidth: undefined, ori: 0,
    languageStyle: 'LTR',
    color: new util.Color('white'),  opacity: 1,
    depth: 0.0 
  });
  
  // Initialize components for Routine "N_back_2_trials"
  N_back_2_trialsClock = new util.Clock();
  grid_lines_2 = new visual.ImageStim({
    win : psychoJS.window,
    name : 'grid_lines_2', units : undefined, 
    image : 'grid', mask : undefined,
    anchor : 'center',
    ori : 0, 
    pos : [0, 0], 
    draggable: false,
    size : [0.6, 0.6],
    color : new util.Color([1, 1, 1]), opacity : 1,
    flipHoriz : false, flipVert : false,
    texRes : 128, interpolate : true, depth : 0.0 
  });
  target_square_2 = new visual.Rect ({
    win: psychoJS.window, name: 'target_square_2', 
    width: [0.15, 0.15][0], height: [0.15, 0.15][1],
    ori: 0, 
    pos: [0, 0], 
    draggable: false, 
    anchor: 'center', 
    lineWidth: 1, 
    lineColor: undefined, 
    fillColor: new util.Color([1.0, 1.0, 1.0]), 
    colorSpace: 'rgb', 
    opacity: 1, 
    depth: -1, 
    interpolate: true, 
  });
  
  fixation_3 = new visual.TextStim({
    win: psychoJS.window,
    name: 'fixation_3',
    text: '+',
    font: 'Arial',
    units: undefined, 
    pos: [0, 0], draggable: false, height: 0.05,  wrapWidth: undefined, ori: 0,
    languageStyle: 'LTR',
    color: new util.Color('white'),  opacity: 1,
    depth: -2.0 
  });
  
  response_2 = new core.Keyboard({psychoJS: psychoJS, clock: new util.Clock(), waitForStart: true});
  
  // Initialize components for Routine "End"
  EndClock = new util.Clock();
  thank_you = new visual.TextStim({
    win: psychoJS.window,
    name: 'thank_you',
    text: 'This is the end of the experiment.\nThank you for your time.',
    font: 'Arial',
    units: undefined, 
    pos: [0, 0], draggable: false, height: 0.1,  wrapWidth: undefined, ori: 0,
    languageStyle: 'LTR',
    color: new util.Color('white'),  opacity: 1,
    depth: 0.0 
  });
  
  // Create some handy timers
  globalClock = new util.Clock();  // to track the time since experiment started
  routineTimer = new util.CountdownTimer();  // to track time remaining of each (non-slip) routine
  
  return Scheduler.Event.NEXT;
}

function Instructions_2RoutineBegin(snapshot) {
  return async function () {
    TrialHandler.fromSnapshot(snapshot); // ensure that .thisN vals are up to date
    
    //--- Prepare to start Routine 'Instructions_2' ---
    t = 0;
    frameN = -1;
    continueRoutine = true; // until we're told otherwise
    // keep track of whether this Routine was forcibly ended
    routineForceEnded = false;
    Instructions_2Clock.reset();
    routineTimer.reset();
    Instructions_2MaxDurationReached = false;
    // update component parameters for each repeat
    key_resp_2.keys = undefined;
    key_resp_2.rt = undefined;
    _key_resp_2_allKeys = [];
    psychoJS.experiment.addData('Instructions_2.started', globalClock.getTime());
    Instructions_2MaxDuration = null
    // keep track of which components have finished
    Instructions_2Components = [];
    Instructions_2Components.push(instructions_2);
    Instructions_2Components.push(key_resp_2);
    
    Instructions_2Components.forEach( function(thisComponent) {
      if ('status' in thisComponent)
        thisComponent.status = PsychoJS.Status.NOT_STARTED;
       });
    return Scheduler.Event.NEXT;
  }
}

function Instructions_2RoutineEachFrame() {
  return async function () {
    //--- Loop for each frame of Routine 'Instructions_2' ---
    // get current time
    t = Instructions_2Clock.getTime();
    frameN = frameN + 1;// number of completed frames (so 0 is the first frame)
    // update/draw components on each frame
    
    // *instructions_2* updates
    if (t >= 0.0 && instructions_2.status === PsychoJS.Status.NOT_STARTED) {
      // keep track of start time/frame for later
      instructions_2.tStart = t;  // (not accounting for frame time here)
      instructions_2.frameNStart = frameN;  // exact frame index
      
      instructions_2.setAutoDraw(true);
    }
    
    
    // if instructions_2 is active this frame...
    if (instructions_2.status === PsychoJS.Status.STARTED) {
    }
    
    
    // *key_resp_2* updates
    if (t >= 0.0 && key_resp_2.status === PsychoJS.Status.NOT_STARTED) {
      // keep track of start time/frame for later
      key_resp_2.tStart = t;  // (not accounting for frame time here)
      key_resp_2.frameNStart = frameN;  // exact frame index
      
      // keyboard checking is just starting
      psychoJS.window.callOnFlip(function() { key_resp_2.clock.reset(); });  // t=0 on next screen flip
      psychoJS.window.callOnFlip(function() { key_resp_2.start(); }); // start on screen flip
      psychoJS.window.callOnFlip(function() { key_resp_2.clearEvents(); });
    }
    
    // if key_resp_2 is active this frame...
    if (key_resp_2.status === PsychoJS.Status.STARTED) {
      let theseKeys = key_resp_2.getKeys({
        keyList: typeof 'space' === 'string' ? ['space'] : 'space', 
        waitRelease: false
      });
      _key_resp_2_allKeys = _key_resp_2_allKeys.concat(theseKeys);
      if (_key_resp_2_allKeys.length > 0) {
        key_resp_2.keys = _key_resp_2_allKeys[_key_resp_2_allKeys.length - 1].name;  // just the last key pressed
        key_resp_2.rt = _key_resp_2_allKeys[_key_resp_2_allKeys.length - 1].rt;
        key_resp_2.duration = _key_resp_2_allKeys[_key_resp_2_allKeys.length - 1].duration;
        // a response ends the routine
        continueRoutine = false;
      }
    }
    
    // check for quit (typically the Esc key)
    if (psychoJS.experiment.experimentEnded || psychoJS.eventManager.getKeys({keyList:['escape']}).length > 0) {
      return quitPsychoJS('The [Escape] key was pressed. Goodbye!', false);
    }
    
    // check if the Routine should terminate
    if (!continueRoutine) {  // a component has requested a forced-end of Routine
      routineForceEnded = true;
      return Scheduler.Event.NEXT;
    }
    
    continueRoutine = false;  // reverts to True if at least one component still running
    Instructions_2Components.forEach( function(thisComponent) {
      if ('status' in thisComponent && thisComponent.status !== PsychoJS.Status.FINISHED) {
        continueRoutine = true;
      }
    });
    
    // refresh the screen if continuing
    if (continueRoutine) {
      return Scheduler.Event.FLIP_REPEAT;
    } else {
      return Scheduler.Event.NEXT;
    }
  };
}

function Instructions_2RoutineEnd(snapshot) {
  return async function () {
    //--- Ending Routine 'Instructions_2' ---
    Instructions_2Components.forEach( function(thisComponent) {
      if (typeof thisComponent.setAutoDraw === 'function') {
        thisComponent.setAutoDraw(false);
      }
    });
    psychoJS.experiment.addData('Instructions_2.stopped', globalClock.getTime());
    // update the trial handler
    if (currentLoop instanceof MultiStairHandler) {
      currentLoop.addResponse(key_resp_2.corr, level);
    }
    psychoJS.experiment.addData('key_resp_2.keys', key_resp_2.keys);
    if (typeof key_resp_2.keys !== 'undefined') {  // we had a response
        psychoJS.experiment.addData('key_resp_2.rt', key_resp_2.rt);
        psychoJS.experiment.addData('key_resp_2.duration', key_resp_2.duration);
        routineTimer.reset();
        }
    
    key_resp_2.stop();
    // the Routine "Instructions_2" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset();
    
    // Routines running outside a loop should always advance the datafile row
    if (currentLoop === psychoJS.experiment) {
      psychoJS.experiment.nextEntry(snapshot);
    }
    return Scheduler.Event.NEXT;
  }
}

function FixationRoutineBegin(snapshot) {
  return async function () {
    TrialHandler.fromSnapshot(snapshot); // ensure that .thisN vals are up to date
    
    //--- Prepare to start Routine 'Fixation' ---
    t = 0;
    frameN = -1;
    continueRoutine = true; // until we're told otherwise
    // keep track of whether this Routine was forcibly ended
    routineForceEnded = false;
    FixationClock.reset(routineTimer.getTime());
    routineTimer.add(1.000000);
    FixationMaxDurationReached = false;
    // update component parameters for each repeat
    psychoJS.experiment.addData('Fixation.started', globalClock.getTime());
    FixationMaxDuration = null
    // keep track of which components have finished
    FixationComponents = [];
    FixationComponents.push(fixation_1);
    
    FixationComponents.forEach( function(thisComponent) {
      if ('status' in thisComponent)
        thisComponent.status = PsychoJS.Status.NOT_STARTED;
       });
    return Scheduler.Event.NEXT;
  }
}

function FixationRoutineEachFrame() {
  return async function () {
    //--- Loop for each frame of Routine 'Fixation' ---
    // get current time
    t = FixationClock.getTime();
    frameN = frameN + 1;// number of completed frames (so 0 is the first frame)
    // update/draw components on each frame
    
    // *fixation_1* updates
    if (t >= 0.0 && fixation_1.status === PsychoJS.Status.NOT_STARTED) {
      // keep track of start time/frame for later
      fixation_1.tStart = t;  // (not accounting for frame time here)
      fixation_1.frameNStart = frameN;  // exact frame index
      
      fixation_1.setAutoDraw(true);
    }
    
    
    // if fixation_1 is active this frame...
    if (fixation_1.status === PsychoJS.Status.STARTED) {
    }
    
    frameRemains = 0.0 + 1.0 - psychoJS.window.monitorFramePeriod * 0.75;// most of one frame period left
    if (fixation_1.status === PsychoJS.Status.STARTED && t >= frameRemains) {
      // keep track of stop time/frame for later
      fixation_1.tStop = t;  // not accounting for scr refresh
      fixation_1.frameNStop = frameN;  // exact frame index
      // update status
      fixation_1.status = PsychoJS.Status.FINISHED;
      fixation_1.setAutoDraw(false);
    }
    
    // check for quit (typically the Esc key)
    if (psychoJS.experiment.experimentEnded || psychoJS.eventManager.getKeys({keyList:['escape']}).length > 0) {
      return quitPsychoJS('The [Escape] key was pressed. Goodbye!', false);
    }
    
    // check if the Routine should terminate
    if (!continueRoutine) {  // a component has requested a forced-end of Routine
      routineForceEnded = true;
      return Scheduler.Event.NEXT;
    }
    
    continueRoutine = false;  // reverts to True if at least one component still running
    FixationComponents.forEach( function(thisComponent) {
      if ('status' in thisComponent && thisComponent.status !== PsychoJS.Status.FINISHED) {
        continueRoutine = true;
      }
    });
    
    // refresh the screen if continuing
    if (continueRoutine && routineTimer.getTime() > 0) {
      return Scheduler.Event.FLIP_REPEAT;
    } else {
      return Scheduler.Event.NEXT;
    }
  };
}

function FixationRoutineEnd(snapshot) {
  return async function () {
    //--- Ending Routine 'Fixation' ---
    FixationComponents.forEach( function(thisComponent) {
      if (typeof thisComponent.setAutoDraw === 'function') {
        thisComponent.setAutoDraw(false);
      }
    });
    psychoJS.experiment.addData('Fixation.stopped', globalClock.getTime());
    if (routineForceEnded) {
        routineTimer.reset();} else if (FixationMaxDurationReached) {
        FixationClock.add(FixationMaxDuration);
    } else {
        FixationClock.add(1.000000);
    }
    // Routines running outside a loop should always advance the datafile row
    if (currentLoop === psychoJS.experiment) {
      psychoJS.experiment.nextEntry(snapshot);
    }
    return Scheduler.Event.NEXT;
  }
}

function trials_2LoopBegin(trials_2LoopScheduler, snapshot) {
  return async function() {
    TrialHandler.fromSnapshot(snapshot); // update internal variables (.thisN etc) of the loop
    
    // set up handler to look after randomisation of conditions etc
    trials_2 = new TrialHandler({
      psychoJS: psychoJS,
      nReps: 7, method: TrialHandler.Method.SEQUENTIAL,
      extraInfo: expInfo, originPath: undefined,
      trialList: 'N-back-2.xlsx',
      seed: undefined, name: 'trials_2'
    });
    psychoJS.experiment.addLoop(trials_2); // add the loop to the experiment
    currentLoop = trials_2;  // we're now the current loop
    
    // Schedule all the trials in the trialList:
    trials_2.forEach(function() {
      snapshot = trials_2.getSnapshot();
    
      trials_2LoopScheduler.add(importConditions(snapshot));
      trials_2LoopScheduler.add(N_back_2_trialsRoutineBegin(snapshot));
      trials_2LoopScheduler.add(N_back_2_trialsRoutineEachFrame());
      trials_2LoopScheduler.add(N_back_2_trialsRoutineEnd(snapshot));
      trials_2LoopScheduler.add(trials_2LoopEndIteration(trials_2LoopScheduler, snapshot));
    });
    
    return Scheduler.Event.NEXT;
  }
}

async function trials_2LoopEnd() {
  // terminate loop
  psychoJS.experiment.removeLoop(trials_2);
  // update the current loop from the ExperimentHandler
  if (psychoJS.experiment._unfinishedLoops.length>0)
    currentLoop = psychoJS.experiment._unfinishedLoops.at(-1);
  else
    currentLoop = psychoJS.experiment;  // so we use addData from the experiment
  return Scheduler.Event.NEXT;
}

function trials_2LoopEndIteration(scheduler, snapshot) {
  // ------Prepare for next entry------
  return async function () {
    if (typeof snapshot !== 'undefined') {
      // ------Check if user ended loop early------
      if (snapshot.finished) {
        // Check for and save orphaned data
        if (psychoJS.experiment.isEntryEmpty()) {
          psychoJS.experiment.nextEntry(snapshot);
        }
        scheduler.stop();
      } else {
        psychoJS.experiment.nextEntry(snapshot);
      }
    return Scheduler.Event.NEXT;
    }
  };
}

function N_back_2_trialsRoutineBegin(snapshot) {
  return async function () {
    TrialHandler.fromSnapshot(snapshot); // ensure that .thisN vals are up to date
    
    //--- Prepare to start Routine 'N_back_2_trials' ---
    t = 0;
    frameN = -1;
    continueRoutine = true; // until we're told otherwise
    // keep track of whether this Routine was forcibly ended
    routineForceEnded = false;
    N_back_2_trialsClock.reset(routineTimer.getTime());
    routineTimer.add(2.000000);
    N_back_2_trialsMaxDurationReached = false;
    // update component parameters for each repeat
    target_square_2.setPos(location);
    response_2.keys = undefined;
    response_2.rt = undefined;
    _response_2_allKeys = [];
    psychoJS.experiment.addData('N_back_2_trials.started', globalClock.getTime());
    N_back_2_trialsMaxDuration = null
    // keep track of which components have finished
    N_back_2_trialsComponents = [];
    N_back_2_trialsComponents.push(grid_lines_2);
    N_back_2_trialsComponents.push(target_square_2);
    N_back_2_trialsComponents.push(fixation_3);
    N_back_2_trialsComponents.push(response_2);
    
    N_back_2_trialsComponents.forEach( function(thisComponent) {
      if ('status' in thisComponent)
        thisComponent.status = PsychoJS.Status.NOT_STARTED;
       });
    return Scheduler.Event.NEXT;
  }
}

function N_back_2_trialsRoutineEachFrame() {
  return async function () {
    //--- Loop for each frame of Routine 'N_back_2_trials' ---
    // get current time
    t = N_back_2_trialsClock.getTime();
    frameN = frameN + 1;// number of completed frames (so 0 is the first frame)
    // update/draw components on each frame
    
    // *grid_lines_2* updates
    if (t >= 0.0 && grid_lines_2.status === PsychoJS.Status.NOT_STARTED) {
      // keep track of start time/frame for later
      grid_lines_2.tStart = t;  // (not accounting for frame time here)
      grid_lines_2.frameNStart = frameN;  // exact frame index
      
      grid_lines_2.setAutoDraw(true);
    }
    
    
    // if grid_lines_2 is active this frame...
    if (grid_lines_2.status === PsychoJS.Status.STARTED) {
    }
    
    frameRemains = 0.0 + 2 - psychoJS.window.monitorFramePeriod * 0.75;// most of one frame period left
    if (grid_lines_2.status === PsychoJS.Status.STARTED && t >= frameRemains) {
      // keep track of stop time/frame for later
      grid_lines_2.tStop = t;  // not accounting for scr refresh
      grid_lines_2.frameNStop = frameN;  // exact frame index
      // update status
      grid_lines_2.status = PsychoJS.Status.FINISHED;
      grid_lines_2.setAutoDraw(false);
    }
    
    
    // *target_square_2* updates
    if (t >= 0 && target_square_2.status === PsychoJS.Status.NOT_STARTED) {
      // keep track of start time/frame for later
      target_square_2.tStart = t;  // (not accounting for frame time here)
      target_square_2.frameNStart = frameN;  // exact frame index
      
      target_square_2.setAutoDraw(true);
    }
    
    
    // if target_square_2 is active this frame...
    if (target_square_2.status === PsychoJS.Status.STARTED) {
    }
    
    frameRemains = 0 + 1.0 - psychoJS.window.monitorFramePeriod * 0.75;// most of one frame period left
    if (target_square_2.status === PsychoJS.Status.STARTED && t >= frameRemains) {
      // keep track of stop time/frame for later
      target_square_2.tStop = t;  // not accounting for scr refresh
      target_square_2.frameNStop = frameN;  // exact frame index
      // update status
      target_square_2.status = PsychoJS.Status.FINISHED;
      target_square_2.setAutoDraw(false);
    }
    
    
    // *fixation_3* updates
    if (t >= 1 && fixation_3.status === PsychoJS.Status.NOT_STARTED) {
      // keep track of start time/frame for later
      fixation_3.tStart = t;  // (not accounting for frame time here)
      fixation_3.frameNStart = frameN;  // exact frame index
      
      fixation_3.setAutoDraw(true);
    }
    
    
    // if fixation_3 is active this frame...
    if (fixation_3.status === PsychoJS.Status.STARTED) {
    }
    
    frameRemains = 1 + 1 - psychoJS.window.monitorFramePeriod * 0.75;// most of one frame period left
    if (fixation_3.status === PsychoJS.Status.STARTED && t >= frameRemains) {
      // keep track of stop time/frame for later
      fixation_3.tStop = t;  // not accounting for scr refresh
      fixation_3.frameNStop = frameN;  // exact frame index
      // update status
      fixation_3.status = PsychoJS.Status.FINISHED;
      fixation_3.setAutoDraw(false);
    }
    
    
    // *response_2* updates
    if (t >= 0.0 && response_2.status === PsychoJS.Status.NOT_STARTED) {
      // keep track of start time/frame for later
      response_2.tStart = t;  // (not accounting for frame time here)
      response_2.frameNStart = frameN;  // exact frame index
      
      // keyboard checking is just starting
      psychoJS.window.callOnFlip(function() { response_2.clock.reset(); });  // t=0 on next screen flip
      psychoJS.window.callOnFlip(function() { response_2.start(); }); // start on screen flip
      psychoJS.window.callOnFlip(function() { response_2.clearEvents(); });
    }
    frameRemains = 0.0 + 2 - psychoJS.window.monitorFramePeriod * 0.75;// most of one frame period left
    if (response_2.status === PsychoJS.Status.STARTED && t >= frameRemains) {
      // keep track of stop time/frame for later
      response_2.tStop = t;  // not accounting for scr refresh
      response_2.frameNStop = frameN;  // exact frame index
      // update status
      response_2.status = PsychoJS.Status.FINISHED;
      frameRemains = 0.0 + 2 - psychoJS.window.monitorFramePeriod * 0.75;// most of one frame period left
      if (response_2.status === PsychoJS.Status.STARTED && t >= frameRemains) {
        // keep track of stop time/frame for later
        response_2.tStop = t;  // not accounting for scr refresh
        response_2.frameNStop = frameN;  // exact frame index
        // update status
        response_2.status = PsychoJS.Status.FINISHED;
        response_2.status = PsychoJS.Status.FINISHED;
          }
        
      }
      
      // if response_2 is active this frame...
      if (response_2.status === PsychoJS.Status.STARTED) {
        let theseKeys = response_2.getKeys({
          keyList: typeof 'space' === 'string' ? ['space'] : 'space', 
          waitRelease: false
        });
        _response_2_allKeys = _response_2_allKeys.concat(theseKeys);
        if (_response_2_allKeys.length > 0) {
          response_2.keys = _response_2_allKeys[_response_2_allKeys.length - 1].name;  // just the last key pressed
          response_2.rt = _response_2_allKeys[_response_2_allKeys.length - 1].rt;
          response_2.duration = _response_2_allKeys[_response_2_allKeys.length - 1].duration;
          // was this correct?
          if (response_2.keys == corrAns) {
              response_2.corr = 1;
          } else {
              response_2.corr = 0;
          }
        }
      }
      
      // Run 'Each Frame' code from code_2
      [marker, ts] = lifu_inlet.pull_sample({"timeout": 0.0});
      if (marker) {
          current_marker = marker[0];
          console.log("Received LIFU marker:", current_marker);
          if ((current_marker === "LIFU_START")) {
              stim_active = true;
          } else {
              if ((current_marker === "LIFU_STOP")) {
                  stim_active = false;
              }
          }
          psychoJS.experiment.addData("LIFU_marker_frame", current_marker);
      }
      
      // check for quit (typically the Esc key)
      if (psychoJS.experiment.experimentEnded || psychoJS.eventManager.getKeys({keyList:['escape']}).length > 0) {
        return quitPsychoJS('The [Escape] key was pressed. Goodbye!', false);
      }
      
      // check if the Routine should terminate
      if (!continueRoutine) {  // a component has requested a forced-end of Routine
        routineForceEnded = true;
        return Scheduler.Event.NEXT;
      }
      
      continueRoutine = false;  // reverts to True if at least one component still running
      N_back_2_trialsComponents.forEach( function(thisComponent) {
        if ('status' in thisComponent && thisComponent.status !== PsychoJS.Status.FINISHED) {
          continueRoutine = true;
        }
      });
      
      // refresh the screen if continuing
      if (continueRoutine && routineTimer.getTime() > 0) {
        return Scheduler.Event.FLIP_REPEAT;
      } else {
        return Scheduler.Event.NEXT;
      }
    };
  }
  
  function N_back_2_trialsRoutineEnd(snapshot) {
    return async function () {
      //--- Ending Routine 'N_back_2_trials' ---
      N_back_2_trialsComponents.forEach( function(thisComponent) {
        if (typeof thisComponent.setAutoDraw === 'function') {
          thisComponent.setAutoDraw(false);
        }
      });
      psychoJS.experiment.addData('N_back_2_trials.stopped', globalClock.getTime());
      // was no response the correct answer?!
      if (response_2.keys === undefined) {
        if (['None','none',undefined].includes(corrAns)) {
           response_2.corr = 1;  // correct non-response
        } else {
           response_2.corr = 0;  // failed to respond (incorrectly)
        }
      }
      // store data for current loop
      // update the trial handler
      if (currentLoop instanceof MultiStairHandler) {
        currentLoop.addResponse(response_2.corr, level);
      }
      psychoJS.experiment.addData('response_2.keys', response_2.keys);
      psychoJS.experiment.addData('response_2.corr', response_2.corr);
      if (typeof response_2.keys !== 'undefined') {  // we had a response
          psychoJS.experiment.addData('response_2.rt', response_2.rt);
          psychoJS.experiment.addData('response_2.duration', response_2.duration);
          }
      
      response_2.stop();
      // Run 'End Routine' code from code_2
      psychoJS.experiment.addData("stim_active", stim_active);
      [marker, ts] = lifu_inlet.pull_sample({"timeout": 0.0});
      if (marker) {
          psychoJS.experiment.addData("LIFU_marker_endTrial", marker[0]);
      }
      
      if (routineForceEnded) {
          routineTimer.reset();} else if (N_back_2_trialsMaxDurationReached) {
          N_back_2_trialsClock.add(N_back_2_trialsMaxDuration);
      } else {
          N_back_2_trialsClock.add(2.000000);
      }
      // Routines running outside a loop should always advance the datafile row
      if (currentLoop === psychoJS.experiment) {
        psychoJS.experiment.nextEntry(snapshot);
      }
      return Scheduler.Event.NEXT;
    }
  }
  
  function EndRoutineBegin(snapshot) {
    return async function () {
      TrialHandler.fromSnapshot(snapshot); // ensure that .thisN vals are up to date
      
      //--- Prepare to start Routine 'End' ---
      t = 0;
      frameN = -1;
      continueRoutine = true; // until we're told otherwise
      // keep track of whether this Routine was forcibly ended
      routineForceEnded = false;
      EndClock.reset(routineTimer.getTime());
      routineTimer.add(3.000000);
      EndMaxDurationReached = false;
      // update component parameters for each repeat
      psychoJS.experiment.addData('End.started', globalClock.getTime());
      EndMaxDuration = null
      // keep track of which components have finished
      EndComponents = [];
      EndComponents.push(thank_you);
      
      EndComponents.forEach( function(thisComponent) {
        if ('status' in thisComponent)
          thisComponent.status = PsychoJS.Status.NOT_STARTED;
         });
      return Scheduler.Event.NEXT;
    }
  }
  
  function EndRoutineEachFrame() {
    return async function () {
      //--- Loop for each frame of Routine 'End' ---
      // get current time
      t = EndClock.getTime();
      frameN = frameN + 1;// number of completed frames (so 0 is the first frame)
      // update/draw components on each frame
      
      // *thank_you* updates
      if (t >= 0.0 && thank_you.status === PsychoJS.Status.NOT_STARTED) {
        // keep track of start time/frame for later
        thank_you.tStart = t;  // (not accounting for frame time here)
        thank_you.frameNStart = frameN;  // exact frame index
        
        thank_you.setAutoDraw(true);
      }
      
      
      // if thank_you is active this frame...
      if (thank_you.status === PsychoJS.Status.STARTED) {
      }
      
      frameRemains = 0.0 + 3 - psychoJS.window.monitorFramePeriod * 0.75;// most of one frame period left
      if (thank_you.status === PsychoJS.Status.STARTED && t >= frameRemains) {
        // keep track of stop time/frame for later
        thank_you.tStop = t;  // not accounting for scr refresh
        thank_you.frameNStop = frameN;  // exact frame index
        // update status
        thank_you.status = PsychoJS.Status.FINISHED;
        thank_you.setAutoDraw(false);
      }
      
      // check for quit (typically the Esc key)
      if (psychoJS.experiment.experimentEnded || psychoJS.eventManager.getKeys({keyList:['escape']}).length > 0) {
        return quitPsychoJS('The [Escape] key was pressed. Goodbye!', false);
      }
      
      // check if the Routine should terminate
      if (!continueRoutine) {  // a component has requested a forced-end of Routine
        routineForceEnded = true;
        return Scheduler.Event.NEXT;
      }
      
      continueRoutine = false;  // reverts to True if at least one component still running
      EndComponents.forEach( function(thisComponent) {
        if ('status' in thisComponent && thisComponent.status !== PsychoJS.Status.FINISHED) {
          continueRoutine = true;
        }
      });
      
      // refresh the screen if continuing
      if (continueRoutine && routineTimer.getTime() > 0) {
        return Scheduler.Event.FLIP_REPEAT;
      } else {
        return Scheduler.Event.NEXT;
      }
    };
  }
  
  function EndRoutineEnd(snapshot) {
    return async function () {
      //--- Ending Routine 'End' ---
      EndComponents.forEach( function(thisComponent) {
        if (typeof thisComponent.setAutoDraw === 'function') {
          thisComponent.setAutoDraw(false);
        }
      });
      psychoJS.experiment.addData('End.stopped', globalClock.getTime());
      if (routineForceEnded) {
          routineTimer.reset();} else if (EndMaxDurationReached) {
          EndClock.add(EndMaxDuration);
      } else {
          EndClock.add(3.000000);
      }
      // Routines running outside a loop should always advance the datafile row
      if (currentLoop === psychoJS.experiment) {
        psychoJS.experiment.nextEntry(snapshot);
      }
      return Scheduler.Event.NEXT;
    }
  }
  
  function importConditions(currentLoop) {
    return async function () {
      psychoJS.importAttributes(currentLoop.getCurrentTrial());
      return Scheduler.Event.NEXT;
      };
  }
  
  async function quitPsychoJS(message, isCompleted) {
    // Check for and save orphaned data
    if (psychoJS.experiment.isEntryEmpty()) {
      psychoJS.experiment.nextEntry();
    }
    psychoJS.window.close();
    psychoJS.quit({message: message, isCompleted: isCompleted});
    
    return Scheduler.Event.QUIT;
  }
