# coding=utf-8
import sys
from typing import List, Tuple

import numpy as np
from OpenGL.GL import glLineWidth, glPopMatrix, glPushMatrix, glRotate, glTranslate

from draw import Draw
from utility import Direction, Tile

# Nothing:			---
# Heavy/Soft Floor:	ooo|iii
# Player: 			PPP|ppp
# Goal: 			ggg
# Switches:			(Hard|Soft Switch)	(on|toggle|off)			[id] 					- (S|s)	(0|1|2)	[0-9]
# Bridges:			(On|off)			(up|down|left|right)	[id] 					- [B|b]	(0|1|2)	[0-9]
# Teleport:			t					[id]					(trigger|first|second) 	- t		[0-9]	(t|0|1)

rotating_speed = 15


class State:

	def __init__(self, stage=1):
		self.steps = 0
		self.degree = 0
		self.found = False
		self.bridges = {}
		self.switches = {}
		self.teleporter = {}
		self.player = np.array([])
		self.board = self.load_level(stage)
		self.previous = self.player

		if not self.is_valid(self.player):
			print('Invalid starting position')
			sys.exit()

		self.states = [(self.player.tolist(), self.get_bridges_status(self.board))]
		self.visited = [(self.player.tolist(), self.get_bridges_status(self.board))]
		self.move_direction = 'none'

	# self.eval_map = None

	@staticmethod
	def check_goal(player: np.ndarray, board: np.ndarray):
		return np.array_equal(player[0], player[1]) and board[player[0, 1], player[0, 0]] == Tile.goal

	@staticmethod
	def get_direction(player: np.ndarray):
		diff = player[1] - player[0]
		if diff[0] == 0 and diff[1] == 0:
			return Direction.standing
		elif (diff[0] == 1 or diff[0] == -1) and diff[1] == 0:
			return Direction.laying_x
		elif (diff[1] == 1 or diff[1] == -1) and diff[0] == 0:
			return Direction.laying_y
		else:
			return Direction.none

	def is_in_bound(self, x: int, y: int):
		height, width = self.board.shape
		return 0 <= x < width and 0 <= y < height

	def is_empty_floor(self, x: int, y: int):
		tile = str(self.board[y, x])
		return tile == Tile.empty or tile.startswith('b')

	def is_valid(self, player: np.ndarray):
		block1, block2 = player
		if not self.is_in_bound(*block1) or not self.is_in_bound(*block2):
			return False

		if self.is_empty_floor(*block1) or self.is_empty_floor(*block2):
			return False

		if np.array_equal(block1, block2):
			tile = str(self.board[block1[1], block1[0]])
			return tile != Tile.soft_floor
		return True

	def activate_bridge(self, bridge_id: str, board: np.ndarray, mode=1):
		mode = int(mode)
		for (x, y) in self.bridges[bridge_id]:
			if mode == 0:
				# on
				board[y, x] = str(board[y, x]).upper()
			elif mode == 1:
				# toggle
				board[y, x] = str(board[y, x]).swapcase()
			elif mode == 2:
				# off
				board[y, x] = str(board[y, x]).lower()

		return board

	def check_switch(self, player: np.ndarray):
		direction = self.get_direction(player)
		block1 = tuple(player[0])
		block2 = tuple(player[1])
		board = np.copy(self.board)

		if direction == Direction.standing:
			if block1 in self.switches:
				for switch in self.switches[block1]:
					if switch[0] == 't':
						player = np.array(self.teleporter[switch])
					else:
						board = self.activate_bridge(switch[2], board, switch[1])
		else:
			if block1 in self.switches:
				for switch in self.switches[block1]:
					if str(switch).startswith('s'):
						board = self.activate_bridge(switch[2], board, switch[1])

			if direction != Direction.none and block2 in self.switches:
				for switch in self.switches[block2]:
					if str(switch).startswith('s'):
						board = self.activate_bridge(switch[2], board, switch[1])
		return player, board

	def check_merge(self, player: np.ndarray):
		diff = player[1] - player[0]
		direction = self.get_direction(player)
		if (direction == Direction.laying_x and diff[0] == -1) or (direction == Direction.laying_y and diff[1] == -1):
			return True
		return False

	def try_move(self, action: str):
		player = np.copy(self.player)
		direction = self.get_direction(player)

		if direction == Direction.standing:
			if action == 'up':
				player[:, 1] -= [2, 1]
			elif action == 'down':
				player[:, 1] += [1, 2]
			elif action == 'left':
				player[:, 0] -= [2, 1]
			elif action == 'right':
				player[:, 0] += [1, 2]
		elif direction == Direction.laying_x:
			if action == 'up':
				player[:, 1] -= [1, 1]
			elif action == 'down':
				player[:, 1] += [1, 1]
			elif action == 'left':
				player[:, 0] -= [1, 2]
			elif action == 'right':
				player[:, 0] += [2, 1]
		elif direction == Direction.laying_y:
			if action == 'up':
				player[:, 1] -= [1, 2]
			elif action == 'down':
				player[:, 1] += [2, 1]
			elif action == 'left':
				player[:, 0] -= [1, 1]
			elif action == 'right':
				player[:, 0] += [1, 1]
		else:
			if action == 'up':
				player[0, 1] -= 1
			elif action == 'down':
				player[0, 1] += 1
			elif action == 'left':
				player[0, 0] -= 1
			elif action == 'right':
				player[0, 0] += 1
			elif action == 'swap':
				player[[0, 1], :] = player[[1, 0], :]
				self.degree = 90

		return player

	def move(self, action: str, commit=True):
		self.previous = np.copy(self.player)
		player = self.try_move(action)

		if self.is_valid(player):
			if action != 'swap':
				player, board = self.check_switch(player)
			else:
				board = self.board

			if commit:
				self.board = board
				self.player = player
				self.move_direction = action
				return True
			else:
				if self.check_merge(player):
					player[[0, 1], :] = player[[1, 0], :]

				if self.check_goal(player, board):
					self.found = True
				return self.add_state(player, board)

		return False

	# region Utils
	def get_bridges_status(self, board: np.ndarray):
		result = []
		for key, value in self.bridges.items():
			x, y = value[0]
			result.append((key, board[y, x][0]))
		return result

	def add_state(self, player: np.ndarray, board: np.ndarray):
		data = (player.tolist(), self.get_bridges_status(board))
		if data not in self.visited:
			self.visited.append(data)
			self.states.append(data)
			return True
		return False

	def load_state(self, player, bridges: List[Tuple[str, str]]):
		self.player = np.array(player)
		for bridge in bridges:
			# bridges = [('1', 'b'), ('2', 'B'), ('0', 'B')]
			# bridge = ('1', 'b')
			# bridge[0] = '1'
			# self.bridges[bridge[0]]= [(11, 1)]
			# => x, y = 11, 1
			# self.board[y, x][0] = 'b10'
			for pos in self.bridges[bridge[0]]:
				x, y = pos
				text = self.board[y, x]
				self.board[y, x] = bridge[1] + text[1:]

	def load_level(self, number: int):
		with open('Stages/stage_{}.txt'.format(number)) as file:
			level = []
			for y, line in enumerate(file):
				if line.strip():
					row = [c for c in line.split() if c]
					level.append(row)
					for x, cell in enumerate(row):
						for i in range(0, len(cell), 3):
							# for every 3 characters
							feature = cell[i:i + 3]
							first_char = feature[0]
							if first_char == 'b' or first_char == 'B':
								bridge_id = feature[2]
								if bridge_id in self.bridges:
									self.bridges[bridge_id].append((x, y))
								else:
									self.bridges[bridge_id] = [(x, y)]
							elif first_char == 's' or first_char == 'S':
								if (x, y) in self.switches:
									self.switches[(x, y)].append(feature)
								else:
									self.switches[(x, y)] = [feature]
							elif first_char == 't':
								if feature[2] != 't':
									# { 't[0-9]t': [ t[0-9][0-1] ] }
									trigger_id = 't' + feature[1] + 't'
									if trigger_id in self.teleporter:
										position = int(feature[2])
										self.teleporter[trigger_id][position:position] = [[x, y]]
									else:
										self.teleporter[trigger_id] = [[x, y]]
								else:
									if (x, y) in self.switches:
										self.switches[(x, y)].append(feature)
									else:
										self.switches[(x, y)] = [feature]
							elif feature == 'PPP':
								self.player = np.array([[x, y], [x, y]])

		return np.array(level)

	def restart(self):
		self.load_state(*self.visited[0])
		self.previous = self.player
	# endregion

	# region Graphics
	@staticmethod
	def draw_feature(feature: str, x: int, y: int):
		if feature == Tile.empty:
			return
		first_char = feature[0]
		if feature == 'ooo' or feature == 'PPP':
			Draw.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Draw.colors['white'])
		elif feature == 'iii':
			Draw.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Draw.colors['orange'])
		elif first_char == 's':
			Draw.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Draw.colors['white'])
			Draw.draw_round_switch(position=(x, y), color=Draw.colors['steel'])
		elif first_char == 'S':
			Draw.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Draw.colors['white'])
			Draw.draw_x_switch(position=(x, y), color=Draw.colors['steel'])
		elif first_char == 'B':
			Draw.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Draw.colors['light_pink'])
		elif first_char == 'b':
			Draw.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Draw.colors['gray'])
		elif first_char == 't':
			if feature[2] == 't':
				Draw.draw_teleport_switch(position=(x, y), color=Draw.colors['steel'])
				Draw.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Draw.colors['white'])
			else:
				Draw.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Draw.colors['white'])

	def draw_level(self):
		height, width = self.board.shape

		for x in range(width):
			for y in range(height):
				tile = str(self.board[y][x])
				if len(tile) > 3:
					# if there's more than 3 characters
					for i in range(0, len(tile), 3):
						# for every 3 characters
						feature = tile[i:i + 3]
						self.draw_feature(feature, x, y)
				else:
					self.draw_feature(tile, x, y)

	@staticmethod
	def draw_main_cube(block: Tuple[int, int], direction: int):
		if direction == Direction.standing:
			Draw.draw_cube(position=block, size=(1, 1, 2))
		elif direction == Direction.laying_x:
			Draw.draw_cube(position=block, size=(2, 1, 1))
		elif direction == Direction.laying_y:
			Draw.draw_cube(position=block, size=(1, 2, 1))
		else:
			Draw.draw_cube(position=block, size=(1, 1, 1))

	@staticmethod
	def draw_secondary_cube(block: Tuple[int, int], direction: int):
		if direction == Direction.none:
			Draw.draw_cube(position=block, size=(1, 1, 1), face_color=Draw.colors['light_gray'])

	def rotate_player(self):
		current = self.player
		[x_diff, y_diff] = current[0] - self.previous[0]
		x_center = self.previous[0, 0] + x_diff if x_diff > 0 else self.previous[0, 0]
		y_center = self.previous[0, 1] + y_diff if y_diff > 0 else self.previous[0, 1]
		if self.degree + rotating_speed >= 90:
			self.degree = 90
			if self.check_merge(self.player):
				self.player[[0, 1], :] = self.player[[1, 0], :]
		else:
			self.degree += rotating_speed
		if (current - self.previous).tolist() != [[0, 0], [0, 0]]:
			glTranslate(x_center, -y_center, 0)
			glRotate(self.degree, y_diff, x_diff, 0)
			glTranslate(-x_center, y_center, 0)

		if self.degree == 90:
			return True
		return False

	def rotate_before_swap(self):
		x_center, y_center = self.previous[0]
		x_diff, y_diff = 0, 0
		if self.move_direction == 'up':
			y_diff = -2
		elif self.move_direction == 'down':
			y_center += 2
			y_diff = 2
		elif self.move_direction == 'left':
			x_diff = -2
		elif self.move_direction == 'right':
			x_center += 2
			x_diff = 2
		if self.steps == 1:
			glTranslate(x_center, -y_center, 0)
			glRotate(90, y_diff, x_diff, 0)
			glTranslate(-x_center, y_center, 0)
			return False

		if self.degree + rotating_speed >= 90:
			self.degree = 90
		else:
			self.degree += rotating_speed

		glTranslate(x_center, -y_center, 0)
		glRotate(self.degree, y_diff, x_diff, 0)
		glTranslate(-x_center, y_center, 0)

		if self.degree == 90:
			return True
		return False

	def teleport_player(self, add_height, speed):
		if self.steps == 1:
			height = add_height * self.degree / 90
			glTranslate(0, 0, height)
			if self.degree + speed >= 90:
				self.degree = 90
				self.steps = 0
				return True
			else:
				self.degree += speed
		return False

	def draw_player(self):
		glLineWidth(2)
		glPushMatrix()

		if self.degree == 90:
			if not self.check_goal(self.player, self.board):
				direction = self.get_direction(self.player)
				self.draw_main_cube(self.player[0], direction)
				self.draw_secondary_cube(self.player[1], direction)
		else:
			direction = self.get_direction(self.previous)
			self.draw_secondary_cube(self.player[1], direction)
			if direction != Direction.none and self.get_direction(self.player) == Direction.none:
				done = self.teleport_player(10, rotating_speed / 2)
				if self.rotate_before_swap():
					if not done:
						self.steps = 1
						self.degree = 0
			elif self.check_goal(self.player, self.board):
				done = self.teleport_player(-10, rotating_speed / 5)
				if self.rotate_before_swap():
					if not done:
						self.steps = 1
						self.degree = 0
			else:
				self.rotate_player()
			self.draw_main_cube(self.previous[0], direction)
		glPopMatrix()
		glLineWidth(1)
	# endregion
