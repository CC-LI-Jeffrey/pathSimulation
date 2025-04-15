import math
import time
import threading
from collections import defaultdict
import pygame

class RobotController:
    def __init__(self, robot):
        """
        Initialize the robot controller with 8 motors.
        Motors 1,3,5,7 control wheel orientation (0-360 degrees)
        Motors 2,4,6,8 control wheel speed (-1 to 1)
        """
        self.robot = robot
        self.moving = False
        self.last_update_time = time.time()
        
        # Initialize motor states
        self.wheel_angles = {1: 0, 3: 0, 5: 0, 7: 0}  # Orientation motors (degrees)
        self.wheel_speeds = {2: 0, 4: 0, 6: 0, 8: 0}  # Speed motors (-1 to 1)
        
        # Wheel positions (top-left, top-right, bottom-left, bottom-right)
        self.wheel_positions = {
            1: "top-left",
            3: "top-right", 
            5: "bottom-left",
            7: "bottom-right"
        }
        
        # Path following state
        self.path_list = []
        self.current_path_index = 0
        self.path_progress = 0  # 0 to 1 progress along current path
        
    def set_paths(self, path_list):
        """
        Set the list of paths to follow in sequence.
        :param path_list: List of Path objects
        """
        self.path_list = path_list
        self.current_path_index = 0
        self.path_progress = 0
        
    def set_wheel_angle(self, motor_id, angle):
        """Set the angle of a wheel orientation motor."""
        if motor_id in self.wheel_angles:
            self.wheel_angles[motor_id] = angle % 360
            # Also update the robot's wheel angle
            self.robot.set_wheel_angle(motor_id, angle)
    
    def set_wheel_speed(self, motor_id, speed):
        """Set the speed of a wheel speed motor."""
        if motor_id in self.wheel_speeds:
            self.wheel_speeds[motor_id] = max(-1, min(1, speed))
    
    def set_all_wheel_angles(self, angle):
        """Set all wheel orientation motors to the same angle."""
        for motor_id in self.wheel_angles:
            self.set_wheel_angle(motor_id, angle)
    
    def set_all_wheel_speeds(self, speed):
        """Set all wheel speed motors to the same speed."""
        for motor_id in self.wheel_speeds:
            self.set_wheel_speed(motor_id, speed)
    
    def follow_paths(self):
        """
        Initialize path following without actually moving the robot.
        This only sets up the initial state for path following.
        """
        if not self.path_list:
            print("No paths defined")
            return False
            
        # Initialize state
        self.current_path_index = 0
        self.path_progress = 0
        self.moving = True
        self.last_update_time = time.time()
        
        # Configure wheels for the first path
        current_path = self.path_list[self.current_path_index]
        self._configure_initial_wheels(current_path)
        
        return True

    def _configure_initial_wheels(self, path):
        """
        Configure wheels for the initial path segment.
        """
        if path.path_type == 'line':
            # For straight line, set orientation
            start_x, start_y = path.start_point
            end_x, end_y = path.end_point
            dx = end_x - start_x
            dy = end_y - start_y
            line_angle = (math.degrees(math.atan2(dy, dx))) % 360
            self.set_all_wheel_angles(line_angle)
        else:  # curve
            # Set wheels tangent to the curve at the starting point
            center_x, center_y = path.circle_center
            start_angle = path.start_angle
            start_x = center_x + path.radius * math.cos(start_angle)
            start_y = center_y + path.radius * math.sin(start_angle)
            dx = center_x - start_x
            dy = center_y - start_y
            center_angle = (math.degrees(math.atan2(dy, dx))) % 360
            tangent_angle = (center_angle + 90) % 360
            self.set_all_wheel_angles(tangent_angle)
        
        # Set initial speed based on path velocity
        velocity = path.velocity if path.velocity is not None else 0.5
        self.set_all_wheel_speeds(velocity)

    def update_path_following(self):
        """
        Update wheel angles and speeds based on current position relative to the path.
        """
        if not self.path_list or self.current_path_index >= len(self.path_list):
            return False
        
        current_path = self.path_list[self.current_path_index]
        current_x, current_y = self.robot.x, self.robot.y
        
        # Get velocity for current path
        velocity = current_path.velocity if current_path.velocity is not None else 0.5
        
        # Handle specific path types
        if current_path.path_type == 'line':
            # For line paths - code remains the same
            start_x, start_y = current_path.start_point
            end_x, end_y = current_path.end_point
            
            # Calculate direction vector
            dx = end_x - start_x
            dy = end_y - start_y
            path_length = math.sqrt(dx**2 + dy**2)
            
            # Normalize direction
            if path_length > 0:
                dx /= path_length
                dy /= path_length
            
            # Calculate progress along line
            t = ((current_x - start_x) * dx + (current_y - start_y) * dy) / path_length
            self.path_progress = max(0, min(1, t))
            
            # Check if reached end of path
            if self.path_progress >= 0.98:
                self._advance_to_next_path()
                return True
            
        else:  # curve path - this is where the fix is needed
            center_x, center_y = current_path.circle_center
            radius = current_path.radius
            start_angle = current_path.start_angle
            end_angle = current_path.end_angle
            
            # Vector from center to current position
            dx = current_x - center_x
            dy = current_y - center_y
            
            # Current angle in the circle
            current_angle = math.atan2(dy, dx)
            
            # Normalize angle for progress calculation
            if end_angle > start_angle:
                while current_angle < start_angle:
                    current_angle += 2 * math.pi
                while current_angle > end_angle:
                    current_angle -= 2 * math.pi
            else:
                while current_angle > start_angle:
                    current_angle -= 2 * math.pi
                while current_angle < end_angle:
                    current_angle += 2 * math.pi
            
            # Calculate progress
            self.path_progress = (current_angle - start_angle) / (end_angle - start_angle)
            self.path_progress = max(0, min(1, self.path_progress))
            
            # Check if reached end of path
            if abs(self.path_progress - 1.0) < 0.02:
                self._advance_to_next_path()
                return True
            
            # Calculate tangent direction for curve
            # The tangent is perpendicular to the radius vector
            # For counter-clockwise movement: tangent = 90° clockwise from center angle
            # For clockwise movement: tangent = 90° counter-clockwise from center angle
            center_angle = math.degrees(math.atan2(dy, dx))
            
            # Determine if we're moving clockwise or counter-clockwise
            is_clockwise = end_angle < start_angle
            
            if is_clockwise:
                # For clockwise movement, tangent is -90° from center angle
                tangent_angle = (center_angle - 90) % 360
            else:
                # For counter-clockwise movement, tangent is +90° from center angle
                tangent_angle = (center_angle + 90) % 360
            
            # Set wheel angles to follow the tangent direction
            self.set_all_wheel_angles(tangent_angle)
        
        return True

    def _advance_to_next_path(self):
        """
        Advance to the next path in the sequence and configure wheels accordingly.
        """
        self.current_path_index += 1
        
        # Check if we're at the end of all paths
        if self.current_path_index >= len(self.path_list):
            self.set_all_wheel_speeds(0)
            self.moving = False
            return
        
        # Reset progress and configure wheels for the new path
        self.path_progress = 0
        next_path = self.path_list[self.current_path_index]
        self._configure_initial_wheels(next_path)

    def move_robot(self):
        """
        Moves the robot based on current wheel angles and speeds.
        If path following is active, updates the path following logic first.
        """
        if not self.moving:
            return
        
        # Calculate delta time
        current_time = time.time()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Update path following if active
        if self.path_list and self.current_path_index < len(self.path_list):
            self.update_path_following()
        
        # ACTUAL PHYSICS-BASED MOVEMENT - pure wheel-based movement
        # Calculate the resultant movement vector based on all wheels
        dx = 0
        dy = 0
        
        # Process each wheel pair (orientation motor, speed motor)
        for orientation_motor, position in self.wheel_positions.items():
            speed_motor = orientation_motor + 1
            angle_rad = math.radians(self.wheel_angles[orientation_motor])
            speed = self.wheel_speeds[speed_motor]
            
            # Calculate this wheel's contribution to movement
            wheel_dx = speed * math.cos(angle_rad)
            wheel_dy = speed * math.sin(angle_rad)
            
            # Add to resultant movement
            dx += wheel_dx
            dy += wheel_dy
        
        # Average the movement contributions from all wheels
        num_wheels = len(self.wheel_positions)
        if num_wheels > 0:
            dx /= num_wheels
            dy /= num_wheels
        
        # Apply velocity scaling
        movement_speed = 100  # Base speed factor
        dx *= movement_speed * delta_time
        dy *= movement_speed * delta_time
        
        # Update robot position
        self.robot.x += dx
        self.robot.y += dy