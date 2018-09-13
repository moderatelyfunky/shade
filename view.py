import tkinter as tk
import time
#jge - build middle layer to load controller or not
#jge - depending on the gotPi value in the ini. 
import middle
mid = middle.Middle()

class BigButton(tk.Button):
    #jge - extend tk.Button
    def __init__(self, presetNo, *args, **kwargs):
        tk.Button.__init__(self, *args, **kwargs)
        self.presetNo = presetNo
        self.configure(image=bigRoundButton, borderwidth=0)
        self.grid(rowspan=2, columnspan=2, ipadx=3, ipady=3)
        self.bind('<ButtonPress-1>', lambda event: self.btnPress(event))
        self.bind('<ButtonRelease-1>', lambda event: self.btnRelease(event))
    
    def btnPress(self, event):
        event.widget.configure(image=bigRoundButtonGreenGlow)
        mid.gotoPreset(event, self.presetNo)  

    def btnRelease(self, event):
        event.widget.configure(image=bigRoundButton)

class ManualButton(tk.Button):
    #jge - extend tk.Button
    def __init__(self, shade, direction, image, *args, **kwargs):
        tk.Button.__init__(self, *args, **kwargs)
        self.shade = shade
        self.direction = direction
        #jge - <ButtonPress-1> is the left mouse button
        self.configure(image=image, borderwidth=0)
        self.bind('<ButtonRelease-1>', lambda event: mid.stop(event, self.shade))
        self.bind('<ButtonPress-1>', lambda event: mid.move(event, self.shade, self.direction))
        self.grid(ipadx=3, ipady=3)
        
class PresetButton(tk.Button):
    #jge - extend tk.Button
    def __init__(self, presetNo, *args, **kwargs):
        tk.Button.__init__(self, *args, **kwargs)
        self.presetNo = presetNo
        self.btnTimer = ButtonTimer(False, 0.0)
        self.bind('<ButtonPress-1>', lambda event: self.btnPress(event))
        self.bind('<ButtonRelease-1>', lambda event: self.btnRelease(event))
        self.configure(image=smallRoundButton, borderwidth=0)
        self.grid(columnspan=2, ipadx=3, ipady=3)

    def drawGreenPreset(self, event) :
        event.widget.configure(image=smallButtonGreenGlow)
    
    def drawNormalPreset(self, event) :
        event.widget.configure(image=smallButtonGreenGlow)
        app.after(500, self.drawGreenPreset(event))

    def btnPress(self, event):
        event.widget.configure(image=smallButtonGreenGlow)
        
        if self.btnTimer.timerOn == False:
            # if the timer is off, start it and get the current time
            self.btnTimer.timerOn = True
            self.btnTimer.timerCount = time.time()

    def btnRelease(self, event):
        event.widget.configure(image=smallRoundButton)
        if self.btnTimer.timerOn == True:
            # if the timer is on, stop it and get the count
            self.btnTimer.timerOn = False
            self.btnTimer.timerCount = time.time() - self.btnTimer.timerCount

            #jge - save the preset if they held it down
            if (self.btnTimer.timerCount > 2):
                app.after(500, self.drawNormalPreset(event))
                mid.writePreset(event, self.presetNo)
                #jge - flash to indicate successful save
            else:
                mid.gotoPreset(event, self.presetNo)  

class ButtonTimer:
    timerOn = False
    timerCount = 0.0

    def __init__(self, timerOn, timerCount):
        self.timerOn = timerOn
        self.timerCount = timerCount

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

    def getStartCoords(self, event):
        # figure out where the user has clicked on the canvas
        # store that point in the rect object
        # and then delete the previous rectangle
        # canvasDraw.option_clear()
        self.start_x = event.x
        self.start_y = event.y
        canvasDraw.delete(self.id)
        print('Starting freehand draw')

    def getEndCoords(self, event):
        # when the user releases the mouse, get the coords there
        # and store them as the end point in the rect object
        # Then draw a rectangle spanning the start to end pts
        # and store the id of the new rectangle in the rect object
        self.end_x = event.x
        self.end_y = event.y
        i = canvasDraw.create_rectangle(self.start_x, self.start_y, self.end_x, self.end_y, fill="black")
        self.id = i
        print('Stopping freehand draw')

#################################
#jge - form settings
app = tk.Tk()
app.geometry("800x480")
#app.wm_attributes('-type', 'dock')
app.title('Slim Shady')
app.option_add("Button.Background", "black")
app.option_add("Button.Foreground", "white")
app.resizable(0, 0)
#app.configure(background='white')
#################################

arrowLeft=tk.PhotoImage(file="images/arrow-left.gif")
arrowRight=tk.PhotoImage(file="images/arrow-right.gif")
arrowUp=tk.PhotoImage(file="images/arrow-up.gif")
arrowDown=tk.PhotoImage(file="images/arrow-down.gif")
bigRoundButton = tk.PhotoImage(file="images/big-button-off.gif")
bigRoundButtonGreenGlow = tk.PhotoImage(file="images/big-button-on.gif")
smallRoundButton = tk.PhotoImage(file="images/small-button-off.gif")
smallButtonGreenGlow = tk.PhotoImage(file="images/small-button-on.gif")

canvasDraw = tk.Canvas(app, width=195, height=419, borderwidth=1)
canvasDraw.grid(row=1, column=1, rowspan=5, ipadx=3, ipady=3)
canvasDraw.bind('<ButtonPress-1>', lambda event: freehandArea.getStartCoords(event))
canvasDraw.bind('<ButtonRelease-1>', lambda event: freehandArea.getEndCoords(event))

freehandArea = Rect(0, 0, 0, 0, 0)
########################
#jge - two button section
btnOpenWide = BigButton(5)
btnOpenWide.grid(row=1, column=3)

btnCloseCenter = BigButton(6)
btnCloseCenter.grid(row=4, column=3)
#jge - end two button
########################

########################
#jge - manual movers
btnTopShadeUp = ManualButton('top', 1, arrowRight)
btnTopShadeUp.grid(row=3, column=7)

btnTopShadeDown = ManualButton('top', 0, arrowLeft)
btnTopShadeDown.grid(row=3, column=6)

btnLeftShadeLeft = ManualButton('left', 1, arrowUp)
btnLeftShadeLeft.grid(row=1, column=5)

btnLeftShadeRight = ManualButton('left', 0, arrowDown)
btnLeftShadeRight.grid(row=2, column=5)

btnRightShadeLeft = ManualButton('right', 0, arrowUp)
btnRightShadeLeft.grid(row=4, column=5)

btnRightShadeRight = ManualButton('right', 1, arrowDown)
btnRightShadeRight.grid(row=5, column=5)

btnBottomShadeUp = ManualButton('bot', 1, arrowRight)
btnBottomShadeUp.grid(row=3, column=4)

btnBottomShadeDown = ManualButton('bot', 0, arrowLeft)
btnBottomShadeDown.grid(row=3, column=3)
#jge - end manual movers
########################

########################
#jge - preset section
btnPreset1 = PresetButton(1, name="btnPreset1")
btnPreset1.grid(row=1, column=6)

btnPreset2 = PresetButton(2, name="btnPreset2")
btnPreset2.grid(row=2, column=6)

btnPreset3 = PresetButton(3, name="btnPreset3")
btnPreset3.grid(row=4, column=6)

btnPreset4 = PresetButton(4, name="btnPreset4")
btnPreset4.grid(row=5, column=6)
#jge - end preset
########################

app.grid_rowconfigure(0, weight=1)
app.grid_rowconfigure(6, weight=1)
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(8, weight=1)

app.mainloop()




