import math
import sys

import pygame


class Camera:
    # A - camera position itself
    # O - rotating point

    def __init__(self, o_coords, focal_l, fov_hor, fov_ver, move_length, lens_curvature_radius):
        # angle between AO projection and positive X direction (0 -> 6.28 rad)
        self.alpha = math.pi

        # angle between AO projection on xy surface and AO itself (0 -> 3.14 rad)
        self.omega = 0

        # AO length
        self.focal_l = focal_l
        # move length (along AO)
        self.move_l = move_length

        self.lens_r = lens_curvature_radius

        # fields of view (vertical and horizontal)
        self.fov_hor = fov_hor
        self.fov_ver = fov_ver

        self.o = o_coords
        self.a = (0, 0, 0)
        self.a_solve()

    def a_solve(self):
        # solve A coords from angles and O coords and AO length (focal_l)
        x, y, z = (self.o[0] - self.focal_l * math.cos(self.omega) * math.cos(self.alpha),
                   self.o[1] - self.focal_l * math.cos(self.omega) * math.sin(self.alpha),
                   self.o[2] - self.focal_l * math.sin(self.omega))
        self.a = (x, y, z)

    def move(self, n):
        # move A along the AO
        self.o = (self.o[0] + n * self.move_l * math.cos(self.omega) * math.cos(self.alpha),
                  self.o[1] + n * self.move_l * math.cos(self.omega) * math.sin(self.alpha),
                  self.o[2] + n * self.move_l * math.sin(self.omega))

    def point_screen_proportion(self, point):
        # atan angle tangent if point is to the right (on X axis) from the A else it is atan + pi
        try:
            point_a_x_angle = math.atan((point[1] - self.a[1]) / (point[0] - self.a[0])) + \
                              (0 if point[0] >= self.a[0] else 3.14)
        except ZeroDivisionError:
            point_a_x_angle = 0 if point[0] >= self.a[0] else 3.14

        # if tan of point_a_Xaxis angle is between camera borders angles with Xaxis
        # then we return proportion of M on this camera screen else return -1
        if not self.alpha + self.fov_hor / 2 > point_a_x_angle > self.alpha - self.fov_hor / 2:
            return -1,

        # if tangent of point-A-AO_xy_projection exists then we find atan and use it as is if
        try:
            point_a_ao_angle = math.atan((point[2] - self.a[2]) /
                                         math.sqrt((point[0] - self.a[0]) ** 2 + (point[1] - self.a[1]) ** 2))
        except ZeroDivisionError:
            point_a_ao_angle = 3.14 if point[2] >= self.a[2] else -3.14

        # same for vertical camera surface (now it is AO "axis" instead of X axis
        if not self.omega + self.fov_ver / 2 > point_a_ao_angle > self.omega - self.fov_ver / 2:
            return -1,

        x_prop = math.tan(self.alpha - point_a_x_angle) / math.tan(self.fov_hor / 2) + 0.5
        y_prop = math.tan(self.omega - point_a_ao_angle) / math.tan(self.fov_ver / 2) + 0.5
        # x_prop = 0.5 + (self.lens_r * math.sin(self.alpha - point_a_x_angle) /
        #                 (2 * self.focal_l * math.cos(point_a_ao_angle) * math.tan(self.fov_hor / 2)))
        # y_prop = 0.5 + (self.lens_r * math.sin(self.omega - point_a_ao_angle) /
        #                 (2 * self.focal_l * math.cos(point_a_x_angle) * math.tan(self.fov_ver / 2)))

        print(point_a_ao_angle, self.omega, self.a, point)
        return x_prop, y_prop


if __name__ == "__main__":
    pygame.init()

    size = 720, 460
    screen = pygame.display.set_mode(size)

    focal_l = 1
    cam_size = (i * 0.02 for i in size)
    fov_hor, fov_ver = (math.atan(i / 2 / focal_l) * 2 for i in cam_size)
    camera = Camera((0, 0, 0), 16, math.pi / 3, math.pi / 6, 1, 1000)

    alpha_add, omega_add = 0.005, 0.005

    points = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 0), (0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 1)] #

    x_hold_start, y_hold_start = -1, -1

    clock = pygame.time.Clock()
    clock.tick(30)

    while True:
        screen.fill('white')
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                x_hold_start, y_hold_start = pygame.mouse.get_pos()

            elif event.type == pygame.MOUSEBUTTONUP:
                x_hold_start, y_hold_start = -1, -1

            elif (x_hold_start, y_hold_start) != (-1, -1):
                camera.alpha = (alpha_add * (-pygame.mouse.get_pos()[0] + x_hold_start) + camera.alpha) % 6.28
                camera.omega = min(math.pi / 2, max(-math.pi / 2,
                                                    omega_add * (-pygame.mouse.get_pos()[1] + y_hold_start) + camera.omega))
                camera.a_solve()
                x_hold_start, y_hold_start = pygame.mouse.get_pos()

            if event.type == pygame.MOUSEWHEEL:
                # camera.move(-event.y)
                camera.focal_l += -event.y * camera.move_l
                camera.a_solve()

        for point in points:
            try:
                prop = camera.point_screen_proportion(point)
            except ZeroDivisionError:
                pass
            else:
                if prop[0] != -1:
                    x, y = size[0] * prop[0], size[1] * prop[1]
                    pygame.draw.circle(screen, 'red' if point != (0, 0, 0) else 'blue', (x, y), 10)
                else:
                    print(point)

        # print(camera.o, camera.a, camera.alpha, camera.omega)
        pygame.display.flip()
