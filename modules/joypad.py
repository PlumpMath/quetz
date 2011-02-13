# Thanks to kampfgnu ( http://www.panda3d.org/forums/viewtopic.php?t=2305 ) for saving me a lot of work

from pandac.PandaModules import *
import pygame as pg
from string import strip as strip

class Joypad:
    def __init__(self):
        pg.init()
        self.padsConnected = False
        self.controllerType = []
        self.setupGamepads()
        self.runPads()
       
    def setupGamepads(self):       
        #Get the number of controllers so we know how many to init
        count = pg.joystick.get_count()
        if count == 0:
            self.padsConnected = False
#            print "no pads connected"
            return
        else: self.padsConnected = True
        #Initialize the controllers
        if count > 0:
            self.c1=pg.joystick.Joystick(0)
            self.c1.init()
            self.controllerType.append(strip(self.c1.get_name()))
        if count > 1:
            self.c2=pg.joystick.Joystick(1)
            self.c2.init()
            self.controllerType.append(strip(self.c2.get_name()))
        if count > 2:
            self.c3=pg.joystick.Joystick(2)
            self.c3.init()         
            self.controllerType.append(strip(self.c3.get_name()))
        if count > 3:
            self.c4=pg.joystick.Joystick(3)
            self.c4.init()
            self.controllerType.append(strip(self.c4.get_name()))
        #print "%i joypads inited" % count
       
        self.mapping = { "default" : {"NORTH-BUTTON":0, "EAST-BUTTON":1, "SOUTH-BUTTON":2, "WEST-BUTTON":3,
                                        "L1-BUTTON" : 4, "R1-BUTTON" : 5, "L2-BUTTON" : 6, "R2-BUTTON" : 7,
                                        "SELECT-BUTTON":8, "START-BUTTON":9,
                                        "L-STICK-BUTTON":10, "R-STICK-BUTTON":11,
                                        "L-STICK-X" : 0, "L-STICK-Y" : 1, "R-STICK-X" : 2, "R-STICK-Y" : 3,
                                        "HAT-WEST":(-1,0), "HAT-EAST":(1,0), "HAT-NORTH":(0,1), "HAT-SOUTH":(0,-1),
                                        "HAT-SOUTH-WEST":(-1,-1), "HAT-NORTH-WEST":(-1,1), "HAT-NORTH-EAST":(1,1), "HAT-SOUTH-EAST":(1,-1),
                                        "HATS-UP":(0,0)
                                        },
                        #my speedlink
                         "USB  Joystick" : {"NORTH-BUTTON":0, "EAST-BUTTON":1, "SOUTH-BUTTON":2, "WEST-BUTTON":3,
                                        "L1-BUTTON" : 4, "R1-BUTTON" : 5, "L2-BUTTON" : 6, "R2-BUTTON" : 7,
                                        "SELECT-BUTTON":8, "START-BUTTON":9,
                                        "L-STICK-BUTTON":10, "R-STICK-BUTTON":11,
                                        "L-STICK-X" : 0, "L-STICK-Y" : 1, "R-STICK-X" : 2, "R-STICK-Y" : 3,
                                        "HAT-WEST":(-1,0), "HAT-EAST":(1,0), "HAT-NORTH":(0,1), "HAT-SOUTH":(0,-1),
                                        "HAT-SOUTH-WEST":(-1,-1), "HAT-NORTH-WEST":(-1,1), "HAT-NORTH-EAST":(1,1), "HAT-SOUTH-EAST":(1,-1),
                                        "HATS-UP":(0,0)
                                        },
                         #my impact
                         "USB Game Controllers" : {"NORTH-BUTTON":1, "EAST-BUTTON":3, "SOUTH-BUTTON":2, "WEST-BUTTON":0,
                                        "L1-BUTTON" : 4, "R1-BUTTON" : 6, "L2-BUTTON" : 5, "R2-BUTTON" : 7,
                                        "SELECT-BUTTON":8, "START-BUTTON":9,
                                        "L-STICK-BUTTON":10, "R-STICK-BUTTON":11,
                                        "L-STICK-X" : 0, "L-STICK-Y" : 1, "R-STICK-X" : 3, "R-STICK-Y" : 2,
                                        "HAT-WEST":(-1,0), "HAT-EAST":(1,0), "HAT-NORTH":(0,1), "HAT-SOUTH":(0,-1),
                                        "HAT-SOUTH-WEST":(-1,-1), "HAT-NORTH-WEST":(-1,1), "HAT-NORTH-EAST":(1,1), "HAT-SOUTH-EAST":(1,-1),
                                        "HATS-UP":(0,0)
                                        },
                                       
                         "USB Joystick" : {"NORTH-BUTTON":0, "EAST-BUTTON":1, "SOUTH-BUTTON":2, "WEST-BUTTON":3,
                                        "L1-BUTTON" : 4, "R1-BUTTON" : 5, "L2-BUTTON" : 6, "R2-BUTTON" : 7,
                                        "SELECT-BUTTON":8, "START-BUTTON":9,
                                        "L-STICK-BUTTON":10, "R-STICK-BUTTON":11,
                                        "L-STICK-X" : 0, "L-STICK-Y" : 1, "R-STICK-X" : 2, "R-STICK-Y" : 3,
                                        "HAT-WEST":(-1,0), "HAT-EAST":(1,0), "HAT-NORTH":(0,1), "HAT-SOUTH":(0,-1),
                                        "HAT-SOUTH-WEST":(-1,-1), "HAT-NORTH-WEST":(-1,1), "HAT-NORTH-EAST":(1,1), "HAT-SOUTH-EAST":(1,-1),
                                        "HATS-UP":(0,0)
                                        }
                         }
   
    def runPads(self):
        if self.padsConnected:
            taskMgr.add(self.gamepadPollingTask, "gamepadPollingTask")
                               
    def gamepadPollingTask(self, task):
        for e in pg.event.get():
#            print e
            #Get which controller this is and add it to the eventName
            if e.dict["joy"] == 0:
                c_number = "C1_"
                c_type = 0
            elif e.dict["joy"] == 1:
                c_number = "C2_"
                c_type = 1
            elif e.dict["joy"] == 2:
                c_number = "C3_"
                c_type = 2
            elif e.dict["joy"] == 3:
                c_number = "C4_" 
                c_type = 3
           
            if self.mapping.has_key(self.controllerType[c_type]):
                type = self.controllerType[c_type]
            else:
                type = "default"
            #Handle the BUTTON DOWN events
            if e.type == pg.JOYBUTTONDOWN:
                if (e.dict["button"] == self.mapping[type]["NORTH-BUTTON"]):
                    eventName = c_number +  "NORTH-BUTTON_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["EAST-BUTTON"]):
                    eventName = c_number +  "EAST-BUTTON_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["SOUTH-BUTTON"]):
                    eventName = c_number +  "SOUTH-BUTTON_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["WEST-BUTTON"]):
                    eventName = c_number +  "WEST-BUTTON_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["L1-BUTTON"]):
                    eventName = c_number +  "L1-BUTTON_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["R1-BUTTON"]):
                    eventName = c_number +  "R1-BUTTON_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["L2-BUTTON"]):
                    eventName = c_number +  "L2-BUTTON_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["R2-BUTTON"]):
                    eventName = c_number +  "R2-BUTTON_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["SELECT-BUTTON"]):
                    eventName = c_number +  "SELECT-BUTTON_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["START-BUTTON"]):
                    eventName = c_number +  "START-BUTTON_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["L-STICK-BUTTON"]):
                    eventName = c_number +  "L-STICK-BUTTON_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["R-STICK-BUTTON"]):
                    eventName = c_number +  "R-STICK-BUTTON_DOWN"
                    messenger.send(eventName, [])       
                             
#                                                                                                                                               
            #Handle the BUTTONUP events
            elif e.type == pg.JOYBUTTONUP:
                if (e.dict["button"] == self.mapping[type]["NORTH-BUTTON"]):
                    eventName = c_number +  "NORTH-BUTTON_UP"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["EAST-BUTTON"]):
                    eventName = c_number +  "EAST-BUTTON_UP"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["SOUTH-BUTTON"]):
                    eventName = c_number +  "SOUTH-BUTTON_UP"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["WEST-BUTTON"]):
                    eventName = c_number +  "WEST-BUTTON_UP"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["L1-BUTTON"]):
                    eventName = c_number +  "L1-BUTTON_UP"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["R1-BUTTON"]):
                    eventName = c_number +  "R1-BUTTON_UP"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["L2-BUTTON"]):
                    eventName = c_number +  "L2-BUTTON_UP"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["R2-BUTTON"]):
                    eventName = c_number +  "R2-BUTTON_UP"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["SELECT-BUTTON"]):
                    eventName = c_number +  "SELECT-BUTTON_UP"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["START-BUTTON"]):
                    eventName = c_number +  "START-BUTTON_UP"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["L-STICK-BUTTON"]):
                    eventName = c_number +  "L-STICK-BUTTON_UP"
                    messenger.send(eventName, [])
                elif (e.dict["button"] == self.mapping[type]["R-STICK-BUTTON"]):
                    eventName = c_number +  "R-STICK-BUTTON_UP"
                    messenger.send(eventName, [])
                                                   
            #Handle the directional pad
            elif e.type == pg.JOYHATMOTION:
                if (e.dict["value"] == self.mapping[type]["HAT-NORTH"]):
                    eventName = c_number +  "HAT-NORTH_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["value"] == self.mapping[type]["HAT-EAST"]):
                    eventName = c_number +  "HAT-EAST_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["value"] == self.mapping[type]["HAT-SOUTH"]):
                    eventName = c_number +  "HAT-SOUTH_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["value"] == self.mapping[type]["HAT-WEST"]):
                    eventName = c_number +  "HAT-WEST_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["value"] == self.mapping[type]["HAT-SOUTH-WEST"]):
                    eventName = c_number +  "HAT-SOUTH-WEST_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["value"] == self.mapping[type]["HAT-NORTH-WEST"]):
                    eventName = c_number +  "HAT-NORTH-WEST_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["value"] == self.mapping[type]["HAT-NORTH-EAST"]):
                    eventName = c_number +  "HAT-NORTH-EAST_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["value"] == self.mapping[type]["HAT-SOUTH-EAST"]):
                    eventName = c_number +  "HAT-SOUTH-EAST_DOWN"
                    messenger.send(eventName, [])
                elif (e.dict["value"] == self.mapping[type]["HATS-UP"]):
                    eventName = c_number +  "HATS-UP"
                    messenger.send(eventName, [])
                 
                   
            #Handle the analog sticks
            elif e.type == pg.JOYAXISMOTION:
                #Handle the left analog stick X axis
                if (e.dict["axis"] == self.mapping[type]["L-STICK-X"]):
                    if (e.dict["value"] != 0):
                        eventName = c_number +  "L-STICK-X"
                        messenger.send(eventName, [e.dict["value"]])
                                                                                                     
                #Handle the left analog stick Y axis
                elif (e.dict["axis"] == self.mapping[type]["L-STICK-Y"]):
                    if (e.dict["value"] != 0):
                        eventName = c_number +  "L-STICK-Y"
                        messenger.send(eventName, [e.dict["value"]])             
#                       
                #Handle the right analog stick X axis
                elif (e.dict["axis"] == self.mapping[type]["R-STICK-X"]):
                    if (e.dict["value"] != 0):
                        eventName = c_number +  "R-STICK-X"
                        messenger.send(eventName, [e.dict["value"]])   
                                                                               
                #Handle the right analog stick Y axis
                elif (e.dict["axis"] == self.mapping[type]["R-STICK-Y"]):
                    if (e.dict["value"] != 0):
                        eventName = c_number +  "R-STICK-Y"
                        messenger.send(eventName, [e.dict["value"]])
                                                                             
        return task.cont 