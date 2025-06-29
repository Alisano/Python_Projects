#include <vector>
#include <math.h>
#include <algorithm>
#include <fstream>
#include <iterator>
#include <iostream>
#include <stdio.h>
#include <thread>

double d_si = 35e-6;
double d_vac_ph = 0.6e-3;
double d_vac_grid = 0.4e-3;
double d_grid = 35e-6;
double d_pyro = 1e-6;
double d_sio2 = 1e-6;
double d_sum = d_vac_grid + d_si + d_pyro + d_sio2 + d_grid + d_vac_ph;
double q = 1.602e-19;
double INIT_ELECTRON_ENERGY = 0.1;
double um = 1e6;

double derivative(double x, double* voltages, std::function<double(double x, double* voltages)> func, double dx);
double potential(double x, double* voltages);
std::vector<double> electrons_energy(std::vector<double> electic_field, double* dz, std::vector<double> z);
std::vector<double> linear_coefficient (double* voltages);
void text_results_writer(std::vector<std::vector<double>> results);
void gnu_plot_figure(std::vector<double>x, std::vector<double> y);
double linear_electric_field(double x, double* voltages);
std::vector<std::vector<double>> parallel_runner(int num_thread, double* voltages, std::vector<double> z, double* dz, double dx, double* v_grid_param, double* v_pyro_param);
void arrays_min_energy_and_distance(double a, double b, std::vector<double>& v_grid,std::vector<double>& v_pyro, double* voltages, double& reference_frame_shift, double* dz, std::vector<double> z, double delta_z_max_dist, std::vector<double>& array_of_min_z, std::vector<double>& array_of_min_energies);

int main(int argc, char *argv[])
{

    double v_ph;
    double v_grid;
    double v_si;
    double v_pyro;
    double delta_pyro;
    double start_z;
    double dx;

    double v_start_grid; 
    double v_stop_grid; 
    double v_step_grid;

    double v_start_pyro; 
    double v_stop_pyro; 
    double v_step_pyro;

    double Cut_array_step = 1e-4;
    double Cut_multiply_step = 1;
    double dz[3] = {Cut_array_step, Cut_multiply_step, 1e-9};

    int num_thread;

    if ((argc == 16) or (argc == 18)){
        v_ph =  atof(argv[1]);
        v_grid = atof(argv[2]);
        v_si = atof(argv[3]);
        v_pyro = atof(argv[4]);
        delta_pyro = atof(argv[5]);
        dz[2] = atof(argv[6]);
        start_z = atof(argv[7]);
        dx = atof(argv[8]);
        v_start_grid = atof(argv[9]);
        v_stop_grid = atof(argv[10]);
        v_step_grid = atof(argv[11]);
        v_start_pyro = atof(argv[12]);
        v_stop_pyro = atof(argv[13]);
        v_step_pyro = atof(argv[14]);
        num_thread = atof(argv[15]);
        if(argc == 18){
            dz[0] = atof(argv[16]);
            dz[1] = atof(argv[17]);           
        }
    } else {
        v_ph =  - 0.1;
        v_grid = 1.98;
        v_si = 2;
        v_pyro = -0.5;
        delta_pyro = 1;
        start_z = 1e-9;
        dx = 1e-10;

        // v_start_grid = 1.8; 
        // v_stop_grid = 2; 
        // v_step_grid = 0.001;

        // v_start_pyro = -0.5; 
        // v_stop_pyro = -0.52; 
        // v_step_pyro = -0.0001;

        v_start_grid = 0; 
        v_stop_grid = 2; 
        v_step_grid = 0.025;

        v_start_pyro = -0.2; 
        v_stop_pyro = -0.4; 
        v_step_pyro = -0.0025;    

        dz[2] = 1e-9;
        num_thread = 8;
    }

    std::vector<double> z;
    double k = 1;

    for (double i = start_z; i < d_sum; i += k*dz[2]){
        z.push_back(i);
        if(i > dz[0])
            k = dz[1];
    }
    
    double voltages[] = {v_si, v_grid, v_ph, v_pyro, delta_pyro};
    double v_grid_param[] = {v_start_grid, v_stop_grid, v_step_grid};
    double v_pyro_param[] = {v_start_pyro, v_stop_pyro, v_step_pyro};

    std::vector<std::vector<double>> results = parallel_runner(num_thread, voltages, z, dz, dx, v_grid_param, v_pyro_param);
    // text_results_writer(results);
    for(auto i: results){
        for(auto j: i)
            std::cout<<j<<' ';
    }

    return 0;
}

double derivative(double x, double* voltages, std::function<double(double x, double* voltages)> func, double dx){
    return (potential(x+dx, voltages) - potential(x-dx, voltages)) / (2*dx);
}

double potential(double x, double* voltages){
    std::vector<double> coef = linear_coefficient(voltages);
    if ((x >= 0) && (x <= d_si))
        return coef[0] * x + coef[6];
    else if ((x > d_si) && (x <= (d_si + d_sio2)))
        return coef[1] * x + coef[7];
    else if ((x > (d_si + d_sio2)) && (x <= (d_si + d_sio2 + d_pyro)))
        return coef[2] * x + coef[8];
    else if ((x > (d_si + d_sio2 + d_pyro)) && (x <= (d_si + d_sio2 + d_pyro + d_vac_grid)))
        return coef[3]* x + coef[9];
    else if ((x > (d_si + d_sio2 + d_pyro)) && (x <= (d_si + d_sio2 + d_pyro + d_vac_grid + d_grid)))
        return coef[4] * x + coef[10];
    else
        return coef[5] * x + coef[11];
}

std::vector<double> electrons_energy(std::vector<double> electic_field, double* dz, std::vector<double> z){
    double summ = INIT_ELECTRON_ENERGY;
    std::reverse(electic_field.begin(), electic_field.end());
    electic_field.push_back(INIT_ELECTRON_ENERGY);
    std::vector<double> electron_energy;

    for (int i = 1; i < z.size(); i++) {
        if(z[i] > dz[0])
            summ += electic_field[i]*dz[1]*dz[2];
        else
            summ += electic_field[i]*dz[2];
        electron_energy.push_back(abs(summ));
    }
    std::reverse(electron_energy.begin(), electron_energy.end());
    return electron_energy;
}

std::vector<double> linear_coefficient (double* voltages){
    double a_si = 0;
    double b_si = voltages[0];

    double a_sio2 = (voltages[4] + voltages[3] - voltages[0]) / d_sio2;
    double b_sio2 = voltages[0] - a_sio2 * d_si;

    double a_pyro = -voltages[4] / d_pyro;
    double b_pyro = (voltages[4] + voltages[3]) - a_pyro * (d_si + d_sio2);

    double a_vac_grid = (voltages[1] - voltages[3]) / d_vac_grid;
    double b_vac_grid = voltages[3] - a_vac_grid * (d_si + d_pyro + d_sio2);

    double a_grid = 0;
    double b_grid = voltages[1];

    double a_ph = (voltages[2] - voltages[1]) / d_vac_ph;
    double b_ph = voltages[1] - a_ph * (d_vac_grid + d_si + d_pyro + d_sio2 + d_grid);

    std::vector<double> coef = {a_si, a_sio2, a_pyro, a_vac_grid, a_grid, a_ph, b_si, b_sio2, b_pyro, b_vac_grid, b_grid, b_ph};
    return coef;
}

void text_results_writer(std::vector<std::vector<double>> results){
    std::vector<double> array_of_min_z = results[0];
    std::vector<double> array_of_min_energies = results[1];

    std::ofstream output_file_1("./min_energy.txt");
    std::ostream_iterator<double> output_iterator_1(output_file_1, "\n");
    std::copy(array_of_min_energies.begin(), array_of_min_energies.end(), output_iterator_1);

    std::ofstream output_file_2("./min_distance.txt");
    std::ostream_iterator<double> output_iterator_2(output_file_2, "\n");
    std::copy(array_of_min_z.begin(), array_of_min_z.end(), output_iterator_2);
}

void gnu_plot_figure(std::vector<double> x, std::vector<double> y){
    FILE *gnupipe = NULL;
    const char* GnuCommands[] = {"plot 'data.tmp' linetype 7 linecolor 0 with lines"};;
    gnupipe = popen("gnuplot -persitent", "w");

    std::ofstream fp;
    fp.open("./data.tmp");
    for(int i = 0; i < (x.size()); i++)
        fp << x[i] << " " << y[i] << "\n";
    fp.close();
    fprintf(gnupipe, "%s\n", GnuCommands[0]);
}

double linear_electric_field(double x, double* voltages){
    std::vector<double> coef = linear_coefficient(voltages);
    if ((x >= 0) && (x <= d_si))
        return -coef[0];
    else if ((x > d_si) && (x <= (d_si + d_sio2)))
        return -coef[1];
    else if ((x > (d_si + d_sio2)) && (x <= (d_si + d_sio2 + d_pyro)))
        return -coef[2];
    else if ((x > (d_si + d_sio2 + d_pyro)) && (x <= (d_si + d_sio2 + d_pyro + d_vac_grid)))
        return -coef[3];
    else if ((x > (d_si + d_sio2 + d_pyro)) && (x <= (d_si + d_sio2 + d_pyro + d_vac_grid + d_grid)))
        return -coef[4];
    else
        return -coef[5];
}

std::vector<std::vector<double>> parallel_runner(int num_thread, double* voltages, std::vector<double> z, double* dz, double dx, double* v_grid_param, double* v_pyro_param){
    std::vector<double> v_grid;
    std::vector<double> v_pyro;
    
    for (double i = v_grid_param[0]; i < v_grid_param[1]; i+=v_grid_param[2])
        v_grid.push_back(i);
 
    for (double i = v_pyro_param[0]; i > v_pyro_param[1]; i+=v_pyro_param[2])
        v_pyro.push_back(i);

    double reference_frame_shift = d_si + d_pyro + d_sio2;
    double delta_z_max_dist = 1e-04;

    std::vector<double> array_of_min_z(v_grid.size()*v_pyro.size());
    std::vector<double> array_of_min_energies(v_grid.size()*v_pyro.size());

    std::vector<std::thread> thread_arr(num_thread);

    for(int i = 0; i < num_thread; i++) {
        thread_arr[i] = (std::thread ([=, &array_of_min_z, &array_of_min_energies, &v_grid, &v_pyro, & reference_frame_shift](){arrays_min_energy_and_distance(i+1, num_thread, v_grid, v_pyro, voltages, reference_frame_shift, dz, z, delta_z_max_dist, array_of_min_z, array_of_min_energies);}));
    }

    for(int i = 0; i < num_thread; i++) {
        thread_arr[i].join();
    }

    std::vector<std::vector<double>> result = {array_of_min_z, array_of_min_energies};

    return result;
}
  
void arrays_min_energy_and_distance(double a, double b, std::vector<double>& v_grid,std::vector<double>& v_pyro, double* voltages, double& reference_frame_shift, double* dz, std::vector<double> z, double delta_z_max_dist, std::vector<double>& array_of_min_z, std::vector<double>& array_of_min_energies){

    for(int i = int((a-1)*v_grid.size()/b); i < int(a*v_grid.size()/b); i++){
        for(int j = 0; j < v_pyro.size(); j++){
            double new_voltages[5] = {voltages[0], v_grid[i], voltages[2], v_pyro[j], voltages[4]};
            double energy_min = 1;
            double energy_min_dist = 1;
            double summ = INIT_ELECTRON_ENERGY;

            for (int k = 1; k < z.size(); k++) {
                if(z[i] > dz[0])
                    summ += linear_electric_field(z[z.size() - k - 1], new_voltages)*dz[1]*dz[2];
                else
                    summ += linear_electric_field(z[z.size() - k - 1], new_voltages)*dz[2];
                if ((abs(summ) < energy_min) && (z[(z.size() - k - 1)] > (reference_frame_shift)) && (z[(z.size() - k - 1)] < (reference_frame_shift+delta_z_max_dist))) {
                    energy_min = abs(summ);
                    energy_min_dist = z[int(z.size() - k - 1)];
                }
            }

            array_of_min_z[i*v_pyro.size()+j] = energy_min_dist-reference_frame_shift;
            array_of_min_energies[i*v_pyro.size()+j] = energy_min;
        }
    }
}