import tkinter as tk

##################################
#jge - 8/30/18 - mashup experiment
import controller_light as con
gUnit = con.Unit()
#jge - 8/30/19 - end mashup experiment
##################################

def doSomething():
    print("hello world")

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

#btnDraw = tk.Button(app, text="This is where the drawing widget will go.\r\n ").grid(row=0,column=0, columnspan=4)
btnCircle1 = tk.Button(app, image=roundButton, borderwidth=0, command=gUnit.coverAll()).grid(row=2, column=0, rowspan=2, columnspan=2)
btnCircle2 = tk.Button(app, image=roundButton, borderwidth=0, command=gUnit.uncoverAll()).grid(row=2, column=3, rowspan=2, columnspan=2)
btnTopShadeUp = tk.Button(app, image=arrowUp, borderwidth=0, command=doSomething).grid(row=2, column=2)
btnTopShadeDown = tk.Button(app, image=arrowDown, borderwidth=0, command=doSomething).grid(row=3, column=2)
btnLeftShadeLeft = tk.Button(app, image=arrowLeft, borderwidth=0, command=gUnit.leftShade.motor.move(1)).grid(row=4, column=0)
btnLeftShadeRight = tk.Button(app, image=arrowRight, borderwidth=0, command=gUnit.leftShade.motor.move(0)).grid(row=4, column=1)
btnRightShadeLeft = tk.Button(app, image=arrowLeft, borderwidth=0, command=doSomething).grid(row=4, column=3)
btnRightShadeRight = tk.Button(app, image=arrowRight, borderwidth=0, command=doSomething).grid(row=4, column=4)
btnBottomShadeUp = tk.Button(app, image=arrowDown, borderwidth=0, command=doSomething).grid(row=5, column=2)
btnBottomShadeDown = tk.Button(app, image=arrowUp, borderwidth=0, command=doSomething).grid(row=6, column=2)


app.mainloop()




