# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
from solidspy.solids_GUI import solids_GUI
import numpy as np
from matplotlib.tri import Triangulation

nodes = np.loadtxt("nodes.txt")
eles = np.loadtxt("eles.txt")

def mesh2tri(nodes, elements):
    coord_x = nodes[:, 1]
    coord_y = nodes[:, 2]
    triangs = []
    for elem in elements:
        if elem[1] == 1:
            triangs.append(elem[[3, 4, 5]])
            triangs.append(elem[[5, 6, 3]])
        if elem[1] == 2:
            triangs.append(elem[[3, 6, 8]])
            triangs.append(elem[[6, 7, 8]])
            triangs.append(elem[[6, 4, 7]])
            triangs.append(elem[[7, 5, 8]])
        if elem[1] == 3:
            triangs.append(elem[3:])
        if elem[1] == 4:
            triangs.append(elem[[3, 7, 11]])
            triangs.append(elem[[7, 4, 8]])
            triangs.append(elem[[3, 11, 10]])
            triangs.append(elem[[7, 8, 11]])
            triangs.append(elem[[10, 11, 9]])
            triangs.append(elem[[11, 8, 5]])
            triangs.append(elem[[10, 9, 6]])
            triangs.append(elem[[11, 5, 9]])

    tri = Triangulation(coord_x, coord_y, np.array(triangs))
    return tri

def tri_plot(tri, field, title="", levels=12, savefigs=False,
             plt_type="contourf", filename="solution_plot.pdf"):
    if plt_type == "pcolor":
        disp_plot = plt.tripcolor
    elif plt_type == "contourf":
        disp_plot = plt.tricontourf
    disp_plot(tri, field, levels, shading="gouraud")
    plt.title(title)
    plt.colorbar(orientation='vertical')
    plt.axis("image")
    if savefigs:
        plt.savefig(filename)

def plot_node_field(field, nodes, elements, plt_type="contourf", levels=12,
                    savefigs=False, title=None, figtitle=None,
                    filename=None):
    tri = mesh2tri(nodes, elements)
    if len(field.shape) == 1:
        nfields = 1
    else:
        _, nfields = field.shape
    if title is None:
        title = ["" for cont in range(nfields)]
    if figtitle is None:
        figs = plt.get_fignums()
        nfigs = len(figs)
        figtitle = [cont + 1 for cont in range(nfigs, nfigs + nfields)]
    if filename is None:
        filename = ["output{}.pdf".format(cont) for cont in range(nfields)]
    for cont in range(nfields):
        if nfields == 1:
            current_field = field
        else:
            current_field = field[:, cont]
        plt.figure(figtitle[cont])
        tri_plot(tri, current_field, title=title[cont], levels=levels,
                 plt_type=plt_type, savefigs=savefigs,
                 filename=filename[cont])
        if savefigs:
            plt.savefig(filename[cont])

if __name__ == '__main__':
  disp_complete, strain_nodes, stress_nodes = solids_GUI(False, True, ".\\")
  plt.figure()
  plot_node_field(strain_nodes, 
                  nodes, 
                  eles, 
                  title=[r"$\epsilon_{xx}$",
                         r"$\epsilon_{yy}$",
                         r"$\gamma_{xy}$",],
                  figtitle=["Strain epsilon-xx",
                         "Strain epsilon-yy",
                         "Strain gamma-xy"])
  plt.show()
