# AQUARIUM
"""
Create a text-based aquarium to view in terminal with a randomized background
and ecosystem
"""

# from termcolor import colored, cprint
from random import randint, choice
from time import sleep, time
from copy import deepcopy
import os
import sys
import signal
import subprocess

# since termcolor isn't a standard module, warn users who don't have it
try:
	from termcolor import colored, cprint
except ImportError:
	print "the python module 'termcolor' must be installed to use this program.  Please download and install, and try again."


##### VARIABLES #####

DELAY = 0.07	# for screen refresh rate

# get size of terminal
WIDTH = int( subprocess.check_output(['tput','cols']) )
HEIGHT = int( subprocess.check_output(['tput','lines']) ) - 1

# used for scaling time fish have to go towards a "desire" (coral)
search_time = WIDTH + HEIGHT

degree_symbol = unichr(176)			# For drawing bubbles

# Set a blank faraway object (for initial object when using FindNearest)
FarawayObject = type('test', (object,), {})()
FarawayObject.position = [-1000, -1000]
FarawayObject.size = [0,0]


# ------- SPECIAL HANDLING FUNCTIONS ------- #
def signal_handler(signum, frame):
	# (Show the cursor again)
	os.system('echo "\x1b[?25h"')
	os.system('tput sgr0')
	sys.exit()

signal.signal(signal.SIGINT, signal_handler)


# ------- FUNCTION DECORATORS ------- #
def speed_check_before(movement_function):
	def wrapper(self, *args):

		# keep speed from exploding
		if self.speed >= self.maxspeed:
			self.speed = self.maxspeed
		if self.speed < 0:
		 	self.speed = 0

		movement_function(self, *args)				# flee or follow

	return wrapper

def speed_check_after(movement_function):
	def wrapper(self, *args):

		movement_function(self, *args)				# flee or follow

		# keep speed from exploding
		if self.speed >= self.maxspeed:
			self.speed = self.maxspeed
		if self.speed < 0:
		 	self.speed = 0

	return wrapper

def turn_around_water(movement_function):
	def wrapper(self, *args):
		#--------------------------------------------------------------------------------
		# TURN AROUND (X)
			# left wall
		if self.position[1] < (self.speed + 1):
			self.direction[1] = 1
			# right wall
		if self.position[1] > (WIDTH - (int(self.direction[1] * self.speed) + self.size[1] + 1) ):
			self.direction[1] = -1
		# TURN AROUND (Y)
			# top (water)
		if self.position[0] < ( Water.position + (self.speed + 1) ):
			self.direction[0] = 1
			#bottom (sand)
		if self.position[0] > ((HEIGHT-1) - (int(self.direction[0] * self.speed) + self.size[0] + 1) ):
			self.direction[0] = -1
		#--------------------------------------------------------------------------------
		movement_function(self, *args)				# flee or follow
	return wrapper

def turn_around_sand(movement_function):
	def wrapper(self, *args):
		#--------------------------------------------------------------------------------
		# TURN AROUND (X)
			# left wall
		if self.position[1] < (self.speed + 1):
			self.direction[1] = 1
			# right wall
		if self.position[1] > (WIDTH - (int(self.direction[1] * self.speed) + self.size[1] + 1) ):
			self.direction[1] = -1
		# TURN AROUND (Y)
			# top (water)
		if self.position[0] < ( Sand.position + (self.speed + 1) ):
			self.direction[0] = 1
			#bottom (sand)
		if self.position[0] > ((HEIGHT-1) - (int(self.direction[0] * self.speed) + self.size[0] + 1) ):
			self.direction[0] = -1
		#--------------------------------------------------------------------------------
		movement_function(self, *args)				# flee or follow
	return wrapper


#########################################################################
##### CLASSES #####

# Display of the aquarium
class Window(object):
	def __init__(self, border_color):
		self.border_color = border_color
		self.width = WIDTH
		self.height = HEIGHT

		self.aquarium_box = []
		self.aquarium_box_background = []

		# clear screen
		os.system('clear')

		# create blank aquarium box
		for y in range(self.height):
			self.aquarium_box.append([" "] * self.width)

		#draw aquarium border
		for y in range(0, self.height):
			for x in range(0, self.width):
				#top 
				self.aquarium_box[0][x] = colored( "=", self.border_color )
				#bottom
				self.aquarium_box[self.height - 1][x] = colored( "=", self.border_color )
				#left
				self.aquarium_box[y][0] = colored( "|", self.border_color )
				#right
				self.aquarium_box[y][self.width - 1] = colored( "|", self.border_color )

	def display(self):
		# Clear screen and scrollback buffer
		#os.system("clear && printf '\e[3J' ")
		os.system('tput cup 0 0')
		# print
		for row in range( len(self.aquarium_box) ):
			print "".join(self.aquarium_box[row])

# Things that can be drawn in the aquarium
class Thing(object):
	def __init__(self, position, color):
		self.position = position
		self.color = color

		# self.direction = [0,0]
		self.size = [0,0]
		self.picture = [['']]

	# Get the picture of the object in question, and assign LEFT or RIGHT picture
	def getPicture(self):
		self.picture = self.right()
		if self.direction[1] < 0:
			self.picture = self.left()
		elif self.direction[1] > 0:
			self.picture = self.right()
		# Get size of the object's picture
		self.size = [ len(self.picture), len(self.picture[0][0]) ]

	# Draw the object
	def draw(self):
		self.getPicture()
		for y in range( self.size[0] ):
			for x in range( self.size[1] ):
				if 	y + self.position[0] > 1 and \
					y + self.position[0] < (HEIGHT-1) and \
					x + self.position[1] > 1 and \
					x + self.position[1] < (WIDTH-1) and \
					self.picture[y][0][x] != " " :			# Avoids drawing a blank box around thing
						Aquarium.aquarium_box[ y + self.position[0] ][ x + self.position[1] ] \
						= colored(self.picture[y][0][x], self.color)

	# Remove object (for when it's moving)
	def erase(self):
		self.getPicture()
		for y in range( self.size[0] ):
			for x in range( self.size[1] ):
				if 	y + self.position[0] > 1 and \
					y + self.position[0] < (HEIGHT-1) and \
					x + self.position[1] > 1 and \
					x + self.position[1] < (WIDTH-1) :
						Aquarium.aquarium_box[ y + self.position[0] ][ x + self.position[1] ] \
						= Aquarium.aquarium_box_background [ y + self.position[0] ][ x + self.position[1] ]

# ------- MOVING THINGS ------- #

# Moving things (animals, bubbles, ships)
class MovingThing(Thing):
	def __init__(self, position, color):
		self.position = position	# [y,x]
		self.maxspeed = 1
		self.color = color
		# set speed initially to maxspeed
		self.speed = 1
		self.speed = self.maxspeed

		# Initiate a start direction of left or right (if direction starts as [0,0]...
		# ... then calmRandomMove objects will stay still)
		self.direction = [0, choice([-1,1])]	# [y,x]
		
		# Initial null values for each object, so that it can be drawn the first time
		self.size = [0,0]
		self.picture = [['']]

	# Move object
	def move(self):
		# Erase current, increment, draw new
		self.erase()
		self.position[0] += int( self.direction[0] * self.speed )
		self.position[1] += int( self.direction[1] * self.speed )
		self.draw()

	# Keep speed from exploding
	def controlSpeed(self):
		# keep speed from exploding
		if self.speed >= self.maxspeed or self.speed < 0:
			self.speed = 1

	# get the distance of a targer
	def getDistance(self, target):
		target_tail = target.position[1] 	# give an initial number (to avoid error)
		target_front = target.position[1] 	# give an initial number (to avoid error)

		# NonMovingObject has no direction attribute, so default 0 with:  getattr(obj, attr, default)

		# --> TELL WHICH SIDE OF THE TARGET ITS TAIL IS ON:
		# moving LEFT
		if getattr(target, 'direction', [0,0])[1] < 0:
			target_tail = target.position[1] + target.size[1]		#tail is on left
		# moving RIGHT
		elif getattr(target, 'direction', [0,0])[1] >= 0:
			target_tail = target.position[1]  						#tail is on right

		# --> TELL WHICH SIDE OF THE ENEMY ITS MOUTH IS ON:
		# moving LEFT
		if getattr(target, 'direction', [0,0])[1] < 0:
			target_front = target.position[1] 					#mouth is on left
		# moving RIGHT
		elif getattr(target, 'direction', [0,0])[1] >= 0:
			target_front = target.position[1] + target.size[1] 	#mouth is on right

		# Calculate distance
		dy = target.position[0] - self.position[0]
		dx_tail = target_tail - self.position[1]
		dx_front = target_front - self.position[1]

		distance_tail_sq = (dx_tail**2) + ((dy/2)**2)
		distance_front_sq = (dx_front**2) + ((dy/2)**2)

		return [dy, dx_tail, dx_front, distance_tail_sq, distance_front_sq]

	# Find nearest individual in a group (list)
	def findNearest(self, group, *arg):
		if len(arg) > 0:
			side = str(arg[0])
		else:
			side = 'tail'

		if side.lower() in ['front', 'mouth']:		# look for front (mouth)
			side_index = 4
		else:										# look for tail
			side_index = 3

		# set initial values as very large, so they don't win in a comparison
		dr_current = 500
		dr_previous = 500

		# initial faraway object
		nearest_member = FarawayObject		# FarawayObject has position [-1000, -1000]

		# Go through list, and if a member is nearer the previous nearest, replace nearest_member
		for member in group:

			if member == self:						# ignore self (don't find distance)
				pass

			# getDistance() returns :
			# [dy, dx_tail, dx_front, distance_tail_sq, distance_front_sq]
			dr_current = self.getDistance(member)[side_index]		# distance to tail or front
			if dr_current == 0:						# ignore those at same position
				pass
			elif dr_current < dr_previous:			# if current is nearer than previous nearest...
				nearest_member = member

		return nearest_member

	# Move randomly (and somewhat chaotically)
	@speed_check_before
	def randomMove(self):
		if randint(1,6) == 1:
			self.direction[0] += randint(-1,1)
			self.direction[1] += randint(-2,2)
			self.speed += randint(-1,1)
		# y-direction
		if abs(self.direction[0]) > 1:
			self.direction[0] = 0
		# x-direction
		if abs(self.direction[1]) > 1:
			self.direction[1] = abs(self.direction[1])/self.direction[1]
		# speed
		# self.controlSpeed()
		self.move()

	# Move randomly up and down, but stay moving forward
	@speed_check_before
	def calmRandomMove(self):
		#only randomize movement in y-direction
		if randint(1,4) == 1:
			self.direction[0] += randint(-1,1)
		if abs(self.direction[0]) > 1:
			self.direction[0] = 0
		if randint(1,500) == 1:
			self.direction[1] *= -1
			
		#speed
		# self.controlSpeed()
		self.move()

	# Follow a leader, trying to stay within a certain distance (abstract)
	@speed_check_before
	def follow(self, leader, distance):
		# variable for how much to accelerate when far from leader
		self.accelerate = 1

		get_distances = self.getDistance(leader)
		# [dy, dx_tail, dx_front, distance_tail_sq, distance_front_sq]
		dy = get_distances[0]
		dx = get_distances[1]			# dx_tail
		dr_sq = get_distances[3]		# distance_tail_sq

		# if the radius is greater than the follow distance, go back towards leader
		if dr_sq  >= (distance**2):
			# if dx > distance or dy > distance/2:
			if dy != 0:
				self.direction[0] = ( dy/abs(dy) )
			if dx != 0:
				self.direction[1] = ( dx/abs(dx) )

			self.speed += self.accelerate		# Get back to leader
			# self.move()						# Move straight to leader

	# Flee from an enemy (i.e. Predator)
	@speed_check_before
	def flee(self, enemy, distance):
		# variable for how much to accelerate when enemy is close
		self.accelerate = 3

		get_distances = self.getDistance(enemy)
		# [dy, dx_tail, dx_front, distance_tail_sq, distance_front_sq]
		dy = get_distances[0]
		dx = get_distances[2]			# dx_front
		dr_sq = get_distances[4]		# distance_front_sq

		# if the radius is less than the flee distance (radius of safety)... Flee for your life!
		if dr_sq <= (distance**2):
			# if dx > distance or dy > distance/2:
			if dy != 0:
				self.direction[0] = -( dy/abs(dy) )
			if dx != 0:
				self.direction[1] = -( dx/abs(dx) )

			# self.speed += self.accelerate		# Get ready to flee quickly
			self.move()							# Move straight away from the enemy
			# self.speed = self.maxspeed
			self.move()							# Move straight away from the enemy
			self.move()							# Move straight away from the enemy

			# Return whether it is fleeing or not (useful for fleeing several things, with varying priority)
			return True
		else:
			return False

	# Follow a leader randomly
	def randomFollow(self, leader, distance):
		self.follow(leader, distance)
		self.randomMove()

	# Follow a leader calmRandomly
	def calmRandomFollow(self, leader, distance):
		self.follow(leader, distance)
		self.calmRandomMove()

# Debris that drifts (like bubbles, sinkers, etc.)
class Debris (MovingThing):
	# erase current, increment, draw new
	def move(self):
		if 	self.position[0] <= ( Water.position ):
			self.erase()
			del self
		else:
			MovingThing.move(self)

	# wiggle from left-to-right, randomly
	def drift(self):
		self.direction[1] += randint(-1,1)
		if abs(self.direction[1]) >= 2:
			self.direction[1] = 0
		self.move()

class Fish(MovingThing):
	@turn_around_water
	def move(self):
		MovingThing.move(self)

class BottomFeeder(MovingThing):
	@turn_around_sand
	def move(self):
		MovingThing.move(self)

# ------- ANIMALS ------- #

# Fish (smallest)
class SeaMonkey(Fish):
	def __init___(self, position, color):
		MovingThing.__init__(self, position, color)
		self.maxspeed = 2
	
	def left(self):
		# if randint(1,2) == 1:
		if self.direction[0] < 0:
			return 	[			\
			['`']
			]
		if self.direction[0] > 0:
			return 	[			\
			[',']
			]
		else:
			return 	[			\
			['-']
			]
	def right(self):
		# if randint(1,2) == 1:
		if self.direction[0] < 0:
			return 	[			\
			[',']
			]
		elif self.direction[0] < 0:
			return 	[			\
			['`']
			]
		else:
			return 	[			\
			['-']
			]

# Fish (small)
class Minnow(Fish):
	def __init___(self, position, color):
		MovingThing.__init__(self, position, color)
		self.maxspeed = 2

	def left(self):
		return 	[			\
		['<']
		]
	def right(self):
		return 	[		\
		['>']
		]

# Fish (medium)
class AngelFish(Fish):
	def __init___(self, position, color):
		MovingThing.__init__(self, position, color)
		self.maxspeed = 1

	def left(self):
		return 	[		\
		['<(']
		]
	def right(self):
		return 	[		\
		[')>']
		]

# Fish (large)
class Tuna(Fish):
	def __init___(self, position, color):
		MovingThing.__init__(self, position, color)
		self.maxspeed = 2

	def left(self):
		return 	[		\
		['<=(']
		]
	def right(self):
		return	[		\
		[')=>']
		]

# Fish (long)
class Baracuda(Fish):
	def __init___(self, position, color):
		MovingThing.__init__(self, position, color)
		self.maxspeed = 2

	def left(self):
		return 	[		\
		['<==^=-<']
		]
	def right(self):
		return 	[		\
		['>-=^==>']
		]

# Whale
class Whale(Fish):
	def __init___(self, position, color):
		MovingThing.__init__(self, position, color)
		self.maxspeed = 1

	def left(self):
		return [							
		[' _--.-^---_____/'],
		['(__`______===== '],
		['    V          \\']				
		]

	def right(self):
		return [							
		['\\_____---^-.--_ '],
		[' =====______`__)'],
		['/          V    ']				
		]

# Baby Whale
class BabyWhale(Fish):
	def __init___(self, position, color):
		MovingThing.__init__(self, position, color)
		self.maxspeed = 1

	def left(self):
		return [							
		[' ________/'],
		['(__`u_===\\']		
		]

	def right(self):
		return [							
		['\\________ '],
		['/===_u`__)']				
		]

# Snail
class Snail(BottomFeeder):
	def __init___(self, position, color):
		MovingThing.__init__(self, position, color)
		self.maxspeed = 1

	def left(self):
		return 	[			\
		['@']
		]
	def right(self):
		return 	[		\
		['@']
		]

# Sea Urchin
class SeaUrchin(BottomFeeder):
	def __init___(self, position, color):
		MovingThing.__init__(self, position, color)
		self.maxspeed = 1

	def left(self):
		return [							
		['  .w.  '],
		['_\ | /_'],
		['> ,*, <']		
		]

	def right(self):
		return [							
		['  .v.  '],
		['_\ | /_'],
		['> ,*, <']		
		]

# Lobster
class Lobster(BottomFeeder):
	def __init___(self, position, color):
		MovingThing.__init__(self, position, color)
		self.maxspeed = 1

	def left(self):
		if randint(0,20) == 1:
			return [							
			['\./  '],
			['>M=={'],
			['     ']		
			]
		elif randint(0,20) == 2:
			return [							
			['_|.  '],
			['>M=={'],
			['     ']		
			]
		else:
			return [							
			['\|.  '],
			['>M=={'],
			['     ']		
			]

	def right(self):
		if randint(0,20) == 1:
			return [							
			['  \./'],
			['}==M<'],
			['     ']		
			]
		elif randint(0,20) == 2:
			return [							
			['  .|_'],
			['}==M<'],
			['     ']		
			]
		else:
			return [							
			['  .|/'],
			['}==M<'],
			['     ']		
			]

# ------- DEBRIS ------- #

# Bubbles!
class Bubble(Debris):
	def __init__(self, position, color):
		self.maxspeed = 1

		Debris.__init__(self, position, color)
		self.position = position
		self.color = color
		self.direction = [-1,0]		# float up

	def left(self):
		return 	[			\
		['o O'],
		[' : ']
		]
	def right(self):
		return 	[		\
		['o .'],
		['.%s ' %(degree_symbol)]
		] 

# ------- NONMOVING THINGS ------- #

# Nonmoving things (sand features, rocks, etc.)
class NonMovingThing(Thing):
	def __init__(self, position, color):
		# self.size = size			# [y,x]
		self.position = position	# [y,x]
		self.color = color

		self.direction = [0,0]
		self.size = [0,0]
		self.picture = [['']]

		# self.draw()

	# Get the picture of the object in question, and assign LEFT or RIGHT picture
	def getPicture(self):
		self.picture = self.image()
		# Get size of the object's picture
		self.size = [ len(self.picture), len(self.picture[0][0]) ]

# Surfaces (for sea and sand)
class Surface(object):
	def __init__(self, position, color):
		self.position = position	# [y,x]
		self.color = color

	#draw line (override NonMovingThing .draw() method
	def draw(self):
		#draw line
		x = 1
		y = self.position
		while x < (WIDTH - 1):
			Aquarium.aquarium_box[y][x] = colored( '~', self.color)
			x += 1

	#draw fill under line
	def drawUnder(self):
		#draw under line
		x = 1
		y = self.position + 1
		while y < (HEIGHT - 1):
			while x < (WIDTH - 2):
				Aquarium.aquarium_box[y][x] = colored( ',', self.color)
				x += 1
				Aquarium.aquarium_box[y][x] = ' '
				x +=1
			x = (y % 2) + 1
			y += 1

	#draw fill above line
	def drawAbove(self):
		#draw under line
		x = 1
		y = 1
		while y < (self.position):
			while x < (WIDTH - 1):
				Aquarium.aquarium_box[y][x] = colored( '-', self.color)
				x += 6
			x = 3*(y % 2) + 1
			y += 1

# ------- NONMOVING DECORATIONS ------- #

# Dune Class
class Dune(NonMovingThing):
	# Draw the object, but omit the blank areas on the sides (which would create a blank box)
	def draw(self):
		self.getPicture()
		for y in range( self.size[0] ):
			for x in range( self.size[1] ):
				if 	y + self.position[0] > 1 and \
					y + self.position[0] < (HEIGHT-1) and \
					x + self.position[1] > 1 and \
					x + self.position[1] < (WIDTH-1) :
					if self.picture[y][0][x] != 'R':		# edges of dune drawing should be ommitted
						Aquarium.aquarium_box[ y + self.position[0] ][ x + self.position[1] ] \
						= colored(self.picture[y][0][x], self.color)

# Dunes
class SmallDune(Dune):
	def image(self):
		return [							
		['RRR.~""~.RRR'],
		['RR/, . . \RR'],
		['~`, . . . `~']				
		]

class BigDune(Dune):
	def image(self):
		return [							
		['RRRRRRR,.~"""""~. ,RRRRRR'],
		['RRRR/; . . . . . . .\RRRR'],
		['RR/;. . . . . . . . . \RR'],				
		['~`; . . . . . . . . . .`~']				
		]

class HugeDune(Dune):
	def image(self):
		return [							
		['RRRRRR,.~"""""""~. ,RRRRRR'],
		['RRRR/; . . . . . . .\RRRRR'],
		['RR/;. . . . . . . . . \RRR'],				
		['R/;. . . . . . . . . . \RR'],				
		['/;. . . . . . . . . . . \R'],				
		['~` . . . . . . . . . . `~R']				
		]

class SlopedDune(Dune):
	def image(self):
		return [							
		['RRRRRRRR,.~"""""""~.,RRRRRRRRRRRRRRRRRRRRRRRRR'],
		['RRRRRR/; . . . . . . .\RRRRRRRRRRRRRRRRRRRRRRR'],
		['RRRR/;. . . . . . . . . \RRRRRRRRRRRRRRRRRRRRR'],				
		['RRR/;. . . . . . . . . . . \RRRRRRRRRRRRRRRRRR'],				
		['RR/;. . . . . . . . . . . . ,-----____RRRRRRRR'],				
		['R/;. . . . . . . . . . . ,;/;. . . . . .\RRRRR'],				
		['/;. . . . . . . . . . .,/;. . . . . . . . \RRR'],				
		['~` . . . . . . . . . .,;;. . . . . . . . . .`~']				
		]

class SlantedDune(Dune):
	def image(self):
		return [							
		['RRRRRRRRRRRRRR,.~"""""""~.,RRRRRRRRRRRRRRRRRR'],
		['RRRRRRRRRRR/;. . . . . . . \RRRRRRRRRRRRRRRRR'],
		['RRRRRRRR/;. . . . . . . . . \RRRRRRRRRRRRRRRR'],				
		['RRRRRR/; . . . . . . . . . . \RRRRRRRRRRRRRRR'],				
		['RRRR/;. . . . . . . . . . . ,-----.___RRRRRRR'],				
		['RR/; . . . . . . . . . . ,;/; . . . . . \RRRR'],				
		['/;. . . . . . . . . . .,/;. . . . . . . .\RRR'],				
		['~` . . . . . . . . . .,; . . . . . . . . . `~']				
		]


# Corals
class TreeCoral(NonMovingThing):
	def image(self):
		return [							
		['-_   \/'],
		[' \/ -/-'],
		['  \ /  '],				
		['   |-  '],				
		]

class BrainCoral(NonMovingThing):
	def image(self):
		return [
		['    ,#&.   '],
		[' *#*@*@@&*.'],				
		['*@@*&*@**%&'],				
		]

class Kelp(NonMovingThing):
	def image(self):
		return [
		[' V '],				
		[' | '],				
		[' |/'],				
		[' | '],				
		['\| '],				
		[' | '],				
		[' |/'],				
		[' | '],				
		['\|/'],				
		[' |/'],				
		[' | '],				
		['\| '],				
		[' | '],				
		]

class LongKelp(NonMovingThing):
	def image(self):
		return [
		[' V '],				
		[' | '],				
		['\| '],				
		[' | '],
		['\|/'],
		[' | '],					
		['\|/'],								
		[' |/'],				
		['\| '],				
		[' | '],				
		[' |/'],				
		[' | '],				
		['\|/'],
		['\| '],				
		[' | '],				
		[' |/'],				
		[' | '],				
		['\|/'],
		[' | '],				
		[' | '],
		[' | '],
		[' | '],				
		[' |/'],				
		[' | '],				
		['\|/'],
		['\| '],
		[' |/'],				
		[' | '],				
		['\| '],				
		[' | '],				
		[' |/'],				
		[' | '],
		['\| '],				
		[' | '],				
		[' |/'],				
		[' | '],				
		['\|/'],
		[' | '],					
		['\|/'],								
		[' |/'],
		['\|/'],
		[' | '],					
		[' | '],					
		['\|/'],								
		[' |/'],				
		[' | '],				
		['\| '],				
		[' | '],				
		[' | '],				
		[' |/'],				
		[' | '],				
		['\|/'],
		['\| '],
		[' |/'],				
		[' | '],				
		['\| '],				
		[' | '],				
		[' |/'],				
		[' | '],
		['\| '],				
		[' | '],				
		[' |/'],				
		[' | '],				
		['\|/'],
		[' | '],					
		['\|/'],								
		[' |/'],
		['\|/'],
		['\|/'],								
		[' |/'],				
		[' | '],				
		['\| '],				
		[' | '],				
		[' | '],				
		[' |/'],				
		[' | '],				
		['\|/'],
		['\| '],
		[' |/'],				
		[' | '],				
		['\| '],				
		[' | '],				
		[' |/'],				
		[' | '],
		['\| '],				
		[' | '],				
		[' |/'],				
		[' | '],				
		['\|/'],
		[' | '],					
		['\|/'],								
		[' |/'],
		['\|/'],
		[' | '],					
		['\|/'],								
		[' |/'],				
		[' | '],				
		['\| '],				
		[' | '],				
		]


# School class
class School(object):
	def __init__(self, students, LeadType, FollowType, FollowDistance):
		self.students = students
		self.LeadType = LeadType
		self.FollowType = FollowType
		self.FollowDistance = FollowDistance

		self.following_order = self.createFollowingOrder()

	# Direct which kind of LeadType
	def Lead(self, current_student):
		if str(self.LeadType).lower() == "randomMove".lower():
			current_student.randomMove()
		elif str(self.LeadType).lower() == "calmRandomMove".lower():
			current_student.calmRandomMove()

	# Direct which kind of FollowType
	def Follow(self, current_student, current_leader, distance):
		if self.FollowType == "randomFollow":
			current_student.randomFollow(current_leader, distance)
		elif self.FollowType == "calmRandomFollow":
			current_student.calmRandomFollow(current_leader, distance)

	# Automate the following heirarchy (during each loop)
	def automate(self):
		for student in range( len(self.students) ):

			current_student = self.students[student]
			current_leader = self.following_order[student]
			distance = self.FollowDistance

			if current_leader == '0':
				self.Lead(current_student)
			else:
				self.Follow(current_student, current_leader, distance)

	# Everyone follows something
	def everyoneFollow(self, leader, distance):
		for student in self.students:
			self.Follow(student, leader, distance)

	# Everyone flees something
	def everyoneFlee(self, enemy_list, distance):
		for student in self.students:
			enemy = student.findNearest(enemy_list)
			student.flee(enemy, distance)

	# Everyone hunts something
	def everyoneHunt(self, target_list, distance):
		for student in self.students:
			target = student.findNearest(target_list)
			student.follow(target, distance)

# --- TYPES OF SCHOOLS --- (following patterns / heirarchies) #

# Everyone follows a single Monarch
class Monarch(School):
	def createFollowingOrder(self):
		# Start with blank list
		self.following_order = []

		for x in self.students:
			self.following_order.append(self.students[0])
		#add student1 to the beginning of the list, as "0"
		self.following_order[0] = "0"
		return self.following_order
# each leader is followed by 2 fish, in a tree branching structure
class Tree(School):
	def createFollowingOrder(self):
		self.following_order = []
		self.branches = []

		self.following_order.append("0")		# First student is main leader

		n = len(self.students)
		for i in range( (n-(n%2)) / 2 ):		# Number of branches is ((n-(n%2)) / 2)
			self.branches.append(self.students[i])
			# Add latest branch leader (twice)
			self.following_order.append(self.branches[-1])
			self.following_order.append(self.branches[-1])
		return self.following_order
# Everyone follows the previous fish in line
class Line(School):
	def createFollowingOrder(self):
		# Start with blank list
		self.following_order = []

		for x in self.students:
			self.following_order.append(x)
		#add student1 to the beginning of the list, as "0"
		self.following_order.insert(0,"0")
		self.following_order.pop()				#remove last student (has no followers)
		return self.following_order
# Same as line, but first fish follows last fish (creating a circle)
class Circle(School):
	def createFollowingOrder(self):
		# Start with blank list
		self.following_order = []

		for x in self.students:
			self.following_order.append(x)
		# make first in list follow last in list
		self.following_order.insert(0, self.following_order.pop())
		return self.following_order
# Follow closest fish
class Neighbor(School):
	def createFollowingOrder(self):
		self.following_order = []
	def automate(self):
		for student in self.students:
			# each fish follows nearest fish in school
			self.Follow( student, student.findNearest(self.students), self.FollowDistance )
# Same as Neighbor, but keep personal space
class ShyNeighbor(Neighbor):
	def automate(self):
		Neighbor.automate(self)
		for student in self.students:
			nearest = student.findNearest(self.students)
			if student.getDistance(nearest) <= self.FollowDistance:
				#student.flee( student.findNearest(self.students), 1 )
				student.flee( nearest, self.FollowDistance - 1 )


# ------- GENERATORS ------- #

# Create an Abstract Factory that can create schools
class SchoolFactory(object):
	def __init__(	self, SchoolType=Tree, SchoolSize=20, SchoolCenter=[HEIGHT/2,WIDTH/2],
					AnimalType=SeaMonkey, FollowType='calmRandomFollow', FollowDistance=2,
					LeadType='randomMove', Color='red'):
		self.SchoolType = SchoolType
		self.SchoolSize = SchoolSize
		self.SchoolCenter = SchoolCenter	#[y,x]
		self.AnimalType = AnimalType
		self.FollowType = FollowType
		self.FollowDistance = FollowDistance
		self.LeadType = LeadType
		self.Color = Color

	def CreateSchool(self, **kwargs):
		self.SchoolType = kwargs.get('SchoolType', self.SchoolType)
		self.SchoolSize = kwargs.get('SchoolSize', self.SchoolSize)
		self.SchoolCenter = kwargs.get('SchoolCenter', self.SchoolCenter)	#[y,x]
		self.AnimalType = kwargs.get('AnimalType', self.AnimalType)
		self.FollowType = kwargs.get('FollowType', self.FollowType)
		self.FollowDistance = kwargs.get('FollowDistance', self.FollowDistance)
		self.LeadType = kwargs.get('LeadType', self.LeadType)
		self.Color = kwargs.get('Color', self.Color)

		# Create list of students and instantiate
		i=0
		self.students = []
		self.following_order = []

		while i < self.SchoolSize:
			# Instantiate the current student
			student = \
			self.AnimalType( 	[	self.SchoolCenter[0]+((i%2)*((-1)**i)), 		\
									self.SchoolCenter[1]+((i%3)*((-1)**i))		], 	\
								self.Color)

			# Add current student to list of students
			self.students.append(student)
			# Draw current student
			self.students[-1].draw()

			# iterate
			i += 1

		# For instantiating School
		return self.SchoolType(self.students, self.LeadType, self.FollowType, self.FollowDistance)

# Generates random objects for start
class Generator(object):
	def __init__(self):

		self.colors = ['red','green','blue','cyan','magenta','white']

		# Bounds 
		self.left = 1
		self.right = WIDTH - 1
		self.top = Water.position + 1
		self.bottom = HEIGHT - 1

	def generate(self, type_list, pos_bounds, n_bounds, color_list, gen_list):
		for species in type_list:

			n = randint(n_bounds[0], n_bounds[1])
			if n != 0:
				i = 0
				while i < n:
					y = 0
					x = 0
					color = choice(color_list)
					current_item = species([y,x], color)

					# To get size of current species being drawn
					if i == 0:
						current_item.getPicture()
						current_item_size = current_item.size

					y = randint(pos_bounds[0][0], pos_bounds[0][1])
					x = randint(pos_bounds[1][0], pos_bounds[1][1] - current_item_size[1])
					current_item.position = [y,x]
					gen_list.append(current_item)
					# NonMovingThings won't draw themselves upon instantiation, so draw now
					if isinstance(current_item, NonMovingThing):
						current_item.draw()
					i += 1

	def DrawList(self, draw_list):
		for item in draw_list:
			item.draw()

# Good for generating seafloor background objects (dunes, coral, etc.)
class SeafloorGenerator(Generator):
	def __init__(self):
		Generator.__init__(self)
		self.left = -7
		self.right = WIDTH + 7
		self.bottom = HEIGHT + 1
		self.top = Sand.position + 1

		self.dune_list = [SmallDune, BigDune]
		self.coral_list = [TreeCoral, BrainCoral]
		self.kelp_list = [Kelp, LongKelp]

# Good for generating fish and whales
class EcosystemGenerator(Generator):
	def __init__(self):
		Generator.__init__(self)
		self.left = 1
		self.right = WIDTH - 1
		self.bottom = HEIGHT - 1
		self.top = Water.position + 1

		self.fish_list = [SeaMonkey, Minnow, AngelFish, Tuna, Baracuda]
		self.whale_list = [Whale, BabyWhale]
		self.bottom_list = [Snail, SeaUrchin]


# ------- HELPER FUNCTIONS ------- #

# randomly create bubbles to float up
def create_bubbles():
	global bub
	#randomly create bubbles
	if bub % randint(1,15) == 5:
		bub_pos = [HEIGHT-5, randint(1, WIDTH -3)]
		bub_list.append(Bubble(bub_pos, 'cyan'))
	bub += 1
	#recycle list
	if len(bub_list) >= 30:
		del(bub_list[:20])
		bub = 1

# group a school of fish around a random coral every now and then 
def group_around_coral(school, period, stay):
	global cor, coral_list
	if cor % period == 0:
		school.desire = choice(coral_list)
	if cor % period < search_time :
		for student in school.students:
			if cor % period < stay:
				if randint(1,2) == 1:
					student.randomFollow(school.desire, 4)
			else:
				student.randomFollow(school.desire, 4)

# generate a number of fish schools, each one randomized
def generate_schools(number_of_schools, factory, school_list, lower_bound, upper_bound):
	global School_Types, School_centers, Follow_Types, Lead_Types, School_Colors
	i=0
	while i < number_of_schools:
		i+=1
		school_list.append( factory.CreateSchool(	SchoolType=choice(School_Types),
													SchoolSize=randint(lower_bound, upper_bound),
													SchoolCenter=choice(School_Centers),
													FollowType=choice(Follow_Types),
													LeadType=choice(Lead_Types),
													Color=choice(School_Colors)
												) )

# get rid of elements generated that do not show up on screen
def remove_peripherals(*args):
	for element_list in args:
		for element in element_list:
			if element.position[1] + element.size[1] < 1 or \
			element.position[1] - element.size[1] > WIDTH-1:
				element_list.remove(element)


##### MAIN #####

#----------------------------------------------------------------------------------
# CREATE BACKGROUND

Aquarium = Window("blue")

Water = Surface(HEIGHT*1/7, "cyan")
Water.draw()
Water.drawAbove()

sand_position = choice(range(HEIGHT*3/4, HEIGHT*6/7))
sand_color = choice(['yellow', 'white', 'red', 'yellow'])
Sand = Surface(sand_position, sand_color)

kelp_color = sand_color
while kelp_color == sand_color:
	kelp_color = choice(['green', 'cyan', 'red', 'magenta', 'blue', 'green'])


# Hide the cursor
os.system('echo -ne "\x1b[?25l"')

############################################################################
# generate(self, type_list, pos_bounds, n_bounds, color_list, gen_list)
############################################################################

# The order in which things are drawn goes from background -> midground -> foreground
SF = SeafloorGenerator()
Eco = EcosystemGenerator()

scale = WIDTH/55
if scale < 1:
	scale = 1

volume = WIDTH * HEIGHT
v_scale = volume / 100

#.....BACKGROUND.....#
BG_Dunes = []
SF.generate(	[SmallDune,BigDune,HugeDune,SlopedDune,SlantedDune], [ [HEIGHT*2/3, HEIGHT-1], [SF.left, SF.right] ], \
				[2,4*scale], [sand_color], BG_Dunes)

BG_Kelp = []
SF.generate(	[Kelp], [ [SF.top-12, SF.bottom-10], [2, WIDTH-2] ], \
				[1,3*scale], [kelp_color], BG_Kelp)

# creat a consolidated list of Background objects
BG_List = BG_Dunes + BG_Kelp


#.....MIDGROUND.....#
# Draw sand 
Sand.drawUnder()

MG_Dunes = []
SF.generate(	[SmallDune,BigDune,HugeDune,SlopedDune,SlantedDune], [ [Sand.position-3, HEIGHT-1], [SF.left, SF.right] ], \
				[2,4*scale], [sand_color], MG_Dunes)

MG_TreeCoral = []
SF.generate(	[TreeCoral], [ [SF.top, SF.bottom], [SF.left, SF.right] ], \
				[3,8*scale], ['red','magenta','blue','cyan'], MG_TreeCoral)

MG_BrainCoral = []
SF.generate(	[BrainCoral], [ [SF.top, SF.bottom], [SF.left, SF.right] ], \
				[1,2*scale], ['red','magenta','blue','cyan'], MG_BrainCoral)

MG_Kelp = []
SF.generate(	[Kelp], [ [SF.top-12, SF.bottom-10], [2, WIDTH-2] ], \
				[1,2*scale], [kelp_color], MG_Kelp)

# creat a consolidated list of Background objects
MG_List = MG_Dunes + MG_TreeCoral + MG_BrainCoral + MG_Kelp


#.....FOREGROUND.....#

FG_Kelp = []
SF.generate(	[LongKelp], [ [Water.position+1, HEIGHT*2/3], [2, WIDTH-2] ], \
				[1*scale,3*scale], [kelp_color], FG_Kelp)

FG_Dunes = []
SF.generate(	[HugeDune,SlopedDune,SlantedDune], [ [HEIGHT-6, HEIGHT-2], [SF.left, SF.right] ], \
				[1*scale,2*scale], [sand_color], FG_Dunes)

# creat a consolidated list of Background objects
FG_List = FG_Kelp + FG_Dunes 



#.....ECOSYSTEM.....#

Eco_Fishies = []
Eco.generate(	[Minnow, AngelFish, Tuna], [ [Eco.top, Eco.bottom], [Eco.left, Eco.right] ], \
				[1,3], SF.colors, Eco_Fishies)

Eco_Baracuda = []
if WIDTH > 30:
	Eco.generate(	[Baracuda], [ [Eco.top, Eco.bottom], [Eco.left, Eco.right] ], \
					[0,1], SF.colors, Eco_Baracuda)

Eco_Whales = []
Eco_BabyWhales = []
Eco_BabyWhaleFollower = []
if WIDTH > 45:
	Eco.generate(	[Whale], [ [Eco.top, Eco.bottom], [Eco.left, Eco.right] ], \
					[0,2], ['blue','white','cyan'], Eco_Whales)

	Eco.generate(	[BabyWhale], [ [Eco.top, Eco.bottom], [Eco.left, Eco.right] ], \
					[0,2], ['blue','white','cyan'], Eco_BabyWhales)

	# For making a baby whale follow its mother
	if len(Eco_Whales) == 2:
		if len(Eco_BabyWhales) > 0:
			# Consolidate list
			Eco_BabyWhaleFollower.append( Eco_BabyWhales[-1] )
			# Make calf same color as mother
			Eco_BabyWhaleFollower[0].color = Eco_Whales[0].color
	# Add the rest of the baby whales to the Eco_Whales list
	Eco_Whales += Eco_BabyWhales

Eco_BottomFeeders = []
Eco.generate(	[Snail, SeaUrchin], [ [Sand.position+1, HEIGHT-1], [SF.left, SF.right] ], \
				[1*scale,3*scale], SF.colors+['yellow'], Eco_BottomFeeders)

Eco.generate(	[Lobster], [ [Sand.position+1, HEIGHT-1], [SF.left, SF.right] ], \
				[1*scale,3*scale], ['red','magenta'], Eco_BottomFeeders)

for snail in Eco_BottomFeeders:
	snail.speed = 1
	snail.direction[0] = 0
	snail.direction[1] = choice([-1,1])

# creat a consolidated list of Background objects
Eco_List = Eco_Fishies + Eco_Baracuda + Eco_Whales + Eco_BabyWhales + \
		   Eco_BabyWhaleFollower + Eco_BottomFeeders



#----------------------------------------------------------------------------------
#set eveything so far as the background environment
Aquarium.aquarium_box_background = deepcopy(Aquarium.aquarium_box)
#----------------------------------------------------------------------------------

# Remove all coral that are off-screen (so fish don't try to follow an invisible coral)
remove_peripherals(BG_Kelp, FG_Kelp, MG_TreeCoral, MG_BrainCoral)

###############################################################################################
# SCHOOL FACTORY
###############################################################################################
# 								SchoolType, SchoolSize, SchoolCenter, AnimalType, \
# 								FollowType, FollowDistance, LeadType, Color

max_fish = v_scale

School_Types = [Monarch, Tree, Line, Circle, Neighbor, ShyNeighbor]
School_Colors = ['blue','cyan','green','red','magenta','white']
Follow_Types = ['calmRandomFollow', 'randomFollow']
Lead_Types = ['calmRandomMove', 'randomMove']
School_Centers = [	[HEIGHT*1/3,WIDTH*1/7],
					[HEIGHT*1/3,WIDTH*5/7],
					[HEIGHT*1/2,WIDTH*1/7],
					[HEIGHT*1/2,WIDTH*5/7],
					[HEIGHT*2/3,WIDTH*1/7],
					[HEIGHT*2/3,WIDTH*5/7]]

# --- SEA MONKEYS! ---#
#number_of_sea_monkey_schools = 3
number_of_sea_monkey_schools = randint(2,8)
fps_avg = ( max_fish / number_of_sea_monkey_schools )
fps_min = int(fps_avg / 2)       # 20
fps_max = int(fps_avg * 1.5)     # 60

sea_monkey_schools = []
SeaMonkeyFactory = SchoolFactory(AnimalType=SeaMonkey)
generate_schools(number_of_sea_monkey_schools, SeaMonkeyFactory, sea_monkey_schools, fps_min,fps_max )


# --- MINNOWS! --- #
#number_of_minnow_schools = 1
number_of_minnow_schools = randint(1,number_of_sea_monkey_schools/2)
fps_avg = ( max_fish / 20 )
fps_min = int(fps_avg / 2)       # 10
fps_max = int(fps_avg * 1.5)     # 20

minnow_schools = []
MinnowFactory = SchoolFactory(AnimalType=Minnow, LeadType='calmRandomMove')
generate_schools(number_of_minnow_schools, MinnowFactory, minnow_schools, fps_min,fps_max )

schools = sea_monkey_schools + minnow_schools
###############################################################################################

##### LOOP #####

# initial bubble list
bub = 1
bub_list = []

#variable for changing which coral the school is going around
cor = 0
#list of corals to choose from (when following)
coral_list = BG_Kelp + MG_Kelp + FG_Kelp + MG_BrainCoral + MG_TreeCoral

while True:
	# Get times for waiting between frames
	t_a = time()
	t_b = time()

	# Move all (independent) creatures
	for bottom_feeder in Eco_BottomFeeders:
		if randint(1,50) == 1:
			bottom_feeder.randomMove()
		else:
			bottom_feeder.draw()

	# Draw coral and kelp in midground (to cover up BottomFeeders)
	SF.DrawList(MG_TreeCoral)
	SF.DrawList(MG_Kelp)

	for fish in Eco_Fishies:
		fish.randomMove()
		for baracuda in Eco_Baracuda:
			fish.flee(baracuda, 3)
		for whale in Eco_Whales:
			fish.flee(whale, 6)

	for baracuda in Eco_Baracuda:
		baracuda.calmRandomMove()
		baracuda.follow(baracuda.findNearest(Eco_Fishies), 2)
		baracuda.flee(baracuda.findNearest(Eco_Whales), 4)

	for whale in Eco_Whales:
		whale.calmRandomMove()		# This includes the baby whale follower (adds spunk)

	# If there's a baby whale following a mother whale, follow it
	if len(Eco_BabyWhaleFollower) == 1:
		Eco_BabyWhaleFollower[0].randomFollow(Eco_Whales[0], 7)

	# Schools
	for school in schools:
		school.automate()

	#------------------------------------------------------------
	# Alternate between grouping around different corals
	for school in schools:
		period = schools.index(school) * 100 + 500
		stay = schools.index(school) * 10 + 50
		group_around_coral(school, period, stay)
	
	if cor >= 10000:
		cor = 0		#reset count
	cor += 1		#increment count
	#------------------------------------------------------------


	# ----------- SCHOOL SPECIAL BEHAVIORS -----------#

	# All fish flee from whales
	for school in schools:
		enemy_list = Eco_Whales + Eco_Baracuda
		school.everyoneFlee(enemy_list, 4)

	# All Sea Monkies flee from Minnows
	for sm_school in sea_monkey_schools:
		for m_school in minnow_schools:
			sm_school.everyoneFlee(m_school.students, 3)
	
	# All Minnows hunt Sea Monkeys
	for m_school in minnow_schools:
		target_list = []
		for sm_school in sea_monkey_schools:
			for student in sm_school.students:
				target_list.append(student)
		m_school.everyoneHunt(target_list, 2)


	# ----------- RE-DRAW ALL SWIMMERS -----------#
	# (some images may have been erased in "move()")
	students = []						# get list of all fish in schools
	for school in schools:
		students += school.students
	# draw every swimming creature
	for creature in Eco_Fishies + Eco_Baracuda + \
                    Eco_Whales + Eco_BabyWhales + Eco_BabyWhaleFollower + \
                    students:
		creature.draw()


	#  ----- ACTIVE FOREGROUND ----- #

	# randomly create bubbles to float up
	create_bubbles()
	# Drift all bubbles (in foreground)
	for bubble in bub_list:
		bubble.drift()

	# Draw long kelp in the front
	SF.DrawList(FG_Kelp[scale:])
	SF.DrawList(FG_Dunes)
	SF.DrawList(FG_Kelp[:scale])


	# Wait to display aquarium
	while (t_b - t_a) < DELAY:
		t_b = time()
	Aquarium.display()
