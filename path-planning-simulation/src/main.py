import pygame
import sys
import robot
import robotController
from path import Path
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("4-Wheel Robot Path Planning Simulation")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
PURPLE = (128, 0, 128)

# Robot dimensions
ROBOT_WIDTH, ROBOT_HEIGHT = 100, 60
WHEEL_WIDTH, WHEEL_HEIGHT = 20, 10

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Window center
CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT // 2

# Path parameters
RADIUS = 200  # Radius of the curve part of the U
STRAIGHT_LENGTH = 200  # Length of straight segments

# Define three parts of the U-shaped path (starting from top left)
# 1. First straight line (top left going down)
line1_start = (CENTER_X - RADIUS, CENTER_Y - STRAIGHT_LENGTH)
line1_end = (CENTER_X - RADIUS, CENTER_Y)

# 2. Curve at the bottom (half circle) - going from left to right
curve_center = (CENTER_X, CENTER_Y)
start_angle = math.pi    # Starting from left (π radians, 180 degrees)
end_angle = 0            # Ending right (0 radians, 0 degrees)

# 3. Second straight line (going back up right)
line2_start = (CENTER_X + RADIUS, CENTER_Y)
line2_end = (CENTER_X + RADIUS, CENTER_Y - STRAIGHT_LENGTH)

# Create path objects with velocities
line1_path = Path('line', start_point=line1_start, end_point=line1_end, velocity=1)  # Slower for first line
curve_path = Path('curve', circle_center=curve_center, radius=RADIUS, 
                start_angle=start_angle, end_angle=end_angle, velocity=1)  # Faster for the curve
line2_path = Path('line', start_point=line2_start, end_point=line2_end, velocity=1)  # Medium speed for last line

# Combine paths in order
path_list = [line1_path, curve_path, line2_path]

# Generate points for visualization
line1_points = line1_path.generate_path(50)
curve_points = curve_path.generate_path(100)
line2_points = line2_path.generate_path(50)

# Combine all path points for drawing
combined_points = line1_points + curve_points + line2_points

# Place robot at the start of the first path (now top left)
robot_x, robot_y = line1_points[0]
robot = robot.Robot(robot_x, robot_y, ROBOT_WIDTH, ROBOT_HEIGHT, WHEEL_WIDTH, WHEEL_HEIGHT, GRAY, BLACK)

# Create robot controller
controller = robotController.RobotController(robot)
controller.set_paths(path_list)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # Start following paths using velocity-based movement
                controller.follow_paths()  
            elif event.key == pygame.K_s:
                # Stop robot movement
                controller.set_all_wheel_speeds(0)

    # Clear screen
    screen.fill(WHITE)

    # Draw the robot at its starting position (not moving)
    robot.draw(screen)

    # Draw control points
    pygame.draw.circle(screen, RED, curve_center, 5)  # Curve center
    pygame.draw.circle(screen, PURPLE, line1_start, 5)  # First line start
    pygame.draw.circle(screen, GREEN, line1_end, 5)  # First line end
    pygame.draw.circle(screen, GREEN, line2_start, 5)  # Second line start
    pygame.draw.circle(screen, PURPLE, line2_end, 5)  # Second line end

    # Draw the combined path
    for i in range(len(combined_points) - 1):
        # Color differently based on path segment
        if i < len(line1_points) - 1:
            color = (100, 100, 255)  # Light blue for first line
        elif i < len(line1_points) + len(curve_points) - 1:
            color = BLUE  # Regular blue for curve
        else:
            color = (100, 255, 100)  # Light green for second line
        pygame.draw.line(screen, color, combined_points[i], combined_points[i + 1], 2)

    # Move robot based on current wheel settings
    controller.move_robot()

    # Update display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

# Quit Pygame
pygame.quit()
sys.exit()