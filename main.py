import math
import sys

import pygame

import proportion_first_try


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

        # local Z axis for camera (rotates with camera)
        self.vec_n = (0, 0, 0)
        # ax + by + cz + d = 0 ==> d for the surface
        self.hor_surf_d = 0

        # local "left" axis for camera (always points to the left of view parallel to XY)
        self.vec_m = (0, 0, 0)
        self.ver_surf_d = 0

        self.view_vec = (0, 0, 0)

        self.a_solve()
        self.view_vec = self.vec_solve(self.a, self.o)
        self.solve_m_n(length=1)

    def a_solve(self):
        # solve A coords from angles and O coords and AO length (focal_l)
        x, y, z = (self.o[0] + self.ao_length * math.cos(self.omega) * math.cos(self.alpha),
                   self.o[1] + self.ao_length * math.cos(self.omega) * math.sin(self.alpha),
                   self.o[2] + self.ao_length * math.sin(self.omega))
        self.a = (x, y, z)

    def vec_solve(self, point_from, point_to):
        return (point_to[0] - point_from[0],
                point_to[1] - point_from[1],
                point_to[2] - point_from[2])

    def vec_length(self, vec):
        return math.sqrt(vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2)

    def vec_mult(self, vec1, vec2):
        return vec1[0] * vec2[0] + vec1[1] * vec2[1] + vec1[2] * vec2[2]

    def solve_m_n(self, length=1):
        self.vec_n = (-length * math.cos(self.alpha) * math.sin(self.omega),
                      -length * math.sin(self.alpha) * math.sin(self.omega),
                      length * math.cos(self.omega))

        # "local" left vector (always point to the left of the view vector AO)
        self.vec_m = (length * math.sin(self.alpha),
                      -length * math.cos(self.alpha),
                      0)

        self.hor_surf_d = -(self.vec_n[0] * self.a[0] + self.vec_n[1] * self.a[1] + self.vec_n[2] * self.a[2])
        self.ver_surf_d = -(self.vec_m[0] * self.a[0] + self.vec_m[1] * self.a[1] + self.vec_m[2] * self.a[2])

    def move(self, n):
        # move A along the AO
        self.o = (self.o[0] + n * self.move_l * math.cos(self.omega) * math.cos(self.alpha),
                  self.o[1] + n * self.move_l * math.cos(self.omega) * math.sin(self.alpha),
                  self.o[2] + n * self.move_l * math.sin(self.omega))

    def update(self):
        self.a_solve()
        self.view_vec = self.vec_solve(self.a, self.o)
        self.solve_m_n()

    def point_screen_proportion(self, point):
        # "local" vertical camera vector (always points perpendicularly up to the view vector AO)
        n_vec = self.vec_n

        # "local" left vector (always point to the left of the view vector AO)
        m_vec = self.vec_m

        # multiplier for vector n so that you can add it to the point to get its projection on the surface
        delta_n = -(point[0] * n_vec[0] + point[1] * n_vec[1] + point[2] * n_vec[2] + self.hor_surf_d) / \
                   (n_vec[0] ** 2 + n_vec[1] ** 2 + n_vec[2] ** 2)

        # point projection on horizontal camera surface
        point_horizontal = (point[0] + delta_n * n_vec[0],
                            point[1] + delta_n * n_vec[1],
                            point[2] + delta_n * n_vec[2])

        delta_m = -(point[0] * m_vec[0] + point[1] * m_vec[1] + point[2] * m_vec[2] + self.ver_surf_d) / \
                   (m_vec[0] ** 2 + m_vec[1] ** 2 + m_vec[2] ** 2)

        point_vertical = (point[0] + delta_m * m_vec[0],
                          point[1] + delta_m * m_vec[1],
                          point[2] + delta_m * m_vec[2])

        # LAMBDA (ANGLE) BETWEEN AO AND POINT HORIZONTAL
        vec_to_point_hor = self.vec_solve(self.a, point_horizontal)

        # cos between OA and AMh
        # --------------------------
        try:
            point_lam_horizontal_cos = (self.vec_mult(vec_to_point_hor, self.view_vec)) / \
                                       (self.vec_length(vec_to_point_hor) * self.vec_length(self.view_vec))
            point_lam_horizontal_cos /= point_lam_horizontal_cos if abs(point_lam_horizontal_cos) > 1 else 1
        except ZeroDivisionError:
            point_lam_horizontal_cos = 0
        # --------------------------
        # ANGLE
        point_lam_horizontal = math.acos(point_lam_horizontal_cos)

        # LAMBDA (ANGLE) BETWEEN AO AND POINT VERTICAL
        vec_to_point_ver = self.vec_solve(self.a, point_vertical)

        # cos between OA and AMv
        # --------------------------
        try:
            point_lam_vertical_cos = (self.vec_mult(vec_to_point_ver, self.view_vec)) / \
                                     (self.vec_length(vec_to_point_ver) * self.vec_length(self.view_vec))
            point_lam_vertical_cos /= point_lam_vertical_cos if abs(point_lam_vertical_cos) > 1 else 1
        except ZeroDivisionError:
            point_lam_vertical_cos = 0
        # --------------------------
        # ANGLE
        point_lam_vertical = math.acos(point_lam_vertical_cos)

        prop_x = 0.5 + math.tan(point_lam_horizontal) / math.tan(self.fov_hor / 2) * \
                 (-1 if self.vec_mult(m_vec, vec_to_point_hor) >= 0 else 1)
        prop_y = 0.5 + math.tan(point_lam_vertical) / math.tan(self.fov_ver / 2) * \
                 (-1 if self.vec_mult(n_vec, vec_to_point_ver) >= 0 else 1)

        if point_lam_horizontal > self.fov_hor / 2 or point_lam_vertical > self.fov_ver / 2:
            prop_x, prop_y = -1, -1

        return prop_x, prop_y

    def __repr__(self):
        props = [f'A: {str(self.a):>10}, O: {str(self.o):>10}',
                 f'vector N: {str(self.vec_n):>10}, vector M: {str(self.vec_m):>10}',
                 f'Alpha: {self.alpha:>10}, Omega: {self.omega:>10}']
        max_l = max(list(map(lambda x: len(x), props)))
        return f'{"-" + "-" * max_l + "-"}\n|{props[0]}|\n|{props[1]}|\n|{props[2]}|\n{"-" + "-" * max_l + "-"}\n'


class Sequance:
    def __init__(self, points, color, cons=()):
        # connections* - cons
        self.cons = cons
        self.points = points
        self.props = list()
        self.color = color

    def get_coords(self, camera):
        self.props.clear()
        for i in self.points:
            if i[0] != -1:
                self.props.append(camera.point_screen_proportion(i))

    def draw(self, screen):
        for i in self.props:
            pygame.draw.circle(screen, self.color, (screen.get_width() * i[0], screen.get_height() * i[1]), 5)
        for i in range(len(self.cons) - 1):
            try:
                pygame.draw.line(screen, self.color,
                                 (screen.get_width() * self.props[self.cons[i]][0], screen.get_height() * self.props[self.cons[i]][1]),
                                 (screen.get_width() * self.props[self.cons[i + 1]][0], screen.get_height() * self.props[self.cons[i + 1]][1]))
            except IndexError:
                pass

    def update(self):
        for i in range(len(self.points)):
            self.points[i] = (self.points[i][0], self.points[i][1], self.points[i][2])


def distance_between_points(point1, point2):
    if isinstance(point1, tuple) and isinstance(point2, tuple):
        return math.sqrt((point1[0] - point2[0]) ** 2 +
                         (point1[1] - point2[1]) ** 2 +
                         (point1[2] - point2[2]) ** 2)
    else:
        return 'not tuples'


if __name__ == "__main__":
    pygame.init()

    size = 1000, 800
    screen = pygame.display.set_mode(size)

    focal_l = 1
    cam_size = (i * 0.02 for i in size)
    fov_hor, fov_ver = (math.atan(i / 2 / focal_l) * 2 for i in cam_size)
    camera = Camera((0, 0, 0), 16, math.pi / 6, math.pi / 7, 1, 1000)

    alpha_add, omega_add = 0.005, 0.005

    seq = Sequance([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], 'red',
                   cons=(0, 1, 2, 3, 0, 4, 5, 6, 7, 4, 5, 1, 2, 6, 7, 3))
    seq2 = Sequance([(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0),
                     (0, 1, 0), (0, 2, 0), (0, 3, 0),
                     (0, 0, 1), (0, 0, 2), (0, 0, 3)], 'blue')

    seq_temp = Sequance([(0, 0, 0), (0, 0, 1)], 'green')

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

                x_hold_start, y_hold_start = pygame.mouse.get_pos()

            if event.type == pygame.MOUSEWHEEL:
                # camera.move(-event.y)
                camera.ao_length += -event.y * camera.move_l
                camera.a_solve()

        seq.get_coords(camera)
        seq2.get_coords(camera)
        seq.draw(screen)
        seq2.draw(screen)
        seq.update()

        seq_temp.get_coords(camera)
        seq_temp.draw(screen)

        camera.update()

        pygame.display.flip()
