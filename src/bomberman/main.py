import tkinter as tk
from .renderer_tk import TkRenderer
from .game import Game

def main():
    root = tk.Tk()
    root.title("Bomberman - Tkinter")
    renderer = TkRenderer(root)
    game = Game(root, renderer)
    root.protocol("WM_DELETE_WINDOW", game.quit)
    root.mainloop()

if __name__ == "__main__":
    main()
