import time
import random
import pygame
import sys

class audio:
    def __init__(self, music_path):
        pygame.mixer.music.load(music_path)

    def check_sound(self, ST):
        if ST > 0 and not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1)
        elif ST == 0 and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

class display:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('chip8 emulator')
        self.screen = pygame.display.set_mode((640, 320))
        self.pixels = [[0] * 64 for _ in range(32)]
        self.clock = pygame.time.Clock()
        self.pixels_changed = set()
        self.fps = 60

    def draw(self):
        if not self.pixels_changed:
            return
        for x, y in self.pixels_changed:
            color = (255, 255, 255) if self.pixels[y][x] == 1 else (0, 0, 0)
            pygame.draw.rect(self.screen, color, (x * 10, y * 10, 10, 10))
        pygame.display.flip()
        self.pixels_changed.clear()

    def cls(self):
        self.screen.fill((0, 0, 0))
        self.pixels = [[0] * 64 for _ in range(32)]
        self.pixels_changed.clear()
        pygame.display.flip()

class keyboard:
    def __init__(self):
        self.key_map = [pygame.K_x, pygame.K_1, pygame.K_2, pygame.K_3, 
                        pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_a,
                        pygame.K_s, pygame.K_d, pygame.K_z, pygame.K_c, 
                        pygame.K_4, pygame.K_r, pygame.K_f, pygame.K_v]
        self.pressed_key = [False] * len(self.key_map)
        self.previous_pressed_key = [False] * len(self.key_map)

    def key_is_pressed(self, index_key):
        return self.pressed_key[index_key]

    def get_new_key(self):
        for i in range(len(self.key_map)):
            if self.pressed_key[i] and not self.previous_pressed_key[i]:
                return i
        return -1

    def update(self):
        get_pressed_key = pygame.key.get_pressed()
        for i, key in enumerate(self.key_map):
            self.previous_pressed_key[i] = self.pressed_key[i]
            self.pressed_key[i] = get_pressed_key[key]

class registers:
    def __init__(self):
        self.Vx = [0] * 16
        self.I = 0
        self.SP = -1
        self.DT = 0
        self.ST = 0
        self.PC = 0x200

class ram:
    def __init__(self):
        self.memory = [0] * 4096
        self.stack = [0] * 16

    def write(self, data, addr):
        self.memory[addr] = data

    def read(self, addr):
        assert addr < len(self.memory), "Addres is out of range"
        return self.memory[addr]

class chip8:
    def __init__(self, rom_path, music_path = 'beep.wav'):
        self.rom_path = rom_path
        self.display = display()
        self.registers = registers()
        self.keyboard = keyboard()
        self.audio = audio(music_path)
        self.ram = ram()
        self.rom_size = 0
        self.start_sound_ticks = pygame.time.get_ticks()
        self.instructions_per_second = 500
        self.quirks = True
        self.limit_emu_loop = False
        self.font_begin_addr = 0x000
        self.font_codes = [0xf0, 0x90, 0x90, 0x90, 0xf0,
                           0x20, 0x60, 0x20, 0x20, 0x70,
                           0xf0, 0x10, 0xf0, 0x80, 0xf0,
                           0xf0, 0x10, 0xf0, 0x10, 0xf0,
                           0x90, 0x90, 0xf0, 0x10, 0x10,
                           0xf0, 0x80, 0xf0, 0x10, 0xf0,
                           0xf0, 0x80, 0xf0, 0x90, 0xf0,
                           0xf0, 0x10, 0x20, 0x40, 0x40,
                           0xf0, 0x90, 0xf0, 0x90, 0xf0,
                           0xf0, 0x90, 0xf0, 0x10, 0xf0,
                           0xf0, 0x90, 0xf0, 0x90, 0x90,
                           0xe0, 0x90, 0xe0, 0x90, 0xe0,
                           0xf0, 0x80, 0x80, 0x80, 0xf0,
                           0xe0, 0x90, 0x90, 0x90, 0xe0,
                           0xf0, 0x80, 0xf0, 0x80, 0xf0,
                           0xf0, 0x80, 0xf0, 0x80, 0x80]
        self.write_fonts()
        self.instructions_per_cycle = self.instructions_per_second // self.display.fps

    def write_fonts(self):
        for addr, value in enumerate(self.font_codes, self.font_begin_addr):
            self.ram.write(value, addr)

    def read_ROM(self, file_path = ""):
        if not file_path:
            file_path = self.rom_path
        with open(file_path, "rb") as file:
            while data := file.read(1):
                value = int.from_bytes(data, "big")
                self.ram.write(value, self.registers.PC)
                self.registers.PC += 1
                self.rom_size += 1
        self.registers.PC = 0x200

    def run(self):
        last_update = pygame.time.get_ticks()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.timer_registers()
            self.audio.check_sound(self.registers.ST)

            current_time = pygame.time.get_ticks()
            delta_time = current_time - last_update
            instructions_to_execute = (self.instructions_per_second * delta_time) // 1000
            for _ in range(min(instructions_to_execute, self.instructions_per_cycle)):
                self.keyboard.update()
                self.fetch()
            last_update = current_time

            self.display.draw()
            self.display.clock.tick(self.display.fps)

    def fetch(self):
        byte1 = self.ram.read(self.registers.PC)
        byte2 = self.ram.read(self.registers.PC + 1)
        self.decode((byte1 << 8) + byte2)

    def decode(self, op):
        decode_command = ""
        match (op >> 12):
            case 0:
                if op == 0x00E0: decode_command = "CLS"
                elif op == 0x00EE: decode_command = "RET"
                else: decode_command = f"SYS {op & 0x0fff}"
            case 1: 
                decode_command = f"JP {op & 0x0fff}"
            case 2: 
                decode_command = f"CALL {op & 0x0fff}"
            case 3: 
                decode_command = f"SE V{(op & 0x0f00) >> 8} {op & 0x00ff}"
            case 4: 
                decode_command = f"SNE V{(op & 0x0f00) >> 8} {op & 0x00ff}"
            case 5: 
                decode_command = f"SE V{(op & 0x0f00) >> 8} V{(op & 0x00f0) >> 4}"
            case 6: 
                decode_command = f"LD V{(op & 0x0f00) >> 8} {op & 0x00ff}"
            case 7: 
                decode_command = f"ADD V{(op & 0x0f00) >> 8} {op & 0x00ff}"
            case 8:
                match (op & 0x000f):
                    case 0:
                        decode_command = f"LD V{(op & 0x0f00) >> 8} V{(op & 0x00f0) >> 4}"
                    case 1:
                        decode_command = f"OR V{(op & 0x0f00) >> 8} V{(op & 0x00f0) >> 4}"
                    case 2:
                        decode_command = f"AND V{(op & 0x0f00) >> 8} V{(op & 0x00f0) >> 4}"
                    case 3:
                        decode_command = f"XOR V{(op & 0x0f00) >> 8} V{(op & 0x00f0) >> 4}"
                    case 4:
                        decode_command = f"ADD V{(op & 0x0f00) >> 8} V{(op & 0x00f0) >> 4}"
                    case 5:
                        decode_command = f"SUB V{(op & 0x0f00) >> 8} V{(op & 0x00f0) >> 4}"
                    case 6:
                        decode_command = f"SHR V{(op & 0x0f00) >> 8} V{(op & 0x00f0) >> 4}"
                    case 7:
                        decode_command = f"SUBN V{(op & 0x0f00) >> 8} V{(op & 0x00f0) >> 4}"
                    case 0xe:
                        decode_command = f"SHL V{(op & 0x0f00) >> 8} V{(op & 0x00f0) >> 4}"
            case 9:
                decode_command = f"SNE V{(op & 0x0f00) >> 8} V{(op & 0x00f0) >> 4}"
            case 0xa:
                decode_command = f"LD I {op & 0x0fff}"
            case 0xb:
                decode_command = f"JP V0 {op & 0x0fff}"
            case 0xc:
                decode_command = f"RND V{(op & 0x0f00) >> 8} {op & 0x00ff}"
            case 0xd:
                decode_command = f"DRW V{(op & 0x0f00) >> 8} V{(op & 0x00f0) >> 4} {(op & 0x000f)}"
            case 0xe:
                if (op & 0x00ff) == 0x9e:
                    decode_command = f"SKP V{(op & 0x0f00) >> 8}"
                else:
                    decode_command = f"SKNP V{(op & 0x0f00) >> 8}"
            case 0xf:
                match (op & 0x00ff):
                    case 0x07:
                        decode_command = f"LD V{(op & 0x0f00) >> 8} DT"
                    case 0x0A:
                        decode_command = f"LD V{(op & 0x0f00) >> 8} K"
                    case 0x15:
                        decode_command = f"LD DT V{(op & 0x0f00) >> 8}"
                    case 0x18: 
                        decode_command = f"LD ST V{(op & 0x0f00) >> 8}"
                    case 0x1e: 
                        decode_command = f"ADD I V{(op & 0x0f00) >> 8}"
                    case 0x29: 
                        decode_command = f"LD F V{(op & 0x0f00) >> 8}"
                    case 0x33: 
                        decode_command = f"LD B V{(op & 0x0f00) >> 8}"
                    case 0x55: 
                        decode_command = f"LD [I] V{(op & 0x0f00) >> 8}"
                    case 0x65: 
                        decode_command = f"LD V{(op & 0x0f00) >> 8} [I]"
        if decode_command == "":
            print(f"Unknown: {hex(op)}")
            return
        self.execute(decode_command)

    def timer_registers(self):
        delta_time = pygame.time.get_ticks() - self.start_sound_ticks
        if delta_time >= 1000 / self.display.fps:
            if self.registers.DT > 0:
                self.registers.DT -= 1
            if self.registers.ST > 0:
                self.registers.ST -= 1
            self.start_sound_ticks = pygame.time.get_ticks()

    def execute(self, string):
        # print(string, f"V0={hex(self.registers.Vx[0])} V1={hex(self.registers.Vx[1])} V2={hex(self.registers.Vx[2])} "
        #               f"V3={hex(self.registers.Vx[3])} V4={hex(self.registers.Vx[4])} V5={hex(self.registers.Vx[5])} "
        #               f"V6={hex(self.registers.Vx[6])} V7={hex(self.registers.Vx[7])} V8={hex(self.registers.Vx[8])} "
        #               f"V9={hex(self.registers.Vx[9])} Va={hex(self.registers.Vx[10])} Vb={hex(self.registers.Vx[11])} "
        #               f"Vc={hex(self.registers.Vx[12])} Vd={hex(self.registers.Vx[13])} Ve={hex(self.registers.Vx[14])} "
        #               f"Vf={hex(self.registers.Vx[15])} I={hex(self.registers.I)} SP={hex(self.registers.SP)} "
        #               f"DT={hex(self.registers.DT)} ST={hex(self.registers.ST)} PC={hex(self.registers.PC)}")

        def get_param(var):
            match (var):
                case "V0"|"V1"|"V2"|"V3"|"V4"|"V5"|"V6"|"V7"|"V8"|"V9"|"V10"|"V11"|"V12"|"V13"|"V14"|"V15":
                    var = self.registers.Vx[int(var[1:])]
                case "I":
                    var = self.registers.I
                case "DT":
                    var = self.registers.DT
                case "ST":
                    var = self.registers.ST
                case "K":
                    var = -1
                    for key_state in self.keyboard.pressed_key:
                        if key_state:
                            var = key_state
                            break
                case _:
                    var = int(var)
            return var

        def set_param(var, value):
            match (var):
                case "V0"|"V1"|"V2"|"V3"|"V4"|"V5"|"V6"|"V7"|"V8"|"V9"|"V10"|"V11"|"V12"|"V13"|"V14"|"V15":
                    self.registers.Vx[int(var[1:])] = value
                case "I":
                    self.registers.I = value
                case "DT":
                    self.registers.DT = value
                case "ST":
                    self.registers.ST = value

        op, *arg = string.split()
        skip_pc_increment = False
        match (op):
            case "RET":
                self.registers.PC = self.ram.stack[self.registers.SP]
                self.registers.SP -= 1
            case "JP":
                if len(arg) == 1:
                    self.registers.PC = get_param(arg[0])
                else:
                    self.registers.PC = get_param(arg[0]) + get_param(arg[1])
                skip_pc_increment = True
            case "CALL":
                self.registers.SP += 1
                self.ram.stack[self.registers.SP] = self.registers.PC
                self.registers.PC = get_param(arg[0])
                skip_pc_increment = True
            case "SE":
                if get_param(arg[0]) == get_param(arg[1]):
                    self.registers.PC += 2
            case "SNE":
                if get_param(arg[0]) != get_param(arg[1]):
                    self.registers.PC += 2
            case "LD":
                if arg[0] == "B":
                    self.ram.memory[self.registers.I] = (self.registers.Vx[int(arg[1][1:])] // 100) % 10
                    self.ram.memory[self.registers.I + 1] = (self.registers.Vx[int(arg[1][1:])] // 10) % 10
                    self.ram.memory[self.registers.I + 2] = self.registers.Vx[int(arg[1][1:])] % 10
                elif arg[0] == "F":
                    self.registers.I = self.font_begin_addr + (self.registers.Vx[int(arg[1][1:])] & 0xf) * 5
                elif arg[0] == "[I]":
                    for i in range(int(arg[1][1:]) + 1):
                        self.ram.memory[self.registers.I + i] = self.registers.Vx[i]
                    self.registers.I = self.registers.I + int(arg[1][1:]) + 1 if self.quirks else self.registers.I
                elif arg[1] == "[I]":
                    for i in range(int(arg[0][1:]) + 1):
                        self.registers.Vx[i] = self.ram.memory[self.registers.I + i]
                    self.registers.I = self.registers.I + int(arg[0][1:]) + 1 if self.quirks else self.registers.I
                elif arg[1] == "K":
                    key = self.keyboard.get_new_key()
                    if key < 0:
                        skip_pc_increment = True
                    else:
                        self.registers.Vx[int(arg[0][1:])] = key
                else:
                    set_param(arg[0], get_param(arg[1]))
            case "OR":
                set_param(arg[0], get_param(arg[0]) | get_param(arg[1]))
                self.registers.Vx[0xf] = 0 if self.quirks else self.registers.Vx[0xf]
            case "AND":
                set_param(arg[0], get_param(arg[0]) & get_param(arg[1]))
                self.registers.Vx[0xf] = 0 if self.quirks else self.registers.Vx[0xf]
            case "XOR":
                set_param(arg[0], get_param(arg[0]) ^ get_param(arg[1]))
                self.registers.Vx[0xf] = 0 if self.quirks else self.registers.Vx[0xf]
            case "ADD":
                summ = get_param(arg[0]) + get_param(arg[1])
                self.registers.Vx[0xf] = 1 if summ > 255 else 0
                if arg[0] != "V15":
                    set_param(arg[0], summ if arg[0] == "I" else summ & 0xff)
            case "SUB":
                sub = get_param(arg[0]) - get_param(arg[1])
                self.registers.Vx[0xf] = 1 if get_param(arg[0]) >= get_param(arg[1]) else 0
                if arg[0] != "V15":
                    set_param(arg[0], sub & 0xff)
            case "SUBN":
                subn = get_param(arg[1]) - get_param(arg[0])
                self.registers.Vx[0xf] = 1 if get_param(arg[0]) <= get_param(arg[1]) else 0
                if arg[0] != "V15":
                    set_param(arg[0], subn & 0xff)
            case "SHR":
                if self.quirks:
                    Vx = self.registers.Vx[int(arg[1][1:])]
                    self.registers.Vx[int(arg[0][1:])] = (Vx >> 1) & 0b1 if arg[1] == "V15" else (Vx >> 1) & 0xff
                else:
                    Vx = self.registers.Vx[int(arg[0][1:])]
                    self.registers.Vx[int(arg[0][1:])] = (Vx >> 1) & 0xff
                self.registers.Vx[0xf] = Vx & 0b1
            case "SHL":
                if self.quirks:
                    Vx = self.registers.Vx[int(arg[1][1:])]
                    self.registers.Vx[int(arg[0][1:])] = (Vx << 1) & 0b1 if arg[1] == "V15" else (Vx << 1) & 0xff
                else:
                    Vx = self.registers.Vx[int(arg[0][1:])]
                    self.registers.Vx[int(arg[0][1:])] = (Vx << 1) & 0xff
                self.registers.Vx[0xf] = Vx >> 7
            case "RND":
                set_param(arg[0], int(arg[1]) & random.randint(0, 255))
            case "DRW":
                x_start = self.registers.Vx[int(arg[0][1:])] % 64
                y_start = self.registers.Vx[int(arg[1][1:])] % 32
                addr = self.registers.I
                n = int(arg[2])
                self.registers.Vx[0xf] = 0
                for row in range(n):
                    y = y_start + row
                    if self.quirks: 
                        if y >= 32 or y < 0:
                            continue
                    else:
                        y %= 32
                    sprite_bytes_row = self.ram.read(addr + row)
                    for col in range(8):
                        x = x_start + col
                        if self.quirks:
                            if x >= 64 or x < 0:
                                continue
                        else:
                            x %= 64
                        old_pixel = self.display.pixels[y][x]
                        pixel_bit = (sprite_bytes_row >> (7 - col)) & 0b1
                        new_pixel = old_pixel ^ pixel_bit
                        self.display.pixels[y][x] = new_pixel
                        if old_pixel == 1 and new_pixel == 0:
                            self.registers.Vx[0xf] = 1
                        if old_pixel != new_pixel:
                            self.display.pixels_changed.add((x, y))
            case "SKP":
                key_index = self.registers.Vx[int(arg[0][1:])]
                if self.keyboard.key_is_pressed(key_index):
                    self.registers.PC += 2
            case "SKNP":
                key_index = self.registers.Vx[int(arg[0][1:])]
                if not self.keyboard.key_is_pressed(key_index):
                    self.registers.PC += 2     
            case "CLS":
                self.display.cls()
            case "SYS":
                pass

        if not skip_pc_increment:
            self.registers.PC += 2

if __name__ == "__main__":
    emu = chip8(rom_path="/Users/alexandrpopov/Scripts/Repositories/chip8-roms/games/Addition Problems [Paul C. Moews].ch8", 
                music_path= "/Users/alexandrpopov/Scripts/python_scripts/pet_projects/beep.wav")
    emu.read_ROM()
    emu.run()