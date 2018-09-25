import weakref
import configparser
from time import sleep
import pigpio
import time
import sys
import operator #jge - used to find max array value and member
import termios
import tty
import logging

class Unit():
    #jge - this is the main point of entry for control from the gui

    def __init__(self):
        #jge - read the ini file
        self.iniFileName = 'shade.ini'
        self.config = configparser.RawConfigParser()
        self.config.optionxform = str
        self.config.read(self.iniFileName)
        #jge - set up logging

        #if (str(self.config.get('config', 'logEvents')) == '1'):
        #self.logger = logging.getLogger('shadeLog.log')
        #self.startLogging()

        logging.basicConfig(level=logging.INFO, 
                    filename='shade.log', # log to this file
                    format='%(asctime)s %(message)s') # include timestamp
        self.pAL('====================================================', 'info')
        self.pAL('program started', 'info') 
        self.pAL('====================================================', 'info')

        #jge - need a master flag to halt all when a limit switch is hit during a preset move
        self.haltAll = 0
        self.goingToPreset = 0
        
        #jge - until the homing is working, allow the manual
        #jge - buttons to move what they think is zero
        self.stopAtWideOpen = self.config.get('config', 'stopAtWideOpen')

        self.pi = pigpio.pi() # Connect to pigpiod daemon
        if not self.pi.connected:
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
        self.leftHomeSwitch = HomeSwitch(self, 16, 'left home switch')
        self.leftMotor = Motor(self, 6, 26, 19, 0, 'motor 3', 0, 1, self.leftHomeSwitch)
        self.leftShade = Shade(self, self.leftMotor,'left shade')
        self.getPresets(self.leftShade)

        self.rightHomeSwitch = HomeSwitch(self, 22, 'right home switch')
        self.rightMotor = Motor(self, 12, 24, 23, 0, 'motor 1', 0, 1, self.rightHomeSwitch)
        self.rightShade = Shade(self, self.rightMotor, 'right shade')
        self.getPresets(self.rightShade)
        
        self.topHomeSwitch = HomeSwitch(self, 4, 'top home switch')
        self.topMotor = Motor(self, 5, 27, 17, 0, 'motor 2', 0, 1, self.topHomeSwitch)
        self.topShade = Shade(self, self.topMotor, 'top shade')
        self.getPresets(self.topShade)
        
        self.botHomeSwitch = HomeSwitch(self, 25, 'bottom home switch')
        self.botMotor = Motor(self, 13, 20, 21, 0, 'motor 4', 1, 0, self.botHomeSwitch)
        self.botShade = Shade(self, self.botMotor, 'bot shade')
        self.getPresets(self.botShade)
        
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
        self.environment = Environment(self, 'Full', 14, 15, 18, 1100, 400, 1) 
        self.pAL('Created environment', 'info')
        self.allShades = [self.leftShade, self.rightShade, self.topShade, self.botShade]
        self.pAL('Created allshades array', 'info')
        self.sleepAll()
        self.pAL('Done with init', 'info')
        #jge - end Unit init
        #################################################################
    
    def pAL(self, message, msgLevel):
        #jge - write to console
        print(message)

        #jge - write to log
        if (msgLevel == 'error'):
            logging.error(message)
        elif (msgLevel == 'info'):
            logging.info(message)

    def startLogging(self):  
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # add formatter to ch
        ch.setFormatter(formatter)

        # add ch to logger
        self.logger.addHandler(ch)

        self.pAL('Program startup', 'info')
        #jge - there are more advanced, built in logging features like auto next day

    def wakeUpAll(self):
        for i, thisShade in enumerate(self.allShades):
            self.allShades[i].motor.wakeUp()

    def sleepAll(self):
        for i, thisShade in enumerate(self.allShades):
            self.allShades[i].motor.sleep()
                
    def uncoverAll(self):
        self.pAL('Uncovering all', 'info')
        self.gotoPreset(self, 5)

    def coverAll(self):
        self.pAL('Covering all', 'info')
        self.gotoPreset(self, 6)

    def stopAll(self):
        for i, thisShade in enumerate(self.allShades):
            self.pAL('Stopping ' + thisShade.name, 'info')           
            self.pAL(self.allShades[i].name + ' steps from home = ' + str(self.allShades[i].motor.stepsFromHomeCount), 'info')
            thisShade.motor.stop('stopAll')

    def cleanup(self):
        self.environment.restoreSettings()

        for thisShade in enumerate(self.allShades):
            self.pAL('Shutting down ' +  thisShade.name, 'info')
            thisShade.motor.stop()

        self.pi.stop()

    def writePreset(self, event, presetNo):
        #jge - write out the current position of each motor
        for i, thisShade in enumerate(self.allShades):
            self.config.set('presets', self.allShades[i].name + ' ' + str(presetNo), str(self.allShades[i].motor.stepsFromHomeCount))
            #jge - update the current preset that's in memory
            self.allShades[i].preset[presetNo -1] = self.allShades[i].motor.stepsFromHomeCount
        with open(self.iniFileName, "w") as config_file:
            self.config.write(config_file)

    def getPresets(self, shade):
        #jge - read the ini for presets       
        shade.preset.append(int(self.config.get('presets', shade.name + ' 1')))
        shade.preset.append(int(self.config.get('presets', shade.name + ' 2')))
        shade.preset.append(int(self.config.get('presets', shade.name + ' 3')))
        shade.preset.append(int(self.config.get('presets', shade.name + ' 4')))
        shade.preset.append(int(self.config.get('presets', shade.name + ' open full')))
        shade.preset.append(int(self.config.get('presets', shade.name + ' closed center')))        

    def getPresetPositions(self, presetNo):
        #jge - Use the preset number to retrieve the positions for each 
        for i, thisShade in enumerate(self.allShades):
            theDestination = self.allShades[i].preset[presetNo - 1]

            #jge - set the direction pin of each motor object also
            #jge - write to the gpio pin to set the direction and 
            #jge - set stepsToDest which is used in the wave creation.  
            if (theDestination > self.allShades[i].motor.stepsFromHomeCount):
                self.allShades[i].motor.direction = self.allShades[i].motor.coverDirection
                self.pi.write(self.allShades[i].motor.dirPin, self.allShades[i].motor.coverDirection)
                self.allShades[i].motor.stepsToDest = theDestination - self.allShades[i].motor.stepsFromHomeCount
            else:
                self.allShades[i].motor.direction = self.allShades[i].motor.uncoverDirection
                self.pi.write(self.allShades[i].motor.dirPin, self.allShades[i].motor.uncoverDirection)
                self.allShades[i].motor.stepsToDest = self.allShades[i].motor.stepsFromHomeCount - theDestination 
            
    def gotoPreset(self, event, presetNo):
        ################################
        #jge - preset init
        self.goingToPreset = 1
        self.wakeUpAll()
        self.getPresetPositions(presetNo)
        maxDelay = self.environment.maxDelay
        minDelay = self.environment.minDelay
        step = self.environment.stepSize
        #jge - end preset init
        ################################

        #jge - sort the shades by least steps to travel
        tempSortedShades = sorted(self.allShades, key=lambda x: x.motor.stepsToDest, reverse=False)
        sortedShades = []

        #jge - there must be a better way to do this
        for i, thisShade in enumerate(tempSortedShades):
            #jge - forget about shades who may already be in position
            if (tempSortedShades[i].motor.stepsToDest != 0):
                sortedShades.append(tempSortedShades[i])
                      
        #jge - build the starting ramp of the wave.  Only add the pins
        #jge - for the shades that still have steps to move.  The bitmask 
        #jge - is the container for all the pins that will be set high.
        #jge - It's an integer that is picked apart later by pigpio.
        
        wfStart = []
        pulseCount = 0
        #jge - don't add to the array when all steps have been used
        hasQualifier = 0
        for delay in range(maxDelay, minDelay, -step):
            bitmask = 0
            hasQualifier = 0
            for i, thisShade in enumerate(sortedShades):
                if (thisShade.motor.stepsToDest > pulseCount):
                    hasQualifier = 1
                    if (bitmask == 0):
                        bitmask = int(1<<sortedShades[i].motor.stepPin)
                    else:
                        bitmask += int(1<<sortedShades[i].motor.stepPin)                   

            if (hasQualifier == 1):    
                #jge - now build the pulse and add it to the array
                pulseCount += 1
                wfStart.append(pigpio.pulse(bitmask, 0, delay))
                wfStart.append(pigpio.pulse(0, bitmask, delay))
            else:
                #jge - all steps have been accounted for
                break

        stepsAlreadyTaken = pulseCount

        #jge - remove any shades who may have no more steps left
        for i, thisShade in enumerate(sortedShades):
            if (sortedShades[i].motor.stepsToDest <= stepsAlreadyTaken):
                sortedShades[i].motor.stepsToDest = 0
                sortedShades.remove(sortedShades[i])
                
        #jge - Build a wave that has the steady state pulses for all
        #jge - until the shade with the least steps is at its goal.
        #jge - Then remove that shade from the array and build for
        #jge - the rest until the step count is reached for the shade 
        #jge - with the next least amount of steps.  Do it two more times

        wfMiddle_A = []
        wfMiddle_B = []
        wfMiddle_C = []
        wfMiddle_D = []
        
        middleWave_A = 0
        wfMiddle_A_Singles = 0
        wfMiddle_A_LoopCount = 0

        middleWave_B = 0
        wfMiddle_B_Singles = 0
        wfMiddle_B_LoopCount = 0
        
        middleWave_C = 0
        wfMiddle_C_Singles = 0
        wfMiddle_C_LoopCount = 0
        
        middleWave_D = 0
        wfMiddle_D_Singles = 0
        wfMiddle_D_LoopCount = 0
        
        #jge - it's possible that the ramp used up all the steps
        if (len(sortedShades) > 0):
            wfMiddle_A, wfMiddle_A_LoopCount, wfMiddle_A_Singles = self.buildMiddleWave(stepsAlreadyTaken, sortedShades)    
            sortedShades.remove(sortedShades[0])
            stepsAlreadyTaken += (wfMiddle_A_LoopCount * 256) + wfMiddle_A_Singles

        if (len(sortedShades) > 0):
            wfMiddle_B, wfMiddle_B_LoopCount, wfMiddle_B_Singles = self.buildMiddleWave(stepsAlreadyTaken, sortedShades)    
            sortedShades.remove(sortedShades[0])
            stepsAlreadyTaken += (wfMiddle_B_LoopCount * 256) + wfMiddle_B_Singles

        if (len(sortedShades) > 0):
            wfMiddle_C, wfMiddle_C_LoopCount, wfMiddle_C_Singles = self.buildMiddleWave(stepsAlreadyTaken, sortedShades)    
            sortedShades.remove(sortedShades[0])
            stepsAlreadyTaken += (wfMiddle_C_LoopCount * 256) + wfMiddle_C_Singles

        if (len(sortedShades) > 0):
            wfMiddle_D, wfMiddle_D_LoopCount, wfMiddle_D_Singles = self.buildMiddleWave(stepsAlreadyTaken, sortedShades)    
            sortedShades.remove(sortedShades[0])
            stepsAlreadyTaken += (wfMiddle_D_LoopCount * 256) + wfMiddle_D_Singles

        #jge - Use Wave_add_generic to "convert" the arrays of pulses
        #jge - into waves that will be fed to pigpio with the wave_chain
        #jge - method
        self.pi.wave_add_generic(wfStart)
        
        #jge - Build an array of the waves to make clean up easier
        allWaves = []                                           

        #jge - make sure not to get empty wave errors
        if (len(wfStart) > 0):
            startRamp = self.pi.wave_create()
            allWaves.append(startRamp)

            if (len(wfMiddle_A) > 0):
                self.pi.wave_add_generic(wfMiddle_A)
                middleWave_A = self.pi.wave_create()
                allWaves.append(middleWave_A)
            
            if (len(wfMiddle_B) > 0):
                self.pi.wave_add_generic(wfMiddle_B)
                middleWave_B = self.pi.wave_create()
                allWaves.append(middleWave_B)

            if (len(wfMiddle_C) > 0):
                self.pi.wave_add_generic(wfMiddle_C)
                middleWave_C = self.pi.wave_create()
                allWaves.append(middleWave_C)

            if (len(wfMiddle_D) > 0):
                self.pi.wave_add_generic(wfMiddle_D)
                middleWave_D = self.pi.wave_create()
                allWaves.append(middleWave_D)                

            #jge - this is the method that pushes the waves to the motors
            #jge - the blocks that start with 255 are loops.  The closing
            #jge - part of the loop tells pigpio how many times to loop
            #jge - each wave and how many single iterations of it after that

            try:
                if (len(wfMiddle_D) > 0):
                    #jge - all elements have length
                    self.pi.wave_chain([
                       startRamp,        
                       255, 0,                       
                          middleWave_A,    
                       255, 1, wfMiddle_A_Singles, wfMiddle_A_LoopCount, #loop x + y*256 times
                       255, 0,                       
                          middleWave_B,    
                       255, 1, wfMiddle_B_Singles, wfMiddle_B_LoopCount,          
                       255, 0,                       
                          middleWave_C,    
                       255, 1, wfMiddle_C_Singles, wfMiddle_C_LoopCount,       
                       255, 0,                       
                          middleWave_D,    
                       255, 1, wfMiddle_D_Singles, wfMiddle_D_LoopCount,                             
                       ])
                else:
                    if (len(wfMiddle_C) > 0):
                        #jge - C is last to have pulses
                        self.pi.wave_chain([
                           startRamp,        
                           255, 0,                       
                              middleWave_A,    
                           255, 1, wfMiddle_A_Singles, wfMiddle_A_LoopCount, 
                           255, 0,                       
                              middleWave_B,    
                           255, 1, wfMiddle_B_Singles, wfMiddle_B_LoopCount,          
                           255, 0,                       
                              middleWave_C,    
                           255, 1, wfMiddle_C_Singles, wfMiddle_C_LoopCount,                                  
                           ])                
                    else:
                        if (len(wfMiddle_B) > 0):
                            #jge - B is last to have pulses
                            self.pi.wave_chain([
                               startRamp,        
                               255, 0,                       
                                  middleWave_A,    
                               255, 1, wfMiddle_A_Singles, wfMiddle_A_LoopCount, 
                               255, 0,                       
                                  middleWave_B,    
                               255, 1, wfMiddle_B_Singles, wfMiddle_B_LoopCount,          
                               ])           
                        else:
                            if (len(wfMiddle_A) > 0):
                                #jge - A is last to have pulses
                                self.pi.wave_chain([
                                   startRamp,        
                                   255, 0,                       
                                      middleWave_A,    
                                   255, 1, wfMiddle_A_Singles, wfMiddle_A_LoopCount, 
                                   ])           
                            else:
                                if (len(wfStart) > 0):
                                    #jge - startRamp is last to have pulses
                                    self.pi.wave_chain([
                                       startRamp,        
                                       ])           
            except Exception as e:
                self.pAL(str(e), 'error')
                        
            #jge - Get control of the situation.  No more phone calls                
            while self.pi.wave_tx_busy():
                #jge - check for a stop message that a limit switch may
                #jge - have thrown.  It's at the unit because anyone could
                #jge - could have hit the switch
                
                if (self.haltAll == 1):
                    self.pi.wave_tx_stop()
                    self.stopAll()
                    #jge - set the flag to indicate to the switch that it's
                    #jge - okay to proceed with homing
                    self.goingToPreset = 0

                time.sleep(0.1)
                
            pigpio.exceptions = True

            if (self.haltAll != 1):
                for i in range(len(allWaves)):
                    self.pAL('deleting a wave -' + str(i) + '-', 'info')
                    try:
                        self.pi.wave_delete(allWaves[i])
                    except Exception as e:
                        self.pAL(str(e), 'error')

        self.sleepAll()
        self.goingToPreset = 0
        self.pi.wave_clear()

        #jge - compare what the callback has counted with the presets
        for i, thisShade in enumerate(self.allShades):
            self.pAL(self.allShades[i].name + ' shade is ' + str(self.allShades[i].motor.stepsFromHomeCount) + ' steps from home', 'info')
        
    def buildMiddleWave(self, stepsAlreadyTaken, sortedShades):
        #jge - This method will build an array of pulses for the
        #jge - steady state portion of the movement.  It uses the
        #jge - same pigpio features as the ramp.  The additional
        #jge - work being done here is to figure out how many times
        #jge - the wave should be looped and run individually.  This
        #jge - is because pigpio has a limit of 256 iterations for
        #jge - each wave.  Anything over that means another loop or
        #jge - just the remainder if it's less than 256
        
        minDelay = self.environment.minDelay
        wfMiddle = []

        #jge - store the count to feed to the wave_chain looper
        maxSingle = 256
        countMiddle = sortedShades[0].motor.stepsToDest - stepsAlreadyTaken
        
        if (countMiddle > 256):
            wfMiddle_LoopCount = int(countMiddle / maxSingle)
            wfMiddle_Singles = countMiddle % maxSingle
        else:
            wfMiddle_LoopCount = 0
            wfMiddle_Singles = countMiddle

        if (sortedShades[0].motor.stepsToDest > stepsAlreadyTaken):
            bitmask = 0
            for i, thisShade in enumerate(sortedShades):
                if (bitmask == 0):
                    bitmask = int(1<<sortedShades[i].motor.stepPin)
                else:
                    bitmask += int(1<<sortedShades[i].motor.stepPin)
            wfMiddle.append(pigpio.pulse(bitmask, 0, minDelay))
            wfMiddle.append(pigpio.pulse(0, bitmask, minDelay))            

        return wfMiddle, wfMiddle_LoopCount, wfMiddle_Singles

    #jge - end unit class
    ####################################################
    
class Environment():
    #jge - housekeeping?

    def __init__(self, parent, microstep, modePin1 = 0, modePin2 = 0, modePin3 = 0, maxDelay = 0, minDelay = 0, stepSize = 0):
        #self.parent = weakref.ref(parent)
        self.parent = parent
        #jge - no need for this with GUI? self.getSettings()
        self.commonPinSetup(microstep, modePin1 = 0, modePin2 = 0, modePin3 = 0)
        #jge - maxDelay is the lowest frequency between pulses
        self.maxDelay = maxDelay
        #jge - minDelay is the quickest pace
        self.minDelay = minDelay
        #jge - how much to gain between high and low frequencies
        self.stepSize = stepSize

    def getSettings(self):
        #jge - this has to do with setting up keyboard input
        #jge - making this change is what goofs up the format
        #jge - when making print statements to the console.         
        self.orig_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin) 

    def restoreSettings(self):
        #jge - this puts the terminal back as it was so line feeds work
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.orig_settings)

    def commonPinSetup(self, microstep, modePin1 = 0, modePin2 = 0, modePin3 = 0):
        #jge - As wired now, these GPIO pins are shared by all motor drivers.
        #jge - Doesn't seem like there will be a need for motors to use different
        #jge - microstepping values.  Also, I don't think there are enough pins on 
        #jge - the pi to accomodate.  

        self.mode = (modePin1, modePin2, modePin3)

        self.resolution = {'Full': (0, 0, 0),
                      'Half': (1, 0, 0),
                      '1/4': (0, 1, 0),
                      '1/8': (1, 1, 0),
                      '1/16': (0, 0, 1),
                      '1/32': (1, 0, 1)}

        for i in range(3):
            self.parent.pi.write(self.mode[i], self.resolution[microstep][i])

class Shade():
    #jge - container for shade elements
    def __init__(self, parent, motor, name = ''):
        self.parent = parent 
        self.motor = motor
        self.name = name
        self.preset = []
        self.parent.pAL('Created ' + self.name, 'info')
                
class HomeSwitch():
    #jge - object to manage the limit switches used to find home
    def __init__(self, parent, switchPin, name = ''):
        self.parent = parent
        self.parentMotor = None
        self.switchPin = switchPin
        self.name = name
        self.prevState = 0
        self.state = 0
        parent.pi.set_mode(switchPin, pigpio.INPUT)
        #jge - using internal resistors in addition to external
        parent.pi.set_pull_up_down(switchPin, pigpio.PUD_DOWN)
        #jge - set up callback function to look for a closing switch
        self.cbf = parent.pi.callback(self.switchPin, pigpio.RISING_EDGE, self.callbackFunc)
        self.parent.pAL('Created ' + self.name, 'info')

    def callbackFunc(self, gpio, level, tick):     
        #jge - no matter what, if the switch is closed, stop the motor.
        #jge - take care of zeroing in the motor stop method
        #jge - also, set the haltAll at the unit to call a stop to the
        #jge - wave_chain in the case of a preset.
        self.state = self.parent.pi.read(self.switchPin)
        self.parent.pAL('In homeswitch cbf - 1 - ' + self.name + ' state = ' + str(self.state) + ' prev state = ' + str(self.prevState), 'info')

        if (self.state == 1 and self.prevState != self.state):
            self.parent.pAL('in homeswitch cbf - 2 - ' + self.name + ' switch closed', 'info')

            if (self.parent.goingToPreset == 1):
                #jge - the pi while loop in the goto preset method
                #jge - will hear this setting of the flag and will
                #jge - cancel the wave send.
             
                self.parent.pAL('in homeswitch cbf - 3 - ' + self.name + ' Interrupting a preset move because a switch has been closed', 'info')
                #jge - set a flag and wait for the gotoPreset to confirm that
                #jge - the goto preset wave_chain has been canceled
                self.parent.haltAll = 1
                while (self.parent.goingToPreset == 1):
                    self.parent.pAL('in homeswitch cbf - 4 ' + self.name + ' - waiting for gotoPreset to be set to 0', 'info')
                    time.sleep(0.1)

            #jge todo - need to home all the motors at this point
            self.parent.pAL('in homeswitch cbf - 5 ' + self.name + ' - about to call homing method', 'info')
            self.parentMotor.findHome('switch Called')
            
            self.parent.pAL('In homeSwitch cbf - 6 ' + self.name + ' -  finished homing', 'info')  

            #jge - reset the checker
            self.state = self.parent.pi.read(self.switchPin)
            self.prevState = self.state
            self.parent.pAL('In homswitch cbf  - 7 ' + self.name + ' = self.state = ' + str(self.state), 'info')
            
            self.parent.haltAll = 0

class Motor():
    def __init__(self, parent, sleepPin = 0, dirPin = 0, stepPin = 0, direction = 0, name = '', coverDirection = 0, uncoverDirection = 0, homeSwitch = 0):
        self.parent = parent
        self.sleepPin = sleepPin
        self.dirPin = dirPin
        self.stepPin = stepPin
        self.direction = coverDirection
        self.name = name
        self.stepsToDest = 0
        self.stepsFromHomeObject = None
        self.stepsFromHomeCount = 0
        self.coverDirection = coverDirection
        self.uncoverDirection = uncoverDirection
        #jge - set up callback function to keep track of steps
        self.stepsFromHomeObject = parent.pi.callback(self.stepPin, pigpio.RISING_EDGE, self.callbackFunc)
        self.homeSwitch = homeSwitch
        self.homeSwitch.parentMotor = self
        #jge - todo - need to find out how many would be fully closed
        #jge - for now set it so it doesn't interfere
        self.maxSteps = 1000000
        self.parent.pi.write(self.stepPin, 1)
        
        self.parent.pAL('Created ' + self.name, 'info')

    def move(self, event, direction):        
        #jge - make sure it's not running against the wide open stops
        if ((direction == self.coverDirection and self.maxSteps > self.stepsFromHomeCount) or
            (direction == self.uncoverDirection and self.stepsFromHomeCount > 0) or
            self.parent.stopAtWideOpen == '0'
            ):
            self.parent.pAL('Moving ' + self.name + ' motor in direction ' + str(direction), 'info')
            self.direction = direction
            self.wakeUp()
            self.parent.pi.write(self.sleepPin, 1)
            self.parent.pi.write(self.dirPin, direction)
            self.parent.pi.set_PWM_dutycycle(self.stepPin, 128)  # PWM 1/2 On 1/2 Off
            self.parent.pi.set_PWM_frequency(self.stepPin, 500)
            sleep(.05)
        else:
            self.parent.pAL('Cant open ' + self.name + ' any further', 'info')
        
    def callbackFunc(self, gpio, level, tick):     
        #jge - figure out whether to add or subtract the steps
        if (self.direction == self.coverDirection):
            self.stepsFromHomeCount += 1
        else:
            self.stepsFromHomeCount -= 1

        #jge - stop the move if it's wide open or closed
        if ((self.stepsFromHomeCount == 0 and self.direction == self.uncoverDirection) or
            (self.stepsFromHomeCount >= self.maxSteps and self.direction == self.coverDirection) or
            (self.parent.haltAll == 1)
           ):
            self.parent.pAL('in Motor cbf - Stopping motor ' + self.name +
                  ' haltAll = ' + str(self.parent.haltAll) +
                  ' stepsFromHome = ' + str(self.stepsFromHomeCount) +
                  ' dir = ' + str(self.direction) +
                  ' cov dir = ' + str(self.coverDirection), 'info')       
            self.stop(self)

            #if (self.stepsFromHomeCount == 0 and self.direction == self.uncoverDirection):
                #jge - since it's at zero, may as well zero it
            #    self.findHome(self)

    def stop(self, event):
        #jge - stop motion then sleep
        self.parent.pi.write(self.stepPin, 0)
        self.parent.pi.write(self.sleepPin, 0)

        self.sleep()

    def findHome(self, event):
        self.parent.pAL('in findhome method', 'info')
        movingOut = []    
        wid = 0
        cushion = []
        cushionStepCount = 10

        #jge - set the direction pin
        self.parent.pi.write(self.dirPin, self.coverDirection)

        #jge - build a generic single pulse
        movingOut.append(pigpio.pulse(1<<self.stepPin, 0, 1100))
        movingOut.append(pigpio.pulse(0, 1<<self.stepPin, 1100))

        while (self.parent.pi.read(self.homeSwitch.switchPin) == 1):
            self.parent.pi.wave_add_generic(movingOut)
            wid = self.parent.pi.wave_create()
            self.parent.pi.wave_send_once(wid)
            while self.parent.pi.wave_tx_busy():
                time.sleep(0.1)
                
        #jge - add some number of steps to completely clear the switch 
        x = 1
        while (x < cushionStepCount):
            cushion.append(pigpio.pulse(1<<self.stepPin, 0, 1100))
            cushion.append(pigpio.pulse(0, 1<<self.stepPin, 1100))
            x+=1
                
        self.parent.pi.wave_add_generic(movingOut)
        wid = self.parent.pi.wave_create()
        self.parent.pi.wave_send_once(wid)
        while self.parent.pi.wave_tx_busy():
            time.sleep(0.1)

        #jge - now that off of switch and cushioned, set to 0
        self.stepsFromHomeCount = 0
        
        self.stop('limit')
        self.parent.pi.wave_clear()
        
    def sleep(self):
        #jge - this turns off motor voltage
        self.parent.pi.write(self.sleepPin, 0)
        
    def wakeUp(self):
        #jge - this restores power to the motor
        self.parent.pi.write(self.sleepPin, 1)

