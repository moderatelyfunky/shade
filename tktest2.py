import tkinter as tk


def doSomething():
    print("hello world")

app = tk.Tk()
app.geometry("800x480")
app.title('Slim Shady')
app.option_add("Button.Background", "black")
app.option_add("Button.Foreground", "white")
app.resizable(0, 0)
app.grid_size()

theCanvas = tk.Frame(master=app, bg='white')
theCanvas.propagate(0)
theCanvas.pack(fill=tk.BOTH, expand=1)

btnLeftShadeLeft = tk.Button(master=theCanvas, text='<', command=doSomething)
btnLeftShadeLeft.place(x=50, y=10)
btnLeftShadeRight = tk.Button(master=theCanvas, text='>', command=doSomething)
btnLeftShadeRight.place(x=80, y=10)
#btnTest.grid(row=1, column=3, columnspan=3)

app.mainloop()




