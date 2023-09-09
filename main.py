import math
import sys

import pygame


class Camera:
    # A - camera position itself
    # O - rotating point

    def __init__(self, o_coords, ao_length, fov_hor, fov_ver, move_length, lens_curvature_radius):
        # angle between AO projection and positive X direction (0 -> 6.28 rad)
        self.alpha = 0

        # angle between AO projection on xy surface and AO itself (0 -> 3.14 rad)
        self.omega = 0

        # AO length
        self.ao_length = ao_length
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
        x, y, z = (self.o[0] + self.ao_length * math.cos(self.omega) * math.cos(self.alpha),
                   self.o[1] + self.ao_length * math.cos(self.omega) * math.sin(self.alpha),
                   self.o[2] + self.ao_length * math.sin(self.omega))
        self.a = (x, y, z)

    def move(self, n):
        # move A along the AO
        self.o = (self.o[0] + n * self.move_l * math.cos(self.omega) * math.cos(self.alpha),
                  self.o[1] + n * self.move_l * math.cos(self.omega) * math.sin(self.alpha),
                  self.o[2] + n * self.move_l * math.sin(self.omega))

    def point_screen_proportion(self, point):
        # atan angle tangent if point is to the right (on X axis) from the A else it is atan + pi
        try:
            tg_amx_angle = (self.a[1] - point[1]) / (self.a[0] - point[0])
            cos_amx_angle = (self.a[0] - point[0]) / math.sqrt((self.a[1] - point[1]) ** 2 +
                                                               (self.a[0] - point[0]) ** 2)
            atan_ang = math.atan(tg_amx_angle)
            amx_angle = atan_ang - (0 if cos_amx_angle >= 0 else math.pi * abs(atan_ang) / atan_ang)
        except ZeroDivisionError:
            amx_angle = -math.pi / 2 if point[1] >= self.a[1] else math.pi / 2

        fov_hor_xy = math.pi if self.fov_hor == math.pi \
            else 2 * math.atan(math.tan(self.fov_hor / 2) / math.cos(self.omega))

        # if tan of point_a_Xaxis angle is between camera borders angles with Xaxis
        # then we return proportion of M on this camera screen else return -1
        if not -fov_hor_xy / 2 < amx_angle - self.alpha < fov_hor_xy / 2:
            return -1,

        # if tangent of point-A-AO_xy_projection exists then we find atan and use it as is if
        try:
            amxl_angle = math.atan((self.a[2] - point[2]) /
                                   (math.sqrt((point[0] - self.a[0]) ** 2 +
                                              (point[1] - self.a[1]) ** 2)
                                    * math.cos(amx_angle - self.alpha)))
        except ZeroDivisionError:
            amxl_angle = -math.pi if point[2] >= self.a[2] else math.pi

        # same for vertical camera surface (now it is AO "axis" instead of X axis
        if not -self.fov_ver / 2 < amxl_angle - self.omega < self.fov_ver / 2:
            return -1,

        x_prop = 0.5 - math.tan(amx_angle - self.alpha) / (2 * math.tan(fov_hor_xy / 2))
        y_prop = 0.5 - math.tan(amxl_angle - self.omega) / (2 * math.tan(self.fov_ver / 2))
        x_prop = 0.5 - math.sin(amx_angle - self.alpha) / (2 * math.sin(fov_hor_xy / 2))
        y_prop = 0.5 - math.sin(amxl_angle - self.omega) / (2 * math.sin(self.fov_ver / 2))
        return x_prop, y_prop


if __name__ == "__main__":
    pygame.init()

    size = 720, 460
    screen = pygame.display.set_mode(size)

    focal_l = 1
    cam_size = (i * 0.02 for i in size)
    fov_hor, fov_ver = (math.atan(i / 2 / focal_l) * 2 for i in cam_size)
    camera = Camera((0, 0, 0), 16, math.pi / 2, math.pi / 3, 1, 1000)

    alpha_add, omega_add = 0.005, 0.005

    points = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)] #
    points_sc = []

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
                camera.alpha = (alpha_add * (-pygame.mouse.get_pos()[0] + x_hold_start) + camera.alpha)
                camera.alpha = min(math.pi, max(-math.pi, -camera.alpha)) if abs(camera.alpha) > math.pi \
                    else camera.alpha
                camera.omega = min(math.pi / 2, max(-math.pi / 2,
                                                    omega_add * (pygame.mouse.get_pos()[1] - y_hold_start) + camera.omega))
                camera.a_solve()
                x_hold_start, y_hold_start = pygame.mouse.get_pos()

            if event.type == pygame.MOUSEWHEEL:
                # camera.move(-event.y)
                camera.ao_length += -event.y * camera.move_l
                camera.a_solve()

        points_sc = []
        for point in points:
            prop = camera.point_screen_proportion(point)
            if prop[0] != -1:
                x, y = size[0] * prop[0], size[1] * (1 - prop[1])
                points_sc.append((x, y))
                pygame.draw.circle(screen, 'red' if point != (0, 0, 0) else 'blue', (x, y), 10)
            else:
                print(point)
        # cube lines
        try:
            if True:
                for i in [(points_sc[0], points_sc[1]),
                          (points_sc[1], points_sc[2]),
                          (points_sc[2], points_sc[3]),
                          (points_sc[3], points_sc[0]),
                          (points_sc[0], points_sc[4]),
                          (points_sc[1], points_sc[5]),
                          (points_sc[2], points_sc[6]),
                          (points_sc[3], points_sc[7]),
                          (points_sc[4], points_sc[5]),
                          (points_sc[5], points_sc[6]),
                          (points_sc[6], points_sc[7]),
                          (points_sc[7], points_sc[4])]:
                    pygame.draw.line(screen, 'red', i[0], i[1], width=1)
        except IndexError:
            pass

        print(camera.o, camera.a, camera.alpha, camera.omega)
        pygame.display.flip()
