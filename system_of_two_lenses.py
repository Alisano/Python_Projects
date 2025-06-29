from alive_progress import alive_bar
from scipy.optimize import fsolve
import math as m
import numpy as np

n1 = 1.551 # BaF2 in 0.85 um 
n2 = 1.452 # BaF2 in 8 um 

h = 25
arr_R_1 = np.arange(h / 2 + 0.5, 101, 1)
arr_R_2 = np.arange(-(h / 2) - 0.5, -101, -1)
h_0 = h / 4
d_window = 5
thick_of_middle_part_of_lens = 0.25
l_F = 1


def focus_one_lens(R_1, R_2, n, thick_of_middle_part_of_lens):
    return 1 / ((n - 1) * (1 / R_1 - 1 / R_2 + (n - 1) * thick_lens(R_1, R_2, thick_of_middle_part_of_lens) / (n * R_1 * R_2)))


def thick_lens(R_1, R_2, thick_of_middle_part_of_lens):
    return thick_of_middle_part_of_lens + (np.abs(R_1) - 0.5 * m.sqrt(4 * R_1 ** 2 - h ** 2)) + (np.abs(R_2) - 0.5 * m.sqrt(4 * R_2 ** 2 - h ** 2))


def S_h(R, R_1, R_2, n, thick_of_middle_part_of_lens):
    return focus_one_lens(R_1, R_2, n, thick_of_middle_part_of_lens) * (n - 1) / (n * np.abs(R)) *  thick_lens(R_1, R_2, thick_of_middle_part_of_lens)


def L(n, R_1, R_2, distance, thick_of_middle_part_of_lens):
    return distance + S_h(R_1, R_1, R_2, n, thick_of_middle_part_of_lens) + S_h(R_2, R_1, R_2, n, thick_of_middle_part_of_lens)


def focus_sum(R_1, R_2, n, distance, thick_of_middle_part_of_lens):
    return 1 / ( 2 / focus_one_lens(R_1, R_2, n, thick_of_middle_part_of_lens) - L(n, R_1, R_2, distance, thick_of_middle_part_of_lens) / (focus_one_lens(R_1, R_2, n, thick_of_middle_part_of_lens)) ** 2 )


def S_F(n, R_1, R_2, distance, thick_of_middle_part_of_lens):
    return (1 - L(n, R_1, R_2, distance, thick_of_middle_part_of_lens) / focus_one_lens(R_1, R_2, n, thick_of_middle_part_of_lens)) * focus_sum(R_1, R_2, n, distance, thick_of_middle_part_of_lens) + S_h(R_1, R_1, R_2, n, thick_of_middle_part_of_lens) 


def S_h_0(R_2):
    return np.abs(R_2) - m.sqrt(R_2 ** 2 - h_0 ** 2)


def F(n, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens):
    return S_F(n, R_1, R_2, distance, thick_of_middle_part_of_lens) + S_h_0(R_2)


def tangens_theta_two(n, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens):
    return m.sqrt(h_0 ** 2 / (n ** 2 * F(n, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens) ** 2 + h_0 ** 2 * (n ** 2 - 1)))


def S_f_n(n, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens):
    return F(n, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens) + d_window - d_window * tangens_theta_two(n, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens) * (F(n, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens) / h_0)


def equations_with_window(var, R_1, R_2):
    distance, x_0 = var
    eq1 = (F(n1, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens) - x_0) * h_0 / (F(n1, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens) * tangens_theta_two(n1, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens)) - d_window
    eq2 = F(n2, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens) - x_0 - d_window * tangens_theta_two(n2, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens) * (F(n2, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens) / h_0) - l_F
    return [eq1, eq2]


def equations_for_two_lenses(distance, R_1, R_2):
    return S_F(n2, R_1, R_2, distance, thick_of_middle_part_of_lens) - S_F(n1, R_1, R_2, distance, thick_of_middle_part_of_lens) - l_F

def resolve_system_nonlinear_eq(only_two_lense, file):
    result_arr = []
    with alive_bar(len(arr_R_1) * len(arr_R_2)) as bar:
        for R_1 in arr_R_1:
            for R_2 in arr_R_2:
                if (only_two_lense):
                    x_0 = S_h_0(R_2)
                    distance = fsolve(equations_for_two_lenses, 1, (R_1, R_2))
                else:
                    distance, x_0 = fsolve(equations_with_window, [1, 1], (R_1, R_2))

                text = output_result(R_1, R_2, distance, x_0)
                if(text is not None):

                    print(text)
                    file.write(text)
                bar()
    return result_arr

def output_result(R_1, R_2, distance, x_0):
    if((S_f_n(n2, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens) - S_f_n(n1, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens) == l_F) and thick_lens(R_1, R_2, thick_of_middle_part_of_lens) < 10 and (x_0 - S_h_0(R_2)) >= 0 and focus_sum(R_1, R_2, n1, distance, thick_of_middle_part_of_lens) > 0 and distance < focus_one_lens(R_1, R_2, n1, thick_of_middle_part_of_lens) and distance > 0):
        return (f"F*_n1 = {F(n1, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens)} F*_n2 = {F(n2, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens)} L_obj = {(S_f_n(n1, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens) - S_h_0(R_2) + distance + 2 * thick_lens(R_1, R_2, thick_of_middle_part_of_lens) - d_window)} F_sum_n1 = {focus_sum(R_1, R_2, n1, distance, thick_of_middle_part_of_lens)} F_sum_n2 = {focus_sum(R_1, R_2, n2, distance, thick_of_middle_part_of_lens)} R_1 = {R_1}, R_2 = {R_2}, distance = {distance}, thick_lenses = {thick_lens(R_1, R_2, thick_of_middle_part_of_lens)}, S_f_n1 = {S_f_n(n1, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens)}, S_f_n2 = {S_f_n(n2, R_1, R_2, h_0, distance, thick_of_middle_part_of_lens)},S_F_n1 = {S_F(n1, R_1, R_2, distance, thick_of_middle_part_of_lens)}, S_F_n2 = {S_F(n2, R_1, R_2, distance, thick_of_middle_part_of_lens)}, x_0 ={x_0}, x = {x_0 - S_h_0(R_2)}, f_n1 = {focus_one_lens(R_1, R_2, n1, thick_of_middle_part_of_lens)}, f_n2 = {focus_one_lens(R_1, R_2, n2, thick_of_middle_part_of_lens)}, S_h_0 ={S_h_0(R_2)}\n")


def main():
    compute_only_two_lense = False
    file = open("./m2_new_result_pyro_IR_BaF2.txt", "w")
    result_arr = resolve_system_nonlinear_eq(compute_only_two_lense, file)
    file.close()

if __name__ == "__main__":
    main()