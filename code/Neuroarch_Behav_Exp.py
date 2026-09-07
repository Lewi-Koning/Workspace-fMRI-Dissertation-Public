from psychopy import core, visual, event, gui, logging
import pandas as pd
import os
import random
from datetime import datetime

os.chdir("C:/Users/LewiK/OneDrive/Desktop/Neuroarchitecture-fMRI-Dissertation")
print(os.getcwd())

logging.console.setLevel(logging.ERROR)


exp_info = {'Participant Number':''} 
form = gui.DlgFromDict(exp_info,title='Intro form')
if not form.OK:
    core.quit()

results_path = (f"./results/Behavioural_Results/Sub{exp_info['Participant Number']}_Behavioural.csv")

win = visual.Window(monitor="HP-Pavilion", units="height", fullscr = True)

VIDEOLIST = os.listdir('../260707_fixedVids/')

if not VIDEOLIST:
    print("No videos were found")
    
MOVIELIST = []
for ii, filename in enumerate(VIDEOLIST):
    print(f"loading video {ii+1}/{len(VIDEOLIST)}: {filename}")
    if filename.endswith('.mp4'):
        filepath = '../260707_fixedVids/' + filename
        MOVIELIST.append(visual.MovieStim(win, 
                             filename=filepath, 
                             units='height', 
                             size=(1.2,0.6625),
                             pos=(0,0.1),
                             noAudio=True))

if not MOVIELIST:
    print("No movies were made")

random.shuffle(MOVIELIST)

# Intro display
introText = visual.TextStim(win, text="""Welcome to this experiment!

You will be shown a series of videos of work spaces with a slider

Task: You must select a slider option according to the emotion that workspace makes you feel

There will be three emotions for each video

Press space after choosing an option to continue

[Press space to continue]""", font="Arial", height=0.05)
introText.draw()
win.flip()
event.waitKeys(keyList=['space'])

# Define sliders, images and text
pleasureSli = visual.Slider(win, ticks=(1,2,3,4,5,6,7,8,9),pos=(0,-0.35), labels=[1,2,3,4,5,6,7,8,9], size=[1,0.03], font="Arial", granularity=1)
pleasureIMGleft = visual.ImageStim(win, image="code/Behavioural_Exp_Components/Self-Assessment-Manikin-pleasure1.jpg",anchor='center',pos=[-0.65,-0.35],size=[0.17,0.17],mask=None,interpolate=True)
pleasureIMGright = visual.ImageStim(win, image="code/Behavioural_Exp_Components/Self-Assessment-Manikin-pleasure2.jpg",anchor='center',pos=[0.65,-0.35],size=[0.17,0.17],mask=None,interpolate=True)
pleasureTEXT = visual.TextStim(win, text="Valence - how pleasant or unpleasant the workspace makes you feel", height=0.03, pos=(0,-0.29))

arousalSli = visual.Slider(win, ticks=(1,2,3,4,5,6,7,8,9),pos=(0,-0.35), labels=[1,2,3,4,5,6,7,8,9], size=[1,0.03], font="Arial", granularity=1)
arousalIMGleft = visual.ImageStim(win, image="code/Behavioural_Exp_Components/Self-Assessment-Manikin-arousal1.jpg",anchor='center',pos=[-0.65,-0.35],size=[0.17,0.17],mask=None,interpolate=True)
arousalIMGright = visual.ImageStim(win, image="code/Behavioural_Exp_Components/Self-Assessment-Manikin-arousal2.jpg",anchor='center',pos=[0.65,-0.35],size=[0.17,0.17],mask=None,interpolate=True)
arousalTEXT = visual.TextStim(win, text="Arousal - how excited or relaxed the workspace makes you feel", height=0.03, pos=(0,-0.29))


dominanceSli = visual.Slider(win, ticks=(1,2,3,4,5,6,7,8,9),pos=(0,-0.35), labels=[1,2,3,4,5,6,7,8,9], size=[1,0.03], font="Arial", granularity=1)
dominanceIMGleft = visual.ImageStim(win, image="code/Behavioural_Exp_Components/Self-Assessment-Manikin-dominance1.jpg",anchor='center',pos=[-0.65,-0.35],size=[0.17,0.17],mask=None,interpolate=True)
dominanceIMGright = visual.ImageStim(win, image="code/Behavioural_Exp_Components/Self-Assessment-Manikin-dominance2.jpg",anchor='center',pos=[0.65,-0.35],size=[0.17,0.17],mask=None,interpolate=True)
dominanceTEXT = visual.TextStim(win, text="Dominance - How in control or out of control the workspace makes you feel", height=0.03, pos=(0,-0.29))


contText = visual.TextStim(win, text="[Press space to continue]", pos=[0,-0.42], font="Arial", height=0.03)

def display_slid(Emotion):
    contText.draw()
    if Emotion == "pleasure":
        sli = pleasureSli
        pleasureSli.draw()
        pleasureIMGleft.draw()
        pleasureIMGright.draw()
        pleasureTEXT.draw()
    elif Emotion == "arousal":
        sli = arousalSli
        arousalSli.draw()
        arousalIMGleft.draw()
        arousalIMGright.draw()
        arousalTEXT.draw()
    elif Emotion == "dominance":
        sli = dominanceSli
        dominanceSli.draw()
        dominanceIMGleft.draw()
        dominanceIMGright.draw()
        dominanceTEXT.draw()
    return sli
    
def save_result_row(row_dict):
    df = pd.DataFrame([row_dict])
    df.to_csv(
        results_path,
        mode="a",
        header=not os.path.exists(results_path),
        index=False
    )
    
def display(trial, emotion):
    
    movieStim = MOVIELIST[trial]
    movieFN = os.path.basename(movieStim.filename)
    
    movieStim.seek(0) # resets video back to 0
    movieStim.play() 

    while True:
        movieStim.draw()
        Sli = display_slid(emotion)
        win.flip()
        k = event.getKeys(keyList=['space', 'escape'])
        if 'escape' in k:
            movieStim.stop()
            win.close()
            core.quit()
        elif Sli.getRating() is not None and 'space' in k:
            movieStim.stop()
            rating = Sli.getRating()
            save_result_row({
                "participant_id": exp_info['Participant Number'],
                "manikin": emotion,
                "score": rating,
                "stimulus": movieFN,
                "date": datetime.now().isoformat()
            })
            Sli.reset()
            break
    
for ii, movie in enumerate(MOVIELIST):
    display(ii,"pleasure")
    display(ii,"arousal")
    display(ii,"dominance")
    
win.close()
core.quit()
