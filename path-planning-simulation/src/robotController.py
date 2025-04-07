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
        Set up path following - only calculates and sets wheel angles and speeds.
        Actual movement is performed by move_robot() in the main loop.
        """
        if not self.path_list:
            print("No paths defined")
            return False
            
        # Initialize state
        self.current_path_index = 0
        self.path_progress = 0
        self.moving = True
        self.last_update_time = time.time()
        
        # Position robot at start of first path
        current_path = self.path_list[self.current_path_index]
        if current_path.path_type == 'line':
            self.robot.x, self.robot.y = current_path.start_point
        else:  # curve
            angle = current_path.start_angle
            self.robot.x = current_path.circle_center[0] + current_path.radius * math.cos(angle)
            self.robot.y = current_path.circle_center[1] + current_path.radius * math.sin(angle)
        
        return True

    def move_robot(self):
        """
        Moves the robot based on current wheel angles, speeds and delta time.
        If in path-following mode, also updates path progress and wheel settings.
        """
        if not self.moving:
            return
            
        # Calculate delta time
        current_time = time.time()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # PATH FOLLOWING LOGIC
        if self.path_list and self.current_path_index < len(self.path_list):
            current_path = self.path_list[self.current_path_index]
            
            # Get velocity for current path (default if not specified)
            velocity = current_path.velocity if current_path.velocity is not None else 0.5
            
            # Calculate path length for proper scaling
            if current_path.path_type == 'line':
                x1, y1 = current_path.start_point
                x2, y2 = current_path.end_point
                path_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            else:  # curve
                # Arc length = radius * angle difference
                angle_diff = abs(current_path.end_angle - current_path.start_angle)
                path_length = current_path.radius * angle_diff
            
            # Calculate progress increment based on velocity and path length
            progress_increment = (velocity * delta_time * 100) / path_length
            
            # Update progress along current path
            self.path_progress += progress_increment
            
            # Check if we've finished the current path
            if self.path_progress >= 1.0:
                # Move to next path
                self.current_path_index += 1
                if self.current_path_index >= len(self.path_list):
                    # All paths complete
                    self.set_all_wheel_speeds(0)
                    self.moving = False
                    return
                    
                # Reset progress for new path
                self.path_progress = 0
                # Get the new current path
                current_path = self.path_list[self.current_path_index]
            
            # Set wheel angles and positions based on path type
            if current_path.path_type == 'line':
                # For straight line, use simple linear interpolation
                start_x, start_y = current_path.start_point
                end_x, end_y = current_path.end_point
                
                # If this is the first update for this path, set wheel angles once
                if self.path_progress < 0.01:
                    # Calculate angle from start to end
                    dx = end_x - start_x
                    dy = end_y - start_y
                    
                    # Calculate the line angle (direction of travel)
                    line_angle = (math.degrees(math.atan2(dy, dx))) % 360
                    
                    # Calculate both possible wheel orientations (parallel to line)
                    wheel_angle1 = line_angle
                    wheel_angle2 = (line_angle + 180) % 360
                    
                    # Get current wheel angle (use wheel 1 as reference)
                    current_wheel_angle = self.wheel_angles[1]
                    
                    # Calculate angle differences
                    diff1 = min((wheel_angle1 - current_wheel_angle) % 360, 
                               (current_wheel_angle - wheel_angle1) % 360)
                    diff2 = min((wheel_angle2 - current_wheel_angle) % 360, 
                               (current_wheel_angle - wheel_angle2) % 360)
                    
                    # Choose orientation requiring smallest rotation
                    if diff1 <= diff2:
                        optimal_angle = wheel_angle1
                    else:
                        optimal_angle = wheel_angle2
                    
                    # Set wheel angles to optimal orientation
                    self.set_all_wheel_angles(optimal_angle)
                    self.set_all_wheel_speeds(velocity)
                
                # Calculate current position
                self.robot.x = start_x + (end_x - start_x) * self.path_progress
                self.robot.y = start_y + (end_y - start_y) * self.path_progress
                
            else:  # curve path
                # For curve, calculate angle based on progress
                center_x, center_y = current_path.circle_center
                radius = current_path.radius
                start_angle = current_path.start_angle
                end_angle = current_path.end_angle
                
                # Calculate current angle
                current_angle = start_angle + (end_angle - start_angle) * self.path_progress
                
                # Calculate current position on circle
                self.robot.x = center_x + radius * math.cos(current_angle)
                self.robot.y = center_y + radius * math.sin(current_angle)
                
                # Calculate vector from robot to center
                dx = center_x - self.robot.x
                dy = center_y - self.robot.y
                
                # Calculate angle pointing directly toward center
                center_angle = (math.degrees(math.atan2(dy, dx))) % 360
                
                # Calculate both possible tangent angles (perpendicular to radius)
                tangent_angle1 = (center_angle + 90) % 360  # Clockwise tangent
                tangent_angle2 = (center_angle - 90) % 360  # Counter-clockwise tangent
                
                # Get current wheel angles (use wheel 1 as reference)
                current_wheel_angle = self.wheel_angles[1]
                
                # Calculate angle differences (choose the smallest angle change)
                diff1 = min((tangent_angle1 - current_wheel_angle) % 360, 
                           (current_wheel_angle - tangent_angle1) % 360)
                diff2 = min((tangent_angle2 - current_wheel_angle) % 360, 
                           (current_wheel_angle - tangent_angle2) % 360)
                
                # Choose the tangent angle that requires the smallest rotation
                if diff1 <= diff2:
                    optimal_angle = tangent_angle1
                else:
                    optimal_angle = tangent_angle2
                
                # Set wheel angles to the optimal tangent direction
                self.set_all_wheel_angles(optimal_angle)
                self.set_all_wheel_speeds(velocity)
        
        # REGULAR MOTOR-BASED MOVEMENT - used when not path following or for manual control
        else:
            # Calculate the resultant movement vector
            dx = 0
            dy = 0
            
            # Process each wheel pair (orientation motor, speed motor)
            for orientation_motor, position in self.wheel_positions.items():
                speed_motor = orientation_motor + 1
                angle = math.radians(self.wheel_angles[orientation_motor])
                speed = self.wheel_speeds[speed_motor]
                
                # Calculate this wheel's contribution to movement
                wheel_dx = speed * math.cos(angle)
                wheel_dy = speed * math.sin(angle)
                
                # Add to resultant movement
                dx += wheel_dx
                dy += wheel_dy
            
            # Normalize and scale movement
            magnitude = math.sqrt(dx**2 + dy**2)
            if magnitude > 0:
                # Scale factor determines how fast the robot moves
                scale = 2.0 / len(self.wheel_positions)
                dx = (dx / magnitude) * scale
                dy = (dy / magnitude) * scale
            
            # Apply delta time scaling to movement
            dx *= delta_time * 60  # Scale by delta time and a base factor
            dy *= delta_time * 60
            
            # Update robot position
            self.robot.x += dx
            self.robot.y += dy