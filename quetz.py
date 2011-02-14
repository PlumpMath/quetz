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

import uuid
import sys
import socket
import json
import zlib
# According to the manual of Panda3D, this is unsafe. But seeing that the Panda3D threads are actually fake, I still use these.
import threading
import thread
import time

import menu

import worlds.NormalMap
import worldObjects
import modules.joypad

from math import pi, sin, cos

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from pandac.PandaModules import AntialiasAttrib, NodePath, SmoothMover, WindowProperties, ClockObject, TextProperties, TextPropertiesManager
from panda3d.core import Point3, Vec3, CollisionSphere, CollisionNode, CollisionHandlerEvent, CollisionTraverser, CollisionHandlerPusher

from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from direct.gui.DirectGuiBase import DirectGuiWidget
from direct.showbase.DirectObject import DirectObject
 
from pandac.PandaModules import TextNode

import modules.joypad

# Distance between tail objects
TAILOBJ_DIST    = 5
# Interval between network updates
UPDATE_INTERVAL = 0.15

# UI
class OST(object):
	def __init__(self):
		# Chattext
		self.chatText = TextNode("chatText")
		self.chatText.setWordwrap(45.0)
		self.chats = []
		self.chatText.setText("")
		self.chatText.setCardColor(0.2, 0.2, 0.2, 0.2)
		self.chatText.setCardAsMargin(0.4, 0.4, 0.2, 0.2)
		self.chatText.setCardDecal(True)
		
		tpRed = TextProperties()
		tpRed.setTextColor(0.7, 0, 0, 1)
		tpWhite = TextProperties()
		tpWhite.setTextColor(1, 1, 1, 1)
		tpBlue = TextProperties()
		tpBlue.setTextColor(0, 0, 0.7, 1)
		
		tpMgr = TextPropertiesManager.getGlobalPtr()
		tpMgr.setProperties("red", tpRed)
		tpMgr.setProperties("white", tpWhite)
		tpMgr.setProperties("blue", tpBlue)
		
		textNodePath = aspect2d.attachNewNode(self.chatText)
		textNodePath.setPos(-1.25, 0, -0.45)
		textNodePath.setScale(0.05)
		
		# Enterchat
		self.enterChat = DirectEntry(text = "", scale=.04, command=self.sendChat, focus=0, pos=(-1.25, 0, -0.95), width=63, text_fg=(1,1,1,1), frameColor=(0.2, 0.2, 0.2, 0.0), relief=3, borderWidth=(0.1, 0.1), parent=aspect2d, sortOrder=1)
		
		# Task for mouse
		base.taskMgr.add(self.mouseWatcher, "mouseWatcher", sort=5)
		
		# Key events
		base.accept("enter", self.toggleFocusChat)
	
	def toggleFocusChat(self):
		self.enterChat['focus'] = not self.enterChat['focus']
		if self.enterChat['focus']:
			self.enterChat['frameColor'] = (0.2, 0.2, 0.2, 0.8)
		else:
			self.enterChat['frameColor'] = (0.2, 0.2, 0.2, 0.0)
	
	def sendChat(self, textEntered):
		if textEntered <> "":
			self.enterChat.enterText("")
			base.serverConnection.sendChat(textEntered)
	
	def mouseWatcher(self, task):
		if base.mouseWatcherNode.hasMouse():
			if base.mouseWatcherNode.getMouseY() < -0.3:
				self.chatText.setCardColor(0.2, 0.2, 0.2, 0.9)
			else:
				self.chatText.setCardColor(0.2, 0.2, 0.2, 0.2)
		return Task.cont
	
	def addChat(self, msg, color="white", name=None):
		# Add this message to the chats
		if name == None:
			self.chats.append("\n\1" + color + "\1" + msg + "\2")
		else:
			self.chats.append("\n" + name + ": \1white\1" + msg + "\2")
		
		# Delete old chats
		if len(self.chats) > 8:
			del self.chats[0]
		
		# Place the chats into the text
		text = ""
		for chat in self.chats:
			text += chat
		
		self.chatText.setText(text)
		
	# Controls onscreen text	
	def showMessage(self, msg, secs):
		try:
			self.timer.cancel()
			self.message.destroy()
		except AttributeError:
			pass
		self.message = OnscreenText(text = msg, scale = .15, pos = ( 0,0), fg=(1,0,0,1), shadow=(0,0,0,0.5), parent=aspect2d)
		self.timer = threading.Timer(secs, self.removeMessage)
		self.timer.start()
	
	def removeMessage(self):
		self.message.destroy()
# END UI

# JOYPAD CONTROL
class JoypadControl():
	def __init__(self, playerActor):
		self.playerActor = playerActor
		#threading.Thread.__init__(self)
		#self.daemon = True
		
	def start(self):
		base.taskMgr.add(self.run, "joypadControl", sort=1)
	
	def run(self, task):
		#while True:
		#task.delayTime = 0.01
		# Store the x and y worths of all the joypads in this list, to calculate the avarage
		
		xA = []
		yA = []
		# Try every joypad
		try:
			xA.append(base.joypad.c1.get_axis(0))
			yA.append(base.joypad.c1.get_axis(1))
			try:
				xA.append(base.joypad.c2.get_axis(0))
				yA.append(base.joypad.c2.get_axis(1))
				try:
					xA.append(base.joypad.c3.get_axis(0))
					yA.append(base.joypad.c3.get_axis(1))
					try:
						xA.append(base.joypad.c4.get_axis(0))
						yA.append(base.joypad.c4.get_axis(1))
					except:
						pass
				except:
					pass
			except:
				pass
			# Calculate the avarage
			x = sum(xA) / len(xA)
			y = sum(yA) / len(yA)
		except:
			# First joypad not connected. Let's stop then.
			return Task.done
			#break
		# Change the position (if the keys are not pressed)
		if not self.playerActor.walkingByKeys:
			self.playerActor.changePosition(x, y)
		#time.sleep(0.01)
		return Task.cont
# END JOYPAD CONTROL

# PLAYER OBJECTS
class PlayerActor(Actor):
	"""
	The player
	"""
	def __init__(self, nickname):
		super(PlayerActor,self).__init__("models/panda-model", {"walk":"models/panda-walk4"})
		self.setScale(0.005, 0.005, 0.005)
		self.reparentTo(base.render)
		
		self.walking = False
		self.walkingByKeys = False
		
		# Some properties
		self.lives = 3
		self.invincible = True
		self.nickname = nickname
		
		# Create the nickname label
		text = TextNode("nicknameLabel")
		text.setText(self.nickname)
		text.setTextColor(1, 0, 0, 1)
		self.nicknameLabel = NodePath(text)
		self.nicknameLabel.reparentTo(base.render)
		
		# Create the tail, not tangible
		self.tail = Tail(self)
		
		# Add tasks
		base.taskMgr.add(self.walkPlayerTask, "walkPlayerTast")
		base.taskMgr.add(self.moveNickLabel, "moveNickLabel")
		
		# Add invincibility
		thread.start_new_thread(self.makeInvincible, (5,))
		
		# Create collision solid for playerActor
		cs = CollisionSphere(0, 0, 200, 400)
		cnodePath = self.attachNewNode(CollisionNode('playerActor'))
		cnodePath.node().addSolid(cs)
		#cnodePath.show()
		
		# Add to the pusher
		base.pusher.addCollider(cnodePath, self)
		base.cTrav.addCollider(cnodePath, base.pusher)
		
		# Key events
		base.accept("w",self.movePlayerForward)
		base.accept("w-up",self.stopMovePlayerForward)
		base.accept("a",self.rotatePlayerLeft)
		base.accept("a-up",self.stopRotatePlayerLeft)
		base.accept("d",self.rotatePlayerRight)
		base.accept("d-up",self.stopRotatePlayerRight)
		base.accept("s",self.movePlayerBackward)
		base.accept("s-up",self.stopMovePlayerBackward)
		
		# Joypad events
		base.accept("C1_NORTH-BUTTON_DOWN", self.movePlayerForward)
		base.accept("C1_NORTH-BUTTON_UP", self.stopMovePlayerForward)
		base.accept("C1_SOUTH-BUTTON_DOWN", self.movePlayerBackward)
		base.accept("C1_SOUTH-BUTTON_UP", self.stopMovePlayerBackward)
		base.accept("C1_EAST-BUTTON_DOWN", self.rotatePlayerRight)
		base.accept("C1_EAST-BUTTON_UP", self.stopRotatePlayerRight)
		base.accept("C1_WEST-BUTTON_DOWN", self.movePlayerBackward)
		base.accept("C1_WEST-BUTTON_UP", self.stopMovePlayerBackward)
		
		base.accept("C2_NORTH-BUTTON_DOWN", self.movePlayerForward)
		base.accept("C2_NORTH-BUTTON_UP", self.stopMovePlayerForward)
		base.accept("C2_SOUTH-BUTTON_DOWN", self.movePlayerBackward)
		base.accept("C2_SOUTH-BUTTON_UP", self.stopMovePlayerBackward)
		base.accept("C2_EAST-BUTTON_DOWN", self.rotatePlayerRight)
		base.accept("C2_EAST-BUTTON_UP", self.stopRotatePlayerRight)
		base.accept("C2_WEST-BUTTON_DOWN", self.movePlayerBackward)
		base.accept("C2_WEST-BUTTON_UP", self.stopMovePlayerBackward)
		
		base.accept("C3_NORTH-BUTTON_DOWN", self.movePlayerForward)
		base.accept("C3_NORTH-BUTTON_UP", self.stopMovePlayerForward)
		base.accept("C3_SOUTH-BUTTON_DOWN", self.movePlayerBackward)
		base.accept("C3_SOUTH-BUTTON_UP", self.stopMovePlayerBackward)
		base.accept("C3_EAST-BUTTON_DOWN", self.rotatePlayerRight)
		base.accept("C3_EAST-BUTTON_UP", self.stopRotatePlayerRight)
		base.accept("C3_WEST-BUTTON_DOWN", self.movePlayerBackward)
		base.accept("C3_WEST-BUTTON_UP", self.stopMovePlayerBackward)
		
		base.accept("C4_NORTH-BUTTON_DOWN", self.movePlayerForward)
		base.accept("C4_NORTH-BUTTON_UP", self.stopMovePlayerForward)
		base.accept("C4_SOUTH-BUTTON_DOWN", self.movePlayerBackward)
		base.accept("C4_SOUTH-BUTTON_UP", self.stopMovePlayerBackward)
		base.accept("C4_EAST-BUTTON_DOWN", self.rotatePlayerRight)
		base.accept("C4_EAST-BUTTON_UP", self.stopRotatePlayerRight)
		base.accept("C4_WEST-BUTTON_DOWN", self.movePlayerBackward)
		base.accept("C4_WEST-BUTTON_UP", self.stopMovePlayerBackward)
		
		# Other events
		
		# Axis task
		joypadcontrol = JoypadControl(self)
		joypadcontrol.start()
	
	def remove(self):
		base.taskMgr.remove("walkPlayerTast")
		base.taskMgr.remove("moveNickLabel")
		self.tail.remove()
		self.removeNode()
	
	def loseLife(self, byPlayer = None):
		if not self.invincible:
			if self.lives == 0:
				self.die()
			else:
				self.lives -= 1
				if byPlayer <> None:
					base.ost.addChat("Quetzt by " + byPlayer + "! Lives left: " + str(self.lives) + "!", "red")
				else:
					base.ost.addChat("Quetzt! Lives left: " + str(self.lives) + "!", "red")
				thread.start_new_thread(self.makeInvincible, (3,))
	
	def die(self):
		base.ost.showMessage("YOU DIE!", 5)
	
	def moveNickLabel(self, task):
		self.nicknameLabel.setPos(self.getX(), self.getY(), 3)
		self.nicknameLabel.setHpr(base.camera, 0, 0, 0)
		return Task.cont
	
	def changePosition(self, x, y):
		if x > 1:
			x = 1
		elif x < -1:
			x = -1
		if y > 0.3:
			y = 0.3
		elif y < -1:
			y = -1
		self.setPos(self, 0, y * 300, 0)
		self.setHpr(self, x * -1.5, 0, 0)
	
	def walkPlayerTask(self, task):
		"""
		Controls the character's animtation on walking
		"""
		myAnimControl = self.getAnimControl("walk")
		if self.walking and myAnimControl.isPlaying() == 0:
			self.loop("walk")
		elif not self.walking and myAnimControl.isPlaying() == 1:
			self.stop("walk")
		return Task.cont
	
	def makeInvincible(self, secs):
		self.invincible = True
		for i in xrange(secs):
			base.ost.showMessage(str(secs-i), 1)
			time.sleep(1)
		base.ost.showMessage("START", 2)
		self.invincible = False
		time.sleep(2)
	
	"""
	These methods add tasks for moving to the taskmanager
	"""
	def movePlayerForward(self):
		base.taskMgr.add(self.moveForwardTask, "movePlayerForwardTask")
	
	def movePlayerBackward(self):
		base.taskMgr.add(self.moveBackwardTask, "movePlayerBackwardTask")
	
	def rotatePlayerLeft(self):
		base.taskMgr.add(self.rotateLeftTask, "rotatePlayerLeftTask")
	
	def rotatePlayerRight(self):
		base.taskMgr.add(self.rotateRightTask, "rotatePlayerRightTask")
		
	"""
	These methods remove tasks for moving from the taskmanager
	"""
	def stopMovePlayerForward(self):
		self.walking = False
		self.walkingByKeys = False
		base.taskMgr.remove("movePlayerForwardTask")
	
	def stopMovePlayerBackward(self):
		self.walking = False
		self.walkingByKeys = False
		base.taskMgr.remove("movePlayerBackwardTask")
		
	def stopRotatePlayerLeft(self):
		self.walking = False
		self.walkingByKeys = False
		base.taskMgr.remove("rotatePlayerLeftTask")
		
	def stopRotatePlayerRight(self):
		self.walking = False
		self.walkingByKeys = False
		base.taskMgr.remove("rotatePlayerRightTask")
	
	"""
	These methods move the playerActor
	"""
	def moveForwardTask(self, task):
		"""
		Task: Move the Player forward
		"""
		self.walking = True
		self.walkingByKeys = True
		self.changePosition(0, -1)
		return Task.cont
	
	def moveBackwardTask(self, task):
		"""
		Task: Move the Player backwards
		"""
		self.walking = True
		self.walkingByKeys = True
		self.changePosition(0, 1)
		return Task.cont
	
	def rotateLeftTask(self, task):
		"""
		Task: Rotate the Player to the left
		"""
		self.walking = True
		self.walkingByKeys = True
		self.changePosition(-1, 0)
		return Task.cont
	
	def rotateRightTask(self, task):
		"""
		Task: Rotate the Player to the right
		"""
		self.walking = True
		self.walkingByKeys = True
		self.changePosition(1, 0)
		return Task.cont

class Tail(object):
	def __init__(self, followObj):
		self.path = []
		self.tailObjects = []
		self.followObj = followObj
		
		self.taskId = uuid.uuid1()
		base.taskMgr.add(self.savePath, str(self.taskId))
	
	def addObject(self):
		"""
		Add a TailObject to this tail
		"""
		tailObject = TailObject(self, len(self.tailObjects))
		tailObject.reparentTo(base.render)
		self.tailObjects.append(tailObject)
		
	def removeObject(self, tailObject):
		"""
		Removes an object from the tail
		"""
		base.taskMgr.remove(str(self.taskId))
		tailObject.remove()
		self.tailObjects.remove(tailObject)
	
	def setObjects(self, number):
		change = abs(number - len(self.tailObjects))
		if number > len(self.tailObjects):
			for i in xrange(change):
				self.addObject()
		elif number < len(self.tailObjects):
			for i in xrange(change):
				self.removeObject()
	
	def updateTail(self):
		"""
		Updates the position of all TailObjects
		"""
		for tailObj in self.tailObjects:
			tailObj.updatePosition()
	
	def savePath(self, task):
		"""
		Task: Saves the path of the followed, so the snake can follow
		"""
		try:
			self.path.append(self.followObj.getPos())
			# Delete the path thats unnecessary for this length of tail, but keep it at a minimum of 10 (for networking)
			if len(self.path) > len(self.tailObjects) * TAILOBJ_DIST + 10:
				del self.path[0]
			# Update the tail
			self.updateTail()
		except AttributeError:
			# Tail not long enough. Just ignore this
			pass
		except AssertionError:
			# Player is gone, but task is still running. Delete the player.
			self.followObj.remove()
			return Task.done
		return Task.cont
	
	def remove(self):
		base.taskMgr.remove(str(self.taskId))
		for tailObj in self.tailObjects:
			tailObj.remove()

class TailObject(NodePath):
	"""
	One of the objects behind the player which together make the tail
	"""
	def __init__(self, tail, position):
		np = loader.loadModel("models/smiley")
		node = np.node()
		NodePath.__init__(self, node)
		
		self.tail = tail
		#number in the row of tailobjects
		self.position = position
		
		self.id = uuid.uuid1()
		
		#sphere
		self._addCollider()
		
		## Oops. Problem. You crashed into someone else.
		base.accept(str(self.id) + "-into-playerActor", self.playerActorDies)
	
	def playerActorDies(self, event):
		#print self.tail.followObj
		if self.tail.followObj <> base.playerActor:
			base.playerActor.loseLife(self.tail.followObj.nickname)
	
	def _addCollider(self):
		cs = CollisionSphere(0,0,0,2)
		cs.setTangible(False)
		cnodePath = self.attachNewNode(CollisionNode(str(self.id)))
		cnodePath.node().addSolid(cs)
		#cnodePath.show()
		
		base.cTrav.addCollider(cnodePath, base.collHandEvent)
	
	def updatePosition(self):
		"""
		Update the position of this tail object
		"""
		try:
			index = -((self.position+1)*TAILOBJ_DIST)
			self.setPos(*self.tail.path[index] + (0,0,1))
		except IndexError:
			self.setPos(self.tail.path[0])
	
	def remove(self):
		self.removeNode()

class OtherPlayer(NodePath):
	"""
	Another player in the world (either AI or networking)
	"""
	def __init__(self, addr=None, nickname=None):
		np = loader.loadModel("models/panda-model")
		node = np.node()
		NodePath.__init__(self, node)
		
		# Tuple (ip, port)
		self.addr = addr
		
		self.nickname = nickname
		self.id = uuid.uuid1()
		
		print "NEW PLAYER! " + str(self.nickname)
		
		# Create the smooth mover
		self.smoothMover = SmoothMover()
		self.smoothMover.setPredictionMode(1)
		self.smoothMover.setSmoothMode(1)
		
		# Create the nickname label
		text = TextNode("nicknameLabel")
		text.setText(self.nickname)
		text.setTextColor(1, 0, 0, 1)
		self.nicknameLabel = NodePath(text)
		self.nicknameLabel.reparentTo(base.render)
		
		# Create collision solid for other player
		cs = CollisionSphere(0, 0, 200, 400)
		cnodePath = self.attachNewNode(CollisionNode('otherPlayer'))
		cnodePath.node().addSolid(cs)
		#cnodePath.show()
		
		# Add to the pusher
		base.pusher.addCollider(cnodePath, self)
		base.cTrav.addCollider(cnodePath, base.pusher)
		
		# Tail
		self.tail = Tail(self)
		
		# Tasks
		base.taskMgr.add(self.moveNickLabel, str(self.id) + "-moveNickLabel")
	
	def moveNickLabel(self, task):
		try:
			self.nicknameLabel.setPos(self.getX(), self.getY(), 3)
			self.nicknameLabel.setHpr(base.camera, 0, 0, 0)
		except AssertionError:
			# Player gone but task still running?
			self.remove()
			return Task.done
		return Task.cont
	
	def remove(self):
		base.taskMgr.remove(str(self.id) + "-moveNickLabel")
		self.tail.remove()
		self.nicknameLabel.removeNode()
		self.removeNode()
# END PLAYER OBJECTS

# NETWORKING
class ServerConnection():
	"""
	Connection to a server
	"""
	def __init__(self, server):
		#threading.Thread.__init__(self)
		#super(ServerConnection, self).__init__(self)
		
		self.timer = time.time()
		
		#stores all the other players
		self.otherplayers = []
		
		self.port = 44454
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		
		self.server = server
		#threading.Thread.__init__(self)
		
		# Handshake
		print "send hs"
		self.socket.sendto("HS " + base.playerActor.nickname, (self.server, self.port))
		print "endsend hs"
		
		base.taskMgr.add(self.run, "run")
		base.taskMgr.add(self.movePlayers, "movePlayers")
		
		self.daemon = True
	
	def run(self, task):
		"""
		This is what the server does every UPDATE_INTERVAL seconds
		"""
		task.delayTime = UPDATE_INTERVAL
		try:
			
			# Send the current player position/heading
			try:
				playerActorPos = zlib.compress(json.dumps([base.playerActor.getX(),base.playerActor.getY(),base.playerActor.getZ(),base.playerActor.getH(),len(base.playerActor.tail.tailObjects)]))
				self.socket.sendto(b'SEND PLAYER ' + playerActorPos, (self.server, self.port))
			except socket.error:
				print "Huh what happened?"
			
			# Ask for the world
			self.socket.sendto(b'REQ WORLD', (self.server, self.port))
			
			data = self.socket.recv(1024)
			
			if data[0:7] == "PLAYERS":
				# Got the world back!
				players = json.loads(zlib.decompress(data[8:]))
				self.placeOtherPlayers(players)
			elif data[0:6] == "PLAYER":
				# Got a new player!
				dataD = json.loads(zlib.decompress(data[7:]))
				self.addPlayer(dataD[0], dataD[1])
			#elif data[0:6] == "PLAYEL":
			#	# Player left
			#	dataD = json.loads(zlib.decompress(data[7:]))
			#	self.removePlayer(self.getPlayerByAddr(dataD))
			elif data == "KICKED":
				# Hey! I'm kicked!?
				print "You were kicked from the server."
			elif data[0:3] == "MSG":
				# Gets (msg, nick)
				msgandnick = json.loads(zlib.decompress(data[4:]))
				if len(msgandnick) == 2:
					base.ost.addChat(msgandnick[0], msgandnick[1])
				else:
					base.ost.addChat(msgandnick[0])
			
		except socket.error:
			print "Connection lost."
			return Task.done
		return Task.again
	
	def sendChat(self, chatmsg):
		"""
		Send a chatmessage to the server
		"""
		self.socket.sendto("MSG " + zlib.compress(chatmsg), (self.server, self.port))
	
	def placeOtherPlayers(self, players):
		"""
		Place all the players you got via the network into the world
		"""
		
		# Try to remove players that don't exist anymore
		for playerlocal in self.otherplayers:
			found = False
			for playerserver in players:
				if playerlocal.addr == playerserver[0]:
					found = True
			if not found:
				self.removePlayer(playerlocal)
		
		# Update all players
		for player in players:
			self.updatePlayer(player[0], player[1], player[2], player[3], player[4], player[5])
	
	#def getPlayerByAddr(self, addr):
	#	for player in self.otherplayers:
	#		if player.addr == addr:
	#			return player
	
	def removePlayer(self, player):
		"""
		Remove a player from the world
		"""
		self.otherplayers.remove(player)
		player.remove()
	
	def updatePlayer(self, addr, cx, cy, cz, h, tailLength):
		"""
		Update a player, or add it when it's not yet there
		"""
		# Check if the player is already there
		for player in self.otherplayers:
			if player.addr == addr:
				# Update the position/heading smoothly
				player.smoothMover.setPos(Point3(cx, cy, cz))
				player.smoothMover.setHpr(Vec3(h, 0, 0))
				player.smoothMover.setTimestamp(globalClock.getFrameTime())
				player.smoothMover.markPosition()
				
				# Update the tail
				player.tail.setObjects(tailLength)
		
	def addPlayer(self, addr, nickname):
		newPlayer = OtherPlayer(addr, nickname)
		newPlayer.reparentTo(base.render)
		newPlayer.setScale(0.005, 0.005, 0.005)
		self.otherplayers.append(newPlayer)
		base.ost.addChat("Player " + nickname + " connected", "blue")
	
	def movePlayers(self, task):
		"""
		Updates all the other players in the environment
		"""
		for player in self.otherplayers:
			player.smoothMover.computeAndApplySmoothPosHpr(player, player)
		return Task.cont
	
	def close(self):
		self.socket.sendto("DISC", (self.server, self.port))
		self.socket.close()
# END NETWORKING

# MAIN APPLICATION
class Quetz(ShowBase):
	"""
	The game itself
	"""
	def __init__(self):
		ShowBase.__init__(self)
		
		menu.MainMenuWidget()
	
	def startGame(self, server = None, nickname = None):		
		self.cameraDistance = 8000
		self.cameraAngle = 0
		self.cameraBirdview = 1700
		self.secondCamera = None
		
		# Set options
		self.render.setAntialias(AntialiasAttrib.MAuto)
		base.disableMouse()
		
		# Fixed framerate
		globalClock.setMode(ClockObject.MLimited)
		globalClock.setFrameRate(40)
		
		# Load the onscreentext
		base.ost = OST()
		
		# Get the world
		map = worlds.NormalMap.World()
		
		# Load the world
		base.render.setFog(map.fog)
		self.setBackgroundColor(map.bgcolor)
		
		# Set colission traverser
		base.cTrav = CollisionTraverser()
		self.collHandEvent = CollisionHandlerEvent()
		self.collHandEvent.addInPattern('%fn-into-%in')
		self.collHandEvent.addAgainPattern('%fn-again-%in')
		self.collHandEvent.addOutPattern('%fn-out-%in')
		
		self.pusher = CollisionHandlerPusher()
		
		# Load environment
		self.environ = base.loader.loadModel(map.map)
		self.environ.reparentTo(self.render)
		self.environ.setScale(*map.scale)
		
		# Load catchables
		self.catchables = []
		for catchable in map.catchables:
			catchableObj = worldObjects.Catchable(*catchable)
			self.catchables.append(catchableObj)
		
		# Load panda
		self.playerActor = PlayerActor(nickname)
		
		# Load rocks
		for rock in map.rocks:
			rockObj = worldObjects.Rock(self.environ, *rock)
		
		# Add tasks
		base.taskMgr.add(self.spinCameraTask, "SpinCameraTask")
		
		# Sending to server task
		if server <> None:
			self.serverConnection = ServerConnection(server)
		
		# Other events
		base.accept("window-event",self.windowEvent)
		base.accept("wheel_down",self.increaseCamDist)
		base.accept("wheel_up",self.decreaseCamDist)
		base.accept("escape",self.showMenu)
		
		base.accept("mouse1",self.turnCamera)
		base.accept("mouse1-up",self.stopTurnCamera)
		
		base.accept("mouse3",self.turnVCamera)
		base.accept("mouse3-up",self.stopTurnVCamera)
		
		base.accept("e",self.toggleSecondCamera)
	
	def stopGame(self):
		base.taskMgr.remove("SpinCameraTask")
		base.taskMgr.remove("resetCamera")
		base.taskMgr.remove("turnVCameraTask")
		base.taskMgr.remove("turnCameraTask")
		base.taskMgr.remove("mouseWatcher")
		base.taskMgr.remove("walkPlayerTast")
		base.taskMgr.remove("moveNickLabel")
		base.taskMgr.remove("movePlayerForwardTask")
		base.taskMgr.remove("movePlayerBackwardTask")
		base.taskMgr.remove("rotatePlayerLeftTask")
		base.taskMgr.remove("rotatePlayerRightTask")
		base.taskMgr.remove("joypadControl")
		base.render.node().removeAllChildren()
		base.ignoreAll()
		self.serverConnection.close()
	
	def turnCamera(self):
		base.taskMgr.add(self.turnCameraTask, "turnCameraTask")
	
	def stopTurnCamera(self):
		base.taskMgr.remove("turnCameraTask")
		base.taskMgr.add(self.resetCamera, "resetCamera")
	
	def turnVCamera(self):
		base.taskMgr.add(self.turnVCameraTask, "turnVCameraTask")
	
	def stopTurnVCamera(self):
		base.taskMgr.remove("turnVCameraTask")
	
	def toggleSecondCamera(self):
		# Make a second camera
		if self.secondCamera == None:
			self.secondCamera = base.makeCamera(base.win, displayRegion=(0.65,1,0,0.35), sort=10)
		else:
			self.secondCamera.removeNode()
			self.secondCamera = None
	
	def resetCamera(self, task):
		if self.cameraAngle < -500 or self.cameraAngle > 500:
			if self.cameraAngle < -500:
				self.cameraAngle += 500
			elif self.cameraAngle > -500:
				self.cameraAngle -= 500
		else:
			self.cameraAngle = 0
			return Task.done
		return Task.cont
	
	def turnCameraTask(self, task):
		try:
			if base.mouseWatcherNode.getMouseX() > self.prevX:
				self.cameraAngle += 500
			elif base.mouseWatcherNode.getMouseX() < self.prevX:
				self.cameraAngle -= 500
		except AttributeError:
			# This is the first time and prevX isnt defined yet
			pass
		self.prevX = base.mouseWatcherNode.getMouseX()
		return Task.cont
	
	def turnVCameraTask(self, task):
		try:
			if base.mouseWatcherNode.getMouseY() > self.prevY:
				self.cameraBirdview += 100
			elif base.mouseWatcherNode.getMouseY() < self.prevY:
				self.cameraBirdview -= 100
		except AttributeError:
			# This is the first time and prevY isnt defined yet
			pass
		self.prevY = base.mouseWatcherNode.getMouseY()
		return Task.cont
	
	def spinCameraTask(self, task):
		"""
		Controls the moving of the camera
		"""
		base.camera.setPos(self.playerActor, self.cameraAngle, self.cameraDistance, self.cameraBirdview)
		base.camera.lookAt(self.playerActor)
		# And now the second camera
		if self.secondCamera <> None:
			self.secondCamera.setPos(self.playerActor, 0, -5000, 1000)
			self.secondCamera.lookAt(self.playerActor)
		return Task.cont
	
	def increaseCamDist(self):
		self.cameraDistance += 300
	
	def decreaseCamDist(self):
		self.cameraDistance -= 300
	
	def windowEvent(self, event):
		"""
		This happens when something happens to the window
		"""
		if self.win.isClosed():
			self.stopGame()
			quit()
		else:
			# Window resize -> set aspect ratio
			base.camLens.setAspectRatio(float(self.win.getXSize()) / float(self.win.getYSize()))
	
	def showMenu(self):
		menu.MainMenuWidget()
		
# END MAIN APPLICATION

Quetz()
run()