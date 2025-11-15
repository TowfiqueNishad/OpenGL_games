from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import sys
import time

WINDOW_WIDTH, WINDOW_HEIGHT = 700, 600
NUM_DROPS = 250

raindrops = []
wind = 0.0              
wind_target = 0.0        
WIND_STEP = 0.005
WIND_LERP = 0.02

brightness = 0.25
brightness_target = brightness
BRIGHTNESS_STEP = 0.02
BRIGHTNESS_LERP = 0.03

new_point = False
point_x, point_y = 0.0, 0.0

tree_positions = [-0.8, -0.4, 0.3, 0.7]
tree_scale = 0.4

last_time = time.time()

# ===== Coordinate Conversion =====
def convert_coordinate(x, y):
    ndc_x = (2.0 * x / WINDOW_WIDTH) - 1.0
    ndc_y = 1.0 - (2.0 * y / WINDOW_HEIGHT)
    return ndc_x, ndc_y

# ===== Raindrop Setup =====
def drop_1():
    x = random.uniform(-1.1, 1.1)
    y = random.uniform(1.05, 1.6)
    speed = random.uniform(0.008, 0.020)
    length = random.uniform(0.02, 0.06)
    return {"x": x, "y": y, "speed": speed, "length": length}

def drop_initiate():
    raindrops.clear()
    for _ in range(NUM_DROPS):
        d = drop_1()
        d["y"] = random.uniform(-1.0, 1.6)
        raindrops.append(d)

# ===== Draw Functions =====
def draw_background():
    day_color = (0.7, 0.9, 1.0)
    night_color = (0.02, 0.04, 0.12)
    r = night_color[0] * (1 - brightness) + day_color[0] * brightness
    g = night_color[1] * (1 - brightness) + day_color[1] * brightness
    b = night_color[2] * (1 - brightness) + day_color[2] * brightness

    glBegin(GL_TRIANGLES)
    glColor3f(r, g, b)
    glVertex2f(-1.0, -1.0)
    glVertex2f(1.0, -1.0)
    glVertex2f(1.0, 1.0)
    glVertex2f(-1.0, -1.0)
    glVertex2f(1.0, 1.0)
    glVertex2f(-1.0, 1.0)
    glEnd()

def draw_field():
    day_field = (0.2, 0.8, 0.3)
    night_field = (0.03, 0.12, 0.05)
    field_col = tuple(night_field[i] * (1 - brightness) + day_field[i] * brightness for i in range(3))
    y_bot, y_top = -1.0, -0.2
    glBegin(GL_TRIANGLES)
    glColor3f(*field_col)
    glVertex2f(-1.0, y_bot)
    glVertex2f(1.0, y_bot)
    glVertex2f(1.0, y_top)
    glVertex2f(-1.0, y_bot)
    glVertex2f(1.0, y_top)
    glVertex2f(-1.0, y_top)
    glEnd()

def draw_tree(x, base_y, scale):
    trunk_day = (0.4, 0.25, 0.15)
    trunk_night = (0.1, 0.07, 0.04)
    trunk_col = tuple(trunk_night[i] * (1 - brightness) + trunk_day[i] * brightness for i in range(3))
    trunk_w = 0.05 * scale
    trunk_h = 0.15 * scale
    tx1, ty1 = x - trunk_w/2.0, base_y
    tx2, ty2 = x + trunk_w/2.0, base_y
    tx3, ty3 = x + trunk_w/2.0, base_y + trunk_h
    tx4, ty4 = x - trunk_w/2.0, base_y + trunk_h

    glBegin(GL_TRIANGLES)
    glColor3f(*trunk_col)
    glVertex2f(tx1, ty1)
    glVertex2f(tx2, ty2)
    glVertex2f(tx3, ty3)
    glVertex2f(tx1, ty1)
    glVertex2f(tx3, ty3)
    glVertex2f(tx4, ty4)
    glEnd()

    foliage_day = (0.1, 0.6, 0.2)
    foliage_night = (0.04, 0.18, 0.08)
    fol_col = tuple(foliage_night[i] * (1 - brightness) + foliage_day[i] * brightness for i in range(3))
    fx1, fy1 = x, base_y + trunk_h + (0.1 * scale)
    fx2, fy2 = x - (0.12 * scale), base_y + trunk_h
    fx3, fy3 = x + (0.12 * scale), base_y + trunk_h

    glBegin(GL_TRIANGLES)
    glColor3f(*fol_col)
    glVertex2f(fx1, fy1)
    glVertex2f(fx2, fy2)
    glVertex2f(fx3, fy3)
    glEnd()

def home():
    wall_day = (0.9, 0.8, 0.7)
    wall_night = (0.35, 0.28, 0.22)
    wall = tuple(wall_night[i] * (1 - brightness) + wall_day[i] * brightness for i in range(3))

    roof_day = (0.6, 0.1, 0.05)
    roof_night = (0.15, 0.04, 0.03)
    roof = tuple(roof_night[i] * (1 - brightness) + roof_day[i] * brightness for i in range(3))

    door_day = (0.35, 0.22, 0.15)
    door_night = (0.07, 0.04, 0.02)
    door = tuple(door_night[i] * (1 - brightness) + door_day[i] * brightness for i in range(3))

    cx, cy = 0.0, -0.2
    w, h = 0.6, 0.45
    x1, y1 = cx - w/2.0, cy - h/2.0
    x2, y2 = cx + w/2.0, cy - h/2.0
    x3, y3 = cx + w/2.0, cy + h/2.0
    x4, y4 = cx - w/2.0, cy + h/2.0

    glBegin(GL_TRIANGLES)
    glColor3f(*wall)
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glVertex2f(x3, y3)
    glVertex2f(x1, y1)
    glVertex2f(x3, y3)
    glVertex2f(x4, y4)
    glEnd()

    roof_h = 0.25
    rx1, ry1 = cx - w*0.6, cy + h/2.0
    rx2, ry2 = cx + w*0.6, cy + h/2.0
    rx3, ry3 = cx, cy + h/2.0 + roof_h
    glBegin(GL_TRIANGLES)
    glColor3f(*roof)
    glVertex2f(rx1, ry1)
    glVertex2f(rx2, ry2)
    glVertex2f(rx3, ry3)
    glEnd()

    door_w, door_h = 0.13, 0.22
    dx1, dy1 = cx - door_w/2.0, cy - h/2.0
    dx2, dy2 = cx + door_w/2.0, cy - h/2.0
    dx3, dy3 = cx + door_w/2.0, cy - h/2.0 + door_h
    dx4, dy4 = cx - door_w/2.0, cy - h/2.0 + door_h
    glBegin(GL_TRIANGLES)
    glColor3f(*door)
    glVertex2f(dx1, dy1)
    glVertex2f(dx2, dy2)
    glVertex2f(dx3, dy3)
    glVertex2f(dx1, dy1)
    glVertex2f(dx3, dy3)
    glVertex2f(dx4, dy4)
    glEnd()

    # windows
    win_w, win_h = 0.12, 0.10
    wx_offsets = [-0.20, 0.20]
    window_day = (0.93, 0.98, 1.0)
    window_night = (0.05, 0.08, 0.12)
    window_col = tuple(window_night[i] * (1 - brightness) + window_day[i] * brightness for i in range(3))
    for xo in wx_offsets:
        wx1, wy1 = cx + xo - win_w/2.0, cy + 0.02
        wx2, wy2 = cx + xo + win_w/2.0, cy + 0.02
        wx3, wy3 = cx + xo + win_w/2.0, cy + 0.02 + win_h
        wx4, wy4 = cx + xo - win_w/2.0, cy + 0.02 + win_h
        glBegin(GL_TRIANGLES)
        glColor3f(*window_col)
        glVertex2f(wx1, wy1)
        glVertex2f(wx2, wy2)
        glVertex2f(wx3, wy3)
        glVertex2f(wx1, wy1)
        glVertex2f(wx3, wy3)
        glVertex2f(wx4, wy4)
        glEnd()

def draw_raindrops():
    rain_day = (0.45, 0.65, 0.9)
    rain_night = (0.9, 0.95, 1.0)
    rain_col = tuple(rain_night[i] * (1 - brightness) + rain_day[i] * brightness for i in range(3))

    glLineWidth(1.5)
    glBegin(GL_LINES)
    glColor3f(*rain_col)
    for d in raindrops:
        x = d["x"]
        y = d["y"]
        length = d["length"]
        dx = wind * 4.0 * length
        glVertex2f(x, y)
        glVertex2f(x + dx, y - length)
    glEnd()

# ===== Keyboard & Mouse =====
def keyboard_listener(key, x, y):
    global brightness_target, new_point
    k = key.decode('utf-8') if isinstance(key, bytes) else key
    if k == '\x1b':
        sys.exit(0)
    if k.lower() == 'd':
        brightness_target = min(1.0, brightness_target + BRIGHTNESS_STEP*5)
    elif k.lower() == 'n':
        brightness_target = max(0.0, brightness_target - BRIGHTNESS_STEP*5)

def special_key_listener(key, x, y):
    global wind_target
    if key == GLUT_KEY_LEFT:
        wind_target -= WIND_STEP * 2
        wind_target = max(-0.25, wind_target)
    elif key == GLUT_KEY_RIGHT:
        wind_target += WIND_STEP * 2
        wind_target = min(0.25, wind_target)
    elif key == GLUT_KEY_UP:
        wind_target = 0.0

def mouse_listener(button, state, x, y):
    global new_point, point_x, point_y
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        new_point = True
        point_x, point_y = convert_coordinate(x, y)

# ===== Display & Animation =====
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    draw_background()
    draw_field()
    for x in tree_positions:
        draw_tree(x, base_y=-0.2, scale=tree_scale)
    home()
    draw_raindrops()
    if new_point:
        glPointSize(6.0)
        glBegin(GL_POINTS)
        glColor3f(1.0, 0.6, 0.2)
        glVertex2f(point_x, point_y)
        glEnd()
    glutSwapBuffers()

def update_wind(dt):
    global wind, brightness
    wind += (wind_target - wind) * WIND_LERP
    brightness += (brightness_target - brightness) * BRIGHTNESS_LERP
    brightness = max(0.0, min(1.0, brightness))
    for d in raindrops:
        d["y"] -= d["speed"] * (60.0 * dt)
        d["x"] += wind * (0.6 + (d["length"] * 5.0)) * (60.0 * dt)
        if d["y"] < -1.2 or d["x"] < -1.6 or d["x"] > 1.6:
            nd = drop_1()
            d.update(nd)

def animate():
    global last_time
    now = time.time()
    dt = now - last_time
    last_time = now
    update_wind(dt)
    glutPostRedisplay()
    glutTimerFunc(16, lambda t: animate(), 0)

# ===== Setup & Main =====
def setup_projection():
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-1, 1, -1, 1, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(200, 100)
    glutCreateWindow(b"House in Rainfall - Trees & Field")

    drop_initiate()
    setup_projection()
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_POINT_SMOOTH)
    glEnable(GL_LINE_SMOOTH)

    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard_listener)
    glutSpecialFunc(special_key_listener)
    glutMouseFunc(mouse_listener)

    glutTimerFunc(16, lambda t=0: animate(), 0)
    print("Controls:")
    print("  Left/Right arrows - Bend rain")
    print("  Up arrow          - Straighten rain")
    print("  D / N             - Day/Night transition")
    print("  Right click       - Place a decorative point")
    print("  Esc               - Exit")
    glutMainLoop()

if __name__ == "__main__":
    main()