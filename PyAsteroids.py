"""
Asteroids by Fer, 2019
Simple implementation in PyGame of the classic arcade game Asteroids

Game Commands:
<ESC>   Exit Game
<P>     Pause Game
<R>     Restart Game
<S>     Toggle Sound On/Off

<+>     Increase Game Speed
<->     Decrease Game Speed

<SPACE> Fire
<LEFT>  Turn spaceship counter clockwise
<RIGHT> Turn spaceship clockwise
<UP>    Accelerate spaceship
<DOWN>  Decelerate spaceship

Image of spaceship thanks to Ahkâm (https://www.freeiconspng.com/img/17270)
Image of asteroids thanks to someone who draw them...
Sounds with courtesy of freesound.org

Disclaimer: This code has been hand crafted by myself, Stackoverflow has been consulted as little as possible,
 and the only original example of Asteroids I have played recently has been on an old Macintosh Plus from 1986

Future improvements to code:
- use of sprites (efficiency, readability)
-

"""

import pygame, sys, time
from pygame.locals import *
import random
import math

WINDOWWIDTH = 800
WINDOWHEIGHT = 600

BLACK = (0, 0, 0)
WHITE = (255,255,255)
RED = (255,0,0)
YELLOW = (220, 220, 10)
BLUE = (0, 0, 255)
GREEN = (10, 250, 10)

# okay to put media here?
# load spaceship images
ship = pygame.image.load ("media/spaceship0.png")
ship_boost = pygame.image.load ("media/spaceship1.png")
ship_hit = pygame.image.load ("media/spaceship_hit.png")

# load asteroid images
img_a0 = pygame.image.load ("media/a0.png")
img_a1 = pygame.image.load ("media/a1.png")
img_a2 = pygame.image.load ("media/a2.png")


# main Game class
class AsteroidsGame():

    def __init__ (self, asteroid_count=10, lifes=3, sound_on=True):

        self.asteroids_count = asteroid_count

        # lists for holding objects that will be drawn to screen
        self.asteroids = []
        self.background_stars = []
        self.lasers_fired = []

        self.initial_lifes = lifes # number of lifes we start with
        self.lifes = self.initial_lifes # current in-game lifes
        self.score = 0

        self.game_over = False
        self.game_run = True
        self.game_not_started = True
        self.boost = False # indicates if we are accelerating
        self.screen_shake = False #used to shake the screen

        self.fps = 25 # default animation speed
        self.low_fps = False


        self.sound_on = sound_on
        pygame.mixer.pre_init (44100, -16, 1, 512)
        self.music_on = sound_on

        # Set up pygame
        pygame.init ()
        self.clock = pygame.time.Clock ()

        # Set up the window
        self.screen = pygame.display.set_mode ((WINDOWWIDTH, WINDOWHEIGHT), 0, 32)
        pygame.display.set_caption ("Asteroids")

        # change mouse pointer
        #pygame.mouse.set_cursor (*pygame.cursors.diamond)
        pygame.mouse.set_visible (False)

        #pre-load sounds
        self.laser_sound = pygame.mixer.Sound ("media/laser.wav")
        self.rocket_sound = pygame.mixer.Sound ("media/rocket.wav")
        self.explosion_sound = pygame.mixer.Sound ("media/explosion.wav")
        self.crack_sound = pygame.mixer.Sound ("media/crack.wav")

        if self.sound_on: #play background sound
            pygame.mixer.music.load ('media/base.wav')
            pygame.mixer.music.play (-1)

        # initiate game objects
        self.init_objects()

        # run animation
        self.run_game()


    def run_game(self):

        if self.game_not_started:
            self.game_start_up()

        while not self.game_over:

            # HANDLE EVENTS
            for event in pygame.event.get ():
                #print(event)
                if event.type == QUIT:
                    pygame.quit ()
                    sys.exit ()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit ()
                        sys.exit ()

                    # Reset Game
                    if event.key == pygame.K_r:
                        self.game_run = True
                        self.restart_game()

                    # toggle settings
                    if event.key == pygame.K_s:
                        self.toggle_sound ()
                    if event.key == pygame.K_m:
                        self.toggle_music ()

                    # spaceship control
                    if event.key == pygame.K_LEFT:
                        self.myShip.turn_left()
                    if event.key == pygame.K_RIGHT:
                        self.myShip.turn_right ()
                    if event.key == pygame.K_UP:
                        self.myShip.accelerate()
                        if self.sound_on and not self.myShip.has_been_hit:
                            pygame.mixer.Sound.play (self.rocket_sound)

                    # fire laser
                    if event.key == pygame.K_SPACE:
                        self.fire_laser ()

                    if event.key == pygame.K_p: # pause animation
                        if not self.game_run:
                            self.game_run = True
                        else:
                            self.game_run = False
                    if event.key == pygame.K_KP_PLUS: # increase anim speed
                        if self.fps < 40:
                            self.fps += 1
                    if event.key == pygame.K_KP_MINUS: # decrease anim speed
                        self.fps -= 1


                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP:
                       self.myShip.stop_accel ()
                    if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                       self.myShip.stop_rotation ()

            # RUN / PAUSE GAME
            if self.game_run:
                # Draw background
                self.screen.fill (BLACK)

                #collision detection
                self.ship_asteroid_collision()
                self.laser_asteroid_collision()

                # Draw objects
                self.draw_objects()

                #draw Infos
                self.draw_infos()

                # draw red frame and shake screen when ship has been hit
                if self.myShip.has_been_hit:
                    pygame.draw.lines (self.screen, RED, True,
                                       [(0, 0), (WINDOWWIDTH, 0), (WINDOWWIDTH, WINDOWHEIGHT), (0, WINDOWHEIGHT)], 5)
                    self.shake_screen()

                # Draw the window onto the screen.
                pygame.display.update ()

                # move objects
                self.update_all_objects ()

                # detect low fps
                if self.fps - self.clock.get_fps() > 2:
                    self.low_fps = True
                else:
                    self.low_fps = False

                self.clock.tick (self.fps)

            if self.lifes < 1:
                self.game_run = False
                # game over screen
                self.game_over_screen()

            if len(self.asteroids) < 1:
                self.game_run = False
                self.game_win_screen()

    def shake_screen(self):
        if self.screen_shake:
            delta = 5
            self.screen_shake = False
        else:
            delta = -5
            self.screen_shake = True

        for asteroid in self.asteroids:
            asteroid.x_pos += delta
        for star in self.background_stars:
            star.x_pos += delta
        self.myShip.x_pos+= delta


    def init_objects(self):
        self.myShip = SpaceShip()

        for i in range(100):
            star = Asteroid(color=WHITE, size=1, x_speed=0, y_speed=0)
            self.background_stars.append(star)

        for i in range(self.asteroids_count):
            asteroid = Asteroid()
            self.asteroids.append(asteroid)


    # Helper method  to turn a rectangle around its center
    def rotate_image_center (self, image, rect, angle):
        # Rotate the original image without modifying it.
        new_image = pygame.transform.rotate (image, angle)
        # Get a new rect with the center of the old rect.
        rect = new_image.get_rect (center=rect.center)
        return new_image, rect

    def draw_objects(self):
        # draw background stars
        for star in self.background_stars:
            pygame.draw.ellipse (self.screen, star.color,
                                 [star.x_pos, star.y_pos, star.size, star.size])

        # draw laser shots
        for laser in self.lasers_fired:
            if laser.life > 0:
                pygame.draw.line (self.screen, BLUE, (laser.x_pos, laser.y_pos), (laser.x_end_pos, laser.y_end_pos))
            else:
                self.lasers_fired.remove (laser)
            laser.life -= 1

        # draw spaceship
        if self.myShip.has_been_hit:
            pygame.draw.circle (self.screen, (10,10,10), [int(self.myShip.x_pos), int(self.myShip.y_pos)], int(self.myShip.size*7/4), 1)
        #pygame.draw.rect (self.screen, WHITE, [self.myShip.x_pos-self.myShip.size/2, self.myShip.y_pos-self.myShip.size/2, self.myShip.size, self.myShip.size])
        rect = self.myShip.ship_image.get_rect (center=(self.myShip.x_pos, self.myShip.y_pos))
        surf, rect = self.rotate_image_center (self.myShip.ship_image, rect, self.myShip.angle)
        self.screen.blit (surf, rect)

        # draw asteroids
        for asteroid in self.asteroids:
            #pygame.draw.ellipse (self.screen, asteroid.color, [asteroid.x_pos, asteroid.y_pos, asteroid.size, asteroid.size])
            #pygame.draw.rect (self.screen, asteroid.color,[asteroid.x_pos-asteroid.size/2, asteroid.y_pos-asteroid.size/2, asteroid.size, asteroid.size])

            #pygame.draw.circle (self.screen, asteroid.color, [int(asteroid.x_pos), int(asteroid.y_pos)], int(asteroid.size), 1)
            rect_ast = asteroid.image.get_rect (center=(asteroid.x_pos, asteroid.y_pos))
            surf_ast, rect_ast = self.rotate_image_center (asteroid.image, rect_ast, asteroid.angle)
            self.screen.blit (surf_ast, rect_ast)


    def draw_infos(self):
        font = pygame.font.SysFont ("Serif", 18)

        text = "Score: " + str(self.score)
        renderText = font.render (text, True, WHITE)
        self.screen.blit (renderText, (30, WINDOWHEIGHT - 50))

        text = "Lifes: " + str(self.lifes)
        if self.myShip.has_been_hit:
            text_color=RED
        else:
            text_color=WHITE
        renderText = font.render (text, True, text_color)
        self.screen.blit (renderText, (30, WINDOWHEIGHT - 30))

        text = "fps: " + str(int (self.clock.get_fps ())) + " (" + str(self.fps) + ")"
        if self.low_fps:
            text_color = RED
        else:
            text_color = WHITE
        renderText = font.render (text, True, text_color)
        self.screen.blit (renderText, (WINDOWWIDTH-100, WINDOWHEIGHT-70))

        if self.sound_on:
            state = "On"
        else:
            state = "Off"
        text = "Sound: " + state
        renderText = font.render (text, True, WHITE)
        self.screen.blit (renderText, (WINDOWWIDTH - 100, WINDOWHEIGHT - 50))

        if self.music_on:
            state = "On"
        else:
            state = "Off"
        text = "Music: " + state
        renderText = font.render (text, True, WHITE)
        self.screen.blit (renderText, (WINDOWWIDTH - 100, WINDOWHEIGHT - 30))


    def update_all_objects(self):
        for asteroid in self.asteroids:
            asteroid.update()
        for star in self.background_stars:
            star.update(self.myShip.x_speed/10, self.myShip.y_speed/10)
        for laser in self.lasers_fired:
            laser.update_laser()
        self.myShip.update()


    def fire_laser(self):
        laser = Laser(self.myShip.x_pos, self.myShip.y_pos, self.myShip.angle, self.myShip.x_speed, self.myShip.y_speed)
        self.lasers_fired.append(laser)
        if self.sound_on:
            pygame.mixer.Sound.play (self.laser_sound)
            #pygame.mixer.music.stop ()


    def ship_asteroid_collision(self):
        for asteroid in self.asteroids:
            if abs(self.myShip.x_pos - asteroid.x_pos) < asteroid.size/2 + self.myShip.size/2 and abs(self.myShip.y_pos - asteroid.y_pos) < asteroid.size/2 + self.myShip.size/2:
                if not self.myShip.has_been_hit: # only count new hits after timeout (has_been_hitz flasg is reset in Asteroids.update method)
                    self.lifes -= 1

                    if self.sound_on:
                        pygame.mixer.Sound.play (self.explosion_sound)

                    # change speed and dir of parent asteroid
                    asteroid.x_speed = asteroid.x_speed + self.myShip.x_speed
                    asteroid.y_speed = asteroid.y_speed + self.myShip.y_speed

                    asteroid.change_image ()

                self.myShip.has_been_hit = True
                self.myShip.hit_time = time.time ()

                if asteroid.size > 8:
                    asteroid.size /= 2
                    # change size,
                    # create new child asteroid and
                    new_asteroid = Asteroid (size=asteroid.size, x_pos=asteroid.x_pos, y_pos=asteroid.y_pos)
                    self.asteroids.append (new_asteroid)

                    # change asteroids image according to size
                    asteroid.change_image ()


    def laser_asteroid_collision(self):
        for laser in self.lasers_fired:
            for asteroid in self.asteroids:
                if abs (laser.x_end_pos - asteroid.x_pos) < asteroid.size and abs (laser.y_end_pos - asteroid.y_pos) < asteroid.size:
                    self.score += 1000
                    pygame.mixer.Sound.play (self.crack_sound)
                    if asteroid.size < 16:
                        self.asteroids.remove(asteroid)
                    else:
                        # change size, speed and dir of parent asteroid
                        asteroid.size /= 2
                        asteroid.x_speed = asteroid.x_speed + (laser.x_end_pos - laser.x_pos) / 10
                        asteroid.y_speed = asteroid.y_speed - (laser.y_end_pos - laser.y_pos) / 10

                        # change image
                        asteroid.change_image ()

                        # create new child asteroid and
                        new_asteroid = Asteroid(size=asteroid.size, x_pos=asteroid.x_pos, y_pos=asteroid.y_pos)
                        self.asteroids.append(new_asteroid)

                    self.lasers_fired.remove (laser)
                    break

    def game_start_up(self):
        self.screen.fill (BLACK)
        for star in self.background_stars:
            pygame.draw.ellipse (self.screen, star.color,
                                 [star.x_pos, star.y_pos, star.size, star.size])

        font = pygame.font.SysFont ("Serif", 36)
        text = "ASTEROIDS v1.0"
        renderText = font.render (text, True, WHITE)
        self.screen.blit (renderText, (WINDOWWIDTH / 2 - 75, WINDOWHEIGHT / 2 - 50))

        font = pygame.font.SysFont ("Serif", 18)
        text = "Press any key to start"
        renderText = font.render (text, True, WHITE)
        self.screen.blit (renderText, (WINDOWWIDTH / 2 - 75, WINDOWHEIGHT / 2))

        pygame.draw.lines (self.screen, WHITE, True,
                           [(0, 0), (WINDOWWIDTH, 0), (WINDOWWIDTH, WINDOWHEIGHT), (0, WINDOWHEIGHT)], 5)

        pygame.display.update ()
        while (self.game_not_started):
            for event in pygame.event.get ():
                if event.type == pygame.KEYDOWN:
                    self.game_not_started=False


    def game_win_screen(self):
        self.screen.fill (BLACK)
        for star in self.background_stars:
            pygame.draw.ellipse (self.screen, star.color,
                                 [star.x_pos, star.y_pos, star.size, star.size])

        font = pygame.font.SysFont ("Serif", 36)
        text = "YOU WIN"
        renderText = font.render (text, True, WHITE)
        self.screen.blit (renderText, (WINDOWWIDTH / 2 - 75, WINDOWHEIGHT / 2 - 50))

        font = pygame.font.SysFont ("Serif", 18)
        text = "Score: " + str (self.score)
        renderText = font.render (text, True, WHITE)
        self.screen.blit (renderText, (WINDOWWIDTH / 2 - 75, WINDOWHEIGHT / 2))

        font = pygame.font.SysFont ("Serif", 18)
        text = "Play again? Press <R>."
        renderText = font.render (text, True, WHITE)
        self.screen.blit (renderText, (WINDOWWIDTH / 2 - 75, WINDOWHEIGHT / 2 + 50))

        pygame.draw.lines (self.screen, GREEN, True,
                           [(0, 0), (WINDOWWIDTH, 0), (WINDOWWIDTH, WINDOWHEIGHT), (0, WINDOWHEIGHT)], 5)

        pygame.display.update ()


    def restart_game(self):
        self.score = 0
        self.lifes = self.initial_lifes
        self.asteroids = []
        self.background_stars = []
        self.lasers_fired = []

        self.init_objects()


    def game_over_screen(self):
        self.screen.fill (BLACK)
        for star in self.background_stars:
            pygame.draw.ellipse (self.screen, star.color,
                                 [star.x_pos, star.y_pos, star.size, star.size])

        font = pygame.font.SysFont ("Serif", 36)
        text = "GAME OVER"
        renderText = font.render (text, True, WHITE)
        self.screen.blit (renderText, (WINDOWWIDTH / 2 - 75, WINDOWHEIGHT / 2 - 50))

        font = pygame.font.SysFont ("Serif", 18)
        text = "Score: " + str (self.score)
        renderText = font.render (text, True, WHITE)
        self.screen.blit (renderText, (WINDOWWIDTH / 2 - 75, WINDOWHEIGHT / 2))

        font = pygame.font.SysFont ("Serif", 18)
        text = "Play again? Press <R>."
        renderText = font.render (text, True, WHITE)
        self.screen.blit (renderText, (WINDOWWIDTH / 2 - 75, WINDOWHEIGHT / 2 + 50))

        pygame.draw.lines (self.screen, RED, True,
                           [(0, 0), (WINDOWWIDTH, 0), (WINDOWWIDTH, WINDOWHEIGHT), (0, WINDOWHEIGHT)], 5)

        pygame.display.update ()


    def toggle_sound(self):
        if self.sound_on==False:
            self.sound_on=True
        else:
            self.sound_on=False

    def toggle_music(self):
        if self.music_on==False:
            self.music_on=True
            pygame.mixer.music.load ('media/base.wav')
            pygame.mixer.music.play (-1)
        else:
            self.music_on=False
            pygame.mixer.music.stop()

class Asteroid():
    def __init__(self, x_pos=None, y_pos=None, size=None, color=None, x_speed=None, y_speed=None):
        if x_pos==None:
            self.x_pos = random.randint (0, WINDOWWIDTH)
        else:
            self.x_pos = x_pos
        if y_pos == None:
            if color==WHITE: # this is a background star (therefore place it anywhere)
                self.y_pos = random.randint (0, WINDOWHEIGHT)
            else: #this is an asteroid (avoid placing on top of ship)
                self.y_pos = random.choice([random.randint (0, WINDOWHEIGHT/2-100), random.randint (WINDOWHEIGHT/2+100, WINDOWHEIGHT)])
        else:
            self.y_pos = y_pos
        if size == None:
            #self.size = random.randint(4, 8)  # 1-5
            self.size = random.choice ([8, 16, 32])
            #self.size = 32
        else:
            self.size = size
        if color == None:
        # self.color = random.choice (colorPals[random.choice (list (colorPals.keys ()))])
            self.color = RED
        else:
            self.color = color
        if x_speed==None:
            #self.x_speed = 0
            self.x_speed = random.randint (-3, 3)
        else:
            self.x_speed = x_speed
        if y_speed==None:
            #self.y_speed = 0
            self.y_speed = random.randint (-3, 3)
        else:
            self.y_speed = y_speed

        #load asteroid images
        self.image = None
        self.change_image()

        self.angle = 0
        self.angle_speed = random.randint(1, 5)

    def change_image (self):
        if self.size == 32:
            self.image = img_a2
        elif self.size == 16:
            self.image = img_a1
        else:
            self.image = img_a0

    def update(self, ship_x_speed=None, ship_y_speed=None):
        if not ship_x_speed == None: #speeds are modified given a collision
            self.x_speed = -ship_x_speed
            self.y_speed = -ship_y_speed

        self.x_pos += self.x_speed
        self.y_pos -= self.y_speed

        # leaving screen left
        if self.x_pos < -self.size:
            self.x_pos = WINDOWWIDTH
        # leaving screen right
        if self.x_pos > WINDOWWIDTH:
            self.x_pos = 0
        # leaving screen top
        if self.y_pos < -self.size :
            self.y_pos = WINDOWHEIGHT
        # leaving screen bottom
        if self.y_pos > WINDOWHEIGHT:
            self.y_pos = 0

        #update rotation angel
        self.angle += self.angle_speed


class SpaceShip():
    def __init__(self):
        self.x_pos = WINDOWWIDTH / 2
        self.y_pos = WINDOWHEIGHT / 2
        self.x_speed = 0
        self.y_speed = 0

        self.angle = 0
        self.boost = False
        self.is_turning_left = False
        self.is_turning_right = False

        self.ship_image = ship

        self.has_been_hit = False
        self.hit_time = time.time()

        self.laser_shots = []

        # get the ships image size (mean between x and y --> like a radius)
        self.size = (self.ship_image.get_rect().size[0]+self.ship_image.get_rect().size[0]) / 4

    def accelerate(self):
        self.boost = True

    def turn_right(self):
        self.is_turning_right = True

    def turn_left(self):
        self.is_turning_left = True

    def stop_accel(self):
        self.boost = False

    def stop_rotation(self):
        self.is_turning_left = False
        self.is_turning_right = False

    def update(self):
        # reset hit timer (ship can be hit again by asteroids)
        if self.hit_time + 1 < time.time():
            self.has_been_hit = False

        # update ship image
        if self.boost:
            self.ship_image = ship_boost
        else:
            self.ship_image = ship
        if self.has_been_hit:
            self.ship_image = ship_hit
            self.boost = False

        #  position
        self.x_pos += self.x_speed
        self.y_pos -= self.y_speed

        # leaving screen left
        if self.x_pos < -10:
            self.x_pos = WINDOWWIDTH
        # leaving screen right
        if self.x_pos > WINDOWWIDTH:
            self.x_pos = 0
        # leaving screen top
        if self.y_pos < -10:
            self.y_pos = WINDOWHEIGHT
        # leaving screen bottom
        if self.y_pos > WINDOWHEIGHT:
            self.y_pos = 0

        # update angle
        if self.is_turning_left:
            self.angle += 6
        elif self.is_turning_right:
            self.angle -= 6

        # update acceleration
        if self.boost:
            rad_angle = (self.angle / 180) * math.pi
            x_incr = -math.sin(rad_angle)
            y_incr = math.cos(rad_angle)
            self.x_speed += x_incr
            self.y_speed += y_incr
        else:
            if self.x_speed > 0:
                self.x_speed -= 0.05
            else:
                self.x_speed += 0.05
            if self.y_speed > 0:
                self.y_speed -= 0.05
            else:
                self.y_speed += 0.05


class Laser():
    def __init__(self, x_pos, y_pos, angle, ship_x_speed, ship_y_speed):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.angle = angle
        self.color = BLUE
        self.life = 100 #number of frames the laser will be visible
        self.laser_speed = 15

        self.ship_x_speed = ship_x_speed
        self.ship_y_speed = ship_y_speed

        rad_angle = (self.angle / 180) * math.pi
        x_incr = -math.sin (rad_angle)
        y_incr = math.cos (rad_angle)
        self.x_end_pos = x_pos + x_incr * 10
        self.y_end_pos = y_pos - y_incr * 10

    def update_laser(self):
        self.life -= 1

        rad_angle = (self.angle / 180) * math.pi
        x_incr = -math.sin (rad_angle) + self.ship_x_speed/10
        y_incr = math.cos (rad_angle) + self.ship_y_speed/10
        self.x_pos = self.x_pos + x_incr * self.laser_speed
        self.y_pos = self.y_pos - y_incr * self.laser_speed
        self.x_end_pos = self.x_end_pos + x_incr * self.laser_speed
        self.y_end_pos = self.y_end_pos - y_incr * self.laser_speed


if __name__ == "__main__":
    myfire = AsteroidsGame (asteroid_count=20, lifes=3, sound_on=True)
