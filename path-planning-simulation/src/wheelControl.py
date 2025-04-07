import redis
import math
import time
import threading
from collections import defaultdict

# Initialize Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Store active timers for each wheel
wheel_timers = defaultdict(lambda: None)

def set_wheel_speed(wheel_id, speed):
    """
    Set the speed of a wheel in Redis.
    :param wheel_id: ID of the wheel(2,4,6,8)
    :param speed: Speed value (-1 to 1)
    """
    redis_client.set(f'speed_{wheel_id}', speed)

def set_wheel_angle(wheel_id, angle):
    """
    Set the angle of a wheel in Redis.  
    :param wheel_id: ID of the wheel(1,3,5,7)
    :param angle: Angle in degrees (0-360)
    """
    redis_client.set(f'angle_{wheel_id}', angle)

def set_timed_speed(wheel_id, speed, duration):
    """
    Set a wheel speed for a specified duration with timer management.
    :param wheel_id: ID of the wheel
    :param speed: Speed value (-1 to 1)
    :param duration: Duration in seconds
    :return: True if timer was set, False if error occurred
    """
    # Cancel existing timer for this wheel if any
    if wheel_timers[wheel_id] is not None:
            wheel_timers[wheel_id].cancel()

    def speed_timer():
        try:
            set_wheel_speed(wheel_id, speed)
            time.sleep(duration)
            set_wheel_speed(wheel_id, 0)
        except redis.RedisError as e:
            print(f"Redis error: {e}")
        finally:
            wheel_timers[wheel_id] = None

    # Create and start new timer thread
    timer = threading.Thread(target=speed_timer)
    wheel_timers[wheel_id] = timer
    timer.start()

def set_timed_angle(wheel_id, initial_angle, final_angle, duration):
    """
    Set a wheel angle for a specified duration with timer management.
    :param wheel_id: ID of the wheel
    :param angle: Angle in degrees (0-360)
    :param duration: Duration in seconds
    """
    # Cancel existing timer for this wheel if any
    if wheel_timers[wheel_id] is not None:
        wheel_timers[wheel_id].cancel()

    def angle_timer():
        try:
            set_wheel_angle(wheel_id, initial_angle)
            time.sleep(duration)
            set_wheel_angle(wheel_id, final_angle)
        except redis.RedisError as e:
            print(f"Redis error: {e}")
        finally:
            wheel_timers[wheel_id] = None

    # Create and start new timer thread
    timer = threading.Thread(target=angle_timer)
    wheel_timers[wheel_id] = timer
    timer.start()

def cancel_timed_speed(wheel_id):
    """
    Cancel any active timed speed for a wheel.
    :param wheel_id: ID of the wheel
    """
    if wheel_timers[wheel_id] is not None:
        wheel_timers[wheel_id].cancel()
        set_wheel_speed(wheel_id, 0)
        wheel_timers[wheel_id] = None

def get_trapezoidal_speed(t):
    """
    Calculate speed using trapezoidal profile.
    :param t: Normalized time (0 to 1)
    :return: Speed value (-1 to 1)
    """
    if t < 0.2:
        return t * 5  # Acceleration
    elif t < 0.8:
        return 1.0    # Constant speed
    else:
        return 1.0 - ((t - 0.8) * 5)  # Deceleration

def get_sinusoidal_speed(t):
    """
    Calculate speed using sinusoidal profile.
    :param t: Normalized time (0 to 1)
    :return: Speed value (-1 to 1)
    """
    return math.sin(t * math.pi)

def get_linear_speed(t):
    """
    Calculate speed using linear profile.
    :param t: Normalized time (0 to 1)
    :return: Speed value (-1 to 1)
    """
    return 0.5

def get_speed_from_curve(t, curve_type='trapezoidal'):
    """
    Get speed value based on curve type and time.
    :param t: Normalized time (0 to 1)
    :param curve_type: Type of speed curve ('trapezoidal', 'sinusoidal', 'linear')
    :return: Speed value (-1 to 1)
    """
    curves = {
        'trapezoidal': get_trapezoidal_speed,
        'sinusoidal': get_sinusoidal_speed,
        'linear': get_linear_speed
    }
    return curves.get(curve_type, get_linear_speed)(t)

def set_curve_speed(wheel_id, duration, curve_type='trapezoidal'):
    """
    Set wheel speed following a curve pattern over time.
    :param wheel_id: ID of the wheel
    :param duration: Total duration in seconds
    :param curve_type: Type of speed curve ('trapezoidal', 'sinusoidal', 'linear')
    """
    if wheel_timers[wheel_id] is not None:
        wheel_timers[wheel_id].cancel()

    def curve_timer():
        try:
            start_time = time.time()
            while True:
                current_time = time.time() - start_time
                if current_time >= duration:
                    set_wheel_speed(wheel_id, 0)
                    break

                t = current_time / duration
                speed = get_speed_from_curve(t, curve_type)
                set_wheel_speed(wheel_id, speed)
                time.sleep(0.05)  # Update every 50ms

        except redis.RedisError as e:
            print(f"Redis error: {e}")
        finally:
            wheel_timers[wheel_id] = None

    timer = threading.Thread(target=curve_timer)
    wheel_timers[wheel_id] = timer
    timer.start()

