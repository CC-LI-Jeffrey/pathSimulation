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
        # Initialize wheels to face up (90 degrees)
        self.wheel_angles = {1: 90, 3: 90, 5: 90, 7: 90}

    def draw(self, screen):
        # Calculate centered position
        center_x = self.x - self.width // 2
        center_y = self.y - self.height // 2

        # Draw robot body
        robot_body = pygame.Rect(center_x, center_y, self.width, self.height)
        pygame.draw.rect(screen, self.body_color, robot_body)

        # Wheel positions
        wheel_positions = {
            1: (center_x, center_y),  # top-left
            3: (center_x + self.width, center_y),  # top-right
            5: (center_x, center_y + self.height),  # bottom-left
            7: (center_x + self.width, center_y + self.height)  # bottom-right
        }

        # Draw each wheel with proper rotation
        for wheel_id, pos in wheel_positions.items():
            angle = self.wheel_angles.get(wheel_id, 0)
            self._draw_rotated_wheel(screen, pos[0], pos[1], self.wheel_width, self.wheel_height, angle, self.wheel_color)

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