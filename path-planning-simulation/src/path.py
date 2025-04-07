import math

class Path:
    def __init__(self, path_type, **kwargs):
        """
        Initialize the path with either line or curve parameters.
        :param path_type: 'line' or 'curve'
        :param kwargs: 
            For line: start_point, end_point
            For curve: circle_center, radius, start_angle, end_angle
        """
        self.path_type = path_type
        
        if path_type == 'line':
            self.start_point = kwargs.get('start_point')
            self.end_point = kwargs.get('end_point')
        elif path_type == 'curve':
            self.circle_center = kwargs.get('circle_center')
            self.radius = kwargs.get('radius')
            self.start_angle = kwargs.get('start_angle')
            self.end_angle = kwargs.get('end_angle')

        self.velocity = kwargs.get('velocity')
        self.orientation = kwargs.get('orientation')
        
        
    def get_point(self, t):
        """
        Get a point on the path for a given t (0 <= t <= 1).
        :param t: Parameter (0 to 1) indicating position along path
        :return: (x, y) point on the path
        """
        if self.path_type == 'line':
            x = self.start_point[0] + (self.end_point[0] - self.start_point[0]) * t
            y = self.start_point[1] + (self.end_point[1] - self.start_point[1]) * t
        else:  # curve
            angle = self.start_angle + (self.end_angle - self.start_angle) * t
            x = self.circle_center[0] + self.radius * math.cos(angle)
            y = self.circle_center[1] + self.radius * math.sin(angle)
            
        return int(x), int(y)

    def generate_path(self, num_points=100):
        """
        Generate a list of points along the path.
        :param num_points: Number of points to generate
        :return: List of (x, y) points
        """
        return [self.get_point(t / (num_points - 1)) for t in range(num_points)]