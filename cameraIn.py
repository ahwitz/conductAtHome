import pygame
import pygame.camera
from pygame.locals import *
import cv
import time
import os
import sys

#HAAR_PATH = "/home/ahwitz/development/opencv-2.4.7/data/haarcascades/"
SCREEN = [640, 360]
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

    def combinedLength(self):
        return sum(len(x.pixels) for x in self.components)

class connectedComponent(object):
    def __init__(self, initPix):
        self.pixels = []
        self.pixels.append(initPix)

    def nextTo(self, pixel):
        curX, curY = pixel
        xCheck = False
        yCheck = False

        xVals = [x for (x, y) in self.pixels]
        yVals = [y for (x, y) in self.pixels]

        if (curX + 1) in xVals or curX in xVals or (curX - 1) in xVals:
            xCheck = True

        if (curY + 1) in yVals or curY in yVals or (curY - 1) in yVals:
            yCheck = True

        if xCheck and yCheck:
            self.pixels.append(pixel)
            return True

        return False

def detect_green(image, cv_image):
    width, height = image.get_size()
    for x in range(0, width):
        for y in range(0, height):
            pixel = (x, y)
            r, g, b, a = image.get_at(pixel)
            if g > r and g > b:
                collection.addPixel(pixel)
    #print dir(cv_image)
    print len(collection.components), "found, length of", collection.combinedLength()
    sys.exit()

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
    cv_image = pygame_to_cvimage(image)
    #storage = cv.CreateMemStorage(-1)
    #points = detect_faces(cv_image, storage)
    #cv_image = draw_from_points(cv_image, points)
    detect_green(image, cv_image)
    screen.fill([0, 0, 0])
    screen.blit(cvimage_to_pygame(cv_image), (0, 0))
    pygame.display.update()