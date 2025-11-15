'''
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time

# ===== Global Variables =====
WINDOW_WIDTH, WINDOW_HEIGHT = 500, 500

# List to store all points [x, y, dx, dy, color, visible]
points = []

# Speed multiplier for all points
speed_multiplier = 0.2

# Blinking state
is_blinking = False
blink_start_time = 0
blink_cycle = 1.0  # 1 second cycle

# Freeze state
is_frozen = False

# Boundary limits
BOUNDARY_LEFT = -240
BOUNDARY_RIGHT = 240
BOUNDARY_TOP = 240
BOUNDARY_BOTTOM = -240

# Point size
POINT_SIZE = 5


# ===== Coordinate Conversion =====
def convert_coordinate(x, y):
    """Convert mouse coordinates to OpenGL coordinates"""
    a = x - (WINDOW_WIDTH / 2)
    b = (WINDOW_HEIGHT / 2) - y
    return a, b


# ===== Draw Functions =====
def draw_point(x, y, size):
    """Draw a single point"""
    glPointSize(size)
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()


def draw_boundary():
    """Draw the boundary box"""
    glColor3f(1.0, 1.0, 1.0)  # White boundary
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    glVertex2f(BOUNDARY_LEFT, BOUNDARY_BOTTOM)
    glVertex2f(BOUNDARY_RIGHT, BOUNDARY_BOTTOM)
    glVertex2f(BOUNDARY_RIGHT, BOUNDARY_TOP)
    glVertex2f(BOUNDARY_LEFT, BOUNDARY_TOP)
    glEnd()


def draw_all_points():
    """Draw all the points"""
    global is_blinking, blink_start_time
    
    current_time = time.time()
    
    for point in points:
        x, y, dx, dy, color, visible = point
        
        if is_blinking:
            # Calculate blink phase (0 to 1 within the cycle)
            elapsed = (current_time - blink_start_time) % blink_cycle
            phase = elapsed / blink_cycle
            
            # Blink: visible for first half, invisible for second half
            if phase < 0.5:
                glColor3f(color[0], color[1], color[2])
            else:
                glColor3f(0.0, 0.0, 0.0)  # Background color (black)
        else:
            glColor3f(color[0], color[1], color[2])
        
        draw_point(x, y, POINT_SIZE)


# ===== Keyboard & Mouse Interaction =====
def keyboard_listener(key, x, y):
    """Handle regular keyboard input"""
    global is_frozen
    
    if key == b' ':  # Spacebar
        is_frozen = not is_frozen
        if is_frozen:
            print("FROZEN - All movements stopped")
        else:
            print("UNFROZEN - Movements resumed")
    elif key == b'\x1b':  # ESC key
        print("Exiting...")
        glutLeaveMainLoop()
    
    glutPostRedisplay()


def special_key_listener(key, x, y):
    """Handle special keys (arrow keys)"""
    global speed_multiplier, is_frozen
    
    if is_frozen:
        return  # Don't change speed when frozen
    
    if key == GLUT_KEY_UP:
        speed_multiplier += 0.5
        print(f"Speed increased: {speed_multiplier:.1f}x")
    elif key == GLUT_KEY_DOWN:
        speed_multiplier = max(0.5, speed_multiplier - 0.5)
        print(f"Speed decreased: {speed_multiplier:.1f}x")
    
    glutPostRedisplay()


def mouse_listener(button, state, x, y):
    """Handle mouse input"""
    global points, is_blinking, blink_start_time, is_frozen
    
    if is_frozen:
        return  # Don't respond to mouse when frozen
    
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        # Convert mouse coordinates to OpenGL coordinates
        ox, oy = convert_coordinate(x, y)
        
        # Only spawn if within boundary
        if BOUNDARY_LEFT < ox < BOUNDARY_RIGHT and BOUNDARY_BOTTOM < oy < BOUNDARY_TOP:
            # Random diagonal direction
            directions = [(-1, 1), (-1, -1), (1, 1), (1, -1)]
            dx, dy = random.choice(directions)
            
            # Scale the direction for base speed
            base_speed = 2.0
            dx *= base_speed
            dy *= base_speed
            
            # Random color (avoid black and very dark colors)
            color = (
                random.uniform(0.3, 1.0),
                random.uniform(0.3, 1.0),
                random.uniform(0.3, 1.0)
            )
            
            # Add point [x, y, dx, dy, color, visible]
            points.append([ox, oy, dx, dy, color, True])
            print(f"Point spawned at ({ox:.1f}, {oy:.1f}) - Total points: {len(points)}")
    
    elif button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Toggle blinking
        is_blinking = not is_blinking
        if is_blinking:
            blink_start_time = time.time()
            print("Blinking enabled")
        else:
            print("Blinking disabled")
    
    glutPostRedisplay()


# ===== Projection Setup =====
def setup_projection():
    """Set up the orthographic projection"""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-250, 250, -250, 250)
    glMatrixMode(GL_MODELVIEW)


# ===== Display & Animation =====
def display():
    """Main display function"""
    # Clear screen with black background
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Draw boundary box
    draw_boundary()
    
    # Draw all points
    draw_all_points()
    
    glutSwapBuffers()


def animate():
    """Animation function for continuous updates"""
    global points, is_frozen
    
    if is_frozen:
        glutPostRedisplay()
        return  # Don't animate when frozen
    
    # Update each point's position
    for point in points:
        # Move the point
        point[0] += point[2] * speed_multiplier * 0.1  # x += dx
        point[1] += point[3] * speed_multiplier * 0.1  # y += dy
        
        # Bounce from left or right wall
        if point[0] <= BOUNDARY_LEFT or point[0] >= BOUNDARY_RIGHT:
            point[2] = -point[2]  # Reverse horizontal direction
            # Keep within bounds
            point[0] = max(BOUNDARY_LEFT, min(BOUNDARY_RIGHT, point[0]))
        
        # Bounce from top or bottom wall
        if point[1] <= BOUNDARY_BOTTOM or point[1] >= BOUNDARY_TOP:
            point[3] = -point[3]  # Reverse vertical direction
            # Keep within bounds
            point[1] = max(BOUNDARY_BOTTOM, min(BOUNDARY_TOP, point[1]))
    
    glutPostRedisplay()


# ===== Main Function =====
def main():
    """Initialize and run the OpenGL program"""
    glutInit()
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Amazing Box - Interactive Points")
    
    # Set up projection
    setup_projection()
    
    # Register callback functions
    glutDisplayFunc(display)
    glutIdleFunc(animate)
    glutKeyboardFunc(keyboard_listener)
    glutSpecialFunc(special_key_listener)
    glutMouseFunc(mouse_listener)
    
    # Print instructions
    print("=" * 50)
    print("AMAZING BOX - CONTROLS")
    print("=" * 50)
    print("RIGHT CLICK    : Spawn a random colored point")
    print("LEFT CLICK     : Toggle blinking effect")
    print("UP ARROW       : Increase speed of all points")
    print("DOWN ARROW     : Decrease speed of all points")
    print("SPACEBAR       : Freeze/Unfreeze all points")
    print("ESC            : Exit")
    print("=" * 50)
    print("\nSpawn points by right-clicking inside the box!")
    
    # Start main loop
    glutMainLoop()


# ===== Entry Point =====
if __name__ == "__main__":
    main()
'''