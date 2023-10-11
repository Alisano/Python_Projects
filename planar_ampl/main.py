from src.library import *
from src.geom import *
from src.study import *
from src.result import *

environ['KMP_WARNINGS'] = 'off'

def main():
    begin_compute = time()

    bias = 80e-6
    points = 1000
    iteration = 10000
    energy1 = 0.01
    vel_x1 = 0
    vel_y1 = -1
    dt = 1e-14
    n_step = 3000
    angle = 0.1

    vel1 = m.sqrt(2 * q * energy1 / m_e)
    vel0_part1 = np.array([vel_x1 * vel1, vel_y1 * vel1])
    time_arr = np.arange(0, n_step * dt, dt)

    width_cathode2 = 5e-6
    height_control2 = 2e-6
    cathode_control_gap = 5e-6
    electrodes_distance = 35e-6
    bar_el_dinode_displacement_y = 7e-6
    bar_el_dinode_displacement_x = 10e-6
    delta_V = 500
    dinode_V0 = 250
    control_potenitial = 50
    cathode_potential = 0
    downer_dinode_control_displacement_x = 20e-6
    downer_dinode_control_displacement_y = 35e-6
    bar_el_anode_displacement_x = 15.5e-6
    displacement_dinodes_x = -2.5e-6
    displacement_dinodes_y = 26e-6
    electrodes_height = 60e-6
    dinode_width = 30e-6
    dinode_height = 36e-6
    control_needle_width = 20e-6 
    anode_y_displacement = -electrodes_height / 2 + 4e-6
    bar_el_height = 60e-6

    control1 = InterfaceGeom.createQuad(0, 0, 140e-6, electrodes_height, 0)
    control_needle = InterfaceGeom.createQuad(control1.xend, control1.yend - height_control2, control_needle_width, height_control2, angle)
    height_cathode2 = electrodes_distance - control_needle.width * np.tan(angle) - cathode_control_gap / np.cos(angle)
    cathode1 = InterfaceGeom.createQuad(0, control1.yend + electrodes_distance, control1.xend + control_needle.width, 48e-6, 0)
    cathode_needle = InterfaceGeom.createQuad(cathode1.xend - width_cathode2, cathode1.y0 - height_cathode2, width_cathode2, height_cathode2, 0)
    dinode1 = InterfaceGeom.createQuad(control1.xend + downer_dinode_control_displacement_x, control_needle.y0 - downer_dinode_control_displacement_y - dinode_height, dinode_width, dinode_height, 0)
    dinode2 = InterfaceGeom.createQuad(dinode1.xend + displacement_dinodes_x, displacement_dinodes_y + dinode1.height, dinode1.width, dinode1.height, 0)
    bar1 = InterfaceGeom.createQuad(dinode1.xend + bar_el_dinode_displacement_x, dinode1.yend - bar_el_height - bar_el_dinode_displacement_y, 5e-6, bar_el_height, 0)
    bar0 = InterfaceGeom.createQuad(dinode2.x0 - bar1.width - bar_el_dinode_displacement_x, dinode2.y0 + bar_el_dinode_displacement_y, bar1.width, bar1.height, 0)
    anode = InterfaceGeom.createQuad(bar1.xend + bar_el_anode_displacement_x, anode_y_displacement, 100e-6, electrodes_height, 0)
    
    dinode1_triangle = InterfaceGeom.createTriangle(dinode1.x0, dinode1.yend, dinode1.width, pi / 2, angle, 0)
    dinode2_triangle = InterfaceGeom.createTriangle(dinode2.x0, dinode2.y0, dinode2.width, -pi / 2, - angle, 0)
    cathode_triangle = InterfaceGeom.createTriangle(cathode_needle.x0, cathode_needle.y0, width_cathode2, -pi / 2, -angle, 0)
    
    x_pos1  = cathode_needle.xend - width_cathode2 / 2
    y_pos1 = cathode_triangle.y0
    pos0_part1 = np.array([x_pos1, y_pos1])

    cathode1.potential = cathode_potential
    dinode1.potential = dinode_V0
    control1.potential = control_potenitial
    cathode_needle.potential = cathode1.potential
    cathode_triangle.potential = cathode1.potential
    dinode2.potential = dinode1.potential + delta_V
    control_needle.potential = control1.potential
    anode.potential = dinode1.potential + 2 * delta_V
    bar1.potential = dinode1.potential
    bar0.potential = cathode1.potential
    dinode1_triangle.potential = dinode1.potential
    dinode2_triangle.potential = dinode2.potential

    objects =  [cathode1, cathode_needle, control1, control_needle, dinode1,\
                dinode2, anode, bar1, bar0, dinode1_triangle, dinode2_triangle, cathode_triangle]

    dinode1.is_emissive = True
    dinode2.is_emissive = True
    dinode1_triangle.is_emissive = True
    dinode2_triangle.is_emissive = True

    anode.energy_dist = True
    anode.endobj = True

    #=======================Study============================
    phi_mesh, dxdy_vec, xy_vec = mesh(bias, points, objects)


    objects =  [cathode1, cathode_needle, control1, control_needle, dinode1,\
            dinode2, anode, bar1, bar0, dinode1_triangle, dinode2_triangle, cathode_triangle]
    
    phi = potential(phi_mesh, iteration, dxdy_vec, objects, bias)

    objects =  [cathode1, cathode_needle, control1, control_needle, dinode1,\
        dinode2, anode, bar1, bar0, dinode1_triangle, dinode2_triangle, cathode_triangle]

    objects.remove(control_needle)

    part_share_arr = [0.1]
    energies = [0.0]
    particle_counter= []
    particle_counter.extend([0] * len(time_arr)) 

    traj(bias, pos0_part1, time_arr, dt, dxdy_vec, phi, vel0_part1, objects, part_share_arr, particle_counter, energies)

    #=======================Result============================
    ax = show_contour(phi, particle_counter, time_arr, dxdy_vec, xy_vec, energies)
    objects.append(control_needle)
    
    print(time() - begin_compute, "s")

    show_figure(ax[0], part_share_arr)
    union_obj(ax, objects)
    plt.show()

if __name__ == "__main__":
    main()
