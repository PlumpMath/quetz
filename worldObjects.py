from pandac.PandaModules import NodePath, SmoothMover
from panda3d.core import CollisionSphere, CollisionNode, CollisionHandlerPusher
import uuid

# WORLD OBJECTS
class Catchable(NodePath):
	"""
	Stuff that the player can pick up for the tail to get longer
	"""
	def __init__(self,game,loader,render,collHandEvent,cx,cy,cz):
		# load the model
		np = loader.loadModel("models/smiley")
		node = np.node()
		NodePath.__init__(self, node)
		
		# give some properties
		self.id = uuid.uuid1()
		self.loader = loader
		self.game = game
		
		# change some properties
		self.reparentTo(render)
		self.setPos(cx,cy,cz)
		
		#sphere
		cs = CollisionSphere(0, 0, 0, 2)
		cs.setTangible(False)
		cnodePath = self.attachNewNode(CollisionNode(str(self.id)))
		cnodePath.node().addSolid(cs)
		base.cTrav.addCollider(cnodePath, collHandEvent)
		cnodePath.show()
		
		game.accept(str(self.id) + '-into-panda', self.catch)
		
	def catch(self, event):
		"""
		Happens when the player catches this item
		"""
		self.removeNode()
		self.game.pandaActor.addObjectToTail()

class Rock(CollisionSphere):
	"""
	An invisible Rock where you can't walk into
	"""
	def __init__(self,bindTo,pusher,cx,cy,cz,radius):
		super(Rock,self).__init__(cx,cy,cz,radius)
		
		#create collision solid
		cnodePath = bindTo.attachNewNode(CollisionNode('rock'))
		cnodePath.node().addSolid(self)
		cnodePath.show()

class OtherPlayer(NodePath):
	"""
	Another player in the world (either AI or networking)
	"""
	def __init__(self, addr=None):
		print "NEW PLAYER! " + str(addr)
		np = loader.loadModel("models/panda-model")
		node = np.node()
		NodePath.__init__(self, node)
		self.addr = addr
		self.smoothMover = SmoothMover()
		self.smoothMover.setPredictionMode(1)
		self.smoothMover.setSmoothMode(1)
# END WORLD OBJECTS