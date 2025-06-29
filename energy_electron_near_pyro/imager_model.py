import math as m
import numpy as np
from scipy.misc import derivative
import matplotlib.pyplot as plt
import time
import subprocess

'''
Here is 2-D colour float of surface contour of 3-D functional dependency of the pyroelectric voltage
on grid and silicon voltages.
'''

#=========================initial parameters==========================

epsilon_0 = 8.85 * 10 ** (-12) # F/m

epsilon_vac = 1
epsilon_pyro = 1704
epsilon_sio2 = 4.2
# epsilon_si = 11.7

d_si = 35 * 10 ** (-6)
d_vac_ph = 0.6 * 10 ** (-3)
d_vac_grid = 0.4 * 10 ** (-3)
d_grid = 35 * 10 ** (-6)
d_pyro = 10 ** (-6)
d_sio2 = 10 ** (-6)

d_sum = d_vac_grid + d_si + d_pyro + d_sio2 + d_grid + d_vac_ph

R = 12 * 10 ** (-3)
S = m.pi * R ** 2

m_e = 9.1 * 10 ** (-31)
q = 1.602 * 10 ** (-19)

C_pyro = epsilon_0 * epsilon_pyro * S / d_pyro # F
C_sio2 = epsilon_0 * epsilon_sio2 * S / d_sio2 # F
C_vac = epsilon_0 * epsilon_vac * S / d_vac_grid # F
C_tot = (C_sio2 * C_pyro * C_vac) / (C_sio2 + C_pyro + C_vac)

INIT_ELECTRON_ENERGY = 0.1 # eV

#==============================methods===================================

def potential(x ,voltages):
    a_si, a_sio2, a_pyro, a_vac_grid, a_grid, \
    a_ph, b_si, b_sio2, b_pyro, b_vac_grid, b_grid, b_ph = linear_coefficient(voltages)
    if x >= 0 and x <= d_si:
        return a_si * x + b_si
    if x > d_si and x <= (d_si + d_sio2):
        return a_sio2 * x + b_sio2
    if x > (d_si + d_sio2) and x <= (d_si + d_sio2 + d_pyro):
        return a_pyro * x + b_pyro
    if x > (d_si + d_sio2 + d_pyro) and x <= (d_si + d_sio2 + d_pyro + d_vac_grid):
        return a_vac_grid * x + b_vac_grid
    if x > (d_si + d_sio2 + d_pyro) and x <= (d_si + d_sio2 + d_pyro + d_vac_grid + d_grid):
        return a_grid * x + b_grid
    if x > (d_si + d_sio2 + d_pyro + d_vac_grid + d_grid) and x <= (d_si + d_sio2 + d_pyro + d_vac_grid + d_vac_ph + d_grid):
        return a_ph * x + b_ph

def electrons_energy(electic_field, dz, z):
    summ = INIT_ELECTRON_ENERGY
    electic_field = np.flip(electic_field)
    electron_energy = np.array([INIT_ELECTRON_ENERGY])
    for i in range(1, len(z)):
        summ += electic_field[i] * dz
        electron_energy = np.append(electron_energy, summ)

    return np.flip(electron_energy)

def linear_coefficient (voltages):
    (v_si, v_grid, v_ph, v_pyro, delta_pyro) = voltages
    a_si = 0
    b_si = v_si

    a_sio2 = (delta_pyro + v_pyro - v_si) / d_sio2
    b_sio2 = v_si - a_sio2 * d_si

    a_pyro = -delta_pyro / d_pyro
    b_pyro = (delta_pyro + v_pyro) - a_pyro * (d_si + d_sio2)

    a_vac_grid = (v_grid - v_pyro) / d_vac_grid
    b_vac_grid = v_pyro - a_vac_grid * (d_si + d_pyro + d_sio2)

    a_grid = 0
    b_grid = v_grid

    a_ph = (v_ph - v_grid) / d_vac_ph
    b_ph = v_grid - a_ph * (d_vac_grid + d_si + d_pyro + d_sio2 + d_grid)

    return a_si, a_sio2, a_pyro, a_vac_grid, a_grid, a_ph, b_si, b_sio2, b_pyro, b_vac_grid, b_grid, b_ph

#===============================plotting figures========================================

def plot2Dfigures(z, potentinals, electron_energies, array_voltages, array_of_min_z, array_of_min_energies):
    v_grid, v_pyro = array_voltages

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2)

    ax1.plot(z * 1000, potentinals)
    ax1.set_xlabel('$z, mm$')
    ax1.set_ylabel('$\phi(z), V$')
    ax1.plot(z * 1000, np.zeros(len(z)), '--')
    ax1.grid()
    
    ax2.plot(z * 1000, electron_energies)
    ax2.set_xlabel('$z, mm$')
    ax2.set_ylabel('$\epsilon(z), eV$')
    ax2.plot(z * 1000, np.zeros(len(z)), '--')
    ax2.grid()

    cs = ax3.contourf(v_pyro, v_grid, array_of_min_z * 10 ** 6, cmap=plt.cm.jet, zorder = 1)
    ax3.set_xlabel('$V_{Pyro}, V$')
    ax3.set_ylabel('$V_{Grid}, V$')
    cbar = fig.colorbar(cs)
    cbar.set_label('distance, um')

    cs = ax4.contourf(v_pyro, v_grid, array_of_min_energies * 10 ** 6, cmap=plt.cm.jet, zorder = 1)
    ax4.set_xlabel('$V_{Pyro}, V$')
    ax4.set_ylabel('$V_{Grid}, V$')
    cbar = fig.colorbar(cs)
    cbar.set_label('$\epsilon$, ueV')   

    print("--- %s seconds ---" % (time.time() - start_time))
    plt.show()

#===============================main function=======================================

def main():

    v_ph =  - 0.1 # V
    v_grid = 1.98 # V
    v_si = 2 # V
    v_pyro = -0.5 # V
    delta_pyro = 2 # V
    dz = 10 ** (-7)
    z = np.arange(10 ** (-7), d_sum, dz) # V

    voltages = (v_si, v_grid, v_ph, v_pyro, delta_pyro)
    potentinals = np.array([potential(x, voltages) for x in z])
    electic_field = np.array([-1 * derivative(potential, x, dx=1e-8, args= [voltages]) for x in z])
    electron_energies = electrons_energy(electic_field, dz, z)

#==============================2-D Countour of distance with minimal electron energy vs various voltages===========================

    v_ph =  - 0.1
    v_grid = 1.98
    v_si = 2
    v_pyro = -0.5
    delta_pyro = 1
    dz = 1e-9
    start_z = 1e-9
    dx = 1e-10

    v_start_grid = 0 
    v_stop_grid = 2
    v_step_grid = 0.025

    v_start_pyro = -0.2 
    v_stop_pyro = -0.4
    v_step_pyro = -0.0025

    num_thread = 8
    Cut_array_step = 1e-4
    Cut_multiply_step = 1

    cmd_param = f'{v_ph} {v_grid} {v_si} {v_pyro} {delta_pyro} {dz} {start_z} {dx} {v_start_grid} {v_stop_grid} {v_step_grid} {v_start_pyro} {v_stop_pyro} {v_step_pyro} {num_thread} {Cut_array_step} {Cut_multiply_step}' 
    cmd = f'/Users/alexandrpopov/Documents/Scripts/figure_model/array_figures_min_step {cmd_param}'

    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    result = process.communicate()[0]

    array_of_min_z = np.array([])
    array_of_min_energies = np.array([])

    v_grid = np.array([])
    v_pyro = np.array([])

    i = v_start_grid
    while (i < v_stop_grid):
        v_grid = np.append(v_grid, i)
        i+=v_step_grid
 
    i = v_start_pyro

    while (i > v_stop_pyro):
        v_pyro = np.append(v_pyro, i)
        i+=v_step_pyro

    for i in range(len(result.split())):
        if (i >= (len(v_grid) * len(v_pyro))):
            array_of_min_energies = np.append(array_of_min_energies, float(result.split()[i]))
        else:
            array_of_min_z = np.append(array_of_min_z, float(result.split()[i]))

    array_of_min_z = array_of_min_z.reshape(len(v_grid), len(v_pyro))
    array_of_min_energies = array_of_min_energies.reshape(len(v_grid), len(v_pyro))

#===================================Plot result=====================================================
    array_voltages = (v_grid, v_pyro)
    dz = 10 ** (-7)
    z = np.arange(10 ** (-7), d_sum, dz) # m
    plot2Dfigures(z, potentinals, electron_energies, array_voltages, array_of_min_z, array_of_min_energies)
#========================================================================================

if __name__ == '__main__':
    start_time = time.time()
    main()