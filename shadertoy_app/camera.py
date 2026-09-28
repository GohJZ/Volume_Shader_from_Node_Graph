import math


class Camera:
    def __init__(self, target=(0.0, 0.0, 0.0), distance=40.0, yaw=0.0, pitch=15.0):
        self.target = list(target)
        self.distance = distance
        self.yaw = yaw  # degrees, around Y
        self.pitch = pitch  # degrees, up/down

    @property
    def position(self):
        yaw_r = math.radians(self.yaw)
        pitch_r = math.radians(self.pitch)
        x = self.target[0] + self.distance * math.cos(pitch_r) * math.cos(yaw_r)
        y = self.target[1] + self.distance * math.sin(pitch_r)
        z = self.target[2] + self.distance * math.cos(pitch_r) * math.sin(yaw_r)
        return (x, y, z)

    def orbit(self, dx, dy):
        self.yaw += dx
        self.pitch = max(-89.0, min(89.0, self.pitch + dy))

    def zoom(self, amount):
        self.distance = max(2.0, self.distance - amount)
