"""A helper class for points selection on canvas"""
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