import pygame
import math
from ctypes import POINTER, WINFUNCTYPE, windll
from ctypes.wintypes import BOOL, HWND, RECT
from random import randint

#initial screen size [ px ]
screen_width = 800
screen_height = 600

#settings
jedi_force = 75 #level of force applied when using the arrow keys
gravity = (0, 9.82/200) #gravity vector
air_resistance = 0.15 # constant multiplier for air resistance
bounce_resistance = 0.25 # how much force is lost when bouncing off a wall
stop_velocity = 75 # velocity at which the ball stops
wall_margin = 10 # margin for the walls to prevent the balls from getting stuck
start_velocity = 500 # initial velocity of the balls

debug = False # show debug things, toggled using 'c'
dark_mode = False # dark mode, toggled using 'm'

# window creation
pygame.init()
screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption("erik's physics engine")
icon = pygame.image.load('icon.png')
pygame.display.set_icon(icon)

# window position, uses win32api to get the window position based on the window handle
hwnd = pygame.display.get_wm_info()["window"] # get the window handle
prototype = WINFUNCTYPE(BOOL, HWND, POINTER(RECT)) # define the function prototype
paramflags = (1, "hwnd"), (2, "lprect") # parameter flags, hwnd is the window handle, lprect is a pointer to a RECT structure
GetWindowRect = prototype(("GetWindowRect", windll.user32), paramflags) # get the window rect using win32api
def update_window_position():
    global window_position
    rect = GetWindowRect(hwnd)
    window_position = [rect.top, rect.left]
#initial window position
update_window_position()

balls = []

class Ball:
    def __init__(self, radius, color=(30, 30, 255)):
        self.radius = radius
        self.mass = radius**2 * math.pi 
        self.color = color
        self.x = 0
        self.y = 0
        self.velocity = (0, 0)
        self.last_collision = 0

        balls.append(self)
    
    def set_position(self, x, y):
        self.x = x
        self.y = y
        return self

    def apply_force(self, force):
        self.velocity = (self.velocity[0] + force[0], self.velocity[1] + force[1])
        return self

    def check_collision(self, other_ball=None):
        result = [0,0]
        # check for collision with walls
        if not other_ball:
            if self.x + self.radius > screen_width:
                result[0] = -1
            if self.y + self.radius > screen_height:
                result[1] = -1
            if self.x - self.radius <= 0:
                result[0] = 1
            if self.y - self.radius <= 0:
                result[1] = 1
            return result != [0,0], result

        # check for collision with other balls
        if abs(self.x - other_ball.x) < self.radius + other_ball.radius and abs(self.y - other_ball.y) < self.radius + other_ball.radius:
            if self.y - other_ball.y != 0 and self.x - other_ball.x != 0:
                # normal vector
                dx = other_ball.x - self.x
                dy = other_ball.y - self.y
                distance = math.sqrt(dx**2 + dy**2)
                

                # separation
                overlap = (self.radius + other_ball.radius) - distance
                
                if distance != 0:
                    normal_x = dx / distance
                    normal_y = dy / distance
                else:
                    #random separation
                    normal_x = randint(-1, 1)
                    normal_y = randint(-1, 1)
                
                separation_x = normal_x * overlap * 0.5
                separation_y = normal_y * overlap * 0.5
                
                self.x -= separation_x
                self.y -= separation_y
                other_ball.x += separation_x
                other_ball.y += separation_y

                # impulse
                relative_velocity_x = self.velocity[0] - other_ball.velocity[0]
                relative_velocity_y = self.velocity[1] - other_ball.velocity[1]

                dot_product = relative_velocity_x * normal_x + relative_velocity_y * normal_y
                j = -(1 + bounce_resistance) * dot_product / (1/self.mass + 1/other_ball.mass)
                if j > 0: # if they are moving apart, don't apply impulse
                    return False, [0, 0]
                impulse_x = j * normal_x
                impulse_y = j * normal_y

                self.velocity = (self.velocity[0] + impulse_x / self.mass, self.velocity[1] + impulse_y / self.mass)
                other_ball.velocity = (other_ball.velocity[0] - impulse_x / other_ball.mass, other_ball.velocity[1] - impulse_y / other_ball.mass)

                self.last_collision = pygame.time.get_ticks()
                other_ball.last_collision = pygame.time.get_ticks()

                return True, (normal_x, normal_y)
            #otherwise we'll handle it next frame
        
        return False, [0, 0] # no collision
    
    def calculate_physics(self, dt):
        self.apply_force((gravity[0] * self.mass, gravity[1] * self.mass)) # apply gravity
        collision, normal = self.check_collision() # wall collisions
        if collision:
            if normal[0] != 0:
                self.velocity = (
                    -self.velocity[0] * (1-bounce_resistance),
                    self.velocity[1])
                if abs(self.velocity[0]) < (stop_velocity*(self.radius/10)):
                    self.velocity = (0, self.velocity[1])
            if normal[1] != 0:
                self.velocity = (self.velocity[0],
                    -self.velocity[1] * (1-bounce_resistance))
                if abs(self.velocity[1]) < stop_velocity:
                    self.velocity = (self.velocity[0], 0)
        for other_ball in balls:
            if other_ball == self: continue
            collision, normal = self.check_collision(other_ball)
            # if collision: continue


        self.velocity = (self.velocity[0] * (1 - air_resistance * dt), self.velocity[1] * (1 - air_resistance * dt))
        
        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt

        if self.x + self.radius > screen_width:
            self.x = screen_width - self.radius
            self.velocity = (-self.velocity[0] * (1-bounce_resistance), self.velocity[1])
        if self.y + self.radius > screen_height:
            self.y = screen_height - self.radius
            self.velocity = (self.velocity[0], -self.velocity[1] * (1-bounce_resistance))
        if self.x - self.radius <= 0:
            self.x = self.radius+.5
            if self.velocity[0] <= 0:
                self.velocity = (-self.velocity[0] * (1 - bounce_resistance), self.velocity[1])
        if self.y - self.radius <= 0:
            self.y = self.radius+.5
            if self.velocity[1] <= 0:
                self.velocity = (self.velocity[0], -self.velocity[1] * (1 - bounce_resistance))
            


    def draw(self):
        color = self.color
        if debug:
            if pygame.time.get_ticks() - self.last_collision < 150:
                color = (225, 0, 0)
            font = pygame.font.Font(None, 20)
            text = font.render(f"({self.velocity[0]:.2f}, {self.velocity[1]:.2f})", True, (0,0,0))
            screen.blit(text, (self.x - self.radius + 5, self.y - self.radius - 20))
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)

    def destroy(self):
        balls.remove(self)

# loop

def add_ball(radius):
    ball = Ball(radius, (randint(0,255),randint(0,255),randint(0,255))).set_position(randint(radius, screen_width-radius), randint(radius, screen_height-radius))
    ball.apply_force((randint(-start_velocity,start_velocity), randint(-start_velocity,start_velocity)))


held_since = 0

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        if event.type == pygame.KEYDOWN:
            match event.key:
                case pygame.K_ESCAPE: # exit
                    pygame.quit()
                    exit()
                case pygame.K_c: # toggle debug text
                    debug = not debug
                case pygame.K_b: # spawn ball
                    add_ball(randint(10, 20))
                case pygame.K_n: # spawn 3 balls
                    for i in range(3):
                        add_ball(randint(10, 20))
                case pygame.K_BACKSPACE: # delete last ball
                    if len(balls) > 0:
                        balls[-1].destroy()
                case pygame.K_DELETE: # delete first ball
                    if len(balls) > 0:
                        balls[0].destroy()
                case pygame.K_SPACE: # apply random force to all balls
                    for ball in balls:
                        ball.apply_force((randint(-start_velocity,start_velocity), -randint(0,start_velocity*5)))
                case pygame.K_r: # reset all balls' velocity
                    for ball in balls:
                        ball.velocity = (0, 0)
                case pygame.K_m: # toggle dark mode
                    dark_mode = not dark_mode
        
        # resize event
        if event.type == pygame.VIDEORESIZE or event.type == pygame.WINDOWMOVED:
            #ensure that the balls stay in the same position on the screen when window is resized
            old_window_position = window_position
            update_window_position()
            dy = old_window_position[0] - window_position[0] 
            dx = old_window_position[1] - window_position[1]
            if dx != 0 or dy != 0:
                for ball in balls:
                    ball.x += dx
                    ball.y += dy
            if event.type == pygame.VIDEORESIZE:
                # resize the screen
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                screen_width, screen_height = event.w, event.h

    keys = pygame.key.get_pressed()
    # jedi force
    if keys[pygame.K_LEFT]:
        for ball in balls:
            ball.apply_force((-jedi_force/2, 0))
    if keys[pygame.K_RIGHT]:
        for ball in balls:
            ball.apply_force((jedi_force/2, 0))
    if keys[pygame.K_UP]:
        for ball in balls:
            ball.apply_force((0, -jedi_force))
    if keys[pygame.K_DOWN]:
        for ball in balls:
            ball.apply_force((0, jedi_force))

    if keys[pygame.K_BACKSPACE]: # delete last ball
        if len(balls) > 0:
            balls[-1].destroy()
    if keys[pygame.K_DELETE]: # delete first ball
        if len(balls) > 0:
            balls[0].destroy()

    # hold b spawn ball
    if keys[pygame.K_b]:
        held_since += 1
        if held_since > 15: # slight delay to prevent accidental spawns
            add_ball(randint(10, 20))
    else:
        held_since = 0

    screen.fill((255, 255, 255) if not dark_mode else (0, 0, 0))

    dt = pygame.time.Clock().tick(60) / 1000.0

    # update all balls
    for ball in balls:
        ball.calculate_physics(dt)
        ball.draw()

    pygame.display.flip()