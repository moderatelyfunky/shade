import tkinter as tk
import time
#jge - build middle layer to load controller or not
#jge - depending on the gotPi value in the ini. 
import middle
mid = middle.Middle()

class ButtonWrapper(tk.Button):
    #jge - for additional button properties
    def __init__(self, btnType, presetNo, *args, **kwargs):
        self.type = btnType
        self.presetNo = presetNo
        tk.Button.__init__(self, *args, **kwargs)
   
class ButtonTimer:
    timerOn = False
    timerCount = 0.0

    def __init__(self, timerOn, timerCount):
        self.timerOn = timerOn
        self.timerCount = timerCount

def drawGreenPreset(event) :
    event.widget.configure(image=smallButtonGlow)
  
def drawNormalPreset(event) :
    event.widget.configure(image=smallButtonGlow)
    app.after(500, drawGreenPreset(event))

def timingStart(event, t: ButtonTimer):
    theType = str(event.widget.type)

    if theType  == "preset":
        event.widget.configure(image=smallButtonGlow)
        
        if t.timerOn == False:
            # if the timer is off, start it and get the current time
            t.timerOn = True
            t.timerCount = time.time()

def timingStop(event, t: ButtonTimer, presetNo):
    theType = str(event.widget.type)
    
    if theType  == "preset":
        event.widget.configure(image=smallRoundButton)
        if t.timerOn == True:
            # if the timer is on, stop it and get the count
            t.timerOn = False
            t.timerCount = time.time() - t.timerCount

            #jge - save the preset if they held it down
            if (t.timerCount > 2):
                app.after(500, drawNormalPreset(event))
                mid.writePreset(event, presetNo)
                #jge - flash to indicate successful save
            else:
                mid.gotoPreset(event, presetNo)         

class Rect:
    # (start_x, start_y) --> upper left corner
    # (end_x, end_y) --> lower right corner
    # the id is so we can easily delete from the canvas
    start_x = 0
    start_y = 0
    end_x = 0
    end_y = 0
    id = 0

    def __init__(self, start_x, start_y, end_x, end_y, id):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.id = id

def getStartCoords(event, r1):
    # figure out where the user has clicked on the canvas
    # store that point in the rect object
    # and then delete the previous rectangle
    # canvasDraw.option_clear()
    r1.start_x = event.x
    r1.start_y = event.y
    canvasDraw.delete(r1.id)

def getEndCoords(event, r1):
    # when the user releases the mouse, get the coords there
    # and store them as the end point in the rect object
    # Then draw a rectangle spanning the start to end pts
    # and store the id of the new rectangle in the rect object
    r1.end_x = event.x
    r1.end_y = event.y
    i = canvasDraw.create_rectangle(r1.start_x, r1.start_y, r1.end_x, r1.end_y, fill="black")
    r1.id = i

r1 = Rect(0, 0, 0, 0, 0)
timer1 = ButtonTimer(False, 0.0)

app = tk.Tk()
app.geometry("800x480")
#app.wm_attributes('-type', 'dock')
app.title('Slim Shady')
app.option_add("Button.Background", "black")
app.option_add("Button.Foreground", "white")
app.resizable(0, 0)
#app.configure(background='white')

arrowLeft=tk.PhotoImage(file="images/arrow-left.gif")
arrowRight=tk.PhotoImage(file="images/arrow-right.gif")
arrowUp=tk.PhotoImage(file="images/arrow-up.gif")
arrowDown=tk.PhotoImage(file="images/arrow-down.gif")
roundButton = tk.PhotoImage(file="images/big-button-off.gif")
roundButtonGlow = tk.PhotoImage(file="images/big-button-on.gif")
smallRoundButton = tk.PhotoImage(file="images/small-button-off.gif")
smallButtonGlow = tk.PhotoImage(file="images/small-button-on.gif")

canvasDraw = tk.Canvas(app, width=195, height=419, borderwidth=1)
canvasDraw.grid(row=1, column=1, rowspan=5, ipadx=3, ipady=3)
canvasDraw.bind('<ButtonPress-1>', lambda event: getStartCoords(event, r1))
canvasDraw.bind('<ButtonRelease-1>', lambda event: getEndCoords(event, r1))

########################
#jge - two button section
btnCircle1 = tk.Button(app, name="btnCircle1", image=roundButton, borderwidth=0)
btnCircle1.grid(row=1, column=3, rowspan=2, columnspan=2, ipadx=3, ipady=3)
btnCircle1.bind('<ButtonPress-1>', lambda event: mid.gotoPreset(event, 5))

btnCircle2 = tk.Button(app, name="btnCircle2", image=roundButton, borderwidth=0)
btnCircle2.grid(row=4, column=3, rowspan=2, columnspan=2, ipadx=3, ipady=3)
btnCircle2.bind('<ButtonPress-1>', lambda event: mid.gotoPreset(event, 6))
#jge - end two button
########################

########################
#jge - manual movers
btnTopShadeUp = tk.Button(app, name="btnTopShadeUp", image=arrowRight, borderwidth=0)
btnTopShadeUp.grid(row=3, column=7, ipadx=3, ipady=3)
btnTopShadeUp.bind('<ButtonRelease-1>', lambda event: mid.stop(event, 'top'))
btnTopShadeUp.bind('<ButtonPress-1>', lambda event: mid.move(event, 'top', 1))

btnTopShadeDown = tk.Button(app, name="btnTopShadeDown", image=arrowLeft, borderwidth=0)
btnTopShadeDown.grid(row=3, column=6, ipadx=3, ipady=3)
btnTopShadeDown.bind('<ButtonRelease-1>', lambda event: mid.stop(event, 'top'))
btnTopShadeDown.bind('<ButtonPress-1>', lambda event: mid.move(event, 'top', 0))

btnLeftShadeLeft = tk.Button(app, name="btnLeftShadeLeft", image=arrowUp, borderwidth=0)
btnLeftShadeLeft.grid(row=1, column=5, ipadx=3, ipady=3)
btnLeftShadeLeft.bind('<ButtonRelease-1>', lambda event: mid.stop(event, 'left'))
btnLeftShadeLeft.bind('<ButtonPress-1>', lambda event: mid.move(event, 'left', 1))

btnLeftShadeRight = tk.Button(app, name="btnLeftShadeRight", image=arrowDown, borderwidth=0)
btnLeftShadeRight.grid(row=2, column=5, ipadx=3, ipady=3)
btnLeftShadeRight.bind('<ButtonRelease-1>', lambda event: mid.stop(event, 'left'))
btnLeftShadeRight.bind('<ButtonPress-1>', lambda event: mid.move(event, 'left', 0))

btnRightShadeLeft = tk.Button(app, name="btnRightShadLeft", image=arrowUp, borderwidth=0)
btnRightShadeLeft.grid(row=4, column=5, ipadx=3, ipady=3)
btnRightShadeLeft.bind('<ButtonRelease-1>', lambda event: mid.stop(event, 'right'))
btnRightShadeLeft.bind('<ButtonPress-1>', lambda event: mid.move(event, 'right', 0))

btnRightShadeRight = tk.Button(app, name="btnRightShadeRight", image=arrowDown, borderwidth=0)
btnRightShadeRight.grid(row=5, column=5, ipadx=3, ipady=3)
btnRightShadeRight.bind('<ButtonRelease-1>', lambda event: mid.stop(event, 'right'))
btnRightShadeRight.bind('<ButtonPress-1>', lambda event: mid.move(event, 'right', 1))

btnBottomShadeUp = tk.Button(app, name="btnBottomShadeUp", image=arrowRight, borderwidth=0)
btnBottomShadeUp.grid(row=3, column=4, ipadx=3, ipady=3)
btnBottomShadeUp.bind('<ButtonRelease-1>', lambda event: mid.stop(event, 'bot'))
btnBottomShadeUp.bind('<ButtonPress-1>', lambda event: mid.move(event, 'bot', 1))

btnBottomShadeDown = tk.Button(app, name="btnBottomShadeDown", image=arrowLeft, borderwidth=0)
btnBottomShadeDown.grid(row=3, column=3, ipadx=3, ipady=3)
btnBottomShadeDown.bind('<ButtonRelease-1>', lambda event: mid.stop(event, 'bot'))
btnBottomShadeDown.bind('<ButtonPress-1>', lambda event: mid.move(event, 'bot', 0))
#jge - end manual movers
########################

########################
#jge - preset section
btnSmallCircle1 = ButtonWrapper('preset', 1,  app, name="btnSmallCircle1", image=smallRoundButton, borderwidth=0)
btnSmallCircle1.grid(row=1, column=6, columnspan=2, ipadx=3, ipady=3)
btnSmallCircle1.bind('<ButtonPress-1>', lambda event: timingStart(event, timer1))
btnSmallCircle1.bind('<ButtonRelease-1>', lambda event: timingStop(event, timer1, 1))

btnSmallCircle2 = ButtonWrapper('preset', 2,  app, name="btnSmallCircle2", image=smallRoundButton, borderwidth=0)
btnSmallCircle2.grid(row=2, column=6, columnspan=2, ipadx=3, ipady=3)
btnSmallCircle2.bind('<ButtonPress-1>', lambda event: timingStart(event, timer1))
btnSmallCircle2.bind('<ButtonRelease-1>', lambda event: timingStop(event, timer1, 2))

btnSmallCircle3 = ButtonWrapper('preset', 3,app, name="btnSmallCircle3", image=smallRoundButton, borderwidth=0)
btnSmallCircle3.grid(row=4, column=6, columnspan=2, ipadx=3, ipady=3)
btnSmallCircle3.bind('<ButtonPress-1>', lambda event: timingStart(event, timer1))
btnSmallCircle3.bind('<ButtonRelease-1>', lambda event: timingStop(event, timer1, 3))

#btnSmallCircle4 = tk.Button(app, name="btnSmallCircle4", image=smallRoundButton, borderwidth=0)
btnSmallCircle4 = ButtonWrapper('preset', 4, app, name="btnSmallCircle4", image=smallRoundButton, borderwidth=0)
btnSmallCircle4.grid(row=5, column=6, columnspan=2, ipadx=3, ipady=3)
btnSmallCircle4.bind('<ButtonPress-1>', lambda event: timingStart(event, timer1))
btnSmallCircle4.bind('<ButtonRelease-1>', lambda event: timingStop(event, timer1, 4))
#jge - end preset
########################

app.grid_rowconfigure(0, weight=1)
app.grid_rowconfigure(6, weight=1)
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(8, weight=1)

app.mainloop()




