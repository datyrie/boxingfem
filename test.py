import pygame
from pygame.locals import *
import tkinter
import sys   # for exit and arg

def Draw(surf):
  #Clear view
  surf.fill((80,80,80))
  pygame.display.flip()


def GetInput():

  for event in pygame.event.get():
    if event.type == QUIT:
      return True
    if event.type == KEYDOWN:
      print(event)
    if event.type == MOUSEBUTTONDOWN:
      print(event)
    sys.stdout.flush()  # get stuff to the console
  return False


Done = False

def quit_callback():
  global Done
  Done = True

def main():

  # initialise pygame
  pygame.init()
  ScreenSize = (200,100)
  Surface = pygame.display.set_mode(ScreenSize)

  #initialise tkinter
  root = tkinter.Tk()
  root.protocol("WM_DELETE_WINDOW", quit_callback)
  main_dialog =  tkinter.Frame(root)
  main_dialog.pack()

  # start pygame clock
  clock = pygame.time.Clock()
  gameframe = 0

  # main loop
  while not Done:
    try:
      main_dialog.update()
    except:
      print("dialog error")

    if GetInput():  # input event can also comes from diaglog
      break
    Draw(Surface)
    clock.tick(100) # slow it to something slightly realistic
    gameframe += 1

  main_dialog.destroy()

if __name__ == '__main__': main()