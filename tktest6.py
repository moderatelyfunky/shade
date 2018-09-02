import tkinter as tk


def doSomething():
    print("hello world")

def bababooey(event, s):
    print(s)

def doSomethingElse(event):
    #print(str(event.widget))
    print(event.widget)

    if str(event.widget) == ".!button":
        print("Big Left Button")
        print(event.type)
    elif str(event.widget) == ".!button2":
        print("Big Right Button")
        print(event.type)
    elif str(event.widget) == ".!button3":
        print("Top Shade Up Button")
        print(event.type)
    elif str(event.widget) == ".!button4":
        print("Top Shade Down Button")
        print(event.type)
    elif str(event.widget) == ".!button5":
        print("Left Shade Left Button")
        print(event.type)
    elif str(event.widget) == ".!button6":
        print("Left Shade Right Button")
        print(event.type)
    elif str(event.widget) == ".!button7":
        print("Right Shade Left Button")
        print(event.type)
    elif str(event.widget) == ".!button8":
        print("Right Shade Right Button")
        print(event.type)
    elif str(event.widget) == ".!button9":
        print("Bottom Shade Up Button")
        print(event.type)
    elif str(event.widget) == ".!button10":
        print("Bottom Shade Down Button")
        print(event.type)
    elif str(event.widget) == ".!button11":
        print("Small Circle 1 Button")
        print(event.type)
    elif str(event.widget) == ".!button12":
        print("Small Circle 2 Button")
        print(event.type)
    elif str(event.widget) == ".!button13":
        print("Small Circle 3 Button")
        print(event.type)
    elif str(event.widget) == ".!button14":
        print("Small Circle 4 Button")
        print(event.type)


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


#btnDraw = tk.Button(app)
#btnDraw.grid(row=0,column=0, columnspan=4)
#btnDraw.bind('<ButtonRelease-1>', doSomethingElse)
btnCircle1 = tk.Button(app, image=roundButton, borderwidth=0)
btnCircle1.grid(row=2, column=0, rowspan=2, columnspan=2)
btnCircle1.bind('<ButtonRelease-1>', lambda event: bababooey(event, "hi there"))
btnCircle1.bind('<ButtonPress-1>', doSomethingElse)
btnCircle2 = tk.Button(app, image=roundButton, borderwidth=0)
btnCircle2.grid(row=2, column=3, rowspan=2, columnspan=2)
btnCircle2.bind('<ButtonRelease-1>', doSomethingElse)
btnCircle2.bind('<ButtonPress-1>', doSomethingElse)
btnTopShadeUp = tk.Button(app, image=arrowUp, borderwidth=0)
btnTopShadeUp.grid(row=2, column=2)
btnTopShadeUp.bind('<ButtonRelease-1>', doSomethingElse)
btnTopShadeUp.bind('<ButtonPress-1>', doSomethingElse)
btnTopShadeDown = tk.Button(app, image=arrowDown, borderwidth=0)
btnTopShadeDown.grid(row=3, column=2)
btnTopShadeDown.bind('<ButtonRelease-1>', doSomethingElse)
btnTopShadeDown.bind('<ButtonPress-1>', doSomethingElse)
btnLeftShadeLeft = tk.Button(app, image=arrowLeft, borderwidth=0)
btnLeftShadeLeft.grid(row=4, column=0)
btnLeftShadeLeft.bind('<ButtonRelease-1>', doSomethingElse)
btnLeftShadeLeft.bind('<ButtonPress-1>', doSomethingElse)
btnLeftShadeRight = tk.Button(app, image=arrowRight, borderwidth=0)
btnLeftShadeRight.grid(row=4, column=1)
btnLeftShadeRight.bind('<ButtonRelease-1>', doSomethingElse)
btnLeftShadeRight.bind('<ButtonPress-1>', doSomethingElse)
btnRightShadeLeft = tk.Button(app, image=arrowLeft, borderwidth=0)
btnRightShadeLeft.grid(row=4, column=3)
btnRightShadeLeft.bind('<ButtonRelease-1>', doSomethingElse)
btnRightShadeLeft.bind('<ButtonPress-1>', doSomethingElse)
btnRightShadeRight = tk.Button(app, image=arrowRight, borderwidth=0)
btnRightShadeRight.grid(row=4, column=4)
btnRightShadeRight.bind('<ButtonRelease-1>', doSomethingElse)
btnRightShadeRight.bind('<ButtonPress-1>', doSomethingElse)
btnBottomShadeUp = tk.Button(app, image=arrowUp, borderwidth=0)
btnBottomShadeUp.grid(row=5, column=2)
btnBottomShadeUp.bind('<ButtonRelease-1>', doSomethingElse)
btnBottomShadeUp.bind('<ButtonPress-1>', doSomethingElse)
btnBottomShadeDown = tk.Button(app, image=arrowDown, borderwidth=0)
btnBottomShadeDown.grid(row=6, column=2)
btnBottomShadeDown.bind('<ButtonRelease-1>', doSomethingElse)
btnBottomShadeDown.bind('<ButtonPress-1>', doSomethingElse)
btnSmallCircle1 = tk.Button(app, image=smallRoundButton, borderwidth=0)
btnSmallCircle1.grid(row=5, column=0)
btnSmallCircle1.bind('<ButtonRelease-1>', doSomethingElse)
btnSmallCircle1.bind('<ButtonPress-1>', doSomethingElse)
btnSmallCircle2 = tk.Button(app, image=smallRoundButton, borderwidth=0)
btnSmallCircle2.grid(row=5, column=1)
btnSmallCircle2.bind('<ButtonRelease-1>', doSomethingElse)
btnSmallCircle2.bind('<ButtonPress-1>', doSomethingElse)
btnSmallCircle3 = tk.Button(app, image=smallRoundButton, borderwidth=0)
btnSmallCircle3.grid(row=5, column=3)
btnSmallCircle3.bind('<ButtonRelease-1>', doSomethingElse)
btnSmallCircle3.bind('<ButtonPress-1>', doSomethingElse)
btnSmallCircle4 = tk.Button(app, image=smallRoundButton, borderwidth=0)
btnSmallCircle4.grid(row=5, column=4)
btnSmallCircle4.bind('<ButtonRelease-1>', doSomethingElse)
btnSmallCircle4.bind('<ButtonPress-1>', doSomethingElse)

app.mainloop()




