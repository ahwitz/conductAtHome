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

pygame.midi.init()

for x in range(0, pygame.midi.get_count()):
	try:
		player = pygame.midi.Output(x)
	except pygame.midi.MidiException:
		continue
	player.note_on(60, 120)
	time.sleep(0.5)
	player.note_off(60)
	choice = raw_input("Did you hear a note?")
	try:
		choice = int(choice)
		if choice == x:
			break
		elif choice < pygame.midi.get_count():
			del player
			player = pygame.midi.Output(choice)
			break
	except ValueError:
		if choice == "y":
			break
		else:
			del player

def shift(k, a):
    return a[-k:]+a[:-k]

#TODO: add in self.timeTrack beats as beats to average out
#TODO: let it skip beats or conduct in 2/4

def tempoWatcher(initTempo, eventQueue):
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



		#the second it changes from positive to negative is the icthus

		#the distance between positive and negative refers to how staccato it is


#class ScorePlayer(Thread):
class ScorePlayer():

	def __init__(self, scoreIn):
		self.score = scoreIn
		self.duration = self.score.duration.quarterLength

		self.tempo = 120
		self.tempoHistoryLength = 5
		self.tempoHistory = [(self.tempo, 1)] * self.tempoHistoryLength
		self.lastTimingTrackVal = 120

		self.shutdown = False
		
		self.timingTrack = {}
		self.tempoMult = 1
		self.noteOnCalls = {}
		self.noteOffCalls = {}
		self.temposCalled = []
		self.noteOnCalled = []
		self.noteOffCalled = []
		
		self.channels = {}
		for x in range(0, 16):
			self.channels[x] = ""
		self.noteCount = {}

		self.notesPlayed = {}
		self.deleteFails = 0

		#p1 = Process(target=self.run())
		#p.start()

	def findChannel(self):
		for (x, y) in self.channels.iteritems():
			if y == "":
				return x
		for x in range(0, 16):
			self.channels[x] = ""
		return 0


	def createNote(self, curObj):
		#print "creating", curObj, (curObj.duration.quarterLength * self.tempo)
		player.note_on(curObj.midi, curObj.volume.velocity, curObj.channel)
		try:
			self.noteOffCalls[curObj.offset + curObj.duration.quarterLength].append(curObj)
		except KeyError:
			self.noteOffCalls[curObj.offset + curObj.duration.quarterLength] = [curObj]

		try:
			self.notesPlayed[curObj.channel].append(curObj.midi)
		except KeyError:
			self.notesPlayed[curObj.channel] = [curObj]

	def stopNote(self, curObj):
		#print "stopping", curObj
		player.note_off(curObj.midi, curObj.volume.velocity, curObj.channel)
		try:
			self.notesPlayed[curObj.channel].remove(curObj)
		except:
			#print "delete failed"
			self.deleteFails += 1

	def addNote(self, curObj):
		try:
			self.noteOnCalls[curObj.offset].append(curObj)
			#self.noteOffCalls[curObj.offset + curObj.duration.quarterLength].append(curObj)
		except KeyError:
			self.noteOnCalls[curObj.offset] = [curObj]
			#self.noteOffCalls[curObj.offset + curObj.duration.quarterLength] = [curObj]

	def processTrack(self, curPart):
		curPart.channel = self.findChannel()
		self.channels[curPart.channel] = "Taken."
		self.noteCount[curPart.channel] = 0
		print "Processing track", curPart.channel
		for curObj in curPart:
			try:
				player.set_instrument(curPart.getInstrument().midiProgram, curPart.channel)
			except TypeError: #can't find instrument, we'll just assume piano
				pass
			if self.shutdown == True:
				break
			if isinstance(curObj, music21.tempo.MetronomeMark): #if it's a tempo change
				#if curObj.offset < 5:
					#print "Found a tempo change", curObj.number, "at", curObj.offset
				try:
					self.timingTrack[curObj.offset] = curObj.number
				except KeyError:
					self.timingTrack[curObj.offset] = curObj.number
			elif isinstance(curObj, music21.note.Note):
				curObj.channel = curPart.channel
				self.addNote(curObj)
				self.noteCount[curPart.channel] += 1

			elif isinstance(curObj, music21.meter.TimeSignature):
				#this will eventually be important to me
				pass
			elif isinstance(curObj, music21.chord.Chord):
				for curNote in curObj:
					if curNote.offset == 0:
						curNote.offset = curObj.offset
					curNote.channel = curPart.channel
					self.addNote(curNote)
					self.noteCount[curPart.channel] += 1
			elif isinstance(curObj, music21.stream.Voice):
				print "Found a new voice on channel", curPart.channel
				self.processTrack(curObj) #YAY RECURSIVENESS

			else:
				pass
				#print "found a new one", curObj
		if self.noteCount[curPart.channel] == 0:
			self.channels[curPart.channel] = ""
			print "Resetting channel", curPart.channel
	
	def run(self):
		#pre-processing here, loads all notes into one track
		for curPart in self.score:
			self.processTrack(curPart)

		print "Done with processing."
		player.note_on(60, 120)
		time.sleep(0.25)
		player.note_off(60)
		elapsedTime = self.duration + 1
		try:
			elapsedTime = raw_input("This track lasts "+str(self.duration)+" beats.\nEnter a number to pick a start time or anything else to start at the beginning.")
			while(int(elapsedTime) > self.duration):
				elapsedTime = raw_input("Please enter a value lower than the total duration.")
			print "Starting at beat "+elapsedTime+"."
		except ValueError: #if a non-int is entered
			print "Starting at zero."
			elapsedTime = 0

		print len(self.timingTrack), self.timingTrack
		if len(self.timingTrack) >= 1:
			firstTempo = self.timingTrack[min(self.timingTrack)]
			self.tempoHistory = [(firstTempo, 1)] * self.tempoHistoryLength
		else:
			pass
		try:
			tempoMult = raw_input("Initial tempo is "+str(firstTempo)+". Please enter a tempo divider (2 for half-time, etc.)")
			
		except ValueError:
			print "Defaulting to 1."
			tempoMult = 1

		self.tempoMult = 3

		elapsedTime = int(elapsedTime)
		
		self.updateNotes(elapsedTime, False)

		eventQueue = Queue()
		orderedTiming = [(a, b) for (a, b) in collections.OrderedDict(sorted(self.timingTrack.items())).iteritems()]
		startTempo = orderedTiming[0][1]
		p = Process(target=tempoWatcher, args=(startTempo, eventQueue)) 
		p.start()

		oldTime = time.time()
		while(1): #waits for a beat
			if not eventQueue.empty():
				newTempo = eventQueue.get()
				self.updateTempo(newTempo, True)
				break
		print "Got the downbeat - going!"
		while elapsedTime < self.duration:
			if self.shutdown == True:
				self.shutDown()

			self.updateNotes(elapsedTime, True)

			if not eventQueue.empty():
				newTempo = eventQueue.get()
				self.updateTempo(newTempo, True)
			
			newTime = time.time()
			elapsedTime += (newTime - oldTime)*(self.tempo/60)
			oldTime = newTime

		p.join()
		self.shutDown()

	def updateNotes(self, elapsedTime, play):
		for curOffset in self.timingTrack:
			if (elapsedTime >= curOffset):
				#print elapsedTime, curOffset
				if play:
					self.updateTempo(self.timingTrack[curOffset])
				self.temposCalled.append(curOffset)

		for curOffset in self.noteOffCalls:
			if (elapsedTime >= curOffset):
				#print elapsedTime, curOffset
				if play:
					for curNote in self.noteOffCalls[curOffset]:
						self.stopNote(curNote)
				self.noteOffCalled.append(curOffset)

		for curOffset in self.noteOnCalls:
			if (elapsedTime >= curOffset):
				#print elapsedTime, curOffset
				if play:
					for curNote in self.noteOnCalls[curOffset]:
						self.createNote(curNote)
				self.noteOnCalled.append(curOffset)
		
		for curOffset in self.noteOffCalled:
			del self.noteOffCalls[curOffset]
		self.noteOffCalled = []
		for curOffset in self.noteOnCalled:
			del self.noteOnCalls[curOffset]
		self.noteOnCalled = []
		for curOffset in self.temposCalled:
			del self.timingTrack[curOffset]
		self.temposCalled = []

	def updateTempo(self, newTempo, deltaTime = False):
		weight = 1
		idealTempo = self.weightedTempoAvg()# + self.lastTimingTrackVal)/2 #this should be an average
		print "ideal tempo:", idealTempo
		if deltaTime: #normalizes tempo, assuming you're trying to beat a specific multiple of the tempo
			newTempo = (60/newTempo)
			origNewTempo = newTempo
			if newTempo > idealTempo:
				print origNewTempo,":", newTempo, "vs", idealTempo
				if newTempo > (1.5*idealTempo):
					for x in range(1, 10):
						newTempo = origNewTempo/x
						if newTempo < (1.5*idealTempo):
							break
						print "newTempo is now", newTempo

				weight = math.fabs(idealTempo - newTempo)/idealTempo
			else:
				print newTempo, "vs", idealTempo, origNewTempo
				if newTempo < (.75*idealTempo):
					for x in range(1, 10):
						newTempo = origNewTempo*x
						if newTempo > (.75*idealTempo):
							break
						print "newTempo is now", newTempo
				weight = math.fabs(idealTempo - newTempo)/idealTempo
			#newTempo = newTempo * self.tempoMult

		else: #if it's built into the track
			maxTimingTrackWeight = 10 #is the maximum weight of a timing track tempo.
			evenWeightThreshold = 15 #for every this many the new timing track is away from the last one, it gets one point of weight. this helps weigh bigger tempo changes.
			weight = min(maxTimingTrackWeight, math.fabs(self.lastTimingTrackVal - newTempo)/evenWeightThreshold)
			self.lastTimingTrackVal = int(newTempo)
		
		self.tempoHistory[len(self.tempoHistory) - 1] = (newTempo, weight)
		self.tempoHistory = shift(1, self.tempoHistory)

		averageTempo = self.weightedTempoAvg()
		self.tempo = averageTempo
		print "New average tempo:", averageTempo

	def weightedTempoAvg(self):
		return sum([a*b for (a, b) in self.tempoHistory])/sum([b for (a, b) in self.tempoHistory])		

	def shutDown(self):
		#clear all notes sounding
		for curNote in self.notesPlayed:
			self.stopNote(curNote)
			
		print self.notesPlayed, self.deleteFails


#TODO: at some point, code here to pick other files
print "Parsing file."
score = music21.converter.parse('/home/ahwitz/development/python/sweetheart.mid')
#tempoWatcher = TempoWatcher()
shutdown = False
scorePlayer = ScorePlayer(score)
scorePlayer.run()

duration = score.duration

try:
	while(1):
		pass
except KeyboardInterrupt, e:
	scorePlayer.shutdown = True
	shutdown = True
	#tempoWatcher.shutdown = True