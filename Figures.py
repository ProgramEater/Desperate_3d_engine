from math import cos, sin


class Point:
    def __init__(self, coords, color=(255, 0, 0)):
        self.coords = coords
        self.color = color

    def move(self, delta_coords):
        self.coords = (self.coords[0] + delta_coords[0],
                       self.coords[1] + delta_coords[1],
                       self.coords[2] + delta_coords[2])

    def rotate(self, targer_line, phi):
        pass