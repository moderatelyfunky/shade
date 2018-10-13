import tkinter as tk
import time
import middle
import threading as th

class DrawingPoint():
    def __init__(self):
        self.x = 0
        self.y = 0

class DrawingCanvas():
    def __init__(self, drawing_enabled, touchScreen):
        self.drawing_enabled = drawing_enabled
        self.the_points = []
        self.touchScreen = touchScreen

        #jge - color choices - http://www.science.smith.edu/dftwiki/index.php/Color_Charts_for_TKinter
        self.the_canvas = tk.Canvas(
            touchScreen.gui.app, 
            width=195, 
            height=419, 
            borderwidth=1, 

            bg="deepskyblue3"
        )
        self.the_canvas.grid(row=1, column=0, rowspan=5, ipadx=3, ipady=3)
        self.the_canvas.bind('<ButtonPress-1>', lambda event: self.enable_drawing())
        self.the_canvas.bind('<Motion>', lambda event: self.start_drawing(event))
        self.the_canvas.bind('<ButtonRelease-1>', lambda event: self.disable_drawing())

    def enable_drawing(self):
        self.drawing_enabled = True
        self.the_points.clear()
        self.the_canvas.delete("all")

    def disable_drawing(self):
        self.drawing_enabled = False
        leftmost_x = 359
        leftmost_y = 0
        rightmost_x = 0
        rightmost_y = 0
        topmost_x = 0
        topmost_y = 430
        bottommost_x = 0
        bottommost_y = 0

        for p in self.the_points:
            if p.x > rightmost_x:
                rightmost_x = p.x
                rightmost_y = p.y
            if p.x < leftmost_x:
                leftmost_x = p.x
                leftmost_y = p.y
            if p.y < topmost_y:
                topmost_x = p.x
                topmost_y = p.y
            if p.y > bottommost_y:
                bottommost_x = p.x
                bottommost_y = p.y

        #jge - now get percentage to cover.
        #jge - swap x and y because of portrait orientation 
        leftShadePct = topmost_y / self.the_canvas.winfo_height()
        rightShadePct = (self.the_canvas.winfo_height() - bottommost_y) / self.the_canvas.winfo_height()
        topShadePct =  (self.the_canvas.winfo_width() - rightmost_x) / self.the_canvas.winfo_width()
        botShadePct = leftmost_x / self.the_canvas.winfo_width()

        if (leftShadePct < 0):
            leftShadePct = 0
        if (rightShadePct < 0):
            rightShadePct = 0
        if (topShadePct < 0):
            topShadePct = 0
        if (botShadePct < 0):
            botShadePct = 0

        self.the_canvas.delete("all")
        ovalId = self.the_canvas.create_oval(leftmost_x, topmost_y, rightmost_x, bottommost_y)
        self.touchScreen.gui.app.after(100, mid.gotoFreehand('freeHand', leftShadePct, rightShadePct, topShadePct, botShadePct))

    def start_drawing(self, event):
        if self.drawing_enabled:
            # print(event.x, event.y)
            self.the_canvas.create_rectangle((event.x, event.y) * 2)
            current_point = DrawingPoint()
            current_point.x = event.x
            current_point.y = event.y
            self.the_points.append(current_point)

class Rect():
    # (start_x, start_y) --> upper left corner
    # (end_x, end_y) --> lower right corner
    # the id is so we can easily delete from the canvas
    start_x = 0
    start_y = 0
    end_x = 0
    end_y = 0
    id = 0

    def __init__(self, touchScreen, start_x, start_y, end_x, end_y, id):
        self.touchScreen = touchScreen
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.id = id
        self.canvasDraw = tk.Canvas(self.touchScreen.gui.app, width=195, height=419, borderwidth=1, highlightbackground="black", highlightthickness=1)
        self.canvasDraw.grid(row=1, column=1, rowspan=5, ipadx=3, ipady=3)
        self.canvasDraw.bind('<ButtonPress-1>', lambda event: self.getStartCoords(event))
        self.canvasDraw.bind('<ButtonRelease-1>', lambda event: self.getEndCoords(event))  


    def getStartCoords(self, event):
        # figure out where the user has clicked on the canvas
        # store that point in the rect object
        # and then delete the previous rectangle
        self.start_x = event.x
        self.start_y = event.y
        self.canvasDraw.delete(self.id)
        print('Starting freehand draw')


    def getEndCoords(self, event):
        # when the user releases the mouse, get the coords there
        # and store them as the end point in the rect object
        # Then draw a rectangle spanning the start to end pts
        # and store the id of the new rectangle in the rect object
        self.end_x = event.x
        self.end_y = event.y
        i = self.canvasDraw.create_rectangle(self.start_x, self.start_y, self.end_x, self.end_y, fill="black")
        self.id = i
        print('Stopping freehand draw')         


class FreeHandContainer():
    def __init__(self, touchScreen):
        self.touchScreen = touchScreen
        #self.freehandArea = Rect(touchScreen, 0, 0, 0, 0, 0)  
        self.freehandArea = DrawingCanvas(False, touchScreen)

class ButtonTimer():
    timerOn = False
    timerCount = 0.0

    def __init__(self, timerOn, timerCount):
        self.timerOn = timerOn
        self.timerCount = timerCount


class PresetButton(tk.Button):
    def __init__(self, touchScreen, presetNo, *args, **kwargs):
        tk.Button.__init__(self, *args, **kwargs)
        self.touchScreen = touchScreen
        self.presetNo = presetNo
        self.btnTimer = ButtonTimer(False, 0.0)
        self.bind('<ButtonPress-1>', lambda event: self.btnPress(event))
        self.bind('<ButtonRelease-1>', lambda event: self.btnRelease(event))
        self.configure(image=self.touchScreen.images.smallRoundButton, borderwidth=0)
        self.grid(columnspan=2, ipadx=3, ipady=3)

    def drawGreenPreset(self, event) :
        event.widget.configure(image=self.touchScreen.images.smallButtonGreen)
    
    def drawNormalPreset(self, event) :
        event.widget.configure(image=self.touchScreen.images.smallRoundButton)

    def btnPress(self, event):
        event.widget.configure(image=self.touchScreen.images.smallButtonGreen)
        
        if self.btnTimer.timerOn == False:
            # if the timer is off, start it and get the current time
            self.btnTimer.timerOn = True
            self.btnTimer.timerCount = time.time()

    def flashGreen(self, event):
        event.widget.configure(image=self.touchScreen.images.smallButtonGreen)

    def flashBlack(self, event):
        event.widget.configure(image=self.touchScreen.images.smallRoundButton)

    def btnRelease(self, event):
        event.widget.configure(image=self.touchScreen.images.smallRoundButton)

        if self.btnTimer.timerOn == True:
            # if the timer is on, stop it and get the count
            self.btnTimer.timerOn = False
            self.btnTimer.timerCount = time.time() - self.btnTimer.timerCount

            # jge - save the preset if they held it down
            if (self.btnTimer.timerCount > 2):
                mid.writePreset(event, self.presetNo)
                # jge - flash to indicate successful save
                # abj - making it happen with 5 separate threads
                t = th.Timer(0.25, lambda: event.widget.configure(image=self.touchScreen.images.smallButtonGreen))
                t.start()
                t1 = th.Timer(.5, lambda: event.widget.configure(image=self.touchScreen.images.smallRoundButton))
                t1.start()
                t2 = th.Timer(.75, lambda: event.widget.configure(image=self.touchScreen.images.smallButtonGreen))
                t2.start()
                t3 = th.Timer(1, lambda: event.widget.configure(image=self.touchScreen.images.smallRoundButton))
                t3.start()
                t4 = th.Timer(1.25, lambda: event.widget.configure(image=self.touchScreen.images.smallButtonGreen))
                t4.start()
                t5 = th.Timer(1.5, lambda: event.widget.configure(image=self.touchScreen.images.smallRoundButton))
                t5.start()

            else:
                mid.gotoPreset(event, self.presetNo)  


class PresetButtonContainer():    
    def __init__(self, touchScreen):
        self.touchScreen = touchScreen
        self.btnPreset1 = PresetButton(self.touchScreen, 1, name="btnPreset1")
        self.btnPreset1.grid(row=1, column=6)
        self.btnPreset2 = PresetButton(self.touchScreen, 2, name="btnPreset2")
        self.btnPreset2.grid(row=2, column=6)
        self.btnPreset3 = PresetButton(self.touchScreen, 3, name="btnPreset3")
        self.btnPreset3.grid(row=4, column=6)
        self.btnPreset4 = PresetButton(self.touchScreen, 4, name="btnPreset4")
        self.btnPreset4.grid(row=5, column=6)


class ManualButton(tk.Button):
    def __init__(self, touchScreen, shade, direction, offImage, onImage, *args, **kwargs):
        tk.Button.__init__(self, *args, **kwargs)

        self.touchScreen = touchScreen
        self.shade = shade
        self.direction = direction
        self.onImage = onImage
        self.offImage = offImage

        # jge - properties common to all manual buttons
        self.configure(image=self.offImage, borderwidth=0)
        self.grid(ipadx=3, ipady=3)

        self.bind('<ButtonPress-1>', lambda event: self.btnPress(event))
        self.bind('<ButtonRelease-1>', lambda event: self.btnRelease(event))

    def btnPress(self, event):
        event.widget.configure(image=self.onImage)
        mid.move(event, self.shade, self.direction)

    def btnRelease(self, event):
        event.widget.configure(image=self.offImage)
        mid.stop(event, self.shade)        

class ManualButtonContainer():
    def __init__(self, touchScreen):
        self.touchScreen = touchScreen 

        self.btnTopShadeUp = ManualButton(self.touchScreen, 'top', 1, self.touchScreen.images.arrowRight, self.touchScreen.images.arrowRightGreen)
        self.btnTopShadeUp.grid(row=3, column=7)

        self.btnTopShadeDown = ManualButton(self.touchScreen, 'top', 0, self.touchScreen.images.arrowLeft, self.touchScreen.images.arrowLeftGreen)
        self.btnTopShadeDown.grid(row=3, column=6)

        self.btnLeftShadeLeft = ManualButton(self.touchScreen, 'left', 1, self.touchScreen.images.arrowUp, self.touchScreen.images.arrowUpGreen)
        self.btnLeftShadeLeft.grid(row=1, column=5)

        self.btnLeftShadeRight = ManualButton(self.touchScreen, 'left', 0, self.touchScreen.images.arrowDown, self.touchScreen.images.arrowDownGreen)
        self.btnLeftShadeRight.grid(row=2, column=5)

        self.btnRightShadeLeft = ManualButton(self.touchScreen, 'right', 0, self.touchScreen.images.arrowUp, self.touchScreen.images.arrowUpGreen)
        self.btnRightShadeLeft.grid(row=4, column=5)

        self.btnRightShadeRight = ManualButton(self.touchScreen, 'right', 1, self.touchScreen.images.arrowDown, self.touchScreen.images.arrowDownGreen)
        self.btnRightShadeRight.grid(row=5, column=5)

        self.btnBottomShadeUp = ManualButton(self.touchScreen, 'bot', 1, self.touchScreen.images.arrowRight, self.touchScreen.images.arrowRightGreen)
        self.btnBottomShadeUp.grid(row=3, column=4)

        self.btnBottomShadeDown = ManualButton(self.touchScreen, 'bot', 0, self.touchScreen.images.arrowLeft, self.touchScreen.images.arrowLeftGreen)
        self.btnBottomShadeDown.grid(row=3, column=3)


class BigButton(tk.Button):
    # jge - extend tk.Button
    def __init__(self, presetNo, touchScreen, *args, **kwargs):
        # jge - get a reference to the overall container
        self.touchScreen = touchScreen
        # jge - call the constructor for tk.Button
        tk.Button.__init__(self, *args, **kwargs)
        # jge - add some additional properties
        self.presetNo = presetNo
        # jge - set the default image for the button
        self.configure(image=self.touchScreen.images.bigRoundButton, borderwidth=0)
        # jge - set default grid positions common to the big buttons
        self.grid(rowspan=2, columnspan=2, ipadx=3, ipady=3)
        # jge - <ButtonPress-1> is the left mouse button
        self.bind('<ButtonPress-1>', lambda event: self.btnPress(event))
        self.bind('<ButtonRelease-1>', lambda event: self.btnRelease(event))
    
    def btnPress(self, event):
        # jge - while the button is pressed, glow green
        event.widget.configure(image=self.touchScreen.images.bigRoundButtonGreen)
        self.touchScreen.gui.app.after(1, mid.gotoPreset(event, self.presetNo))  

    def btnRelease(self, event):
        # jge - when released, set the button image back to default
        event.widget.configure(image=self.touchScreen.images.bigRoundButton)

class BigButtonContainer:
    def __init__(self, touchScreen):
        self.touchScreen = touchScreen
        self.btnOpenWide = BigButton(5, self.touchScreen)
        self.btnOpenWide.grid(row=1, column=3)
        self.btnCloseCenter = BigButton(6, self.touchScreen)
        self.btnCloseCenter.grid(row=4, column=3)


class ImageLoader():
    def __init__(self, parent):   
        self.arrowLeft = tk.PhotoImage(file="images/left-arrow-off.gif")
        self.arrowLeftGreen = tk.PhotoImage(file="images/left-arrow-green.gif")
        self.arrowLeftBlue = tk.PhotoImage(file="images/left-arrow-blue.gif")
        self.arrowLeftOrange = tk.PhotoImage(file="images/left-arrow-orange.gif")
        self.arrowLeftRed = tk.PhotoImage(file="images/left-arrow-red.gif")
        self.arrowRight = tk.PhotoImage(file="images/right-arrow-off.gif")
        self.arrowRightGreen = tk.PhotoImage(file="images/right-arrow-green.gif")
        self.arrowRightBlue = tk.PhotoImage(file="images/right-arrow-blue.gif")
        self.arrowRightOrange = tk.PhotoImage(file="images/right-arrow-orange.gif")
        self.arrowRightRed = tk.PhotoImage(file="images/right-arrow-red.gif")
        self.arrowUp = tk.PhotoImage(file="images/up-arrow-off.gif")
        self.arrowUpGreen = tk.PhotoImage(file="images/up-arrow-green.gif")
        self.arrowUpBlue = tk.PhotoImage(file="images/up-arrow-blue.gif")
        self.arrowUpOrange = tk.PhotoImage(file="images/up-arrow-orange.gif")
        self.arrowUpRed = tk.PhotoImage(file="images/up-arrow-red.gif")
        self.arrowDown = tk.PhotoImage(file="images/down-arrow-off.gif")
        self.arrowDownGreen = tk.PhotoImage(file="images/down-arrow-green.gif")
        self.arrowDownBlue = tk.PhotoImage(file="images/down-arrow-blue.gif")
        self.arrowDownOrange = tk.PhotoImage(file="images/down-arrow-orange.gif")
        self.arrowDownRed = tk.PhotoImage(file="images/down-arrow-red.gif")
        self.bigRoundButton = tk.PhotoImage(file="images/big-button-off.gif")
        self.bigRoundButtonGreen = tk.PhotoImage(file="images/big-button-green.gif")
        self.bigRoundButtonBlue = tk.PhotoImage(file="images/big-button-blue.gif")
        self.bigRoundButtonOrange = tk.PhotoImage(file="images/big-button-orange.gif")
        self.bigRoundButtonRed = tk.PhotoImage(file="images/big-button-red.gif")
        self.smallRoundButton = tk.PhotoImage(file="images/sm-button-off.gif")
        self.smallButtonGreen = tk.PhotoImage(file="images/sm-button-green.gif")
        self.smallRoundButtonGreen = tk.PhotoImage(file="images/sm-button-green.gif")
        self.smallRoundButtonBlue = tk.PhotoImage(file="images/sm-button-blue.gif")
        self.smallRoundButtonOrange = tk.PhotoImage(file="images/sm-button-orange.gif")
        self.smallRoundButtonRed = tk.PhotoImage(file="images/sm-button-red.gif")


class Gui():
    def __init__(self, parent):
        self.parent = parent
        self.app = tk.Tk()

        self.app.geometry("800x480")
        # self.app.wm_attributes('-type', 'dock')
        self.app.title('Slim Shady')
        self.app.option_add("Button.Background", "black")
        self.app.option_add("Button.Foreground", "white")
        self.app.resizable(0, 0)
        # self.app.configure(background='white')

        self.app.grid_rowconfigure(0, weight=1)
        self.app.grid_rowconfigure(6, weight=1)
        self.app.grid_columnconfigure(0, weight=1)
        self.app.grid_columnconfigure(8, weight=1)

class TouchScreen():
    def __init__(self):
        self.gui = Gui(self)
        self.images = ImageLoader(self)
        self.bigButtons = BigButtonContainer(self)
        self.manualButtons = ManualButtonContainer(self)
        self.presetButtons = PresetButtonContainer(self)
        self.freehandInput = FreeHandContainer(self)


# jge - build middle layer to load controller or not
# jge - depending on the gotPi value in the ini.
mid = middle.Middle()
# jge - create the main container and start the tk.mainloop()
touchScreen = TouchScreen()
touchScreen.gui.app.mainloop()
