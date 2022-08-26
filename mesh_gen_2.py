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
from collections import deque
import tkinter
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.backends.backend_agg as agg
import pylab

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
    self.root.geometry('260x600')
    self.root.protocol("WM_DELETE_WINDOW", quit_callback)

    self.showOriginal = tkinter.BooleanVar()
    self.showOriginal.set(True)

    self.showPatches = tkinter.BooleanVar()
    self.showPatches.set(True)

    tkinter.Label(self.root, text="Layers").grid(row=0, column=0, sticky=tkinter.W, columnspan=2)
    tkinter.Checkbutton(self.root, text="Original Image", variable = self.showOriginal, onvalue = True, offvalue = False).grid(row=1, column=0, sticky=tkinter.W, columnspan=2)
    tkinter.Checkbutton(self.root, text="Patches Plot", variable = self.showPatches, onvalue = True, offvalue = False).grid(row=2, column=0, sticky=tkinter.W, columnspan=2)
  
  def __del__(self):
    self.root.destroy()
  
  def update(self):
    self.root.update()
  
  def setPatchesLegend(self, legend):
    self.patches_legend = legend
    self.patches_material = []

    def _from_rgb(rgb):
      (r, g, b) = rgb
      return '#%02x%02x%02x' % (int(r*255), int(g*255), int(b*255))
    
    row_start_index = 3
    tkinter.Label(self.root, text="Material Patches").grid(row=row_start_index, column=0, sticky=tkinter.W, columnspan=2)
    row_start_index += 1
    for p in self.patches_legend:
      var1 = tkinter.DoubleVar()
      var1.set(1.0)
      var2 = tkinter.DoubleVar()
      var2.set(1.0)
      self.patches_material.append([var1, var2])
      tkinter.Label(self.root, text="■", fg=_from_rgb(p[0])).grid(row=row_start_index, column=0, sticky=tkinter.W)
      tkinter.Label(self.root, text=p[1]).grid(row=row_start_index, column=1, sticky=tkinter.W)
      row_start_index += 1
      tkinter.Label(self.root, text="Young's Module").grid(row=row_start_index, column=0, sticky=tkinter.W)
      tkinter.Entry(self.root, textvariable=var1).grid(row=row_start_index, column=1, sticky=tkinter.W)
      row_start_index += 1
      tkinter.Label(self.root, text="Poisson’s ratio").grid(row=row_start_index, column=0, sticky=tkinter.W)
      tkinter.Entry(self.root, textvariable=var2).grid(row=row_start_index, column=1, sticky=tkinter.W)
      row_start_index += 1


class MeshGenerator:
  def __init__(self, path):
    print("[Mesh Generator] reading file")
    src = cv2.imread(path)
    image = cv2.flip(src, 0)
    self.width = image.shape[1]
    self.height = image.shape[0]

    meshScale = min(image.shape[0], image.shape[1]) / SCALE

    print("[Mesh Generator] binarize image")
    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(img_gray, 150, 255, cv2.THRESH_BINARY)

    print("[Mesh Generator] extracting contours")
    contours, hierarchy = cv2.findContours(image=thresh, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_TC89_L1)

    print("[Mesh Generator] adding geometry")
    gmsh.initialize()
    gmsh.model.add("model")

    factory = gmsh.model.geo
    cts = []

    for c, info in zip(contours, hierarchy[0]):
        if info[3] == -1:
            cts.append(None)
            continue
        cts.append(Contour(factory, c, info, meshScale))

    for ct in cts:
        if ct is not None:
            ct.makePlane(factory, cts)

    print("[Mesh Generator] generating mesh")
    factory.synchronize()
    gmsh.model.mesh.generate(2)

    print("[Mesh Generator] writing mesh")
    gmsh.write("mesh.msh")
    gmsh.finalize()
    time.sleep(0.1)

    print("[Mesh Analyzer] reading mesh")

    mesh = meshio.read("mesh.msh")

    self.points = mesh.points
    self.cells = mesh.cells
    self.point_data = mesh.point_data
    self.cell_data = mesh.cell_data

    self.eles_list = []
    self.nodes_list = []
    self.loads_list = []
    self.mater_list = []

    cmap = get_cmap("tab20")
    self.colors = cmap.colors

    print("[Mesh Analyzer] writing nodes")
    for i, p in enumerate(self.points):
      self.nodes_list.append([i, p[0], p[1], 0, 0]) 
    
    print("[Mesh Analyzer] writing and plotting elements")
    self.plotPatches()
    
  
  def plotPatches(self):
    fig = pylab.figure(figsize=[self.width / 40, self.height / 40], dpi=40)
    ax = fig.gca()

    self.patch_list = []
    index = 0
    element_index = 0

    self.patches_plot_legend = []

    for cell in self.cells:
        if cell.type == "triangle":
            self.patch_list.append([])
            legend_logged = False
            for pt in cell.data:
                ptlt = [self.points[pt[0]][0:2].tolist(), self.points[pt[1]][0:2].tolist(), self.points[pt[2]][0:2].tolist()]
                color = self.colors[index % len(self.colors)]
                t = plt.Polygon(ptlt, color = color)

                if not legend_logged:
                  self.patches_plot_legend.append([color, f"Material {index + 1}"])
                  legend_logged = True

                ax.add_patch(t)
                self.patch_list[-1].append(copy.deepcopy(ptlt))

                # write element
                mean = np.mean(ptlt, axis=0)
                angles = np.arctan2((ptlt-mean)[:, 1], (ptlt-mean)[:, 0])
                angles[angles < 0] = angles[angles < 0] + 2 * np.pi
                sorting_indices = np.argsort(angles)

                self.eles_list.append([element_index, 3, index, pt[sorting_indices[0]], pt[sorting_indices[1]], pt[sorting_indices[2]]])
                element_index += 1

            index += 1
    
    ax.axis(xmin=0, xmax=self.width, ymin=0, ymax=self.height)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    renderer = canvas.get_renderer()
    self.patches_plot = pygame.image.fromstring(renderer.tostring_rgb(), (self.width, self.height), "RGB")
    self.patches_plot = pygame.transform.flip(self.patches_plot, False, True)

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

  gui = UIPanel()
  gui.setPatchesLegend(generator.patches_plot_legend)
    
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
    if gui.showPatches.get():
      canvas.getSurface().blit(generator.patches_plot, (0, 0))
    canvas.end(screen)

    pygame.display.update()

  pygame.quit()