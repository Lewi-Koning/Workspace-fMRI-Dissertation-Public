#!/usr/bin/env python

from tracemalloc import start
from psychopy import core, visual, event, gui
import pandas as pd
import os
import random
import csv
import compatibility # macpro stuff...
from sys import platform
from psychopy import logging
from datetime import datetime

today = compatibility.getTimeStr() 
#date.today().isoformat()

logging.console.setLevel(logging.ERROR)

# and some site-specific parameters
params = compatibility.setDefaultParams()
parser = compatibility.setupParser('neuroarchitecture fMRI experiment')
parser.add_argument('-sn', '--screen_number', default=0, type=int, help='Screen number')
# make this a parameter you can pass in
parser.add_argument('-wt', '--wall-time', default=240.0, type=float,
                        help='Wallt ime for experiment (seconds) -- stop experiment after this time, even if not all trials are done')
parser.add_argument('--observer', default='sub01', type=str,
                    help='Observer code')
# TODO - TR should be a parameter... assuming 1.5s for now is ok

# specific help for this program
parser.epilog = './Neuroarch_MRI_Exp.py -sn 1'

# get the arguments out of this parser
args = parser.parse_args().__dict__.copy()

# reconcile default params and passed in / GUI specced arguments:
params = compatibility.reconcileParamsAndArgs(params, args)
params['debug'] = False

# hook for stimulus videos files 
# on lewi's pc this is a path, but on macos we dont' need to
if platform == "win32":
    os.chdir("C:/Users/LewiK/OneDrive/Desktop/MRI_Dissertation/Neuroarchitecture-fMRI-Dissertation")
    print(f"changed dir to {os.getcwd()}")
    win = visual.Window(monitor="AsusMonitor",units="cm", fullscr = True)

else:
    print(f"current dir is {os.getcwd()} - which from where code ie being run (macos)")
    win = compatibility.createWindow(units='deg', params=params)  # use defaults


win.mouseVisible = False

# setting up timers for the experiment
Timer = core.Clock()
fixTimer = core.Clock()
TotalTime = core.Clock()

fixCol = ['magenta','red','yellow','green','cyan','blue']
fixation = visual.ShapeStim(win, 
    vertices=((0, -0.5), (0, 0.5), (0,0), (-0.5,0), (0.5, 0)),
    lineWidth=8,
    closeShape=False,
    lineColor=random.choice(fixCol)
    )

def activeFix():
    if fixTimer.getTime() >= 0.6:
        fixation.lineColor = random.choice(fixCol)
        fixTimer.reset()

    fixation.draw()
    k = event.getKeys(keyList=['6'])
    if k:
        print(f"key pressed: {k}")
        print(f"fixation color: {fixation.lineColor}")
    # if fixation.lineColor[0] == 1 and fixation.lineColor[1] == -1 and fixation.lineColor[2] == -1 and '6' in k:
    #     print("red")
    # elif 'r' in k:
    #     print('wrong')



# preload a bunch of videos to avoid lag / stutter
videoList = os.listdir('../260707_fixedVids/')

print(videoList)

# at this point, before experiment starts,
# load all videos and create a movieStim for each
t0 = core.getTime()
movieStimList = []
for ii, filename in enumerate(videoList):
    print(f"loading video {ii+1}/{len(videoList)}: {filename}")
    if filename.endswith('.mp4'):
        filepath = '../260707_fixedVids/' + filename
        movieStimList.append(visual.MovieStim(win, 
                             filename=filepath, 
                             units='height', 
                             size=(2,1.125),
                             noAudio=True))
t1 = core.getTime() - t0

print(f"loaded {len(videoList)} videos = hopefully succesully.")
print(f"Time taken to load videos: {t1:.2f} seconds")

# this is the trigger code
# TODO - fix up a bit ? function?
tr = None
while tr is None:
    tr = compatibility.checkForKeyTriggerOrQuit(win,params = params)

print(f"trigger: {tr:.2f}")


##  things to sort out... for LK to have a look at:
# [1] make a function that takes one movieStim (from the list) and plays it for 3s
# ... the input should be the movieStim object, and the output should be the time it was shown (for logging)
#
# [2] make a function that takes the numbers 1...30 and permutes them (random )
# something like this>?? np.random.permutation(30)  # returns a random permutation of numbers 0-29
#
# [3] a function for ITI... also picking from a list of 3, 4, 5* TR (1.5s) ---
#
# [4]from here: display loop... each time through loop: 1 stim and 1 ITI... 
#
# [5]...then write out which stimulus was shown timestampes add to dataframe or list and then save out at end
#
# [6]LOOP condition.. stop exp if time > 240s
#
# [7]reconsider what to do about recording colour changes
# ?? moviestim hogs processing... button presses don't get picked up very well..

# via help from google / AI
event.clearEvents()  # Clear any existing events

### [3] ###
def InterTrial():
    Timer.reset()
    ITI = random.choice([4.5,6,7.5,9])
    while Timer.getTime() < ITI:
        activeFix()
        win.flip()
        compatibility.checkForKeyTriggerOrQuit(win)
        # check if experiment should end during ITI
        checkTime()
    return ITI

### [1] ###
def TrialRep(trialnum):    
    # movieStimList is global, but we have access to it here
    movieStim = movieStimList[trialnum]
    movieFN = os.path.basename(movieStim.filename)
    print(f"playing video {trialnum+1}/{len(movieStimList)}: {movieStim.filename}")
    
    movieStim.seek(0) # resets video back to 0
    movieStim.play()    
    
    startTime = TotalTime.getTime()
    while TotalTime.getTime() - startTime < 3.0:  # Ensures it plays for at least 3 seconds
        movieStim.draw()
        activeFix() 
        win.flip()
        compatibility.checkForKeyTriggerOrQuit(win)
        checkTime()
    movieStim.stop()
    return movieFN, startTime

# 
results_path = f"../data/{today}Neuroarch_Exp_Results.csv"
print(f"saving data to: {results_path}")

def save_result_row(row_dict):
    df = pd.DataFrame([row_dict])
    df.to_csv(
        results_path,
        mode="a",
        header=not os.path.exists(results_path),
        index=False
    )
    
def checkTime():
    if TotalTime.getTime() >= params['wall_time']:
        print(f"Neuroarchitecture, took {TotalTime.getTime()}")
        win.close()
        core.quit()


TotalTime.reset()

### [2] ###
random.shuffle(movieStimList)

### [4] ###
for ii, movieStim in enumerate(movieStimList):    
    movieFN, startTime = TrialRep(ii)
    Inter = InterTrial()
    ### [5] ###
    save_result_row({
        "participant_id": params['observer'],
        "stimulus": movieFN,
        "time_shown": startTime,
        "ITI": Inter,
        "Date": datetime.now().isoformat()
    })

print(f"Neuroarchitecture, took {TotalTime.getTime()}")

win.close()
core.quit()