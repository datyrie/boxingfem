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