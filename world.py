#!/usr/bin/env python3

import random
import copy
import time
from enum import Enum
from tkinter import *
import matplotlib.pyplot as plt


# I want to get the same random each run
random.seed(0)

MELTING_POINT = 20

POLLUTION_CHANGE = 0.001
POLLUTION_THRESHOLD = 0.05
POLLUTION_FACTOR = 3
POLLUTION_DOWNAGE = POLLUTION_CHANGE / 2

RAIN_TEMPATURE_CHANGE = 2.5
RAIN_POLLUTION_REDUCTION = 0.01
RAIN_CHANCE = 4
RAIN_HEIGHT_FACTOR = 20
RAIN_TEMPATURE_FACTOR = 20
RAIN_THRESHOLD = 8.5

WIND_TTL = 3
STRONG_WIND_THRESHOLD = 2
CLOUD_TTL = 2

MAX_TEMPERATURE = 45
MIN_TEMPERATURE = -10
MAX_HEIGHT = 100
CLOUDY_CHANCE = 4

TOTAL_DAYS = 365

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
        self.wind = [0, 0, 0] # [col, row, TTL]
        self.cloudy = [False, CLOUD_TTL] # [Cloudy, TTL]
        self.pollution = 0
        self.temperature = 0
        self.pending_changes = []
        self.days_from_last_rain = 0


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
            print("Invalid wind value", self.wind)
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
        self.next = Button(self.controls, text='Next 50',
                command=self.next_50_steps)
        self.next.grid(row=0, column=3, sticky=(W))

        self.info_label = Label(self.controls, text="")
        self.info_label.grid(row=0, column=4, sticky=(W))

        #Size Configuration
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=4)
        self.content.rowconfigure(1, weight=1)
        self.controls.columnconfigure(0,weight=1)
        self.controls.columnconfigure(1,weight=1)
        self.controls.columnconfigure(2,weight=1)
        self.controls.columnconfigure(3,weight=1)
        self.controls.columnconfigure(4,weight=1)
        self.controls.rowconfigure(0,weight=1)

        # Keep track of old steps
        self.old = []
        self.calculate_all()

    def calculate_all(self):
        for i in range(TOTAL_DAYS + 1):
            self.old.append(copy.deepcopy(self.blocks))
            self.step()

        self.standard_deviation()

    def next_step(self):
        self.day = min(self.day + 1, TOTAL_DAYS)
        self.draw()

    def next_50_steps(self):
        self.day = min(self.day + 50, TOTAL_DAYS)
        self.draw()

    def previous_step(self):
        self.day = max(self.day - 1, 0)
        self.draw()

    def draw(self, event=None):
        # Draw each of the rows based on its data
        self.canvas.delete('rect')
        width = int(self.canvas.winfo_width()/self.height)
        height = int(self.canvas.winfo_height()/self.width)
        for row in range(self.height):
            for col in range(self.width):
                x1 = col*width
                x2 = x1 + width
                y1 = row*height
                y2 = y1 + height

                color = self.old[self.day][row][col].get_color()
                cell = self.canvas.create_rectangle(x1, y1, x2, y2,
                        fill=color, tags='cell')

                center = ((x1+x2)//2, (y1+y2)//2)
                info = self.old[self.day][row][col].get_info()
                self.canvas.create_text(center, text=info)
                self.canvas.tag_bind(cell)

        self.day_label["text"] = "Day {}".format(self.day)
        self.info_label["text"] = self.get_day_summary(self.day)

    def get_day_summary(self, day):
        # Calculates the data for the day and formats a string summary
        pollution = 0
        temperature = 0
        for row in self.old[day]:
            for block in row:
                pollution += block.pollution
                temperature += block.temperature

        block_count = (self.height * self.width)
        temp, poll = temperature / block_count, pollution / block_count
        return "Average - Tempature:{:.2f}, pollution:{:.2f}".format(temp, poll)

    def step(self):
        for row in range(self.height):
            for col in range(self.width):
                self.evolve_rule(row, col)

        # Apply all necessary changes
        for row in range(self.height):
            for col in range(self.width):
                self.blocks[row][col].apply_changes()


    def init_cell_state(self):
        # Init each block instead of doing it manually.
        # Its not really random because I have a const random seed
        b = Block()
        b.type = random.choice(list(BlockType))
        b.height = random.randint(0, MAX_HEIGHT)
        b.cloudy = [random.randint(0, CLOUDY_CHANCE) == 0, CLOUD_TTL]
        b.wind = [random.randint(-1,1), random.randint(-1,1), random.randint(0,WIND_TTL)]
        b.temperature = random.randint(MIN_TEMPERATURE, MAX_TEMPERATURE)
        return b


    def evolve_rule(self, row, col):
        block = self.blocks[row][col]

        # Pollution makes the temperature rise
        block.temperature = min(block.pollution + block.temperature, MAX_TEMPERATURE)

        # If its hot, the iceberg melts
        if block.type == BlockType.ICEBERG and block.temperature >= MELTING_POINT:
            block.type = BlockType.SEA

        # Cities cause pollution
        elif block.type == BlockType.CITY:
            block.pollution = min(block.pollution + POLLUTION_CHANGE, POLLUTION_THRESHOLD)

        # If we have wind carry it
        if block.wind[0] != 0 and block.wind[1] != 0:
            neighbour = self.blocks[(row + block.wind[0]) % self.height][(col + block.wind[1]) % self.width]
            changes = {"pollution": block.pollution / POLLUTION_FACTOR}

            # If the wind is strong, it passes on and takes a new strength
            if block.wind[2] > STRONG_WIND_THRESHOLD:
                changes["wind"] = copy.deepcopy(block.wind)
                changes["wind"][2] = WIND_TTL

            changes["cloudy"] = block.cloudy[0]

            neighbour.pending_changes.append(changes)


        block.days_from_last_rain += 1
        # If its cloudy there is a random chance of rain (height and temperature help the rain)
        if block.cloudy[0]:
            will_rain = (block.days_from_last_rain - block.height//RAIN_HEIGHT_FACTOR - block.temperature//RAIN_TEMPATURE_FACTOR) / RAIN_CHANCE
            if will_rain > RAIN_THRESHOLD:
                block.temperature = clamp(block.temperature - RAIN_TEMPATURE_CHANGE, MIN_TEMPERATURE, MAX_TEMPERATURE)
                block.pollution = max(block.pollution - RAIN_POLLUTION_REDUCTION, 0)
                block.days_from_last_rain = 0

            block.cloudy[0] = block.cloudy[1] != 0

        # Reduce variables each step
        block.cloudy[1] = max(block.cloudy[1] - 1, 0)
        block.wind[2] = max(block.wind[2] - 1, 0)
        block.pollution = max(block.pollution - POLLUTION_DOWNAGE, 0)

    def standard_deviation(self):
        count = TOTAL_DAYS + 1

        # Calculate mean
        pollution = 0
        temperature = 0
        for day in range(TOTAL_DAYS):
            for row in self.old[day]:
                for block in row:
                    pollution += block.pollution
                    temperature += block.temperature

        mean_poll = pollution / count
        mean_temp = temperature / count

        # Calculate variance
        sum_mean_poll = 0
        sum_mean_temp = 0
        for day in range(TOTAL_DAYS):
            day_poll = 0
            day_temp = 0
            for row in self.old[day]:
                for block in row:
                    day_poll += block.pollution
                    day_temp += block.temperature

            sum_mean_poll += (mean_poll - day_poll) ** 2
            sum_mean_temp += (mean_temp - day_temp) ** 2


        variance_poll = sum_mean_poll / count
        variance_temp = sum_mean_temp / count

        # Calculate deviant
        deviant_poll = variance_poll ** 0.5
        deviant_temp = variance_temp ** 0.5


        data_days = [i for i in range(TOTAL_DAYS)]
        data_poll = []
        data_temp = []

        for day in range(TOTAL_DAYS):
            day_poll = 0
            day_temp = 0
            for row in self.old[day]:
                for block in row:
                    day_poll += block.pollution
                    day_temp += block.temperature

            data_poll.append((day_poll-mean_poll) / deviant_poll)
            data_temp.append((day_temp-mean_temp) / deviant_temp)

        plt.plot(data_days, data_poll, label="pollution")
        plt.plot(data_days, data_temp, label="temperature")
        plt.plot(data_days, [0 for x in range(TOTAL_DAYS)])

        plt.legend()
        plt.show()
        exit()

if __name__ == '__main__':
    e = EarthAutomaton()
    e.mainloop()

