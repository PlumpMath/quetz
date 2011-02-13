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