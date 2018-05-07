# coding=utf-8
import time

import pygame

from state import State
from utility import Method


def time_function(func, stage, *args):
	import os
	import psutil
	process = psutil.Process(os.getpid())
	before = process.memory_info().rss / 1024 / 1024
	start = time.clock()
	func(*args)
	end = time.clock()
	total = (end - start) * 1000
	after = process.memory_info().rss / 1024 / 1024
	print('Memory (Before): {0:.3f}MB'.format(before))
	print('Memory (After): {0:.3f}MB'.format(after))
	print('Time to complete: {0:.3f} ms'.format(total))

	with open('result2.txt') as file:
		lines = file.readlines()

	with open('result2.txt', 'w') as file:
		string = '{0:.3f}\t{1:.3f}\t{2:.3f}\n'.format(before, after, total)
		if len(lines) == 0:
			lines = [string]
		elif int(stage) - 1 >= len(lines):
			lines += [string]
		else:
			result = lines[-1].split('\t')
			if float(result[2]) > total:
				lines = lines[:-1] + [string]
		file.writelines(lines)


def main(playable=True, visualize=True, method=Method.hill_climbing, stage=1):
	state = State(stage=stage)

	if not playable:
		from solver import Solver
		if visualize:
			if method is Method.hill_climbing:
				# path = Solver.hill_climbing(state)
				return
			elif method is Method.breadth_first_search:
				path = Solver.bfs_path(state)
			elif method is Method.depth_first_search:
				path = Solver.dfs_path(state)
			else:
				return
			# reset position
			state.restart()
		else:
			if method is Method.hill_climbing:
				# Solver.hill_climbing(state)
				return
			elif method is Method.breadth_first_search:
				time_function(Solver.bfs, stage, state)
			elif method is Method.depth_first_search:
				time_function(Solver.dfs, stage, state)
			return

	from display import Display
	pygame.init()
	display = Display('Bloxorz', offset=(state.board.shape[1], state.board.shape[0]))

	steps = 0
	next_action = ''
	while True:
		if next_action != '' and state.degree == 90:
			state.degree = 0
			state.move(next_action)
			next_action = ''
			if not playable:
				steps += 1

		for event in pygame.event.get():
			if display.is_trying_to_quit(event):
				pygame.quit()
				return

			if event.type == pygame.KEYDOWN:
				if playable:
					if event.key == pygame.K_UP:
						next_action = 'up'
					elif event.key == pygame.K_DOWN:
						next_action = 'down'
					elif event.key == pygame.K_LEFT:
						next_action = 'left'
					elif event.key == pygame.K_RIGHT:
						next_action = 'right'
					elif event.key == pygame.K_SPACE:
						next_action = 'swap'
					elif event.key == pygame.K_r and pygame.key.get_mods() and pygame.KMOD_CTRL:
						state.restart()
						next_action = ''
					if state.check_goal(state.player, state.board):
						next_action = ''
				else:
					if event.key == pygame.K_RIGHT or event.key == pygame.K_DOWN:
						if next_action == '':
							if steps >= len(path):
								steps = 0
								state.restart()
								next_action = ''
							else:
								next_action = path[steps]
					elif event.key == pygame.K_r and pygame.key.get_mods() and pygame.KMOD_CTRL:
						steps = 0
						state.restart()
						next_action = ''

		state.draw_level()
		state.draw_player()
		display.update()


main(
		stage=4,
		playable=True,
		visualize=False,
		method=Method.breadth_first_search
)
