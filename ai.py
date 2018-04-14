import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import time
import sys

degree = 0
b_done = True
rotating_speed = 10


# region Enums
class Direction:
	standing = 0
	laying_x = 1
	laying_y = 2


class Tile:
	empty = 0
	floor = 1
	switch = 2
	bridge = 3
	goal = 4
	player = 5

	# @formatter:off
	colors = {
		'gray'	:	(	0.83137256,	0.83137256,	0.83137256, 1	),
		'white'	:	(	1, 			1, 			1, 			1	),
		'yellow':	(	1, 			1, 			0.4, 		1	),
		'green'	:	(	0.59607846,	0.9843137,	0.59607846, 1	),
	}
	# @formatter:on

	@staticmethod
	def get_color(tile_type):
		if tile_type == Tile.floor:
			return Tile.colors['white']
		elif tile_type == Tile.goal:
			return Tile.colors['yellow']
		elif tile_type == Tile.player:
			return Tile.colors['green']
		else:
			return Tile.colors['gray']


class Cube:
	vertices = np.array([
		[1, 0, 0],
		[1, 1, 0],
		[0, 1, 0],
		[0, 0, 0],
		[1, 0, 1],
		[1, 1, 1],
		[0, 0, 1],
		[0, 1, 1]
	])
	edges = np.array([
		[0, 1],
		[0, 3],
		[0, 4],
		[2, 1],
		[2, 3],
		[2, 7],
		[6, 3],
		[6, 4],
		[6, 7],
		[5, 1],
		[5, 4],
		[5, 7]
	])
	faces = np.array([
		[0, 1, 2, 3],
		[0, 1, 5, 4],
		[4, 5, 7, 6],
		[1, 2, 7, 5],
		[0, 3, 6, 4],
		[2, 3, 6, 7],
	])

	@staticmethod
	def draw_cube(position, size, face_color=(0.94, 0.66, 0.75), border_color=(0.5, 0.5, 0.5)):
		Cube.draw_border(position, size, border_color)
		Cube.draw_faces(position, size, face_color)

	@staticmethod
	def draw_faces(position, size, face_color):
		pos_x, pos_y = position
		size_x, size_y, size_z = size
		for i, face in enumerate(Cube.faces):
			glBegin(GL_POLYGON)
			glColor(face_color)
			for vertex in face:
				glVertex3f(
						Cube.vertices[vertex, 0] * size_x + pos_x,
						-(Cube.vertices[vertex, 1] * size_y + pos_y),
						Cube.vertices[vertex, 2] * size_z
				)
			glEnd()

	@staticmethod
	def draw_border(position, size, border_color):
		pos_x, pos_y = position
		size_x, size_y, size_z = size
		glBegin(GL_LINES)
		glColor(border_color)
		for edge in Cube.edges:
			for vertex in edge:
				glVertex3f(
						Cube.vertices[vertex, 0] * size_x + pos_x,
						-(Cube.vertices[vertex, 1] * size_y + pos_y),
						Cube.vertices[vertex, 2] * size_z
				)
		glEnd()


class Method:
	depth_first_search = 0
	breadth_first_search = 1
	hill_climbing = 2


# endregion

# region Global Variables (Default)
# Player Control
PLAYABLE = True
# Calculate path and display using OpenGL
VISUALIZE = True
# map of the level
ALGORITHM = Method.hill_climbing

LEVEL_ARRAY = np.array([
	[1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
	[1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
	[1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
	[0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
	[0, 0, 0, 0, 0, 1, 1, 4, 1, 1],
	[0, 0, 0, 0, 0, 1, 1, 1, 1, 0]
])
# self explanatory
HEIGHT, WIDTH = LEVEL_ARRAY.shape


# endregion


# Mainly to setup OpenGL
class Display:
	def __init__(self, title='', fps=60, fullscreen=False, size=(800, 600), offset=(WIDTH, HEIGHT)):
		self.title = title
		self.fps = fps
		self.fullscreen = fullscreen
		self.size = size
		self.width, self.height = offset

		self.delta = 0
		self.currentFrame = self.get_time()
		self.lastFrame = self.get_time()
		if self.fullscreen:
			self.surface = pygame.display.set_mode(self.size, FULLSCREEN | HWSURFACE | DOUBLEBUF | OPENGL)
		else:
			self.surface = pygame.display.set_mode(self.size, DOUBLEBUF | OPENGL)

		pygame.display.set_caption(self.title)

		glClearColor(0.83137254902, 0.83137254902, 0.83137254902, 1)
		gluPerspective(60, (size[0] / size[1]), 0.1, 1000.0)
		gluLookAt(4, 4, 8, 0, 0, 0, 0, 0, 1)

		glRotatef(180, 0, 0, 1)
		glRotatef(-45, 0, 0, 1)
		glTranslatef(-self.width / 2, self.height / 2, 0)
		glEnable(GL_DEPTH_TEST)
		glEnable(GL_LINE_SMOOTH)
		glEnable(GL_POLYGON_SMOOTH)
		glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
		glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)
		glEnable(GL_BLEND)
		glLineWidth(1)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

	def update(self):
		self.delta = self.currentFrame - self.lastFrame
		pygame.display.flip()
		self.lastFrame = self.get_time()

		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glViewport(0, 0, self.surface.get_width(), self.surface.get_height())

	@staticmethod
	def is_trying_to_quit(event):
		pressed_keys = pygame.key.get_pressed()
		alt_pressed = pressed_keys[pygame.K_LALT] or pressed_keys[pygame.K_RALT]
		x_button = event.type == pygame.QUIT
		alt_f4 = alt_pressed and event.type == pygame.KEYDOWN and event.key == pygame.K_F4
		escape = event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
		return x_button or alt_f4 or escape

	@staticmethod
	def get_time():
		return time.time() * 1000

# region State (including: location, direction, and map)


class State:

	def __init__(self, start=(0, 0, Direction.standing), board=LEVEL_ARRAY):
		self.x, self.y, self.rot = start
		self.board = board

		if not self.is_valid():
			print('Invalid starting position')
			sys.exit()

		self.start = start
		self.prev = start
		self.states = [start]
		self.visited = [start]
		self.all_moves = (
			self.try_move_up,
			self.try_move_down,
			self.try_move_left,
			self.try_move_right
		)
		self.eval_map = None

	# region get/set
	def set_player_position(self, state):
		self.x, self.y, self.rot = state

	def get_player_position(self):
		return self.x, self.y, self.rot

	# endregion

	# region all_moves
	def try_move_up(self, playable=False):
		self.prev = self.get_player_position()
		if self.rot == Direction.standing:
			self.y -= 2
			self.rot = Direction.laying_y
		elif self.rot == Direction.laying_x:
			self.y -= 1
		elif self.rot == Direction.laying_y:
			self.y -= 1
			self.rot = Direction.standing

		if self.is_valid():
			if playable:
				return True
			return self.add_state()
		self.set_player_position(self.prev)
		return False

	def try_move_down(self, playable=False):
		self.prev = self.get_player_position()
		if self.rot == Direction.standing:
			self.y += 1
			self.rot = Direction.laying_y
		elif self.rot == Direction.laying_x:
			self.y += 1
		elif self.rot == Direction.laying_y:
			self.y += 2
			self.rot = Direction.standing

		if self.is_valid():
			if playable:
				return True
			return self.add_state()
		self.set_player_position(self.prev)
		return False

	def try_move_left(self, playable=False):
		self.prev = self.get_player_position()
		if self.rot == Direction.standing:
			self.x -= 2
			self.rot = Direction.laying_x
		elif self.rot == Direction.laying_x:
			self.x -= 1
			self.rot = Direction.standing
		elif self.rot == Direction.laying_y:
			self.x -= 1

		if self.is_valid():
			if playable:
				return True
			return self.add_state()
		self.set_player_position(self.prev)
		return False

	def try_move_right(self, playable=False):
		self.prev = self.get_player_position()
		if self.rot == Direction.standing:
			self.x += 1
			self.rot = Direction.laying_x
		elif self.rot == Direction.laying_x:
			self.x += 2
			self.rot = Direction.standing
		elif self.rot == Direction.laying_y:
			self.x += 1

		if self.is_valid():
			if playable:
				return True
			return self.add_state()
		self.set_player_position(self.prev)
		return False

	# endregion

	# region Utils
	def is_floor(self, x, y):
		height, width = self.board.shape
		if x < 0 or x >= width or y < 0 or y >= height:
			return False
		return self.board[y, x] != Tile.empty

	def is_valid(self):
		if not self.is_floor(self.x, self.y):
			return False

		if self.rot == Direction.standing:
			return True
		elif self.rot == Direction.laying_x:
			return self.is_floor(self.x + 1, self.y)
		elif self.rot == Direction.laying_y:
			return self.is_floor(self.x, self.y + 1)

	def add_state(self):
		data = (self.x, self.y, self.rot)
		if data not in self.visited:
			self.visited.append(data)
			self.states.append(data)
			return True
		return False

	def is_goal(self, x, y):
		return self.board[y, x] == Tile.goal

	def check_goal(self):
		return self.rot == Direction.standing and self.is_goal(self.x, self.y)

	# endregion

	# region Graphics
	def draw_level(self):
		height, width = self.board.shape

		for x in range(width):
			for y in range(height):
				tile = self.board[y][x]
				if tile != Tile.empty:
					if (
							x == self.start[0] and y == self.start[1]) or (
							x == self.start[0] + 1 and y == self.start[1] and self.start[2] == Direction.laying_x) or (
							x == self.start[0] and y == self.start[1] + 1 and self.start[2] == Direction.laying_y):
						Cube.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Tile.get_color(Tile.player))
					else:
						Cube.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Tile.get_color(tile))

	def draw_player(self):
		global degree
		current = self.get_player_position()
		x_diff = current[0] - self.prev[0]
		y_diff = current[1] - self.prev[1]
		x_center = self.prev[0] + x_diff if x_diff > 0 else self.prev[0]
		y_center = self.prev[1] + y_diff if y_diff > 0 else self.prev[1]
		degree = 90 if degree >= 90 else degree + rotating_speed

		glPushMatrix()
		if current != self.prev:
			glTranslate(x_center, -y_center, 0)
			glRotate(degree, y_diff, x_diff, 0)
			glTranslate(-x_center, y_center, 0)

		glLineWidth(2)
		if self.prev[2] == Direction.standing:
			Cube.draw_cube(position=(self.prev[0], self.prev[1]), size=(1, 1, 2), border_color=(0.42, 0.56, 0.87))
		elif self.prev[2] == Direction.laying_x:
			Cube.draw_cube(position=(self.prev[0], self.prev[1]), size=(2, 1, 1), border_color=(0.42, 0.56, 0.87))
		elif self.prev[2] == Direction.laying_y:
			Cube.draw_cube(position=(self.prev[0], self.prev[1]), size=(1, 2, 1), border_color=(0.42, 0.56, 0.87))
		glPopMatrix()
		glLineWidth(1)

	# endregion

	def h_map(self):
		([y], [x]) = np.where(self.board == Tile.goal)
		state = State((x, y, Direction.standing))
		q = [0]
		result = np.full((3, HEIGHT, WIDTH), 1000)
		result[0, y, x] = 0

		while state.states:
			current_state = state.states.pop(0)
			count = q.pop(0)
			for move in state.all_moves:
				state.set_player_position(current_state)
				if move():
					result[state.rot, state.y, state.x] = count + 1
					q.append(count + 1)

		return result

	def evaluate(self):
		return self.eval_map[self.rot, self.y, self.x]


# endregion


# region Algorithm
class Solver:
	# Simple Depth First Search to calculate time
	@staticmethod
	def dfs(state: State):
		while state.states:
			current_state = state.states.pop()
			for move in state.all_moves:
				state.set_player_position(current_state)
				if move():
					if state.check_goal():
						return

	# Simple Breadth First Search to calculate time
	@staticmethod
	def bfs(state: State):
		while state.states:
			current_state = state.states.pop(0)
			for move in state.all_moves:
				state.set_player_position(current_state)
				if move():
					if state.check_goal():
						return

	# Depth First Search with path to visualize
	@staticmethod
	def dfs_path(state: State):
		s = [[(state.x, state.y, state.rot)], ]
		while state.states:
			current_state = state.states.pop()
			path = s.pop()

			for move in state.all_moves:
				state.set_player_position(current_state)
				if move():
					if state.check_goal():
						k = path + [(state.x, state.y, state.rot)]
						return k
					s.append(path + [(state.x, state.y, state.rot)])

	# Breadth First Search with path to visualize
	@staticmethod
	def bfs_path(state: State):
		q = [[(state.x, state.y, state.rot)], ]
		while state.states:
			current_state = state.states.pop(0)
			path = q.pop(0)

			for move in state.all_moves:
				state.set_player_position(current_state)
				if move():
					if state.check_goal():
						k = path + [(state.x, state.y, state.rot)]
						return k
					q.append(path + [(state.x, state.y, state.rot)])

	# Depth First Search with recursion
	@staticmethod
	def dfs_rec(state: State):
		if state.check_goal():
			raise ValueError('Found')

		current_state = state.get_player_position()
		# if path is None:
		#     path = [current_state]

		for move in state.all_moves:
			state.set_player_position(current_state)
			if move():
				Solver.dfs_rec(state)

	# Hill Climbing
	@staticmethod
	def hill_climbing(state: State):
		state.eval_map = state.h_map()
		path = []

		while True:
			next_eval = 1000
			next_state = None
			current_state = state.get_player_position()
			path.append(current_state)
			for move in state.all_moves:
				if move():
					x = state.evaluate()
					if x < next_eval:
						next_eval = x
						next_state = state.get_player_position()
				state.set_player_position(current_state)

			if next_eval >= state.evaluate():
				return path
			state.set_player_position(next_state)


# endregion

def handle_move_event(move, action, state):
	prev = state.prev
	current = state.get_player_position()
	if move(True):
		action.append(move)
	state.prev = prev
	state.set_player_position(current)


def main(playable=PLAYABLE, visualize=VISUALIZE, method=ALGORITHM, level=LEVEL_ARRAY):
	global degree
	state = State((1, 1, Direction.standing), level)

	if not playable:
		if visualize:
			if method is Method.hill_climbing:
				a = Solver.hill_climbing(state)
			elif method is Method.breadth_first_search:
				a = Solver.bfs_path(state)
			elif method is Method.depth_first_search:
				a = Solver.dfs_path(state)
		else:
			if method is Method.hill_climbing:
				Solver.hill_climbing(state)
			elif method is Method.breadth_first_search:
				Solver.bfs(state)
			elif method is Method.depth_first_search:
				Solver.dfs(state)
			return

	pygame.init()
	display = Display('Bloxorz', offset=(level.shape[1], level.shape[0]))
	font = pygame.font.Font(None, 30)
	clock = pygame.time.Clock()

	steps = 0
	action_queue = []
	while True:
		if playable and len(action_queue) != 0 and degree == 90:
			degree = 0
			next_action = action_queue[-1]
			next_action(True)
			action_queue = []

		for event in pygame.event.get():
			if display.is_trying_to_quit(event):
				return

			if playable:

				if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
					handle_move_event(state.try_move_up, action_queue, state)
				elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
					handle_move_event(state.try_move_down, action_queue, state)
				elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
					handle_move_event(state.try_move_left, action_queue, state)
				elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
					handle_move_event(state.try_move_right, action_queue, state)
			else:
				if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
					steps += 1
					if steps >= len(a):
						steps -= len(a)
					state.set_player_position(a[steps])
				if event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
					steps -= 1
					if steps < 0:
						steps += len(a)
					state.set_player_position(a[steps])
		state.draw_level()
		state.draw_player()
		display.update()


main(
		# level=np.array([
		# 	[1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
		# 	[1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
		# 	[1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
		# 	[0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
		# 	[0, 0, 0, 0, 0, 1, 1, 4, 1, 1],
		# 	[0, 0, 0, 0, 0, 1, 1, 1, 1, 0]
		# ])
)
