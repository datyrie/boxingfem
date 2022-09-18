import tkinter
import tkinter.filedialog
import numpy as np
import pygame
from solidspy.solids_GUI import solids_GUI
import tkinter
import tkinter.ttk
import time
import subprocess

from mesh import MeshGenerator
from canvas import Canvas
from ui import UIPanel
from selectionbox import SelectionBox

# Running indicator
running = False

"""Create a Tk file dialog and cleanup when finished"""
def prompt_file():
    top = tkinter.Tk()
    top.withdraw()  # hide window
    file_name = tkinter.filedialog.askopenfilename(parent=top)
    top.destroy()
    return file_name

"""Callback function when quiting command is received"""
def quit_callback():
  global running
  running = False

"""Helper function for drawing boundary points on canvas"""
def drawBoundaryPoints(generator, canvas, screen):
  def getColor(x_constraint, y_constraint):
    if x_constraint < 0 and y_constraint < 0:
      return (0, 255, 255)
    if x_constraint < 0 and y_constraint == 0:
      return (0, 255, 128)
    if x_constraint == 0 and y_constraint < 0:
      return (0, 128, 255)
    return (0, 128, 128)
  
  def transformPose(x, y):
    return (x * canvas.zoom + canvas.origin[0], (size[1] - y) * canvas.zoom + canvas.origin[1])

  for b in generator.boundary_points:
    pygame.draw.circle(screen, getColor(b[2], b[3]), transformPose(b[1][0], b[1][1]), 5, 0)

    if b[4] != 0 or b[5] != 0:
      pygame.draw.line(screen, (251, 206, 177), transformPose(b[1][0], b[1][1]), transformPose(b[1][0] + b[4] * canvas.zoom, b[1][1] + b[5] * canvas.zoom), 4)

"""Helper function for drawing selected points on canvas"""
def drawSelectedPoints(generator, canvas, screen, selected):
  for b in selected:
    pygame.draw.circle(screen, (255, 0, 0), (b[1][0] * canvas.zoom + canvas.origin[0], (size[1] - b[1][1]) * canvas.zoom + canvas.origin[1]), 3, 0)

"""Helper function to make sure the rectangle is in the correct format"""
def validRect(rect):
  new_rect = list(rect)
  if new_rect[2] < 0:
    new_rect[0] = new_rect[0] + new_rect[2]
    new_rect[2] = -new_rect[2]
  if new_rect[3] < 0:
    new_rect[1] = new_rect[1] + new_rect[3]
    new_rect[3] = -new_rect[3]
  return tuple(new_rect)

# Container holding the selected points
selected_points = []

if __name__ == '__main__':
  pygame.init()

  path = prompt_file()
  generator = MeshGenerator(path)

  image = pygame.image.load(path)
  image = pygame.transform.flip(image, False, True)
  size = image.get_rect().size

  screen = pygame.display.set_mode((640, 480), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
    
  # set title
  pygame.display.set_caption('boxingfem')

  canvas = Canvas(size)

  gui = UIPanel(quit_callback)
  gui.setPatchesLegend(generator.patches_plot_legend)
  gui.setPointsLegend()
  gui.setForceOptions()
  gui.setCalculation()
    
  selection = SelectionBox()

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
          elif event.button == 1:
            selection.onMouseDown(event.pos)
        if event.type == pygame.MOUSEBUTTONUP:
          if event.button == 3:
            canvas.onMouseUp(event.pos)
          elif event.button == 1:
            selection.onMouseUp(event.pos)
        if event.type == pygame.MOUSEMOTION:
          canvas.onMouseMove(pygame.mouse.get_pos())
          selection.onMouseMove(pygame.mouse.get_pos())
        if event.type == pygame.MOUSEWHEEL:
          canvas.onMouseWheel(event.y)

    screen.fill((255, 255, 255))

    canvas.begin()
    if gui.showOriginal.get():
      canvas.getSurface().blit(image, (0, 0))
    if gui.showPatches.get():
      canvas.getSurface().blit(generator.patches_plot, (0, 0))
    if gui.showBoundary.get():
      canvas.getSurface().blit(generator.boundary_plot, (0, 0))
    canvas.end(screen)

    # Draw boundary points
    if gui.showBoundaryPoints.get():
      drawBoundaryPoints(generator, canvas, screen)
      drawSelectedPoints(generator, canvas, screen, selected_points)
    
    # Draw selection box
    if selection.isMouseDown: 
      pygame.draw.rect(screen, (255, 0, 0), validRect((selection.mouseDownPos[0], 
                                                       selection.mouseDownPos[1], 
                                                       selection.currentMousePos[0] - selection.mouseDownPos[0], 
                                                       selection.currentMousePos[1] - selection.mouseDownPos[1])), 2)
      selected_points = generator.getSelection(selection.getSelectionBBox(canvas, size))

    # Read UI events
    if gui.event == "apply-x":
      for p in selected_points:
        p[2] = -1
    elif gui.event == "apply-y":
      for p in selected_points:
        p[3] = -1
    elif gui.event == "clear-apply":
      for p in selected_points:
        p[2] = 0
        p[3] = 0
    elif gui.event == "apply-force":
      for p in selected_points:
        p[4] = gui.forceX.get()
        p[5] = gui.forceY.get()
    elif gui.event == "clear-force":
      for p in selected_points:
        p[4] = 0
        p[5] = 0
    elif gui.event == "calculate":
      print("Writting files")
      for p in generator.boundary_points:
        generator.nodes_list[p[0]][3] = p[2]
        generator.nodes_list[p[0]][4] = p[3]
        if p[4] != 0 or p[5] != 0:
          generator.loads_list.append([p[0], p[4], p[5]])
      for p in gui.patches_material:
        generator.mater_list.append([p[0].get(), p[1].get()])
      
      # Create files
      np.savetxt("data/eles.txt", generator.eles_list, fmt="%d")
      np.savetxt("data/nodes.txt", generator.nodes_list, fmt=("%d", "%.4f", "%.4f", "%d", "%d"))
      np.savetxt("data/loads.txt", generator.loads_list, fmt=("%d", "%.6f", "%.6f"))
      np.savetxt("data/mater.txt", generator.mater_list, fmt="%.6f")

      print("Done writting!")
      time.sleep(0.1)
      subprocess.call(['python','run_solidspy.py'])
    
    gui.event = ""

    pygame.display.update()

  pygame.quit()