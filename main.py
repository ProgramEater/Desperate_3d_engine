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
        a_mao = (math.cos(self.omega) * math.cos(self.alpha) * (self.a[0] - point[0]) +
                 math.cos(self.omega) * math.sin(self.alpha) * (self.a[1] - point[1]) +
                 math.sin(self.omega) * (self.a[2] - point[2]))

        mao = (self.a[0] - a_mao * math.cos(self.alpha) * math.cos(self.omega),
               self.a[1] - a_mao * math.sin(self.alpha) * math.cos(self.omega),
               self.a[2] - a_mao * math.sin(self.omega))

        # possibly error
        mao_m_alpha = math.sin(self.alpha) * (point[0] - mao[0]) - math.cos(self.alpha) * (point[1] - mao[1])
        m_alpha = (mao[0] + math.sin(self.alpha) * mao_m_alpha,
                   mao[1] - math.cos(self.alpha) * mao_m_alpha,
                   mao[2])

        m_omega = (mao[0] + point[0] - m_alpha[0],
                   mao[1] + point[1] - m_alpha[1],
                   point[2])

        # amx angle
        am = distance_between_points((self.a[0], self.a[1], 0), (point[0], point[1], 0))
        amx_angle = 0 if am == 0 else (math.acos((self.a[0] - point[0]) / am) * (-1 if point[1] > self.a[1] else 1))

        # am_omega_xy angle
        am_omega = distance_between_points(self.a, m_omega)
        amxy_angle = 0 if am_omega == 0 else math.acos(math.sqrt((self.a[0] - m_omega[0]) ** 2 + (self.a[1] - m_omega[1]) ** 2) /
                                                       am_omega)

        prop_x = 0.5 + distance_between_points(mao, m_alpha) / \
                 (distance_between_points(self.a, mao) * math.tan(self.fov_hor / 2)) * \
                 (-1 if amx_angle > self.alpha else 1)
        prop_y = 0.5 + distance_between_points(mao, m_omega) / \
                 (distance_between_points(self.a, mao) * math.tan(self.fov_ver / 2)) * (
                     1 if (amxy_angle > self.omega >= 0 or (self.omega < 0 and amxy_angle < abs(self.omega))) else -1)
        return prop_x, prop_y


class Sequance:
    def __init__(self, points, color, cons=()):
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
            self.points[i] = (self.points[i][0], self.points[i][1], self.points[i][2] )


def distance_between_points(point1, point2):
    if isinstance(point1, tuple) and isinstance(point2, tuple):
        return math.sqrt((point1[0] - point2[0]) ** 2 +
                         (point1[1] - point2[1]) ** 2 +
                         (point1[2] - point2[2]) ** 2)
    else:
        return 'not tuples'


if __name__ == "__main__":
    pygame.init()

    size = 720, 460
    screen = pygame.display.set_mode(size)

    focal_l = 1
    cam_size = (i * 0.02 for i in size)
    fov_hor, fov_ver = (math.atan(i / 2 / focal_l) * 2 for i in cam_size)
    camera = Camera((0, 0, 0), 16, math.pi / 6, math.pi / 6, 1, 1000)

    alpha_add, omega_add = 0.005, 0.005

    seq = Sequance([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], 'red',
                   cons=(0, 1, 2, 3, 0, 4, 5, 6, 7, 4, 5, 1, 2, 6, 7, 3))
    seq2 = Sequance([(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0),
                     (0, 1, 0), (0, 2, 0), (0, 3, 0),
                     (0, 0, 1), (0, 0, 2), (0, 0, 3)], 'blue')

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

        seq.get_coords(camera)
        seq2.get_coords(camera)
        seq.draw(screen)
        seq2.draw(screen)
        seq.update()

        pygame.display.flip()
