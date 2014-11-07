from __future__ import division
import pygame
import pygame.camera
from pygame.locals import *
import cv
import time
import os
import sys
import inspect

WIDTH = 630
HEIGHT = 360
RED = pygame.Color(255, 0, 0, 0)
COLOR_THRESHOLD = 30
SCREEN = [WIDTH, HEIGHT]

#takes (x, y) location
def isGreen(x, y):
    try:
        r, g, b, a = image.get_at((x, y))
    except IndexError:
        if x < 0 or x > (WIDTH - 1):
            return False
        if y < 0 or y > (HEIGHT - 1):
            return False
        else:
            print "unknown error"
            return False

    return (g > r + COLOR_THRESHOLD and g > b + COLOR_THRESHOLD)

class componentCollection(object):
    def __init__(self):
        self.components = {}
        self.oldComponents = {}
        self.componentID = 0
        self.activeComponent = False
        self.pixels = {}
        self.checkedPix = {} # a dict of x: [y1, y2, y3]; the alternative is a [], where using the "in" operator ain't gonna happen
        print "Initializing collection."

    def update(self):
        for curCompID in self.oldComponents:
            self.activeComponent = curCompID
            ulx, uly, lrx, lry = self.oldComponents[curCompID].getVals()
            horizCenter = int((lrx - ulx) / 2) + ulx
            vertCenter = int((lry - uly) / 2) + uly
            #print "for", curComp.xVals, curComp.yVals, "center is", horizCenter, vertCenter, "total", int((curComp.xVals[1] - curComp.xVals[0]) / 2) * int((curComp.yVals[1] - curComp.yVals[0]) / 2) 
            pixel = (horizCenter, vertCenter)
            
            for curX in range(ulx - 1, lrx + 1):
                for curY in range(uly - 1, lry + 1):
                    curPixel = (curX, curY)
                    self.checkedCheck(curX, curY)
                    if(isGreen(curX, curY)):
                        if curCompID in self.components:
                            self.components[self.activeComponent].nextTo(curPixel)
                            self.spiralExpand(curPixel)
                        else:
                            self.components[self.activeComponent] = connectedComponent(curPixel)
                            self.spiralExpand(curPixel)
                        self.mergeCheck()
            #print "\t new total", int((curCompAlt.xVals[1] - curCompAlt.xVals[0]) / 2) * int((curCompAlt.yVals[1] - curCompAlt.yVals[0]) / 2) 
        self.activeComponent = False

        #this is not a speed issue: benchmarked at 26fps with this, 27 without
        for x in range(0, WIDTH, 5): #check by 5s, spiralExpand still goes by 1s
            for y in range(0, HEIGHT, 5):
                if self.checkedCheck(x, y):
                    pixel = (x, y)
                    if isGreen(x, y):
                        collection.addPixel(pixel)

        self.oldComponents = {}

    #checks whether (x, y) has been checked already or is in valid pixel range; adds and returns true if it hasn't
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


    def spiralExpand(self, curPixel):
        x, y = curPixel
        if(isGreen(x, y)):
            self.components[self.activeComponent].nextTo(curPixel)
            for xVal in range(x - 1, x + 1):
                for yVal in range(y - 1, y + 1):
                    if self.checkedCheck(xVal, yVal):
                        self.spiralExpand((xVal, yVal))

    def addPixel(self, pixel):
        for compID in self.components:
            if self.components[compID].nextTo(pixel):
                return

        self.components[self.componentID] = connectedComponent(pixel)
        self.activeComponent = self.componentID
        self.spiralExpand(pixel)
        self.activeComponent = False
        self.componentID += 1
        self.mergeCheck()

    def draw(self):
        for curComp in self.components:
            self.components[curComp].draw()
        self.oldComponents = self.components
        self.components = {}
        self.checkedPix = {}

    def mergeCheck(self):
        toSkip = []
        for curComp in self.components:
            if curComp not in toSkip:
                for curCompareComp in self.components:
                    if curCompareComp == curComp:
                        continue
                    elif curCompareComp in toSkip:
                        continue
                    else:
                        curXVals = self.components[curComp].xVals
                        curYVals = self.components[curComp].yVals
                        compXVals = self.components[curCompareComp].xVals
                        compYVals = self.components[curCompareComp].yVals

                        xMatch = False
                        yMatch = False

                        if curXVals[1] >= compXVals[0] and curXVals[1] <= compXVals[1]:
                            xMatch = True
                        elif curXVals[0] >= compXVals[0] and curXVals[0] <= compXVals[1]:
                            xMatch = True

                        if not xMatch:
                            continue

                        if curYVals[1] >= compYVals[0] and curYVals[1] <= compYVals[1]:
                            yMatch = True
                        elif curYVals[0] >= compYVals[0] and curYVals[0] <= compYVals[1]:
                            yMatch = True

                        if not yMatch:
                            continue

                        toSkip.append(curCompareComp)
                        self.components[curComp].mergeWith(curCompareComp)
                        #TODO: since the edge values are here, move mergeWith code to this function)
        
        for curComp in toSkip:
            del self.components[curComp]

class connectedComponent(object):
    def __init__(self, initPix):
        self.xVals = [initPix[0], initPix[0]]
        self.yVals = [initPix[1], initPix[1]]
        self.tracked = False

    def getVals(self):
        return self.xVals[0], self.yVals[0], self.xVals[1], self.yVals[1]

    def nextTo(self, pixel):
        #todo: add override parameter for when spiralExpand adds pixels that it knows will work
        curX, curY = pixel
        xCheck = False
        yCheck = False

        if curX >= self.xVals[0] and curX <= self.xVals[1]:
            xCheck = True
        elif curX == self.xVals[0] - 1:
            xCheck = True
            self.xVals[0] -= 1
        elif curX == self.xVals[1] + 1:
            xCheck = True
            self.xVals[1] += 1

        if curY >= self.yVals[0] and curY <= self.yVals[1]:
            yCheck = True
        elif curY == self.yVals[0] - 1:
            yCheck = True
            self.yVals[0] -= 1
        elif curY == self.yVals[1] + 1:
            yCheck = True
            self.yVals[1] += 1

        if xCheck and yCheck:
            return True

        return False

    def draw(self):
        for curX in range(self.xVals[0], self.xVals[1]):
            image.set_at((curX, self.yVals[0]), RED)
            image.set_at((curX, self.yVals[1]), RED)

        for curY in range(self.yVals[0], self.yVals[1]):
            image.set_at((self.xVals[0], curY), RED)
            image.set_at((self.xVals[1], curY), RED)

    def mergeWith(self, otherComp):
        ulx, lrx = collection.components[otherComp].xVals
        uly, lry = collection.components[otherComp].yVals

        if ulx < self.xVals[0]:
            self.xVals[0] = ulx
        if lrx > self.xVals[1]:
            self.xVals[1] = lrx
        if uly < self.yVals[0]:
            self.yVals[0] = uly
        if lry > self.yVals[1]:
            self.yVals[1] = lry

pygame.init()
pygame.camera.init()

screen = pygame.display.set_mode(SCREEN)
cam = pygame.camera.Camera('/dev/video0', SCREEN)
cam.start()
collection = componentCollection()
image = ""

oldTime = int(time.time())
passedFrames = 0
fpsVector = []

while 1:
    image = cam.get_image()
    collection.update()
    collection.draw()

    screen.fill([0, 0, 0])
    screen.blit(image, (0, 0))
    pygame.display.update()

    newTime = int(time.time())
    if newTime != oldTime:
        oldTime = newTime
        fpsVector.append(passedFrames)
        print passedFrames, "fps", sum(fpsVector) / len(fpsVector), "avg"
        passedFrames = 0
    else:
        passedFrames += 1

    #time.sleep(0.5)
