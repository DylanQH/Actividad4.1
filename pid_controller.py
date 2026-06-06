"""Controlador PID sencillo para la direccion del vehiculo."""

import time


class PIDController:
    def __init__(self, kp, ki, kd, output_min=None, output_max=None):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_min = output_min
        self.output_max = output_max
        self.reset()

    def reset(self):
        self.integral = 0.0
        self.previous_error = None
        self.previous_time = None

    def compute(self, error, current_time=None):
        current_time = time.monotonic() if current_time is None else current_time

        if self.previous_time is None:
            delta_time = 0.0
            derivative = 0.0
        else:
            delta_time = max(current_time - self.previous_time, 1e-6)
            derivative = (error - self.previous_error) / delta_time

        self.integral += error * delta_time
        output = self.kp * error + self.ki * self.integral + self.kd * derivative

        if self.output_min is not None:
            output = max(self.output_min, output)
        if self.output_max is not None:
            output = min(self.output_max, output)

        self.previous_error = error
        self.previous_time = current_time
        return output
