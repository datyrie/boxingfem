import tkinter
import tkinter.ttk

"""The helper UI class for configs and settings"""
class UIPanel:
  def __init__(self, quit_handler):
    self.root = tkinter.Tk()
    self.root.title("boxingfem Config")
    self.root.geometry('400x600')
    self.root.protocol("WM_DELETE_WINDOW", quit_handler)

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