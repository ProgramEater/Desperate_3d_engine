import math
from main import distance_between_points


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
    amxy_angle = 0 if am_omega == 0 else math.acos(
        math.sqrt((self.a[0] - m_omega[0]) ** 2 + (self.a[1] - m_omega[1]) ** 2) /
        am_omega)

    prop_x = 0.5 + distance_between_points(mao, m_alpha) / \
             (distance_between_points(self.a, mao) * math.tan(self.fov_hor / 2)) * \
             (-1 if amx_angle > self.alpha else 1)
    prop_y = 0.5 + distance_between_points(mao, m_omega) / \
             (distance_between_points(self.a, mao) * math.tan(self.fov_ver / 2)) * (
                 1 if (amxy_angle > self.omega >= 0 or (self.omega < 0 and amxy_angle < abs(self.omega))) else -1)
    return prop_x, prop_y