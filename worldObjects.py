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

from pandac.PandaModules import NodePath, SmoothMover
from panda3d.core import CollisionSphere, CollisionNode, CollisionHandlerPusher
import uuid

# WORLD OBJECTS
class Catchable(NodePath):
	"""
	Stuff that the player can pick up for the tail to get longer
	"""
	def __init__(self,cx,cy,cz):
		# load the model
		np = base.loader.loadModel("models/smiley")
		node = np.node()
		NodePath.__init__(self, node)
		
		# give some properties
		self.id = uuid.uuid1()
		
		# change some properties
		self.reparentTo(base.render)
		self.setPos(cx,cy,cz)
		
		#sphere
		cs = CollisionSphere(0, 0, 0, 2)
		cs.setTangible(False)
		cnodePath = self.attachNewNode(CollisionNode(str(self.id)))
		cnodePath.node().addSolid(cs)
		base.cTrav.addCollider(cnodePath, base.collHandEvent)
		#cnodePath.show()
		
		base.accept(str(self.id) + '-into-playerActor', self.catch)
		
	def catch(self, event):
		"""
		Happens when the player catches this item
		"""
		self.removeNode()
		base.playerActor.tail.addObject()

class Rock(CollisionSphere):
	"""
	An invisible Rock where you can't walk into
	"""
	def __init__(self,bindTo,cx,cy,cz,radius):
		super(Rock,self).__init__(cx,cy,cz,radius)
		
		#create collision solid
		cnodePath = bindTo.attachNewNode(CollisionNode('rock'))
		cnodePath.node().addSolid(self)
		cnodePath.show()
# END WORLD OBJECTS