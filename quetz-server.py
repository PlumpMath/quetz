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
import threading
import thread
import json
import zlib
import time
import SocketServer

PORT = 44454
TIMEOUT_TIME = 1

class PlayerInWorld(object):
	def __init__(self, addr, nickname):
		self.x = 0
		self.y = 0
		self.z = 0
		self.h = 0
		self.tailLength = 0
		
		self.addr = addr
		self.nickname = nickname

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
				self.updatePlayer(position[0], position[1], position[2], position[3], position[4])
			except ValueError:
				pass
		elif data[0:2] == "HS":
			# Handshake
			print "HANDSHAKE"
			# Send all the other players to this player
			for player in self.world.players:
				self.socket.sendto("PLAYER " + zlib.compress(json.dumps([player.addr, player.nickname])), self.addr)
			
			# Add this player to the world
			self.addPlayer(data[3:])
		elif data[0:3] == "MSG":
			self.udphandler.multicast("MSG " + zlib.compress(json.dumps([zlib.decompress(data[4:]), self.player.nickname])))
	
	def updatePlayer(self, x, y, z, h, tailLength):
		self.player.x = x
		self.player.y = y
		self.player.z = z
		self.player.h = h
		
		self.player.tailLength = tailLength
	
	def addPlayer(self, nickname):
		self.player = PlayerInWorld(self.addr, nickname)
		self.world.players.append(self.player)
		self.udphandler.multicast("PLAYER " + zlib.compress(json.dumps([self.addr, nickname])), self.addr)
		print "PLAYER " + nickname + " ADDED"
	
	def removePlayer(self):
		self.world.players.remove(self.player)
		print "PLAYER " + self.player.nickname + " KICKED"
	
	def checkTimeout(self):
		while True:
			if time.time() - self.lastrequest > TIMEOUT_TIME:
				self.remove()
				print "PLAYER TIMEOUT " + str(self.addr)
				break
	
	def remove(self):
		self.removePlayer()
		self.udphandler.connectedClients.remove(self)


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
				client.remove()
				self.connectedClients.remove(client)
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