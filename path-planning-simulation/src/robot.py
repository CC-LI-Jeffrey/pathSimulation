import pygame
import math

class Robot:
    def __init__(self, x, y, width, height, wheel_width, wheel_height, body_color, wheel_color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.wheel_width = wheel_width
        self.wheel_height = wheel_height
        self.body_color = body_color
        self.wheel_color = wheel_color
        self.orientation = 0  # Add this line to track robot body orientation
        # Initialize wheels to face up (90 degrees)
        self.wheel_angles = {1: 270, 3: 270, 5: 270, 7: 270}

    def draw(self, screen):
        # Calculate corner positions based on orientation
        corners = self._get_rotated_corners()
        
        # Draw robot body
        pygame.draw.polygon(screen, self.body_color, corners)
        
        # Draw colored triangles at the center of each side to identify orientation
        triangle_size = 15
        
        # Define colors for each side
        side_colors = {
            "top": (255, 100, 100),     # Red for top
            "right": (100, 255, 100),   # Green for right
            "bottom": (100, 100, 255),  # Blue for bottom
            "left": (255, 255, 0)       # Yellow for left
        }
        
        # Calculate midpoints of each side based on rotated corners
        side_centers = {
            "top": ((corners[0][0] + corners[1][0]) / 2, (corners[0][1] + corners[1][1]) / 2),      # Top middle (between top-left and top-right)
            "right": ((corners[1][0] + corners[2][0]) / 2, (corners[1][1] + corners[2][1]) / 2),    # Right middle
            "bottom": ((corners[2][0] + corners[3][0]) / 2, (corners[2][1] + corners[3][1]) / 2),   # Bottom middle
            "left": ((corners[3][0] + corners[0][0]) / 2, (corners[3][1] + corners[0][1]) / 2)      # Left middle
        }
        
        # Get angle for each side (perpendicular to the side)
        rad_angle = math.radians(self.orientation)
        
        # Calculate the outward direction for each side based on the robot's orientation
        side_angles = {
            "top": rad_angle - math.pi/2,        # Top points upward (negative y)
            "right": rad_angle,                  # Right points rightward (positive x)
            "bottom": rad_angle + math.pi/2,     # Bottom points downward (positive y)
            "left": rad_angle + math.pi,         # Left points leftward (negative x)
        }

        # Draw triangles at each side center, pointing outward but positioned closer to center
        for side, center in side_centers.items():
            angle = side_angles[side]
            
            # Move triangle starting position inward towards robot center
            inward_offset = self.width / 4  # Move triangle 1/4 of the way toward center
            
            # Calculate new starting position
            center_angle = angle + math.pi  # Opposite direction (toward center)
            adjusted_center_x = center[0] + inward_offset * math.cos(center_angle)
            adjusted_center_y = center[1] + inward_offset * math.sin(center_angle)
            
            # Calculate the tip of the triangle (pointing outward from adjusted center)
            tip_x = adjusted_center_x + triangle_size * math.cos(angle)
            tip_y = adjusted_center_y + triangle_size * math.sin(angle)
            
            # Calculate the perpendicular angle for the base of the triangle
            perp_angle = angle + math.pi/2
            
            # Calculate the base points of the triangle
            base1_x = adjusted_center_x + (triangle_size/2) * math.cos(perp_angle)
            base1_y = adjusted_center_y + (triangle_size/2) * math.sin(perp_angle)
            
            base2_x = adjusted_center_x - (triangle_size/2) * math.cos(perp_angle)
            base2_y = adjusted_center_y - (triangle_size/2) * math.sin(perp_angle)
            
            # Draw triangle
            pygame.draw.polygon(screen, side_colors[side], [
                (tip_x, tip_y),
                (base1_x, base1_y),
                (base2_x, base2_y)
            ])

        # Draw wheels
        for motor_id in [1, 3, 5, 7]:
            # Get wheel position
            wheel_x, wheel_y = self._get_wheel_position(motor_id)
            
            # Get wheel angle - this is relative to robot body
            angle = self.wheel_angles[motor_id]
            
            # Calculate wheel dimensions
            wheel_length = self.wheel_width
            wheel_width = self.wheel_height
            
            # Calculate wheel corner points with rotation
            # Angle is relative to robot body, so add robot orientation
            total_angle = (angle + self.orientation) % 360
            rad_angle = math.radians(total_angle)
            
            # Calculate rotated wheel corners
            self._draw_rotated_wheel(screen, wheel_x, wheel_y, wheel_length, wheel_width, total_angle, self.wheel_color)

    def _draw_rotated_wheel(self, screen, x, y, width, height, angle_degrees, color):
        """
        Draw a rotated wheel at the specified position.
        :param screen: Pygame screen
        :param x: X coordinate of wheel center
        :param y: Y coordinate of wheel center
        :param width: Wheel width (short side)
        :param height: Wheel height (long side)
        :param angle_degrees: Angle in degrees (0-360)
        :param color: Wheel color
        """
        # Create wheel surface with margin for rotation
        max_dim = max(width, height) * 2
        wheel_surface = pygame.Surface((max_dim, max_dim), pygame.SRCALPHA)
        
        # Draw wheel on surface - short side is width, long side is height
        # At angle=0, the wheel will be horizontal with width as short side
        wheel_rect = pygame.Rect(max_dim//2 - width//2, max_dim//2 - height//2, width, height)
        pygame.draw.rect(wheel_surface, color, wheel_rect)
        
        # Add direction indicator line pointing in the same direction as short side
        center = (max_dim//2, max_dim//2)
        # Make indicator shorter - reduced extension from wheel edge
        indicator_end = (center[0], center[1] - width//2 + 2)  # Reduced from 5 to 2
        pygame.draw.line(wheel_surface, (255, 0, 0), center, indicator_end, 2)
        
        # Invert the rotation to match expected behavior (counter-clockwise)
        rotated_surface = pygame.transform.rotate(wheel_surface, -angle_degrees)
        
        # Blit to screen at correct position
        blit_rect = rotated_surface.get_rect(center=(x, y))
        screen.blit(rotated_surface, blit_rect)
    
    def set_wheel_angle(self, wheel_id, angle):
        """
        Set the angle of a specific wheel.
        :param wheel_id: ID of the wheel (1,3,5,7)
        :param angle: Angle in degrees (0-360)
        """
        self.wheel_angles[wheel_id] = angle % 360
    
    def set_all_wheel_angles(self, angle):
        """
        Set all wheel angles to the same value.
        :param angle: Angle in degrees (0-360)
        """
        for wheel_id in [1, 3, 5, 7]:
            self.set_wheel_angle(wheel_id, angle)

    def _get_rotated_corners(self):
        # Calculate center and corner positions
        half_width = self.width / 2
        half_height = self.height / 2
        
        # Define corners relative to center
        corners_rel = [
            (-half_width, -half_height),  # top-left
            (half_width, -half_height),   # top-right
            (half_width, half_height),    # bottom-right
            (-half_width, half_height)    # bottom-left
        ]
        
        # Rotate corners based on robot orientation
        rad_angle = math.radians(self.orientation)
        rotated_corners = []
        
        for x_rel, y_rel in corners_rel:
            # Rotate point
            x_rot = x_rel * math.cos(rad_angle) - y_rel * math.sin(rad_angle)
            y_rot = x_rel * math.sin(rad_angle) + y_rel * math.cos(rad_angle)
            
            # Translate back to screen coordinates
            x_screen = self.x + x_rot
            y_screen = self.y + y_rot
            
            rotated_corners.append((x_screen, y_screen))
        
        return rotated_corners

    def _get_wheel_position(self, wheel_id):
        """
        Calculate the position of a specific wheel based on robot position and orientation.
        
        Args:
            wheel_id: ID of the wheel (1=top-left, 3=top-right, 5=bottom-left, 7=bottom-right)
            
        Returns:
            Tuple (x, y) with wheel position
        """
        # Calculate half dimensions
        half_width = self.width / 2
        half_height = self.height / 2
        
        # Define wheel positions relative to center (before rotation)
        wheel_offsets = {
            1: (-half_width, -half_height),  # top-left
            3: (half_width, -half_height),   # top-right
            5: (-half_width, half_height),    # bottom-left
            7: (half_width, half_height)     # bottom-right
        }
        
        # Get offset for this wheel
        x_offset, y_offset = wheel_offsets[wheel_id]
        
        # Apply rotation based on robot orientation
        rad_angle = math.radians(self.orientation)
        
        # Rotate offset
        rotated_x = x_offset * math.cos(rad_angle) - y_offset * math.sin(rad_angle)
        rotated_y = x_offset * math.sin(rad_angle) + y_offset * math.cos(rad_angle)
        
        # Calculate final wheel position
        wheel_x = self.x + rotated_x
        wheel_y = self.y + rotated_y
        
        return (wheel_x, wheel_y)