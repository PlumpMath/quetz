#    Quetz development version
#   Copyright (C) 2011 Milan Boers
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import socket
#import threading
import thread
import json
import zlib
import time
import uuid
import random
import math

# Server port
PORT = 44454
# Player timeout
TIMEOUT_TIME = 5
# Admin password
ADMIN_PASS = "Hello!"
# Server welcome message
WELCOME_MESSAGE = "Welcome to Milan's homeserver! Rules don't apply!"

# Nice AI names
AI_NAMES = ["Zubie", "Fin", "Puck"]
# Number of AI's
AI_NUMBER = 1

class PlayerInWorld(object):
	def __init__(self, addr, nickname):
		self.x = 0
		self.y = 0
		self.z = 0
		self.h = 0
		self.tailLength = 0
		
		self.addr = addr
		self.nickname = nickname
	
	def update(self, x, y, z, h, tailLength):
		self.x = x
		self.y = y
		self.z = z
		self.h = h
		
		self.tailLength = tailLength

class AIPlayer(PlayerInWorld):
	def __init__(self, world):
		super(AIPlayer, self).__init__(str(uuid.uuid1()), "[AI] " + random.choice(AI_NAMES))
		
		self.world = world
		self.world.players.append(self)
		
		self.movingToX = 0
		self.movingToY = 0
		
		self.tailLength = 5
		
		self.prevX = 0
		self.prevY = 0
		
		self.index = random.randint(40,60)
		self.sindex = random.randint(-5,5)
		self.sindex2 = random.randint(-5,5)
		
		# Sets the next target
		thread.start_new_thread(self.setTargetThread, ())
		# Moves to the target
		thread.start_new_thread(self.moveToTargetThread, ())
	
	def getClosestPlayer(self):
		closestDist = None
		for player in self.world.players:
			if player.addr <> self.addr:
				distance = abs(self.x - player.x) ** 2 + abs(self.y - player.x) ** 2
				if distance < closestDist or closestDist == None:
					closest = player
					closestDist = distance
		
		return closest
	
	def getHeading(self, x, y):
		dx = self.x - x
		dy = self.y - y
		
		if dx >= 0 and dy >= 0:
			# upper right
			return math.degrees ( math.atan2( abs(dy) , abs(dx) ) ) + 90
		elif dx >= 0 and dy <= 0:
			# lower right
			return math.degrees ( math.atan2( abs(dy) , abs(dx) ) )
		elif dx <= 0 and dy <= 0:
			# lower left
			return math.degrees ( math.atan2( abs(dy) , abs(dx) ) ) - 90
		elif dx <= 0 and dy >= 0:
			# upper left
			return math.degrees ( math.atan2( abs(dy) , abs(dx) ) ) - 180
	
	def setTargetThread(self):
		while True:
			time.sleep(2)
			try:
				self.closestPlayer = self.getClosestPlayer()
				self.movingToX = self.closestPlayer.x + math.sin(math.radians(self.closestPlayer.h)) * self.index + self.sindex
				self.movingToY = self.closestPlayer.y - math.cos(math.radians(self.closestPlayer.h)) * self.index + self.sindex2
			
			except UnboundLocalError:
				# No players
				pass
		
	def moveToTargetThread(self):
		while True:
			time.sleep(0.1)
			# Turn towards the nearest player
			if self.prevX <> self.x and self.prevY <> self.y:
				newHeading = self.getHeading(self.prevX, self.prevY)
				if abs(self.h - newHeading) > 10:
					if self.h > newHeading:
						self.h -= 10
					else:
						self.h += 10
				else:
					self.h = self.getHeading(self.prevX, self.prevY)
			
			# Set prevx and prevy
			self.prevX = self.x
			self.prevY = self.y
			
			# Move towards it
			if abs(self.x - self.movingToX) > 6:
				if self.x > self.movingToX:
					self.x -= 6
				else:
					self.x += 6
			else:
				self.x = self.movingToX
			
			if abs(self.y - self.movingToY) > 6:
				if self.y > self.movingToY:
					self.y -= 6
				else:
					self.y += 6
			else:
				self.y = self.movingToY

		
class World(object):
	"""
	Models the World as it currently looks like on the server
	"""
	def __init__(self):
		self.players = []
	
	def getPlayersNotSelf(self, addr):
		playersNotSelf = []
		for player in self.players:
			# Not the player who is asking
			if player.addr <> addr:
				playersNotSelf.append([player.addr, player.x, player.y, player.z, player.h, player.tailLength])
		
		#return the players
		return playersNotSelf
	
	def getPlayerByName(self, name):
		for player in self.players:
			if player.name == name:
				return player


class ClientConnection(object):
	def __init__(self, udphandler, socket, addr, world):
		self.socket = socket
		self.addr = addr
		self.world = world
		
		self.udphandler = udphandler
		
		self.lastrequest = time.time()
		
		thread.start_new_thread(self.checkTimeout, ())
	
	def addData(self, data):
		self.lastrequest = time.time()
		
		if data == "REQ WORLD":
			# Send the players
			self.socket.sendto("PLAYERS " + zlib.compress(json.dumps(self.world.getPlayersNotSelf(self.addr))), self.addr)
		elif data[0:11] == "SEND PLAYER":
			try:
				position = json.loads(zlib.decompress(data[12:]))
				self.player.update(position[0], position[1], position[2], position[3], position[4])
			except ValueError:
				pass
		elif data[0:2] == "HS":
			# Handshake
			print "HANDSHAKE"
			# Send all the other players to this player
			for player in self.world.players:
				self.socket.sendto("PLAYER " + zlib.compress(json.dumps([player.addr, player.nickname])), self.addr)
			# Send the welcome message
			self.socket.sendto("MSG " + zlib.compress(json.dumps([WELCOME_MESSAGE])), self.addr)
			
			# Add this player to the world
			self.addPlayer(data[3:])
		elif data[0:3] == "MSG":
			# Got a message!
			message = zlib.decompress(data[4:])
			# Is this a command?
			if message[0:1] == "/":
				# This is a command!
				# Is this an admin command?
				if message[1:6] == "admin" and message[7:(7+len(ADMIN_PASS))] == ADMIN_PASS:
					adminCommand = message[8+len(ADMIN_PASS):]
					if adminCommand[0:3] == "MSG":
						# This is an admin message
						self.udphandler.multicast("MSG " + zlib.compress(json.dumps([adminCommand[4:], "ADMIN"])))
					if adminCommand[0:4] == "KICK":
						# Kick a player (by name)
						self.udphandler.removeClient(self.world.getPlayerByName(adminCommand[5:]).addr)
			else:
				# This is a normal message
				self.udphandler.multicast("MSG " + zlib.compress(json.dumps([message, self.player.nickname])))
		elif data[0:4] == "DISC":
			# Player disconnects
			print "PLAYER " + self.player.nickname + " DISCONNECTED"
			self.remove()
	
	def addPlayer(self, nickname):
		self.player = PlayerInWorld(self.addr, nickname)
		self.world.players.append(self.player)
		self.udphandler.multicast("PLAYER " + zlib.compress(json.dumps([self.addr, nickname])), self.addr)
		print "PLAYER " + nickname + " ADDED"
	
	def checkTimeout(self):
		try:
			while True:
				if time.time() - self.lastrequest > TIMEOUT_TIME:
					self.udphandler.removeClient(self.addr)
					print "PLAYER TIMEOUT " + str(self.addr)
					break
		except ValueError:
			# Player already gone
			pass
	
	def remove(self):	
		self.world.players.remove(self.player)


class UDPHandler(object):
	def __init__(self, world, socket):
		self.connectedClients = []
		self.world = world
		self.socket = socket
	
	def handle(self, data, addr):
		for client in self.connectedClients:
			if client.addr == addr:
				client.addData(data)
				break
		else:
			client = self.addClient(addr)
			client.addData(data)
	
	def addClient(self, addr):
		client = ClientConnection(self, self.socket, addr, self.world)
		self.connectedClients.append(client)
		return client
	
	def removeClient(self, addr):
		for client in self.connectedClients:
			if client.addr == addr:
				self.connectedClients.remove(client)
				client.remove()
				break
	
	def multicast(self, msg, addr=None):
		for client in self.connectedClients:
			if addr == None or client.addr <> addr:
				client.socket.sendto(msg, client.addr)

class QuetzServer():
	def __init__(self, port):
		global base
		base = self
		
		print "QUETZ SERVER v 0.01 STARTED"
		
		# Setup the world as it looks like on this server
		world = World()
		print "INITIATED WORLD"
		
		# Setup the socket
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socket.bind(("", port))
		
		self.udphandler = UDPHandler(world, self.socket)
		
		# AI
		for i in xrange(AI_NUMBER):
			AIPlayer(world)
		
		# The daemon
		while True:
			try:
				data, addr = self.socket.recvfrom(1024)
				
				self.udphandler.handle(data, addr)
			except socket.error:
				# something went wrong, but we have to keep on going for all other clients
				self.udphandler.removeClient(addr)
				pass

server = QuetzServer(PORT)