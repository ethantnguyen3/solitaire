import tkinter as tk
# sets up GUI for Solitaire game, including board layout, pegs, and possible move indicators
class SolitaireGUI:
    def __init__(self, root): 
        self.root = root 
        self.root.title("Solitaire Game") 
        self.root.geometry("400x400") 

        #lines 10-30 AI generated
        label = tk.Label(root, text="Board size:") 
        entry = tk.Entry(root, width=10) 

        label.pack(anchor=tk.W, padx=5, pady=5)
        entry.pack(anchor=tk.W, padx=5, pady=5) 

        OPTIONS = [
            ("Option 1", "English"), 
            ("Option 2", "Hexagon"), 
            ("Option 3", "Diamond")]
        
        variable = tk.StringVar(value="English")
        for text, value in OPTIONS:
            tk.Radiobutton(
                root,
                text=text,
                variable=variable,
                value=value
            ).pack(anchor=tk.W)

        var = tk.BooleanVar()
        checkbutton = tk.Checkbutton(
            root,
            text="Record Game",
            variable=var
        )
        checkbutton.pack()   

        replay = tk.Button(root, text="Replay") 
        new_game = tk.Button(root, text="New Game") 
        autoplay = tk.Button(root, text="Autoplay") 
        randomize = tk.Button(root, text="Randomize") 

        #lines 44 and beyond AI generated
        self.cell_size = 60
        self.peg_radius = 20
        self.board_size = 7
        # Define the valid cell locations (1 for valid, 0 for invalid in the cross shape)
        self.board_layout = [
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0]
        ]
        # Initial pegs setup (assuming center is empty)
        self.pegs = [row[:] for row in self.board_layout]
        self.pegs[3][3] = 0 # Empty center
        
        self.canvas = tk.Canvas(root, width=self.board_size * self.cell_size + 20, 
                                height=self.board_size * self.cell_size + 20, bg='white')
        self.canvas.pack()

        self.draw_board()
        self.draw_pegs()
        # Example function to show how to draw a move arrow
        self.draw_possible_move(2, 3, 4, 3) 
    def get_coords(self, row, col):
        """Calculate the center coordinates for a given row and column."""
        x = col * self.cell_size + self.cell_size // 2 + 10
        y = row * self.cell_size + self.cell_size // 2 + 10
        return x, y

    def draw_board(self):
        """Draw the grid lines for the cross shape."""
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.board_layout[r][c] == 1:
                    x1 = c * self.cell_size + 10
                    y1 = r * self.cell_size + 10
                    x2 = x1 + self.cell_size
                    y2 = y1 + self.cell_size
                    # Draw cell background
                    self.canvas.create_rectangle(x1, y1, x2, y2, outline="black", fill="burlywood")
                    # Draw grid lines (optional, the rectangles already form a grid)

    def draw_pegs(self):
        """Draw circles (pegs) in each valid cell."""
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.pegs[r][c] == 1:
                    x, y = self.get_coords(r, c)
                    # Use create_oval to draw a circle
                    self.canvas.create_oval(x - self.peg_radius, y - self.peg_radius, 
                                            x + self.peg_radius, y + self.peg_radius, 
                                            outline="black", fill="saddlebrown", tags="peg")

    def draw_possible_move(self, from_row, from_col, to_row, to_col):
        """Draw a red arrow to indicate a possible move."""
        x_start, y_start = self.get_coords(from_row, from_col)
        x_end, y_end = self.get_coords(to_row, to_col)
        # Draw a line with an arrow
        self.canvas.create_line(x_start, y_start, x_end, y_end, arrow=tk.LAST, 
                                fill="red", width=3, tags="move_arrow")
        # You would typically delete/hide this arrow after a move is made
        # self.canvas.delete("move_arrow") 

if __name__ == "__main__":
    root = tk.Tk()
    app = SolitaireGUI(root)
    root.mainloop()