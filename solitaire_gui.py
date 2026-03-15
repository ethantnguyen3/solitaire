import tkinter as tk
import math
import board as logic
from tkinter import messagebox # For the Game Over popup
import game_engine 
class SolitaireGUI:
    def __init__(self, root): 
        self.root = root 
        self.root.title("Peg Solitaire") 
        self.root.geometry("600x650") 

        # --- Variables to store user input ---
        self.size_var = tk.StringVar(value="7")
        self.type_var = tk.StringVar(value=logic.BoardType.ENGLISH)

        # --- Control Panel Setup ---
        control_frame = tk.Frame(root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        tk.Label(control_frame, text="Board size:").grid(row=0, column=0, sticky=tk.W) 
        tk.Entry(control_frame, textvariable=self.size_var, width=10).grid(row=0, column=1, sticky=tk.W) 

        OPTIONS = [
            ("English", logic.BoardType.ENGLISH), 
            ("Hexagon", logic.BoardType.HEXAGON), 
            ("Diamond", logic.BoardType.DIAMOND)
        ]
        
        for i, (text, value) in enumerate(OPTIONS):
            tk.Radiobutton(
                control_frame, text=text, variable=self.type_var, value=value
            ).grid(row=1, column=i, sticky=tk.W)

        tk.Button(control_frame, text="New Game", command=self.update_board).grid(row=2, column=0, pady=10) 

        # --- Canvas Setup ---
        self.cell_size = 50
        self.peg_radius = 20
        self.selected_peg = None # Tracks the peg you want to move
        self.game_over = False
        
        self.canvas = tk.Canvas(root, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse clicks to our new interaction function
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Draw the initial board
        self.update_board()

    def update_board(self):
        try:
            board_size = int(self.size_var.get())
        except ValueError:
            board_size = 7 
            
        board_type = self.type_var.get()
        self.board_layout = logic.generate_board_layout(board_type, board_size)
        self.selected_peg = None
        self.game_over = False

        self.canvas.delete("all")
        self.render_board_and_pegs(board_type)
        self.check_for_game_over(board_type)

    def check_for_game_over(self, board_type):
        """Show the end-of-game rating when no valid moves remain."""
        if self.game_over:
            return

        if game_engine.check_game_over(self.board_layout, board_type):
            self.game_over = True
            score = game_engine.get_score_rating(self.board_layout)
            messagebox.showinfo("Game Over", f"No more valid moves are possible.\nRating: {score}")

    def _cell_pixel(self, r, c, radius, board_type, cell_size):
        """Return (pixel_x, pixel_y) for a cell using a given cell_size."""
        dc = c - radius
        dr = r - radius
        if board_type == logic.BoardType.HEXAGON:
            px = cell_size * math.sqrt(3) * (dc + dr / 2.0)
            py = cell_size * 1.5 * dr
        else:
            px = dc * cell_size
            py = dr * cell_size
        return px, py

    def render_board_and_pegs(self, board_type):
        # Force the canvas to update so we get the real window dimensions
        self.root.update_idletasks()
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        # Fallback just in case the canvas hasn't drawn to the screen yet
        if canvas_w < 10: 
            canvas_w, canvas_h = 600, 500

        radius = len(self.board_layout) // 2

        # --- PASS 1: compute bounding box with unit cell_size=1 ---
        xs, ys = [], []
        for r in range(len(self.board_layout)):
            for c in range(len(self.board_layout[0])):
                if self.board_layout[r][c] == logic.CellState.INVALID:
                    continue
                px, py = self._cell_pixel(r, c, radius, board_type, 1.0)
                xs.append(px)
                ys.append(py)

        if not xs:
            return

        # Tile half-extent at unit cell_size
        if board_type == logic.BoardType.HEXAGON:
            half_ext = 1.0  # hex circumradius == cell_size
        else:
            half_ext = 0.5  # square half-side

        padding = 20  # pixels of margin around the board
        span_x = (max(xs) - min(xs)) + 2 * half_ext
        span_y = (max(ys) - min(ys)) + 2 * half_ext

        scale = min(
            (canvas_w - padding * 2) / span_x,
            (canvas_h - padding * 2) / span_y
        )
        # Cap at the default cell size so it doesn't grow huge on small boards
        scale = min(scale, self.cell_size)

        # Peg radius proportional to 40% of cell size
        peg_radius = scale * 0.4

        center_x = canvas_w / 2
        center_y = canvas_h / 2

        # --- PASS 2: draw ---
        for r in range(len(self.board_layout)):
            for c in range(len(self.board_layout[0])):
                state = self.board_layout[r][c]
                if state == logic.CellState.INVALID:
                    continue

                ux, uy = self._cell_pixel(r, c, radius, board_type, scale)
                pixel_x = center_x + ux
                pixel_y = center_y + uy

                # --- DRAW TILE BACKGROUNDS ---
                if board_type == logic.BoardType.HEXAGON:
                    points = []
                    for i in range(6):
                        angle_rad = math.pi / 180 * (60 * i - 30)
                        points.append(pixel_x + scale * math.cos(angle_rad))
                        points.append(pixel_y + scale * math.sin(angle_rad))
                    self.canvas.create_polygon(points, outline="black", fill="burlywood")
                else:
                    half = scale / 2
                    self.canvas.create_rectangle(
                        pixel_x - half, pixel_y - half,
                        pixel_x + half, pixel_y + half,
                        outline="black", fill="burlywood"
                    )

                # --- DRAW PEGS & HOLES ---
                if state == logic.CellState.PEG:
                    self.canvas.create_oval(
                        pixel_x - peg_radius, pixel_y - peg_radius,
                        pixel_x + peg_radius, pixel_y + peg_radius,
                        outline="black", fill="saddlebrown", tags=f"peg_{r}_{c}"
                    )
                elif state == logic.CellState.HOLE:
                    self.canvas.create_oval(
                        pixel_x - peg_radius, pixel_y - peg_radius,
                        pixel_x + peg_radius, pixel_y + peg_radius,
                        outline="saddlebrown", fill="black", tags=f"hole_{r}_{c}"
                    )

    def on_canvas_click(self, event):
        """Handles mouse clicks to select pegs and make jumps."""
        if self.game_over:
            return

        # Ask Tkinter what item is under the mouse pointer
        item = self.canvas.find_withtag("current")

        if not item:
            # Clicked empty background, deselect any peg
            self.selected_peg = None
            self.canvas.delete("all")
            self.render_board_and_pegs(self.type_var.get())
            return

        # Read the tag we placed on the circle (e.g., "peg_3_4")
        tags = self.canvas.gettags(item[0])
        clicked_type, r, c = None, -1, -1

        for tag in tags:
            if tag.startswith("peg_") or tag.startswith("hole_"):
                parts = tag.split("_")
                clicked_type = parts[0]
                r = int(parts[1])
                c = int(parts[2])
                break

        board_type = self.type_var.get()

        # LOGIC: Picking up a peg
        if clicked_type == "peg":
            self.selected_peg = (r, c)
            # Redraw to show selection highlight
            self.canvas.delete("all")
            self.render_board_and_pegs(board_type)

        # LOGIC: Clicking a hole to jump into
        elif clicked_type == "hole" and self.selected_peg is not None:
            start_pos = self.selected_peg
            end_pos = (r, c)

            # Ask the game engine if this is allowed
            valid_moves = game_engine.get_all_valid_moves(self.board_layout, board_type)

            if (start_pos, end_pos) in valid_moves:
                # Make the move!
                game_engine.execute_move(self.board_layout, start_pos, end_pos)
                self.selected_peg = None

                # Redraw the updated board
                self.canvas.delete("all")
                self.render_board_and_pegs(board_type)
                self.check_for_game_over(board_type)
            else:
                # Invalid move, cancel selection
                self.selected_peg = None
                self.canvas.delete("all")
                self.render_board_and_pegs(board_type)