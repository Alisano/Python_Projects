from tkinter import *
from tkinter import filedialog, ttk
from tkinter.messagebox import showerror
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy import interpolate
import numpy as np
import os


def get_coord_from_txt(file_path):
    with open(file_path, "r") as file:
        tmp_data = file.readlines()
    coord = []
    coord.append([float(string.rstrip("\n").split()[0]) for string in tmp_data])
    coord.append([float(string.rstrip("\n").split()[1]) for string in tmp_data])
    return coord


def open_file():
    global coord, ignoreMod, ax2, norm_state, overlay_state, combobox
    types = [("Text Files", "*.txt")]
    file_path = filedialog.askopenfilename(title="Выберите график для обработки в .txt формате", filetypes=types)
    if not file_path:
        return
    else:
        ignoreMod = False
        ax2.clear()
        norm_state.set(0)
        overlay_state.set(0)
        combobox.set("ДДС-30")

    coord = get_coord_from_txt(file_path)
    plot(coord, ax1)


def set_standart_for_mod(event):
    global coord_ref, combobox, defaultPath, isFirstRequest, ax2, ignoreMod

    if combobox.get() == "ДДС-30":
        file_name="dds30_std.txt"
        combobox.select_clear()

    if combobox.get() == "ФПУ":
        file_name="phd_std.txt"
        combobox.select_clear()

    file_path = defaultPath + file_name
    try:
        coord_ref = get_coord_from_txt(file_path)
    except FileNotFoundError:
        showerror(title="Ошибка", message=f"Не найден текстовый файл коодинат эталона,\nудостоверьтесь, что текстовый файл лежит в по пути\n{file_path}")

    if isFirstRequest:
        isFirstRequest = False
    else:
        try:
            ax2.lines[0]
        except:
            pass
        else:
            ignoreMod = False
            mod_figure()
            if overlay_state.get() == 1:
                overlay_plot()


def mod_figure():
    global coord, coord_ref, norm_coef_func_coord, ignoreMod
    try:
        coord
    except NameError:
        showerror(title="Ошибка построения функции", message="Не выбрана функция для модификации")
        return
    
    try:
         ax2.lines[0]
    except:
        pass
    else:
        if ignoreMod:
            return       
    
    if not coord_ref:
        showerror(title="Ошибка", message="Не определён эталон для пересчета заданной функции")
        return
    
    ignoreMod = True

    coef_func_coord = mul_two_func(coord, coord_ref, step_x=0.1)
    if norm_state.get() == 1:
        norm()
        plot(norm_coef_func_coord, ax2)
    else:
        plot(coef_func_coord, ax2)


def mul_two_func(coord, coord_ref, step_x=0.1):
    interpolate_dds30_std = interpolate.interp1d(coord[0], coord[1])
    interpolate_responsivity = interpolate.interp1d(coord_ref[0], coord_ref[1])
    
    min_x = min(coord[0]) if min(coord[0]) > min(coord_ref[0]) else min(coord_ref[0])
    max_x = max(coord[0]) if max(coord[0]) < max(coord_ref[0]) else max(coord_ref[0])
    
    x_arr = np.arange(min_x, max_x, step_x)
    y_arr = []
    for x in x_arr:
        y_arr.append(interpolate_dds30_std(x) * interpolate_responsivity(x))
    return [x_arr, y_arr]


def plot(coord, ax, xlimit=900.0, xlabel='Длина волны, нм', ylabel='Интенсивность, Отн. ед.', two_plot=False, name_label=''):
    if not two_plot:
        ax.clear()
    ax.grid(linestyle = '--')
    for i, x in enumerate(coord[0]):
        if x >= xlimit:
            coord[0] = coord[0][:i]
            coord[1] = coord[1][:i]

    ax.plot(coord[0], coord[1], linestyle='-', linewidth=2, label=name_label)
    ax.set_xlabel(xlabel, labelpad=0.01)
    ax.set_ylabel(ylabel)
    if two_plot:
        ax.legend()
    canvas.draw()


def write_coord_func():
    global norm_state, norm_coef_func_coord, coord, coord_ref

    try:
        ax2.lines[0]
    except:
        showerror(title="Ошибка", message="Постройте модифицированный график для сохранения координат")
        return    

    types = [("Text Files", "*.txt")]
    file_path = filedialog.asksaveasfilename(title="Выберите график для сохранения файла в .txt формате", filetypes=types, initialfile="figure.txt")
    if not file_path:
        return

    if norm_state.get() == 1:
        write_file(file_path, norm_coef_func_coord)
    else:
        coef_func_coord = mul_two_func(coord, coord_ref, step_x=0.1)
        write_file(file_path, coef_func_coord)


def write_file(file_path, coord):
    with open(file_path, "w") as file:
        for x, y in zip(coord[0], coord[1]):
            file.write(f"{x} {y}\n")


def add_label():
    global label_window, entry_label, ax2, x_label, y_label, canvas, label_win_cnt
    try:
        ax2.text(float(x_label.get()), float(y_label.get()), entry_label.get())
    except:
        showerror(title="Ошибка", message="Неправильно введены данные для подписи")
    destroy_label_window()
    canvas.draw()


def destroy_label_window():
    global label_win_cnt, label_window
    label_win_cnt -= 1
    label_window.destroy()


def write_text_func():
    global label_window, entry_label, x_label, y_label, ax2, label_win_cnt

    try:
        ax1.lines[0]
        ax2.lines[0]
    except:
        showerror(title="Ошибка", message="Постройте графики для подписи")
        return
    
    if not label_win_cnt:
        label_win_cnt += 1
    else:
        showerror(title="Ошибка", message="Окно уже открыто")
        return   

    label_window = Toplevel()
    label_window.title("Установка подписи у графика")
    label_window.resizable(False, False)
    frame_labels = Frame(label_window)
    frame_button = Frame(label_window)

    text_label = ttk.Label(frame_labels, text="Подпись:")
    text_label.grid(row=0, column=0)
    entry_label = ttk.Entry(frame_labels)
    entry_label.grid(row=0, column=1)

    x_text = ttk.Label(frame_labels, text="x:")
    x_text.grid(row=0, column=2)
    x_label = ttk.Entry(frame_labels, width=10)
    x_label.grid(row=0, column=3)

    y_text = ttk.Label(frame_labels, text="y:")
    y_text.grid(row=0, column=4)
    y_label = ttk.Entry(frame_labels, width=10)
    y_label.grid(row=0, column=5)

    btn = ttk.Button(frame_button, text="Готово", command=add_label)
    btn.pack(anchor=S)

    frame_labels.pack(anchor=N)
    frame_button.pack(anchor=S)
   
    label_window.protocol("WM_DELETE_WINDOW", destroy_label_window)


def save_image_func():
    global fig, ax2

    try:
        ax2.lines[0]
    except:
        showerror(title="Ошибка", message="Постройте модифицированный график для сохранения")
        return    

    types = [("Image Files", "*.png")]
    file_path = filedialog.asksaveasfilename(title="Выберите график для сохранения файла в .png формате", filetypes=types, initialfile="figure.png")
    if not file_path:
        return
    extent = ax2.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    extent.x0 = 1.88
    extent.y0 = 0.15
    fig.savefig(file_path, bbox_inches=extent.expanded(1.05, 1.05))


class CustomNavigationToolbar(NavigationToolbar2Tk):
    global coord_message
    def __init__(self, canvas, window):
        super().__init__(canvas, window)
        coord = f'x=None, y=None'
        coord_message.set(coord)

    def mouse_move(self, event):
        global coord_text
        if event.inaxes and event.inaxes.get_navigate():
            x, y = event.xdata, event.ydata
            coord = f'x={x:.2f}, y={y:.2f}'
            coord_message.set(coord)
        else:
            coord = f'x=None, y=None'
            coord_message.set(coord)


def norm():
    global ax1, ax2, coord, coord_ref, norm_state, norm_coord, norm_coef_func_coord
    try:
        coef_func_coord = mul_two_func(coord, coord_ref, step_x=0.1)
        line1 = ax1.lines[0]
        data = line1.get_ydata()

        if norm_state.get() == 1:
            norm_coord = [coord[0], (np.array(coord[1]) - min(coord[1])) / (max(coord[1]) - min(coord[1]))]
            norm_coef_func_coord = [coef_func_coord[0], (np.array(coef_func_coord[1]) - min(coef_func_coord[1])) / (max(coef_func_coord[1]) - min(coef_func_coord[1]))]
            if len(data):
                plot(norm_coord, ax1)
        else:
            if len(data):
                plot(coord, ax1)
    except:
        showerror(title="Ошибка", message="Не выбран график для нормировки")
        data = []
        norm_state.set(0)
    else:
        try:
            ax2.lines[0]
        except:
            pass
        else:
            overlay_plot()


def overlay_plot():
    global overlay_state, norm_state, norm_coord, norm_coef_func_coord, coord, coord_ref
    try:
        line2 = ax2.lines[0]
        data = line2.get_ydata()
    except:
        showerror(title="Ошибка", message="Не выбраны графики для совмещения")
        overlay_state.set(0)
        data = []
    
    if overlay_state.get() == 1:
        if norm_state.get() == 1:
            if len(data):
                plot(norm_coef_func_coord, ax2, two_plot=False, name_label="Модифицированный график")
                plot(norm_coord, ax2, two_plot=True, name_label="Оригинальный график")
        else:
            if len(data):
                coef_func_coord = mul_two_func(coord, coord_ref, step_x=0.1)
                plot(coef_func_coord, ax2, two_plot=False, name_label="Модифицированный график")
                plot(coord, ax2, two_plot=True, name_label="Оригинальный график")      
    else:
        if norm_state.get() == 1:
            if len(data):
                plot(norm_coef_func_coord, ax2)
        else:
            if len(data):
                coef_func_coord = mul_two_func(coord, coord_ref, step_x=0.1)
                plot(coef_func_coord, ax2)


def main():
    global ax1, ax2, canvas, coord, fig, coord_message, combobox, defaultPath, norm_state, overlay_state, isFirstRequest, ignoreMod, label_win_cnt

    label_win_cnt = 0
    window = Tk()
    window.title("Программа для корректировки графиков")
    window.resizable(False, False)
    window.iconbitmap("miet.ico")
    frame_up_buttons = Frame(window)
    frame_figures = Frame(window, height=700)
    frame_down_buttons = Frame(window)

    plt.rcParams['font.family'] = "Times New Roman"
    fig, (ax1, ax2) = plt.subplots(2, 1)
    plt.subplots_adjust(wspace=0.0, hspace=0.164, left=0.255, top=0.979, bottom=0.064, right=0.82)

    open_fig_button = Button(frame_up_buttons, text="Выбрать .txt файл графика", command=open_file)
    open_fig_button.grid(row=0, column=0, padx=10)

    ignoreMod = False
    mod_fig_button = Button(frame_up_buttons, text="Модифицировать график", command=mod_figure)
    mod_fig_button.grid(row=0, column=1, padx=10)

    isFirstRequest = True
    standart_mode = ["ДДС-30", "ФПУ"]
    defaultPath = f"{os.path.dirname(os.path.abspath(__file__))}\\Data\\"
    cur_state = StringVar(value=standart_mode[0])  
    combobox = ttk.Combobox(frame_up_buttons, textvariable=cur_state, values=standart_mode, state="readonly")
    set_standart_for_mod(0)
    combobox.grid(row=0, column=2, padx=10)
    combobox.bind("<<ComboboxSelected>>", set_standart_for_mod)

    canvas = FigureCanvasTkAgg(fig, master=frame_figures)
    canvas.get_tk_widget().pack(fill='both', expand=True)

    coord_message = StringVar()
    toolbar = CustomNavigationToolbar(canvas, frame_down_buttons)
    toolbar.children['!button5'].pack_forget()
    # toolbar.children['!button4'].pack_forget()
    toolbar.children['!button3'].pack_forget()
    toolbar.children['!button2'].pack_forget()
    toolbar.grid(row=0, column=0)
    
    coord_label = Label(frame_down_buttons, textvariable=coord_message)
    coord_label.config(width=20)
    coord_label.grid(row=0, column=1, padx=10)

    mod_fig_button = Button(frame_down_buttons, text="Сохранить координаты графика", command=write_coord_func)
    mod_fig_button.grid(row=0, column=2, padx=10)

    mod_text_button = Button(frame_down_buttons, text="Подпись графика", command=write_text_func)
    mod_text_button.grid(row=0, column=6, padx=10)

    mod_fig_button = Button(frame_down_buttons, text="Сохранить изображение графика", command=save_image_func)
    mod_fig_button.grid(row=0, column=3, padx=10)

    overlay_state = IntVar(value=0)
    overlay_checkbutton = Checkbutton(frame_down_buttons, text="Совмещение\n графиков", command=overlay_plot, variable=overlay_state)
    overlay_checkbutton.grid(row=0, column=4, padx=10)

    norm_state = IntVar(value=0)
    norm_checkbutton = Checkbutton(frame_down_buttons, text="Нормировка\n графиков", command=norm, variable=norm_state)
    norm_checkbutton.grid(row=0, column=5, padx=10)

    frame_up_buttons.pack(anchor="n")
    frame_figures.pack(fill="both")
    frame_figures.pack_propagate(False)
    frame_down_buttons.pack(fill='both')

    window.protocol("WM_DELETE_WINDOW", window.quit)
    window.mainloop()


if __name__ == "__main__":
    main()