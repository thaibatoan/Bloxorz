# coding=utf-8
import time

import pygame
from OpenGL.raw.GL.VERSION.GL_1_0 import glBlendFunc, glClear, glClearColor, glEnable, glHint, glLineWidth, glRotatef, \
	glTranslatef, glViewport
from OpenGL.raw.GL.VERSION.GL_1_1 import GL_BLEND, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_DEPTH_TEST, \
	GL_LINE_SMOOTH, GL_LINE_SMOOTH_HINT, GL_NICEST, GL_ONE_MINUS_SRC_ALPHA, GL_POLYGON_SMOOTH, GL_POLYGON_SMOOTH_HINT, \
	GL_SRC_ALPHA
from OpenGL.raw.GLU import gluLookAt, gluPerspective
from pygame.constants import DOUBLEBUF, FULLSCREEN, HWSURFACE, OPENGL


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
		ratio = (self.width ** 2 + self.height ** 2) / 325
		glClearColor(0.83137254902, 0.83137254902, 0.83137254902, 1)
		gluPerspective(60, (size[0] / size[1]), 0.1, 1000.0)
		gluLookAt(0.0, 0.0, 3.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
		gluLookAt(4 * ratio, 4 * ratio, 8 * ratio, 0, 0, 0, 0, 0, 1)

		glRotatef(135, 0, 0, 1)
		glRotatef(5, 0, 0, 1)
		glTranslatef(-self.width / 2, self.height / 2 + 1, 0)
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
