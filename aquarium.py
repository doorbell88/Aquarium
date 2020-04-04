# AQUARIUM
"""
--------------------------------------------------------------------------------
A text-based aquarium to view in terminal with a randomized background and
ecosystem.

You can customize the features and amount of everything in the "CUSTOMIZE"
section below.
--------------------------------------------------------------------------------
"""

from random import choice
from random import randint as random_int
from time import sleep, time
from datetime import datetime
from copy import deepcopy
from termcolor import colored
import os
import sys
import signal
import subprocess


# wrapper for random.randint() --> avoids errors with float args
def randint(a,b):
    X = int(min(a,b))
    Y = int(max(a,b))
    return random_int(X,Y)


# get size of terminal
WIDTH  = int( subprocess.check_output(['tput','cols']) )
HEIGHT = int( subprocess.check_output(['tput','lines']) ) - 1
VOLUME = WIDTH * HEIGHT


#================================= CUSTOMIZE ===================================

#------------------------------- time and space --------------------------------
# for screen refresh rate
DELAY                           = 0.08
# used for scaling time fish periodically take to swim towards a coral/kelp
coral_search_time               = (WIDTH + HEIGHT) // 2
# scale (for how much stuff (eg. kelp) can fit in the terminal width)
scale                           = WIDTH // 40
# avoid divide-by-zero errors
scale                           = 1 if scale == 0 else scale


#----------------------------- optional features -------------------------------
draw_sand                       = True
draw_water                      = False
bubbles                         = True
underwater_hill                 = True
periodic_ocean_current_drift    = False
clock_fish                      = False
explorer_school                 = False

# Generate random word bubbles
word_bubbles                    = False     # "bubbles" must be True to work
word_file                       = "/usr/share/dict/words"

# print info about aquarium (can be toggled with ctrl-\)
verbose                         = False

# If set to a positive number, creatures can go outside of the "box"
MARGIN_WATER                    = 50
MARGIN_SAND                     = 5


#----------------------------------- colors ------------------------------------
all_possible_colors = ['red','green','blue','cyan','magenta','yellow','white']
#all_possible_colors+= ['grey']
#-------------------------------------------------------------------------------
window_colors                   = ['blue','cyan']
water_colors                    = ['cyan']
bubble_colors                   = ['cyan']
sand_colors                     = ['yellow','white','red','magenta','green']#,'grey']
kelp_colors                     = [x for x in all_possible_colors if x != 'grey']
coral_colors                    = all_possible_colors
creature_colors                 = all_possible_colors
lobster_colors                  = ['red','magenta']
snail_colors                    = all_possible_colors
sea_urchin_colors               = all_possible_colors
fish_school_colors              = all_possible_colors
whale_colors                    = ['blue','white','cyan']#,'grey']
jellyfish_colors                = ['white','cyan']
clock_fish_colors               = all_possible_colors


#---------------------------------- scenery ------------------------------------
# ... background
background_dunes                = randint( 0 , 3*scale ) #randint( 0 , 4*scale )
background_kelp                 = randint( 0 , 3*scale )
hill_kelp                       = randint( 0 , 2*scale )
hill_coral                      = randint( 0 , 3*scale )
# ... midground
midground_dunes                 = randint( 0 , 1*scale ) #randint( 0 , 4*scale )
midground_tree_coral            = randint( 0 , 8*scale )
midground_brain_coral           = randint( 0 , 2*scale )
midground_kelp                  = randint( 0 , 2*scale )
# ... foreground
foreground_dunes                = randint( 0 , 1*scale ) #randint( 0 , 3*scale )
foreground_kelp                 = randint( 0 , 2*scale )
# ... sand
sand_position                   = randint( HEIGHT*2//3 , HEIGHT*6//7 )
# ... water
water_position                  = HEIGHT*1//7
bubble_frequency                = 30     # (higher number means less frequent)


#------------------------------------ life -------------------------------------
# ... fish schools
#...............................................................................
all_school_types = ['Monarch','Tree','Line','Circle','Neighbor','ShyNeighbor']
#...............................................................................
school_types                    = all_school_types
max_fish                        = VOLUME // 200
min_fish_per_school             = 5
number_of_sea_monkey_schools    = randint( 2 , 5 )
number_of_minnow_schools        = randint( 1 , number_of_sea_monkey_schools/2 )
# ... independent swimmers
number_of_whales                = randint( 0 , 1 ) if VOLUME > 1500 else 0
number_of_baby_whales           = randint( 0 , 1 ) if VOLUME > 1000 else 0
number_of_barracudas            = randint( 0 , 1 ) if VOLUME > 800  else 0
number_of_tuna                  = randint( 2 , 4 )
number_of_angelfish             = randint( 2 , 4 )
number_of_minnows               = randint( 0 , 4 )
number_of_seamonkeys            = randint( 0 , 4 )
number_of_jellyfish             = randint( 4 , 10 )
# ... bottomfeeders
number_of_snails                = randint( 1 , 3*scale )
number_of_sea_urchins           = randint( 1 , 2*scale )
number_of_lobsters              = randint( 1 , 2*scale )

#===============================================================================


################################################################################
################################## FUNCTIONS ###################################

#------------------------- SPECIAL HANDLING FUNCTIONS --------------------------

# catch SIGINT ( ctrl-c )
def signal_SIGINT_handler(signum, frame):
    # (Show the cursor again)
    os.system('echo "\x1b[?25h"')
    os.system('tput sgr0')
    sys.exit()
signal.signal(signal.SIGINT, signal_SIGINT_handler)

# catch SIGQUIT ( ctrl-\ )
def signal_SIGQUIT_handler(signum, frame):
    global verbose
    # Toggle verbosity (info about aquarium)
    verbose = not verbose
signal.signal(signal.SIGQUIT, signal_SIGQUIT_handler)

def debug_printout():
    subprocess.call(['tput', 'cup', '0', '0'])
    print("reduce_clock:  {}".format(reduce_clock))
    print("frame time:    {}".format((t_b - t_a)))
    print()
    print("{:12}  {:4}  {}".format("SCHOOL TYPE", "SIZE", "COLOR"))
    print("{}".format(28*"-"))
    for school in schools:
        try:
            color = school.students[0].color
        except:
            color = ''

        print("{:12}  {:4}  {}".format( school.__class__.__name__, 
                                        len(school.students),
                                        color,
                                        school.following_order, ))

#---------------------------- FUNCTION DECORATORS ------------------------------

def speed_check_before(movement_function):
    def wrapper(self, *args, **kwargs):
        # keep speed from exploding
        if self.speed >= self.maxspeed:
            self.speed = self.maxspeed
        if self.speed < 0:
            self.speed = 0
        movement_function(self, *args, **kwargs)    # flee or follow
    return wrapper

def speed_check_after(movement_function):
    def wrapper(self, *args, **kwargs):
        movement_function(self, *args, **kwargs)    # flee or follow
        # keep speed from exploding
        if self.speed >= self.maxspeed:
            self.speed = self.maxspeed
        if self.speed < 0:
            self.speed = 0
    return wrapper

def turn_around_water(movement_function):
    def wrapper(self, *args, **kwargs):
        left_wall   = 1 - MARGIN_WATER
        right_walL  = WIDTH + MARGIN_WATER
        top_wall    = Water.position + 1
        bottom_waLL = HEIGHT - 1
        #--------------------------------------------------------------------------------
        # TURN AROUND (X)
        # left wall
        if self.position[1] < (self.speed + left_wall):
            self.direction[1] = 1
        # right wall
        if self.position[1] > (right_walL - (int(self.direction[1] * self.speed) + self.size[1] + 1) ):
            self.direction[1] = -1
        #--------------------------------------------------------------------------------
        # TURN AROUND (Y)
        # top (water)
        if self.position[0] < ( self.speed + top_wall ):
            self.direction[0] = 1
        #bottom (sand)
        if self.position[0] > (bottom_waLL - (int(self.direction[0] * self.speed) + self.size[0] + 1) ):
            self.direction[0] = -1
        #--------------------------------------------------------------------------------
        movement_function(self, *args, **kwargs)              # flee or follow
    return wrapper

def turn_around_sand(movement_function):
    def wrapper(self, *args, **kwargs):
        left_wall   = 1 - MARGIN_SAND
        right_walL  = WIDTH + MARGIN_SAND
        top_wall    = Sand.position + 1
        bottom_waLL = HEIGHT - 1
        #--------------------------------------------------------------------------------
        # TURN AROUND (X)
        # left wall
        if self.position[1] < (self.speed + left_wall):
            self.direction[1] = 1
        # right wall
        if self.position[1] > (right_walL - (int(self.direction[1] * self.speed) + self.size[1] + 1) ):
            self.direction[1] = -1
        #--------------------------------------------------------------------------------
        # TURN AROUND (Y)
        # top (water)
        if self.position[0] < ( self.speed + top_wall ):
            self.direction[0] = 1
        #bottom (sand)
        if self.position[0] > (bottom_waLL - (int(self.direction[0] * self.speed) + self.size[0] + 1) ):
            self.direction[0] = -1
        #--------------------------------------------------------------------------------
        movement_function(self, *args, **kwargs)              # flee or follow
    return wrapper


################################################################################
################################### CLASSES ####################################

# Display of the aquarium
class Window(object):
    def __init__(self, border_color):
        self.border_color = border_color
        self.width = WIDTH
        self.height = HEIGHT

        # create lists for "screen"
        self.stage = []
        self.background = []

        # clear screen
        os.system('clear')

        # create blank aquarium box
        for y in range(self.height):
            self.stage.append([" "] * self.width)

        #draw aquarium border
        for y in range(0, self.height):
            for x in range(0, self.width):
                #top
                self.stage[0][x] = \
                        colored( "=", self.border_color )
                #bottom
                self.stage[self.height-1][x] = \
                        colored( "=", self.border_color )
                #left
                self.stage[y][0] = \
                        colored( "|", self.border_color )
                #right
                self.stage[y][self.width-1] = \
                        colored( "|", self.border_color )

    def display(self):
        # Move cursor back to top left
        os.system('tput cup 0 0')
        # print
        for row in range( len(self.stage) ):
            print("".join(self.stage[row]))

# Things that can be drawn in the aquarium
class Thing(object):
    def __init__(self, position, color):
        self.position = position
        self.color = color

        # self.direction = [0,0]
        self.size = [0,0]
        self.picture = ['']

    # Get the picture of the object in question, and assign LEFT or RIGHT picture
    def getPicture(self):
        #self.picture = self.right()
        if self.direction[1] < 0:
            self.picture = self.left()
        elif self.direction[1] > 0:
            self.picture = self.right()
        # Get size of the object's picture
        try:
            self.size = [ len(self.picture), len(self.picture[0]) ]
        except:
            self.size = [0,0]

    # Draw the object
    def draw(self):
        self.getPicture()
        for y in range( self.size[0] ):
            for x in range( self.size[1] ):
                if  y + self.position[0] > 0 and \
                    y + self.position[0] < (HEIGHT-1) and \
                    x + self.position[1] > 0 and \
                    x + self.position[1] < (WIDTH-1) and \
                    self.picture[y][x] != " " :          # Avoids drawing a blank box around thing
                        Aquarium.stage[ int(y + self.position[0]) ]\
                                      [ int(x + self.position[1]) ] \
                        = colored(self.picture[y][x], self.color)

    # Remove object (for when it's moving)
    def erase(self):
        self.getPicture()
        for y in range( self.size[0] ):
            for x in range( self.size[1] ):
                if  y + self.position[0] > 0 and \
                    y + self.position[0] < (HEIGHT-1) and \
                    x + self.position[1] > 0 and \
                    x + self.position[1] < (WIDTH-1) :
                        Aquarium.stage[ int(y + self.position[0]) ]\
                                      [ int(x + self.position[1]) ] \
                        = Aquarium.background[ int(y + self.position[0]) ]\
                                             [ int(x + self.position[1]) ]

#------------------------------- MOVING THINGS ---------------------------------

# Moving things (animals, bubbles, ships)
class MovingThing(Thing):
    def __init__(self, position, color):
        self.position = position    # [y,x]
        self.speed = 1
        self.maxspeed = 1
        self.color = color

        # Initiate a start direction of left or right (if direction starts as [0,0]...
        # ... then calmRandomMove objects will stay still)
        self.direction = [0, choice([-1,1])]    # [y,x]
        
        # Initial null values for each object, so that it can be drawn the first time
        self.size = [0,0]
        self.picture = ['']

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
        target_tail = target.position[1]    # give an initial number (to avoid error)
        target_front = target.position[1]   # give an initial number (to avoid error)

        # NonMovingObject has no direction attribute, so default 0 with:  getattr(obj, attr, default)

        # --> TELL WHICH SIDE OF THE TARGET ITS TAIL IS ON:
        # moving LEFT
        if getattr(target, 'direction', [0,0])[1] < 0:
            target_tail = target.position[1] + target.size[1]       #tail is on left
        # moving RIGHT
        elif getattr(target, 'direction', [0,0])[1] >= 0:
            target_tail = target.position[1]                        #tail is on right

        # --> TELL WHICH SIDE OF THE ENEMY ITS MOUTH IS ON:
        # moving LEFT
        if getattr(target, 'direction', [0,0])[1] < 0:
            target_front = target.position[1]                   #mouth is on left
        # moving RIGHT
        elif getattr(target, 'direction', [0,0])[1] >= 0:
            target_front = target.position[1] + target.size[1]  #mouth is on right

        # Calculate distance
        dy = target.position[0] - self.position[0]
        dx_tail = target_tail - self.position[1]
        dx_front = target_front - self.position[1]

        distance_tail_sq = (dx_tail**2) + ((dy//2)**2)
        distance_front_sq = (dx_front**2) + ((dy//2)**2)

        return (dy, dx_tail, dx_front, distance_tail_sq, distance_front_sq)

    # Find nearest individual in a group (list)
    def findNearest(self, group, *arg):
        if len(arg) > 0:
            side = str(arg[0])
        else:
            side = 'tail'

        if side.lower() in ['front', 'mouth']:      # look for front (mouth)
            side_index = 4
        else:                                       # look for tail
            side_index = 3

        # set initial values as very large, so they don't win in a comparison
        dr_current = 500
        dr_previous = 500

        # initial faraway object
        nearest_member = FarawayObject      # FarawayObject has position [-1000, -1000]

        # Go through list, and if a member is nearer the previous nearest, replace nearest_member
        for member in group:

            if member == self:                      # ignore self (don't find distance)
                pass

            # getDistance() returns :
            # [dy, dx_tail, dx_front, distance_tail_sq, distance_front_sq]
            dr_current = self.getDistance(member)[side_index]       # distance to tail or front
            if dr_current == 0:                     # ignore those at same position
                pass
            elif dr_current < dr_previous:          # if current is nearer than previous nearest...
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
            self.direction[1] = abs(self.direction[1]) // self.direction[1]
        # speed
        # self.controlSpeed()
        self.move()

    # Move randomly up and down, but stay moving forward
    @speed_check_before
    def calmRandomMove(self, y_rand=4, stop_rand=50, resume_rand=8, turn_rand=500):
        #only randomize movement in y-direction
        if randint(1,y_rand) == 1:
            self.direction[0] += randint(-1,1)
        if abs(self.direction[0]) > 1:
            self.direction[0] = 0

        #turn around (x-direction) every once in a while
        if turn_rand:
            if randint(1,turn_rand) == 1:
                self.direction[1] *= -1
            
        # sometimes stop x-movement (float and bob for a bit)
        if stop_rand:
            if randint(1,stop_rand) == 1:
                self.direction[1] = 0
            # if not moving in x-direction, resume 
            if self.direction[1] == 0:
                if randint(1,resume_rand) == 1:
                    self.direction[1] = randint(-1,1)

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
        dx = get_distances[1]           # dx_tail
        dr_sq = get_distances[3]        # distance_tail_sq

        # if the radius is greater than the follow distance, go back towards leader
        if dr_sq  >= (distance**2):
            # if dx > distance or dy > distance/2:
            if dy != 0:
                self.direction[0] = ( dy//abs(dy) )
            if dx != 0:
                self.direction[1] = ( dx//abs(dx) )

            self.speed += self.accelerate       # Get back to leader
            # self.move()                       # Move straight to leader

    # Flee from an enemy (i.e. Predator)
    @speed_check_before
    def flee(self, enemy, distance):
        # variable for how much to accelerate when enemy is close
        self.accelerate = 3

        get_distances = self.getDistance(enemy)
        # [dy, dx_tail, dx_front, distance_tail_sq, distance_front_sq]
        dy = get_distances[0]
        dx = get_distances[2]           # dx_front
        dr_sq = get_distances[4]        # distance_front_sq

        # if the radius is less than the flee distance (radius of safety)... Flee for your life!
        if dr_sq <= (distance**2):
            # if dx > distance or dy > distance/2:
            if dy != 0:
                self.direction[0] = -( dy//abs(dy) )
            if dx != 0:
                self.direction[1] = -( dx//abs(dx) )

            # self.speed += self.accelerate     # Get ready to flee quickly
            self.move()                         # Move straight away from the enemy
            # self.speed = self.maxspeed
            self.move()                         # Move straight away from the enemy
            self.move()                         # Move straight away from the enemy

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
class Debris(MovingThing):
    # erase current, increment, draw new
    def move(self):
        if self.position[0] <= ( Water.position ):
            MovingThing.move(self)
            self.erase()
        else:
            MovingThing.move(self)

    # wiggle from left-to-right, randomly
    def drift(self):
        self.direction[1] += randint(-1,1)
        if abs(self.direction[1]) >= 2:
            self.direction[1] = 0
        self.move()

# Fish (and whales etc.) -- things that swim around
class Fish(MovingThing):
    @turn_around_water
    def move(self):
        MovingThing.move(self)

# Snails and Lobsters etc. -- things that move slowly on the ocean floor
class BottomFeeder(MovingThing):
    @turn_around_sand
    def move(self):
        MovingThing.move(self)

#---------------------------------- ANIMALS ------------------------------------

# Fish (smallest)
class SeaMonkey(Fish):
    def __init__(self, position, color):
        MovingThing.__init__(self, position, color)
        self.maxspeed = 2
    
    def left(self):
        if self.direction[0] < 0:
            return  ('`',)
        elif self.direction[0] > 0:
            return  (',',)
        else:
            return  ('-',)
    def right(self):
        if self.direction[1] == 0:
            if self.direction[0] == 0:
                return  ('-',)
            else:
                return  ('\'',)
        else:
            if self.direction[0] < 0:
                return  (',',)
            elif self.direction[0] > 0:
                return  ('`',)
            else:
                return  ('-',)

# Fish (small)
class Minnow(Fish):
    def __init__(self, position, color):
        MovingThing.__init__(self, position, color)
        self.maxspeed = 2

    def left(self):
        return  (
        '<',
        )
    def right(self):
        return  (
        '>',
        )

# Fish (medium)
class AngelFish(Fish):
    def __init__(self, position, color):
        MovingThing.__init__(self, position, color)
        self.maxspeed = 1

    def left(self):
        return  (
        '<(',
        )
    def right(self):
        return  (
        ')>',
        )

# Fish (large)
class Tuna(Fish):
    def __init__(self, position, color):
        MovingThing.__init__(self, position, color)
        self.maxspeed = 2

    def left(self):
        return  (
        '<=(',
        )
    def right(self):
        return  (
        ')=>',
        )

# Fish (long)
class Barracuda(Fish):
    def __init__(self, position, color):
        MovingThing.__init__(self, position, color)
        self.maxspeed = 2

    def left(self):
        return  (
        '<==^=-<',
        )

    def right(self):
        return  (
        '>-=^==>',
        )

# Clock - displays time in 12-hr format
class Clock(Fish):
    def __init__(self, position, color):
        MovingThing.__init__(self, position, color)
        self.maxspeed = 2

    def left(self):
        now         = datetime.now()
        day         = now.day
        hour        = int(now.strftime('%I'))
        minute      = now.minute
        second      = now.second
        ampm        = now.strftime('%p').lower()
        return  (
        '{}:{:02d} {}'.format(hour, minute, ampm),
        )
    def right(self):
        now         = datetime.now()
        day         = now.day
        hour        = int(now.strftime('%I'))
        minute      = now.minute
        second      = now.second
        ampm        = now.strftime('%p').lower()
        return  (
        '{}:{:02d} {}'.format(hour, minute, ampm),
        )

# Whale
class Whale(Fish):
    def __init__(self, position, color):
        MovingThing.__init__(self, position, color)
        self.maxspeed = 1

    def left(self):
        return (                            
        ' _--.-^---_____/',
        '(__`______===== ',
        '    V          \\'               
        )

    def right(self):
        return (                            
        '\\_____---^-.--_ ',
        ' =====______`__)',
        '/          V    '                
        )

# Baby Whale
class BabyWhale(Fish):
    def __init__(self, position, color):
        MovingThing.__init__(self, position, color)
        self.maxspeed = 1

    def left(self):
        return (                            
        ' ________/',
        '(__`u_===\\'     
        )

    def right(self):
        return (                            
        '\\________ ',
        '/===_u`__)'              
        )

# Jellyfish
class Jellyfish(MovingThing):
    def __init__(self, position, color):
        MovingThing.__init__(self, position, color)
        self.speed    = 1
        self.maxspeed = 1
        # each jellyfish swims a little differently
        self.bell_0 = randint(6, 10)
        self.bell_1 = self.bell_0 + randint(1,3)
        self.bell_2 = self.bell_1 + randint(1,3)
        self.bell_3 = self.bell_2 + randint(1,3)
        # start each jellyfish at a different part of the "stroke"
        self.bell = randint(0, self.bell_3)

    @turn_around_water
    def move(self):
        # only move on the "stroke"
        if self.bell == 0:
            # stay moving horizontal mostly
            if randint(1, 10) == 1:
                self.direction[0] = choice([1,-1])
                #---------------------------------------------------------------
                # TURN AROUND (Y)
                    # top (water)
                if self.position[0] < ( Water.position + (self.speed + 1) ):
                    self.direction[0] = 1
                    #bottom (sand)
                if self.position[0] > ( (HEIGHT-1) - \
                        (int(self.direction[0]*self.speed)+self.size[0]+1) ):
                    self.direction[0] = -1
                #---------------------------------------------------------------
            else:
                self.direction[0] = 0
            # Move
            MovingThing.move(self)
        else:
            # set direction back to horizontal
            self.direction[0] = 0
            MovingThing.erase(self)
            MovingThing.draw(self)

        # increment bell counter
        self.bell = (self.bell+1) % self.bell_3

    def left(self):
        if self.bell < self.bell_0:
            return self.left_0()
        elif self.bell < self.bell_1:
            return self.left_1()
        elif self.bell < self.bell_2:
            return self.left_2()
        elif self.bell < self.bell_3:
            return self.left_3()

    def right(self):
        if self.bell < self.bell_0:
            return self.right_0()
        elif self.bell < self.bell_1:
            return self.right_1()
        elif self.bell < self.bell_2:
            return self.right_2()
        elif self.bell < self.bell_3:
            return self.right_3()

    def left_0(self):
        return (                            
        '(=',
        )
    def left_1(self):
        return (                            
        '{=',
        )
    def left_2(self):
        return (                            
        '[=',
        )
    def left_3(self):
        return (                            
        '|=',
        )

    def right_0(self):
        return (                            
        '=)',
        )
    def right_1(self):
        return (                            
        '=}',
        )
    def right_2(self):
        return (                            
        '=)',
        )
    def right_3(self):
        return (                            
        '=|',
        )


# Snail
class Snail(BottomFeeder):
    def __init__(self, position, color):
        MovingThing.__init__(self, position, color)
        self.maxspeed = 1

    def left(self):
        return  (
        '@',
        )
    def right(self):
        return  (
        '@',
        )

# Sea Urchin
class SeaUrchin(BottomFeeder):
    def __init__(self, position, color):
        MovingThing.__init__(self, position, color)
        self.maxspeed = 1

    def left(self):
        return (                            
        '  .w.  ',
        '_\ | /_',
        '> ,*, <'     
        )

    def right(self):
        return (                            
        '  .v.  ',
        '_\ | /_',
        '> ,*, <'     
        )

# Lobster
class Lobster(BottomFeeder):
    def __init__(self, position, color):
        MovingThing.__init__(self, position, color)
        self.maxspeed = 1

    def left(self):
        if randint(0,20) == 1:
            return (                            
            '\./  ',
            '>M=={',
            '     '       
            )
        elif randint(0,20) == 2:
            return (                            
            '_|.  ',
            '>M=={',
            '     '       
            )
        else:
            return (                            
            '\|.  ',
            '>M=={',
            '     '       
            )

    def right(self):
        if randint(0,20) == 1:
            return (                            
            '  \./',
            '}==M<',
            '     '       
            )
        elif randint(0,20) == 2:
            return (                            
            '  .|_',
            '}==M<',
            '     '       
            )
        else:
            return (                            
            '  .|/',
            '}==M<',
            '     '       
            )

#----------------------------------- DEBRIS ------------------------------------

# Bubbles!
class Bubble(Debris):
    def __init__(self, position, color):
        global word_bubbles

        self.maxspeed = 1

        Debris.__init__(self, position, color)
        self.position = position
        self.color = color
        self.direction = [-1,0]     # float up

        now              = datetime.now()
        self.year        = now.year
        self.month       = now.month
        self.month_name  = now.strftime('%b')
        self.day         = now.day
        self.hour        = int(now.strftime('%I'))
        self.minute      = now.minute
        self.second      = now.second
        self.ampm        = now.strftime('%p').lower()

        try:
            self.word = u"{}".format(choice(word_list)).replace("'s","")
        except:
            self.word = "puppies"

        # choose between possible bubble images
        self_images = [
                        [self._left1, self._right1],
                        [self._left2, self._right2],
                        [self._left3, self._right3]
                      ]

        if word_bubbles == True:
            self_images.append([self._words, self._words])


        self.left, self.right = choice(self_images)

    # First set of bubble images
    def _left1(self):
        return  (
        'o O',
        ' : ',
        )
    def _right1(self):
        return  (
        'o .',
        '.%s ' %(degree_symbol),
        ) 

    # Second set of bubble images
    def _left2(self):
        return  (
        'o. ',
        '   ',
        ' .%s' %(degree_symbol),
        )
    def _right2(self):
        return  (
        ' o.',
        '.  ',
        '  .',
        ) 

    # Third set of bubble images
    def _left3(self):
        return  (
        '%s :' %(degree_symbol),
        ' . ',
        )
    def _right3(self):
        return  (
        ' %s:' %(degree_symbol),
        '.  ',
        ) 

    # Bubble shows the time
    def _clock(self):
        #return  (
        #'{}:{:02d}:{:02d}'.format(hour, minute, second),
        #)
        return  (
        '{}:{:02d} {}'.format(self.hour, self.minute, self.ampm),
        )

    # Bubble shows the date
    def _date(self):
        return  (
        '{} {}'.format(self.month_name, self.day),
        )

    # Random words
    def _words(self):
        return  (
        '{}'.format(self.word),
        )

#------------------------------ NONMOVING THINGS -------------------------------

# Nonmoving things (sand features, rocks, etc.)
class NonMovingThing(Thing):
    def __init__(self, position, color):
        # self.size = size          # [y,x]
        self.position = position    # [y,x]
        self.color = color

        self.direction = [0,0]
        self.size = [0,0]
        self.picture = ['']

        # self.draw()

    # Get the picture of the object in question, and assign LEFT or RIGHT picture
    def getPicture(self):
        self.picture = self.image()
        # Get size of the object's picture
        self.size = [ len(self.picture), len(self.picture[0]) ]

# Surfaces (for sea and sand)
class Surface(object):
    def __init__(self, position, color):
        self.position = position    # [y,x]
        self.color = color

    #draw line (override NonMovingThing .draw() method
    def draw(self):
        #draw line
        x = 1
        y = int(self.position)
        while x < (WIDTH - 1):
            Aquarium.stage[y][x] = colored( '~', self.color)
            x += 1

    #draw fill under line
    def drawUnder(self):
        #draw under line
        x = 1
        y = int(self.position + 1)
        while y < (HEIGHT - 1):
            while x < (WIDTH - 2):
                Aquarium.stage[y][x] = colored( ',', self.color)
                x += (HEIGHT - self.position) // (y - self.position)  #1
                #Aquarium.stage[y][x] = ' '
                x += 1   #1
            #x = (y % 2) + 1
            x = randint(1, 3)
            y += 1

    #draw fill above line
    def drawAbove(self):
        #draw under line
        x = 1
        y = 1
        while y < (self.position):
            while x < (WIDTH - 1):
                Aquarium.stage[y][x] = colored( '-', self.color)
                x += 6
            x = 3*(y % 2) + 1
            y += 1

#--------------------------- NONMOVING DECORATIONS -----------------------------

# Dune Class
class Dune(NonMovingThing):
    # Draw the object, but omit the blank areas on the sides (which would create a blank box)
    def draw(self):
        self.getPicture()
        for y in range( self.size[0] ):
            for x in range( self.size[1] ):
                if  y + self.position[0] > 1 and \
                    y + self.position[0] < (HEIGHT-1) and \
                    x + self.position[1] > 1 and \
                    x + self.position[1] < (WIDTH-1) :
                    if self.picture[y][x] != 'R':        # edges of dune drawing should be ommitted
                        Aquarium.stage[ y + self.position[0] ][ x + self.position[1] ] \
                        = colored(self.picture[y][x], self.color)

# Dunes
class SmallDune(Dune):
    def image(self):
        return (                            
        'RRR.~""~.RRR',
        'RR/; . . \RR',
        '~`; . . . `~'                
        )

class BigDune(Dune):
    def image(self):
        return (                            
        'RRRRRRR,.~"""""~. ,RRRRRR',
        'RRRR/; . . . . . . .\RRRR',
        'RR/;. . . . . . . . . \RR',              
        '~`; . . . . . . . . . .`~'               
        )

class HugeDune(Dune):
    def image(self):
        return (                            
        'RRRRRR,.~"""""""~. ,RRRRRR',
        'RRRR/; . . . . . . .\RRRRR',
        'RR/;. . . . . . . . . \RRR',             
        'R/;. . . . . . . . . . \RR',             
        '/;. . . . . . . . . . . \R',             
        '~` . . . . . . . . . . `~R'              
        )

class SlopedDune(Dune):
    def image(self):
        return (                            
        'RRRRRRRR,.~"""""""~.,RRRRRRRRRRRRRRRRRRRRRRRRR',
        'RRRRRR/; . . . . . . .\RRRRRRRRRRRRRRRRRRRRRRR',
        'RRRR/;. . . . . . . . . \RRRRRRRRRRRRRRRRRRRRR',             
        'RRR/;. . . . . . . . . . . \RRRRRRRRRRRRRRRRRR',             
        'RR/;. . . . . . . . . . . . ,-----____RRRRRRRR',             
        'R/;. . . . . . . . . . . ,;/;. . . . . .\RRRRR',             
        '/;. . . . . . . . . . .,/;. . . . . . . . \RRR',             
        '~` . . . . . . . . . .,;;. . . . . . . . . .`~'              
        )

class SlantedDune(Dune):
    def image(self):
        return (                            
        'RRRRRRRRRRRRRR,.~"""""""~.,RRRRRRRRRRRRRRRRRR',
        'RRRRRRRRRRR/;. . . . . . . \RRRRRRRRRRRRRRRRR',
        'RRRRRRRR/;. . . . . . . . . \RRRRRRRRRRRRRRRR',              
        'RRRRRR/; . . . . . . . . . . \RRRRRRRRRRRRRRR',              
        'RRRR/;. . . . . . . . . . . ,-----.___RRRRRRR',              
        'RR/; . . . . . . . . . . ,;/; . . . . . \RRRR',              
        '/;. . . . . . . . . . .,/;. . . . . . . .\RRR',              
        '~` . . . . . . . . . .,; . . . . . . . . . `~'               
        )


# Corals
class TreeCoral(NonMovingThing):
    def __init__(self, position, color):
        NonMovingThing.__init__(self, position, color)

        self.position = position
        self.color = color
        
        self.image = choice([
                            self._image1,
                            self._image2,
                           ])
        
    def _image1(self):
        return (                            
        '-_   \/',
        ' \/ -/-',
        '  \ /  ',                
        '   |-  ',                
        )

    def _image2(self):
        return (                            
        '_|/ |/ ',
        '  \|/  ',                
        '   |   ',                
        )

class BrainCoral(NonMovingThing):
    def image(self):
        return (
        '    ,#&.   ',
        ' *#*@*@@&*.',                
        '*@@*&*@**%&',                
        )

class Kelp(NonMovingThing):
    def image(self):
        return (
        ' V ',                
        ' | ',                
        ' |/',                
        ' | ',                
        '\| ',                
        ' | ',                
        ' |/',                
        ' | ',                
        '\|/',                
        ' |/',                
        ' | ',                
        '\| ',                
        ' | ',                
        )

class LongKelp(NonMovingThing):
    def image(self):
        return (
        ' V ',                
        ' | ',                
        '\| ',                
        ' | ',
        '\|/',
        ' | ',                    
        '\|/',                                
        ' |/',                
        '\| ',                
        ' | ',                
        ' |/',                
        ' | ',                
        '\|/',
        '\| ',                
        ' | ',                
        ' |/',                
        ' | ',                
        '\|/',
        ' | ',                
        ' | ',
        ' | ',
        ' | ',                
        ' |/',                
        ' | ',                
        '\|/',
        '\| ',
        ' |/',                
        ' | ',                
        '\| ',                
        ' | ',                
        ' |/',                
        ' | ',
        '\| ',                
        ' | ',                
        ' |/',                
        ' | ',                
        '\|/',
        ' | ',                    
        '\|/',                                
        ' |/',
        '\|/',
        ' | ',                    
        ' | ',                    
        '\|/',                                
        ' |/',                
        ' | ',                
        '\| ',                
        ' | ',                
        ' | ',                
        ' |/',                
        ' | ',                
        '\|/',
        '\| ',
        ' |/',                
        ' | ',                
        '\| ',                
        ' | ',                
        ' |/',                
        ' | ',
        '\| ',                
        ' | ',                
        ' |/',                
        ' | ',                
        '\|/',
        ' | ',                    
        '\|/',                                
        ' |/',
        '\|/',
        '\|/',                                
        ' |/',                
        ' | ',                
        '\| ',                
        ' | ',                
        ' | ',                
        ' |/',                
        ' | ',                
        '\|/',
        '\| ',
        ' |/',                
        ' | ',                
        '\| ',                
        ' | ',                
        ' |/',                
        ' | ',
        '\| ',                
        ' | ',                
        ' |/',                
        ' | ',                
        '\|/',
        ' | ',                    
        '\|/',                                
        ' |/',
        '\|/',
        ' | ',                    
        '\|/',                                
        ' |/',                
        ' | ',                
        '\| ',                
        ' | ',                
        )


# School class
class School(object):
    def __init__(self, students, LeadType, FollowType, FollowDistance):
        self.students       = students
        self.LeadType       = LeadType
        self.FollowType     = FollowType
        self.FollowDistance = FollowDistance

        self.createFollowingOrder()

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
            current_leader  = self.following_order[student]
            distance        = self.FollowDistance

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

#--------------- TYPES OF SCHOOLS (following patterns / heirarchies) -----------

# Everyone follows a single Monarch
class Monarch(School):
    """Everyone follows a single "monarch"

             o  oo 
          o o  o o o 
           o o o  o   --> o   
           o oo o o
             o  o  

    """
    def createFollowingOrder(self):
        # Start with blank list
        self.following_order = []

        for x in self.students:
            self.following_order.append(self.students[0])
        #add student1 to the beginning of the list, as "0"
        try:
            self.following_order[0] = "0"
        except:
            pass

# each leader is followed by 2 fish, in a tree branching structure
class Tree(School):
    """Each fish is followed by 2 fish, in a tree branching structure

                  o 
                 / \ 
                o   o
               /|   |\ 
              o o   o o
             /| |\  |\ \ 
            o o o o o o o

    """
    def createFollowingOrder(self):
        self.following_order = []
        self.branches = []

        self.following_order.append("0")        # First student is main leader

        n = len(self.students)
        for i in range( (n-(n%2)) // 2):        # Number of branches is ((n-(n%2)) // 2
            self.branches.append(self.students[i])
            # Add latest branch leader (twice)
            self.following_order.append(self.branches[-1])
            self.following_order.append(self.branches[-1])

# Everyone follows the previous fish in line
class Line(School):
    """Everyone follows the fish in front of them

                ,o--o,              
             ,o        o--o--o  --> 
           o                        

    """
    def createFollowingOrder(self):
        # Start with blank list
        self.following_order = []

        for x in self.students:
            self.following_order.append(x)
        #add student1 to the beginning of the list, as "0"
        try:
            self.following_order.insert(0,"0")
            self.following_order.pop()              #remove last student (has no followers)
        except:
            pass

# Same as line, but first fish follows last fish (creating a circle)
class Circle(School):
    """Same as line, but first fish follows last fish (creating a circle)

            ,o--o--o--o--o--o,     
           o                  o    
            'o--o--o--o--o--o'     

    """
    def createFollowingOrder(self):
        # Start with blank list
        self.following_order = []

        for x in self.students:
            self.following_order.append(x)
        # make first in list follow last in list
        try:
            self.following_order.insert(0, self.following_order.pop())
        except:
            pass

# Follow closest fish
class Neighbor(School):
    """Everyone follows the closest fish to them in the school

           o  ooo    oo      o
            oo     oo    oo o
        oo     oo  oo    o o 
           oo       oo       

    """
    def createFollowingOrder(self):
        self.following_order = []
    def automate(self):
        for student in self.students:
            # each fish follows nearest fish in school
            self.Follow( student, student.findNearest(self.students), self.FollowDistance )

# Same as Neighbor, but keep personal space
class ShyNeighbor(Neighbor):
    """Everyone follows the closest fish to them in the school,
    unless they're too close and then the flee

           o  o o    o       o
            o      o      o  
        o      o           o 
            o      o o       

    """
    def createFollowingOrder(self):
        self.following_order = []
    def automate(self):
        Neighbor.automate(self)
        for student in self.students:
            nearest = student.findNearest(self.students)
            if student.getDistance(nearest)[3] <= self.FollowDistance:
                #student.flee( student.findNearest(self.students), 1 )
                student.flee( nearest, self.FollowDistance - 1 )

#------------------------------ HELPER FUNCTIONS -------------------------------

# randomly create bubbles to float up
def create_bubbles():
    global bub
    #randomly create bubbles
    if bub % randint(1,bubble_frequency) == 2:
        bub_position = [HEIGHT-5, randint(1, WIDTH -3)]
        bub_color    = choice(bubble_colors)
        bub_list.append(Bubble(bub_position, bub_color))
    bub += 1

# group a school of fish around a random coral every now and then 
def group_around_coral(school, period, stay):
    global cor, coral_list
    if cor % period == 0:
        school.desire = choice(coral_list)
    if cor % period < coral_search_time :
        for student in school.students:
            if cor % period < stay:
                if randint(1,2) == 1:
                    student.randomFollow(school.desire, 4)
            else:
                student.randomFollow(school.desire, 4)

# generate a number of fish schools, each one randomized
def generate_schools(number_of_schools, factory, school_list, lower_bound, upper_bound):
    global School_Types, Follow_Types, Lead_Types, School_Colors

    if  not School_Types or \
        not Follow_Types or \
        not Lead_Types or \
        not School_Colors:
            return

    ###############################################################################################
    # SCHOOL FACTORY
    ###############################################################################################
    #                               SchoolType, SchoolSize, SchoolCenter, AnimalType, \
    #                               FollowType, FollowDistance, LeadType, Color
    i=0
    while i < number_of_schools:
        i+=1
        school_list.append( factory.CreateSchool(   SchoolType   = choice(School_Types),
                                                    SchoolSize   = randint(lower_bound, upper_bound),
                                                    SchoolCenter = choice(School_Centers),
                                                    FollowType   = choice(Follow_Types),
                                                    LeadType     = choice(Lead_Types),
                                                    Color        = choice(School_Colors)
                                                ) )

# get rid of elements generated that do not show up on screen
def remove_peripherals(*args):
    for element_list in args:
        for element in element_list:
            if element.position[1] + element.size[1] < 1 or \
            element.position[1] - element.size[1] > WIDTH-1:
                element_list.remove(element)

# drift all swimming creatures, as if by an ocean current
def ocean_drift():
    global ocean_current_count, ocean_current_value
    if ocean_current_count == 0:
        if randint(1,50) == 1:
            ocean_current_count = 2 * randint(0,10)
            if randint(1,2) == 1:
                ocean_current_count *= -1
            ocean_current_value = 0
        return
    else:
        ocean_current_drift = (ocean_current_value * ocean_current_count) // 30
        direction = abs(ocean_current_count)//ocean_current_count
        ocean_current_count -= direction
        ocean_current_value += 1

        # CURRENTS SWEEP THINGS OUTSIDE AQUARIUM (BUT THEY SWIM BACK IN)
        for fish in Eco_Swimmers + bub_list:
            fish.erase()
            try:
                fish_depth  = (fish.position[0])
                water_depth = (Aquarium.height - Water.position)
                depth_ratio = 1.0*(water_depth // fish_depth)

                current_sections = 3
                current_at_depth = 1.0*(ocean_current_drift * (depth_ratio // current_sections))

                fish.position[1] += int(current_at_depth)

            except ZeroDivisionError:
                pass

        ## KEEP EVERYONE INSIDE THE AQUARIUM (THEY HIT THE WALLS)
        #for fish in Eco_Swimmers + bub_list:
        #   fish.draw()
        #   if fish.position[1] + ocean_current_drift > 2 and \
        #      fish.position[1] + ocean_current_drift < WIDTH - 2:
        #           fish.erase()
        #           fish.position[1] += int(current_at_depth)
        #           fish.draw()

#--------------------------------- GENERATORS ----------------------------------

# Create an Abstract Factory that can create schools
class SchoolFactory(object):
    def __init__( self,
                  SchoolType=Tree,
                  SchoolSize=20,
                  SchoolCenter=[HEIGHT//2,WIDTH//2],
                  AnimalType=SeaMonkey,
                  FollowType='calmRandomFollow',
                  FollowDistance=2,
                  LeadType='randomMove',
                  Color='red' ):

        self.SchoolType     = SchoolType
        self.SchoolSize     = SchoolSize
        self.SchoolCenter   = SchoolCenter
        self.AnimalType     = AnimalType
        self.FollowType     = FollowType
        self.FollowDistance = FollowDistance
        self.LeadType       = LeadType
        self.Color          = Color

    def CreateSchool(self, **kwargs):
        self.SchoolType     = kwargs.get('SchoolType', self.SchoolType)
        self.SchoolSize     = kwargs.get('SchoolSize', self.SchoolSize)
        self.SchoolCenter   = kwargs.get('SchoolCenter', self.SchoolCenter)
        self.AnimalType     = kwargs.get('AnimalType', self.AnimalType)
        self.FollowType     = kwargs.get('FollowType', self.FollowType)
        self.FollowDistance = kwargs.get('FollowDistance', self.FollowDistance)
        self.LeadType       = kwargs.get('LeadType', self.LeadType)
        self.Color          = kwargs.get('Color', self.Color)

        # Create list of students and instantiate
        i=0
        self.students = []
        self.following_order = []

        while i < self.SchoolSize:
            # Instantiate the current student
            student = \
                self.AnimalType( [self.SchoolCenter[0]+((i%2)*((-1)**i)),
                                  self.SchoolCenter[1]+((i%3)*((-1)**i)) ],
                                  self.Color )

            # Add current student to list of students
            self.students.append(student)
            # Draw current student
            student.draw()

            # iterate
            i += 1

        # return school instance
        return self.SchoolType( self.students, self.LeadType,
                                self.FollowType, self.FollowDistance )

# Generates random objects for start
class Generator(object):
    def __init__(self):
        self.colors = creature_colors

        # Bounds 
        self.left   = 1
        self.right  = WIDTH - 1
        self.top    = Water.position + 1
        self.bottom = HEIGHT - 1

    def generate(self, type_list, pos_bounds, n_bounds, color_list, gen_list):
        for species in type_list:
            if len(n_bounds) == 2:
                n = randint(n_bounds[0], n_bounds[1])
            else:
                n = n_bounds[0]

            # generate list of creatures, if n is not 0
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
        self.colors = coral_colors
        self.left   = -7
        self.right  = WIDTH + 7
        self.bottom = HEIGHT + 1
        self.top    = Sand.position + 1

        self.dune_list  = [SmallDune, BigDune, HugeDune, SlopedDune, SlantedDune]
        self.coral_list = [TreeCoral, BrainCoral]
        self.kelp_list  = [Kelp, LongKelp]

# Good for generating fish and whales
class EcosystemGenerator(Generator):
    def __init__(self):
        Generator.__init__(self)
        self.colors = creature_colors
        self.left   = 1
        self.right  = WIDTH - 1
        self.bottom = HEIGHT - 1
        self.top    = Water.position + 1

        self.fish_list   = [SeaMonkey, Minnow, AngelFish, Tuna, Barracuda]
        self.whale_list  = [Whale, BabyWhale]
        self.bottom_list = [Snail, SeaUrchin]

#------------------------------ LAYER GENERATORS -------------------------------

def generate_background():
    global BG_List
    global BG_Dunes
    global BG_Kelp

    ############################################################################
    # generate(self, type_list, pos_bounds, n_bounds, color_list, gen_list)
    ############################################################################
    BG_Dunes = []
    SF.generate( type_list=[SmallDune,BigDune,HugeDune,SlopedDune,SlantedDune],
                 pos_bounds=[ (HEIGHT*2//3, HEIGHT-1),
                              (SF.left, SF.right) ],
                 n_bounds=[background_dunes],
                 color_list=[sand_color],
                 gen_list=BG_Dunes )

    BG_Kelp = []
    SF.generate( type_list=[Kelp],
                 pos_bounds=[ (SF.top-12, SF.bottom-10),
                              (2, WIDTH-2) ],
                 n_bounds=[background_kelp],
                 color_list=[kelp_color],
                 gen_list=BG_Kelp )

    #---------------------------------------------------------------------------
    if underwater_hill == True:
        # Create an underwater hill
        hill_position = randint(SF.left, SF.right)
        hill_spread   = randint(WIDTH*1//4, WIDTH*1//3)
        hill_left     = hill_position - hill_spread
        hill_right    = hill_position + hill_spread
        hill_y_bounds = [randint(HEIGHT*1//3,Sand.position), Sand.position]
        hill_x_bounds = [hill_left, hill_right]
        hill_number   = ((hill_y_bounds[1]-hill_y_bounds[0])*hill_spread) // 500

        SF.generate( type_list=[SmallDune,BigDune,HugeDune,SlopedDune,SlantedDune],
                     pos_bounds=[ hill_y_bounds , hill_x_bounds ],
                     n_bounds=[0*hill_number , 3*hill_number],
                     color_list=[sand_color],
                     gen_list=BG_Dunes )

        SF.generate( type_list=[Kelp],
                     pos_bounds=[ (hill_y_bounds[0]-12, hill_y_bounds[1]-12),
                                  hill_x_bounds ],
                     n_bounds=[hill_kelp],
                     color_list=[kelp_color],
                     gen_list=BG_Kelp )

        SF.generate( type_list=[TreeCoral],
                     pos_bounds=[ hill_y_bounds , hill_x_bounds ],
                     n_bounds=[hill_coral],
                     color_list=coral_colors,
                     gen_list=BG_Kelp )
    #---------------------------------------------------------------------------

    # creat a consolidated list of Background objects
    BG_List = BG_Dunes + BG_Kelp

    # sort by vertical position
    BG_List.sort(key=lambda x: x.position[0] + x.size[0], reverse=False)
    for item in BG_List:
        item.draw()

def generate_midground():
    global MG_List
    global MG_Dunes
    global MG_TreeCoral
    global MG_BrainCoral
    global MG_Kelp

    ############################################################################
    # generate(self, type_list, pos_bounds, n_bounds, color_list, gen_list)
    ############################################################################
    MG_Dunes = []
    SF.generate( type_list=[SmallDune,BigDune,HugeDune,SlopedDune,SlantedDune],
                 pos_bounds=[ (Sand.position-3, HEIGHT-1),
                              (SF.left, SF.right) ],
                 n_bounds=[midground_dunes],
                 color_list=[sand_color],
                 gen_list=MG_Dunes )

    MG_TreeCoral = []
    SF.generate( type_list=[TreeCoral],
                 pos_bounds=[ (SF.top, SF.bottom),
                              (SF.left, SF.right) ],
                 n_bounds=[midground_tree_coral],
                 color_list=coral_colors,
                 gen_list=MG_TreeCoral )

    MG_BrainCoral = []
    SF.generate( type_list=[BrainCoral],
                 pos_bounds=[ (SF.top, SF.bottom),
                              (SF.left, SF.right) ],
                 n_bounds=[midground_brain_coral],
                 color_list=coral_colors,
                 gen_list=MG_BrainCoral )

    MG_Kelp = []
    SF.generate( type_list=[Kelp],
                 pos_bounds=[ (SF.top-12, SF.bottom-10),
                              (2, WIDTH-2) ],
                 n_bounds=[midground_kelp],
                 color_list=[kelp_color],
                 gen_list=MG_Kelp )

    # creat a consolidated list of Background objects
    MG_List = MG_Dunes + MG_TreeCoral + MG_BrainCoral + MG_Kelp

    # sort by vertical position
    MG_List.sort(key=lambda x: x.position[0] + x.size[0], reverse=False)
    for item in MG_List:
        item.draw()

def generate_foreground():
    global FG_List
    global FG_Dunes
    global FG_Kelp
    
    ############################################################################
    # generate(self, type_list, pos_bounds, n_bounds, color_list, gen_list)
    ############################################################################
    FG_Kelp = []
    SF.generate( type_list=[LongKelp],
                 pos_bounds=[ (Water.position+1, HEIGHT*2//3),
                              (2, WIDTH-2) ],
                 n_bounds=[0*scale, 3*scale],
                 color_list=[kelp_color],
                 gen_list=FG_Kelp)

    FG_Dunes = []
    SF.generate( type_list=[HugeDune,SlopedDune,SlantedDune],
                 pos_bounds=[ (HEIGHT-6, HEIGHT-2),
                              (SF.left, SF.right) ],
                 n_bounds=[0*scale,2*scale],
                 color_list=[sand_color],
                 gen_list=FG_Dunes )

    # creat a consolidated list of Background objects
    FG_List = FG_Kelp + FG_Dunes 

    # sort by vertical position
    FG_List.sort(key=lambda x: x.position[0] + x.size[0], reverse=False)
    for item in FG_List:
        item.draw()

def generate_ecosystem():
    global Eco_Creatures
    global Eco_Swimmers
    global Eco_Fishies
    global Eco_Barracuda
    global Eco_Whales
    global Eco_BabyWhales
    global Eco_BabyWhaleFollower
    global Eco_BottomFeeders
    global Eco_Jellyfish

    ############################################################################
    # generate(self, type_list, pos_bounds, n_bounds, color_list, gen_list)
    ############################################################################

    #-------------------------------------------------------------------------------
    # Eco_Fishies
    Eco_Tuna = []
    Eco.generate( [Tuna], [ [Eco.top, Eco.bottom], [Eco.left, Eco.right] ],
                  [number_of_tuna], Eco.colors, Eco_Tuna)

    Eco_AngelFish = []
    Eco.generate( [AngelFish], [ [Eco.top, Eco.bottom], [Eco.left, Eco.right] ],
                  [number_of_angelfish], Eco.colors, Eco_AngelFish)

    Eco_Minnows = []
    Eco.generate( [Minnow], [ [Eco.top, Eco.bottom], [Eco.left, Eco.right] ],
                  [number_of_minnows], Eco.colors, Eco_Minnows)

    Eco_SeaMonkeys = []
    Eco.generate( [SeaMonkey], [ [Eco.top, Eco.bottom], [Eco.left, Eco.right] ],
                  [number_of_seamonkeys], Eco.colors, Eco_SeaMonkeys)

    # consolidate all fishies into one list
    Eco_Fishies = Eco_Tuna + Eco_AngelFish + Eco_Minnows + Eco_SeaMonkeys

    #-------------------------------------------------------------------------------
    # Eco_Barracuda
    Eco_Barracuda = []
    if WIDTH > 30:
        Eco.generate( [Barracuda], [ [Eco.top, Eco.bottom], [Eco.left, Eco.right] ],
                      [number_of_barracudas], Eco.colors, Eco_Barracuda)

    if clock_fish == True:
        Eco.generate( [Clock], [ [Eco.top, Eco.bottom], [Eco.left, Eco.right] ],
                      [1,1], clock_fish_colors, Eco_Barracuda)

    #-------------------------------------------------------------------------------
    # Eco_Whales
    Eco_Whales = []
    Eco_BabyWhales = []
    Eco_BabyWhaleFollower = []
    if WIDTH > 45:
        Eco.generate( [Whale], [ [Eco.top, Eco.bottom], [Eco.left, Eco.right] ],
                      [number_of_whales], whale_colors, Eco_Whales)

        Eco.generate( [BabyWhale], [ [Eco.top, Eco.bottom], [Eco.left, Eco.right] ],
                      [number_of_baby_whales], whale_colors, Eco_BabyWhales)

        # For making a baby whale follow its mother
        if len(Eco_Whales) == 2:
            if len(Eco_BabyWhales) > 0:
                # Consolidate list
                #Eco_BabyWhaleFollower.append( Eco_BabyWhales[-1] )
                Eco_BabyWhaleFollower.append( Eco_BabyWhales.pop() )
                # Make calf same color as mother
                Eco_BabyWhaleFollower[0].color = Eco_Whales[0].color
        # Add the rest of the baby whales to the Eco_Whales list
        Eco_Whales += Eco_BabyWhales

    #-------------------------------------------------------------------------------
    # Eco_Jellyfish
    Eco_Jellyfish = []
    Eco.generate(   [Jellyfish], [ [Eco.top, (Eco.bottom-Eco.top)//2], [SF.left, SF.right] ],
                    [number_of_jellyfish], jellyfish_colors, Eco_Jellyfish)


    #-------------------------------------------------------------------------------
    # Eco_BottomFeeders

    Eco_Snails = []
    Eco.generate( [Snail], [ [Sand.position+1, HEIGHT-1], [SF.left, SF.right] ],
                  [number_of_snails], snail_colors, Eco_Snails)

    Eco_SeaUrchins = []
    Eco.generate( [SeaUrchin], [ [Sand.position+1, HEIGHT-1], [SF.left, SF.right] ],
                  [number_of_sea_urchins], sea_urchin_colors, Eco_SeaUrchins)

    Eco_Lobsters = []
    Eco.generate( [Lobster], [ [Sand.position+1, HEIGHT-1], [SF.left, SF.right] ],
                  [number_of_lobsters], lobster_colors, Eco_Lobsters)

    # consolidate all bottomfeeders into one list
    Eco_BottomFeeders = Eco_Snails + Eco_SeaUrchins + Eco_Lobsters

    # initialize bottomfeeders
    for bottomfeeder in Eco_BottomFeeders:
        bottomfeeder.speed = 1
        bottomfeeder.direction[0] = 0
        bottomfeeder.direction[1] = choice([-1,1])
    #-------------------------------------------------------------------------------

    # creat a consolidated list of creature objects
    Eco_Creatures = Eco_Fishies + Eco_Barracuda + Eco_Whales + Eco_BabyWhales + \
                    Eco_BabyWhaleFollower + Eco_BottomFeeders

    # creat a consolidated list of creature objects
    Eco_Swimmers = Eco_Fishies + Eco_Barracuda + Eco_Whales + Eco_Jellyfish + \
                   Eco_BabyWhales + Eco_BabyWhaleFollower

def generate_all_schools():
    global schools
    global sea_monkey_schools
    global minnow_schools
    global Eco_Swimmers
    global School_Types
    global School_Colors
    global Follow_Types
    global Lead_Types
    global School_Centers
    global number_of_sea_monkey_schools
    global number_of_minnow_schools
    global max_fish

    sea_monkey_schools = []
    minnow_schools = []

    #School_Types = [Monarch, Tree, Line, Circle, Neighbor, ShyNeighbor]
    School_Types  = []
    for school_type in school_types:
        try:
            School_Types.append(eval(school_type))
        except:
            pass

    if len(School_Types) == 0:
        return

    School_Colors  = fish_school_colors
    Follow_Types   = ['calmRandomFollow', 'randomFollow']
    Lead_Types     = ['calmRandomMove', 'randomMove']
    School_Centers = [ [HEIGHT*1//3,WIDTH*1//7],
                       [HEIGHT*1//3,WIDTH*5//7],
                       [HEIGHT*1//2,WIDTH*1//7],
                       [HEIGHT*1//2,WIDTH*5//7],
                       [HEIGHT*2//3,WIDTH*1//7],
                       [HEIGHT*2//3,WIDTH*5//7] ]

    # --- SEA MONKEYS! ---#
    #number_of_sea_monkey_schools = 3
    #number_of_sea_monkey_schools = randint(2,8)
    try:
        fps_avg = ( max_fish // number_of_sea_monkey_schools ) 
    except ZeroDivisionError:
        fps_avg = 0
    fps_min = (fps_avg // 4)+1
    fps_max = (fps_avg *  2)+1

    sea_monkey_schools = []
    SeaMonkeyFactory = SchoolFactory(AnimalType=SeaMonkey)
    generate_schools( number_of_sea_monkey_schools, 
                      SeaMonkeyFactory,
                      sea_monkey_schools,
                      fps_min,fps_max )


    # --- MINNOWS! --- #
    #number_of_minnow_schools = 1
    #number_of_minnow_schools = randint(1,number_of_sea_monkey_schools/2)
    fps_avg = (max_fish // 20)
    fps_min = (fps_avg // 2)+1
    fps_max = int(fps_avg * 1.5)+1

    minnow_schools = []
    MinnowFactory = SchoolFactory(AnimalType=Minnow, LeadType='calmRandomMove')
    generate_schools( number_of_minnow_schools,
                      MinnowFactory,
                      minnow_schools,
                      fps_min,fps_max )

    schools = sea_monkey_schools + minnow_schools

    for school in schools:
        for student in school.students:
            Eco_Swimmers.append(student)

#--------------------------- AUTOMATION DURING LOOP ----------------------------

# periodically follow something
def periodic_grouping():
    global cor

    # Alternate between grouping around different corals
    for school in schools:
        period = schools.index(school) * 100 + 500
        stay = schools.index(school) * 10 + 50
        group_around_coral(school, period, stay)

    # Sometimes the Barracuda hunts nearest fish
    for barracuda in Eco_Barracuda:
        period = Eco_Barracuda.index(barracuda) * 200 + 500
        stay = Eco_Barracuda.index(barracuda) * 20 + 50
        if cor % period < stay:
            barracuda.follow(barracuda.findNearest(Eco_Fishies), 2)

    # increment cor counter
    if cor >= 10000:
        cor = 0
    cor += 1

# automate fish and whale moving
def automate_swimmers():
    # automate moving and fleeing
    for fish in Eco_Fishies:
        fish.randomMove()
        for barracuda in Eco_Barracuda:
            fish.flee(barracuda, 3)
        for whale in Eco_Whales:
            fish.flee(whale, 6)

    for barracuda in Eco_Barracuda:
        barracuda.calmRandomMove()
        barracuda.flee(barracuda.findNearest(Eco_Whales), 4)

    for whale in Eco_Whales:
        whale.calmRandomMove()      # This includes the baby whale follower (adds spunk)

    for jellyfish in Eco_Jellyfish:
        jellyfish.calmRandomMove(y_rand=20, stop_rand=0, resume_rand=8, turn_rand=0)

    # If there's a baby whale following a mother whale, follow it
    if len(Eco_BabyWhaleFollower) == 1:
        Eco_BabyWhaleFollower[0].randomFollow(Eco_Whales[0], 7)

    # Schools
    if explorer_school == True:
        for school in schools[1:]:
            school.automate()
    else:
        for school in schools:
            school.automate()

# automate snail and lobster movement (sparse)
def automate_bottomfeeders():
    for bottom_feeder in Eco_BottomFeeders:
        if randint(1,50) == 1:
            bottom_feeder.randomMove()
        else:
            bottom_feeder.draw()

# schools follow and flee other things
def school_special_behaviors():
    # All fish flee from whales
    for school in schools:
        enemy_list = Eco_Whales + Eco_Barracuda
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

    # EXPLORER SCHOOL
    if explorer_school == True:
        school = sea_monkey_schools[0]
        period = 1133
        explore = 777
        if (cor % period) < explore:
            for student in school.students:
                choice([student.randomMove(), student.calmRandomMove()])
        else:
            school.automate()

# create bubbles and drift them up
def automate_bubbles():
    if bubbles == True:
        # randomly create bubbles to float up
        create_bubbles()
        # Drift all bubbles (in foreground)
        for bubble in bub_list:
            bubble.drift()
            if bubble.position[0] <= ( Water.position - 5):
                bub_list.remove(bubble)

# remove creatures if there are too many and program is too slow
def reduce_ecosystem(count):
    # Target ratio for seamonkeys / minnows
    ratio = 5

    #---------------------------------------------------------------------------
    # if there are no fish to remove, don't attempt to
    if len(schools) == 0 or len(Eco_Swimmers) == 0:
        return
    # if count is 0, make it 1
    count = 1 if count == 0 else count

    #---------------------------------------------------------------------------
    # remove [count] fish from the aquarium
    for _ in range(int(count)):
        # get ratio of seamonkeys to minonows
        total_sea_monkeys = 0
        for school in sea_monkey_schools:
            total_sea_monkeys += len(school.students)
        total_minnows = 0
        for school in minnow_schools:
            total_minnows += len(school.students)

        try:
            sm_m_ratio = (total_sea_monkeys // total_minnows)
        except ZeroDivisionError:
            sm_m_ratio = ratio + 1

        #-----------------------------------------------------------------------
        # choose a school at random
        unlucky_class = []
        class_selection_count = 0
        while len(unlucky_class) < 1 and class_selection_count < 10:
            class_selection_count += 1

            #----------------------------------------------
            # extra seamonkeys
            if sm_m_ratio > ratio:
                unlucky_school = choice(sea_monkey_schools)
            # extra minnows
            elif sm_m_ratio < ratio:
                unlucky_school = choice(minnow_schools)
            # right at the ratio
            else:
                unlucky_school = choice(schools)
            #----------------------------------------------

            unlucky_class  = unlucky_school.students

        #-----------------------------------------------------------------------
        # choose last fish in students list.  Erase it.  Remove from lists.
        if len(unlucky_class) > min_fish_per_school:
            unlucky_fish = unlucky_class.pop()
            unlucky_fish.erase()
            Eco_Swimmers.remove(unlucky_fish)

            # recreate following order, after fish has been removed
            unlucky_school.createFollowingOrder()

        #-----------------------------------------------------------------------
        # (if school is empty, remove it from the list of schools)
        if len(unlucky_class) == 0:
            try:
                schools.remove(unlucky_school)
            except:
                pass


################################################################################
##################################### MAIN #####################################

#-------------------------------- PREPARATION ----------------------------------
# Set a blank faraway object (for initial object when using FindNearest)
FarawayObject = type('test', (object,), {})()
FarawayObject.position = [-1000, -1000]
FarawayObject.size = [0,0]

# check Python version (for defining how to lookup unicode characters)
if sys.version_info[0] < 3:
    degree_symbol = unichr(176)    # For drawing bubbles
else:
    degree_symbol = chr(176)       # For drawing bubbles

# Prepare the dictionary for word bubbles (if set)
if word_bubbles == True:
    try:
        word_list = open(word_file).read().splitlines()
    except:
        word_bubbles = False

# Look for argument for verbosity
if len(sys.argv) > 1 and  sys.argv[1] in ['-v', '--verbose']:
    verbose = True


#------------------------------ CREATE AQUARIUM --------------------------------
# instantiate Aquarium Window
Aquarium = Window(choice(window_colors))


#----------------------------- CREATE BACKGROUND -------------------------------
# define water
water_color = choice(water_colors)
if draw_water == True:
    water_surface = water_position
else:
    water_surface = 0
Water = Surface(water_surface, water_color)
if draw_water == True:
    Water.draw()
    Water.drawAbove()

# define sand
sand_color = choice(sand_colors)
Sand = Surface(sand_position, sand_color)
if draw_sand == True:
    Sand.drawUnder()

# define kelp color as different from sand color
kelp_color = sand_color
while kelp_color == sand_color:
    kelp_color = choice(kelp_colors)

# The order in which things are drawn goes from background -> midground -> foreground
SF = SeafloorGenerator()
Eco = EcosystemGenerator()

# generate layers
generate_background()
generate_midground()
generate_foreground()

# Remove all coral that are off-screen (so fish don't try to follow an invisible coral)
remove_peripherals(BG_List, MG_List, FG_List)

#set eveything so far as the background environment
Aquarium.background = deepcopy(Aquarium.stage)


#------------------------------ CREATE ECOSYSTEM -------------------------------
generate_ecosystem()
generate_all_schools()

# initial bubble list
bub = 1
bub_list = []
# variable for changing which coral the school is going around
cor = 0
# variable for making sure fish reduction doesn't happen forever
reduce_clock = 0
# variables for modulating ocean current
ocean_current_value = 0
ocean_current_count = 0
# list of corals to choose from (when following)
coral_list = BG_Kelp + MG_Kelp + FG_Kelp + MG_BrainCoral + MG_TreeCoral

# Hide the cursor
os.system('echo -ne "\x1b[?25l"')


################################################################################
##################################### LOOP #####################################
while True:
    # ocean currents move all the swimmers
    if periodic_ocean_current_drift == True:
        ocean_drift()

    # Get times for waiting between frames
    t_a = time()
    t_b = time()


    #============================= MIDGROUND ===================================
    # draw midground layer
    SF.DrawList(MG_List)

    #------------------ ocean floor ------------------------
    # Move all (independent) creatures
    automate_bottomfeeders()

    # Draw coral and kelp in midground (to cover up BottomFeeders)
    SF.DrawList(MG_TreeCoral)
    SF.DrawList(MG_Kelp)

    #-------------------- swimmers -------------------------
    # automate moving of fish and whales, etc.
    automate_swimmers()

    # fish sometimes group around coral
    # barracuda sometimes hunts fish
    periodic_grouping()

    # schools follow and flee other things
    school_special_behaviors()

    # ----------- RE-DRAW ALL SWIMMERS -----------#
    # (some images may have been erased in "move()")
    for creature in Eco_Swimmers:
        creature.draw()


    #========================= ACTIVE FOREGROUND ===============================
    automate_bubbles()

    # Draw long kelp in the front
    SF.DrawList(FG_Kelp[:scale])
    SF.DrawList(FG_Dunes)
    SF.DrawList(FG_Kelp[scale:])


    #========================== DISPLAY AQUARIUM ===============================
    # Wait to display aquarium
    while (t_b - t_a) < DELAY:
        t_b = time()
    Aquarium.display()


    #---------------------- debug printout -------------------------
    if verbose:
        debug_printout()


    #========================== REDUCE ECOSYSTEM ===============================
    if reduce_clock < 20:
        #-----------------------------------------------------------------------
        # if it's taking too much time before each refesh, remove some of the fish
        if (t_b - t_a) > DELAY*1.25:
            reduce_ecosystem(max_fish//10)
            reduce_clock -= 1
        elif (t_b - t_a) > DELAY*1.125:
            reduce_ecosystem(max_fish//20)
            reduce_clock -= 1
        elif (t_b - t_a) > DELAY*1.1:
            reduce_ecosystem(1)
            reduce_clock -= 1
        #-----------------------------------------------------------------------
        else:
            reduce_clock += 1

    #---------------------------------------------------------------------------
    #elif (t_b - t_a) > DELAY*1.4:
    #    reduce_clock = 0
