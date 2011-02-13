import uuid
import sys
import socket
import json
import zlib
# According to the manual of Panda3D, this is unsafe. But seeing that the Panda3D threads are actually fake, I still use these.
#import threading
import time

import menu

import worlds.NormalMap
import worldObjects
import modules.joypad

from math import pi, sin, cos

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from pandac.PandaModules import AntialiasAttrib, NodePath, SmoothMover, WindowProperties, ClockObject
from panda3d.core import Point3, Vec3, CollisionSphere, CollisionNode, CollisionHandlerEvent, CollisionTraverser, CollisionHandlerPusher
#from direct.stdpy import threading
 
from pandac.PandaModules import TextNode

# Distance between tail objects
TAILOBJ_DIST    = 5
# Interval between network updates
UPDATE_INTERVAL = 0.15

# JOYPAD CONTROL
class JoypadControl():
	def __init__(self, game, panda):
		self.game = game
		self.panda = panda
		#threading.Thread.__init__(self)
		#self.daemon = True
		
	def start(self):
		self.game.taskMgr.add(self.run, "joypadControl", sort=1)
	
	def run(self, task):
		#while True:
		#task.delayTime = 0.01
		# Store the x and y worths of all the joypads in this list, to calculate the avarage
		
		xA = []
		yA = []
		# Try every joypad
		try:
			xA.append(self.game.joypad.c1.get_axis(0))
			yA.append(self.game.joypad.c1.get_axis(1))
			try:
				xA.append(self.game.joypad.c2.get_axis(0))
				yA.append(self.game.joypad.c2.get_axis(1))
				try:
					xA.append(self.game.joypad.c3.get_axis(0))
					yA.append(self.game.joypad.c3.get_axis(1))
					try:
						xA.append(self.game.joypad.c4.get_axis(0))
						yA.append(self.game.joypad.c4.get_axis(1))
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
		if not self.panda.walkingByKeys:
			self.panda.changePosition(x, y)
		#time.sleep(0.01)
		return Task.cont
# END JOYPAD CONTROL

# PLAYER OBJECTS
class Panda(Actor):
	"""
	The player
	"""
	def __init__(self, game):
		super(Panda,self).__init__("models/panda-model", {"walk":"models/panda-walk4"})
		self.game = game
		self.setScale(0.005, 0.005, 0.005)
		self.reparentTo(self.game.render)
		
		self.walking = False
		self.walkingByKeys = False
		self.path = []
		
		# Add tasks
		self.game.taskMgr.add(self.savePath,"pandaSavePath")
		self.game.taskMgr.add(self.walkPandaTask, "walkPandaTast")
		
		# Contains all the tail objects
		self.tailObjects = []
			
		# Create collision solid for panda
		cs = CollisionSphere(0, 0, 200, 400)
		cnodePath = self.attachNewNode(CollisionNode('panda'))
		cnodePath.node().addSolid(cs)
		cnodePath.show()
		
		# Add to the pusher
		game.pusher.addCollider(cnodePath, self)
		base.cTrav.addCollider(cnodePath, game.pusher)
		
		# Key events
		self.game.accept("w",self.movePandaForward)
		self.game.accept("w-up",self.stopMovePandaForward)
		self.game.accept("a",self.rotatePandaLeft)
		self.game.accept("a-up",self.stopRotatePandaLeft)
		self.game.accept("d",self.rotatePandaRight)
		self.game.accept("d-up",self.stopRotatePandaRight)
		self.game.accept("s",self.movePandaBackward)
		self.game.accept("s-up",self.stopMovePandaBackward)
		
		# Joypad events
		self.game.accept("C1_NORTH-BUTTON_DOWN", self.movePandaForward)
		self.game.accept("C1_NORTH-BUTTON_UP", self.stopMovePandaForward)
		self.game.accept("C1_SOUTH-BUTTON_DOWN", self.movePandaBackward)
		self.game.accept("C1_SOUTH-BUTTON_UP", self.stopMovePandaBackward)
		self.game.accept("C1_EAST-BUTTON_DOWN", self.rotatePandaRight)
		self.game.accept("C1_EAST-BUTTON_UP", self.stopRotatePandaRight)
		self.game.accept("C1_WEST-BUTTON_DOWN", self.movePandaBackward)
		self.game.accept("C1_WEST-BUTTON_UP", self.stopMovePandaBackward)
		
		self.game.accept("C2_NORTH-BUTTON_DOWN", self.movePandaForward)
		self.game.accept("C2_NORTH-BUTTON_UP", self.stopMovePandaForward)
		self.game.accept("C2_SOUTH-BUTTON_DOWN", self.movePandaBackward)
		self.game.accept("C2_SOUTH-BUTTON_UP", self.stopMovePandaBackward)
		self.game.accept("C2_EAST-BUTTON_DOWN", self.rotatePandaRight)
		self.game.accept("C2_EAST-BUTTON_UP", self.stopRotatePandaRight)
		self.game.accept("C2_WEST-BUTTON_DOWN", self.movePandaBackward)
		self.game.accept("C2_WEST-BUTTON_UP", self.stopMovePandaBackward)
		
		self.game.accept("C3_NORTH-BUTTON_DOWN", self.movePandaForward)
		self.game.accept("C3_NORTH-BUTTON_UP", self.stopMovePandaForward)
		self.game.accept("C3_SOUTH-BUTTON_DOWN", self.movePandaBackward)
		self.game.accept("C3_SOUTH-BUTTON_UP", self.stopMovePandaBackward)
		self.game.accept("C3_EAST-BUTTON_DOWN", self.rotatePandaRight)
		self.game.accept("C3_EAST-BUTTON_UP", self.stopRotatePandaRight)
		self.game.accept("C3_WEST-BUTTON_DOWN", self.movePandaBackward)
		self.game.accept("C3_WEST-BUTTON_UP", self.stopMovePandaBackward)
		
		self.game.accept("C4_NORTH-BUTTON_DOWN", self.movePandaForward)
		self.game.accept("C4_NORTH-BUTTON_UP", self.stopMovePandaForward)
		self.game.accept("C4_SOUTH-BUTTON_DOWN", self.movePandaBackward)
		self.game.accept("C4_SOUTH-BUTTON_UP", self.stopMovePandaBackward)
		self.game.accept("C4_EAST-BUTTON_DOWN", self.rotatePandaRight)
		self.game.accept("C4_EAST-BUTTON_UP", self.stopRotatePandaRight)
		self.game.accept("C4_WEST-BUTTON_DOWN", self.movePandaBackward)
		self.game.accept("C4_WEST-BUTTON_UP", self.stopMovePandaBackward)
		
		# Axis task
		joypadcontrol = JoypadControl(self.game, self)
		joypadcontrol.start()
	
	def pandaDies(self, entry):
		print "AAAHHH"
	
	def changePosition(self, x, y):
		if x > 1:
			x = 1
		elif x < -1:
			x = -1
		if y > 1:
			y = 1
		elif y < -1:
			y = -1
		self.setPos(self, 0, y * 300, 0)
		self.setHpr(self, x * -1.5, 0, 0)
	
	def addObjectToTail(self):
		"""
		Add a TailObject to the tail of the Panda
		"""
		tailObject = TailObject(self, self.game.collHandEvent, len(self.tailObjects))
		tailObject.reparentTo(self.game.render)
		self.tailObjects.append(tailObject)
	
	def updateTail(self):
		"""
		Updates the position of all TailObjects
		"""
		for tailObj in self.tailObjects:
			tailObj.updatePosition()
	
	def walkPandaTask(self, task):
		"""
		Controls the character's animtation on walking
		"""
		myAnimControl = self.getAnimControl("walk")
		if self.walking and myAnimControl.isPlaying() == 0:
			self.loop("walk")
		elif not self.walking and myAnimControl.isPlaying() == 1:
			self.stop("walk")
		return Task.cont
	
	def savePath(self, task):
		"""
		Task: Saves the path of the Panda, so the snake can follow
		"""
		#task.delayTime = 0.01
		# Don't save or update tail when youre standing still
		try:
			#if self.previousPos <> self.getPos():
			self.path.append(self.getPos())
			# Delete the path thats unnecessary for this length of tail, but keep it at a minimum of 10 (for networking)
			if len(self.path) > len(self.tailObjects) * TAILOBJ_DIST + 10:
				del self.path[0]
			# Update the tail
			self.updateTail()
		except AttributeError:
			pass
		self.previousPos = self.getPos()
		return Task.cont
	
	"""
	These methods add tasks for moving to the taskmanager
	"""
	def movePandaForward(self):
		self.game.taskMgr.add(self.moveForwardTask, "movePandaForwardTask")
	
	def movePandaBackward(self):
		self.game.taskMgr.add(self.moveBackwardTask, "movePandaBackwardTask")
	
	def rotatePandaLeft(self):
		self.game.taskMgr.add(self.rotateLeftTask, "rotatePandaLeftTask")
	
	def rotatePandaRight(self):
		self.game.taskMgr.add(self.rotateRightTask, "rotatePandaRightTask")
		
	"""
	These methods remove tasks for moving from the taskmanager
	"""
	def stopMovePandaForward(self):
		self.walking = False
		self.walkingByKeys = False
		self.game.taskMgr.remove("movePandaForwardTask")
	
	def stopMovePandaBackward(self):
		self.walking = False
		self.walkingByKeys = False
		self.game.taskMgr.remove("movePandaBackwardTask")
		
	def stopRotatePandaLeft(self):
		self.walking = False
		self.walkingByKeys = False
		self.game.taskMgr.remove("rotatePandaLeftTask")
		
	def stopRotatePandaRight(self):
		self.walking = False
		self.walkingByKeys = False
		self.game.taskMgr.remove("rotatePandaRightTask")
	
	"""
	These methods move the panda
	"""
	def moveForwardTask(self, task):
		"""
		Task: Move the Panda forward
		"""
		self.walking = True
		self.walkingByKeys = True
		self.changePosition(0, -1)
		return Task.cont
	
	def moveBackwardTask(self, task):
		"""
		Task: Move the Panda backwards
		"""
		self.walking = True
		self.walkingByKeys = True
		self.changePosition(0, 1)
		return Task.cont
	
	def rotateLeftTask(self, task):
		"""
		Task: Rotate the Panda to the left
		"""
		self.walking = True
		self.walkingByKeys = True
		self.changePosition(-1, 0)
		return Task.cont
	
	def rotateRightTask(self, task):
		"""
		Task: Rotate the Panda to the right
		"""
		self.walking = True
		self.walkingByKeys = True
		self.changePosition(1, 0)
		return Task.cont
	
class TailObject(NodePath):
	"""
	One of the objects behind the player which together make the tail
	"""
	def __init__(self, panda, collHandEvent, position):
		np = loader.loadModel("models/smiley")
		node = np.node()
		NodePath.__init__(self, node)
		
		self.panda = panda
		#number in the row of tailobjects
		self.position = position
		
		#sphere
		cs = CollisionSphere(0,0,0,2)
		cs.setTangible(False)
		cnodePath = self.attachNewNode(CollisionNode(str(self.id)))
		cnodePath.node().addSolid(cs)
		cnodePath.show()
		
		base.cTrav.addCollider(cnodePath, collHandEvent)
	
	def updatePosition(self):
		"""
		Update the position of this tail object
		"""
		try:
			index = -((self.position+1)*TAILOBJ_DIST)
			self.setPos(self.panda.path[index])
		except IndexError:
			self.setPos(self.panda.path[0])
	
	def remove(self):
		self.removeNode()
# END PLAYER OBJECTS

# NETWORKING
class ServerConnection():
	"""
	Connection to a server
	"""
	def __init__(self, server, game):
		#threading.Thread.__init__(self)
		#super(ServerConnection, self).__init__(self)
		self.game = game
		
		self.timer = time.time()
		
		#stores all the other players
		self.otherplayers = []
		
		self.port = 44454
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		# Disable Nagle algorithm
		#self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)
		#self.socket.connect((server, port))
		self.server = server
		#threading.Thread.__init__(self)
		
		self.game.taskMgr.add(self.run, "run")
		self.game.taskMgr.add(self.movePlayers, "movePlayers")
		
		self.daemon = True
	
	def run(self, task):
		"""
		This is what the server does every UPDATE_INTERVAL seconds
		"""
		#while time.time() + UPDATE_INTERVAL >= self.timer:
		#	self.timer = time.time()
		task.delayTime = UPDATE_INTERVAL
		try:
			# Send the current player position/heading
			try:
				pandaPos = zlib.compress(json.dumps([self.game.pandaActor.getX(),self.game.pandaActor.getY(),self.game.pandaActor.getZ(),self.game.pandaActor.getH()]))
				self.socket.sendto(b'SEND P POS ' + pandaPos, (self.server, self.port))
			except socket.error:
				print "Huh what happened?"
			
			# Ask for the world
			self.socket.sendto(b'REQ WORLD', (self.server, self.port))
			data = self.socket.recv(1024)
			if data[0:7] == "PLAYERS":
				players = json.loads(zlib.decompress(data[8:]))
				self.placeOtherPlayers(players)
			elif data == "KICKED":
				# Hey! I'm kicked!?
				print "You were kicked from the server."
		except socket.error:
			print "Connection lost."
			return Task.done
		return Task.again
	
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
			self.updatePlayer(player[0], player[1], player[2], player[3], player[4])
	
	def removePlayer(self, player):
		"""
		Remove a player from the world
		"""
		self.otherplayers.remove(player)
		player.removeNode()
	
	def updatePlayer(self, addr, cx, cy, cz, h):
		"""
		Update a player, or add it when it's not yet there
		"""
		# Check if the player is already there
		foundPlayer = False
		for player in self.otherplayers:
			if player.addr == addr:
				# Update the position/heading smoothly
				player.smoothMover.setPos(Point3(cx, cy, cz))
				player.smoothMover.setHpr(Vec3(h, 0, 0))
				player.smoothMover.setTimestamp(globalClock.getFrameTime())
				player.smoothMover.markPosition()
				foundPlayer = True
		
		# If the player is not already there, add it
		if not foundPlayer:
			newPlayer = worldObjects.OtherPlayer(addr)
			newPlayer.reparentTo(self.game.render)
			newPlayer.setScale(0.005, 0.005, 0.005)
			newPlayer.setFluidPos(cx, cy, cz)
			self.otherplayers.append(newPlayer)
	
	def movePlayers(self, task):
		"""
		Updates all the other players in the environment
		"""
		for player in self.otherplayers:
			player.smoothMover.computeAndApplySmoothPosHpr(player, player)
		return Task.cont
	
	def __del__(self):
		self.socket.close()
# END NETWORKING

class Snake(ShowBase):
	"""
	The game itself
	"""
	def __init__(self):
		ShowBase.__init__(self)
		self.menu = menu.MainMenu(self)
		self.run()
	
	def startGame(self, server = None):
		self.menu.destroy()
		
		self.cameraDistance = 5000
		
		# Set options
		self.render.setAntialias(AntialiasAttrib.MAuto)
		
		# Fixed framerate
		
		globalClock.setMode(ClockObject.MLimited)
		globalClock.setFrameRate(40)
		
		# Get the world
		map = worlds.NormalMap.World()
		
		# Load the world
		self.render.setFog(map.fog)
		self.setBackgroundColor(map.bgcolor)
		
		# Set colission traverser
		base.cTrav = CollisionTraverser()
		self.collHandEvent = CollisionHandlerEvent()
		self.collHandEvent.addInPattern('%fn-into-%in')
		self.collHandEvent.addAgainPattern('%fn-again-%in')
		self.collHandEvent.addOutPattern('%fn-out-%in')
		
		self.pusher = CollisionHandlerPusher()
		
		# Load environment
		self.environ = self.loader.loadModel(map.map)
		self.environ.reparentTo(self.render)
		self.environ.setScale(*map.scale)
		
		# Load catchables
		self.catchables = []
		for catchable in map.catchables:
			catchableObj = worldObjects.Catchable(self, self.loader, self.render, self.collHandEvent, *catchable)
			self.catchables.append(catchableObj)
		
		# Load panda
		self.pandaActor = Panda(self)
		
		# Load rocks
		for rock in map.rocks:
			rockObj = worldObjects.Rock(self.environ, self.pusher, *rock)
		
		# Add tasks
		self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")
		
		# Sending to server task
		if server <> None:
			self.serverConnection = ServerConnection(server, self)
		
		# Other events
		self.accept("window-event",self.windowEvent)
		self.accept("wheel_down",self.increaseCamDist)
		self.accept("wheel_up",self.decreaseCamDist)
		self.accept("escape",self.quitGame)
		
	def spinCameraTask(self, task):
		"""
		Controls the moving of the camera
		"""
		self.camera.setPos(self.pandaActor, 0, self.cameraDistance, 1000)
		self.camera.lookAt(self.pandaActor)
		return Task.cont
	
	def increaseCamDist(self):
		self.cameraDistance += 100
	
	def decreaseCamDist(self):
		self.cameraDistance -= 100
	
	def windowEvent(self, event):
		"""
		This happens when something happens to the window
		"""
		if self.win.isClosed():
			self.quitGame()
		else:
			# Window resize -> set aspect ratio
			base.camLens.setAspectRatio(float(self.win.getXSize()) / float(self.win.getYSize()))
	
	def quitGame(self):
		quit()
		
app = Snake()