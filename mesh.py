import cv2
import copy
import gmsh
import time
import meshio
import pylab
import numpy as np
import pygame
import matplotlib.pyplot as plt
from pyqtree import Index
from matplotlib.cm import get_cmap

import matplotlib
matplotlib.use("Agg")
import matplotlib.backends.backend_agg as agg

from contour import Contour

# Given an input image, the size of the mesh is approximately the length size dividing SCALE
SCALE = 50

"""A class for 2D mesh generation. Give the path of the input file, the class will 
generate meshes as the required formats used my the FEM library.
"""
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