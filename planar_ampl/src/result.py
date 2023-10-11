from src.library import plt, np
from src.geom import Quad_numba, Triangle_numba

def show_figure(ax, part_share_arr):
    part_share_arr = np.array(part_share_arr)
    particle = np.array([])
    x = np.array([])
    y = np.array([])
    j = 0

    for i, element in enumerate(part_share_arr):
        if (element == -1):
            if (abs(i - j) > 1):
                particle = part_share_arr[j + 1 : i]
                x = particle[::2]
                y = particle[1::2]
                ax.plot(x * 1e6, y * 1e6, color = 'black')
            j = i

def show_contour(phi, particle_counter_dif, time, dxdy_vec, xy_vec, energies):
    ax1 = plt.subplot(221)
    voltage = ax1.contourf(xy_vec[0] * 1e6, xy_vec[1] * 1e6, phi, 30, cmap = 'rainbow')
    E_vec = np.gradient(-phi, dxdy_vec[1], dxdy_vec[0])
    E = np.sqrt(E_vec[0] ** 2 + E_vec[1] ** 2)
    ax1.set_xlabel('Distance, um')
    ax1.set_ylabel('Distance, um')

    ax2 = plt.subplot(222)
    E_field = ax2.contourf(xy_vec[0] * 1e6, xy_vec[1] * 1e6, E, 30, cmap = 'rainbow')
    ax2.streamplot(xy_vec[0] * 1e6, xy_vec[1] * 1e6, E_vec[1], E_vec[0], color = 'black', density = 2.0)
    ax1.set_aspect('equal')
    ax2.set_aspect('equal')
    ax2.set_xlabel('Distance, um')
    ax2.set_ylabel('Distance, um')
    vcolor = plt.colorbar(voltage, ax = ax1, shrink = 0.7)
    vcolor.set_label('V')
    ecolor = plt.colorbar(E_field, ax = ax2, shrink = 0.7)
    ecolor.set_label('V/m')

    ax3 = plt.subplot(223)
    ax3.grid()
    particle_counter = []
    for i, _ in enumerate(particle_counter_dif):
        particle_counter.append(sum(particle_counter_dif[:(i + 1)]))
    ax3.plot(time * 1e12, particle_counter)
    ax3.set_xlabel('Time, ps')
    ax3.set_ylabel('Number of particles on the anode')

    ax4 = plt.subplot(224)
    counts, bins = np.histogram(energies)
    ax4.stairs(counts, bins)
    ax4.hist(bins[:-1], bins, weights=counts, lw=1, ec="yellow", fc="green", alpha=0.5)
    ax4.set_xlabel('Energy, eV')
    ax4.set_ylabel('Number of particles on the anode')
    ax4.set_title(f"$\sigma={np.std(energies)}$ $\mu={np.mean(energies)}$")

    return (ax1, ax2, ax3, ax4)

def union_obj(ax, quads):
    for quad in quads:
        ax[0].plot(np.array(quad.x) * 1e6, np.array(quad.y) * 1e6, color = 'black')
        ax[1].plot(np.array(quad.x) * 1e6, np.array(quad.y) * 1e6, color = 'black')

