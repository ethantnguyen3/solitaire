import tkinter as tk
import math
from tkinter import filedialog, messagebox
import game_engine


class SolitaireGUI:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Peg Solitaire")
        self.root.geometry("600x650")

        # --- Variables to store user input ---
        self.size_var = tk.StringVar(value="7")
        self.type_var = tk.StringVar(value=game_engine.BoardType.ENGLISH)
        self.mode_var = tk.StringVar(value="Manual")
        self.record_btn_text = tk.StringVar(value="Start Recording")
        self.autoplay_btn_text = tk.StringVar(value="Start Autoplay")
        self.replay_status_text = tk.StringVar(value="Replay: not loaded")
        self._auto_job = None
        self.autoplay_running = False
        self.replay_session = None

        # --- Control Panel Setup ---
        control_frame = tk.Frame(root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        tk.Label(control_frame, text="Board size:").grid(row=0, column=0, sticky=tk.W)
        tk.Entry(control_frame, textvariable=self.size_var, width=10).grid(row=0, column=1, sticky=tk.W)
        #lines 42 and down are ChatGPT generated + anything concerning the automated moves
        OPTIONS = [
            ("English", game_engine.BoardType.ENGLISH),
            ("Hexagon", game_engine.BoardType.HEXAGON),
            ("Diamond", game_engine.BoardType.DIAMOND),
        ]

        for i, (text, value) in enumerate(OPTIONS):
            tk.Radiobutton(
                control_frame, text=text, variable=self.type_var, value=value
            ).grid(row=1, column=i, sticky=tk.W)

        tk.Label(control_frame, text="Mode:").grid(row=2, column=0, sticky=tk.W)
        tk.Radiobutton(control_frame, text="Manual", variable=self.mode_var, value="Manual").grid(
            row=2, column=1, sticky=tk.W
        )
        tk.Radiobutton(control_frame, text="Automated", variable=self.mode_var, value="Automated").grid(
            row=2, column=2, sticky=tk.W
        )

        tk.Button(control_frame, text="New Game", command=self.new_game).grid(row=3, column=0, pady=10)
        tk.Button(control_frame, text="Randomize", command=self.randomize_board).grid(row=3, column=1, pady=10)
        tk.Button(control_frame, textvariable=self.record_btn_text, command=self.toggle_recording).grid(
            row=3, column=2, pady=10
        )
        tk.Button(control_frame, text="Load Replay", command=self.replay_recording_from_file).grid(
            row=3, column=3, pady=10
        )
        tk.Button(control_frame, textvariable=self.autoplay_btn_text, command=self.toggle_autoplay).grid(
            row=3, column=4, pady=10
        )

        self.prev_replay_btn = tk.Button(
            control_frame,
            text="Previous Move",
            command=self.replay_previous_move,
            state=tk.DISABLED,
        )
        self.prev_replay_btn.grid(row=4, column=1, pady=5)

        self.next_replay_btn = tk.Button(
            control_frame,
            text="Next Move",
            command=self.replay_next_move,
            state=tk.DISABLED,
        )
        self.next_replay_btn.grid(row=4, column=2, pady=5)

        self.complete_replay_btn = tk.Button(
            control_frame,
            text="Complete",
            command=self.replay_complete,
            state=tk.DISABLED,
        )
        self.complete_replay_btn.grid(row=4, column=3, pady=5)

        tk.Label(control_frame, textvariable=self.replay_status_text).grid(
            row=5,
            column=0,
            columnspan=5,
            sticky=tk.W,
            pady=5,
        )

        # --- Canvas Setup ---
        self.cell_size = 50

        # Wire up controller callbacks before starting the first game so that
        # the on_game_over handler is in place even for instant-over boards.
        self.controller = game_engine.SolitaireGameController()
        self.controller.on_move = self._on_move
        self.controller.on_game_over = self._on_game_over
        self.manual_mode = game_engine.ManualGameMode(self.controller)
        self.automated_mode = game_engine.AutomatedGameMode(self.controller)

        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Draw the initial board
        self.new_game()

    # ------------------------------------------------------------------
    # Game lifecycle (thin wrappers – no logic here)
    # ------------------------------------------------------------------

    def new_game(self):
        """Read UI controls and ask the controller to start a fresh game."""
        self.stop_autoplay()
        self._clear_replay_session()

        try:
            board_size = int(self.size_var.get())
        except ValueError:
            board_size = 7

        board_type = self.type_var.get()
        mode_name = self.mode_var.get()

        self.controller.start_new_game(board_type=board_type, board_size=board_size, mode_name=mode_name)
        self._redraw_board()

        if mode_name == "Automated":
            self.start_autoplay()

    def randomize_board(self):
        """Randomize the current board state and redraw."""
        if self.replay_session is not None:
            messagebox.showwarning("Replay Active", "Start a new game to exit replay mode first.")
            return

        self.stop_autoplay()
        self.controller.randomize_board_state()
        self._redraw_board()

    def toggle_recording(self):
        if self.replay_session is not None:
            messagebox.showwarning("Replay Active", "Start a new game to exit replay mode first.")
            return

        if self.controller.is_recording():
            self._stop_and_save_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        self.controller.start_recording(mode_name=self.mode_var.get())
        self.record_btn_text.set("Stop & Save Recording")

    def _stop_and_save_recording(self):
        recording = self.controller.stop_recording()
        self.record_btn_text.set("Start Recording")

        if recording is None:
            messagebox.showwarning("Recording", "No recording data is available to save.")
            return

        file_path = self._ask_recording_save_path("Save Game Recording")
        if not file_path:
            return

        try:
            self.controller.save_recording(file_path)
        except Exception as ex:
            messagebox.showerror("Recording Error", f"Failed to save recording:\n{ex}")
            return

        messagebox.showinfo("Recording Saved", f"Recording saved to:\n{file_path}")

    def _ask_recording_save_path(self, title):
        return filedialog.asksaveasfilename(
            title=title,
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("Text Files", "*.txt"), ("All Files", "*.*")],
        )

    def _auto_finalize_recording_after_game_over(self):
        recording = self.controller.stop_recording()
        self.record_btn_text.set("Start Recording")
        if recording is None:
            return

        file_path = self._ask_recording_save_path("Save Completed Game Recording")
        if not file_path:
            messagebox.showwarning(
                "Recording",
                "Recording was finalized but not saved because no file path was selected.",
            )
            return

        try:
            self.controller.save_recording(file_path)
            messagebox.showinfo("Recording Saved", f"Recording saved to:\n{file_path}")
        except Exception as ex:
            messagebox.showerror("Recording Error", f"Failed to save recording:\n{ex}")

    def replay_recording_from_file(self):
        """Load a recording file and initialize step-by-step replay."""
        if self.controller.is_recording():
            messagebox.showwarning(
                "Replay Blocked",
                "Stop and save the active recording before replaying another session.",
            )
            return

        self.stop_autoplay()

        file_path = filedialog.askopenfilename(
            title="Open Game Recording",
            filetypes=[("JSON Files", "*.json"), ("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        try:
            self.replay_session = self.controller.create_replay_session_from_file(file_path)
            self.replay_session.apply_current_to_controller(self.controller)
        except Exception as ex:
            messagebox.showerror("Replay Error", f"Failed to replay recording:\n{ex}")
            return

        self._redraw_board()
        self._update_replay_controls()

        mode_name = self.replay_session.mode_name
        if mode_name in ("Manual", "Automated"):
            self.mode_var.set(mode_name)

        messagebox.showinfo(
            "Replay Loaded",
            "Replay is loaded at the initial board state."
            "\nUse Next Move / Previous Move / Complete to navigate.",
        )

    def replay_next_move(self):
        if self.replay_session is None:
            messagebox.showwarning("Replay", "Load a replay file first.")
            return

        if self.replay_session.can_step_next():
            self.replay_session.step_next()

        self.replay_session.apply_current_to_controller(self.controller)
        self._redraw_board()
        self._update_replay_controls()

    def replay_previous_move(self):
        if self.replay_session is None:
            messagebox.showwarning("Replay", "Load a replay file first.")
            return

        if self.replay_session.can_step_previous():
            self.replay_session.step_previous()

        self.replay_session.apply_current_to_controller(self.controller)
        self._redraw_board()
        self._update_replay_controls()

    def replay_complete(self):
        if self.replay_session is None:
            messagebox.showwarning("Replay", "Load a replay file first.")
            return

        self.replay_session.jump_to_complete()
        self.replay_session.apply_current_to_controller(self.controller)
        self._redraw_board()
        self._update_replay_controls()
        messagebox.showinfo("Replay Complete", "Replay Complete")

    def _clear_replay_session(self):
        self.replay_session = None
        self._update_replay_controls()

    def _update_replay_controls(self):
        if self.replay_session is None:
            self.prev_replay_btn.config(state=tk.DISABLED)
            self.next_replay_btn.config(state=tk.DISABLED)
            self.complete_replay_btn.config(state=tk.DISABLED)
            self.replay_status_text.set("Replay: not loaded")
            return

        self.prev_replay_btn.config(
            state=tk.NORMAL if self.replay_session.can_step_previous() else tk.DISABLED
        )
        self.next_replay_btn.config(
            state=tk.NORMAL if self.replay_session.can_step_next() else tk.DISABLED
        )
        self.complete_replay_btn.config(state=tk.NORMAL)

        snapshot = self.replay_session.current_snapshot()
        self.replay_status_text.set(
            f"Replay step {self.replay_session.position + 1}/{self.replay_session.total_steps}"
            f" ({snapshot.get('event_type')})"
        )

    # ------------------------------------------------------------------
    # Controller event callbacks
    # ------------------------------------------------------------------

    def _on_move(self, start_pos, end_pos):
        """Called by the controller after every successful move."""
        self._redraw_board()

    def _on_game_over(self, score_rating):
        """Called by the controller exactly once when no moves remain."""
        self.stop_autoplay()

        if self.controller.is_recording():
            self._auto_finalize_recording_after_game_over()

        messagebox.showinfo(
            "Game Over",
            f"No more valid moves are possible.\nRating: {score_rating}",
        )

    def start_autoplay(self):
        if self.replay_session is not None:
            messagebox.showwarning("Replay Active", "Start a new game to exit replay mode first.")
            return

        if self.controller.is_game_over():
            return
        if self.autoplay_running:
            return

        self.autoplay_running = True
        self.autoplay_btn_text.set("Stop Autoplay")
        self._schedule_auto_move()

    def stop_autoplay(self):
        if self._auto_job is not None:
            self.root.after_cancel(self._auto_job)
            self._auto_job = None
        self.autoplay_running = False
        self.autoplay_btn_text.set("Start Autoplay")

    def toggle_autoplay(self):
        if self.autoplay_running:
            self.stop_autoplay()
        else:
            self.start_autoplay()

    # ------------------------------------------------------------------
    # Canvas interaction
    # ------------------------------------------------------------------

    def on_canvas_click(self, event):
        """Translate a raw canvas click into a controller call."""
        if self.replay_session is not None:
            return

        if self.autoplay_running:
            return

        item = self.canvas.find_withtag("current")

        if not item:
            # Clicked empty background – clear selection and redraw
            self.controller.clear_selection()
            self._redraw_board()
            return

        tags = self.canvas.gettags(item[0])
        clicked_type, r, c = None, -1, -1

        for tag in tags:
            if tag.startswith("peg_") or tag.startswith("hole_"):
                parts = tag.split("_")
                clicked_type = parts[0]
                r = int(parts[1])
                c = int(parts[2])
                break

        action = self.manual_mode.make_move(clicked_type, r, c)

        # Redraw on any action that changes visible state (selection or move).
        # "moved" redraws via _on_move callback; handle the remaining cases here.
        if action in ("selected", "invalid"):
            self._redraw_board()

    def _schedule_auto_move(self):
        if self._auto_job is not None:
            self.root.after_cancel(self._auto_job)
            self._auto_job = None

        def _step():
            self._auto_job = None
            if not self.autoplay_running:
                return
            if self.controller.is_game_over():
                self.stop_autoplay()
                return

            moved = self.automated_mode.make_move()
            if moved and not self.controller.is_game_over() and self.autoplay_running:
                self._auto_job = self.root.after(200, _step)
            elif self.controller.is_game_over():
                self.stop_autoplay()

        self._auto_job = self.root.after(200, _step)

    # ------------------------------------------------------------------
    # Rendering helpers (pure presentation – reads board, draws pixels)
    # ------------------------------------------------------------------

    def _redraw_board(self):
        self.canvas.delete("all")
        self._render_board()

    def _cell_pixel(self, r, c, radius, board_type, cell_size):
        """Return (pixel_x, pixel_y) for a cell using a given cell_size."""
        dc = c - radius
        dr = r - radius
        if board_type == game_engine.BoardType.HEXAGON:
            px = cell_size * math.sqrt(3) * (dc + dr / 2.0)
            py = cell_size * 1.5 * dr
        else:
            px = dc * cell_size
            py = dr * cell_size
        return px, py

    def _render_board(self):
        board_layout = self.controller.board_layout
        board_type = self.controller.game.board_type

        self.root.update_idletasks()
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        if canvas_w < 10:
            canvas_w, canvas_h = 600, 500

        radius = len(board_layout) // 2

        # --- Pass 1: compute bounding box with unit cell_size=1 ---
        xs, ys = [], []
        for r in range(len(board_layout)):
            for c in range(len(board_layout[0])):
                if board_layout[r][c] == game_engine.CellState.INVALID:
                    continue
                px, py = self._cell_pixel(r, c, radius, board_type, 1.0)
                xs.append(px)
                ys.append(py)

        if not xs:
            return

        half_ext = 1.0 if board_type == game_engine.BoardType.HEXAGON else 0.5
        padding = 20
        span_x = (max(xs) - min(xs)) + 2 * half_ext
        span_y = (max(ys) - min(ys)) + 2 * half_ext

        scale = min(
            (canvas_w - padding * 2) / span_x,
            (canvas_h - padding * 2) / span_y,
        )
        scale = min(scale, self.cell_size)

        peg_radius = scale * 0.4
        center_x = canvas_w / 2
        center_y = canvas_h / 2

        # --- Pass 2: draw ---
        for r in range(len(board_layout)):
            for c in range(len(board_layout[0])):
                state = board_layout[r][c]
                if state == game_engine.CellState.INVALID:
                    continue

                ux, uy = self._cell_pixel(r, c, radius, board_type, scale)
                pixel_x = center_x + ux
                pixel_y = center_y + uy

                # Draw tile background
                if board_type == game_engine.BoardType.HEXAGON:
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
                        outline="black", fill="burlywood",
                    )

                # Draw peg or hole
                if state == game_engine.CellState.PEG:
                    self.canvas.create_oval(
                        pixel_x - peg_radius, pixel_y - peg_radius,
                        pixel_x + peg_radius, pixel_y + peg_radius,
                        outline="black", fill="saddlebrown",
                        tags=f"peg_{r}_{c}",
                    )
                elif state == game_engine.CellState.HOLE:
                    self.canvas.create_oval(
                        pixel_x - peg_radius, pixel_y - peg_radius,
                        pixel_x + peg_radius, pixel_y + peg_radius,
                        outline="saddlebrown", fill="black",
                        tags=f"hole_{r}_{c}",
                    )