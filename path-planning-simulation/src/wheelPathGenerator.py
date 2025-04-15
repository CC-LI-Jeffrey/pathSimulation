import math
from path import Path

class WheelPathGenerator:
    """
    Generates paths for each wheel based on the robot's center path and orientation.
    """
    
    def __init__(self, robot_width, robot_height):
        """
        Initialize the wheel path generator.
        
        Args:
            robot_width: Width of the robot (distance between wheels)
            robot_height: Height of the robot (distance between wheels)
        """
        self.robot_width = robot_width
        self.robot_height = robot_height
        
        # Wheel positions relative to center (top-left, top-right, bottom-left, bottom-right)
        self.wheel_offsets = {
            1: (-robot_width/2, -robot_height/2),  # top-left
            3: (robot_width/2, -robot_height/2),   # top-right
            5: (-robot_width/2, robot_height/2),   # bottom-left
            7: (robot_width/2, robot_height/2)     # bottom-right
        }
    
    def generate_wheel_paths(self, center_path_list, initial_orientation, final_orientation):
        """
        Generate paths for each wheel based on the robot's center path.
        
        Args:
            center_path_list: List of Path objects for the robot's center
            initial_orientation: Initial orientation of the robot in degrees
            final_orientation: Final orientation of the robot in degrees
            
        Returns:
            Dictionary mapping wheel IDs to lists of path points
        """
        wheel_paths = {}
        total_segments = len(center_path_list)
        
        # For each wheel
        for wheel_id, offset in self.wheel_offsets.items():
            wheel_paths[wheel_id] = []
            
            # For each path segment
            for i, center_path in enumerate(center_path_list):
                # Calculate orientation at this segment
                segment_progress = i / total_segments
                current_orientation = initial_orientation + segment_progress * (final_orientation - initial_orientation)
                next_orientation = initial_orientation + (i+1) / total_segments * (final_orientation - initial_orientation)
                
                # Generate path points for this wheel segment
                wheel_segment_points = self._generate_wheel_segment(
                    center_path, 
                    offset,
                    current_orientation,
                    next_orientation
                )
                
                wheel_paths[wheel_id].extend(wheel_segment_points)
        
        return wheel_paths
    
    def _generate_wheel_segment(self, center_path, wheel_offset, start_orientation, end_orientation):
        """
        Generate points for a wheel along a single center path segment.
        
        Args:
            center_path: Path object for the robot's center
            wheel_offset: (x, y) offset of the wheel from center
            start_orientation: Orientation at the start of the segment in degrees
            end_orientation: Orientation at the end of the segment in degrees
            
        Returns:
            List of (x, y) points for the wheel's path
        """
        # Generate a reasonable number of points
        num_points = 100
        points = []
        
        for i in range(num_points):
            t = i / (num_points - 1)
            
            # Get center point at this position
            center_x, center_y = center_path.get_point(t)
            
            # Interpolate orientation
            current_orientation = start_orientation + t * (end_orientation - start_orientation)
            angle_rad = math.radians(current_orientation)
            
            # Calculate rotated wheel offset at this orientation
            rotated_x = wheel_offset[0] * math.cos(angle_rad) - wheel_offset[1] * math.sin(angle_rad)
            rotated_y = wheel_offset[0] * math.sin(angle_rad) + wheel_offset[1] * math.cos(angle_rad)
            
            # Calculate wheel position
            wheel_x = center_x + rotated_x
            wheel_y = center_y + rotated_y
            
            points.append((wheel_x, wheel_y))
        
        return points
    
    def draw_wheel_paths(self, screen, wheel_paths, colors):
        """
        Draw the wheel paths on the screen.
        
        Args:
            screen: Pygame screen to draw on
            wheel_paths: Dictionary mapping wheel IDs to lists of path points
            colors: Dictionary mapping wheel IDs to colors
        """
        import pygame
        
        for wheel_id, points in wheel_paths.items():
            color = colors.get(wheel_id, (255, 255, 255))
            
            for i in range(len(points) - 1):
                pygame.draw.circle(
                    screen, 
                    color, 
                    points[i], 
                    1
                )