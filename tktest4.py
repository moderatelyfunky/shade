import tkinter as tk

##################################
#jge - 8/29/18 - mashup experiment
import controller_light
from time import sleep
import pigpio
import time
import tty
import sys
import termios
import RPi.GPIO as GPIO #jge - using for step count movement
import operator #jge - used to find max array value and member
controller = controller_light
#################################################################
#jge - init

pi = pigpio.pi() # Connect to pigpiod daemon
if not pi.connected:
   exit(0)
##########################################################
#jge - Motor constructors 
#jge - 1st argument = sleep Pin
#jge - 2nd argument = dir Pin
#jge - 3rd argument = step pin
#jge - 4th argument = name
#jge - 5th argument = Cover direction - so can compare when +- steps
#jge - 6th argument = Uncover direction
#jge - HomeSwitch constructors.  1st arg - gpio
##########################################################
leftHomeSwitch = controller.HomeSwitch(1, 'left home switch')
leftMotor = controller.Motor(6, 26, 19, 0, 'motor 3', 0, 1, pi)
leftShade = controller.Shade(leftMotor, leftHomeSwitch, 'left shade')

rightHomeSwitch = controller.HomeSwitch(1, 'right home switch')
rightMotor = controller.Motor(12, 24, 23, 0, 'motor 1', 0, 1, pi)
rightShade = controller.Shade(rightMotor, rightHomeSwitch, 'right shade')

topHomeSwitch = controller.HomeSwitch(1, 'top home switch')
topMotor = controller.Motor(5, 27, 17, 0, 'motor 2', 0, 1, pi)
topShade = controller.Shade(topMotor, topHomeSwitch, 'top shade')

botHomeSwitch = controller.HomeSwitch(1, 'bottom home switch')
botMotor = controller.Motor(13, 20, 21, 0, 'motor 4', 1, 0, pi)
botShade = controller.Shade(botMotor, botHomeSwitch, 'bottom shade')

##########################################################
#jge - Environment constructor - setup common properties
#jge - 1st argument = Microstep Mode - Full, 1/2, 1/4, 1/8, 1/16, 1/32
#jge - 2nd argument = Mode pin 1 - shared by all motor drivers
#jge - 3rd argument = Mode pin 2 - shared by all motor drivers
#jge - 4th argument = Mode pin 3 - shared by all motor drivers
#jge - 5th argument = Maximum microsecond delay between preset going pulses
#jge - 6th argument = Minimum ""
#jge - 7th argument - How much to gain between the min and max in each loop  
#################################################################
environment = controller.Environment('Full', 14, 15, 18, 1100, 400, 1, pi) 
unit = controller.Unit([leftShade, rightShade, topShade, botShade], environment)
#################################################################
#jge - hard coded preset building for now
         
leftShade.preset.append(3000)
rightShade.preset.append(7000)
topShade.preset.append(3200)
botShade.preset.append(2500)

leftShade.preset.append(8000)
rightShade.preset.append(500)
topShade.preset.append(100)
botShade.preset.append(100)

leftShade.preset.append(5000)
rightShade.preset.append(4000)
topShade.preset.append(3000)
botShade.preset.append(2000)

leftShade.preset.append(1000)
rightShade.preset.append(2000)
topShade.preset.append(3000)
botShade.preset.append(4000)

leftShade.preset.append(0)
rightShade.preset.append(0)
topShade.preset.append(0)
botShade.preset.append(0)

leftShade.preset.append(8900)
rightShade.preset.append(8900)
topShade.preset.append(10500)
botShade.preset.append(10500)
#jge - end mashup
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
btnCircle1 = tk.Button(app, image=roundButton, borderwidth=0, command=unit.gotoPreset(5,unit)).grid(row=2, column=0, rowspan=2, columnspan=2)
btnCircle2 = tk.Button(app, image=roundButton, borderwidth=0, command=unit.gotoPreset(6,unit)).grid(row=2, column=3, rowspan=2, columnspan=2)
btnTopShadeUp = tk.Button(app, image=arrowUp, borderwidth=0, command=doSomething).grid(row=2, column=2)
btnTopShadeDown = tk.Button(app, image=arrowDown, borderwidth=0, command=doSomething).grid(row=3, column=2)
btnLeftShadeLeft = tk.Button(app, image=arrowLeft, borderwidth=0, command=leftShade.motor.move(1)).grid(row=4, column=0)
btnLeftShadeRight = tk.Button(app, image=arrowRight, borderwidth=0, command=leftShade.motor.move(0)).grid(row=4, column=1)
btnRightShadeLeft = tk.Button(app, image=arrowLeft, borderwidth=0, command=doSomething).grid(row=4, column=3)
btnRightShadeRight = tk.Button(app, image=arrowRight, borderwidth=0, command=doSomething).grid(row=4, column=4)
btnBottomShadeUp = tk.Button(app, image=arrowDown, borderwidth=0, command=doSomething).grid(row=5, column=2)
btnBottomShadeDown = tk.Button(app, image=arrowUp, borderwidth=0, command=doSomething).grid(row=6, column=2)


app.mainloop()




