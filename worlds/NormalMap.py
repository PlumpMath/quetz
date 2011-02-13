from pandac.PandaModules import Fog
import worldObjects

class World(object):
	def __init__(self):
		# Make some nice fog
		colour = (0.3,0.3,0.3)
		linfog = Fog("A linear-mode Fog node")
		linfog.setColor(*colour)
		linfog.setLinearRange(0,320)
		linfog.setLinearFallback(45,160,320)
		
		# Catchables positions
		catchables = []
		for i in xrange(100):
			pos = (i*10+10, 0, 2)
			catchables.append(pos)
		
		# Rocks positions and such
		rocks = []
		rock1 = (0,50,0,10)
		rocks.append(rock1)
		
		self.fog = linfog
		self.bgcolor = colour
		self.scale = (1,1,1)
		self.map = "worlds/maps/normalmap"
		self.catchables = catchables
		self.rocks = rocks