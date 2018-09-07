import tkinter as tk
import time

import controller_light as con
gUnit = con.Unit()

class ButtonTimer:
    timerOn = False
    timerCount = 0.0

    def __init__(self, timerOn, timerCount):
        self.timerOn = timerOn
        self.timerCount = timerCount

def doSomethingElse(event):
    print(event.widget)

def timingStart(event, t: ButtonTimer):
    if str(event.widget) == ".btnSmallCircle4":
        print("Small Button Pressed")
        btnSmallCircle4.configure(image=smallButtonGlow)
        #jge - add sleep interrupt?
        #time.sleep(0.1)
        
        if t.timerOn == False:
            # if the timer is off, start it and get the current time
            t.timerOn = True
            t.timerCount = time.time()

def timingStop(event, t: ButtonTimer, presetNo):
    if str(event.widget) == ".btnSmallCircle4":
        print("Small Button Released")
        btnSmallCircle4.configure(image=smallRoundButton)
        if t.timerOn == True:
            # if the timer is on, stop it and get the count
            t.timerOn = False
            t.timerCount = time.time() - t.timerCount
            print(str(t.timerCount))
            #jge - save the preset if they are holding down
            if (t.timerCount > 4):
                gUnit.writePreset(event, presetNo)
                #jge - flash to indicate successful save
                btnSmallCircle4.configure(image=smallRoundButton)
                btnSmallCircle4.configure(image=smallButtonGlow)                
                btnSmallCircle4.configure(image=smallRoundButton)
                btnSmallCircle4.configure(image=smallButtonGlow)                
                btnSmallCircle4.configure(image=smallRoundButton)                  
            else:
                #jge - go to the preset
                gUnit.gotoPreset(event, presetNo)
          
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
    # print(str(r1.start_x) + " " + str(r1.start_y))
    canvasDraw.delete(r1.id)

def getEndCoords(event, r1):
    # when the user releases the mouse, get the coords there
    # and store them as the end point in the rect object
    # Then draw a rectangle spanning the start to end pts
    # and store the id of the new rectangle in the rect object
    r1.end_x = event.x
    r1.end_y = event.y
    # print(str(r1.end_x) + " " + str(r1.end_y))
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
#btnCircle1.bind('<ButtonRelease-1>', doSomethingElse)
btnCircle1.bind('<ButtonPress-1>', lambda event: gUnit.gotoPreset(event, 5))

btnCircle2 = tk.Button(app, name="btnCircle2", image=roundButton, borderwidth=0)
btnCircle2.grid(row=4, column=3, rowspan=2, columnspan=2, ipadx=3, ipady=3)
#btnCircle2.bind('<ButtonRelease-1>', doSomethingElse)
btnCircle2.bind('<ButtonPress-1>', lambda event: gUnit.gotoPreset(event, 6))
#jge - end two button
########################

########################
#jge - manual movers
btnTopShadeUp = tk.Button(app, name="btnTopShadeUp", image=arrowRight, borderwidth=0)
btnTopShadeUp.grid(row=3, column=7, ipadx=3, ipady=3)
btnTopShadeUp.bind('<ButtonRelease-1>', lambda event: gUnit.topShade.motor.stop(event))
btnTopShadeUp.bind('<ButtonPress-1>', lambda event: gUnit.topShade.motor.move(event, 1))

btnTopShadeDown = tk.Button(app, name="btnTopShadeDown", image=arrowLeft, borderwidth=0)
btnTopShadeDown.grid(row=3, column=6, ipadx=3, ipady=3)
btnTopShadeDown.bind('<ButtonRelease-1>', lambda event: gUnit.topShade.motor.stop(event))
btnTopShadeDown.bind('<ButtonPress-1>', lambda event: gUnit.topShade.motor.move(event, 0))

btnLeftShadeLeft = tk.Button(app, name="btnLeftShadeLeft", image=arrowUp, borderwidth=0)
btnLeftShadeLeft.grid(row=1, column=5, ipadx=3, ipady=3)
btnLeftShadeLeft.bind('<ButtonRelease-1>', lambda event: gUnit.leftShade.motor.stop(event))
btnLeftShadeLeft.bind('<ButtonPress-1>', lambda event: gUnit.leftShade.motor.move(event, 1))

btnLeftShadeRight = tk.Button(app, name="btnLeftShadeRight", image=arrowDown, borderwidth=0)
btnLeftShadeRight.grid(row=2, column=5, ipadx=3, ipady=3)
btnLeftShadeRight.bind('<ButtonRelease-1>', lambda event: gUnit.leftShade.motor.stop(event))
btnLeftShadeRight.bind('<ButtonPress-1>', lambda event: gUnit.leftShade.motor.move(event, 0))

btnRightShadeLeft = tk.Button(app, name="btnRightShadLeft", image=arrowUp, borderwidth=0)
btnRightShadeLeft.grid(row=4, column=5, ipadx=3, ipady=3)
btnRightShadeLeft.bind('<ButtonRelease-1>', lambda event: gUnit.rightShade.motor.stop(event))
btnRightShadeLeft.bind('<ButtonPress-1>', lambda event: gUnit.rightShade.motor.move(event, 0))

btnRightShadeRight = tk.Button(app, name="btnRightShadeRight", image=arrowDown, borderwidth=0)
btnRightShadeRight.grid(row=5, column=5, ipadx=3, ipady=3)
btnRightShadeRight.bind('<ButtonRelease-1>', lambda event: gUnit.rightShade.motor.stop(event))
btnRightShadeRight.bind('<ButtonPress-1>', lambda event: gUnit.rightShade.motor.move(event, 1))

btnBottomShadeUp = tk.Button(app, name="btnBottomShadeUp", image=arrowRight, borderwidth=0)
btnBottomShadeUp.grid(row=3, column=4, ipadx=3, ipady=3)
btnBottomShadeUp.bind('<ButtonRelease-1>', lambda event: gUnit.botShade.motor.stop(event))
btnBottomShadeUp.bind('<ButtonPress-1>', lambda event: gUnit.botShade.motor.move(event, 1))

btnBottomShadeDown = tk.Button(app, name="btnBottomShadeDown", image=arrowLeft, borderwidth=0)
btnBottomShadeDown.grid(row=3, column=3, ipadx=3, ipady=3)
btnBottomShadeDown.bind('<ButtonRelease-1>', lambda event: gUnit.botShade.motor.stop(event))
btnBottomShadeDown.bind('<ButtonPress-1>', lambda event: gUnit.botShade.motor.move(event, 0))
#jge - end manual movers
########################

########################
#jge - preset section
btnSmallCircle1 = tk.Button(app, name="btnSmallCircle1", image=smallRoundButton, borderwidth=0)
btnSmallCircle1.grid(row=1, column=6, ipadx=3, ipady=3)
btnSmallCircle1.bind('<ButtonPress-1>', lambda event: timingStart(event, timer1))
btnSmallCircle1.bind('<ButtonRelease-1>', lambda event: timingStop(event, timer1, 1))

btnSmallCircle2 = tk.Button(app, name="btnSmallCircle2", image=smallRoundButton, borderwidth=0)
btnSmallCircle2.grid(row=2, column=6, ipadx=3, ipady=3)
btnSmallCircle2.bind('<ButtonPress-1>', lambda event: gUnit.gotoPreset(event, timer1))
btnSmallCircle2.bind('<ButtonRelease-1>', lambda event: timingStop(event, timer1, 2))

btnSmallCircle3 = tk.Button(app, name="btnSmallCircle3", image=smallRoundButton, borderwidth=0)
btnSmallCircle3.grid(row=4, column=6, ipadx=3, ipady=3)
btnSmallCircle3.bind('<ButtonPress-1>', lambda event: gUnit.gotoPreset(event, timer1))
btnSmallCircle3.bind('<ButtonRelease-1>', lambda event: timingStop(event, timer1, 3))

btnSmallCircle4 = tk.Button(app, name="btnSmallCircle4", image=smallRoundButton, borderwidth=0)
btnSmallCircle4.grid(row=5, column=6, ipadx=3, ipady=3)
btnSmallCircle4.bind('<ButtonPress-1>', lambda event: timingStart(event, timer1))
btnSmallCircle4.bind('<ButtonRelease-1>', lambda event: timingStop(event, timer1, 4))
#jge - end preset
########################

app.grid_rowconfigure(0, weight=1)
app.grid_rowconfigure(6, weight=1)
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(8, weight=1)

app.mainloop()




