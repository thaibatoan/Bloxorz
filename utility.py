# coding=utf-8
class Direction:
	standing = 0
	laying_x = 1
	laying_y = 2
	none = 3


class Tile:
	empty = '---'
	floor = 'ooo'
	soft_floor = 'iii'
	switch = 's[0-9][0-1]'
	bridge = 'b[0-3][0-9]'
	goal = 'ggg'
	player = 'ppp'


class Method:
	depth_first_search = 0
	breadth_first_search = 1
	hill_climbing = 2
