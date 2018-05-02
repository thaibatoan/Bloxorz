# coding=utf-8
from math import cos, pi, sin
from typing import Tuple

import numpy as np
from OpenGL.GL import glBegin, glColor, glEnd, glTranslate
from OpenGL.raw.GL.VERSION.GL_1_0 import glLineWidth, glPopMatrix, glPushMatrix, glVertex3f
from OpenGL.raw.GL.VERSION.GL_1_1 import GL_LINES, GL_POLYGON, GL_QUAD_STRIP


class Draw:
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
		'light_blue':   (0.68, 0.85, 0.9),
		'rust':			(0.72, 0.25, 0.05),
		'steel':		(0.69, 0.77, 0.87),
	}
	# @formatter:on

	torus_pt = []
	x_switch_pt = []

	@staticmethod
	def draw_cube(
			position: Tuple[int, int],
			size: Tuple[float, float, float],
			face_color=(0.94, 0.66, 0.75),
			border_color=(0.42, 0.56, 0.87)):
		Draw.draw_border(position, size, border_color)
		Draw.draw_faces(position, size, face_color)

	@staticmethod
	def draw_faces(position: Tuple[int, int], size: Tuple[float, float, float], face_color: Tuple[float, float, float]):
		pos_x, pos_y = position
		size_x, size_y, size_z = size
		glColor(face_color)
		for face in Draw.faces:
			glBegin(GL_POLYGON)
			for vertex in face:
				glVertex3f(
						Draw.vertices[vertex, 0] * size_x + pos_x,
						-(Draw.vertices[vertex, 1] * size_y + pos_y),
						Draw.vertices[vertex, 2] * size_z
				)
			glEnd()

	@staticmethod
	def draw_border(position: Tuple[int, int], size: Tuple[float, float, float],
					border_color: Tuple[float, float, float]):
		pos_x, pos_y = position
		size_x, size_y, size_z = size
		glBegin(GL_LINES)
		glColor(border_color)
		for edge in Draw.edges:
			for vertex in edge:
				glVertex3f(
						Draw.vertices[vertex, 0] * size_x + pos_x,
						-(Draw.vertices[vertex, 1] * size_y + pos_y),
						Draw.vertices[vertex, 2] * size_z
				)
		glEnd()

	@staticmethod
	def draw_teleport_switch(position: Tuple[int, int], color: Tuple[float, float, float]):
		radius = 0.4
		height = 0.15
		angle_stepsize = 0.1

		glPushMatrix()
		glTranslate(0.5 + position[0], -0.5 - position[1], 0)
		glColor(color)

		# side 1
		glBegin(GL_QUAD_STRIP)
		angle = 0.0
		first = True
		temp_x, temp_y = 0, 0
		while angle < 2 * pi:
			x = radius * cos(angle)
			y = radius * sin(angle)
			if y >= 0.1:
				if first:
					temp_x, temp_y = x, y
					first = False
				glVertex3f(x, y, height)
				glVertex3f(x, y, 0)
			angle += angle_stepsize

		while angle > 0:
			x = radius * cos(angle)
			y = radius * sin(angle)
			if y >= 0.1:
				glVertex3f(x * 0.6, y * 0.6, height)
				glVertex3f(x * 0.6, y * 0.6, 0)
			angle -= angle_stepsize
		glVertex3f(temp_x, temp_y, height)
		glVertex3f(temp_x, temp_y, 0)
		glEnd()

		# side 2
		glBegin(GL_QUAD_STRIP)
		angle = 0.0
		first = True
		temp_x, temp_y = 0, 0
		while angle < 2 * pi:
			x = radius * cos(angle)
			y = radius * sin(angle)
			if y <= -0.1:
				if first:
					temp_x, temp_y = x, y
					first = False
				glVertex3f(x, y, height)
				glVertex3f(x, y, 0)
			angle += angle_stepsize

		while angle > 0:
			x = radius * cos(angle)
			y = radius * sin(angle)
			if y <= -0.1:
				glVertex3f(x * 0.6, y * 0.6, height)
				glVertex3f(x * 0.6, y * 0.6, 0)
			angle -= angle_stepsize
		glVertex3f(temp_x, temp_y, height)
		glVertex3f(temp_x, temp_y, 0)
		glEnd()

		# top 1
		glColor(Draw.colors['gray'])
		glBegin(GL_QUAD_STRIP)
		angle = 0.0
		while angle < 2 * pi:
			x1 = radius * cos(angle)
			y1 = radius * sin(angle)
			x2 = radius * cos(angle) * 0.6
			y2 = radius * sin(angle) * 0.6
			if y1 >= 0.1:
				glVertex3f(x1, y1, height)
				glVertex3f(x2, y2, height)
			angle += angle_stepsize
		glEnd()

		# top 2
		glColor(Draw.colors['gray'])
		glBegin(GL_QUAD_STRIP)
		angle = 0.0
		while angle < 2 * pi:
			x1 = radius * cos(angle)
			y1 = radius * sin(angle)
			x2 = radius * cos(angle) * 0.6
			y2 = radius * sin(angle) * 0.6
			if y1 <= -0.1:
				glVertex3f(x1, y1, height)
				glVertex3f(x2, y2, height)
			angle += angle_stepsize
		glEnd()

		glPopMatrix()

	@staticmethod
	def draw_round_switch(position: Tuple[int, int], color: Tuple[float, float, float]):

		glPushMatrix()
		glTranslate(0.5 + position[0], -0.5 - position[1], 0)
		glColor(color)

		radius = 0.4
		height = 0.15
		angle = 0.0
		angle_stepsize = 0.1
		# glColor(Cube.colors['light_blue'])
		glBegin(GL_QUAD_STRIP)
		while angle < 2 * pi:
			x = radius * cos(angle)
			y = radius * sin(angle)
			glVertex3f(x, y, height - 0.01)
			glVertex3f(x, y, 0.0)
			angle += angle_stepsize

		glVertex3f(radius, 0.0, height - 0.01)
		glVertex3f(radius, 0.0, 0.0)
		glEnd()

		# glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
		glLineWidth(3)
		glColor(Draw.colors['gray'])
		glBegin(GL_POLYGON)
		angle = 0.0
		while angle < 2 * pi:
			x = radius * cos(angle)
			y = radius * sin(angle)
			glVertex3f(x, y, height)
			angle += angle_stepsize
		glVertex3f(radius, 0.0, height)
		glEnd()
		glLineWidth(1)

		glPopMatrix()

	@staticmethod
	def draw_x_switch(position: Tuple[int, int], color: Tuple[float, float, float]):

		glPushMatrix()
		glTranslate(0.5 + position[0], -0.5 - position[1], 0)

		height = 0.15
		# glColor(Cube.colors['light_blue'])
		if len(Draw.x_switch_pt) == 0:
			width = 0.15
			size = 0.25
			Draw.x_switch_pt = [
				(-width, 0),
				(-(width + size), -size),
				(-(width + size), -(width + size)),
				(-size, -(width + size)),
				(0, -width),
				(size, -(width + size)),
				(width + size, -(width + size)),
				(width + size, -size),
				(width, 0),
				(width + size, size),
				(width + size, width + size),
				(size, width + size),
				(0, width),
				(-size, width + size),
				(-(width + size), width + size),
				(-(width + size), size)]

		glColor(color)
		glBegin(GL_QUAD_STRIP)
		for x, y in Draw.x_switch_pt:
			glVertex3f(x, y, height)
			glVertex3f(x, y, 0)
		glVertex3f(Draw.x_switch_pt[0][0], Draw.x_switch_pt[0][1], height)
		glVertex3f(Draw.x_switch_pt[0][0], Draw.x_switch_pt[0][1], 0)
		glEnd()

		glLineWidth(3)
		glColor(Draw.colors['gray'])
		# -0.2, 0 -> -0.8, 0.6
		glBegin(GL_POLYGON)
		for x, y in Draw.x_switch_pt:
			glVertex3f(x, y, height)
		glEnd()
		glLineWidth(1)

		glPopMatrix()
