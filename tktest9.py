import tkinter as tk
import time

class ButtonTimer:
    timerOn = False
    timerCount = 0.0

    def __init__(self, timerOn, timerCount):
        self.timerOn = timerOn
        self.timerCount = timerCount


def doSomethingElse(event):
    print(event.widget)

def timingStart(event, t: ButtonTimer):
    if str(event.widget) == ".!button11":
        print("Small Button Pressed")
        if t.timerOn == False:
            t.timerOn = True
            t.timerCount = time.time()


def timingStop(event, t: ButtonTimer):
    if str(event.widget) == ".!button11":
        print("Small Button Released")
        if t.timerOn == True:
            t.timerOn = False
            t.timerCount = time.time() - t.timerCount
            print(str(t.timerCount))

class Rect:
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


def drawMe(event):
    event.x


def getStartCoords(event, r1):
    canvasDraw.option_clear()
    r1.start_x = event.x
    r1.start_y = event.y
    print(str(r1.start_x) + " " + str(r1.start_y))
    canvasDraw.delete(r1.id)


def getEndCoords(event, r1):
    r1.end_x = event.x
    r1.end_y = event.y
    print(str(r1.end_x) + " " + str(r1.end_y))
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
roundButton = tk.PhotoImage(file="images/round-button.gif")
smallRoundButton = tk.PhotoImage(file="images/small-round-button.gif")
drawingArea = tk.PhotoImage(file="images/rect-rev.gif")

canvasDraw = tk.Canvas(app, width=195, height=419, borderwidth=1)
canvasDraw.grid(row=1, column=1, rowspan=5, ipadx=3, ipady=3)
canvasDraw.bind('<B1-Motion>', drawMe)
canvasDraw.bind('<ButtonPress-1>', lambda event: getStartCoords(event, r1))
canvasDraw.bind('<ButtonRelease-1>', lambda event: getEndCoords(event, r1))

btnCircle1 = tk.Button(app, image=roundButton, borderwidth=0)
btnCircle1.grid(row=1, column=3, rowspan=2, columnspan=2, ipadx=3, ipady=3)
btnCircle1.bind('<ButtonRelease-1>', doSomethingElse)
btnCircle1.bind('<ButtonPress-1>', doSomethingElse)
btnCircle2 = tk.Button(app, image=roundButton, borderwidth=0)
btnCircle2.grid(row=4, column=3, rowspan=2, columnspan=2, ipadx=3, ipady=3)
btnCircle2.bind('<ButtonRelease-1>', doSomethingElse)
btnCircle2.bind('<ButtonPress-1>', doSomethingElse)
btnTopShadeUp = tk.Button(app, image=arrowLeft, borderwidth=0)
btnTopShadeUp.grid(row=3, column=3, ipadx=3, ipady=3)
btnTopShadeUp.bind('<ButtonRelease-1>', doSomethingElse)
btnTopShadeUp.bind('<ButtonPress-1>', doSomethingElse)
btnTopShadeDown = tk.Button(app, image=arrowRight, borderwidth=0)
btnTopShadeDown.grid(row=3, column=4, ipadx=3, ipady=3)
btnTopShadeDown.bind('<ButtonRelease-1>', doSomethingElse)
btnTopShadeDown.bind('<ButtonPress-1>', doSomethingElse)
btnLeftShadeLeft = tk.Button(app, image=arrowUp, borderwidth=0)
btnLeftShadeLeft.grid(row=1, column=5, ipadx=3, ipady=3)
btnLeftShadeLeft.bind('<ButtonRelease-1>', doSomethingElse)
btnLeftShadeLeft.bind('<ButtonPress-1>', doSomethingElse)
btnLeftShadeRight = tk.Button(app, image=arrowDown, borderwidth=0)
btnLeftShadeRight.grid(row=2, column=5, ipadx=3, ipady=3)
btnLeftShadeRight.bind('<ButtonRelease-1>', doSomethingElse)
btnLeftShadeRight.bind('<ButtonPress-1>', doSomethingElse)
btnRightShadeLeft = tk.Button(app, image=arrowUp, borderwidth=0)
btnRightShadeLeft.grid(row=4, column=5, ipadx=3, ipady=3)
btnRightShadeLeft.bind('<ButtonRelease-1>', doSomethingElse)
btnRightShadeLeft.bind('<ButtonPress-1>', doSomethingElse)
btnRightShadeRight = tk.Button(app, image=arrowDown, borderwidth=0)
btnRightShadeRight.grid(row=5, column=5, ipadx=3, ipady=3)
btnRightShadeRight.bind('<ButtonRelease-1>', doSomethingElse)
btnRightShadeRight.bind('<ButtonPress-1>', doSomethingElse)
btnBottomShadeUp = tk.Button(app, image=arrowLeft, borderwidth=0)
btnBottomShadeUp.grid(row=3, column=6, ipadx=3, ipady=3)
btnBottomShadeUp.bind('<ButtonRelease-1>', doSomethingElse)
btnBottomShadeUp.bind('<ButtonPress-1>', doSomethingElse)
btnBottomShadeDown = tk.Button(app, image=arrowRight, borderwidth=0)
btnBottomShadeDown.grid(row=3, column=7, ipadx=3, ipady=3)
btnBottomShadeDown.bind('<ButtonRelease-1>', doSomethingElse)
btnBottomShadeDown.bind('<ButtonPress-1>', doSomethingElse)
btnSmallCircle1 = tk.Button(app, image=smallRoundButton, borderwidth=0)
btnSmallCircle1.grid(row=1, column=6, ipadx=3, ipady=3)
#btnSmallCircle1.bind('<ButtonRelease-1>', doSomethingElse)
#btnSmallCircle1.bind('<ButtonPress-1>', doSomethingElse)
btnSmallCircle1.bind('<ButtonPress-1>', lambda event: timingStart(event, timer1))
btnSmallCircle1.bind('<ButtonRelease-1>', lambda event: timingStop(event, timer1))
btnSmallCircle2 = tk.Button(app, image=smallRoundButton, borderwidth=0)
btnSmallCircle2.grid(row=2, column=6, ipadx=3, ipady=3)
btnSmallCircle2.bind('<ButtonRelease-1>', doSomethingElse)
btnSmallCircle2.bind('<ButtonPress-1>', doSomethingElse)
btnSmallCircle3 = tk.Button(app, image=smallRoundButton, borderwidth=0)
btnSmallCircle3.grid(row=4, column=6, ipadx=3, ipady=3)
btnSmallCircle3.bind('<ButtonRelease-1>', doSomethingElse)
btnSmallCircle3.bind('<ButtonPress-1>', doSomethingElse)
btnSmallCircle4 = tk.Button(app, image=smallRoundButton, borderwidth=0)
btnSmallCircle4.grid(row=5, column=6, ipadx=3, ipady=3)
btnSmallCircle4.bind('<ButtonRelease-1>', doSomethingElse)
btnSmallCircle4.bind('<ButtonPress-1>', doSomethingElse)

app.grid_rowconfigure(0, weight=1)
app.grid_rowconfigure(6, weight=1)
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(8, weight=1)

app.mainloop()




