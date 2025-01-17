import sys

import pygame
import thorpy
import copy, math, random
import numpy as np
import argparse
import json

from qrules import DSQGOL, SQGOL, liveliness

pygame.init()

# Interface Constants
PIXEL_SIZE = 10
LINE_WIDTH = 4
WIN_WIDTH = 600
WIN_HEIGHT = 400
WIN_INTERSPACE = 50
Y_LIMIT = WIN_HEIGHT // PIXEL_SIZE
X_LIMIT = WIN_WIDTH // PIXEL_SIZE

# Quantum Constants
ALIVE = np.array([1, 0])
DEAD = np.array([0, 1])
SUPERPOSITION_UP_LIMIT_ARG = 'sp_up'
SUPERPOSITION_UP_LIMIT_VAL = 0.51
SUPERPOSITION_DOWN_LIMIT_ARG = 'sp_down'
SUPERPOSITION_DOWN_LIMIT_VAL = 0.48

FILE_ARG = 'json'

#Update every 2ms
REFRESH_DEFAULT = 2
# REFRESH_DEFAULT = 0.1*1000
TARGET_FPS = 60

class GameState:
    game_paused = False
    step_forward = False

    def __init__(self, sp_up_limit=SUPERPOSITION_UP_LIMIT_VAL, sp_down_limit=SUPERPOSITION_DOWN_LIMIT_VAL, file_path=None, refresh_rate=REFRESH_DEFAULT):
        '''
        Inputs: Superposition limits and optional file to load from
        '''
        self.sp_up_limit = sp_up_limit
        self.sp_down_limit = sp_down_limit
        self.file_path = file_path
        self.refresh_rate = refresh_rate
        self.add_mode_classical = 1 # 0: kill cells, 1: create cell, 2: toggle cell
        self.add_mode_quantum = 3 # 0: kill cells, 1: create cell, 2: toggle cell, 3: random using sp_down_limit and sp_up_limit
        return

    def pause_simulation(self):
        print('before: self.game_paused: ', self.game_paused)
        self.game_paused = not self.game_paused
        print('after: self.game_paused: ', self.game_paused)
        return

    def advance_simulation(self):
        self.step_forward = True
        return

    def clear_grids(self):
        return

    def setup(self):
        print(f'file_path: {self.file_path}')

        ##### SETTING UP THE BACKGROUNDS
        # 2x2 window
        res = (2 * WIN_WIDTH + WIN_INTERSPACE, 2 * WIN_HEIGHT + WIN_INTERSPACE)
        self.screen = pygame.display.set_mode(res)
        # initial fill, which helps locate used/unused surfaces
        self.screen.fill((40,40,40))

        background_Final = pygame.Surface(self.screen.get_size())

        # Classical GOL Setup
        rect_classical = pygame.Rect(0, 0, WIN_WIDTH, WIN_HEIGHT)
        self.background_classical = background_Final.subsurface(rect_classical)
        self.background_classical = self.background_classical.convert()
        self.background_classical.fill((0, 0, 0))

        rect_interspace = pygame.Rect(WIN_WIDTH + WIN_INTERSPACE, 0,
                                      WIN_INTERSPACE, WIN_HEIGHT)
        interspace = background_Final.subsurface(rect_interspace)
        interspace = interspace.convert()
        interspace.fill((0, 0, 0))

        for x in range(0, WIN_INTERSPACE // PIXEL_SIZE):
            for y in range(Y_LIMIT):
                drawBlankSpace(interspace, x, y)

        # Quantum GOL Setup
        rect_quantum = pygame.Rect(WIN_WIDTH + WIN_INTERSPACE, 0, WIN_WIDTH,
                                   WIN_HEIGHT)
        self.background_quantum = background_Final.subsurface(rect_quantum)
        self.background_quantum = self.background_quantum.convert()
        self.background_quantum.fill((0, 0, 0))

        rect_interspace_horizontal = pygame.Rect(0, WIN_HEIGHT,
                                                 2 * WIN_WIDTH + WIN_INTERSPACE,
                                                 WIN_INTERSPACE)
        interspace_horizontal = background_Final.subsurface(
            rect_interspace_horizontal)
        interspace_horizontal = interspace_horizontal.convert()
        interspace_horizontal.fill((0, 0, 0))

        for x in range(0, (2 * WIN_WIDTH + WIN_INTERSPACE) // PIXEL_SIZE):
            for y in range(0, WIN_INTERSPACE // PIXEL_SIZE):
                drawBlankSpace(interspace_horizontal, x, y)

        # Fully Quantum GOL Setup
        # rect_fully_quantum = pygame.Rect(0, 0, WIN_WIDTH, WIN_HEIGHT)
        background_fully_quantum = None
        # background_fully_quantum = background_Final.subsurface(rect_quantum)
        # background_fully_quantum = background_fully_quantum.convert()
        # background_fully_quantum.fill((0, 0, 0))

        #####
        self.clock = pygame.time.Clock()

        self.isActive = True
        self.actionDown = False

        self.final = pygame.time.get_ticks()
        self.grid_quantum = Grid()
        self.grid_classical = Grid()
        # grid_fully_quantum = Grid()
        self.grid_fully_quantum = None
        self.debug = debugText(self.screen, self.clock)

        #Create the orginal grid pattern randomly
        if self.file_path is None:
            init_grid_random(self.sp_up_limit, self.sp_down_limit, self.grid_quantum,
                             self.background_quantum, self.grid_classical,
                             self.background_classical, self.grid_fully_quantum,
                             background_fully_quantum)
        else:
            init_grid_file(self.file_path, self.grid_quantum, self.background_quantum,
                           self.grid_classical, self.background_classical,
                           self.grid_fully_quantum, background_fully_quantum)

        self.screen.blit(self.background_classical, (0, 0))
        self.screen.blit(interspace, (WIN_WIDTH, 0))
        self.screen.blit(self.background_quantum, (WIN_WIDTH + WIN_INTERSPACE, 0))
        self.screen.blit(interspace_horizontal, (0, WIN_HEIGHT))
        # self.screen.blit(background_quantum, (WIN_WIDTH / 2 + WIN_INTERSPACE / 2, WIN_HEIGHT + WIN_INTERSPACE)) # this is actually the fully quantum area

        # add labels
        addLabel('Classical', (WIN_WIDTH / 2, WIN_HEIGHT + WIN_INTERSPACE/2), self.screen)
        addLabel('Quantum', (WIN_WIDTH + WIN_INTERSPACE + WIN_WIDTH / 2, WIN_HEIGHT + WIN_INTERSPACE/2), self.screen)

        pygame.display.flip()

        # ThorPy GUI
        # declaration of some ThorPy elements ...
        #element = thorpy.Element("Element")
        self.slider = thorpy.SliderX(1000, (0, 1000), "Refresh rate (ms):", initial_value=REFRESH_DEFAULT)
        self.slider_sp_down_limit = thorpy.SliderX(100, (0, 1), "Superposition DOWN limit:", initial_value=SUPERPOSITION_DOWN_LIMIT_VAL)
        self.slider_sp_up_limit = thorpy.SliderX(100, (0, 1), "Superposition UP limit:", initial_value=SUPERPOSITION_UP_LIMIT_VAL)
        # button_pause = thorpy.make_button("Pause", func=pause_simulation, params={"game_state": game_state})
        self.button_start = thorpy.make_button("Start", func=self.run)
        self.button_reset = thorpy.make_button("Reset", func=self.setup)
        self.button_pause = thorpy.make_button("Pause", func=self.pause_simulation)
        self.button_toggle_pause = thorpy.Togglable("Pause")

        self.button_next_step = thorpy.make_button("Next step", func=self.advance_simulation)
        self.button_cleargrids = thorpy.make_button("Clear grids", func=self.clear_grids)
        self.button_quit = thorpy.make_button("Quit", func=thorpy.functions.quit_func)
        self.dropdownlist_add_mode_classical = thorpy.DropDownListLauncher(const_text="Choose:",
                                                   var_text="",
                                                   titles=[str(i) * i for i in range(1, 9)])
        self.dropdownlist_add_mode_classical.scale_to_title()
        self.dropdownlist_add_mode_classical.max_chars = 12  # limit size of drop down list

        self.dropdownlist_add_mode_quantum = thorpy.DropDownListLauncher(const_text="Choose:",
                                                   var_text="",
                                                   titles=[str(i) * i for i in range(1, 9)])
        self.box = thorpy.Box(elements=[
                                        # self.button_start,
                                        # self.button_pause,
                                        self.button_toggle_pause,
                                        self.button_next_step,
                                        # self.button_cleargrids,
                                        self.slider,
                                        self.slider_sp_down_limit,
                                        self.slider_sp_up_limit,
                                        # self.dropdownlist_add_mode_classical,
                                        self.button_quit,
                                        ], size=(self.screen.get_size()[0],WIN_HEIGHT))
        # we regroup all elements on a menu, even if we do not launch the menu
        self.menu = thorpy.Menu(self.box)
        # important : set the screen as surface for all elements
        for element in self.menu.get_population():
            element.surface = self.screen
        # use the elements normally...
        self.box.set_topleft((0, WIN_HEIGHT + WIN_INTERSPACE))
        self.box.blit()
        self.box.update()

        self.run()

        return

    def run(self):
        # game loop start
        while self.isActive:

            self.clock.tick(TARGET_FPS)
            newgrid_quantum = Grid()
            newgrid_classical = Grid()
            # newgrid_fully_quantum = None #Grid()

            self.refresh_rate = self.slider.get_value()
            self.sp_up_limit = self.slider_sp_up_limit.get_value()
            self.sp_down_limit = self.slider_sp_down_limit.get_value()
            self.game_paused = self.button_toggle_pause.toggled
            if (pygame.time.get_ticks() - self.final > self.refresh_rate and not self.game_paused) or self.step_forward:
                self.step_forward = False
                self.background_quantum.fill((0, 0, 0))
                self.background_classical.fill((0, 0, 0))

                for x in range(0, X_LIMIT):
                    for y in range(0, Y_LIMIT):
                        subgrid = self.grid_quantum.getNeighboursAround(x, y)
                        newgrid_quantum.setCell(x, y, SQGOL(subgrid))
                        drawSquare(self.background_quantum, x, y,
                                   newgrid_quantum.getCell(x, y))
                        #Classic game of life
                        if (self.grid_classical.getCell(x, y) == ALIVE).all():
                            count = self.grid_classical.countNeighbours(x, y)
                            if count < 2:
                                newgrid_classical.setCell(x, y, DEAD)

                            elif count <= 3:
                                newgrid_classical.setCell(x, y, ALIVE)
                                drawSquareClassic(self.background_classical, x, y)

                            elif count >= 4:
                                newgrid_classical.setCell(x, y, DEAD)
                        else:
                            if self.grid_classical.countNeighbours(x, y) == 3:
                                newgrid_classical.setCell(x, y, ALIVE)
                                drawSquareClassic(self.background_classical, x, y)

                        # subgrid_fully_quantum = grid_fully_quantum.getNeighboursAround(x, y)
                        # newgrid_fully_quantum.setCell(x, y, DSQGOL(subgrid_fully_quantum)) # disabled, as it causes crashes with qiskit 0.36.1
                        # drawSquare(background_fully_quantum, x, y,
                        #            newgrid_fully_quantum.getCell(x, y))

                self.final = pygame.time.get_ticks()

            else:
                newgrid_quantum = self.grid_quantum
                newgrid_classical = self.grid_classical
                # newgrid_fully_quantum = grid_fully_quantum

            self.debug.update()

            # get mouse position
            x = pygame.mouse.get_pos()[0] // PIXEL_SIZE
            y = pygame.mouse.get_pos()[1] // PIXEL_SIZE

            actionDown = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print('QUITTING')
                    isActive = False
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.MOUSEBUTTONDOWN and 0 <= x < X_LIMIT and 0 <= y < Y_LIMIT:
                    actionDown = True

                    while actionDown:
                        x = pygame.mouse.get_pos()[0] // PIXEL_SIZE
                        y = pygame.mouse.get_pos()[1] // PIXEL_SIZE

                        if 0 <= x < X_LIMIT and 0 <= y < Y_LIMIT:
                            if (newgrid_classical.getCell(x, y) == DEAD).all():
                                newgrid_classical.setCell(x, y, ALIVE)
                                newgrid_quantum.setCell(x, y, random_cell(self.sp_up_limit, self.sp_down_limit))
                                # newgrid_fully_quantum.setCell(x, y, random_cell(sp_up_limit, sp_down_limit))

                                drawSquareClassic(self.background_classical, x, y)
                                drawSquare(self.background_quantum, x, y, newgrid_quantum.getCell(x, y))
                                # drawSquare for fully quantum version left
                            else:
                                newgrid_classical.setCell(x, y, DEAD)
                                newgrid_quantum.setCell(x, y, random_cell(self.sp_up_limit, self.sp_down_limit))
                                # newgrid_fully_quantum.setCell(x, y, random_cell(sp_up_limit, sp_down_limit))

                                drawSquareClassic(self.background_classical, x, y, DEAD)
                                drawSquare(self.background_quantum, x, y, newgrid_quantum.getCell(x, y))
                                # drawSquare for fully quantum version left

                        for event in pygame.event.get():
                            if event.type == pygame.MOUSEBUTTONUP:
                                actionDown = False

                        self.screen.blit(self.background_classical, (0, 0))
                        self.screen.blit(self.background_quantum, (WIN_WIDTH + 100, 0))
                        pygame.display.flip()
                self.menu.react(event)  # the menu automatically integrate your elements

            #Draws the new grid
            self.grid_quantum = newgrid_quantum
            self.grid_classical = newgrid_classical
            # grid_fully_quantum = newgrid_fully_quantum

            #Updates screen
            self.screen.blit(self.background_classical, (0, 0))
            # self.screen.blit(interspace, (WIN_WIDTH, 0))
            self.screen.blit(self.background_quantum, (WIN_WIDTH + WIN_INTERSPACE, 0))
            # self.screen.blit(interspace_horizontal, (0, WIN_HEIGHT))
            # self.screen.blit(
            #     background_fully_quantum,
            #     (WIN_WIDTH / 2 + WIN_INTERSPACE / 2, WIN_HEIGHT + WIN_INTERSPACE))
            self.debug.update()
            self.debug.printText()
            pygame.display.flip()


class Grid():
    def __init__(self, *args, **kwargs):
        self.grid = [[DEAD for i in range(Y_LIMIT)] for i in range(X_LIMIT)]

    def setCell(self, x, y, stat):
        self.grid[x][y] = stat

    def getCell(self, x, y):
        return self.grid[x][y]

    def getNeighboursAround(self, x, y):
        neighbors = []

        for sub_x in range(3):
            row = []

            for sub_y in range(3):
                actual_x = x - 1 + sub_x
                if actual_x < 0:
                    actual_x = X_LIMIT + actual_x
                elif actual_x >= X_LIMIT:
                    actual_x -= X_LIMIT

                actual_y = y - 1 + sub_y
                if actual_y < 0:
                    actual_y = Y_LIMIT + actual_y
                elif actual_y >= Y_LIMIT:
                    actual_y -= Y_LIMIT

                cell = self.getCell(actual_x, actual_y)

                row.append(np.array(cell))

            neighbors.append(np.array(row))

        return neighbors

    def countNeighbours(self, x, y):
        neighbours = self.getNeighboursAround(x, y)
        return liveliness(neighbours)

        count = 0
        for x in range(3):
            for y in range(3):
                if x == 1 and y == 1:
                    continue
                count += 1 if (neighbours[x][y] == np.array([0., 1.
                                                             ])).all() else 0

        return count


class debugText():
    def __init__(self, screen, clock, *args, **kwargs):
        self.screen = screen
        self.clock = clock
        self.font = pygame.font.SysFont("Monospaced", 20)

    def printText(self):
        label_frameRate = self.font.render("FPS: " + str(self.clock.get_fps()),
                                           1, (255, 255, 255))
        self.screen.blit(label_frameRate, (8, 22))

    def update(self, *args, **kwargs):
        self.screen = kwargs.get("screen", self.screen)
        self.clock = kwargs.get("clock", self.clock)


# Initialize the grids randomly
def init_grid_random(sp_up_limit, sp_down_limit, grid, background, grid2,
                     background2, grid_fully_quantum,
                     background_fully_quantum):
    for x in range(X_LIMIT):
        for y in range(Y_LIMIT):
            cell = random_cell(sp_up_limit, sp_down_limit)
            grid.setCell(x, y, cell)
            drawSquare(background, x, y, cell)

            # grid_fully_quantum.setCell(x, y, cell)
            # drawSquare(background_fully_quantum, x, y, cell)

            if cell[1] >= 0.5:
                grid2.setCell(x, y, DEAD)
                drawSquareClassic(background2, x, y)
            else:
                grid2.setCell(x, y, ALIVE)
                drawSquareClassic(background2, x, y)


# Initialize the grids from a json prespecification
def init_grid_file(file_path, grid, background, grid2, background2,
                   grid_fully_quantum, background_fully_quantum):
    with open(file_path) as json_file:
        data = json.load(json_file)

        row_inc = len(data) // 2
        column_inc = len(data[0]) // 2

        grid_x_inc = X_LIMIT // 2
        grid_y_inc = Y_LIMIT // 2

        for r, row in enumerate(data):
            for c, elem in enumerate(row):
                cell = json_cell(elem)
                final_x = grid_x_inc - column_inc + c
                final_y = grid_y_inc - row_inc + r

                grid.setCell(final_x, final_y, cell)
                drawSquare(background, final_x, final_y, cell)

                if cell[1] >= 0.5:
                    grid2.setCell(final_x, final_y, DEAD)
                    # drawSquareClassic(background2, final_x, final_y)
                    print(f'{c}, {r} -> {cell[0]}, {cell[1]} -> {final_x}, {final_y}, DEAD')
                else:
                    grid2.setCell(final_x, final_y, ALIVE)
                    drawSquareClassic(background2, final_x, final_y)
                    print(f'{c}, {r} -> {cell[0]}, {cell[1]} -> {final_x}, {final_y}, ALIVE')

def json_cell(a):
    b = math.sqrt(1 - a**2)
    return np.array([a, b])


def random_cell(up_limit, down_limit):
    a = random.random()
    b = math.sqrt(1 - a**2)
    if b >= up_limit:
        b = 1.
        a = 0.
    elif b <= down_limit:
        b = 0.
        a = 1.

    return np.array([a, b])


def drawSquare(background, x, y, array):
    #Cell colour
    value = 255.0 - np.floor((array[1]**2) * 255)
    colour = value, value, value
    pygame.draw.rect(background, colour,
                     (x * PIXEL_SIZE, y * PIXEL_SIZE, PIXEL_SIZE, PIXEL_SIZE),
                     LINE_WIDTH)


def drawBlankSpace(background, x, y):
    #Random cell colour
    colour = 40, 40, 40
    pygame.draw.rect(background, colour,
                     (x * PIXEL_SIZE, y * PIXEL_SIZE, PIXEL_SIZE, PIXEL_SIZE))


def drawSquareClassic(background, x, y, state=ALIVE):
    if (state==ALIVE).all():
        colour = 255, 255, 255
    else:
        colour = 0, 0, 0
    pygame.draw.rect(background, colour,
                     (x * PIXEL_SIZE, y * PIXEL_SIZE, PIXEL_SIZE, PIXEL_SIZE),
                     LINE_WIDTH)


def addLabel(txt, pos, screen):
    textcolor = (255, 255, 255)
    smallfont = pygame.font.SysFont('Corbel', 35)
    info_text = smallfont.render(txt, True, textcolor)
    text_width, text_height = smallfont.size(txt)
    x = pos[0] - text_width/2
    y = pos[1] - text_height / 2
    screen.blit(info_text, (x,y))
    return

def startgui(args):
    pygame.init()
    res = (720, 720)
    screen = pygame.display.set_mode(res)
    color = (255, 255, 255)
    color_light = (170, 170, 170)
    color_dark = (100, 100, 100)
    width = self.screen.get_width()
    height = self.screen.get_height()
    smallfont = pygame.font.SysFont('Corbel', 35)

    button_height = 40
    button_width = 280
    gap_height = 10

    quit_text = smallfont.render('Quit', True, color)
    random_sim_text = smallfont.render('Start random simulation', True, color)
    empty_sim_text = smallfont.render('Start empty simulation', True, color)
    json_sim_text = smallfont.render('Load simulation', True, color)

    def on_quit_button(x, y):
        if width / 2 <= x <= width / 2 + button_width and height / 2 <= y <= height / 2 + button_height:
            return True

    def on_random_sim_button(x, y):
        if width / 2 <= x <= width / 2 + button_width and height / 2 + button_height + gap_height <= y <= height / 2 + 2 * button_height + gap_height:
            return True

    def on_empty_sim_button(x, y):
        if width / 2 <= x <= width / 2 + button_width and height / 2 + 2 * button_height + 2 * gap_height <= y <= height / 2 + (
                3 * button_height + 2 * gap_height):
            return True

    def on_json_sim_button(x, y):
        if width / 2 <= x <= width / 2 + button_width and height / 2 + 3 * button_height + 3 * gap_height <= y <= height / 2 + 4 * button_height + 3 * gap_height:
            return True

    game_start = False

    while True:

        mouse = pygame.mouse.get_pos()

        # Handle clicks for each button
        for ev in pygame.event.get():

            if ev.type == pygame.QUIT:
                pygame.quit()

            if ev.type == pygame.MOUSEBUTTONDOWN:
                if on_quit_button(mouse[0], mouse[1]):
                    pygame.quit()
                elif on_random_sim_button(mouse[0], mouse[1]):
                    game_start = True
                elif on_empty_sim_button(mouse[0], mouse[1]):
                    game_start = False
                elif on_json_sim_button(mouse[0], mouse[1]):
                    game_start = False

        screen.fill((60, 25, 60))

        # Change buttons to lighter shade if hovered upon
        if on_quit_button(mouse[0], mouse[1]):
            pygame.draw.rect(
                screen, color_light,
                (width / 2, height / 2, button_width, button_height))
        else:
            pygame.draw.rect(
                screen, color_dark,
                (width / 2, height / 2, button_width, button_height))

        if on_random_sim_button(mouse[0], mouse[1]):
            pygame.draw.rect(screen, color_light,
                             (width / 2, height / 2 + button_height +
                              gap_height, button_width, button_height))
        else:
            pygame.draw.rect(screen, color_dark,
                             (width / 2, height / 2 + button_height +
                              gap_height, button_width, button_height))

        if on_empty_sim_button(mouse[0], mouse[1]):
            pygame.draw.rect(screen, color_light,
                             (width / 2, height / 2 + 2 * button_height +
                              2 * gap_height, button_width, button_height))
        else:
            pygame.draw.rect(screen, color_dark,
                             (width / 2, height / 2 + 2 * button_height +
                              2 * gap_height, button_width, button_height))

        if on_json_sim_button(mouse[0], mouse[1]):
            pygame.draw.rect(screen, color_light,
                             (width / 2, height / 2 + 3 * button_height +
                              3 * gap_height, button_width, button_height))
        else:
            pygame.draw.rect(screen, color_dark,
                             (width / 2, height / 2 + 3 * button_height +
                              3 * gap_height, button_width, button_height))

        screen.blit(quit_text, (width / 2, height / 2))
        screen.blit(random_sim_text,
                    (width / 2, height / 2 + (button_height + gap_height)))
        screen.blit(empty_sim_text,
                    (width / 2, height / 2 + 2 * (button_height + gap_height)))
        screen.blit(json_sim_text,
                    (width / 2, height / 2 + 3 * (button_height + gap_height)))
        pygame.display.flip()
        pygame.display.update()

        if game_start:
            main(args[SUPERPOSITION_UP_LIMIT_ARG],
                 args[SUPERPOSITION_DOWN_LIMIT_ARG], args[FILE_ARG], args['refresh_rate'])

def main(sp_up_limit=SUPERPOSITION_UP_LIMIT_VAL, sp_down_limit=SUPERPOSITION_DOWN_LIMIT_VAL, file_path=None, refresh_rate=REFRESH_DEFAULT):
    game_state = GameState(sp_up_limit, sp_down_limit, file_path, refresh_rate)
    game_state.setup()

# Code starts here.
# Takes in optional arguments and calls main()
if __name__ == "__main__":
    # if not len(sys.argv) > 1:
    #     # start GUI
    #     startgui()
    # else:
    # parse arguments
    parser = argparse.ArgumentParser(description='Quantum Game of Life')
    parser.add_argument('--no-gui', action='store_true', help='Start simulation directly without loading GUI.')
    parser.add_argument('--{}'.format(SUPERPOSITION_UP_LIMIT_ARG),
                        type=float,
                        default=SUPERPOSITION_UP_LIMIT_VAL,
                        help='Superposition UP limit (default: {})'.format(
                            SUPERPOSITION_UP_LIMIT_VAL))
    parser.add_argument('--{}'.format(SUPERPOSITION_DOWN_LIMIT_ARG),
                        type=float,
                        default=SUPERPOSITION_DOWN_LIMIT_VAL,
                        help='Superposition DOWN limit (default: {})'.format(
                            SUPERPOSITION_DOWN_LIMIT_VAL))
    parser.add_argument('--{}'.format(FILE_ARG),
                        help='Path to JSON file with pre-configured seed',
                        default=None)
    parser.add_argument('--refresh-rate',
                        type=float,
                        help='Refresh rate in ms (default: {})'.format(REFRESH_DEFAULT),
                        default=REFRESH_DEFAULT)
    args = vars(parser.parse_args())

    if True: #args['no_gui']:
        # start simulation directly
        main(args[SUPERPOSITION_UP_LIMIT_ARG],
             args[SUPERPOSITION_DOWN_LIMIT_ARG], args[FILE_ARG], args['refresh_rate'])
    else:
        # start GUI
        startgui(args)
