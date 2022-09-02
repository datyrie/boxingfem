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
from solidspy.solids_GUI import solids_GUI
import tkinter
import tkinter.ttk
import time
from pyqtree import Index
import subprocess

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
    self.root.geometry('400x600')
    self.root.protocol("WM_DELETE_WINDOW", quit_callback)

    self.showOriginal = tkinter.BooleanVar()
    self.showOriginal.set(True)

    self.showPatches = tkinter.BooleanVar()
    self.showPatches.set(True)

    self.showBoundary = tkinter.BooleanVar()
    self.showBoundary.set(True)

    self.showBoundaryPoints = tkinter.BooleanVar()
    self.showBoundaryPoints.set(True)

    tkinter.ttk.Label(self.root, text="Layers").grid(row=0, column=0, sticky=tkinter.W, columnspan=2)
    tkinter.ttk.Checkbutton(self.root, text="Original Image", variable = self.showOriginal, onvalue = True, offvalue = False).grid(row=1, column=0, sticky=tkinter.W, columnspan=2)
    tkinter.ttk.Checkbutton(self.root, text="Material Patches Plot", variable = self.showPatches, onvalue = True, offvalue = False).grid(row=2, column=0, sticky=tkinter.W, columnspan=2)
    tkinter.ttk.Checkbutton(self.root, text="Boundary Plot", variable = self.showBoundary, onvalue = True, offvalue = False).grid(row=3, column=0, sticky=tkinter.W, columnspan=2)
    tkinter.ttk.Checkbutton(self.root, text="Boundary Points", variable = self.showBoundaryPoints, onvalue = True, offvalue = False).grid(row=4, column=0, sticky=tkinter.W, columnspan=2)
    self.row_start_index = 5

    self.event = "None"
  
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
    
    tkinter.ttk.Label(self.root, text="Material Patches").grid(row=self.row_start_index, column=0, sticky=tkinter.W, columnspan=2)
    self.row_start_index += 1
    for p in self.patches_legend:
      var1 = tkinter.DoubleVar()
      var1.set(1.0)
      var2 = tkinter.DoubleVar()
      var2.set(1.0)
      self.patches_material.append([var1, var2])
      tkinter.ttk.Label(self.root, text="■", foreground=_from_rgb(p[0])).grid(row=self.row_start_index, column=0, sticky=tkinter.W)
      tkinter.Label(self.root, text=p[1]).grid(row=self.row_start_index, column=1, sticky=tkinter.W)
      self.row_start_index += 1
      tkinter.ttk.Label(self.root, text="Young's Module").grid(row=self.row_start_index, column=0, sticky=tkinter.W)
      tkinter.Entry(self.root, textvariable=var1).grid(row=self.row_start_index, column=1, sticky=tkinter.W)
      self.row_start_index += 1
      tkinter.ttk.Label(self.root, text="Poisson's ratio (-1 to 0.5)").grid(row=self.row_start_index, column=0, sticky=tkinter.W)
      tkinter.ttk.Entry(self.root, textvariable=var2).grid(row=self.row_start_index, column=1, sticky=tkinter.W)
      self.row_start_index += 1
  
  def setEvent(self, e):
    self.event = e
  
  def setPointsLegend(self):
    def _from_rgb(rgb):
      (r, g, b) = rgb
      return '#%02x%02x%02x' % (int(r*255), int(g*255), int(b*255))

    tkinter.ttk.Label(self.root, text="Boundary Conditions").grid(row=self.row_start_index, column=0, sticky=tkinter.W, columnspan=2)
    self.row_start_index += 1
    tkinter.ttk.Label(self.root, text="•", foreground=_from_rgb((1, 0, 0))).grid(row=self.row_start_index, column=0, sticky=tkinter.W)
    tkinter.ttk.Label(self.root, text="Selected boundary points").grid(row=self.row_start_index, column=1, sticky=tkinter.W)
    self.row_start_index += 1
    tkinter.ttk.Label(self.root, text="⬤", foreground=_from_rgb((0, 0.5, 0.5))).grid(row=self.row_start_index, column=0, sticky=tkinter.W)
    tkinter.ttk.Label(self.root, text="Free boundary points").grid(row=self.row_start_index, column=1, sticky=tkinter.W)
    self.row_start_index += 1
    tkinter.ttk.Label(self.root, text="⬤", foreground=_from_rgb((0, 1, 0.5))).grid(row=self.row_start_index, column=0, sticky=tkinter.W)
    tkinter.ttk.Label(self.root, text="boundary points with x constraints").grid(row=self.row_start_index, column=1, sticky=tkinter.W)
    self.row_start_index += 1
    tkinter.ttk.Label(self.root, text="⬤", foreground=_from_rgb((0, 0.5, 1))).grid(row=self.row_start_index, column=0, sticky=tkinter.W)
    tkinter.ttk.Label(self.root, text="boundary points with y constraints").grid(row=self.row_start_index, column=1, sticky=tkinter.W)
    self.row_start_index += 1
    tkinter.ttk.Label(self.root, text="⬤", foreground=_from_rgb((0, 1, 1))).grid(row=self.row_start_index, column=0, sticky=tkinter.W)
    tkinter.ttk.Label(self.root, text="boundary points with x and y constraints").grid(row=self.row_start_index, column=1, sticky=tkinter.W)
    self.row_start_index += 1
    tkinter.ttk.Button(self.root, text="Apply x constraints on select", command= lambda: self.setEvent("apply-x")).grid(row=self.row_start_index, column=0, sticky=tkinter.W)
    self.row_start_index += 1
    tkinter.ttk.Button(self.root, text="Apply y constraints on select", command= lambda: self.setEvent("apply-y")).grid(row=self.row_start_index, column=0, sticky=tkinter.W)
    self.row_start_index += 1
    tkinter.ttk.Button(self.root, text="Clear constraints on select", command= lambda: self.setEvent("clear-apply")).grid(row=self.row_start_index, column=0, sticky=tkinter.W)
    self.row_start_index += 1
  
  def setForceOptions(self):
    self.forceX = tkinter.DoubleVar()
    self.forceX.set(1.0)
    self.forceY = tkinter.DoubleVar()
    self.forceY.set(1.0)
    
    tkinter.ttk.Label(self.root, text="Force on x direction").grid(row=self.row_start_index, column=0, sticky=tkinter.W)
    tkinter.ttk.Entry(self.root, textvariable=self.forceX).grid(row=self.row_start_index, column=1, sticky=tkinter.W)
    self.row_start_index += 1
    tkinter.ttk.Label(self.root, text="Force on y direction").grid(row=self.row_start_index, column=0, sticky=tkinter.W)
    tkinter.ttk.Entry(self.root, textvariable=self.forceY).grid(row=self.row_start_index, column=1, sticky=tkinter.W)
    self.row_start_index += 1
    tkinter.ttk.Button(self.root, text="Apple force on select", command= lambda: self.setEvent("apply-force")).grid(row=self.row_start_index, column=0, sticky=tkinter.W)
    self.row_start_index += 1
    tkinter.ttk.Button(self.root, text="Clear force on select", command= lambda: self.setEvent("clear-force")).grid(row=self.row_start_index, column=0, sticky=tkinter.W)
    self.row_start_index += 1
  
  def setCalculation(self):
    boldStyle = tkinter.ttk.Style()
    boldStyle.configure("Bold.TButton", font = ('Sans','10','bold'))
    tkinter.ttk.Button(self.root, text = "Calculate", style = "Bold.TButton", command= lambda: self.setEvent("calculate")).grid(row=self.row_start_index, column=0, sticky=tkinter.W)
    self.row_start_index += 1


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
    gmsh.write("data/mesh.msh")
    gmsh.finalize()
    time.sleep(0.1)

    print("[Mesh Analyzer] reading mesh")

    mesh = meshio.read("data/mesh.msh")

    self.points = mesh.points
    self.cells = mesh.cells
    self.point_data = mesh.point_data
    self.cell_data = mesh.cell_data

    self.eles_list = []
    self.nodes_list = []
    self.loads_list = []
    self.mater_list = []

    self.boundary_points = []

    cmap = get_cmap("tab20")
    self.colors = cmap.colors

    print("[Mesh Analyzer] writing nodes")
    for i, p in enumerate(self.points):
      self.nodes_list.append([i, p[0], p[1], 0, 0]) 
    
    print("[Mesh Analyzer] writing and plotting elements")
    self.plotPatches()

    print("[Mesh Analyzer] writing and plotting boundaries")
    self.plotBoundaryPoints()

    print("[Mesh Analyzer] building Qdtree")
    self.buildQdtree()
    
  
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
  
  def plotBoundaryPoints(self):
    fig = pylab.figure(figsize=[self.width / 40, self.height / 40], dpi=40)
    ax = fig.gca()

    index = 0
    x = []
    y = []
    clr = []
    point_set = set()
    for cell in self.cells:
        if cell.type == "line":
            for pt in cell.data:
              # [index, (x, y), x-constraint, y-constraint, x-force, y-force]
              if pt[0] not in point_set:
                point_set.add(pt[0])
                self.boundary_points.append([pt[0], copy.deepcopy(self.points[pt[0]][0:2].tolist()), 0, 0, 0, 0])
              if pt[1] not in point_set:
                point_set.add(pt[1])
                self.boundary_points.append([pt[1], copy.deepcopy(self.points[pt[1]][0:2].tolist()), 0, 0, 0, 0])
              x.append(self.points[pt[0]][0:2].tolist()[0])
              y.append(self.points[pt[0]][0:2].tolist()[1])
              x.append(self.points[pt[1]][0:2].tolist()[0])
              y.append(self.points[pt[1]][0:2].tolist()[1])
              clr.append((0, 0.9, 0.1))
              clr.append((0, 0.9, 0.1))
            index += 1
    plt.scatter(x, y, color = clr)
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
    self.boundary_plot = pygame.image.fromstring(renderer.tostring_rgb(), (self.width, self.height), "RGB")
    self.boundary_plot = pygame.transform.flip(self.boundary_plot, False, True)

  def buildQdtree(self):
    self.tree = Index(bbox=(0, 0, self.width, self.height))
    for p in self.boundary_points:
      self.tree.insert(p, (p[1][0], p[1][1], p[1][0], p[1][1]))
  
  def getSelection(self, bbox):
    return self.tree.intersect(bbox)

class SelectionBox:
  def __init__(self):
    self.isMouseDown = False
    self.mouseDownPos = None
    self.currentMousePos = None
  
  def onMouseDown(self, pos):
    self.mouseDownPos = pos
    self.currentMousePos = pos
    self.isMouseDown = True

  def onMouseUp(self, pos):
    self.isMouseDown = False
  
  def onMouseMove(self, pos):
    if self.isMouseDown:
      self.currentMousePos = pos
  
  def getSelectionBBox(self, canvas, size):
    x1 = (self.mouseDownPos[0] - canvas.origin[0]) / canvas.zoom
    y1 = size[1] - (self.mouseDownPos[1] - canvas.origin[1]) / canvas.zoom
    x2 = (self.currentMousePos[0] - canvas.origin[0]) / canvas.zoom
    y2 = size[1] - (self.currentMousePos[1] - canvas.origin[1]) / canvas.zoom
    return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

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

def drawSelectedPoints(generator, canvas, screen, selected):
  for b in selected:
    pygame.draw.circle(screen, (255, 0, 0), (b[1][0] * canvas.zoom + canvas.origin[0], (size[1] - b[1][1]) * canvas.zoom + canvas.origin[1]), 3, 0)

def validRect(rect):
  new_rect = list(rect)
  if new_rect[2] < 0:
    new_rect[0] = new_rect[0] + new_rect[2]
    new_rect[2] = -new_rect[2]
  if new_rect[3] < 0:
    new_rect[1] = new_rect[1] + new_rect[3]
    new_rect[3] = -new_rect[3]
  return tuple(new_rect)

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

  gui = UIPanel()
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