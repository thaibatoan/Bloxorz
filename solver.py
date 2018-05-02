# coding=utf-8
from state import State
from utility import Direction


class Solver:
	# Simple Depth First Search to calculate time
	@staticmethod
	def dfs(state: State):
		while state.states:
			player, bridge = state.states.pop()
			state.load_state(player, bridge)

			for direction in ['up', 'down', 'left', 'right']:
				if state.move(direction, False):
					if state.found:
						return

			if state.get_direction(state.player) == Direction.none:
				state.move('swap', False)

	# Simple Breadth First Search to calculate time
	@staticmethod
	def bfs(state: State):
		while state.states:
			player, bridge = state.states.pop(0)
			state.load_state(player, bridge)

			for direction in ['up', 'down', 'left', 'right']:
				if state.move(direction, False):
					if state.found:
						return

			if state.get_direction(state.player) == Direction.none:
				state.move('swap', False)

	# Depth First Search with path to visualize
	@staticmethod
	def dfs_path(state: State):
		move_stack = []
		while state.states:
			player, bridge = state.states.pop()
			move = move_stack.pop() if len(move_stack) > 0 else []
			state.load_state(player, bridge)
			for direction in ['up', 'down', 'left', 'right']:
				if state.move(direction, False):
					if state.found:
						return move + [direction]
					move_stack.append(move + [direction])

			if state.get_direction(state.player) == Direction.none:
				if state.move('swap', False):
					move_stack.append(move + ['swap'])

	# Breadth First Search with path to visualize
	@staticmethod
	def bfs_path(state: State):
		move_queue = []
		while state.states:
			player, bridge = state.states.pop(0)
			move = move_queue.pop(0) if len(move_queue) > 0 else []
			state.load_state(player, bridge)
			for direction in ['up', 'down', 'left', 'right']:
				if state.move(direction, False):
					if state.found:
						return move + [direction]
					move_queue.append(move + [direction])

			if state.get_direction(state.player) == Direction.none:
				if state.move('swap', False):
					move_queue.append(move + ['swap'])
