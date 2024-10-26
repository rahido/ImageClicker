
import tkinter as tk


from PIL import ImageGrab

from time import sleep
from threading import Thread, Event

from numpy import array as nparr

import cv2
# import numpy as np
import pyautogui

from configparser import ConfigParser

from os import path

# Skip button ref image (skip.png): 
# - Crop the image evenly. The image's center will be used as a click target

# LIBS ###################
# PIL for screen capture
# time for sleep() between screen grabs
# threading for running the detection check loop on a thread
# # The threading.Event -class has an internal thread-safe boolean flag that can be set to True or False. By default, the internal flag is False
# OpenCV for image reading and template matching (/ image detection)
# PyAutoGui for simulating a mouse click
# configparser for saving options to .ini file
# os.path for creating a default .ini file (in case it's missing)


# SAVE SCREEN GRAB IMAGE for debugging
# global saves
# saves = 0

CONFIG_PATH = "./config.ini"
def createDefaultConfig():
    config = ConfigParser()
    config['main'] = {'interval':1.0}
    # with open(path, 'w') --> create the .ini file using the default contents. Closes automatically
    with open(CONFIG_PATH, 'w') as configfile:
        config.write(configfile)
        
def getIntervalFromConfig():
    if not (path.isfile(CONFIG_PATH)):
        createDefaultConfig()
    config = ConfigParser()
    config.read(CONFIG_PATH)
    # get(section, key)
    value = config.get("main","interval")
    try:
        value = float(value)
    except:
        value = 1.0
        updateInfoWidget("Could not read interval from config! \nSet interval -value in options.")
    return value
    
def saveIntervalToConfig(new_value):
    config = ConfigParser()
    config.read(CONFIG_PATH)
    # set(section, key, value)
    config.set('main', 'interval', str(new_value))
    with open(CONFIG_PATH, 'w') as config_file:
        config.write(config_file)


def grabScreen():
    bounds = (0, 0,root.winfo_screenwidth(), root.winfo_screenheight())
    screenimage = ImageGrab.grab(bbox=bounds, include_layered_windows=True, all_screens=True)
    #screenimage = screenimage.convert('RGB')
    #img_as_arr = nparr(screenimage)

    # SAVE SCREEN GRAB IMAGE for debugging
    # global saves
    # n = "test_img" + str(saves) + ".png"
    # screenimage.save(n)
    # saves += 1

    # https://stackoverflow.com/questions/14134892/convert-image-from-pil-to-opencv-format
    # Convert RGB to BGR
    opencvImage = cv2.cvtColor(nparr(screenimage), cv2.COLOR_RGB2BGR)

    return opencvImage

def checkForImage():

    print("checkForImage")
    updateInfoWidget("checking For Image")
    img_target_path = "./Target.png"

    # Read images
    #src_img = cv2.imread(img_source_path, cv2.IMREAD_UNCHANGED)
    target_img = cv2.imread(img_target_path, cv2.IMREAD_UNCHANGED)

    src_img = grabScreen()

    # Result from method (TM_CCOEFF_NORMED)
    result = cv2.matchTemplate(src_img, target_img, cv2.TM_CCOEFF_NORMED)
    # --> result is an B&W image
    # cv2.imshow('Result', result)


    # Worst and Best match
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    print("max_loc:",max_loc, ", max_val",max_val)
    # >max_loc: (731,301) , max_val 0.99998927...
    if max_val > 0.8:
        appWindow.clicks += 1
        print("Looks like a hit. At loc:", max_loc)
        height, width, channels = target_img.shape
        target_x, target_y = max_loc[0] + int(0.5 * width), max_loc[1] + int(0.5 * height)
        
        print("--- Target center:", target_x, target_y)
        pyautogui.click(target_x, target_y)
        #print("--- Click simulated at target")
        updateInfoWidget("Click simulated at target")
    else:
        updateInfoWidget("No click. Looping..")

def toggleDetectionRunning():
    # Is running -> Stop
    if appWindow.thread_event.is_set():
        updateInfoWidget("Click looper stopped")
        appWindow.action_b.configure(text="Start")
        appWindow.options_b.configure(state="normal")
        appWindow.thread_event.clear()
    else:
        updateInfoWidget("Click looper started")
        appWindow.action_b.configure(text="Stop")
        appWindow.options_b.configure(state="disabled")
        appWindow.thread_event.set()
        appWindow.thread = Thread(target=threadedCheck)
        appWindow.thread.start()


def threadedCheck():
    # Wait before starting
    sleep(appWindow.interval)
    # Run detection checks by interval
    while appWindow.thread_event.is_set():
        checkForImage()
        sleep(appWindow.interval)

def updateInfoWidget(t):
    new_t = t + "\n\n Total clicks:",appWindow.clicks
    appWindow.info_t.configure(text=new_t)

class AppWindow():
    master = None
    info_te = None
    action_b = None
    interval = 1.0
    clicks = 0
    thread = None
    thread_event = None
    options = None
    def __init__(self, master):
        self.master = master
        self.thread_event = Event()

        master.wm_title(string="Image Clicker")
        master.minsize(200,100)
        master.geometry("300x150")
        master.update()

        canvas = tk.Canvas(master)
        canvas.pack(fill='x')

        self.action_b = tk.Button(canvas,text="Start",command=toggleDetectionRunning)
        self.action_b.pack()
        
        self.options_b = tk.Button(canvas,text="Options",command=toggleOptions)
        self.options_b.pack()
        
        self.info_t = tk.Label(canvas, text="Yo. This app looks for image (to Target.png) on screen\nand clicks it if it's found on screen")
        self.info_t.pack(fill='x')

    def setDefaults(self):
        self.interval = getIntervalFromConfig()

def toggleOptions():
    # Show Options
    if appWindow.options == None:
        appWindow.options = Options(appWindow.master)
    # Close Options
    else:
        appWindow.options.canvas.place_forget()
        appWindow.options = None

class Options():
    canvas = None
    opt_info_t = None
    interval_var = None
    config_path = "./config.ini"
    def __init__(self,master):
        self.interval_var = tk.StringVar()

        canvas = tk.Canvas(master,background="white")
        canvas.place(x=0,y=0,relwidth=1,relheight=1)
        self.canvas = canvas

        label = tk.Label(canvas, text="OPTIONS",font=("Arial",24))
        label.pack()

        # INTERVAL #
        row1 = tk.Frame(canvas)
        row1.pack(fill='x',pady=10)

        interval_label = tk.Label(row1,text="Check Interval")
        interval_label.pack(side='left',fill='x',expand=True)

        interval_entry = tk.Entry(row1,textvariable=self.interval_var)
        interval_entry.pack(side='left',fill='x',expand=True)

        # Get saved interval
        interval_val = getIntervalFromConfig()
        self.interval_var.set(str(interval_val))

        interval_label2 = tk.Label(row1,text="seconds")
        interval_label2.pack(side='left',fill='x',expand=True)

        # RETURN #
        row2 = tk.Frame(canvas)
        row2.pack(fill='x',pady=10,expand=True)

        b_accept = tk.Button(row2,text="Accept",command=self.accept)
        b_accept.pack(side='left',padx=20,fill='x',expand=True)

        b_cancel = tk.Button(row2,text="Cancel",command=self.cancel)
        b_cancel.pack(side='left',padx=20,fill='x',expand=True)

        opt_info_t = tk.Label(canvas,text="",foreground="red")
        opt_info_t.pack()
        self.opt_info_t = opt_info_t
    
    def accept(self):
        str_val = self.interval_var.get()
        float_val = 0.0
        err_msg = ""
        try:
            float_val = float(str_val)
        except:
            err_msg = "Invalid interval number"
        if err_msg != "" and "," in str_val:
            err_msg = err_msg + " ( , for . )"

        # Success. Set new value, close options.
        if err_msg == "":
            self.opt_info_t.configure(text="")
            appWindow.interval = float_val
            updateInfoWidget("Interval updated!")
            saveIntervalToConfig(float_val)
            toggleOptions()
        # Error. Show message, keep options open.
        else:
            self.opt_info_t.configure(text=err_msg)

    def cancel(self):
        self.opt_info_t.configure(text="")
        toggleOptions()

root = tk.Tk()

# global 
appWindow = AppWindow(root)
appWindow.setDefaults()

root.mainloop()

