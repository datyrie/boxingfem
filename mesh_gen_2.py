from pickle import FALSE
import tkinter
import tkinter.filedialog
import pygame
import cv2
import numpy as np
import gmsh
import copy
import sys
import meshio
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
from matplotlib.widgets import RectangleSelector
from solidspy.solids_GUI import solids_GUI
import pygame_gui
from collections import deque
import tkinter

SCALE = 50

"""Create a Tk file dialog and cleanup when finished"""
def prompt_file():
    top = tkinter.Tk()
    top.withdraw()  # hide window
    file_name = tkinter.filedialog.askopenfilename(parent=top)
    top.destroy()
    return file_name

"""Helper class to extract the contours for the gmsh"""
class Contour:
  def __init__(self, factory, point_list, hierarchy, meshScale = 1):
    self.points = []
    self.poly_list = []
    self.line_indices = []
    self.loop_index = -1
    self.plane_index = -1

    self.hierarchy = hierarchy

    for pt in point_list:
      self.addPoint(factory, pt, meshScale)
    
    for i in range(len(self.poly_list)):
      self.line_indices.append(factory.addLine(self.poly_list[i], self.poly_list[(i + 1) % len(self.poly_list)]))

    self.loop_index = factory.addCurveLoop(self.line_indices)

  def addPoint(self, factory, point_list, meshScale):
    pt = [point_list[0][0], point_list[0][1]]
    index = factory.addPoint(pt[0], pt[1], 0, meshScale)
    self.points.append(pt)
    self.poly_list.append(index)
  
  def makePlane(self, factory, contours):
    line_list = [self.loop_index]
    next = self.hierarchy[2]
    while next != -1:
      line_list.append(contours[next].loop_index)
      next = contours[next].hierarchy[0]
    self.plane_index = factory.addPlaneSurface(line_list)

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

running = False

def quit_callback():
  global running
  running = False

class UIPanel:
  def __init__(self):
    self.root = tkinter.Tk()
    self.root.title("boxingfem Config")
    self.root.geometry('200x600')
    self.root.protocol("WM_DELETE_WINDOW", quit_callback)

    self.showOriginal = tkinter.BooleanVar()
    self.showOriginal.set(True)

    tkinter.Label(self.root, text="Layers").grid(row=0, column=0, sticky=tkinter.W)
    tkinter.Checkbutton(self.root, text="Original Image", variable = self.showOriginal, onvalue = True, offvalue = False).grid(row=1, column=0, sticky=tkinter.W)
  
  def __del__(self):
    self.root.destroy()
  
  def update(self):
    self.root.update()

if __name__ == '__main__':
  pygame.init()

  image = pygame.image.load(prompt_file())
  image = pygame.transform.flip(image, False, True)
  size = image.get_rect().size

  screen = pygame.display.set_mode((640, 480), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
    
  # set title
  pygame.display.set_caption('boxingfem')

  canvas = Canvas(size)

  gui = UIPanel()
    
  # run window
  running = True
  while running:
    gui.update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
          running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
          if event.button == 3:
            canvas.onMouseDown(event.pos)
        if event.type == pygame.MOUSEBUTTONUP:
          if event.button == 3:
            canvas.onMouseUp(event.pos)
        if event.type == pygame.MOUSEMOTION:
          canvas.onMouseMove(pygame.mouse.get_pos())
        if event.type == pygame.MOUSEWHEEL:
          canvas.onMouseWheel(event.y)

    screen.fill((255, 255, 255))

    canvas.begin()
    if gui.showOriginal.get():
      canvas.getSurface().blit(image, (0, 0))
    canvas.end(screen)

    pygame.display.update()

  pygame.quit()