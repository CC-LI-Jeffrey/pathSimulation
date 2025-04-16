import pygame
import sys
import math
from path import Path
from robot import Robot
from wheelPathGenerator import WheelPathGenerator
from wheel_speed_calculator import WheelSpeedCalculator

# Add this function at the beginning of wheel_speed_demo.py, 
# after imports but before creating the pygame window

def calculate_world_wheel_angles(path_direction, robot_orientation):
    """
    Calculate wheel angles in world coordinates, then adjust for robot orientation.
    
    Args:
        path_direction: Direction of motion in degrees (0 = right, 90 = up)
        robot_orientation: Current orientation of the robot body in degrees
        
    Returns:
        Dictionary of adjusted wheel angles accounting for robot orientation
    """
    # In world coordinates, all wheels point in the path direction
    world_wheel_angle = path_direction
    
    # Adjust for robot orientation (subtract robot orientation)
    # This is because the wheel angles are set relative to the robot body
    adjusted_angle = (world_wheel_angle - robot_orientation) % 360
    
    # Return the same angle for all wheels
    return {
        1: adjusted_angle,  # top-left
        3: adjusted_angle,  # top-right
        5: adjusted_angle,  # bottom-left
        7: adjusted_angle   # bottom-right
    }

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wheel Speed Ratio Visualization")

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
initial_orientation = 0
final_orientation = 90  # Start with 90 degree rotation

# Generate wheel paths
wheel_paths = wheel_path_generator.generate_wheel_paths(path_list, initial_orientation, final_orientation)

# Calculate wheel speeds
speed_calculator = WheelSpeedCalculator(wheel_paths)
wheel_speed_ratios = speed_calculator.calculate_speed_ratios()

# Wheel colors for visualization
wheel_colors = {
    1: RED,     # top-left: red
    3: GREEN,   # top-right: green
    5: BLUE,    # bottom-left: blue
    7: YELLOW   # bottom-right: yellow
}

# Animation variables
animate = False
animation_progress = 0
animation_speed = 0.005
base_speed = 0.5  # Base speed for animation

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
                # Change final orientation
                orientations = [0, 90, 180, 270, 360]
                current_index = orientations.index(final_orientation) if final_orientation in orientations else 0
                final_orientation = orientations[(current_index + 1) % len(orientations)]
                
                # Regenerate wheel paths and recalculate speeds
                wheel_paths = wheel_path_generator.generate_wheel_paths(path_list, initial_orientation, final_orientation)
                speed_calculator = WheelSpeedCalculator(wheel_paths)
                wheel_speed_ratios = speed_calculator.calculate_speed_ratios()
                
                # Reset animation
                animation_progress = 0
                robot.x, robot.y = path_list[0].get_point(0)
                
            elif event.key == pygame.K_SPACE:
                # Toggle animation
                animate = not animate
                if not animate:
                    animation_progress = 0
                    robot.x, robot.y = path_list[0].get_point(0)
                    robot.set_all_wheel_angles(initial_orientation)
                
            elif event.key == pygame.K_p:
                # Print speed ratios to console
                print(speed_calculator.visualize_speeds(20))

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
    
    # Animate the robot
    if animate:
        # Update progress
        animation_progress += animation_speed
        if animation_progress > 1:
            animation_progress = 0
        
        # Calculate robot position
        center_x, center_y = path_list[0].get_point(animation_progress)
        
        # Calculate current robot orientation
        current_orientation = initial_orientation + animation_progress * (final_orientation - initial_orientation)
        
        # Calculate path direction (for the straight line case, it's 0 degrees/right)
        if path_list[0].path_type == 'line':
            dx = path_list[0].end_point[0] - path_list[0].start_point[0]
            dy = path_list[0].end_point[1] - path_list[0].start_point[1]
            path_direction = math.degrees(math.atan2(dy, dx))
        else:
            # For curves, calculate tangent direction at current point
            # For this example, we'll assume a straight line path
            path_direction = 0  
        
        # Calculate wheel angles in world coordinates, adjusted for robot orientation
        wheel_angles = calculate_world_wheel_angles(path_direction, current_orientation)
        
        # Update robot position
        robot.x, robot.y = center_x, center_y
        
        # Update robot body orientation
        # For visualization purposes - in a real robot, the body orientation 
        # would change naturally due to wheel speed differentials
        robot.orientation = current_orientation
        
        # Set the wheel angles to maintain world direction
        for wheel_id, angle in wheel_angles.items():
            robot.set_wheel_angle(wheel_id, angle)
        
        # Get wheel speeds at current progress
        speeds = speed_calculator.get_speed_at_progress(animation_progress, base_speed)
        normalized_speeds = speed_calculator.normalize_speeds(speeds, -1.0, 1.0)
    
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
    
    # Display current wheel speeds during animation
    if animate:
        y_offset = 160
        speed_title = "Current Wheel Speeds:"
        text_surface = font.render(speed_title, True, BLACK)
        screen.blit(text_surface, (20, y_offset))
        y_offset += 25
        
        for wheel_id in sorted(wheel_colors.keys()):
            speed_motor_id = wheel_id + 1
            if speed_motor_id in normalized_speeds:
                speed_text = f"Motor {speed_motor_id}: {normalized_speeds[speed_motor_id]:.2f}"
                text_surface = font.render(speed_text, True, wheel_colors[wheel_id])
                screen.blit(text_surface, (30, y_offset))
                y_offset += 20
    
    # Display instructions
    instructions = [
        f"Initial Orientation: {initial_orientation}°",
        f"Final Orientation: {final_orientation}°",
        f"Base Speed: {base_speed:.2f}",
        "Press SPACE to toggle animation",
        "Press R to change target orientation",
        "Press P to print speed tables"
    ]
    
    y_offset = HEIGHT - 150
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