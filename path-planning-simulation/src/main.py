import pygame
import sys
import robot
import robotController
from path import Path
import math
import random

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


def generate_u_shaped_path(center_x, center_y, radius=200, straight_length=200, velocity=1.0):
    """
    Generate a U-shaped path with three segments: line down, curve, line up.
    Starting from top right going counter-clockwise.
    
    Args:
        center_x: Center X coordinate for the path
        center_y: Center Y coordinate for the path
        radius: Radius of the curve part
        straight_length: Length of straight segments
        velocity: Speed for all path segments
    
    Returns:
        Tuple of (path_list, path_points, segment_points, control_points, curve_center)
    """
    # Define three parts of the U-shaped path (starting from top right)
    # 1. First straight line (top right going down)
    line1_start = (center_x + radius, center_y - straight_length)
    line1_end = (center_x + radius, center_y)

    # 2. Curve at the bottom (half circle) - going from right to left
    curve_center = (center_x, center_y)
    start_angle = 0         # Starting from right (0 radians, 0 degrees)
    end_angle = math.pi     # Ending left (π radians, 180 degrees)

    # 3. Second straight line (going back up left)
    line2_start = (center_x - radius, center_y)
    line2_end = (center_x - radius, center_y - straight_length)

    # Create path objects with velocities
    line1_path = Path('line', start_point=line1_start, end_point=line1_end, velocity=velocity)
    curve_path = Path('curve', circle_center=curve_center, radius=radius, 
                      start_angle=start_angle, end_angle=end_angle, velocity=velocity)
    line2_path = Path('line', start_point=line2_start, end_point=line2_end, velocity=velocity)

    # Combine paths in order
    path_list = [line1_path, curve_path, line2_path]

    # Generate points for visualization
    line1_points = line1_path.generate_path(50)
    curve_points = curve_path.generate_path(100)
    line2_points = line2_path.generate_path(50)

    # Combine all path points for drawing
    path_points = line1_points + curve_points + line2_points
    segment_points = [line1_points, curve_points, line2_points]
    
    # Store control points for visualization
    control_points = [line1_start, line1_end, line2_start, line2_end]
    
    return path_list, path_points, segment_points, control_points, curve_center


def generate_random_path(num_segments=5, margin=100, min_velocity=0.3, max_velocity=1.0):
    """
    Generate a random path with specified number of segments that are properly connected.
    
    Args:
        num_segments: Number of path segments to create
        margin: Margin from screen edges
        min_velocity: Minimum velocity for path segments
        max_velocity: Maximum velocity for path segments
    
    Returns:
        Tuple of (path_list, control_points, segment_points)
    """
    path_list = []
    segment_points = []
    
    # Generate first control point
    start_x = random.randint(margin, WIDTH - margin)
    start_y = random.randint(margin, HEIGHT - margin)
    current_point = (start_x, start_y)
    
    # List to store all control points (including intermediate ones for visualization)
    control_points = [current_point]
    
    for i in range(num_segments):
        # Randomly choose between line and curve
        if random.random() < 0.6:  # 60% chance for line
            # Generate end point for this line segment
            end_x = random.randint(margin, WIDTH - margin)
            end_y = random.randint(margin, HEIGHT - margin)
            end_point = (end_x, end_y)
            
            # Create line segment
            velocity = random.uniform(min_velocity, max_velocity)
            line_path = Path('line', start_point=current_point, end_point=end_point, 
                           velocity=velocity)
            path_list.append(line_path)
            
            # Generate points for visualization
            line_points = line_path.generate_path(50)
            segment_points.append(line_points)
            
            # Update current point for next segment
            current_point = end_point
            control_points.append(current_point)
            
        else:  # 40% chance for curve
            # Generate end point for this curve segment
            end_x = random.randint(margin, WIDTH - margin)
            end_y = random.randint(margin, HEIGHT - margin)
            end_point = (end_x, end_y)
            
            # Calculate a reasonable center point for the curve that connects current_point to end_point
            # First find the midpoint between current and end
            mid_x = (current_point[0] + end_point[0]) / 2
            mid_y = (current_point[1] + end_point[1]) / 2
            
            # Add some perpendicular offset from the midpoint to create a curved path
            # Calculate the direction vector from current to end
            dx = end_point[0] - current_point[0]
            dy = end_point[1] - current_point[1]
            
            # Calculate perpendicular direction (rotate 90 degrees)
            perpendicular_x = -dy
            perpendicular_y = dx
            
            # Normalize and scale
            length = math.sqrt(perpendicular_x**2 + perpendicular_y**2)
            if length > 0:
                perpendicular_x /= length
                perpendicular_y /= length
            
            # Apply random offset in perpendicular direction
            offset = random.randint(50, 150) * (1 if random.random() < 0.5 else -1)
            center_x = mid_x + perpendicular_x * offset
            center_y = mid_y + perpendicular_y * offset
            
            # Calculate radius based on distances
            radius = math.sqrt((center_x - current_point[0])**2 + (center_y - current_point[1])**2)
            
            # Calculate angles from center to start and end points
            start_angle = math.atan2(current_point[1] - center_y, current_point[0] - center_x)
            end_angle = math.atan2(end_point[1] - center_y, end_point[0] - center_x)
            
            # Create curve segment
            velocity = random.uniform(min_velocity, max_velocity)
            curve_path = Path('curve', circle_center=(center_x, center_y), radius=radius,
                             start_angle=start_angle, end_angle=end_angle, 
                             velocity=velocity)
            path_list.append(curve_path)
            
            # Generate points for visualization
            curve_points = curve_path.generate_path(50)
            segment_points.append(curve_points)
            
            # Add the circle center to control points for visualization
            control_points.append((center_x, center_y))
            
            # Update current point for next segment
            current_point = end_point
            control_points.append(current_point)
    
    return path_list, control_points, segment_points


def draw_path(screen, path_points, segment_points, control_points=None, curve_center=None):
    """
    Draw a path with its control points.
    
    Args:
        screen: Pygame screen to draw on
        path_points: List of all points on the path
        segment_points: List of points for each segment
        control_points: List of control points to draw
        curve_center: Center point of curve for U-shaped path
    """
    # Draw control points if provided
    if control_points:
        for point in control_points:
            pygame.draw.circle(screen, PURPLE, point, 5)
    
    # Draw curve center if provided (for U-shaped path)
    if curve_center:
        pygame.draw.circle(screen, RED, curve_center, 5)
        
    # Draw the path with different colors for each segment
    colors = [(100, 100, 255), (50, 150, 255), (0, 200, 150), 
              (100, 255, 100), (150, 255, 50), (200, 200, 0)]
    
    # If we have concatenated points, draw them segment by segment
    point_index = 0
    for i, segment in enumerate(segment_points):
        color = colors[i % len(colors)]
        
        # Draw each segment
        for j in range(len(segment) - 1):
            pygame.draw.line(screen, color, segment[j], segment[j + 1], 2)


# Create U-shaped path with all components
path_list, combined_points, segment_points, control_points_u, curve_center = generate_u_shaped_path(CENTER_X, CENTER_Y)

# Place robot at the start of the first path
robot_x, robot_y = combined_points[0]
robot = robot.Robot(robot_x, robot_y, ROBOT_WIDTH, ROBOT_HEIGHT, WHEEL_WIDTH, WHEEL_HEIGHT, GRAY, BLACK)

# Create robot controller
controller = robotController.RobotController(robot)
controller.set_paths(path_list)

# Path mode (0 = U-shaped, 1 = random)
path_mode = 0

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
            elif event.key == pygame.K_r:
                # Generate a new random path
                path_list, control_points, segment_points = generate_random_path(5)
                combined_points = [point for segment in segment_points for point in segment]
                
                # Reset robot to start of new path
                robot.x, robot.y = combined_points[0]
                controller.set_paths(path_list)
                controller.set_all_wheel_speeds(0)
                controller.moving = False
                path_mode = 1
            elif event.key == pygame.K_u:
                # Switch back to U-shaped path
                path_list, combined_points, segment_points, control_points_u, curve_center = generate_u_shaped_path(CENTER_X, CENTER_Y)
                
                # Reset robot to start of path
                robot.x, robot.y = combined_points[0]
                controller.set_paths(path_list)
                controller.set_all_wheel_speeds(0)
                controller.moving = False
                path_mode = 0

    # Clear screen
    screen.fill(WHITE)

    # Draw the robot
    robot.draw(screen)

    # Draw the path and control points
    if path_mode == 0:
        # Draw U-shaped path
        draw_path(screen, combined_points, segment_points, 
                 control_points=control_points_u, 
                 curve_center=curve_center)
    else:
        # Draw random path
        draw_path(screen, combined_points, segment_points, control_points=control_points)

    # Move robot based on current wheel settings
    controller.move_robot()

    # Update display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

# Quit Pygame
pygame.quit()
sys.exit()