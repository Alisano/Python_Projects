from src.library import np, convolve, m_e, q, pi, triangular, njit, linalg, NumbaDeprecationWarning, NumbaPendingDeprecationWarning, simplefilter, gradient

simplefilter('ignore', category=NumbaDeprecationWarning)
simplefilter('ignore', category=NumbaPendingDeprecationWarning)

def potential(phi, iteration, dxdy_vec, quads, bias):
    kern = np.array([[0, 0.25, 0], [0.25, 0, 0.25], [0, 0.25, 0]])
    for _ in range(iteration):
        phi = convolve(phi, kern, mode='constant', cval=0.0)
        for quad in quads:
            phi = quad.potential_mask(phi, dxdy_vec, bias)
            phi = neumann(phi)
    return phi

def mesh(bias, points, quads):
    max_xend = max(quads, key = lambda x: x.xend).xend
    max_yend = max(quads, key = lambda x: x.yend).yend
    aspect_ratio = (max_yend + 2 * bias) / (max_xend + 2 * bias)
    x_array = np.linspace(-bias, max_xend + bias, points)
    y_array = np.linspace(-bias, max_yend + bias, int(aspect_ratio * points))
    xy_vec = np.meshgrid(x_array, y_array)
    dxdy_vec = ((max_xend + 2 * bias)/ len(x_array), (max_yend + 2 * bias) / len(y_array))
    phi = np.zeros((len(y_array),len(x_array)))
    return phi, dxdy_vec, xy_vec

@njit()
def traj(bias, pos_part, time_arr, dt, dxdy_vec, phi, vel0_part, objects, part_share_arr, particle_counter, energies):
    result = [0.0]
    old_vel_x = vel0_part[1]
    old_vel_y = vel0_part[0]

    for t in time_arr:
        j = int(abs(pos_part[0] + bias) / dxdy_vec[0])
        i = int(abs(pos_part[1] + bias) / dxdy_vec[1])

        result.append(pos_part[0])
        result.append(pos_part[1])

        for obj in objects:
            if (obj.intersect_mask_quad_xy(pos_part) or (i >= (phi.shape[0] - 1)) or (j >= (phi.shape[1] - 1))):
                if (not list(result)) :
                    result.append(pos_part[0])
                    result.append(pos_part[1])

                if(obj.energy_dist):
                    part_energy = m_e * (old_vel_x ** 2 + old_vel_y ** 2) / (2 * q)
                    energies.append(part_energy)

                if(obj.endobj):
                    result.append(-1.0)
                    for i, element in enumerate(result):
                        if (i > 0):
                            part_share_arr.append(element)

                    particle_counter[np.where(time_arr == t)[0][0]] += 1
                    return
                
                if (obj.is_emissive):
                    vel_xy = np.array([old_vel_x, old_vel_y])
                    intersect_emission(vel_xy, bias, pos_part, time_arr, dt, dxdy_vec, phi, vel0_part, objects, part_share_arr, particle_counter, obj, energies)

                result.append(-1.0)
                for i, element in enumerate(result):
                    if (i > 0):
                        part_share_arr.append(element)
                return

        old_vel_x += -1 * q * electric_field(pos_part, phi, bias, dxdy_vec)[0] * dt / m_e
        old_vel_y += -1 * q * electric_field(pos_part, phi, bias, dxdy_vec)[1] * dt / m_e
        pos_part[0] += old_vel_x * dt
        pos_part[1] += old_vel_y * dt

    result.append(-1.0)
    for i, element in enumerate(result):
        if (i > 0):
            part_share_arr.append(element)

@njit()
def intersect_emission(vel_xy, bias, pos0_part, time_arr, dt, dxdy_vec, phi, vel0_part, objects, part_share_arr, particle_counter, obj_emission, energies):
    energy = m_e * (vel_xy[0] ** 2 + vel_xy[1] ** 2) / 2
    pair_formation_energy = 10
    part_energy = energy / q
    n_sec = part_energy / pair_formation_energy
    vel_sec = 5.5e5
    l_new_pos = 1e-7
    tmp = pos0_part
    for _ in range(int(n_sec)):
        alpha = alpha_compute(pos0_part, obj_emission)
        angle = angle_compute(vel_xy, alpha)
        pos0_part = [pos0_part[0] + l_new_pos * np.cos(angle), pos0_part[1] + l_new_pos * np.sin(angle)]
        vel0_part = [vel_sec * np.cos(angle), vel_sec * np.sin(angle)]
        traj(bias, pos0_part, time_arr, dt, dxdy_vec, phi, vel0_part, objects, part_share_arr, particle_counter, energies)

        pos0_part = tmp

@njit()
def angle_compute(vel_xy, alpha):
    if ((alpha != 0) and (vel_xy[1] > 0)):
        return triangular(alpha - pi, alpha)
    elif((vel_xy[0] > 0) and (alpha != 0)):
        return triangular(alpha, pi + alpha)
    elif((vel_xy[1] < 0) and (alpha == 0)):
        return triangular(alpha, pi + alpha)
    elif((vel_xy[0] < 0) and (alpha != 0)):
        return triangular(alpha - pi, alpha)
    elif((vel_xy[1] > 0) and (alpha == 0)):
        return triangular(alpha - pi, alpha)

@njit()
def alpha_compute(pos_part, quad):
    coord = []
    norm = []
 
    for x, y in zip(quad.x, quad.y):
        coord.append([x, y])

    for i in range(len(coord) - 1):
        a = np.sqrt((pos_part[0] - coord[i + 1][0]) ** 2 + (pos_part[1] - coord[i + 1][1]) ** 2)
        b = np.sqrt((coord[i][0] - pos_part[0]) ** 2 + (coord[i][1] - pos_part[1]) ** 2)
        c = np.sqrt((coord[i][0] - coord[i + 1][0]) ** 2 + (coord[i][1] - coord[i + 1][1]) ** 2)
        p = (a + b + c) / 2
        s = np.sqrt(p * (p - a) * (p - b) * (p - c))
        h = 2 * s / c
        norm.append(h)
    min_line = norm.index(min(norm))

    if ((coord[min_line + 1][0] - coord[min_line][0]) != 0):
        alpha = (np.arctan((coord[min_line + 1][1] - coord[min_line][1]) / (coord[min_line + 1][0] - coord[min_line][0])))
    else:
        alpha = pi / 2

    return alpha

@njit()
def neumann(phi):
    for i in range(phi.shape[1]):
        phi[0, i] = phi[1, i]
        phi[-1, i] = phi[-2, i]
    for i in range(phi.shape[0]):
        phi[i, 0] = phi[i, 1]
        phi[i, -1] = phi[i, -2]
    return phi

@njit()
def electric_field(pos_part, phi, bias, dxdy_vec):
    j = int(abs(pos_part[0] + bias) / dxdy_vec[0])
    i = int(abs(pos_part[1] + bias) / dxdy_vec[1])

    point1 = (j * dxdy_vec[0] - bias, i * dxdy_vec[1] - bias)
    if ((i < (phi.shape[0] - 1)) and (j < (phi.shape[1] - 1))):
        point2 = ((j + 1) * dxdy_vec[0] - bias, (i + 1) * dxdy_vec[1] - bias)
        point3 = ((j + 1) * dxdy_vec[0] - bias, i * dxdy_vec[1] - bias)
        point4 = (j * dxdy_vec[0] - bias, (i + 1) * dxdy_vec[1] - bias)

        l1 = np.sqrt((point1[0] - pos_part[0]) ** 2 + (point1[1] - pos_part[1]) ** 2)
        l2 = np.sqrt((point2[0] - pos_part[0]) ** 2 + (point2[1] - pos_part[1]) ** 2)

        if (l1 > l2):
            coord = np.array([[point2[0], point2[1], point2[0] * point2[1]], 
                            [point3[0], point3[1], point3[0] * point3[1]], 
                            [point4[0], point4[1], point4[0] * point4[1]]]) 
            phi =  np.array([phi[i + 1, j + 1], phi[i, j + 1], phi[i + 1, j]])
            coef = linalg.solve(coord, phi)
            return [-1 * (coef[0] + coef[2] * pos_part[1]), -1 * (coef[1] + coef[2] * pos_part[0])]
        else:
            coord = np.array([[point1[0], point1[1], point1[0] * point1[1]], 
                            [point3[0], point3[1], point3[0] * point3[1]], 
                            [point4[0], point4[1], point4[0] * point4[1]]]) 
            phi =  np.array([phi[i, j], phi[i, j + 1], phi[i + 1, j]])
            coef = linalg.solve(coord, phi)
            return [-1 * (coef[0] + coef[2] * pos_part[1]), -1 * (coef[1] + coef[2] * pos_part[0])]
    
    elif ((i == (phi.shape[0] - 1)) and (j == (phi.shape[1] - 1))):
        point2 = ((j - 1) * dxdy_vec[0] - bias, i * dxdy_vec[1] - bias)
        point3 = (j * dxdy_vec[0] - bias, (i - 1) * dxdy_vec[1] - bias)
        coord = np.array([[point1[0], point1[1], point1[0] * point1[1]], 
                        [point2[0], point2[1], point2[0] * point2[1]], 
                        [point3[0], point3[1], point3[0] * point3[1]]]) 
        phi =  np.array([phi[i, j], phi[i, j - 1], phi[i - 1, j]])
        coef = linalg.solve(coord, phi)
        return [-1 * (coef[0] + coef[2] * pos_part[1]), -1 * (coef[1] + coef[2] * pos_part[0])]
    
    elif ((j == (phi.shape[1] - 1))):
        point2 = ((j - 1) * dxdy_vec[0] - bias, i * dxdy_vec[1] - bias)
        point3 = (j * dxdy_vec[0] - bias, (i + 1) * dxdy_vec[1] - bias)
        coord = np.array([[point1[0], point1[1], point1[0] * point1[1]], 
                        [point2[0], point2[1], point2[0] * point2[1]], 
                        [point3[0], point3[1], point3[0] * point3[1]]]) 
        phi =  np.array([phi[i, j], phi[i, j - 1], phi[i + 1, j]])
        coef = linalg.solve(coord, phi)
        return [-1 * (coef[0] + coef[2] * pos_part[1]), -1 * (coef[1] + coef[2] * pos_part[0])]
    else:
        point2 = ((j + 1) * dxdy_vec[0] - bias, i * dxdy_vec[1] - bias)
        point3 = (j * dxdy_vec[0] - bias, (i - 1) * dxdy_vec[1] - bias)
        coord = np.array([[point1[0], point1[1], point1[0] * point1[1]], 
                        [point2[0], point2[1], point2[0] * point2[1]], 
                        [point3[0], point3[1], point3[0] * point3[1]]]) 
        phi =  np.array([phi[i, j], phi[i, j + 1], phi[i - 1, j]])
        coef = linalg.solve(coord, phi)
        return [-1 * (coef[0] + coef[2] * pos_part[1]), -1 * (coef[1] + coef[2] * pos_part[0])]