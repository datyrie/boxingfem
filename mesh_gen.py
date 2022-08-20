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

###################### Part 1 #################################

SCALE = 50
PATH = 'skull.png'

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

def drawContour(ct):
    x = []
    y = []
    for pt in ct.points:
        x.append(pt[0])
        y.append(pt[1])

    plt.plot(x, y)
    plt.show()

src = cv2.imread(PATH)
image = cv2.flip(src, 0)
cv2.imshow('Original', image)

meshScale = min(image.shape[0], image.shape[1]) / SCALE

img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
ret, thresh = cv2.threshold(img_gray, 150, 255, cv2.THRESH_BINARY)
cv2.imshow('Binary', thresh)

contours, hierarchy = cv2.findContours(image=thresh, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_TC89_L1)
  
image_copy = image.copy()
cv2.drawContours(image=image_copy, contours=contours, contourIdx=-1, color=(0, 255, 0), thickness=2, lineType=cv2.LINE_AA)
 
cv2.imshow('Contour', image_copy)
cv2.waitKey(0)
cv2.destroyAllWindows()

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

factory.synchronize()

gmsh.model.mesh.generate(2)

gmsh.write("mesh.msh")

# Launch the GUI to see the results:
if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()

###################### Part 2 #################################

width = image.shape[1]
height = image.shape[0]

mesh = meshio.read("mesh.msh")

points = mesh.points
cells = mesh.cells
point_data = mesh.point_data
cell_data = mesh.cell_data

eles_list = []
nodes_list = []
loads_list = []
mater_list = []

selection_result = []

cmap = get_cmap("tab20")
colors = cmap.colors 

def line_select_callback(eclick, erelease):
    global selection_result
    x1, y1 = eclick.xdata, eclick.ydata
    x2, y2 = erelease.xdata, erelease.ydata
    w = abs(x1 - x2)
    h = abs(y1 - y2)
    bx = min(x1, x2)
    by = min(y1, y2)
    selection_result = [bx, by, bx + w, by + h]

def toggle_selector(event):
    print(' Key pressed.')
    if event.key in ['Q', 'q'] and toggle_selector.RS.active:
        toggle_selector.RS.set_active(False)
    if event.key in ['A', 'a'] and not toggle_selector.RS.active:
        toggle_selector.RS.set_active(True)

def is_in_rect(rect, point):
    if (point[0] > rect[0] and point[0] < rect[2] and point[1] > rect[1] and point[1] < rect[3]) :
        return True
    else :
        return False

# write points
for i, p in enumerate(points):
    nodes_list.append([i, p[0], p[1], 0, 0])

# iterate triangle
plt.figure()
patch_list = []

index = 0
element_index = 0
for cell in cells:
    if cell.type == "triangle":
        patch_list.append([])
        for pt in cell.data:
            ptlt = [points[pt[0]][0:2].tolist(), points[pt[1]][0:2].tolist(), points[pt[2]][0:2].tolist()]
            t = plt.Polygon(ptlt, color=colors[index % len(colors)])
            plt.gca().add_patch(t)
            patch_list[-1].append(copy.deepcopy(ptlt))

            # write element
            mean = np.mean(ptlt, axis=0)
            angles = np.arctan2((ptlt-mean)[:, 1], (ptlt-mean)[:, 0])
            angles[angles < 0] = angles[angles < 0] + 2 * np.pi
            sorting_indices = np.argsort(angles)

            eles_list.append([element_index, 3, index, pt[sorting_indices[0]], pt[sorting_indices[1]], pt[sorting_indices[2]]])
            element_index += 1

        index += 1

plt.xlim([0, width])
plt.ylim([0, height])
plt.show()
plt.clf()

# assign material
index = 0
for i in patch_list:
    for pi in i:
        t = plt.Polygon(pi)
        plt.gca().add_patch(t)
    print(f"Patch {index}: ")
    index += 1
    plt.xlim([0, width])
    plt.ylim([0, height])
    plt.show()
    plt.clf()
    print(f"Young's modulus for Patch {index}: ")
    mt1 = float(input())
    print(f"Poisson's ratio for Patch {index}: ")
    mt2 = float(input())
    mater_list.append([mt1, mt2])
    index += 1

# iterate line
index = 0
x = []
y = []
clr = []
for cell in cells:
    if cell.type == "line":
        for pt in cell.data:
            x.append(points[pt[0]][0:2].tolist()[0])
            y.append(points[pt[0]][0:2].tolist()[1])
            x.append(points[pt[1]][0:2].tolist()[0])
            y.append(points[pt[1]][0:2].tolist()[1])
            clr.append(colors[index % len(colors)])
            clr.append(colors[index % len(colors)])
        index += 1

print("Select nodes with x support: ")

toggle_selector.RS = RectangleSelector(plt.gca(), line_select_callback,
                                       drawtype='box', useblit=True,
                                       button=[1, 3],  # don't use middle button
                                       minspanx=5, minspany=5,
                                       spancoords='data',
                                       interactive=True)

plt.scatter(x, y, color = clr)
plt.xlim([0, width])
plt.ylim([0, height])
plt.connect('key_press_event', toggle_selector)
plt.show()
plt.clf()

x_support_rect = copy.deepcopy(selection_result)

print("Select nodes with y support: ")

toggle_selector.RS = RectangleSelector(plt.gca(), line_select_callback,
                                       drawtype='box', useblit=True,
                                       button=[1, 3],  # don't use middle button
                                       minspanx=5, minspany=5,
                                       spancoords='data',
                                       interactive=True)

plt.scatter(x, y, color = clr)
plt.xlim([0, width])
plt.ylim([0, height])
plt.connect('key_press_event', toggle_selector)
plt.show()
plt.clf()

y_support_rect = copy.deepcopy(selection_result)

# write support
for line in nodes_list: 
    if is_in_rect(x_support_rect, [line[1], line[2]]):
        line[3] = -1
    if is_in_rect(y_support_rect, [line[1], line[2]]):
        line[4] = -1

# write load
print(f"Load x: ")
ld1 = float(input())
print(f"Load y: ")
ld2 = float(input())

print("Select nodes with load: ")

toggle_selector.RS = RectangleSelector(plt.gca(), line_select_callback,
                                       drawtype='box', useblit=True,
                                       button=[1, 3],  # don't use middle button
                                       minspanx=5, minspany=5,
                                       spancoords='data',
                                       interactive=True)

plt.scatter(x, y, color = clr)
plt.xlim([0, width])
plt.ylim([0, height])
plt.connect('key_press_event', toggle_selector)
plt.show()
plt.clf()

for index, line in enumerate(nodes_list): 
    if is_in_rect(selection_result, [line[1], line[2]]):
        loads_list.append([index, ld1, ld2])

# Create files
np.savetxt("eles.txt", eles_list, fmt="%d")
np.savetxt("nodes.txt", nodes_list, fmt=("%d", "%.4f", "%.4f", "%d", "%d"))
np.savetxt("loads.txt", loads_list, fmt=("%d", "%.6f", "%.6f"))
np.savetxt("mater.txt", mater_list, fmt="%.6f")

###################### Part 3 #################################
displacement = solids_GUI(True, True, ".\\")
plt.show()