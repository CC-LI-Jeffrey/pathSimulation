import pygame
import sys
import math
from path import Path
from robot import Robot
from wheelPathGenerator import WheelPathGenerator

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wheel Path Visualization")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 100, 100)
GREEN = (100, 255, 100)
BLUE = (100, 100, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# Robot dimensions
ROBOT_SLANT = 80
ROBOT_WIDTH, ROBOT_HEIGHT = math.sqrt(pow(ROBOT_SLANT, 2)), math.sqrt(pow(ROBOT_SLANT, 2))
WHEEL_WIDTH, WHEEL_HEIGHT = 15, 8

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Create a simple straight line path from left to right
def create_straight_line_path():
    start_point = (100, HEIGHT // 2)
    end_point = (WIDTH - 100, HEIGHT // 2)
    path = Path('line', start_point=start_point, end_point=end_point, velocity=0.5)
    return [path]  # Return as a list for consistency

# Create a robot
robot = Robot(100, HEIGHT // 2, ROBOT_WIDTH, ROBOT_HEIGHT, WHEEL_WIDTH, WHEEL_HEIGHT, GRAY, BLACK)

# Create a wheel path generator
wheel_path_generator = WheelPathGenerator(ROBOT_WIDTH, ROBOT_HEIGHT)

# Generate straight line path
path_list = create_straight_line_path()

# Initial settings
orientation = 0  # Default orientation

# Generate wheel paths
wheel_paths = wheel_path_generator.generate_wheel_paths(path_list, 0, orientation)

# Wheel colors for visualization
wheel_colors = {
    1: RED,     # top-left: red
    3: GREEN,   # top-right: green
    5: BLUE,    # bottom-left: blue
    7: YELLOW   # bottom-right: yellow
}

# Font for displaying info
font = pygame.font.SysFont(None, 24)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # Change orientation
                orientation = (orientation + 90) % 360
                
                # Regenerate wheel paths
                wheel_paths = wheel_path_generator.generate_wheel_paths(path_list, 0, orientation)
                
            elif event.key == pygame.K_c:
                # Toggle center position (start/end)
                if robot.x == path_list[0].start_point[0]:
                    robot.x, robot.y = path_list[0].end_point
                else:
                    robot.x, robot.y = path_list[0].start_point

    # Clear screen
    screen.fill(WHITE)
    
    # Draw path
    start_x, start_y = path_list[0].start_point
    end_x, end_y = path_list[0].end_point
    pygame.draw.line(screen, BLACK, (start_x, start_y), (end_x, end_y), 3)
    
    # Draw center point markers at start and end
    pygame.draw.circle(screen, PURPLE, (start_x, start_y), 5)
    pygame.draw.circle(screen, PURPLE, (end_x, end_y), 5)
    
    # Draw wheel paths
    wheel_path_generator.draw_wheel_paths(screen, wheel_paths, wheel_colors)
    
    # Draw the robot
    robot.draw(screen)
    
    # Draw legend for wheel paths
    y_offset = 20
    for wheel_id, color in wheel_colors.items():
        wheel_label = f"Wheel {wheel_id}"
        text_surface = font.render(wheel_label, True, BLACK)
        pygame.draw.rect(screen, color, (20, y_offset, 20, 20))
        screen.blit(text_surface, (50, y_offset + 5))
        y_offset += 30
    
    # Display instructions
    instructions = [
        f"Target Orientation: {orientation}°",
        "Press R to change orientation",
        "Press C to toggle robot position"
    ]
    
    y_offset = HEIGHT - 80
    for instruction in instructions:
        text_surface = font.render(instruction, True, BLACK)
        screen.blit(text_surface, (20, y_offset))
        y_offset += 20
    
    # Update display
    pygame.display.flip()
    
    # Cap the frame rate
    clock.tick(60)

# Quit Pygame
pygame.quit()
sys.exit()