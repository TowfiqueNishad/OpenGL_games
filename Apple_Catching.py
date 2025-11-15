'''
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import math
import random
import time


# --- CONSTANTS ---
WINDOW_WIDTH, WINDOW_HEIGHT = 1200, 800
WORLD_SIZE = 2000
TREE_COUNT = 30
SHELTER_COUNT = 6
APPLE_FALL_INTERVAL = 0.5  # More frequent (was 1.0)
APPLE_FALL_SPEED = 8
APPLE_RADIUS = 12
BAG_RADIUS = 30
SCORE_SPEED_STEP = 50
SPEED_INCREASE = 0.5
PLAYER_SPEED = 8
TURN_SPEED = 5  # Character rotation speed
HOUSE_POS = [0, 0]
HOUSE_SIZE = 150
DOOR_SIZE = 50

SHOP_SIZE = 100  # size of the shop square

# Game duration (5 minutes)
game_duration = 300

# Rain constants
RAIN_MIN_INTERVAL = 8
RAIN_MAX_INTERVAL = 15
RAIN_DURATION = 9
RAIN_DAMAGE_TIME = 3
RAIN_DAMAGE = 3

# --- SNOWFALL CONSTANTS ---
SNOW_MIN_INTERVAL = 40
SNOW_MAX_INTERVAL = 60
SNOW_DURATION = 15
SNOW_FALL_SPEED = 5
SNOWFLAKES_COUNT = 200

# Camera controls
cam_angle = 0
cam_distance = 500
cam_height = 300

# Day/night cycle
day_cycle_duration = 60.0  # 60 seconds for full day cycle
game_start_time = time.time()

# Sky features
clouds = []
stars = []

keys = {}
apples = []
last_apple_time = time.time()


# --- SNOWFALL STATE ---
snowflakes = []
snow_start_time = 0
snow_active = False
snow_next_time = time.time() + random.randint(SNOW_MIN_INTERVAL, SNOW_MAX_INTERVAL)


# --- CLASSES ---
class Player:
    def __init__(self):
        self.pos = [100, 100, 0]
        self.angle = 0
        self.inside_house = False
        self.inside_shop = False
        self.score = 0
        self.alive = True
        self.health = 100
        self.under_shelter = False
        self.won = False


player = Player()


class RainSystem:
    def __init__(self):
        self.is_raining = False
        self.rain_start_time = 0
        self.next_rain_time = time.time() + random.randint(RAIN_MIN_INTERVAL, RAIN_MAX_INTERVAL)
        self.player_rain_exposure_start = 0
        self.player_in_rain = False


rain_system = RainSystem()


# --- DOG CLASS WITH FIXED SIZE 20 ---
class Dog:
    def __init__(self, x, y):
        self.pos = [x, y]
        self.size = 30  # changed to 20

    def update(self):
        # Simple random movement for dogs
        self.pos[0] += random.uniform(-2, 2)
        self.pos[1] += random.uniform(-2, 2)

        # Keep dogs within world bounds
        self.pos[0] = max(-WORLD_SIZE + 100, min(WORLD_SIZE - 100, self.pos[0]))
        self.pos[1] = max(-WORLD_SIZE + 100, min(WORLD_SIZE - 100, self.pos[1]))

    def draw(self):
        glPushMatrix()
        glTranslatef(self.pos[0], self.pos[1], 22)
        glColor3f(0.44, 0.34, 0.24)  # Main body color
        # Body (big sphere)
        glutSolidSphere(self.size, 16, 16)
        # Head
        glPushMatrix()
        glTranslatef(0, self.size * 0.5, self.size * 0.3)
        glColor3f(0.61, 0.45, 0.22)
        glutSolidSphere(self.size * 0.4, 14, 14)
        # Face details (nose)
        glColor3f(0.1, 0.1, 0.1)
        glPushMatrix()
        glTranslatef(self.size * 0.15, -self.size * 0.1, self.size * 0.1)
        glutSolidSphere(self.size * 0.1, 7, 7)
        glPopMatrix()
        # Ears
        glPushMatrix()
        glTranslatef(self.size * 0.25, self.size * 0.2, self.size * 0.35)
        glutSolidCone(self.size * 0.1, self.size * 0.25, 6, 6)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-self.size * 0.25, self.size * 0.2, self.size * 0.35)
        glutSolidCone(self.size * 0.1, self.size * 0.25, 6, 6)
        glPopMatrix()
        glPopMatrix()  # head
        # Legs (4 legs)
        for dx, dy in [(-self.size * 0.4, -self.size * 0.3), (self.size * 0.4, -self.size * 0.3),
                       (-self.size * 0.4, self.size * 0.3), (self.size * 0.4, self.size * 0.3)]:
            glPushMatrix()
            glTranslatef(dx, dy, -self.size * 0.5)
            glScalef(self.size * 0.15, self.size * 0.15, self.size * 0.75)
            glutSolidCube(1)
            glPopMatrix()
        # Tail
        glPushMatrix()
        glTranslatef(0, -self.size * 0.6, self.size * 0.15)
        glRotatef(40, 1, 0, 0)
        glutSolidCone(self.size * 0.2, self.size * 0.6, 6, 6)
        glPopMatrix()
        glPopMatrix()


# --- CREATE MULTIPLE DOGS AROUND THE WORLD ---
dogs = []
for _ in range(6):
    dogs.append(Dog(random.randint(-WORLD_SIZE + 200, WORLD_SIZE - 200), random.randint(-WORLD_SIZE + 200, WORLD_SIZE - 200)))


class QuestNPC:
    def __init__(self):
        self.pos = [random.randint(-400, 400), random.randint(-400, 400), 0]


quest_npc = QuestNPC()


class ShopNPC:
    def __init__(self):
        self.pos = [random.randint(-450, 450), random.randint(-450, 450), 0]


shop_npc = ShopNPC()


# Generate random cloud positions
def generate_clouds():
    global clouds
    clouds = []
    for _ in range(8):
        clouds.append({
            'x': random.uniform(-2000, 2000),
            'y': random.uniform(-2000, 2000),
            'z': random.uniform(600, 900),
            'size': random.uniform(80, 150),
            'drift_x': random.uniform(-0.5, 0.5),
            'drift_y': random.uniform(-0.5, 0.5)
        })


# Generate random star positions
def generate_stars():
    global stars
    stars = []
    for _ in range(50):
        stars.append({
            'x': random.uniform(-3000, 3000),
            'y': random.uniform(-3000, 3000),
            'z': random.uniform(1200, 2000),
            'brightness': random.uniform(0.3, 1.0),
            'twinkle_speed': random.uniform(2, 8)
        })


# Initialize sky features
generate_clouds()
generate_stars()


# Generate random tree positions (avoid house area)
trees = []
for _ in range(TREE_COUNT):
    while True:
        x = random.randint(-WORLD_SIZE + 200, WORLD_SIZE - 200)
        y = random.randint(-WORLD_SIZE + 200, WORLD_SIZE - 200)
        # Make sure trees are not too close to house
        if abs(x - HOUSE_POS[0]) > HOUSE_SIZE + 100 or abs(y - HOUSE_POS[1]) > HOUSE_SIZE + 100:
            trees.append([x, y])
            break


# Generate random shelter positions
shelters = []
max_attempts = 100  # Prevent infinite loops
for _ in range(SHELTER_COUNT):
    attempts = 0
    while attempts < max_attempts:
        x = random.randint(-WORLD_SIZE + 400, WORLD_SIZE - 400)
        y = random.randint(-WORLD_SIZE + 400, WORLD_SIZE - 400)
        # Make sure shelters are not too close to house or trees
        valid_position = True

        # Check distance from house (reduced requirement)
        house_dist = math.sqrt((x - HOUSE_POS[0]) ** 2 + (y - HOUSE_POS[1]) ** 2)
        if house_dist < HOUSE_SIZE + 150:
            valid_position = False

        # Check distance from trees (reduced requirement)
        if valid_position:
            for tree_x, tree_y in trees:
                tree_dist = math.sqrt((x - tree_x) ** 2 + (y - tree_y) ** 2)
                if tree_dist < 200:
                    valid_position = False
                    break

        # Check distance from other shelters (reduced requirement)
        if valid_position:
            for shelter_x, shelter_y in shelters:
                shelter_dist = math.sqrt((x - shelter_x) ** 2 + (y - shelter_y) ** 2)
                if shelter_dist < 250:
                    valid_position = False
                    break

        if valid_position:
            shelters.append([x, y])
            break

        attempts += 1

    # If we couldn't find a valid position after max_attempts, place it anyway
    if attempts >= max_attempts:
        x = random.randint(-WORLD_SIZE + 400, WORLD_SIZE - 400)
        y = random.randint(-WORLD_SIZE + 400, WORLD_SIZE - 400)
        shelters.append([x, y])


# --- DAY/NIGHT CYCLE FUNCTIONS ---
def get_day_time():
    """Returns time of day as a value between 0 (midnight) and 1 (next midnight)"""
    elapsed = time.time() - game_start_time
    return (elapsed % day_cycle_duration) / day_cycle_duration


def get_sky_color():
    """Returns sky color based on time of day"""
    day_time = get_day_time()
    hour = day_time * 24

    if 5 <= hour < 7:  # Dawn
        t = (hour - 5) / 2
        r = 0.1 + t * 0.43
        g = 0.1 + t * 0.61
        b = 0.2 + t * 0.72
    elif 7 <= hour < 8:  # Early morning
        t = (hour - 7) / 1
        r = 0.53 + t * 0.17
        g = 0.71 + t * 0.10
        b = 0.92 + t * 0.0
    elif 8 <= hour < 17:  # Day
        r, g, b = 0.53, 0.81, 0.92
    elif 17 <= hour < 19:  # Sunset
        t = (hour - 17) / 2
        r = 0.53 + t * 0.37
        g = 0.81 - t * 0.41
        b = 0.92 - t * 0.62
    elif 19 <= hour < 21:  # Dusk
        t = (hour - 19) / 2
        r = 0.9 - t * 0.6
        g = 0.4 - t * 0.2
        b = 0.3 - t * 0.0
    elif 21 <= hour < 23:  # Evening
        t = (hour - 21) / 2
        r = 0.3 - t * 0.15
        g = 0.2 - t * 0.05
        b = 0.3 - t * 0.05
    else:  # Night (23-5)
        r, g, b = 0.05, 0.05, 0.15

    # Darken sky during rain
    if rain_system.is_raining:
        r *= 0.4
        g *= 0.4
        b *= 0.4

    return r, g, b


def get_ambient_light():
    """Returns ambient light intensity based on time of day"""
    day_time = get_day_time()
    hour = day_time * 24

    if 5 <= hour < 7:  # Dawn
        t = (hour - 5) / 2
        base_light = 0.3 + t * 0.7
    elif 7 <= hour < 17:  # Day
        base_light = 1.0
    elif 17 <= hour < 19:  # Sunset
        t = (hour - 17) / 2
        base_light = 1.0 - t * 0.4
    elif 19 <= hour < 21:  # Dusk
        t = (hour - 19) / 2
        base_light = 0.6 - t * 0.25
    elif 21 <= hour < 23:  # Evening
        t = (hour - 21) / 2
        base_light = 0.35 - t * 0.05
    else:  # Night
        base_light = 0.3

    # Reduce light during rain
    if rain_system.is_raining:
        base_light *= 0.6

    return base_light


def is_day_time():
    """Returns True if it's daytime (sun should be visible)"""
    day_time = get_day_time()
    hour = day_time * 24
    return 6 <= hour < 18


def is_night_time():
    """Returns True if it's nighttime (moon and stars should be visible)"""
    day_time = get_day_time()
    hour = day_time * 24
    return hour >= 20 or hour < 6


def get_sun_moon_position():
    """Calculate sun/moon position across the sky"""
    day_time = get_day_time()
    angle = (day_time * 360) - 90

    x = 1800 * math.cos(math.radians(angle))
    y = 0
    z = 800 + 400 * math.sin(math.radians(angle))

    return x, y, z


# --- DRAWING FUNCTIONS ---
def draw_clouds():
    """Draw clouds in the sky"""
    current_time = time.time()

    # Update cloud positions (drift)
    for cloud in clouds:
        cloud['x'] += cloud['drift_x']
        cloud['y'] += cloud['drift_y']

        # Wrap clouds around
        if cloud['x'] > 3000:
            cloud['x'] = -3000
        elif cloud['x'] < -3000:
            cloud['x'] = 3000
        if cloud['y'] > 3000:
            cloud['y'] = -3000
        elif cloud['y'] < -3000:
            cloud['y'] = 3000

    for cloud in clouds:
        glPushMatrix()
        glTranslatef(player.pos[0] + cloud['x'], player.pos[1] + cloud['y'], cloud['z'])

        # Cloud color - gray during rain, white otherwise
        if rain_system.is_raining:
            glColor4f(0.3, 0.3, 0.3, 0.8)
        else:
            glColor4f(1.0, 1.0, 1.0, 0.7)

        # Draw cloud as multiple spheres
        for i in range(5):
            glPushMatrix()
            offset_x = (i - 2) * cloud['size'] * 0.3
            offset_y = random.uniform(-cloud['size'] * 0.2, cloud['size'] * 0.2)
            offset_z = random.uniform(-cloud['size'] * 0.1, cloud['size'] * 0.1)
            glTranslatef(offset_x, offset_y, offset_z)
            glutSolidSphere(cloud['size'] * random.uniform(0.6, 1.0), 10, 10)
            glPopMatrix()

        glPopMatrix()


def draw_stars():
    """Draw stars in the night sky"""
    if not is_night_time():
        return

    current_time = time.time()

    for star in stars:
        # Twinkling effect
        twinkle = 0.5 + 0.5 * math.sin(current_time * star['twinkle_speed'])
        brightness = star['brightness'] * twinkle

        glPushMatrix()
        glTranslatef(player.pos[0] + star['x'], player.pos[1] + star['y'], star['z'])
        glColor4f(brightness, brightness, brightness, 1.0)

        # Draw star as a small bright sphere
        glutSolidSphere(3, 6, 6)
        glPopMatrix()


def draw_sun():
    """Draw the sun during daytime"""
    if not is_day_time():
        return

    x, y, z = get_sun_moon_position()

    # Don't draw sun if it's below horizon
    if z < 100:
        return

    glPushMatrix()
    glTranslatef(player.pos[0] + x, player.pos[1] + y, z)

    # Sun color - dimmer during rain
    if rain_system.is_raining:
        glColor3f(0.8, 0.7, 0.3)
    else:
        glColor3f(1.0, 1.0, 0.3)

    # Draw sun
    glutSolidSphere(100, 20, 20)

    # Sun rays (only when not raining)
    if not rain_system.is_raining:
        glColor4f(1.0, 1.0, 0.5, 0.3)
        for i in range(12):
            angle = i * 30
            glPushMatrix()
            glRotatef(angle, 0, 0, 1)
            glTranslatef(150, 0, 0)
            glScalef(40, 8, 8)
            glutSolidCube(1.0)
            glPopMatrix()

    glPopMatrix()


def draw_moon():
    """Draw the moon during nighttime"""
    if not is_night_time():
        return

    x, y, z = get_sun_moon_position()

    # Don't draw moon if it's below horizon
    if z < 100:
        return

    glPushMatrix()
    glTranslatef(player.pos[0] + x, player.pos[1] + y, z)

    # Moon color
    glColor3f(0.9, 0.9, 0.8)

    # Draw moon
    glutSolidSphere(80, 20, 20)

    # Moon craters (darker spots)
    glColor3f(0.7, 0.7, 0.6)
    glPushMatrix()
    glTranslatef(20, 20, 60)
    glutSolidSphere(12, 8, 8)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-15, 30, 65)
    glutSolidSphere(8, 8, 8)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(35, -10, 55)
    glutSolidSphere(6, 8, 8)
    glPopMatrix()

    glPopMatrix()


def draw_ground():
    # Apply lighting based on day/night cycle
    light_intensity = get_ambient_light()
    base_green = 0.6 * light_intensity
    glColor3f(0.2 * light_intensity, base_green, 0.2 * light_intensity)
    glBegin(GL_QUADS)
    glVertex3f(-WORLD_SIZE, -WORLD_SIZE, 0)
    glVertex3f(WORLD_SIZE, -WORLD_SIZE, 0)
    glVertex3f(WORLD_SIZE, WORLD_SIZE, 0)
    glVertex3f(-WORLD_SIZE, WORLD_SIZE, 0)
    glEnd()


def draw_house():
    light_intensity = get_ambient_light()

    glPushMatrix()
    glTranslatef(HOUSE_POS[0], HOUSE_POS[1], 0)

    # House walls (square box)
    glColor3f(0.7 * light_intensity, 0.5 * light_intensity, 0.3 * light_intensity)
    glPushMatrix()
    glTranslatef(0, 0, HOUSE_SIZE // 2)
    glScalef(HOUSE_SIZE, HOUSE_SIZE, HOUSE_SIZE)
    glutSolidCube(1.0)
    glPopMatrix()

    # Door opening (cut out from front wall)
    glColor3f(0.0, 0.0, 0.0)  # Black for door opening
    glPushMatrix()
    glTranslatef(0, -HOUSE_SIZE // 2 + 5, DOOR_SIZE // 2)
    glScalef(DOOR_SIZE, 10, DOOR_SIZE)
    glutSolidCube(1.0)
    glPopMatrix()

    # Add window lights during night
    if light_intensity < 0.6:
        glColor3f(1.0, 1.0, 0.8)  # Warm light
        glPushMatrix()
        glTranslatef(30, -HOUSE_SIZE // 2 + 2, 80)
        glScalef(20, 5, 20)
        glutSolidCube(1.0)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(-30, -HOUSE_SIZE // 2 + 2, 80)
        glScalef(20, 5, 20)
        glutSolidCube(1.0)
        glPopMatrix()

    glPopMatrix()


def draw_tree(x, y):
    light_intensity = get_ambient_light()

    glPushMatrix()
    glTranslatef(x, y, 0)

    # Tree trunk
    glColor3f(0.4 * light_intensity, 0.2 * light_intensity, 0.1 * light_intensity)
    glPushMatrix()
    glTranslatef(0, 0, 100)
    glScalef(5, 5, 20)
    glutSolidCube(10)
    glPopMatrix()

    # Tree foliage
    glColor3f(0.1 * light_intensity, 0.5 * light_intensity, 0.1 * light_intensity)
    glTranslatef(0, 0, 250)
    glutSolidSphere(150, 20, 20)

    glPopMatrix()


def draw_apple(apple):
    light_intensity = get_ambient_light()

    glPushMatrix()
    x, y, z = apple['pos']
    glTranslatef(x, y, z)
    if apple['type'] == 'red':
        glColor3f(1 * light_intensity, 0, 0)
    elif apple['type'] == 'golden':
        glColor3f(1 * light_intensity, 0.84 * light_intensity, 0 * light_intensity)
    else:
        glColor3f(0.2 * light_intensity, 0.2 * light_intensity, 0.2 * light_intensity)
    glutSolidSphere(APPLE_RADIUS, 10, 10)
    glPopMatrix()


def draw_text(x, y, text):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1, 1, 1)
    glRasterPos2f(x, y)
    for c in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_shelter(x, y):
    """Draw a shelter with roof and support posts"""
    light_intensity = get_ambient_light()

    glPushMatrix()
    glTranslatef(x, y, 0)

    # Support posts (4 corners)
    glColor3f(0.4 * light_intensity, 0.3 * light_intensity, 0.2 * light_intensity)
    post_positions = [(-60, -60), (60, -60), (60, 60), (-60, 60)]
    for px, py in post_positions:
        glPushMatrix()
        glTranslatef(px, py, 100)
        glScalef(8, 8, 20)
        glutSolidCube(10)
        glPopMatrix()

    # Roof
    glColor3f(0.6 * light_intensity, 0.2 * light_intensity, 0.1 * light_intensity)
    glPushMatrix()
    glTranslatef(0, 0, 220)
    glScalef(14, 14, 1)
    glutSolidCube(10)
    glPopMatrix()

    # Roof supports
    glColor3f(0.5 * light_intensity, 0.3 * light_intensity, 0.2 * light_intensity)
    glPushMatrix()
    glTranslatef(0, 0, 210)
    glScalef(2, 12, 1)
    glutSolidCube(8)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 210)
    glScalef(12, 2, 1)
    glutSolidCube(8)
    glPopMatrix()

    glPopMatrix()


def draw_boundary_walls():
    """Draw walls around the world boundary"""
    light_intensity = get_ambient_light()
    wall_height = 200
    wall_thickness = 50

    glColor3f(0.4 * light_intensity, 0.4 * light_intensity, 0.4 * light_intensity)

    # North wall
    glPushMatrix()
    glTranslatef(0, WORLD_SIZE - wall_thickness // 2, wall_height // 2)
    glScalef(WORLD_SIZE * 2, wall_thickness, wall_height)
    glutSolidCube(1.0)
    glPopMatrix()

    # South wall
    glPushMatrix()
    glTranslatef(0, -WORLD_SIZE + wall_thickness // 2, wall_height // 2)
    glScalef(WORLD_SIZE * 2, wall_thickness, wall_height)
    glutSolidCube(1.0)
    glPopMatrix()

    # East wall
    glPushMatrix()
    glTranslatef(WORLD_SIZE - wall_thickness // 2, 0, wall_height // 2)
    glScalef(wall_thickness, WORLD_SIZE * 2, wall_height)
    glutSolidCube(1.0)
    glPopMatrix()

    # West wall
    glPushMatrix()
    glTranslatef(-WORLD_SIZE + wall_thickness // 2, 0, wall_height // 2)
    glScalef(wall_thickness, WORLD_SIZE * 2, wall_height)
    glutSolidCube(1.0)
    glPopMatrix()


def draw_rain():
    """Draw rain particles"""
    if not rain_system.is_raining:
        return

    glColor4f(0.6, 0.8, 1.0, 0.6)
    glBegin(GL_LINES)

    # Draw rain drops around player
    for i in range(500):
        # Random position around player
        x = player.pos[0] + random.randint(-800, 800)
        y = player.pos[1] + random.randint(-800, 800)
        z_top = random.randint(200, 600)
        z_bottom = z_top - 20

        glVertex3f(x, y, z_top)
        glVertex3f(x + 2, y + 2, z_bottom)

    glEnd()


# --- SNOWFALL IMPLEMENTATION ---
def init_snowflakes():
    global snowflakes
    snowflakes.clear()
    for _ in range(SNOWFLAKES_COUNT):
        snowflakes.append({
            'x': random.uniform(-WORLD_SIZE, WORLD_SIZE),
            'y': random.uniform(-WORLD_SIZE, WORLD_SIZE),
            'z': random.uniform(300, 900),
            'size': random.uniform(4, 8),
            'speed': random.uniform(SNOW_FALL_SPEED * 0.8, SNOW_FALL_SPEED * 1.2)
        })


def update_snow():
    global snow_active, snow_start_time, snow_next_time
    now = time.time()

    # Don't start snow if it's raining
    if not snow_active and now >= snow_next_time and not rain_system.is_raining:
        snow_active = True
        snow_start_time = now

    # Stop snow if rain starts
    if snow_active and rain_system.is_raining:
        snow_active = False
        snow_next_time = now + random.randint(SNOW_MIN_INTERVAL, SNOW_MAX_INTERVAL)
        init_snowflakes()

    if snow_active:
        if now - snow_start_time > SNOW_DURATION:
            snow_active = False
            snow_next_time = now + random.randint(SNOW_MIN_INTERVAL, SNOW_MAX_INTERVAL)
            init_snowflakes()
        else:
            for flake in snowflakes:
                flake['z'] -= flake['speed']
                if flake['z'] < 100:
                    flake['z'] = random.uniform(500, 900)
                    flake['x'] = player.pos[0] + random.uniform(-WORLD_SIZE, WORLD_SIZE)
                    flake['y'] = player.pos[1] + random.uniform(-WORLD_SIZE, WORLD_SIZE)


def draw_snow():
    if not snow_active:
        return
    glPointSize(7)
    glColor4f(1.0, 1.0, 1.0, 0.8)
    glBegin(GL_POINTS)
    for flake in snowflakes:
        glVertex3f(flake['x'], flake['y'], flake['z'])
    glEnd()


def draw_player():
    if player.inside_house or player.inside_shop:
        return

    px, py, pz = player.pos

    # Draw player body
    glPushMatrix()
    glTranslatef(px, py, pz + 35)
    glRotatef(player.angle, 0, 0, 1)
    glColor3f(0.8, 0.2, 0.2)
    glutSolidSphere(20, 20, 20)

    # Draw head
    glPushMatrix()
    glTranslatef(0, 0, 30)
    glColor3f(1, 0.8, 0.6)
    glutSolidSphere(15, 20, 20)

    # Draw eyes (positioned in front of head based on player angle)
    glPushMatrix()
    glColor3f(0, 0, 0)
    # Right eye
    glPushMatrix()
    glTranslatef(5, -12, 8)  # Position in front of face
    glutSolidSphere(2, 8, 8)
    glPopMatrix()
    # Left eye
    glPushMatrix()
    glTranslatef(-5, -12, 8)  # Position in front of face
    glutSolidSphere(2, 8, 8)
    glPopMatrix()
    glPopMatrix()

    glPopMatrix()

    # Draw left arm
    glPushMatrix()
    glTranslatef(-25, 0, 5)
    glRotatef(-20, 0, 1, 0)  # Angle arm forward
    glColor3f(1, 0.8, 0.6)
    glScalef(1, 1, 3)
    glutSolidCube(8)
    glPopMatrix()

    # Draw right arm
    glPushMatrix()
    glTranslatef(25, 0, 5)
    glRotatef(20, 0, 1, 0)  # Angle arm forward
    glColor3f(1, 0.8, 0.6)
    glScalef(1, 1, 3)
    glutSolidCube(8)
    glPopMatrix()

    # Draw left hand
    glPushMatrix()
    glTranslatef(-15, -10, -5)
    glColor3f(1, 0.8, 0.6)
    glutSolidSphere(6, 10, 10)
    glPopMatrix()

    # Draw right hand
    glPushMatrix()
    glTranslatef(15, -10, -5)
    glColor3f(1, 0.8, 0.6)
    glutSolidSphere(6, 10, 10)
    glPopMatrix()

    glPopMatrix()

    # Draw bucket (in front of player)
    glPushMatrix()
    glTranslatef(px, py, pz)
    glRotatef(player.angle, 0, 0, 1)

    # Position bucket in front of player
    glTranslatef(0, -40, 25)

    glColor3f(0.4, 0.2, 0.1)

    # Bucket bottom
    glPushMatrix()
    glScalef(BAG_RADIUS / 10, BAG_RADIUS / 10, 2)
    glutSolidCube(10)
    glPopMatrix()

    # Bucket walls
    glColor3f(0.5, 0.3, 0.1)
    for i in range(8):
        angle = i * 45
        glPushMatrix()
        glRotatef(angle, 0, 0, 1)
        glTranslatef(BAG_RADIUS - 3, 0, 8)
        glScalef(1, 3, 1.5)
        glutSolidCube(8)
        glPopMatrix()

    # Bucket handles
    glColor3f(0.3, 0.3, 0.3)
    glPushMatrix()
    glTranslatef(-BAG_RADIUS + 5, 0, 8)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(2, 8, 8, 8)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(BAG_RADIUS - 5, 0, 8)
    glRotatef(90, 0, 1, 0)
    glutSolidTorus(2, 8, 8, 8)
    glPopMatrix()

    glPopMatrix()


def draw_dogs():
    for dog in dogs:
        dog.draw()


def draw_npc():
    glPushMatrix()
    glTranslatef(quest_npc.pos[0], quest_npc.pos[1], 37)
    # Torso
    glColor3f(0.18, 0.58, 0.83)
    glutSolidSphere(15, 10, 10)
    glPushMatrix()
    glTranslatef(0, 0, 14)
    glColor3f(0.96, 0.81, 0.61)
    glutSolidSphere(7, 8, 8)
    glPopMatrix()
    glPopMatrix()


def draw_shop():
    glPushMatrix()
    glTranslatef(shop_npc.pos[0], shop_npc.pos[1], 89)  # Raised so visible above ground
    # Shop building
    light_intensity = get_ambient_light()
    glColor3f(0.7 * light_intensity, 0.4 * light_intensity, 0.2 * light_intensity)
    glScalef(SHOP_SIZE, SHOP_SIZE, 100)
    glutSolidCube(1.0)
    glPopMatrix()

    # Shopkeeper (in front of shop)
    glPushMatrix()
    glTranslatef(shop_npc.pos[0], shop_npc.pos[1], 37)
    glColor3f(0.91, 0.55, 0.12)
    glutSolidCube(18)
    glPushMatrix()
    glTranslatef(0, 0, 12)
    glColor3f(0.91, 0.86, 0.72)
    glutSolidSphere(7, 10, 10)
    glPopMatrix()
    glPopMatrix()


# --- CAMERA SETUP ---
def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, WINDOW_WIDTH / WINDOW_HEIGHT, 1.0, 5000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    global cam_angle, cam_distance, cam_height

    if player.inside_house:
        # Interior camera view house
        gluLookAt(HOUSE_POS[0], HOUSE_POS[1], 100,
                  HOUSE_POS[0], HOUSE_POS[1] - 50, 50,
                  0, 0, 1)
    elif player.inside_shop:
        # Interior camera view shop
        gluLookAt(shop_npc.pos[0], shop_npc.pos[1], 80,
                  shop_npc.pos[0], shop_npc.pos[1], 0,
                  0, 1, 0)
    else:
        # Third-person camera that follows player
        camera_x = player.pos[0] - cam_distance * math.sin(math.radians(cam_angle))
        camera_y = player.pos[1] - cam_distance * math.cos(math.radians(cam_angle))
        gluLookAt(camera_x, camera_y, cam_height,
                  player.pos[0], player.pos[1], 0,
                  0, 0, 1)


def draw_scene():
    r, g, b = get_sky_color()
    glClearColor(r, g, b, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    setup_camera()

    draw_stars()
    # Removed: draw_clouds()
    draw_sun()
    # Removed: draw_moon()

    draw_ground()
    draw_boundary_walls()
    draw_house()
    draw_shop()

    for shelter in shelters:
        draw_shelter(shelter[0], shelter[1])
    for tree in trees:
        draw_tree(tree[0], tree[1])

    if player.inside_shop:
        # Could add interior shop drawing here if desired
        pass
    else:
        draw_player()
        draw_rain()
        draw_snow()

    draw_dogs()
    draw_npc()

    if not player.inside_house and not player.inside_shop:
        for apple in apples:
            draw_apple(apple)

    # Display UI text
    elapsed_time = time.time() - game_start_time
    remaining_time = max(0, game_duration - elapsed_time)
    minutes = int(remaining_time // 60)
    seconds = int(remaining_time % 60)
    time_remaining_str = f"{minutes}:{seconds:02d}"

    if player.won:
        msg = f"YOU WIN! Final Score: {player.score}. Press 'r' to restart."
    elif not player.alive:
        if elapsed_time >= game_duration:
            msg = f"TIME UP! Final Score: {player.score}. Press 'r' to restart."
        else:
            msg = f"GAME OVER! Score: {player.score}. Press 'r' to restart."
    elif player.inside_house:
        msg = f"Inside house! Press 'e' to exit. Score: {player.score} | Health: {player.health} | Time Left: {time_remaining_str}"
    elif player.inside_shop:
        msg = f"Welcome to the shop! Press 'e' to exit. Score: {player.score} | Health: {player.health} | Time Left: {time_remaining_str}"
    else:
        shelter_status = " [Under Shelter]" if player.under_shelter else ""
        rain_status = " [RAINING!]" if rain_system.is_raining else ""
        snow_status = " [SNOWING!]" if snow_active else ""
        msg = f"Catch red/golden apples (+5/+20), avoid black (-10). Score: {player.score} | Health: {player.health} | Time Left: {time_remaining_str}{shelter_status}{rain_status}{snow_status}"

    draw_text(20, WINDOW_HEIGHT - 40, msg)
    draw_text(20, WINDOW_HEIGHT - 70, "[WASD] Move  [Arrows] Rotate  [E] Enter/Leave house/shop  [R] Restart")

    glutSwapBuffers()


# --- GAME LOGIC & UPDATES ---
def check_dog_collisions():
    if not player.alive:
        return
    for dog in dogs:
        dx = player.pos[0] - dog.pos[0]
        dy = player.pos[1] - dog.pos[1]
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < dog.size + 25:  # collision threshold
            player.score += 0.5
            # Push dog away randomly to prevent multiple counts rapidly
            dog.pos[0] += random.choice([-1, 1]) * dog.size * 2
            dog.pos[1] += random.choice([-1, 1]) * dog.size * 2


def check_shelter_protection():
    player.under_shelter = False
    for shelter_x, shelter_y in shelters:
        if (shelter_x - 74 < player.pos[0] < shelter_x + 74 and
                shelter_y - 74 < player.pos[1] < shelter_y + 74):
            player.under_shelter = True
            break


def update_rain():
    global snow_active, snow_next_time
    now = time.time()

    # Don't start rain if it's snowing
    if not rain_system.is_raining and now >= rain_system.next_rain_time and not snow_active:
        rain_system.is_raining = True
        rain_system.rain_start_time = now
        rain_system.next_rain_time = now + RAIN_DURATION + random.randint(RAIN_MIN_INTERVAL, RAIN_MAX_INTERVAL)

    # Stop snow if rain starts
    if rain_system.is_raining and snow_active:
        snow_active = False
        snow_next_time = now + random.randint(SNOW_MIN_INTERVAL, SNOW_MAX_INTERVAL)
        init_snowflakes()

    if rain_system.is_raining and now - rain_system.rain_start_time >= RAIN_DURATION:
        rain_system.is_raining = False
        rain_system.player_in_rain = False
        rain_system.player_rain_exposure_start = 0

    if rain_system.is_raining and not player.inside_house and not player.under_shelter and not player.inside_shop and player.alive:
        if not rain_system.player_in_rain:
            rain_system.player_in_rain = True
            rain_system.player_rain_exposure_start = now
        elif now - rain_system.player_rain_exposure_start >= RAIN_DAMAGE_TIME:
            player.health -= RAIN_DAMAGE
            rain_system.player_rain_exposure_start = now
            if player.health <= 0:
                player.alive = False
    else:
        rain_system.player_in_rain = False
        rain_system.player_rain_exposure_start = 0


def update_apples():
    global last_apple_time
    if not player.alive or player.inside_house or player.inside_shop:
        return

    now = time.time()
    elapsed = now - game_start_time

    # After 5 seconds, spawn apples from all trees every 1 second
    if elapsed > 5:
        if now - last_apple_time > 1.0:
            for tree in trees:
                rand_val = random.random()
                if rand_val < 0.7:
                    apple_type = "red"
                elif rand_val < 0.9:
                    apple_type = "black"
                else:
                    apple_type = "golden"
                apples.append({
                    'type': apple_type,
                    'pos': [tree[0] + random.randint(-40, 40),
                            tree[1] + random.randint(-40, 40),
                            300],
                    'fall_speed': APPLE_FALL_SPEED
                })
            last_apple_time = now
    else:
        if now - last_apple_time > APPLE_FALL_INTERVAL:
            tree = random.choice(trees)
            rand_val = random.random()
            if rand_val < 0.7:
                apple_type = "red"
            elif rand_val < 0.9:
                apple_type = "black"
            else:
                apple_type = "golden"
            apples.append({
                'type': apple_type,
                'pos': [tree[0] + random.randint(-40, 40),
                        tree[1] + random.randint(-40, 40),
                        300],
                'fall_speed': APPLE_FALL_SPEED
            })
            last_apple_time = now

    for apple in apples[:]:
        apple['pos'][2] -= apple['fall_speed']

        bucket_x = player.pos[0] - 40 * math.sin(math.radians(player.angle))
        bucket_y = player.pos[1] - 40 * math.cos(math.radians(player.angle))
        bucket_z = 25

        dx = bucket_x - apple['pos'][0]
        dy = bucket_y - apple['pos'][1]
        dz = bucket_z - apple['pos'][2]
        dist = math.sqrt(dx * dx + dy * dy + dz * dz)

        if dist < BAG_RADIUS + APPLE_RADIUS and 12 <= apple['pos'][2] <= 55:
            if apple['type'] == "red":
                player.score += 5
            elif apple['type'] == "black":
                player.score -= 10
            elif apple['type'] == "golden":
                player.score += 20

            apples.remove(apple)

            if player.score >= 40:
                player.alive = False
                player.won = True

        elif apple['pos'][2] < 5:
            apples.remove(apple)

    # Game over if score too low
    if player.score < -25:
        player.alive = False


def update_player():
    if player.inside_house or not player.alive or player.inside_shop:
        return

    rot_angle = player.angle
    new_x, new_y = player.pos[0], player.pos[1]

    # Full 4-direction movement (WASD)
    if keys.get(b'w', False):
        new_x += PLAYER_SPEED * math.sin(math.radians(rot_angle))
        new_y += PLAYER_SPEED * math.cos(math.radians(rot_angle))
    if keys.get(b's', False):
        new_x -= PLAYER_SPEED * math.sin(math.radians(rot_angle))
        new_y -= PLAYER_SPEED * math.cos(math.radians(rot_angle))
    if keys.get(b'a', False):
        new_x -= PLAYER_SPEED * math.cos(math.radians(rot_angle))
        new_y += PLAYER_SPEED * math.sin(math.radians(rot_angle))
    if keys.get(b'd', False):
        new_x += PLAYER_SPEED * math.cos(math.radians(rot_angle))
        new_y -= PLAYER_SPEED * math.sin(math.radians(rot_angle))

    # Bound check
    new_x = max(-WORLD_SIZE + 35, min(WORLD_SIZE - 35, new_x))
    new_y = max(-WORLD_SIZE + 35, min(WORLD_SIZE - 35, new_y))

    # Simple collision check with house
    house_left = HOUSE_POS[0] - HOUSE_SIZE // 2
    house_right = HOUSE_POS[0] + HOUSE_SIZE // 2
    house_top = HOUSE_POS[1] + HOUSE_SIZE // 2
    house_bottom = HOUSE_POS[1] - HOUSE_SIZE // 2
    if (house_left - 25 < new_x < house_right + 25 and house_bottom - 25 < new_y < house_top + 25):
        door_x = HOUSE_POS[0]
        door_y = HOUSE_POS[1] - HOUSE_SIZE // 2
        if math.sqrt((new_x - door_x) ** 2 + (new_y - door_y) ** 2) > 59:
            return

    # Simple collision check with shop boundaries (to prevent walking through walls)
    shop_left = shop_npc.pos[0] - SHOP_SIZE // 2
    shop_right = shop_npc.pos[0] + SHOP_SIZE // 2
    shop_top = shop_npc.pos[1] + SHOP_SIZE // 2
    shop_bottom = shop_npc.pos[1] - SHOP_SIZE // 2
    if player.inside_shop:
        # Player cannot move outside shop while inside
        if not (shop_left < new_x < shop_right and shop_bottom < new_y < shop_top):
            return
    else:
        # Prevent entering shop walls except near door area - for simplicity we won't do door here, allow free move

        # Just prevent walking inside shop without "entering"
        if (shop_left < new_x < shop_right and shop_bottom < new_y < shop_top):
            # We'll let entering be manual by pressing E near door, so block "walking" in
            return

    player.pos[0], player.pos[1] = new_x, new_y
    check_shelter_protection()


def update_dogs():
    for dog in dogs:
        dog.update()


def check_house_entry():
    if not player.alive:
        return

    # Check distance to door
    door_x = HOUSE_POS[0]
    door_y = HOUSE_POS[1] - HOUSE_SIZE // 2

    dx = player.pos[0] - door_x
    dy = player.pos[1] - door_y
    dist = math.sqrt(dx * dx + dy * dy)

    if not player.inside_house and dist < 80:
        player.inside_house = True
    elif player.inside_house:
        player.inside_house = False
        # Move player outside the door when exiting
        player.pos[0] = door_x
        player.pos[1] = door_y - 80


def check_shop_entry():
    if not player.alive:
        return

    shop_left = shop_npc.pos[0] - SHOP_SIZE // 2
    shop_right = shop_npc.pos[0] + SHOP_SIZE // 2
    shop_top = shop_npc.pos[1] + SHOP_SIZE // 2
    shop_bottom = shop_npc.pos[1] - SHOP_SIZE // 2

    px, py = player.pos[0], player.pos[1]

    dist_x = min(abs(px - shop_left), abs(px - shop_right))
    dist_y = min(abs(py - shop_bottom), abs(py - shop_top))

    # Accept entering when near shop boundary (within 80 units roughly)
    near_shop = (shop_left - 80 < px < shop_right + 80) and (shop_bottom - 80 < py < shop_top + 80)
    inside = (shop_left <= px <= shop_right) and (shop_bottom <= py <= shop_top)

    if not player.inside_shop and near_shop and inside:
        player.inside_shop = True
    elif player.inside_shop and (not inside):
        player.inside_shop = False
        # Move player outside the shop when exiting - just outside on the south side
        player.pos[0] = shop_npc.pos[0]
        player.pos[1] = shop_npc.pos[1] - SHOP_SIZE // 2 - 60


def keyboard_down(key, x, y):
    keys[key] = True

    if key == b'e':
        if player.inside_shop:
            player.inside_shop = False
            # Put player just outside shop
            player.pos[0] = shop_npc.pos[0]
            player.pos[1] = shop_npc.pos[1] - SHOP_SIZE // 2 - 60
        elif player.inside_house:
            player.inside_house = False
            # Move player outside the door when exiting
            player.pos[0] = HOUSE_POS[0]
            player.pos[1] = HOUSE_POS[1] - HOUSE_SIZE // 2 - 80
        else:
            # Try to enter house or shop
            check_house_entry()
            check_shop_entry()

    if key == b'r' and (not player.alive or player.won):
        # Reset game
        global game_start_time
        game_start_time = time.time()
        player.__init__()
        rain_system.__init__()
        apples.clear()
        generate_clouds()
        generate_stars()
        shop_npc.__init__()
        quest_npc.__init__()
        # Reinitialize dogs
        global dogs
        dogs = []
        for _ in range(6):
            dogs.append(Dog(random.randint(-WORLD_SIZE + 200, WORLD_SIZE - 200),
                            random.randint(-WORLD_SIZE + 200, WORLD_SIZE - 200)))
        init_snowflakes()
        glutPostRedisplay()

    glutPostRedisplay()


def keyboard_up(key, x, y):
    keys[key] = False
    glutPostRedisplay()


def special_key_down(key, x, y):
    global cam_angle, cam_height
    if key == GLUT_KEY_LEFT:
        player.angle += TURN_SPEED
    elif key == GLUT_KEY_RIGHT:
        player.angle -= TURN_SPEED
    elif key == GLUT_KEY_UP:
        cam_height = min(cam_height + 35, 610)
    elif key == GLUT_KEY_DOWN:
        cam_height = max(cam_height - 35, 120)
    player.angle %= 360
    glutPostRedisplay()


def update_game(value):
    if player.alive:
        elapsed_time = time.time() - game_start_time
        if elapsed_time >= game_duration:
            player.alive = False

    update_player()
    update_apples()
    update_rain()
    update_snow()
    update_dogs()
    check_dog_collisions()
    glutPostRedisplay()
    glutTimerFunc(16, update_game, 0)


# Initialize snowflakes on startup
init_snowflakes()


# --- MAIN FUNCTION ---
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Apple Catching Game - Enhanced With Snow, Big Dogs and Shop")

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glutDisplayFunc(draw_scene)
    glutKeyboardFunc(keyboard_down)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(special_key_down)
    glutTimerFunc(0, update_game, 0)

    glutMainLoop()


if __name__ == "__main__":
    main()
'''