from __future__ import division
import pygame.midi
import music21
import time
from threading import Thread, Timer
from multiprocessing import Process, Queue
import serial
import re
import math
import sys
import traceback
import collections

def serialTempoWatcher(initTempo, eventQueue):
	ser = serial.Serial("/dev/ttyACM0", 9600)
	line = ""
	hold = False
	historyVector = [0] * 20

	waitThreshold = 20
	waitCount = waitThreshold + 1
	origTime = time.time()
	thresholdCount = 0
	thresholdThreshold = 2
	while(1):
		if shutdown == True:
			break
		try:
			for c in ser.read():
				if c == '\n' or c == '\r':
					if len(re.findall(",", line)) != 2:
						hold = True
					if not hold:
						#move all this to a separate function
						line = line.split(",")
						line = [int(x) for x in line]
						curSum = sum(line)
						historyVector = shift(1, historyVector)
						historyAvg = sum(historyVector)/len(historyVector)
						historyVector[len(historyVector) - 1] = curSum
						if thresholdCount:
							if curSum < 0:
								thresholdCount += 1
							if thresholdCount >= thresholdThreshold:
								waitCount = 0
								eventQueue.put(deltaTime)
								thresholdCount = 0
						elif curSum < 0 and historyAvg > 0 and waitCount > waitThreshold:
							newTime = time.time()

							deltaTime = newTime - origTime

							origTime = newTime
							thresholdCount = 1
						waitCount+=1
					hold = True
					line = ""
				else:
					hold = False
					line += str(c)
		except ValueError as e:
			#move this and IndexError to a separate function as well
			ex_type, ex, tb = sys.exc_info()
			#print "Encountered a ValueError", e
			line = ''
			traceback.print_tb(tb)
		except TypeError as e:
			ex_type, ex, tb = sys.exc_info()
			#print "Encountered a TypeError", e
			line = ''
			traceback.print_tb(tb)

class tempoCalculator(object):
	def __init__(self):
		print "Initiating calculator."
		self.lastBeatTimestamp = time.time()

	def beat(self):
		curBeat = time.time()
		print "current tempo:", 60 / (curBeat - self.lastBeatTimestamp)
		self.lastBeatTimestamp = curBeat

calc = tempoCalculator()
while(1):
	a = raw_input("Beat?")
	calc.beat()