import pygame
import pygame.camera
from pygame.locals import *
import cv
import time
import os
import sys

#HAAR_PATH = "/home/ahwitz/development/opencv-2.4.7/data/haarcascades/"
SCREEN = [640, 360]
RED = pygame.Color(255, 0, 0, 0)
components = []
# Face
#FACE_HAAR = os.path.join(HAAR_PATH, "haarcascade_frontalface_default.xml")
#FACE_HAAR = cv.Load(FACE_HAAR)

def cvimage_grayscale(cv_image):
    """Converts a cvimage into grayscale"""
    grayscale = cv.CreateImage(cv.GetSize(cv_image), 8, 1)
    cv.CvtColor(cv_image, grayscale, cv.CV_RGB2GRAY)
    return grayscale 

#def detect_faces(cv_image, storage):
#    """Detects faces based on haar. Returns points"""
#    return cv.HaarDetectObjects(cvimage_grayscale(cv_image), FACE_HAAR, storage)

class componentCollection(object):
    def __init__(self):
        self.components = []
        print "Initializing collection."

    def addPixel(self, pixel):
        for curComp in self.components:
            if curComp.nextTo(pixel):
                return True

        self.components.append(connectedComponent(pixel))

    def draw(self, image):
        for curComp in self.components:
            curComp.draw(image)

    def mergeCheck(self):
        toDel = []
        for origComp in self.components:
            topLeft = tuple(origComp.xVals)
            botRight = tuple(origComp.yVals)

            for curComp in self.components:
                if curComp in toDel:
                    continue
                if curComp.nextTo(topLeft) or curComp.nextTo(botRight):
                    curComp.mergeWith(origComp)
                    toDel.append(origComp)
                    break

        for curComp in toDel:
            self.components.remove(curComp)

class connectedComponent(object):
    def __init__(self, initPix):
        self.xVals = [initPix[0], initPix[0]]
        self.yVals = [initPix[1], initPix[1]]

    def nextTo(self, pixel):
        curX, curY = pixel
        xCheck = False
        yCheck = False

        if curX in range(self.xVals[0], self.xVals[1]):
            xCheck = True
        elif curX == self.xVals[0] - 1:
            xCheck = True
            self.xVals[0] = curX
        elif curX == self.xVals[1] + 1:
            xCheck = True
            self.xVals[1] = curX

        if curY in range(self.yVals[0], self.yVals[1]):
            yCheck = True
        elif curY == self.yVals[0] - 1:
            yCheck = True
            self.yVals[0] = curY
        elif curY == self.yVals[1] + 1:
            yCheck = True
            self.yVals[1] = curY

        if xCheck and yCheck:
            return True

        return False

    def draw(self, image):
        for curX in range(self.xVals[0], self.xVals[1]):
            image.set_at((curX, self.yVals[0]), RED)
            image.set_at((curX, self.yVals[1]), RED)

        for curY in range(self.yVals[0], self.yVals[1]):
            image.set_at((self.xVals[0], curY), RED)
            image.set_at((self.xVals[1], curY), RED)

    def mergeWith(self, otherComp):
        ulx, lrx = otherComp.xVals
        uly, lry = otherComp.yVals

        if ulx < self.xVals[0]:
            self.xVals[0] = ulx
        if lrx > self.xVals[1]:
            self.xVals[1] = lrx
        if uly < self.yVals[0]:
            self.yVals[0] = uly
        if lry > self.yVals[1]:
            self.yVals[1] = lry

def detect_green(image):
    width, height = image.get_size()
    mergeCount = 0
    for x in range(0, width):
        for y in range(0, height):
            pixel = (x, y)
            r, g, b, a = image.get_at(pixel)
            if g > r + 30 and g > b + 30:
                collection.addPixel(pixel)
        if mergeCount == 4:
            collection.mergeCheck()
            mergeCount = 0
        else:
            mergeCount += 1
    #print dir(cv_image)
    print len(collection.components), "found, length of"

def cvimage_to_pygame(image):
    """Convert cvimage into a pygame image"""
    image_rgb = cv.CreateMat(image.height, image.width, cv.CV_8UC3)
    cv.CvtColor(image, image_rgb, cv.CV_BGR2RGB)
    return pygame.image.frombuffer(image.tostring(), cv.GetSize(image_rgb),
"RGB")

def draw_from_points(cv_image, points):
    """Takes the cv_image and points and draws a rectangle based on the points.
Returns a cv_image."""
    for (x, y, w, h), n in points:
        cv.Rectangle(cv_image, (x, y), (x + w, y + h), 255)
    return cv_image

def pygame_to_cvimage(surface):
    """Convert a pygame surface into a cv image"""
    cv_image = cv.CreateImageHeader(surface.get_size(), cv.IPL_DEPTH_8U, 3)
    image_string = surface_to_string(surface)
    cv.SetData(cv_image, image_string)
    return cv_image    
 
def surface_to_string(surface):
    """Convert a pygame surface into string"""
    return pygame.image.tostring(surface, 'RGB')

pygame.init()
pygame.camera.init()

screen = pygame.display.set_mode(SCREEN)
cam = pygame.camera.Camera('/dev/video0', SCREEN)
cam.start()
collection = componentCollection()

while 1:
    #time.sleep(1/1000)
    image = cam.get_image()
    #cv_image = pygame_to_cvimage(image)
    #storage = cv.CreateMemStorage(-1)
    #points = detect_faces(cv_image, storage)
    #cv_image = draw_from_points(cv_image, points)
    detect_green(image)
    collection.draw(image)
    collection.components = [] #eventually work with the ones that exist
    print collection.components

    screen.fill([0, 0, 0])
    screen.blit(image, (0, 0))
    pygame.display.update()