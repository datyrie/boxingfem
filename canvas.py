import pygame

"""Pygame canvas that allows pan and zoom"""
class Canvas:
  def __init__(self, surface_size):
    self.surface_size = surface_size
    self.origin = (0, 0)
    self.zoom = 1

    self.mouseDownPos = None
    self.isMouseDown = False

  def begin(self):
    self.surface = pygame.Surface(self.surface_size, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
    self.surface.fill((255, 255, 255))

  def getSurface(self):
    return self.surface

  def transformPoints(self, points):
    return list(map(lambda p: (p[1] * self.zoom, p[0] * self.zoom), points))

  def end(self, screen):
    self.surface = pygame.transform.smoothscale(self.surface, (self.surface_size[0] * self.zoom, self.surface_size[1] * self.zoom))
    self.surface = pygame.transform.flip(self.surface, False, True)
    screen.blit(self.surface, self.origin)
  
  def onMouseDown(self, pos):
    self.mouseDownPos = pos
    self.isMouseDown = True

  def onMouseUp(self, pos):
    self.isMouseDown = False
  
  def onMouseMove(self, pos):
    if self.isMouseDown:
      self.origin = (self.origin[0] + pos[0] - self.mouseDownPos[0], self.origin[1] + pos[1] - self.mouseDownPos[1])
      self.mouseDownPos = pos
  
  def onMouseWheel(self, direction):
    if direction > 0:
      self.zoom *= 1.05
    else:
      self.zoom *= 0.95