/*************** 
 * N-Back Test *
 ***************/

import { PsychoJS } from 'https://pavlovia.org/lib/core.js';
import * as core from 'https://pavlovia.org/lib/core.js';
import { TrialHandler } from 'https://pavlovia.org/lib/data.js';
import { Scheduler } from 'https://pavlovia.org/lib/util.js';
import * as util from 'https://pavlovia.org/lib/util.js';
import * as visual from 'https://pavlovia.org/lib/visual.js';
import { Sound } from 'https://pavlovia.org/lib/sound.js';

// init psychoJS:
var psychoJS = new PsychoJS({
  debug: true
});

// open window:
psychoJS.openWindow({
  fullscr: true,
  color: new util.Color([0, 0, 0]),
  units: 'height'
});

// store info about the experiment session:
let expName = 'N-back';  // from the Builder filename that created this script
let expInfo = {'participant': '', 'session': '001'};

// schedule the experiment:
psychoJS.schedule(psychoJS.gui.DlgFromDict({
  dictionary: expInfo,
  title: expName
}));

const flowScheduler = new Scheduler(psychoJS);
const dialogCancelScheduler = new Scheduler(psychoJS);
psychoJS.scheduleCondition(function() { return (psychoJS.gui.dialogComponent.button === 'OK'); }, flowScheduler, dialogCancelScheduler);

// flowScheduler gets run if the participants presses OK
flowScheduler.add(updateInfo); // add timeStamp
flowScheduler.add(experimentInit);
flowScheduler.add(InstructionsRoutineBegin);
flowScheduler.add(InstructionsRoutineEachFrame);
flowScheduler.add(InstructionsRoutineEnd);
flowScheduler.add(FixationRoutineBegin);
flowScheduler.add(FixationRoutineEachFrame);
flowScheduler.add(FixationRoutineEnd);
const trialsLoopScheduler = new Scheduler(psychoJS);
flowScheduler.add(trialsLoopBegin, trialsLoopScheduler);
flowScheduler.add(trialsLoopScheduler);
flowScheduler.add(trialsLoopEnd);
flowScheduler.add(Instructions_2RoutineBegin);
flowScheduler.add(Instructions_2RoutineEachFrame);
flowScheduler.add(Instructions_2RoutineEnd);
flowScheduler.add(FixationRoutineBegin);
flowScheduler.add(FixationRoutineEachFrame);
flowScheduler.add(FixationRoutineEnd);
const trials_2LoopScheduler = new Scheduler(psychoJS);
flowScheduler.add(trials_2LoopBegin, trials_2LoopScheduler);
flowScheduler.add(trials_2LoopScheduler);
flowScheduler.add(trials_2LoopEnd);
flowScheduler.add(EndRoutineBegin);
flowScheduler.add(EndRoutineEachFrame);
flowScheduler.add(EndRoutineEnd);
flowScheduler.add(quitPsychoJS, '', true);

// quit if user presses Cancel in dialog box:
dialogCancelScheduler.add(quitPsychoJS, '', false);

psychoJS.start({expName, expInfo});

var frameDur;
function updateInfo() {
  expInfo['date'] = util.MonotonicClock.getDateStr();  // add a simple timestamp
  expInfo['expName'] = expName;
  expInfo['psychopyVersion'] = '3.1.2';

  // store frame rate of monitor if we can measure it successfully
  expInfo['frameRate'] = psychoJS.window.getActualFrameRate();
  if (typeof expInfo['frameRate'] !== 'undefined')
    frameDur = 1.0/Math.round(expInfo['frameRate']);
  else
    frameDur = 1.0/60.0; // couldn't get a reliable measure so guess

  // add info from the URL:
  util.addInfoFromUrl(expInfo);
  
  return Scheduler.Event.NEXT;
}

var InstructionsClock;
var instructions;
var FixationClock;
var fixation_1;
var N_back_1_TrialClock;
var grid_lines;
var target_square;
var fixation_2;
var Instructions_2Clock;
var instructions_2;
var N_back_2_trialsClock;
var grid_lines_2;
var target_square_2;
var fixation_3;
var EndClock;
var thank_you;
var globalClock;
var routineTimer;
function experimentInit() {
  // Initialize components for Routine "Instructions"
  InstructionsClock = new util.Clock();
  instructions = new visual.TextStim({
    win: psychoJS.window,
    name: 'instructions',
    text: 'In this task you will be required to press space if the white square appeared in the same location as the location on the last trial. For example if the square was in the left down corner on trial 1 and then it appeared in the same location on trial 2, press space. Otherwise, do not respond. Press space to continue.',
    font: 'Arial',
    units : undefined, 
    pos: [0, 0], height: 0.05,  wrapWidth: undefined, ori: 0,
    color: new util.Color('white'),  opacity: 1,
    depth: 0.0 
  });
  
  // Initialize components for Routine "Fixation"
  FixationClock = new util.Clock();
  fixation_1 = new visual.TextStim({
    win: psychoJS.window,
    name: 'fixation_1',
    text: '+',
    font: 'Arial',
    units : undefined, 
    pos: [0, 0], height: 0.05,  wrapWidth: undefined, ori: 0,
    color: new util.Color('white'),  opacity: 1,
    depth: 0.0 
  });
  
  // Initialize components for Routine "N_back_1_Trial"
  N_back_1_TrialClock = new util.Clock();
  grid_lines = new visual.ImageStim({
    win : psychoJS.window,
    name : 'grid_lines', units : undefined, 
    image : 'grid', mask : undefined,
    ori : 0, pos : [0, 0], size : [0.6, 0.6],
    color : new util.Color([1, 1, 1]), opacity : 1,
    flipHoriz : false, flipVert : false,
    texRes : 128, interpolate : true, depth : 0.0 
  });
  target_square = new visual.Rect ({
    win: psychoJS.window, name: 'target_square',
    units: 'height',
    width: [0.15, 0.15][0], height: [0.15, 0.15][1],
    ori: 0, pos: [0, 0],
    lineWidth: 1, lineColor: new util.Color(undefined),
    fillColor: new util.Color([1.0, 1.0, 1.0]),
    opacity: 1, depth: -1, interpolate: true,
  });
  
  fixation_2 = new visual.TextStim({
    win: psychoJS.window,
    name: 'fixation_2',
    text: '+',
    font: 'Arial',
    units : undefined, 
    pos: [0, 0], height: 0.05,  wrapWidth: undefined, ori: 0,
    color: new util.Color('white'),  opacity: 1,
    depth: -2.0 
  });
  
  // Initialize components for Routine "Instructions_2"
  Instructions_2Clock = new util.Clock();
  instructions_2 = new visual.TextStim({
    win: psychoJS.window,
    name: 'instructions_2',
    text: 'This is the end of N-back-1 trials. You are about to start N-back-2 trials. This means that instead of pressing space whenever the square appears in the same position as on the position on one trial before, you are required to press space whenever the square appears in the same position as on the position two trials before. For example if the square appeared in left down corner on trial 1, you should press space if the square appears in the left down corner on trial 3. Press space to continue.',
    font: 'Arial',
    units : undefined, 
    pos: [0, 0], height: 0.05,  wrapWidth: undefined, ori: 0,
    color: new util.Color('white'),  opacity: 1,
    depth: 0.0 
  });
  
  // Initialize components for Routine "Fixation"
  FixationClock = new util.Clock();
  fixation_1 = new visual.TextStim({
    win: psychoJS.window,
    name: 'fixation_1',
    text: '+',
    font: 'Arial',
    units : undefined, 
    pos: [0, 0], height: 0.05,  wrapWidth: undefined, ori: 0,
    color: new util.Color('white'),  opacity: 1,
    depth: 0.0 
  });
  
  // Initialize components for Routine "N_back_2_trials"
  N_back_2_trialsClock = new util.Clock();
  grid_lines_2 = new visual.ImageStim({
    win : psychoJS.window,
    name : 'grid_lines_2', units : undefined, 
    image : 'grid', mask : undefined,
    ori : 0, pos : [0, 0], size : [0.6, 0.6],
    color : new util.Color([1, 1, 1]), opacity : 1,
    flipHoriz : false, flipVert : false,
    texRes : 128, interpolate : true, depth : 0.0 
  });
  target_square_2 = new visual.Rect ({
    win: psychoJS.window, name: 'target_square_2',
    units: 'height',
    width: [0.15, 0.15][0], height: [0.15, 0.15][1],
    ori: 0, pos: [0, 0],
    lineWidth: 1, lineColor: new util.Color(undefined),
    fillColor: new util.Color([1.0, 1.0, 1.0]),
    opacity: 1, depth: -1, interpolate: true,
  });
  
  fixation_3 = new visual.TextStim({
    win: psychoJS.window,
    name: 'fixation_3',
    text: '+',
    font: 'Arial',
    units : undefined, 
    pos: [0, 0], height: 0.05,  wrapWidth: undefined, ori: 0,
    color: new util.Color('white'),  opacity: 1,
    depth: -2.0 
  });
  
  // Initialize components for Routine "End"
  EndClock = new util.Clock();
  thank_you = new visual.TextStim({
    win: psychoJS.window,
    name: 'thank_you',
    text: 'This is the end of the experiment.\nThank you for your time.',
    font: 'Arial',
    units : undefined, 
    pos: [0, 0], height: 0.1,  wrapWidth: undefined, ori: 0,
    color: new util.Color('white'),  opacity: 1,
    depth: 0.0 
  });
  
  // Create some handy timers
  globalClock = new util.Clock();  // to track the time since experiment started
  routineTimer = new util.CountdownTimer();  // to track time remaining of each (non-slip) routine
  
  return Scheduler.Event.NEXT;
}

var t;
var frameN;
var key_resp;
var InstructionsComponents;
function InstructionsRoutineBegin() {
  //------Prepare to start Routine 'Instructions'-------
  t = 0;
  InstructionsClock.reset(); // clock
  frameN = -1;
  // update component parameters for each repeat
  key_resp = new core.BuilderKeyResponse(psychoJS);
  
  // keep track of which components have finished
  InstructionsComponents = [];
  InstructionsComponents.push(instructions);
  InstructionsComponents.push(key_resp);
  
  for (const thisComponent of InstructionsComponents)
    if ('status' in thisComponent)
      thisComponent.status = PsychoJS.Status.NOT_STARTED;
  
  return Scheduler.Event.NEXT;
}

var continueRoutine;
function InstructionsRoutineEachFrame() {
  //------Loop for each frame of Routine 'Instructions'-------
  let continueRoutine = true; // until we're told otherwise
  // get current time
  t = InstructionsClock.getTime();
  frameN = frameN + 1;// number of completed frames (so 0 is the first frame)
  // update/draw components on each frame
  
  // *instructions* updates
  if (t >= 0.0 && instructions.status === PsychoJS.Status.NOT_STARTED) {
    // keep track of start time/frame for later
    instructions.tStart = t;  // (not accounting for frame time here)
    instructions.frameNStart = frameN;  // exact frame index
    instructions.setAutoDraw(true);
  }

  
  // *key_resp* updates
  if (t >= 0.0 && key_resp.status === PsychoJS.Status.NOT_STARTED) {
    // keep track of start time/frame for later
    key_resp.tStart = t;  // (not accounting for frame time here)
    key_resp.frameNStart = frameN;  // exact frame index
    key_resp.status = PsychoJS.Status.STARTED;
    // keyboard checking is just starting
    psychoJS.window.callOnFlip(function() { key_resp.clock.reset(); }); // t = 0 on screen flip
    psychoJS.eventManager.clearEvents({eventType:'keyboard'});
  }

  if (key_resp.status === PsychoJS.Status.STARTED) {
    let theseKeys = psychoJS.eventManager.getKeys({keyList:['space']});
    
    // check for quit:
    if (theseKeys.indexOf('escape') > -1) {
      psychoJS.experiment.experimentEnded = true;
    }
    
    if (theseKeys.length > 0) {  // at least one key was pressed
      key_resp.keys = theseKeys[theseKeys.length-1];  // just the last key pressed
      key_resp.rt = key_resp.clock.getTime();
      // a response ends the routine
      continueRoutine = false;
    }
  }
  
  // check for quit (typically the Esc key)
  if (psychoJS.experiment.experimentEnded || psychoJS.eventManager.getKeys({keyList:['escape']}).length > 0) {
    return psychoJS.quit('The [Escape] key was pressed. Goodbye!', false);
  }
  
  // check if the Routine should terminate
  if (!continueRoutine) {  // a component has requested a forced-end of Routine
    return Scheduler.Event.NEXT;
  }
  
  continueRoutine = false;  // reverts to True if at least one component still running
  for (const thisComponent of InstructionsComponents)
    if ('status' in thisComponent && thisComponent.status !== PsychoJS.Status.FINISHED) {
      continueRoutine = true;
      break;
    }
  
  // refresh the screen if continuing
  if (continueRoutine) {
    return Scheduler.Event.FLIP_REPEAT;
  }
  else {
    return Scheduler.Event.NEXT;
  }
}


function InstructionsRoutineEnd() {
  //------Ending Routine 'Instructions'-------
  for (const thisComponent of InstructionsComponents) {
    if (typeof thisComponent.setAutoDraw === 'function') {
      thisComponent.setAutoDraw(false);
    }
  }
  
  // check responses
  if (key_resp.keys === undefined || key_resp.keys.length === 0) {    // No response was made
      key_resp.keys = undefined;
  }
  
  psychoJS.experiment.addData('key_resp.keys', key_resp.keys);
  if (typeof key_resp.keys !== 'undefined') {  // we had a response
      psychoJS.experiment.addData('key_resp.rt', key_resp.rt);
      routineTimer.reset();
      }
  
  // the Routine "Instructions" was not non-slip safe, so reset the non-slip timer
  routineTimer.reset();
  
  return Scheduler.Event.NEXT;
}

var FixationComponents;
function FixationRoutineBegin() {
  //------Prepare to start Routine 'Fixation'-------
  t = 0;
  FixationClock.reset(); // clock
  frameN = -1;
  routineTimer.add(1.000000);
  // update component parameters for each repeat
  // keep track of which components have finished
  FixationComponents = [];
  FixationComponents.push(fixation_1);
  
  for (const thisComponent of FixationComponents)
    if ('status' in thisComponent)
      thisComponent.status = PsychoJS.Status.NOT_STARTED;
  
  return Scheduler.Event.NEXT;
}

var frameRemains;
function FixationRoutineEachFrame() {
  //------Loop for each frame of Routine 'Fixation'-------
  let continueRoutine = true; // until we're told otherwise
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

  frameRemains = 0.0 + 1.0 - psychoJS.window.monitorFramePeriod * 0.75;  // most of one frame period left
  if (fixation_1.status === PsychoJS.Status.STARTED && t >= frameRemains) {
    fixation_1.setAutoDraw(false);
  }
  // check for quit (typically the Esc key)
  if (psychoJS.experiment.experimentEnded || psychoJS.eventManager.getKeys({keyList:['escape']}).length > 0) {
    return psychoJS.quit('The [Escape] key was pressed. Goodbye!', false);
  }
  
  // check if the Routine should terminate
  if (!continueRoutine) {  // a component has requested a forced-end of Routine
    return Scheduler.Event.NEXT;
  }
  
  continueRoutine = false;  // reverts to True if at least one component still running
  for (const thisComponent of FixationComponents)
    if ('status' in thisComponent && thisComponent.status !== PsychoJS.Status.FINISHED) {
      continueRoutine = true;
      break;
    }
  
  // refresh the screen if continuing
  if (continueRoutine && routineTimer.getTime() > 0) {
    return Scheduler.Event.FLIP_REPEAT;
  }
  else {
    return Scheduler.Event.NEXT;
  }
}


function FixationRoutineEnd() {
  //------Ending Routine 'Fixation'-------
  for (const thisComponent of FixationComponents) {
    if (typeof thisComponent.setAutoDraw === 'function') {
      thisComponent.setAutoDraw(false);
    }
  }
  return Scheduler.Event.NEXT;
}

var trials;
var currentLoop;
function trialsLoopBegin(thisScheduler) {
  // set up handler to look after randomisation of conditions etc
  trials = new TrialHandler({
    psychoJS: psychoJS,
    nReps: 1, method: TrialHandler.Method.SEQUENTIAL,
    extraInfo: expInfo, originPath: undefined,
    trialList: 'N-back-1.xlsx',
    seed: undefined, name: 'trials'});
  psychoJS.experiment.addLoop(trials); // add the loop to the experiment
  currentLoop = trials;  // we're now the current loop

  // Schedule all the trials in the trialList:
  for (const thisTrial of trials) {
    thisScheduler.add(importConditions(trials));
    thisScheduler.add(N_back_1_TrialRoutineBegin);
    thisScheduler.add(N_back_1_TrialRoutineEachFrame);
    thisScheduler.add(N_back_1_TrialRoutineEnd);
    thisScheduler.add(endLoopIteration(thisScheduler, thisTrial));
  }

  return Scheduler.Event.NEXT;
}


function trialsLoopEnd() {
  psychoJS.experiment.removeLoop(trials);

  return Scheduler.Event.NEXT;
}

var trials_2;
function trials_2LoopBegin(thisScheduler) {
  // set up handler to look after randomisation of conditions etc
  trials_2 = new TrialHandler({
    psychoJS: psychoJS,
    nReps: 1, method: TrialHandler.Method.SEQUENTIAL,
    extraInfo: expInfo, originPath: undefined,
    trialList: 'N-back-2.xlsx',
    seed: undefined, name: 'trials_2'});
  psychoJS.experiment.addLoop(trials_2); // add the loop to the experiment
  currentLoop = trials_2;  // we're now the current loop

  // Schedule all the trials in the trialList:
  for (const thisTrial_2 of trials_2) {
    thisScheduler.add(importConditions(trials_2));
    thisScheduler.add(N_back_2_trialsRoutineBegin);
    thisScheduler.add(N_back_2_trialsRoutineEachFrame);
    thisScheduler.add(N_back_2_trialsRoutineEnd);
    thisScheduler.add(endLoopIteration(thisScheduler, thisTrial_2));
  }

  return Scheduler.Event.NEXT;
}


function trials_2LoopEnd() {
  psychoJS.experiment.removeLoop(trials_2);

  return Scheduler.Event.NEXT;
}

var response;
var N_back_1_TrialComponents;
function N_back_1_TrialRoutineBegin() {
  //------Prepare to start Routine 'N_back_1_Trial'-------
  t = 0;
  N_back_1_TrialClock.reset(); // clock
  frameN = -1;
  routineTimer.add(2.000000);
  // update component parameters for each repeat
  target_square.setPos(location);
  response = new core.BuilderKeyResponse(psychoJS);
  
  // keep track of which components have finished
  N_back_1_TrialComponents = [];
  N_back_1_TrialComponents.push(grid_lines);
  N_back_1_TrialComponents.push(target_square);
  N_back_1_TrialComponents.push(fixation_2);
  N_back_1_TrialComponents.push(response);
  
  for (const thisComponent of N_back_1_TrialComponents)
    if ('status' in thisComponent)
      thisComponent.status = PsychoJS.Status.NOT_STARTED;
  
  return Scheduler.Event.NEXT;
}


function N_back_1_TrialRoutineEachFrame() {
  //------Loop for each frame of Routine 'N_back_1_Trial'-------
  let continueRoutine = true; // until we're told otherwise
  // get current time
  t = N_back_1_TrialClock.getTime();
  frameN = frameN + 1;// number of completed frames (so 0 is the first frame)
  // update/draw components on each frame
  
  // *grid_lines* updates
  if (t >= 0 && grid_lines.status === PsychoJS.Status.NOT_STARTED) {
    // keep track of start time/frame for later
    grid_lines.tStart = t;  // (not accounting for frame time here)
    grid_lines.frameNStart = frameN;  // exact frame index
    grid_lines.setAutoDraw(true);
  }

  frameRemains = 0 + 2 - psychoJS.window.monitorFramePeriod * 0.75;  // most of one frame period left
  if (grid_lines.status === PsychoJS.Status.STARTED && t >= frameRemains) {
    grid_lines.setAutoDraw(false);
  }
  
  // *target_square* updates
  if (t >= 0 && target_square.status === PsychoJS.Status.NOT_STARTED) {
    // keep track of start time/frame for later
    target_square.tStart = t;  // (not accounting for frame time here)
    target_square.frameNStart = frameN;  // exact frame index
    target_square.setAutoDraw(true);
  }

  frameRemains = 0 + 1 - psychoJS.window.monitorFramePeriod * 0.75;  // most of one frame period left
  if (target_square.status === PsychoJS.Status.STARTED && t >= frameRemains) {
    target_square.setAutoDraw(false);
  }
  
  // *fixation_2* updates
  if (t >= 1 && fixation_2.status === PsychoJS.Status.NOT_STARTED) {
    // keep track of start time/frame for later
    fixation_2.tStart = t;  // (not accounting for frame time here)
    fixation_2.frameNStart = frameN;  // exact frame index
    fixation_2.setAutoDraw(true);
  }

  frameRemains = 1 + 1.0 - psychoJS.window.monitorFramePeriod * 0.75;  // most of one frame period left
  if (fixation_2.status === PsychoJS.Status.STARTED && t >= frameRemains) {
    fixation_2.setAutoDraw(false);
  }
  
  // *response* updates
  if (t >= 0.0 && response.status === PsychoJS.Status.NOT_STARTED) {
    // keep track of start time/frame for later
    response.tStart = t;  // (not accounting for frame time here)
    response.frameNStart = frameN;  // exact frame index
    response.status = PsychoJS.Status.STARTED;
    // keyboard checking is just starting
    psychoJS.window.callOnFlip(function() { response.clock.reset(); }); // t = 0 on screen flip
    psychoJS.eventManager.clearEvents({eventType:'keyboard'});
  }

  frameRemains = 0.0 + 2 - psychoJS.window.monitorFramePeriod * 0.75;  // most of one frame period left
  if (response.status === PsychoJS.Status.STARTED && t >= frameRemains) {
    response.status = PsychoJS.Status.FINISHED;
  }

  if (response.status === PsychoJS.Status.STARTED) {
    let theseKeys = psychoJS.eventManager.getKeys({keyList:['space']});
    
    // check for quit:
    if (theseKeys.indexOf('escape') > -1) {
      psychoJS.experiment.experimentEnded = true;
    }
    
    if (theseKeys.length > 0) {  // at least one key was pressed
      response.keys = theseKeys[theseKeys.length-1];  // just the last key pressed
      response.rt = response.clock.getTime();
      // was this 'correct'?
      if (response.keys == corrAns) {
          response.corr = 1;
      } else {
          response.corr = 0;
      }
    }
  }
  
  // check for quit (typically the Esc key)
  if (psychoJS.experiment.experimentEnded || psychoJS.eventManager.getKeys({keyList:['escape']}).length > 0) {
    return psychoJS.quit('The [Escape] key was pressed. Goodbye!', false);
  }
  
  // check if the Routine should terminate
  if (!continueRoutine) {  // a component has requested a forced-end of Routine
    return Scheduler.Event.NEXT;
  }
  
  continueRoutine = false;  // reverts to True if at least one component still running
  for (const thisComponent of N_back_1_TrialComponents)
    if ('status' in thisComponent && thisComponent.status !== PsychoJS.Status.FINISHED) {
      continueRoutine = true;
      break;
    }
  
  // refresh the screen if continuing
  if (continueRoutine && routineTimer.getTime() > 0) {
    return Scheduler.Event.FLIP_REPEAT;
  }
  else {
    return Scheduler.Event.NEXT;
  }
}


function N_back_1_TrialRoutineEnd() {
  //------Ending Routine 'N_back_1_Trial'-------
  for (const thisComponent of N_back_1_TrialComponents) {
    if (typeof thisComponent.setAutoDraw === 'function') {
      thisComponent.setAutoDraw(false);
    }
  }
  
  // check responses
  if (response.keys === undefined || response.keys.length === 0) {    // No response was made
      response.keys = undefined;
  }
  
  // was no response the correct answer?!
  if (response.keys === undefined) {
    if (['None','none',undefined].includes(corrAns)) {
       response.corr = 1  // correct non-response
    } else {
       response.corr = 0  // failed to respond (incorrectly)
    }
  }
  // store data for thisExp (ExperimentHandler)
  psychoJS.experiment.addData('response.keys', response.keys);
  psychoJS.experiment.addData('response.corr', response.corr);
  if (typeof response.keys !== 'undefined') {  // we had a response
      psychoJS.experiment.addData('response.rt', response.rt);
      }
  
  return Scheduler.Event.NEXT;
}

var key_resp_2;
var Instructions_2Components;
function Instructions_2RoutineBegin() {
  //------Prepare to start Routine 'Instructions_2'-------
  t = 0;
  Instructions_2Clock.reset(); // clock
  frameN = -1;
  // update component parameters for each repeat
  key_resp_2 = new core.BuilderKeyResponse(psychoJS);
  
  // keep track of which components have finished
  Instructions_2Components = [];
  Instructions_2Components.push(instructions_2);
  Instructions_2Components.push(key_resp_2);
  
  for (const thisComponent of Instructions_2Components)
    if ('status' in thisComponent)
      thisComponent.status = PsychoJS.Status.NOT_STARTED;
  
  return Scheduler.Event.NEXT;
}


function Instructions_2RoutineEachFrame() {
  //------Loop for each frame of Routine 'Instructions_2'-------
  let continueRoutine = true; // until we're told otherwise
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

  
  // *key_resp_2* updates
  if (t >= 0.0 && key_resp_2.status === PsychoJS.Status.NOT_STARTED) {
    // keep track of start time/frame for later
    key_resp_2.tStart = t;  // (not accounting for frame time here)
    key_resp_2.frameNStart = frameN;  // exact frame index
    key_resp_2.status = PsychoJS.Status.STARTED;
    // keyboard checking is just starting
    psychoJS.window.callOnFlip(function() { key_resp_2.clock.reset(); }); // t = 0 on screen flip
    psychoJS.eventManager.clearEvents({eventType:'keyboard'});
  }

  if (key_resp_2.status === PsychoJS.Status.STARTED) {
    let theseKeys = psychoJS.eventManager.getKeys({keyList:['space']});
    
    // check for quit:
    if (theseKeys.indexOf('escape') > -1) {
      psychoJS.experiment.experimentEnded = true;
    }
    
    if (theseKeys.length > 0) {  // at least one key was pressed
      key_resp_2.keys = theseKeys[theseKeys.length-1];  // just the last key pressed
      key_resp_2.rt = key_resp_2.clock.getTime();
      // a response ends the routine
      continueRoutine = false;
    }
  }
  
  // check for quit (typically the Esc key)
  if (psychoJS.experiment.experimentEnded || psychoJS.eventManager.getKeys({keyList:['escape']}).length > 0) {
    return psychoJS.quit('The [Escape] key was pressed. Goodbye!', false);
  }
  
  // check if the Routine should terminate
  if (!continueRoutine) {  // a component has requested a forced-end of Routine
    return Scheduler.Event.NEXT;
  }
  
  continueRoutine = false;  // reverts to True if at least one component still running
  for (const thisComponent of Instructions_2Components)
    if ('status' in thisComponent && thisComponent.status !== PsychoJS.Status.FINISHED) {
      continueRoutine = true;
      break;
    }
  
  // refresh the screen if continuing
  if (continueRoutine) {
    return Scheduler.Event.FLIP_REPEAT;
  }
  else {
    return Scheduler.Event.NEXT;
  }
}


function Instructions_2RoutineEnd() {
  //------Ending Routine 'Instructions_2'-------
  for (const thisComponent of Instructions_2Components) {
    if (typeof thisComponent.setAutoDraw === 'function') {
      thisComponent.setAutoDraw(false);
    }
  }
  
  // check responses
  if (key_resp_2.keys === undefined || key_resp_2.keys.length === 0) {    // No response was made
      key_resp_2.keys = undefined;
  }
  
  psychoJS.experiment.addData('key_resp_2.keys', key_resp_2.keys);
  if (typeof key_resp_2.keys !== 'undefined') {  // we had a response
      psychoJS.experiment.addData('key_resp_2.rt', key_resp_2.rt);
      routineTimer.reset();
      }
  
  // the Routine "Instructions_2" was not non-slip safe, so reset the non-slip timer
  routineTimer.reset();
  
  return Scheduler.Event.NEXT;
}

var response_2;
var N_back_2_trialsComponents;
function N_back_2_trialsRoutineBegin() {
  //------Prepare to start Routine 'N_back_2_trials'-------
  t = 0;
  N_back_2_trialsClock.reset(); // clock
  frameN = -1;
  routineTimer.add(2.000000);
  // update component parameters for each repeat
  target_square_2.setPos(location);
  response_2 = new core.BuilderKeyResponse(psychoJS);
  
  // keep track of which components have finished
  N_back_2_trialsComponents = [];
  N_back_2_trialsComponents.push(grid_lines_2);
  N_back_2_trialsComponents.push(target_square_2);
  N_back_2_trialsComponents.push(fixation_3);
  N_back_2_trialsComponents.push(response_2);
  
  for (const thisComponent of N_back_2_trialsComponents)
    if ('status' in thisComponent)
      thisComponent.status = PsychoJS.Status.NOT_STARTED;
  
  return Scheduler.Event.NEXT;
}


function N_back_2_trialsRoutineEachFrame() {
  //------Loop for each frame of Routine 'N_back_2_trials'-------
  let continueRoutine = true; // until we're told otherwise
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

  frameRemains = 0.0 + 2 - psychoJS.window.monitorFramePeriod * 0.75;  // most of one frame period left
  if (grid_lines_2.status === PsychoJS.Status.STARTED && t >= frameRemains) {
    grid_lines_2.setAutoDraw(false);
  }
  
  // *target_square_2* updates
  if (t >= 0 && target_square_2.status === PsychoJS.Status.NOT_STARTED) {
    // keep track of start time/frame for later
    target_square_2.tStart = t;  // (not accounting for frame time here)
    target_square_2.frameNStart = frameN;  // exact frame index
    target_square_2.setAutoDraw(true);
  }

  frameRemains = 0 + 1.0 - psychoJS.window.monitorFramePeriod * 0.75;  // most of one frame period left
  if (target_square_2.status === PsychoJS.Status.STARTED && t >= frameRemains) {
    target_square_2.setAutoDraw(false);
  }
  
  // *fixation_3* updates
  if (t >= 1 && fixation_3.status === PsychoJS.Status.NOT_STARTED) {
    // keep track of start time/frame for later
    fixation_3.tStart = t;  // (not accounting for frame time here)
    fixation_3.frameNStart = frameN;  // exact frame index
    fixation_3.setAutoDraw(true);
  }

  frameRemains = 1 + 1 - psychoJS.window.monitorFramePeriod * 0.75;  // most of one frame period left
  if (fixation_3.status === PsychoJS.Status.STARTED && t >= frameRemains) {
    fixation_3.setAutoDraw(false);
  }
  
  // *response_2* updates
  if (t >= 0.0 && response_2.status === PsychoJS.Status.NOT_STARTED) {
    // keep track of start time/frame for later
    response_2.tStart = t;  // (not accounting for frame time here)
    response_2.frameNStart = frameN;  // exact frame index
    response_2.status = PsychoJS.Status.STARTED;
    // keyboard checking is just starting
    psychoJS.window.callOnFlip(function() { response_2.clock.reset(); }); // t = 0 on screen flip
    psychoJS.eventManager.clearEvents({eventType:'keyboard'});
  }

  frameRemains = 0.0 + 2 - psychoJS.window.monitorFramePeriod * 0.75;  // most of one frame period left
  if (response_2.status === PsychoJS.Status.STARTED && t >= frameRemains) {
    response_2.status = PsychoJS.Status.FINISHED;
  }

  if (response_2.status === PsychoJS.Status.STARTED) {
    let theseKeys = psychoJS.eventManager.getKeys({keyList:['space']});
    
    // check for quit:
    if (theseKeys.indexOf('escape') > -1) {
      psychoJS.experiment.experimentEnded = true;
    }
    
    if (theseKeys.length > 0) {  // at least one key was pressed
      response_2.keys = theseKeys[theseKeys.length-1];  // just the last key pressed
      response_2.rt = response_2.clock.getTime();
      // was this 'correct'?
      if (response_2.keys == corrAns) {
          response_2.corr = 1;
      } else {
          response_2.corr = 0;
      }
    }
  }
  
  // check for quit (typically the Esc key)
  if (psychoJS.experiment.experimentEnded || psychoJS.eventManager.getKeys({keyList:['escape']}).length > 0) {
    return psychoJS.quit('The [Escape] key was pressed. Goodbye!', false);
  }
  
  // check if the Routine should terminate
  if (!continueRoutine) {  // a component has requested a forced-end of Routine
    return Scheduler.Event.NEXT;
  }
  
  continueRoutine = false;  // reverts to True if at least one component still running
  for (const thisComponent of N_back_2_trialsComponents)
    if ('status' in thisComponent && thisComponent.status !== PsychoJS.Status.FINISHED) {
      continueRoutine = true;
      break;
    }
  
  // refresh the screen if continuing
  if (continueRoutine && routineTimer.getTime() > 0) {
    return Scheduler.Event.FLIP_REPEAT;
  }
  else {
    return Scheduler.Event.NEXT;
  }
}


function N_back_2_trialsRoutineEnd() {
  //------Ending Routine 'N_back_2_trials'-------
  for (const thisComponent of N_back_2_trialsComponents) {
    if (typeof thisComponent.setAutoDraw === 'function') {
      thisComponent.setAutoDraw(false);
    }
  }
  
  // check responses
  if (response_2.keys === undefined || response_2.keys.length === 0) {    // No response was made
      response_2.keys = undefined;
  }
  
  // was no response the correct answer?!
  if (response_2.keys === undefined) {
    if (['None','none',undefined].includes(corrAns)) {
       response_2.corr = 1  // correct non-response
    } else {
       response_2.corr = 0  // failed to respond (incorrectly)
    }
  }
  // store data for thisExp (ExperimentHandler)
  psychoJS.experiment.addData('response_2.keys', response_2.keys);
  psychoJS.experiment.addData('response_2.corr', response_2.corr);
  if (typeof response_2.keys !== 'undefined') {  // we had a response
      psychoJS.experiment.addData('response_2.rt', response_2.rt);
      }
  
  return Scheduler.Event.NEXT;
}

var EndComponents;
function EndRoutineBegin() {
  //------Prepare to start Routine 'End'-------
  t = 0;
  EndClock.reset(); // clock
  frameN = -1;
  routineTimer.add(3.000000);
  // update component parameters for each repeat
  // keep track of which components have finished
  EndComponents = [];
  EndComponents.push(thank_you);
  
  for (const thisComponent of EndComponents)
    if ('status' in thisComponent)
      thisComponent.status = PsychoJS.Status.NOT_STARTED;
  
  return Scheduler.Event.NEXT;
}


function EndRoutineEachFrame() {
  //------Loop for each frame of Routine 'End'-------
  let continueRoutine = true; // until we're told otherwise
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

  frameRemains = 0.0 + 3 - psychoJS.window.monitorFramePeriod * 0.75;  // most of one frame period left
  if (thank_you.status === PsychoJS.Status.STARTED && t >= frameRemains) {
    thank_you.setAutoDraw(false);
  }
  // check for quit (typically the Esc key)
  if (psychoJS.experiment.experimentEnded || psychoJS.eventManager.getKeys({keyList:['escape']}).length > 0) {
    return psychoJS.quit('The [Escape] key was pressed. Goodbye!', false);
  }
  
  // check if the Routine should terminate
  if (!continueRoutine) {  // a component has requested a forced-end of Routine
    return Scheduler.Event.NEXT;
  }
  
  continueRoutine = false;  // reverts to True if at least one component still running
  for (const thisComponent of EndComponents)
    if ('status' in thisComponent && thisComponent.status !== PsychoJS.Status.FINISHED) {
      continueRoutine = true;
      break;
    }
  
  // refresh the screen if continuing
  if (continueRoutine && routineTimer.getTime() > 0) {
    return Scheduler.Event.FLIP_REPEAT;
  }
  else {
    return Scheduler.Event.NEXT;
  }
}


function EndRoutineEnd() {
  //------Ending Routine 'End'-------
  for (const thisComponent of EndComponents) {
    if (typeof thisComponent.setAutoDraw === 'function') {
      thisComponent.setAutoDraw(false);
    }
  }
  return Scheduler.Event.NEXT;
}


function endLoopIteration(thisScheduler, thisTrial) {
  // ------Prepare for next entry------
  return function () {
    // ------Check if user ended loop early------
    if (currentLoop.finished) {
      thisScheduler.stop();
    } else if (typeof thisTrial === 'undefined' || !('isTrials' in thisTrial) || thisTrial.isTrials) {
      psychoJS.experiment.nextEntry();
    }
  return Scheduler.Event.NEXT;
  };
}


function importConditions(loop) {
  const trialIndex = loop.getTrialIndex();
  return function () {
    loop.setTrialIndex(trialIndex);
    psychoJS.importAttributes(loop.getCurrentTrial());
    return Scheduler.Event.NEXT;
    };
}


function quitPsychoJS(message, isCompleted) {
  psychoJS.window.close();
  psychoJS.quit({message: message, isCompleted: isCompleted});

  return Scheduler.Event.QUIT;
}
