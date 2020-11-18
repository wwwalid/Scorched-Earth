import pygame as pg
import random as rd
import numpy as np
import time

# Colors
black       = (0,0,0)
white       = (255,255,255)
red         = (255, 0, 0)
green       = (0, 255, 0)
darkgreen   = (0, 200, 0)
yellow      = (255, 255, 0)
orange      = (255, 153, 51)
blue        = (0, 0, 255)
lightblue   = (135,206,250)
purple      = (128, 0, 128)

tank_colors = [black, red, green, yellow, orange]

# Create window
background_color = lightblue
xmax = 1200  # pixels
ymax = 800  # pixels
scr = pg.display.set_mode((xmax, ymax))
pg.display.set_caption('Scorched Earth')

class Cursor:
    cursor_img = pg.image.load("cursor.png").convert_alpha()
    cursor_img.set_colorkey(white)
    rect = cursor_img.get_rect()

    def draw(self):
        pg.mouse.set_visible(False)
        self.rect.center = pg.mouse.get_pos()
        scr.blit(self.cursor_img, self.rect)

class Ground():
    WIDTH = xmax
    HEIGHT = 100
    COLOR = darkgreen
    y = ymax - HEIGHT

    def draw(self):
        self.ground = pg.Rect(0, self.y, self.WIDTH, self.HEIGHT)
        pg.draw.rect(scr, self.COLOR, self.ground)

class Player():
    HEIGHT = 20
    WIDTH = 60
    CANNON_LENGTH = 30
    WHEEL_RADIUS = 8
    ALPHA = 60
    SPEED = 5
    FUEL = 100
    HEALTH = 100
    HIT = False
    y = ymax - Ground.HEIGHT - HEIGHT - WHEEL_RADIUS

    def __init__(self, name, x, color, alpha, power):
        self.name = name
        self.x = x
        self.color = color
        self.alpha = np.radians(alpha)
        self.power = power

    def update_cannon(self):
        # Update value for alpha
        self.alpha = -np.arctan2(pg.mouse.get_pos()[1] - self.y, pg.mouse.get_pos()[0] - self.x)
        if self.alpha <= np.pi / 4:
            self.alpha = np.pi / 4
        if self.alpha >= 3 / 4 * np.pi:
            self.alpha = 3 / 4 * np.pi

        # Calculate power
        self.power = int(np.sqrt( (pg.mouse.get_pos()[1] - self.y) ** 2 + (pg.mouse.get_pos()[0] - self.x - self.WIDTH/2) ** 2 ) / 5)
        if self.power >= 100:
            self.power = 100

    def move_right(self):
        if not self.x + self.WIDTH >= xmax and self.FUEL > 0:
            self.x += self.SPEED
            self.FUEL -= 2
    def move_left(self):
        if not self.x <= 0 and self.FUEL > 0:
            self.x -= self.SPEED
            self.FUEL -= 2

    def draw_tanks(self):
        # Draw tank
        self.tank = pg.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
        pg.draw.rect(scr, self.color, self.tank)

        # Draw cannon
        self.cannon_start = (self.tank.centerx, self.tank.top)
        self.cannon_end = (self.tank.centerx + self.CANNON_LENGTH * np.cos(self.alpha),
                      self.tank.top - self.CANNON_LENGTH * np.sin(self.alpha))
        pg.draw.line(scr, self.color, self.cannon_start, self.cannon_end, 6)
        pg.draw.circle(scr, self.color, (self.tank.centerx, self.tank.top), 2 * self.WHEEL_RADIUS)

        # Draw wheels
        pg.draw.circle(scr, black, (self.tank.left + self.WHEEL_RADIUS, self.tank.bottom), self.WHEEL_RADIUS)
        pg.draw.circle(scr, black, (self.tank.right - self.WHEEL_RADIUS, self.tank.bottom), self.WHEEL_RADIUS)
        pg.draw.circle(scr, black, (self.tank.centerx, self.tank.bottom), self.WHEEL_RADIUS)

        # Wheelcaps
        pg.draw.circle(scr, white, (self.tank.left + self.WHEEL_RADIUS, self.tank.bottom), 2)
        pg.draw.circle(scr, white, (self.tank.right - self.WHEEL_RADIUS, self.tank.bottom), 2)
        pg.draw.circle(scr, white, (self.tank.centerx, self.tank.bottom), 2)

    def draw_bars(self):
        # Draw health bar
        barwidth = 300
        health_bar = pg.Rect(xmax - 1.25 * barwidth, 20, barwidth, 30)
        self.health = pg.Rect(xmax - 1.25 * barwidth, 20, 3 * self.HEALTH, 30)
        pg.draw.rect(scr, (255 - self.HEALTH * 255 / 100, self.HEALTH * 255 / 100, 0), self.health)
        pg.draw.rect(scr, white, health_bar, 4)
        write_text("HEALTH", xmax - 1.8 * barwidth, 20, white, 38)

        # Draw fuel bar
        fuel_bar = pg.Rect(xmax - 1.25 * barwidth, 60,  barwidth, 30)
        self.fuel = pg.Rect(xmax - 1.25 * barwidth, 60, 3 * self.FUEL, 30)
        pg.draw.rect(scr, green, self.fuel)
        pg.draw.rect(scr, white, fuel_bar, 4)
        write_text("FUEL", xmax - 1.8 * barwidth, 60, white, 38)

        # Draw power bar
        power_bar = pg.Rect(xmax - 1.25 * barwidth, 100, barwidth, 30)
        self.powerbar = pg.Rect(xmax - 1.25 * barwidth, 100, 3 * self.power, 30)
        pg.draw.rect(scr, (255, 255 - self.power * 255/100, 0), self.powerbar)
        pg.draw.rect(scr, white, power_bar, 4)
        write_text("POWER", xmax - 1.8 * barwidth, 100, white, 38)

    def draw_health(self):
        # Draw small health bars above tanks
        barwidth = self.WIDTH
        barheight = self.HEIGHT / 3
        self.h_bar = pg.Rect(self.x, self.y - 40, self.HEALTH * barwidth / 100, barheight)
        pg.draw.rect(scr, (255 - self.HEALTH * 255 / 100, self.HEALTH * 255 / 100, 0), self.h_bar)

class Projectile():
    # Constants and initial values
    Cd = 0.07
    S = 0.005
    m = 1
    rho = 1.225
    g = -3500
    COLOR = black
    RADIUS = 5
    t0 = 0

    def __init__(self, power, alpha, x, y):
        self.V = 20 * power
        self.gamma = alpha
        self.vx = self.V * np.cos(self.gamma)
        self.vy = self.V * np.sin(self.gamma)
        self.x = x
        self.y = y
        self.trajectory = [(self.x, self.y)]

    def calc_trajec(self, dt):
        # Forces
        self.D = self.Cd * 0.5 * self.rho * self.V ** 2 * self.S
        self.W = self.m * self.g

        # Net force
        self.Fx = -self.D * np.cos(self.gamma)
        self.Fy = self.W - self.D * np.sin(self.gamma)

        # acceleration and velocity
        self.ax = self.Fx / self.m
        self.ay = self.Fy / self.m

        self.vy += self.ay * dt
        self.vx += self.ax * dt

        self.V = np.sqrt( self.vx ** 2 + self.vy ** 2)

        # Update flight path angle
        self.gamma = np.arctan2(self.vy , self.vx)

        # Position
        self.x += int(self.vx * dt)
        self.y -= int(self.vy * dt)

        # # When the bal hits the ground, show explosion
        if self.y >= Ground.y:
            self.y = Ground.y
            self.vx = 0

            self.t0 += dt
            self.RADIUS = 40
            self.COLOR = purple
            if self.t0 > 0.5:
                self.RADIUS = 0
                self.x = -1
                self.y = 0
                self.trajectory = []

        # Trajectory line
        self.trajectory.append((self.x, self.y))

    def fire(self):
        # Draw projectile
        pg.draw.circle(scr, self.COLOR, (int(self.x), int(self.y)), self.RADIUS)
        if len(self.trajectory) > 1:
            pg.draw.lines(scr, red, False, self.trajectory)

def write_text(txt, x_pos, y_pos, color, font=32):
    font = pg.font.Font('Minecraft.ttf', font)
    text = font.render(txt, True, color)
    Rect = text.get_rect()
    Rect.topleft = (x_pos, y_pos)
    scr.blit(text, Rect)

def draw_window(scr, players, ground, turn, projectile, shot, dt, cursor):
    # Draw background
    scr.fill(background_color)

    # Draw text
    txt = f"Player {players[turn].name}: Power= {players[turn].power}%, angle= {int(np.degrees(players[turn].alpha))}"
    write_text(txt, 20, 20, players[turn].color)

    # Draw ground
    ground.draw()

    # Draw players
    for player in players:
        player.draw_tanks()
        player.draw_health()

    # Draw fuel bars
    players[turn].draw_bars()

    # Draw trajectory
    if shot:
        projectile.calc_trajec(dt)
        projectile.fire()

    # Draw cursor
    cursor.draw()

def got_hit(player, projectile):
    if player.x - projectile.RADIUS <= projectile.x <= player.x + player.WIDTH + projectile.RADIUS and projectile.y == Ground.y:
        return True
    return False

def main():
    # Create players
    players = []
    n = int(input("Start game with how many players? (max 5) "))

    for i in range(n):
        players.append(Player(input(f"Enter name for player {i+1}: "),
                              rd.randrange(0, xmax - Player.WIDTH),
                              tank_colors[i], 60, 100))

    # players.append(Player("Walid", rd.randrange(0, xmax - Player.WIDTH), tank_colors[0], 60, 100))
    # players.append(Player("Rayan", rd.randrange(0, xmax - Player.WIDTH), tank_colors[1], 60, 100))
    # players.append(Player("Nihad", rd.randrange(0, xmax - Player.WIDTH), tank_colors[2], 60, 100))

    # Indicate players turn
    turn = 0

    # initialize pygame
    pg.init()

    # Play music
    pg.mixer.init()
    pg.mixer.music.load("Song.mp3")
    pg.mixer.music.play()

    # Create other objects
    ground = Ground()
    projectile = None

    # Clock
    clock = pg.time.Clock()

    running = True
    shot = False
    while running and len(players) > 1:
        cursor = Cursor()
        # 30 fps
        clock.tick(30)
        dt = clock.get_fps() / 1000

        # Event pump
        pg.event.pump()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False

                if event.key == pg.K_SPACE:
                    # Shoot projectile
                    shot = True
                    Player.HIT = True
                    projectile = Projectile(players[turn].power, players[turn].alpha,
                                            players[turn].x + Player.WIDTH/2 + Player.CANNON_LENGTH * np.cos(players[turn].alpha),
                                            players[turn].y - Player.CANNON_LENGTH * np.sin(players[turn].alpha))
                    players[turn].FUEL = 100

                    turn += 1
                    if turn > n - 1:
                        turn = 0

        # Move left and right
        keys = pg.key.get_pressed()
        if keys[pg.K_RIGHT]:
            players[turn].move_right()
        if keys[pg.K_LEFT]:
            players[turn].move_left()

        # Calculate Power and angle
        players[turn].update_cannon()

        # Check if tank got hit and deduct 40 points of health
        if Player.HIT:
            for player in players:
                if got_hit(player, projectile):
                    player.HEALTH -= 40
                    if player.HEALTH <= 0:
                        player.HEALTH = 0
                        players.remove(player)
                        n -= 1
                        if turn > n - 1:
                            turn = 0
                    Player.HIT = False

        # Clear screen
        draw_window(scr, players, ground, turn, projectile, shot, dt, cursor)

        # Update screen
        pg.display.flip()

    print("\n", players[0].name.capitalize(), "is the Winner!")
    pg.mixer_music.stop()
    pg.quit()

main()