# coding=utf-8
import sys
import time

import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from pygame.locals import *
from typing import List, Tuple

degree = 0
b_done = True
rotating_speed = 15


# region Enums
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

	# @formatter:off
	colors = {
		'gray'	:		(0.83, 0.83, 0.83, 1),
		'light_gray':	(0.91, 0.91, 0.91),
		'white'	:		(1, 1, 1, 1	),
		'yellow':		(1, 1, 0.4, 1),
		'green'	:		(0.6, 1, 0.6, 1	),
		'orange':		(1, 0.9, 0.71, 1),
		'light_pink':	(1.0, 0.88, 0.94),
		'white_smoke':	(0.97, 0.97, 1.0),
		'light_blue':   (0.68, 0.85, 0.9)
	}
	# @formatter:on


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
	def draw_cube(
			position: Tuple[int, int],
			size: Tuple[float, float, float],
			face_color=(0.94, 0.66, 0.75),
			border_color=(0.42, 0.56, 0.87)):
		Cube.draw_border(position, size, border_color)
		Cube.draw_faces(position, size, face_color)

	@staticmethod
	def draw_faces(position: Tuple[int, int], size: Tuple[float, float, float], face_color: Tuple[float, float, float]):
		pos_x, pos_y = position
		size_x, size_y, size_z = size
		glColor(face_color)
		for face in Cube.faces:
			glBegin(GL_POLYGON)
			for vertex in face:
				glVertex3f(
						Cube.vertices[vertex, 0] * size_x + pos_x,
						-(Cube.vertices[vertex, 1] * size_y + pos_y),
						Cube.vertices[vertex, 2] * size_z
				)
			glEnd()

	@staticmethod
	def draw_border(position: Tuple[int, int], size: Tuple[float, float, float], border_color: Tuple[float, float, float]):
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

ALGORITHM = Method.hill_climbing

# Nothing:			---
# Heavy/Soft Floor:	ooo|iii
# Player: 			PPP|ppp
# Goal: 			ggg
# Switches:			(Hard|Soft Switch)	(on|toggle|off)			[id] 					- (S|s)	(0|1|2)	[0-9]
# Bridges:			(On|off)			(up|down|left|right)	[id] 					- [B|b]	(0|1|2)	[0-9]
# Teleport:			t					[id]					(trigger|first|second) 	- t		[0-9]	(t|0|1)

LEVELS = np.array([
	# Stage 1
	"""
ooo ooo ooo --- --- --- --- --- --- ---
ooo PPP ooo ooo ooo --- --- --- --- ---
ooo ooo ooo ooo ooo ooo ooo ooo ooo ---
--- ooo ooo ooo ooo ooo ooo ooo ooo ooo
--- --- --- --- --- ooo ooo ggg ooo ooo
--- --- --- --- --- ooo ooo ooo ooo ---
""",
	# Stage 2
	"""
--- --- --- --- --- --- ooo ooo ooo ooo --- --- ooo ooo ooo
ooo ooo ooo ooo --- --- ooo ooo S11 ooo --- --- ooo ggg ooo
ooo ooo s10 ooo --- --- ooo ooo ooo ooo --- --- ooo ooo ooo
ooo PPP ooo ooo b20 b30 ooo ooo ooo ooo b21 b31 ooo ooo ooo
ooo ooo ooo ooo --- --- ooo ooo ooo ooo --- --- --- --- ---
""",
	# Stage 3
	"""
--- --- --- --- --- --- ooo ooo ooo ooo ooo ooo ooo --- ---
ooo ooo ooo ooo --- --- ooo ooo ooo --- --- ooo ooo --- ---
ooo ooo ooo ooo ooo ooo ooo ooo ooo --- --- ooo ooo ooo ooo
ooo PPP ooo ooo --- --- --- --- --- --- --- ooo ooo ggg ooo
ooo ooo ooo ooo --- --- --- --- --- --- --- ooo ooo ooo ooo
--- --- --- --- --- --- --- --- --- --- --- --- ooo ooo ooo
""",
	# Stage 4
	"""
--- --- --- iii iii iii iii iii iii iii --- --- --- ---
--- --- --- iii iii iii iii iii iii iii --- --- --- ---
ooo ooo ooo ooo --- --- --- --- --- ooo ooo ooo --- ---
ooo ooo ooo --- --- --- --- --- --- --- ooo ooo --- ---
ooo ooo ooo --- --- --- --- --- --- --- ooo ooo --- ---
ooo PPP ooo --- --- ooo ooo ooo ooo iii iii iii iii iii
ooo ooo ooo --- --- ooo ooo ooo ooo iii iii iii iii iii
--- --- --- --- --- ooo ggg ooo --- --- iii iii ooo iii
--- --- --- --- --- ooo ooo ooo --- --- iii iii iii iii
""",
	# Stage 5
	"""
--- --- --- --- --- --- --- --- --- --- --- ooo ooo ooo ooo
--- ooo ooo ooo ooo b20 b30 ooo s10 ooo ooo ooo ooo PPP ooo
--- ooo ooo ooo ooo --- --- --- --- --- --- --- ooo ooo ooo
--- ooo ooo s02 ooo --- --- --- --- --- --- --- ooo ooo ooo
--- ooo ooo ooo ooo --- --- --- --- --- --- --- --- --- ---
--- --- --- ooo ooo ooo s22 ooo B21 B31 ooo ooo ooo --- ---
--- --- --- --- --- --- --- --- --- --- ooo ooo ooo ooo s02
ooo ooo ooo --- --- --- --- --- --- --- ooo ooo ooo ooo ooo
ooo ggg ooo ooo b22 b32 ooo ooo ooo ooo ooo ooo ooo --- ---
ooo ooo ooo ooo --- --- --- --- --- --- --- --- --- --- ---
""",
	# Stage 6
	"""
--- --- --- --- --- ooo ooo ooo ooo ooo ooo --- --- --- ---
--- --- --- --- --- ooo --- --- ooo ooo ooo --- --- --- ---
--- --- --- --- --- ooo --- --- ooo ooo ooo ooo ooo --- ---
PPP ooo ooo ooo ooo ooo --- --- --- --- --- ooo ooo ooo ooo
--- --- --- --- ooo ooo ooo --- --- --- --- ooo ooo ggg ooo
--- --- --- --- ooo ooo ooo --- --- --- --- --- ooo ooo ooo
--- --- --- --- --- --- ooo --- --- ooo ooo --- --- --- ---
--- --- --- --- --- --- ooo ooo ooo ooo ooo --- --- --- ---
--- --- --- --- --- --- ooo ooo ooo ooo ooo --- --- --- ---
--- --- --- --- --- --- --- ooo ooo ooo --- --- --- --- ---
""",
	# Stage 7
	"""
--- --- --- --- --- --- --- --- ooo ooo ooo ooo --- --- ---
--- --- --- --- --- --- --- --- ooo ooo ooo ooo --- --- ---
ooo ooo ooo --- --- --- --- --- ooo --- --- ooo ooo ooo ooo
ooo PPP ooo ooo ooo ooo ooo ooo ooo --- --- ooo ooo ggg ooo
ooo ooo ooo --- --- --- --- ooo ooo S10 --- --- ooo ooo ooo
ooo ooo ooo --- --- --- --- ooo ooo ooo --- --- ooo ooo ooo
--- ooo ooo b20 --- --- --- ooo --- --- --- --- --- --- ---
--- --- ooo ooo ooo ooo ooo ooo --- --- --- --- --- --- ---
""",
	# Stage 8
	"""
--- --- --- --- --- --- --- --- --- ooo ooo ooo --- --- ---
--- --- --- --- --- --- --- --- --- ooo t00 ooo --- --- ---
--- --- --- --- --- --- --- --- --- ooo ooo ooo --- --- ---
--- --- --- --- --- --- --- --- --- ooo ooo ooo --- --- ---
ooo ooo ooo ooo ooo ooo --- --- --- ooo ooo ooo ooo ooo ooo
ooo PPP ooo ooo t0t ooo --- --- --- ooo ooo ooo ooo ggg ooo
ooo ooo ooo ooo ooo ooo --- --- --- ooo ooo ooo ooo ooo ooo
--- --- --- --- --- --- --- --- --- ooo ooo ooo --- --- ---
--- --- --- --- --- --- --- --- --- ooo ooo ooo --- --- ---
--- --- --- --- --- --- --- --- --- ooo t01 ooo --- --- ---
--- --- --- --- --- --- --- --- --- ooo ooo ooo --- --- ---
""",
	# Stage 9
	"""
ooo ooo ooo ooo --- --- --- ooo --- --- --- ooo ooo ooo ooo
ooo PPP t01 ooo --- --- --- ooo --- --- --- ooo t00 t0t ooo
ooo ooo ooo ooo ooo ooo ooo ooo ooo ooo ooo ooo ooo ooo ooo
--- --- --- --- --- --- ooo ggg ooo --- --- --- --- --- ---
--- --- --- --- --- --- ooo ooo ooo --- --- --- --- --- ---
""",
	# Stage 10
	"""
ooo ooo ooo --- --- --- --- --- ooo ooo    ooo ooo ooo    ooo
ooo ggg ooo b20 b30 ooo b21 b31 ooo PPPt01 ooo ooo t0tt00 ooo
ooo ooo ooo --- --- --- --- --- ooo ooo    ooo ooo b11    ---
--- --- --- --- --- --- --- --- --- ooo    ooo ooo b11    ---
--- --- --- --- --- --- --- --- --- ---    --- ooo ooo    ---
--- --- --- --- --- --- --- --- --- ---    --- --- ooo    ---
--- --- --- --- --- --- --- --- --- ---    --- --- ooo    ---
--- --- --- --- --- --- --- --- --- ---    --- ooo ooo    ---
--- --- --- --- ooo ooo ooo ooo ooo ---    --- ooo ooo    ---
--- --- --- --- ooo s10 --- --- ooo ooo    ooo S11 ooo    ---
""",
	# Stage 11
	"""
--- ooo ooo ooo B10 --- --- --- --- --- --- ---
--- ooo ggg ooo B10 --- --- --- --- --- --- ---
--- ooo ooo ooo --- --- --- --- --- --- --- ---
--- ooo --- --- --- ooo ooo ooo ooo ooo ooo ---
--- ooo --- --- --- ooo ooo --- --- ooo ooo ---
PPP ooo ooo ooo ooo ooo ooo --- --- ooo ooo ooo
--- --- --- --- --- ooo s20 --- --- --- --- ooo
--- --- --- --- --- ooo ooo ooo ooo --- --- ooo
--- --- --- --- --- ooo ooo ooo ooo ooo ooo ooo
--- --- --- --- --- --- --- --- ooo ooo ooo ---
""",
	# Stage 12
	"""
--- --- --- --- --- --- --- --- --- --- --- --- S11
--- --- --- --- --- ooo ooo ooo --- --- ooo ooo ooo
--- --- --- --- --- ooo S10 ooo ooo ooo ooo ooo b20
--- --- --- ooo ooo ooo ooo ooo --- --- ooo ooo ---
--- --- --- ooo ggg ooo b21 --- --- --- ooo ooo ---
--- ooo ooo ooo ooo ooo --- --- --- ooo ooo ooo ooo
ooo ooo PPP ooo --- --- --- --- --- ooo ooo ooo ooo
ooo ooo ooo ooo --- --- ooo ooo ooo ooo ooo --- ---
--- --- --- --- --- ooo ooo ooo --- --- --- --- ---
--- --- --- --- --- ooo ooo ooo --- --- --- --- ---
""",
	# Stage 13
	"""
ooo ooo ooo iii ooo ooo ooo ooo iii ooo ooo ooo ooo ---
ooo ooo --- --- --- --- --- --- --- --- ooo ooo ooo ---
ooo ooo --- --- --- --- --- --- --- --- --- ooo ooo ooo
ooo ooo ooo --- --- --- ooo ooo ooo --- --- ooo PPP ooo
ooo ooo ooo iii iii iii ooo ggg ooo --- --- ooo ooo ooo
ooo ooo ooo --- --- iii ooo ooo ooo --- --- ooo --- ---
--- --- ooo --- --- iii iii iii iii iii ooo ooo --- ---
--- --- ooo ooo ooo iii iii ooo iii iii iii --- --- ---
--- --- --- ooo ooo iii iii iii iii iii iii --- --- ---
--- --- --- ooo ooo ooo --- --- ooo ooo --- --- --- ---
""",
	# Stage 14
	"""
--- --- --- --- --- --- --- --- ooo ooo ooo --- --- ---
--- --- --- ooo ooo ooo --- --- ooo ooo ooo --- --- ---
ooo b20 b30 ooo PPP ooo ooo ooo ooo ooo ooo ooo ooo ooo
ooo b21 b31 ooo ooo ooo --- --- --- --- --- --- S10 ooo
ooo --- --- --- --- --- --- --- --- --- --- --- ooo ooo
ooo --- --- --- --- --- --- --- --- --- --- --- ooo ooo
ooo --- --- --- --- --- --- --- ooo ooo ooo ooo ooo ooo
ooo ooo ooo ooo ooo --- --- --- ooo ooo ooo --- --- ---
--- ooo ooo ggg ooo --- --- --- ooo ooo ooo --- --- ---
--- --- ooo ooo ooo --- --- --- ooo ooo ooo ooo ooo S11
""",
	# Stage 15
	"""
--- ---    --- --- --- --- --- ooo ooo    ooo --- --- ooo    ooo ooo
--- ---    --- --- ooo B21 B31 ooo ooo    ooo b20 b30 S11S12 t00 ooo
ooo ooo    b22 b32 ooo --- --- ooo ooo    ooo --- --- ooo    ooo ooo
ooo ooo    ooo ooo ooo --- --- --- s10s11 --- --- --- ---    --- ---
ooo ooo    --- --- --- --- --- --- ---    --- --- --- ---    --- ---
--- ooo    --- --- --- --- --- t0t ---    --- --- --- ---    --- ---
--- ooo    --- --- --- --- --- ooo ---    --- --- --- ---    --- ---
ooo ooo    ooo --- --- --- ooo ooo ooo    --- --- s23 ooo    ooo ---
ooo PPPt01 ooo ooo ooo ooo ooo ooo ooo    B23 B33 ooo ggg    ooo ---
ooo ooo    ooo --- --- --- ooo ooo ooo    --- --- s23 ooo    ooo ---
""",
	# Stage 16
	"""
---          t1tt00t41 ---       --- --- ---    --- --- --- --- ooo ooo ooo
t4tt01t20t31 ooo       t2tt21t40 b20 b30 S00t11 S01 t10 b21 b31 ooo ggg ooo
---          t3tt30    ---       --- --- ---    --- --- --- --- ooo ooo ooo
---          ---       ---       --- --- ---    --- --- --- --- --- --- ---
---          ---       ---       --- --- ---    --- --- --- --- --- --- ---
---          ---       ooo       ooo ooo ---    --- --- ooo ooo ooo --- ---
---          ---       ooo       PPP ooo ooo    ooo ooo ooo t0t ooo --- ---
---          ---       ooo       ooo ooo ---    --- --- ooo ooo ooo --- ---
""",
	# Stage 17
	"""
ooo ooo ooo --- --- --- --- --- --- --- --- --- ---    --- ---
ooo PPP ooo ooo ooo ooo ooo ooo ooo b22 --- --- ooo    ooo ooo
ooo ooo ooo --- --- --- --- b31 ooo ooo ooo ooo ooo    ggg ooo
ooo ooo ooo --- --- --- --- --- --- --- --- --- S24    S04 ooo
ooo ooo ooo --- --- --- --- --- --- --- --- --- ---    --- ---
ooo ooo ooo --- --- --- --- --- --- --- --- --- ---    --- ---
ooo ooo ooo --- --- --- b34 ooo ooo ooo ooo ooo S01    --- ---
ooo ooo ooo ooo ooo ooo ooo ooo b20 --- --- ooo ooo    --- ---
ooo s10 ooo --- --- --- --- --- --- --- --- ooo ooo    --- ---
ooo ooo ooo --- --- --- --- --- --- --- --- ooo S20S02 --- ---
""",
	# Stage 18
	"""
--- --- --- --- --- --- --- s00 --- --- --- --- --- --- ---
ooo ooo s21 ooo --- --- --- ooo --- --- --- --- --- --- ---
ooo ooo ooo ooo ooo --- --- ooo --- --- --- --- --- --- ---
ooo s20 PPP ooo ooo ooo ooo ooo b20 b30 ooo ooo b21 b31 ooo
ooo ooo ooo ooo ooo b22 --- --- ooo --- --- --- ooo --- ---
ooo ooo s21 ooo --- --- --- --- ooo --- --- --- ooo --- ---
ooo --- --- --- --- --- --- --- s01 --- --- ooo ooo ooo ---
ooo --- --- --- --- --- --- --- --- --- ooo ooo ggg ooo ---
ooo b21 b31 S12 --- --- --- --- --- --- ooo ooo ooo ooo ---
""",
	# Stage 19
	"""
--- PPP ooo ooo ooo ooo ooo ooo ooo ooo s10 ooo ooo ooo ooo
--- --- --- --- --- ooo ooo --- --- --- --- --- --- ooo ooo
--- --- --- --- --- ooo ooo --- --- --- --- --- --- ooo ooo
--- --- --- --- --- --- --- --- --- --- --- --- --- ooo ooo
--- --- --- --- --- --- --- --- --- --- --- --- --- ooo ooo
ooo ooo ooo --- --- ooo ooo b20 b30 ooo s21 ooo ooo ooo ooo
ooo ggg ooo --- --- ooo ooo --- --- --- --- --- --- --- ---
ooo ooo ooo --- --- ooo ooo --- --- --- --- --- --- --- ---
--- ooo ooo --- --- ooo ooo --- --- --- --- --- --- --- ---
--- ooo B21 B31 ooo ooo ooo ooo ooo ooo s01 ooo ooo ooo ---
""",
	# Stage 20
	"""
--- --- --- --- --- --- --- --- --- --- --- --- ooo ooo ooo
--- --- ooo ooo ooo B20 B30 ooo ooo ooo b21 b31 ooo t00 ooo
--- --- ooo ooo ooo --- --- s20 PPP ooo --- --- ooo ooo ooo
--- --- ooo ooo ooo --- --- ooo ooo ooo --- --- --- --- ---
--- --- ooo s20 ooo --- --- t0t ooo s20 --- --- --- --- ---
--- --- ooo ooo ooo --- --- ooo ooo ooo --- --- --- --- ---
ooo ooo ooo ooo --- --- --- ooo ooo ooo b22 b32 s12 ooo ooo
ooo s11 --- --- --- --- --- --- --- --- --- --- ooo t01 ooo
--- --- --- --- --- --- --- --- --- --- --- --- ooo ggg ooo
--- --- --- --- --- --- --- --- --- --- --- --- ooo ooo ooo
""",
	# Stage 21
	"""
--- --- --- --- --- --- --- --- ooo ooo --- --- --- --- ---
--- --- --- --- --- --- --- ooo ooo ooo --- --- --- --- ---
ooo ooo --- --- ooo ooo ooo ooo ooo ooo --- --- --- --- ---
ooo PPP ooo ooo ooo ooo --- --- ooo --- --- --- --- --- ---
ooo ooo ooo ooo --- --- --- --- ooo --- --- --- ooo ooo ooo
--- ooo ooo --- --- --- --- --- S10 ooo ooo ooo ooo ggg ooo
--- --- ooo --- --- --- --- --- S11 ooo --- --- ooo ooo ooo
--- --- ooo ooo ooo b21 --- --- ooo ooo --- --- --- --- ---
--- --- --- ooo ooo ooo --- --- ooo ooo --- --- --- --- ---
--- --- --- b30 ooo ooo ooo ooo ooo ooo --- --- --- --- ---
""",
	# Stage 22
	"""
--- --- --- --- ---    ooo ooo    --- --- --- --- ooo ooo ooo
--- --- --- ooo ooo    ooo ooo    ooo ooo --- --- ooo ggg ooo
ooo ooo ooo ooo ooo    ooo s20s21 ooo ooo ooo ooo ooo ooo ooo
ooo PPP ooo ooo s20s21 --- ---    ooo ooo ooo ooo ooo b22 ---
ooo ooo ooo --- ---    --- ---    --- --- ooo ooo ooo --- ---
--- ooo --- --- ---    --- ---    --- --- --- ooo --- --- ---
--- ooo --- --- ---    --- ---    --- --- --- ooo --- --- ---
--- ooo b21 --- ---    --- ---    --- --- B30 ooo --- --- ---
--- ooo ooo --- ---    --- ---    --- --- ooo ooo --- --- ---
--- --- S12 --- ---    --- ---    --- --- S11 --- --- --- ---
""",
	# Stage 23
	"""
---    ooo ooo ooo --- --- --- --- --- --- --- --- ooo    ooo    ooo
---    ooo S04 ooo --- --- --- --- --- --- --- --- ooo    s00s11 ooo
---    ooo t01 ooo --- --- --- ooo ooo ooo B22 B32 ooo    ooo    ooo
b33    ooo ooo ooo b24 --- --- ooo ggg ooo --- --- ooo    ooo    s22
ooo    --- --- --- ooo --- --- ooo ooo ooo --- --- ---    ---    ooo
s20s03 --- --- --- ooo --- --- iii iii iii --- --- ---    ---    ooo
ooo    b20 b30 ooo ooo ooo iii iii iii iii iii ooo ooo    ooo    B22
---    --- --- ooo PPP ooo iii iii iii iii iii ooo t0tt00 ooo    ---
---    --- --- ooo ooo ooo iii iii iii iii iii ooo ooo    ooo    ---
---    --- --- ooo ooo ooo ooo ooo b21 --- --- --- ---    ---    ---
""",
	# Stage 24
	"""
--- --- --- --- --- --- --- --- --- --- ooo ooo ooo ooo
--- --- --- b30 ooo ooo ooo ooo ooo ooo ooo S01 ooo t0t
--- PPP b21 b31 ooo S02 ooo --- --- --- ooo ooo ooo ooo
S00 ooo --- --- ooo ooo --- --- --- --- --- --- ooo ---
ooo ooo --- --- ooo --- --- --- --- --- --- --- ooo ---
ooo ooo ooo ooo ooo --- --- --- --- --- ooo ooo ooo ---
ooo ooo ooo --- --- t00 ooo t01 b23 b33 ooo ggg ooo ---
--- --- --- --- --- S03 ooo b22 --- --- ooo ooo ooo ---
""",
	# Stage 25
	"""
--- --- ooo ooo ---    --- --- --- ---    --- --- --- --- ---
--- --- ooo ooo ooo    --- --- --- ---    --- --- --- --- ---
--- --- ooo ooo s10s13 --- --- --- ---    --- ooo ooo ooo b13
--- --- --- ooo ooo    ooo ooo b22 ---    --- ooo ggg ooo b13
--- --- --- --- ---    --- ooo ooo b20    b30 ooo ooo ooo ---
--- ooo ooo --- ---    --- ooo ooo ---    --- --- --- --- ---
ooo ooo S00 ooo B21    B31 ooo ooo ---    --- --- --- --- ---
ooo PPP ooo B14 ---    --- ooo ooo ---    --- --- ooo ooo ooo
ooo ooo ooo B14 ---    --- ooo ooo s21s02 ooo ooo ooo ooo ooo
--- --- --- --- ---    --- --- --- ---    --- --- ooo ooo ooo
""",
	# Stage 26
	"""
--- --- --- --- --- ooo ooo ooo ooo --- ---    --- --- t0t
--- --- --- --- --- ooo ooo s20 ooo ooo ooo    --- --- ooo
--- --- --- --- ooo ooo ooo ooo ooo ooo ooo    --- --- ooo
ooo ooo B20 B30 ooo ooo ooo ooo --- --- ooo    ooo t00 ooo
ooo ooo ooo b21 --- --- ooo --- --- --- ooo    ooo --- ---
ooo ooo ooo --- --- --- ooo --- --- --- PPPt01 --- --- ---
--- ooo --- --- --- --- ooo ooo ooo --- ---    --- --- ---
--- S01 --- --- --- --- ooo ggg ooo b21 ---    --- --- ---
--- --- --- --- --- --- ooo ooo ooo --- ---    --- --- ---
""",
	# Stage 27
	"""
ooo ooo ooo --- --- --- --- ooo ooo ooo ooo ooo ooo ooo    ooo
ooo PPP ooo ooo ooo ooo ooo ooo ooo ooo ooo --- --- ooo    ooo
ooo ooo ooo --- --- --- --- ooo ooo --- --- --- --- ooo    ooo
--- --- --- --- --- --- --- --- --- --- --- --- ooo S20S21 ooo
--- --- --- --- --- --- --- --- --- --- --- --- ooo ooo    ---
ooo ooo ooo --- --- iii iii iii iii ooo --- --- s20 s21    ---
ooo ggg ooo iii iii iii iii iii iii iii --- --- ooo ooo    ooo
ooo ooo ooo iii iii iii iii iii iii iii iii iii ooo ooo    ooo
--- --- --- --- --- iii iii iii iii iii iii iii ooo ooo    ooo
--- --- --- --- --- --- B30 ooo ooo B21 --- --- --- ---    ---
""",
	# Stage 28
	"""
--- ooo ooo B20 B30 ooo ooo --- --- --- --- --- --- --- ---
--- ooo ooo --- --- ooo ooo ooo --- --- --- --- --- --- ---
iii iii PPP --- --- ooo ooo ooo ooo --- --- --- --- --- ---
iii iii --- --- --- --- --- ooo ooo ooo --- --- --- --- ---
iii iii --- --- --- --- --- --- ooo ooo ooo --- --- --- ---
iii ooo ooo ooo --- --- --- --- --- ooo ooo t0t --- --- ---
--- ooo ggg ooo --- --- --- --- --- --- ooo ooo ooo ooo t00
--- ooo ooo ooo ooo ooo ooo --- --- --- ooo s20 ooo ooo ooo
--- --- ooo --- --- ooo ooo --- --- --- ooo ooo ooo --- ---
--- --- ooo --- --- ooo ooo ooo B20 B30 ooo ooo t01 --- ---
""",
	# Stage 29
	"""
---    --- s21s04 B20 B30 ooo --- --- --- ooo b24 b34 S06          --- ---
---    --- ---    --- --- ooo --- --- --- ooo --- --- ---          --- ---
---    --- ---    --- --- ooo ooo ooo ooo ooo --- --- ---          --- ---
S22S08 b23 b33    ooo ooo ooo ooo PPP ooo ooo ooo ooo b25          b35 S07
---    --- ---    --- --- ooo ooo ooo ooo ooo --- --- ---          --- ---
---    --- ---    --- --- b16 ooo --- --- ooo --- --- ---          --- ---
---    --- ---    --- --- b16 ooo --- --- ooo B21 B31 s03          --- ---
ooo    ooo ooo    --- --- ooo ooo --- --- ooo --- --- ---          --- ---
ooo    ggg ooo    b28 b38 ooo --- --- --- ooo --- --- ---          --- ---
ooo    ooo ooo    b27 --- ooo --- --- --- ooo B22 B32 s20s21s24s05 --- ---
""",
	# Stage 30
	"""
--- --- --- ooo ooo ooo ooo ooo iii iii ooo ooo ooo ooo ---
--- --- --- ooo ggg ooo ooo --- --- --- --- --- iii ooo ---
--- --- --- ooo ooo ooo --- --- --- --- --- --- iii ooo S20S02
--- --- --- --- --- --- --- iii ooo ooo B20 B30 ooo ooo ooo
--- --- PPP --- --- --- --- iii iii --- --- --- --- --- ooo
--- S00 ooo iii --- --- --- iii iii --- --- --- --- --- ooo
iii iii iii iii --- --- --- ooo ooo b22 --- --- b32 ooo ooo
iii iii iii ooo iii ooo iii iii ooo iii --- --- S11 ooo b21
ooo iii iii iii iii iii iii iii iii iii iii iii ooo --- ---
--- iii ooo iii iii iii --- --- iii iii iii iii ooo --- ---
""",
	# Stage 31
	"""
--- --- ---    --- --- --- ---          ---          --- --- --- ooo ooo ooo b25
--- ooo ooo    ooo --- --- ---          ---          S10 --- --- ooo ggg ooo b25
--- ooo ooo    ooo B23 B33 ooo          ooo          ooo b20 b30 ooo ooo ooo b25
--- ooo ooo    ooo --- --- ooo          ooo          ooo --- --- --- ooo --- ---
--- iii iii    iii --- --- s20s21s22s23 ooo          ooo --- --- --- iii --- ---
--- --- iii    --- --- --- ooo          ooo          ooo --- --- iii iii iii ---
--- --- ooo    --- --- --- ooo          ooo          ooo --- --- ooo ooo ooo ---
B04 ooo ooo    ooo b22 b32 ooo          s20s21s22s23 ooo B21 B31 ooo PPP ooo ---
B04 ooo S23S05 ooo --- --- S12          ---          --- --- --- ooo ooo ooo ---
B04 ooo ooo    ooo --- --- ---          ---          --- --- --- --- --- --- ---
""",
	# Stage 32
	"""
--- --- --- --- --- --- --- --- --- --- --- --- ooo S10S12
--- --- ooo ooo B20 B30 ooo ooo --- --- --- ooo ooo ooo
--- ooo ooo ooo b21 b31 ooo ooo --- --- ooo S13 ooo ooo
--- ooo ggg ooo --- --- --- ooo ooo ooo ooo ooo --- ---
--- ooo ooo ooo --- --- --- --- ooo ooo ooo --- --- ---
--- --- --- --- --- --- --- --- --- ooo ooo --- --- ---
--- --- --- --- ooo ooo ooo --- --- ooo PPP	 --- --- ---
ooo ooo b22 b32 ooo S11 ooo --- --- ooo ooo --- --- ---
ooo ooo b23 b33 ooo ooo ooo ooo ooo ooo ooo --- --- ---
""",
	# Stage 33
	"""
--- --- --- --- --- ooo ooo s20 ooo ooo ooo --- --- --- ---
--- --- --- --- --- ooo ooo ooo ooo ooo ooo b21 --- --- ---
ooo ooo ooo --- --- s20 ooo ooo s20 ooo ooo ooo ooo ooo ---
ooo PPP ooo B22 B32 ooo ooo ooo ooo s20 s20 ooo ooo s20 ---
--- --- --- --- --- ooo ooo s20 ooo ooo s20 ooo ooo ooo ---
--- --- --- --- --- ooo ooo ooo ooo ooo ooo s20 ooo ooo ---
ooo ooo ooo --- --- ooo ooo ooo ooo ooo ooo s20 ooo ooo ooo
ooo ggg ooo B20 B30 ooo s20 ooo --- --- ooo ooo ooo s20 S01
ooo ooo ooo --- --- ooo ooo ooo --- --- --- ooo ooo ooo ooo
ooo ooo ooo --- --- --- --- --- --- --- --- --- ooo ooo ooo
"""

])


# endregion


# Mainly to setup OpenGL
class Display:
	def __init__(self, title='', fps=60, fullscreen=False, size=(800, 600), offset=(0, 0)):
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
		# glViewport(0, 0, 600, 800)
		# glMatrixMode(GL_PROJECTION)
		# glLoadIdentity()
		# glOrtho(0, WIDTH, -HEIGHT, HEIGHT, -5, 5)
		# glMatrixMode(GL_MODELVIEW)
		gluPerspective(60, (size[0] / size[1]), 0.1, 1000.0)
		gluLookAt(0.0, 0.0, 3.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
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
class Player:
	def __init__(self, x, y, rot):
		self.x = x
		self.y = y
		self.rot = rot


class State:

	def __init__(self, stage=1):
		self.start = (0, 0, Direction.standing)
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
		self.eval_map = None

	def load_level(self, number: int):
		level = []
		lines = LEVELS[number - 1].splitlines()
		lines = [line for line in lines if line.strip()]
		self.bridges = {}
		for y, line in enumerate(lines):
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
							self.start = (x, y, Direction.standing)
		print('Bridges:', self.bridges)
		print('Switches:', self.switches)
		print('Player:', *self.player)
		print('Player:', self.get_bridges_status(np.array(level)))
		print('Teleporter:', self.teleporter)
		return np.array(level)

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

	def restart(self):
		self.load_state(*self.states[0])

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
				global degree
				degree = 90

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
				return True
			else:
				return self.add_state(player, board)

		return False

	# endregion

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
						self.previous = player
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

	def is_goal(self, x, y):
		return self.board[y, x] == Tile.goal

	@staticmethod
	def check_goal(player: np.ndarray, board: np.ndarray):
		return np.array_equal(player[0], player[1]) and board[player[0, 1], player[0, 0]] == Tile.goal

	# endregion

	# region Graphics
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
			Cube.draw_cube(position=block, size=(1, 1, 2))
		elif direction == Direction.laying_x:
			Cube.draw_cube(position=block, size=(2, 1, 1))
		elif direction == Direction.laying_y:
			Cube.draw_cube(position=block, size=(1, 2, 1))
		else:
			Cube.draw_cube(position=block, size=(1, 1, 1))

	@staticmethod
	def draw_secondary_cube(block: Tuple[int, int], direction: int):
		if direction == Direction.none:
			Cube.draw_cube(position=block, size=(1, 1, 1), face_color=Tile.colors['light_gray'])

	def rotate_player(self):
		global degree
		current = self.player
		[x_diff, y_diff] = current[0] - self.previous[0]
		x_center = self.previous[0, 0] + x_diff if x_diff > 0 else self.previous[0, 0]
		y_center = self.previous[0, 1] + y_diff if y_diff > 0 else self.previous[0, 1]
		if degree + rotating_speed >= 90:
			degree = 90
			if self.check_merge(self.player):
				self.player[[0, 1], :] = self.player[[1, 0], :]
		else:
			degree += rotating_speed
		if (current - self.previous).tolist() != [[0, 0], [0, 0]]:
			glTranslate(x_center, -y_center, 0)
			glRotate(degree, y_diff, x_diff, 0)
			glTranslate(-x_center, y_center, 0)

	def draw_player(self):
		global degree
		glLineWidth(2)
		glPushMatrix()

		if degree == 90:
			direction = self.get_direction(self.player)
			self.draw_main_cube(self.player[0], direction)
		else:
			direction = self.get_direction(self.previous)
			self.rotate_player()
			self.draw_main_cube(self.previous[0], direction)
		glPopMatrix()
		self.draw_secondary_cube(self.player[1], direction)
		glLineWidth(1)

	@staticmethod
	def draw_feature(feature: str, x: int, y: int):
		if feature == Tile.empty:
			return
		first_char = feature[0]
		if feature == 'ooo' or feature == 'PPP':
			Cube.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Tile.colors['white'])
		elif feature == 'iii':
			Cube.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Tile.colors['orange'])
		elif first_char == 's':
			Cube.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Tile.colors['green'])
		elif first_char == 'S':
			Cube.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Tile.colors['yellow'])
		elif first_char == 'B':
			Cube.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Tile.colors['light_pink'])
		elif first_char == 'b':
			Cube.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Tile.colors['gray'])
		elif first_char == 't':
			if feature[2] == 't':
				Cube.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Tile.colors['light_blue'])
			else:
				Cube.draw_cube(position=(x, y), size=(1, 1, -0.2), face_color=Tile.colors['white'])

	# endregion

	# def h_map(self):
	# 	([y], [x]) = np.where(self.board == Tile.goal)
	# 	state = State()
	# 	q = [0]
	# 	height, width = state.board.shape
	# 	result = np.full((3, height, width), 1000)
	# 	result[0, y, x] = 0
	#
	# 	while state.states:
	# 		current_state = state.states.pop(0)
	# 		count = q.pop(0)
	# 		for move in state.all_moves:
	# 			state.set_player_position(current_state)
	# 			if move():
	# 				result[state.current.rot, state.current.y, state.current.x] = count + 1
	# 				q.append(count + 1)
	#
	# 	return result
	#
	# def evaluate(self):
	# 	return self.eval_map[self.current.rot, self.current.y, self.current.x]


# endregion


# region Algorithm
class Solver:
	# Simple Depth First Search to calculate time
	@staticmethod
	def dfs(state: State):
		while state.states:
			player, bridge = state.states.pop()
			state.load_state(player, bridge)

			for direction in ['up', 'down', 'left', 'right']:
				if state.move(direction, False):
					state.check_goal(state.player, state.board)

			if state.get_direction(state.player) == Direction.none:
				state.move('swap', False)
				return

	# Simple Breadth First Search to calculate time
	@staticmethod
	def bfs(state: State):
		while state.states:
			player, bridge = state.states.pop(0)
			state.load_state(player, bridge)

			for direction in ['up', 'down', 'left', 'right']:
				if state.move(direction, False):
					state.check_goal(state.player, state.board)

			if state.get_direction(state.player) == Direction.none:
				state.move('swap', False)
				return

	# Depth First Search with path to visualize
	@staticmethod
	def dfs_path(state: State):
		path_stack = [[state.visited[-1]], ]
		while state.states:
			player, bridge = state.states.pop()
			path = path_stack.pop()
			state.load_state(player, bridge)

			for direction in ['up', 'down', 'left', 'right']:
				if state.move(direction, False):
					if state.check_goal(state.player, state.board):
						return path
					path_stack.append(path + [state.visited[-1]])

			if state.get_direction(state.player) == Direction.none:
				state.move('swap', False)

	# Breadth First Search with path to visualize
	@staticmethod
	def bfs_path(state: State):
		path_queue = [[state.visited[-1]], ]
		while state.states:
			player, bridge = state.states.pop(0)
			path = path_queue.pop(0)
			state.load_state(player, bridge)

			for direction in ['up', 'down', 'left', 'right']:
				if state.move(direction, False):
					if state.check_goal(state.player, state.board):
						return path
					path_queue.append(path + [state.visited[-1]])

			if state.get_direction(state.player) == Direction.none:
				state.move('swap', False)

	# Hill Climbing
	# @staticmethod
	# def hill_climbing(state: State):
	# 	state.eval_map = state.h_map()
	# 	path = []
	#
	# 	while True:
	# 		next_eval = 1000
	# 		next_state = None
	# 		current_state = state.get_player_position()
	# 		path.append(current_state)
	# 		for move in state.all_moves:
	# 			if move():
	# 				x = state.evaluate()
	# 				if x < next_eval:
	# 					next_eval = x
	# 					next_state = state.get_player_position()
	# 			state.set_player_position(current_state)
	#
	# 		if next_eval >= state.evaluate():
	# 			return path
	# 		state.set_player_position(next_state)


# endregion

def handle_move_event(move, action, state):
	prev = state.prev
	current = state.get_player_position()
	if move(True):
		action.append(move)
	state.prev = prev
	state.set_player_position(current)


def main(playable=True, visualize=True, method=Method.hill_climbing, stage=1):
	global degree
	state = State(stage=stage)

	if not playable:
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
			state.prev = path[0]
			state.load_state(*path[0])
			state.previous = state.player
		else:
			if method is Method.hill_climbing:
				# Solver.hill_climbing(state)
				return
			elif method is Method.breadth_first_search:
				Solver.bfs(state)
			elif method is Method.depth_first_search:
				Solver.dfs(state)
			return
	pygame.init()
	display = Display('Bloxorz', offset=(state.board.shape[1], state.board.shape[0]))

	steps = 0
	action_queue = []
	while True:
		if playable and len(action_queue) != 0 and degree == 90:
			degree = 0
			next_action = action_queue[-1]
			state.move(next_action)
			action_queue = []

		for event in pygame.event.get():
			if display.is_trying_to_quit(event):
				pygame.quit()
				return

			if event.type == pygame.KEYDOWN:
				if playable:
					if event.key == pygame.K_UP:
						action_queue.append('up')
					elif event.key == pygame.K_DOWN:
						action_queue.append('down')
					elif event.key == pygame.K_LEFT:
						action_queue.append('left')
					elif event.key == pygame.K_RIGHT:
						action_queue.append('right')
					elif event.key == pygame.K_SPACE:
						action_queue.append('swap')
					elif event.key == pygame.K_r and pygame.key.get_mods() and pygame.KMOD_CTRL:
						state.restart()
				else:
					if event.key == pygame.K_RIGHT or event.key == pygame.K_DOWN:
						steps += 1
						degree = 0
						if steps >= len(path):
							steps -= len(path)
						if steps > 0:
							state.previous = state.player
							state.load_state(*path[steps])
						else:
							state.load_state(*path[steps])
							state.previous = state.player
					elif event.key == pygame.K_LEFT or event.key == pygame.K_UP:
						steps -= 1
						degree = 0
						if steps < 0:
							steps += len(path)
						if steps < len(path) - 1:
							state.previous = state.player
							state.load_state(*path[steps])
						else:
							state.load_state(*path[steps])
							state.previous = state.player
					elif event.key == pygame.K_r and pygame.key.get_mods() and pygame.KMOD_CTRL:
						steps = 0
						degree = 0
						state.load_state(*path[steps])
						state.previous = state.player

		state.draw_level()
		state.draw_player()
		display.update()


main(
		stage=33,
		playable=False,
		visualize=True,
		method=Method.breadth_first_search
)
