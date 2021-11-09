#!/usr/bin/env python3
import random
import copy
import time
from enum import Enum
from tkinter import *

# I want to get the same random each run
random.seed(0)

MELTING_POINT = 20

POLLUTION_CHANGE = 0.05
POLLUTION_THRESHOLD = 0.5
POLLUTION_FACTOR = 3
POLLUTION_DOWNAGE = 0.02
RAIN_CHANCE = 20

WIND_TTL = 3
STRONG_WIND_THRESHOLD = 2
CLOUD_TTL = 2

MAX_TEMPERATURE = 45
MIN_TEMPERATURE = -10
MAX_HEIGHT = 100
CLOUDY_CHANCE = 4
HEIGHT_RAIN_FACTOR = 33

CANVAS_HEIGHT = 600
CANVAS_WIDTH = 1000

GRID_HEIGHT = 10
GRID_WIDTH = 10

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)


class BlockType(str, Enum):
    LAND = "land"
    SEA = "seas"
    ICEBERG = "iceberg"
    FORREST = "forrest"
    CITY = "city"


class Block:
    def __init__(self):
        self.type = BlockType.LAND
        self.height = 0
        self.wind = [0, 0, 0] # Direction of wind like numpad
        self.cloudy = [False, CLOUD_TTL]
        self.pollution = 0
        self.temperature = 0
        self.pending_changes = []


    def apply_changes(self):
        for changes in self.pending_changes:
            if "wind" in changes:
                self.wind = changes["wind"]

            self.pollution = min(self.pollution + changes["pollution"], POLLUTION_THRESHOLD)
            if changes["cloudy"]:
                self.cloudy = [True, CLOUD_TTL]

        self.pending_changes = []

    def get_wind_str(self):
        s = ""
        if self.wind[2] == 0:
            s += "[]"
        elif self.wind[0] == -1 and self.wind[1] == -1:
            s += "↖"
        elif self.wind[0] == 0 and self.wind[1] == -1:
            s += "↑"
        elif self.wind[0] == 1 and self.wind[1] == -1:
            s += "↗"
        elif self.wind[0] == -1 and self.wind[1] == 0:
            s += "←"
        elif self.wind[0] == 0 and self.wind[1] == 0:
            s += "[]"
        elif self.wind[0] == 1 and self.wind[1] == 0:
            s += "→"
        elif self.wind[0] == -1 and self.wind[1] == 1:
            s += "↙"
        elif self.wind[0] == 0 and self.wind[1] == 1:
            s += "↓"
        elif self.wind[0] == 1 and self.wind[1] == 1:
            s += "↘"
        else:
            print("FUCK", self.wind)
            exit()
        # Add strength
        s += str(self.wind[2])
        #s += "" if self.wind[2] <= STRONG_WIND_THRESHOLD else "S"

        return s


    def __str__(self):
        return "{} {}m {} {}{} {} {}c".format(self.type,
                    self.height,
                    self.get_wind_str(),
                    "cloudy" if self.cloudy[0] else "clear",
                    self.cloudy[1],
                    self.pollution,
                    self.temperature)


    def get_info(self):
        return "{}m\n{} {} {}\n{:.2f}p {:.2f}c".format(self.height,
                    self.get_wind_str(),
                    "cloudy" if self.cloudy[0] else "clear",
                    self.cloudy[1],
                    self.pollution,
                    self.temperature)

    def get_color(self):
        if self.type == BlockType.LAND:
            return "brown"
        elif self.type == BlockType.SEA:
            return "blue"
        elif self.type == BlockType.ICEBERG:
            return "white"
        elif self.type == BlockType.FORREST:
            return "green"
        elif self.type == BlockType.CITY:
            return "gray"


class EarthAutomaton(Tk):
    """ A cellur automaton simulating the earth. """

    def __init__(self,  *args,**kwargs):
        Tk.__init__(self, *args, **kwargs)

        self.height = GRID_HEIGHT
        self.width = GRID_WIDTH
        self.blocks = [[self.init_cell_state() for i in range(self.width)] for j in range(self.height)]
        self.water_height = 0
        self.day = 0

        # Content frame
        self.content = Frame(self)
        self.content.grid(row=0, column=0, sticky=(N,S,E,W))

        # Cells frame
        self.canvas = Canvas(self.content, height=CANVAS_HEIGHT, width=CANVAS_WIDTH,
                                highlightthickness=0, background='white')

        self.canvas.grid(row=0, column=0, sticky=(N,S,E,W))
        self.canvas.bind('<Configure>', self.draw)

        # Controls frame and buttons
        self.controls = Frame(self.content)
        self.controls.grid(row=1, column=0, sticky=(N,S,E,W))
        self.prev = Button(self.controls, text='Previous',
                command=self.previous_step)
        self.prev.grid(row=0, column=0, sticky=(W))

        self.day_label = Label(self.controls, text="Day: 0")
        self.day_label.grid(row=0, column=1, sticky=(W))
        self.next = Button(self.controls, text='Next',
                command=self.next_step)
        self.next.grid(row=0, column=2, sticky=(W))

        #Size Configuration
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=4)
        self.content.rowconfigure(1, weight=1)
        self.controls.columnconfigure(0,weight=1)
        self.controls.columnconfigure(1,weight=1)
        self.controls.columnconfigure(2,weight=1)
        self.controls.rowconfigure(0,weight=1)

        # Keep track of old steps
        self.old = []


    def next_step(self):
        start_time = time.time()
        self.day += 1
        self.old.append((copy.deepcopy(self.blocks), self.water_height))
        self.step()
        self.draw()
        print("Time: {}".format(time.time() - start_time))

    def previous_step(self):
        if self.day == 0:
            return

        self.day -= 1
        self.blocks, self.water_height = self.old.pop()
        self.draw()

    def draw(self, event=None):
        self.canvas.delete('rect')
        width = int(self.canvas.winfo_width()/self.height)
        height = int(self.canvas.winfo_height()/self.width)
        for row in range(self.height):
            for col in range(self.width):
                x1 = col*width
                x2 = x1 + width
                y1 = row*height
                y2 = y1 + height

                color = self.blocks[row][col].get_color()
                cell = self.canvas.create_rectangle(x1, y1, x2, y2,
                        fill=color, tags='cell')

                center = ((x1+x2)//2, (y1+y2)//2)
                info = self.blocks[row][col].get_info()
                self.canvas.create_text(center, text=info)
                self.canvas.tag_bind(cell)

        self.day_label["text"] = "Day {}, Water Level {}m".format(self.day, self.water_height)

    def step(self):
        for row in range(self.height):
            for col in range(self.width):
                self.evolve_rule(row, col)

        # Apply all necessary changes
        for row in range(self.height):
            for col in range(self.width):
                if row == 5 and col == 5:
                    print(self.blocks[row][col].pending_changes)
                self.blocks[row][col].apply_changes()
                if row == 5 and col == 5:
                    print(self.blocks[row][col])


    def init_cell_state(self):
        b = Block()
        b.type = random.choice(list(BlockType))
        b.height = random.randint(0, MAX_HEIGHT)
        b.cloudy = [random.randint(0, CLOUDY_CHANCE) == 0, CLOUD_TTL]
        b.wind = [random.randint(-1,1), random.randint(-1,1), random.randint(0,WIND_TTL)]
        b.temperature = random.randint(MIN_TEMPERATURE, MAX_TEMPERATURE)
        return b


    def evolve_rule(self, row, col):
        block = self.blocks[row][col]

        # Raising water height turns land to sea
        if block.height < self.water_height and block.type != BlockType.ICEBERG:
            block.type = BlockType.SEA

        # Pollution makes the temperature rise
        block.temperature = min(block.pollution + block.temperature, MAX_TEMPERATURE)

        # If its hot, the iceberg melts
        if block.type == BlockType.ICEBERG and block.temperature >= MELTING_POINT:
            block.type = BlockType.SEA
            self.water_height += 1

        # Cities cause pollution
        elif block.type == BlockType.CITY:
            block.pollution = min(block.pollution + POLLUTION_CHANGE, POLLUTION_THRESHOLD)

        # If we have wind carry it
        if block.wind[0] != 0 and block.wind[1] != 0:
            neighbour = self.blocks[(row + block.wind[0]) % self.height][(col + block.wind[1]) % self.width]
            changes = {"pollution": block.pollution / POLLUTION_FACTOR}
            neighbour.pollution = min(neighbour.pollution + block.pollution / POLLUTION_FACTOR, POLLUTION_THRESHOLD)

            # If the wind is strong, it passes on and takes a new strength
            if block.wind[2] > STRONG_WIND_THRESHOLD:
                changes["wind"] = copy.deepcopy(block.wind)
                changes["wind"][2] = WIND_TTL

            changes["cloudy"] = block.cloudy[0]

            neighbour.pending_changes.append(changes)


        if block.cloudy[0]:
            # If its cloudy there is a random chance of rain (height and temperature help the rain)
            if random.randint(0, max(0, (RAIN_CHANCE - block.height//HEIGHT_RAIN_FACTOR + block.temperature//1))) == 0:
                block.temperature = clamp(block.temperature - 5, MIN_TEMPERATURE, MAX_TEMPERATURE)

            block.cloudy[0] = block.cloudy[1] != 0

        # Reduce each step
        block.cloudy[1] = max(block.cloudy[1] - 1, 0)
        block.wind[2] = max(block.wind[2] - 1, 0)
        block.pollution = max(block.pollution - POLLUTION_DOWNAGE, 0)

    def run(self):
        for row in range(self.height):
            for col in range(self.width):
                block_height = root.winfo_height() // self.height
                block_width = root.winfo_height() // self.width
                top = block_height * row
                left = block_width * col
                self.canvas.create_rectangle(top, left, top+self.block_height, left+self.block_width, fill="green", outline = 'red')
                self.canvas.pack()
                print(root.winfo_height(), top, left, top+self.block_height, left+self.block_width)

if __name__ == '__main__':
    e = EarthAutomaton()
    e.mainloop()

