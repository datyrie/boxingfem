from solidspy.solids_GUI import solids_GUI
import matplotlib.pyplot as plt

if __name__ == '__main__':
  displacement = solids_GUI(True, True, "./data/")
  plt.show()