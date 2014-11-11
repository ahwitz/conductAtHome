from __future__ import division
import pygame
import pygame.camera
from pygame.locals import *
import cv
import time
import os
import sys
import inspect

#dimensions of image
WIDTH = 630
HEIGHT = 360
SCREEN = [WIDTH, HEIGHT]

#pygame color for drawing boxes on image
RED = pygame.Color(255, 0, 0, 0)

#threshold for how much more green than red or blue the pixels need to be
COLOR_THRESHOLD = 30

#buffer to include a pixel or a component as part of another
MERGE_BUFFER = 2

#takes (x, y) location
def isGreen(x, y):
    try:
        r, g, b, a = image.get_at((x, y))
    except IndexError:
        #if pixel is invalid, return false
        if x < 0 or x > (WIDTH - 1):
            return False
        if y < 0 or y > (HEIGHT - 1):
            return False
        else:
            print "unknown error"
            return False

    #return if it's green
    return (g > r + COLOR_THRESHOLD and g > b + COLOR_THRESHOLD)

#keeps track of all the components
class componentCollection(object):
    def __init__(self):
        self.components = {}
        self.oldComponents = {}
        self.componentID = 0
        self.activeComponent = False
        self.pixels = {}
        self.checkedPix = {} # a dict of (for (x,y) points) x: [y1, y2, y3]; the alternative is a [] of (x,y) tuples, where using the "in" operator ain't gonna happen
        print "Initializing collection."

    #beginning of every frame
    def update(self):
        #for each component in the old frame
        for curCompID in self.oldComponents:
            #make sure we're expanding the right component
            self.activeComponent = curCompID

            #get the center pixel coordinates
            ulx, uly, lrx, lry = self.oldComponents[curCompID].getVals()
            horizCenter = int((lrx - ulx) / 2) + ulx
            vertCenter = int((lry - uly) / 2) + uly
            pixel = (horizCenter, vertCenter)

            foundCount = 0
            missedCount = 0
            missedGreen = 0
            #go through each pixel
            for curX in range(ulx - 1, lrx + 1):
                for curY in range(uly - 1, lry + 1):
                    #if it hasn't already been checked
                    if self.checkedCheck(curX, curY):
                        curPixel = (curX, curY)
                        #and if it's green
                        if isGreen(curX, curY):
                            #if the component already exists
                            if curCompID in self.components:
                                #make this pixel part of the current component and expand it to all the green ones next to it
                                self.spiralExpand(curPixel)
                            else:
                                #else add a new component using the old component ID and expand it
                                self.components[self.activeComponent] = connectedComponent(curPixel)
                                self.spiralExpand(curPixel)
                            foundCount += 1
                        else:
                            missedGreen += 1
                    else:
                        missedCount += 1

            #try to merge with currently-existing components
            self.mergeCheck()  
            print foundCount, "found", missedGreen, "missedGreen", missedCount, "missed"

        #deactivate all the components
        self.activeComponent = False

        #go through the rest of the unchecked pixels and add if they're green
            #look through the pixels by 5s, but addPixel calls spiralExpand which goes by 1s
            #this is not a speed issue: benchmarked at 26fps with this, 27 without. 
            #this IS a speed issue if it's not checked by 5s
        for x in range(0, WIDTH, 5):
            for y in range(0, HEIGHT, 5):
                if self.checkedCheck(x, y):
                    pixel = (x, y)
                    if isGreen(x, y):
                        collection.addPixel(pixel)

        #reset the oldComponents dict
        self.oldComponents = {}

    #checks whether (x, y) has been checked already; adds and returns true if it hasn't
    def checkedCheck(self, x, y):
        if x in self.checkedPix:
            if y in self.checkedPix[x]:
                return False
            else:
                self.checkedPix[x].append(y)
                return True
        else:
            self.checkedPix[x] = [y]
            return True

    #does a recursive breadth-first search on the pixels in the image, adds if green
    def spiralExpand(self, curPixel):
        x, y = curPixel
        if(isGreen(x, y)):
            self.components[self.activeComponent].nextTo(curPixel)
            for xVal in range(x - 1, x + 1):
                for yVal in range(y - 1, y + 1):
                    if self.checkedCheck(xVal, yVal):
                        self.spiralExpand((xVal, yVal))
            return True
        return False

    #adds a pixel to collection
    def addPixel(self, pixel):
        #go through each component and see if it's next to it; nextTo automatically adds if it is
        for compID in self.components:
            if self.components[compID].nextTo(pixel):
                return

        #if function hasn't returned yet, create, activate, expand, deactivate
        self.components[self.componentID] = connectedComponent(pixel)
        self.activeComponent = self.componentID
        self.spiralExpand(pixel)
        self.activeComponent = False
        self.componentID += 1
        self.mergeCheck()

    #draws the boxes around the components
    def draw(self):
        for curComp in self.components:
            self.components[curComp].draw()
        self.oldComponents = self.components
        self.components = {}
        self.checkedPix = {}

    #checks to see if two components are next to each other 
    def mergeCheck(self):
        #alreadyMerged array keeps track of components that are already merged
        alreadyMerged = []

        #go through list of components
        for curComp in self.components:
            if curComp not in alreadyMerged:
                #if it's not already merged, compare it to the rest of the components
                for curCompareComp in self.components:
                    if curCompareComp == curComp: #that aren't it
                        continue
                    elif curCompareComp in alreadyMerged: #and that aren't already merged into another
                        continue
                    else:
                        #get X/Y vals of current component and compared component
                        ulx, uly, lrx, lry = self.components[curComp].getVals()
                        culx, culy, clrx, clry = self.components[curCompareComp].getVals()

                        xMatch = False
                        yMatch = False

                        #if the x values overlap
                        if lrx >= culx - MERGE_BUFFER and lrx <= clrx + MERGE_BUFFER:
                            xMatch = True
                        elif ulx >= culx - MERGE_BUFFER and ulx <= clrx + MERGE_BUFFER:
                            xMatch = True

                        if not xMatch:
                            continue

                        #and the y values overlap
                        if lry >= culy - MERGE_BUFFER and lry <= clry + MERGE_BUFFER:
                            yMatch = True
                        elif uly >= culy - MERGE_BUFFER and uly <= clry + MERGE_BUFFER:
                            yMatch = True

                        if not yMatch:
                            continue

                        #it's a match and merge them
                        alreadyMerged.append(curCompareComp)
                        self.components[curComp].mergeWith(curCompareComp)
                        #TODO: since the edge values are here, move mergeWith code to this function)
        
        #delete the merged ones
        for curComp in alreadyMerged:
            del self.components[curComp]

#class for a single component
class connectedComponent(object):
    def __init__(self, initPix):
        self.xVals = [initPix[0], initPix[0]]
        self.yVals = [initPix[1], initPix[1]]

    #public funtion to return values
    def getVals(self):
        return self.xVals[0], self.yVals[0], self.xVals[1], self.yVals[1]

    #determines if a pixel is next to this component
    def nextTo(self, pixel):
        curX, curY = pixel
        xCheck = False
        yCheck = False

        #if it's already within the range
        if curX >= self.xVals[0] and curX <= self.xVals[1]:
            xCheck = True
        #if it's within two pixels less...
        elif curX < self.xVals[0] and curX >= self.xVals[0] - MERGE_BUFFER:
            xCheck = True
            self.xVals[0] = curX
        #or two pixels more, extend the x values to the new pixel
        elif curX > self.xVals[1] and curX <= self.xVals[1] + MERGE_BUFFER:
            xCheck = True
            self.xVals[1] = curX

        if curY >= self.yVals[0] and curY <= self.yVals[1]:
            yCheck = True
        elif curY < self.yVals[0] and curY >= self.yVals[0] - MERGE_BUFFER:
            yCheck = True
            self.yVals[0] = curY
        elif curY > self.yVals[0] and curY <= self.yVals[1] + MERGE_BUFFER:
            yCheck = True
            self.yVals[1] = curY

        #if either worked, return true as it was next to the component
        if xCheck or yCheck:
            return True
        
        #else return false
        return False

    #draws a box around the pixels
    def draw(self):
        for curX in range(self.xVals[0], self.xVals[1]):
            image.set_at((curX, self.yVals[0]), RED)
            image.set_at((curX, self.yVals[1]), RED)

        for curY in range(self.yVals[0], self.yVals[1]):
            image.set_at((self.xVals[0], curY), RED)
            image.set_at((self.xVals[1], curY), RED)

    #merge with another component
    def mergeWith(self, otherComp):
        ulx, uly, lrx, lry = collection.components[otherComp].getVals()

        #take smaller ul values and bigger lr values between the two
        self.xVals[0] = min(self.xVals[0], ulx)
        self.xVals[1] = max(self.xVals[1], lrx)
        self.yVals[0] = min(self.yVals[0], uly)
        self.yVals[1] = max(self.yVals[1], lry)

#initialize pygame
pygame.init()
pygame.camera.init()

#get the webcam input
screen = pygame.display.set_mode(SCREEN)
cam = pygame.camera.Camera('/dev/video0', SCREEN)
cam.start()

#init the collection and image
collection = componentCollection()
image = ""

#init framerate calculations
oldTime = int(time.time())
passedFrames = 0
fpsVector = []

#main loop
while 1:
    #get a picture, update and draw the info
    image = cam.get_image()
    collection.update()
    collection.draw()

    #display the image
    screen.fill([0, 0, 0])
    screen.blit(image, (0, 0))
    pygame.display.update()

    #average the fps
    newTime = int(time.time())
    if newTime != oldTime:
        oldTime = newTime
        fpsVector.append(passedFrames)
        print passedFrames, "fps", sum(fpsVector) / len(fpsVector), "avg"
        passedFrames = 0
    else:
        passedFrames += 1

#    time.sleep(0.5)
