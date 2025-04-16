import math
import time
import threading
from collections import defaultdict
import wheelControl
from wheelPathGenerator import WheelPathGenerator
from wheel_speed_calculator import WheelSpeedCalculator

class PathHandler:
    """
    Handles robot path following using physical hardware through wheelControl module.
    Controls the robot to follow paths defined by Path objects.
    """
    
    def __init__(self, robot_width, robot_height, motor_update_frequency=10):
        """
        Initialize the path handler.
        
        Args:
            robot_width: Width of the robot chassis (distance between wheels)
            robot_height: Height of the robot chassis (distance between wheels)
            motor_update_frequency: How many times per second to update motor commands
        """
        self.robot_width = robot_width
        self.robot_height = robot_height
        self.update_interval = 1.0 / motor_update_frequency
        
        # Path following state
        self.path_list = []
        self.current_path_index = 0
        self.path_progress = 0  # 0 to 1 progress along current path
        
        # Execution state
        self.is_following = False
        self.current_position = (0, 0)  # (x, y) - must be updated by external position tracking
        self.current_orientation = 0     # degrees - must be updated by external orientation tracking
        
        # Controller thread
        self.control_thread = None
        self.stop_event = threading.Event()
        
        # Wheel path generation and speed calculation
        self.wheel_path_generator = WheelPathGenerator(robot_width, robot_height)
        
        # Motor IDs
        self.angle_motors = [1, 3, 5, 7]  # Motor IDs for angle control
        self.speed_motors = [2, 4, 6, 8]  # Motor IDs for speed control
        
        print("PathHandler initialized with robot dimensions:", robot_width, "x", robot_height)
        
    def set_position(self, x, y, orientation):
        """
        Update the robot's current position and orientation.
        This method should be called regularly by the position tracking system.
        
        Args:
            x: Current x position
            y: Current y position
            orientation: Current orientation in degrees
        """
        self.current_position = (x, y)
        self.current_orientation = orientation
        
    def set_paths(self, path_list, initial_orientation=0, final_orientation=0):
        """
        Set the list of paths to follow.
        
        Args:
            path_list: List of Path objects to follow in sequence
            initial_orientation: Starting orientation in degrees
            final_orientation: Target ending orientation in degrees
        """
        if not path_list:
            print("Error: Empty path list")
            return False
            
        self.path_list = path_list
        self.initial_orientation = initial_orientation
        self.final_orientation = final_orientation
        self.current_path_index = 0
        self.path_progress = 0
        
        # Generate wheel paths for speed calculation
        self.wheel_paths = self.wheel_path_generator.generate_wheel_paths(
            path_list, initial_orientation, final_orientation)
        
        # Calculate wheel speeds
        self.speed_calculator = WheelSpeedCalculator(self.wheel_paths)
        self.wheel_speed_ratios = self.speed_calculator.calculate_speed_ratios()
        
        print(f"Paths set: {len(path_list)} segments, orientation {initial_orientation}° → {final_orientation}°")
        return True
        
    def start_following(self, base_speed=0.5):
        """
        Start following the set paths.
        
        Args:
            base_speed: Base speed scaling factor (0.0 to 1.0)
        
        Returns:
            True if started successfully, False otherwise
        """
        if not self.path_list:
            print("Error: No paths defined")
            return False
            
        if self.is_following:
            print("Already following path")
            return False
            
        self.base_speed = base_speed
        self.is_following = True
        self.stop_event.clear()
        
        # Start the control thread
        self.control_thread = threading.Thread(target=self._control_loop)
        self.control_thread.daemon = True
        self.control_thread.start()
        
        print(f"Started path following with base speed {base_speed}")
        return True
        
    def stop_following(self):
        """
        Stop following the path and halt motors.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.is_following:
            return False
            
        # Signal the thread to stop
        self.stop_event.set()
        
        # Wait for the thread to end
        if self.control_thread:
            self.control_thread.join(timeout=2.0)
            
        # Stop all motors
        for motor_id in self.speed_motors:
            try:
                wheelControl.set_wheel_speed(motor_id, 0)
            except Exception as e:
                print(f"Error stopping motor {motor_id}: {e}")
                
        self.is_following = False
        print("Stopped path following")
        return True
        
    def _control_loop(self):
        """
        Main control loop that runs in a separate thread.
        Updates wheel angles and speeds based on current position and path.
        """
        print("Path following control loop started")
        
        while not self.stop_event.is_set():
            try:
                # Start time for loop timing
                loop_start = time.time()
                
                # Handle the current path
                if self.current_path_index < len(self.path_list):
                    self._handle_current_path()
                else:
                    # End of all paths
                    print("Reached end of all paths")
                    self.stop_following()
                    break
                    
                # Sleep to maintain update frequency
                elapsed = time.time() - loop_start
                if elapsed < self.update_interval:
                    time.sleep(self.update_interval - elapsed)
                    
            except Exception as e:
                print(f"Error in control loop: {e}")
                # Continue running despite errors
                
        print("Path following control loop ended")
        
    def _handle_current_path(self):
        """
        Handle the current path segment based on its type.
        Updates path progress and wheel controls accordingly.
        """
        current_path = self.path_list[self.current_path_index]
        
        # Update path progress based on current position
        self._update_path_progress(current_path)
        
        # Check if we've reached the end of this path segment
        if self.path_progress >= 0.98:
            print(f"Completed path segment {self.current_path_index + 1}/{len(self.path_list)}")
            self._advance_to_next_path()
            return
            
        # Calculate current target orientation
        target_orientation = self.initial_orientation + self.path_progress * (self.final_orientation - self.initial_orientation)
        
        # Calculate path direction based on path type
        path_direction = self._calculate_path_direction(current_path)
        
        # Set wheel angles based on path type and direction
        self._set_wheel_angles(current_path, path_direction, target_orientation)
        
        # Set wheel speeds based on calculated ratios
        self._set_wheel_speeds()
        
    def _update_path_progress(self, current_path):
        """
        Update the progress along the current path based on current position.
        
        Args:
            current_path: The current Path object being followed
        """
        x, y = self.current_position
        
        if current_path.path_type == 'line':
            # For straight line paths
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
            
            # Calculate progress along line (dot product with normalized direction)
            t = ((x - start_x) * dx + (y - start_y) * dy) / path_length
            self.path_progress = max(0, min(1, t))
            
        else:  # curve path
            center_x, center_y = current_path.circle_center
            radius = current_path.radius
            start_angle = current_path.start_angle
            end_angle = current_path.end_angle
            
            # Vector from center to current position
            dx = x - center_x
            dy = y - center_y
            
            # Current angle in the circle
            current_angle = math.atan2(dy, dx)
            
            # Normalize angle for progress calculation
            if end_angle > start_angle:
                # Moving counter-clockwise
                while current_angle < start_angle:
                    current_angle += 2 * math.pi
                while current_angle > end_angle:
                    current_angle -= 2 * math.pi
            else:
                # Moving clockwise
                while current_angle > start_angle:
                    current_angle -= 2 * math.pi
                while current_angle < end_angle:
                    current_angle += 2 * math.pi
            
            # Calculate progress
            angular_progress = (current_angle - start_angle) / (end_angle - start_angle)
            self.path_progress = max(0, min(1, angular_progress))
    
    def _calculate_path_direction(self, path):
        """
        Calculate the direction of motion along the current path at the current progress.
        
        Args:
            path: Current Path object
            
        Returns:
            Direction angle in degrees (0-360)
        """
        if path.path_type == 'line':
            # For line paths, direction is constant
            start_x, start_y = path.start_point
            end_x, end_y = path.end_point
            dx = end_x - start_x
            dy = end_y - start_y
            return math.degrees(math.atan2(dy, dx)) % 360
            
        else:  # curve path
            # For curve paths, direction is tangent to the circle
            center_x, center_y = path.circle_center
            current_x, current_y = self.current_position
            
            # Vector from center to current position
            dx = current_x - center_x
            dy = current_y - center_y
            
            # Center angle (pointing from center to current position)
            center_angle = math.degrees(math.atan2(dy, dx))
            
            # Direction depends on clockwise/counter-clockwise movement
            is_clockwise = path.end_angle < path.start_angle
            
            if is_clockwise:
                # For clockwise movement, tangent is -90° from center angle
                return (center_angle - 90) % 360
            else:
                # For counter-clockwise movement, tangent is +90° from center angle
                return (center_angle + 90) % 360
    
    def _set_wheel_angles(self, path, path_direction, target_orientation):
        """
        Set the wheel angles based on path type and current position.
        Adjusts angles based on robot orientation to maintain correct world direction.
        
        Args:
            path: Current Path object
            path_direction: Current direction of motion in degrees
            target_orientation: Target robot orientation in degrees
        """
        # Calculate adjusted wheel angles (world to robot frame)
        adjusted_angle = (path_direction - self.current_orientation) % 360
        
        # Set all wheel angles
        for motor_id in self.angle_motors:
            try:
                wheelControl.set_wheel_angle(motor_id, adjusted_angle)
            except Exception as e:
                print(f"Error setting angle for motor {motor_id}: {e}")
    
    def _set_wheel_speeds(self):
        """
        Set wheel speeds based on the calculated speed ratios at current progress.
        """
        try:
            # Get wheel speeds at current progress
            speeds = self.speed_calculator.get_speed_at_progress(self.path_progress, self.base_speed)
            normalized_speeds = self.speed_calculator.normalize_speeds(speeds, -1.0, 1.0)
            
            # Set speeds for each motor
            for motor_id, speed in normalized_speeds.items():
                wheelControl.set_wheel_speed(motor_id, speed)
                
        except Exception as e:
            print(f"Error setting wheel speeds: {e}")
    
    def _advance_to_next_path(self):
        """
        Advance to the next path in the sequence.
        """
        self.current_path_index += 1
        self.path_progress = 0
        
        # If we're at the end of all paths, stop following
        if self.current_path_index >= len(self.path_list):
            print("Reached end of path list")
            self.stop_following()
            
    def get_status(self):
        """
        Get the current status of path following.
        
        Returns:
            Dictionary with current status information
        """
        status = {
            "is_following": self.is_following,
            "current_position": self.current_position,
            "current_orientation": self.current_orientation,
            "current_path_index": self.current_path_index,
            "path_progress": self.path_progress,
            "total_paths": len(self.path_list),
        }
        
        # Add additional information if paths are set
        if self.path_list:
            path_types = [path.path_type for path in self.path_list]
            status["path_types"] = path_types
            
        return status


# Example usage
if __name__ == "__main__":
    from path import Path
    import time
    
    # Create a path handler
    handler = PathHandler(robot_width=120, robot_height=120)
    
    # Create a test path (straight line)
    start_point = (0, 0)
    end_point = (1000, 0)
    line_path = Path('line', start_point=start_point, end_point=end_point, velocity=0.5)
    
    # Create a curved path
    center = (1500, 0)
    radius = 500
    curve_path = Path('curve', circle_center=center, radius=radius, 
                      start_angle=math.pi, end_angle=0, velocity=0.5)
    
    # Set the paths with a 90 degree final orientation
    handler.set_paths([line_path, curve_path], initial_orientation=0, final_orientation=90)
    
    # Define a simple position update callback (in a real system, this would come from sensors)
    def update_position():
        # Simulate moving along the path
        t = 0
        while t <= 1 and handler.is_following:
            # Calculate position along first path
            if t <= 0.5:
                # First half is on the line path
                normalized_t = t * 2  # scale from 0-0.5 to 0-1
                x = start_point[0] + (end_point[0] - start_point[0]) * normalized_t
                y = start_point[1] + (end_point[1] - start_point[1]) * normalized_t
                # Simulate gradual orientation change (0 to 45 degrees)
                orientation = 45 * normalized_t
            else:
                # Second half is on the curve path
                normalized_t = (t - 0.5) * 2  # scale from 0.5-1 to 0-1
                angle = math.pi - normalized_t * math.pi  # From π to 0
                x = center[0] + radius * math.cos(angle)
                y = center[1] + radius * math.sin(angle)
                # Simulate continued orientation change (45 to 90 degrees)
                orientation = 45 + 45 * normalized_t
            
            handler.set_position(x, y, orientation)
            t += 0.01
            time.sleep(0.1)
    
    try:
        # Start path following
        handler.start_following(base_speed=0.5)
        
        # Start position updates in a separate thread
        position_thread = threading.Thread(target=update_position)
        position_thread.daemon = True
        position_thread.start()
        
        # Let it run for a while
        time.sleep(30)
        
    finally:
        # Stop following
        handler.stop_following()