from enum import Enum
from typing import Callable, Optional
#chatgpt 5.3 - implemented the game engine and controller logic for a peg solitaire game, including board generation for different types, move validation, game over detection, and scoring. The code is structured to separate game rules from state management and UI interactions, making it easy to test and extend.

class CellState(Enum):
    PEG = 1
    HOLE = 0
    INVALID = -1


class BoardType:
    ENGLISH = "English"
    HEXAGON = "Hexagon"
    DIAMOND = "Diamond"


class BoardGenerator:
    @staticmethod
    def generate_english_board(size):
        if size % 2 == 0:
            print("Warning: Even sizes won't have a perfect center.")

        board = []
        corner_size = size // 3
        center = size // 2

        for r in range(size):
            row = []
            for c in range(size):
                in_top_left = (r < corner_size) and (c < corner_size)
                in_top_right = (r < corner_size) and (c >= size - corner_size)
                in_bottom_left = (r >= size - corner_size) and (c < corner_size)
                in_bottom_right = (r >= size - corner_size) and (c >= size - corner_size)

                if in_top_left or in_top_right or in_bottom_left or in_bottom_right:
                    row.append(CellState.INVALID)
                elif r == center and c == center:
                    row.append(CellState.HOLE)
                else:
                    row.append(CellState.PEG)

            board.append(row)

        return board

    @staticmethod
    def generate_diamond_board(size):
        if size % 2 == 0:
            print("Warning: Even sizes won't have a perfect center.")

        board = []
        center = size // 2

        for r in range(size):
            row = []
            for c in range(size):
                distance_from_center = abs(r - center) + abs(c - center)

                if distance_from_center > center:
                    row.append(CellState.INVALID)
                elif r == center and c == center:
                    row.append(CellState.HOLE)
                else:
                    row.append(CellState.PEG)

            board.append(row)

        return board

    @staticmethod
    def generate_hexagon_board(size):
        if size % 2 == 0:
            print("Warning: Even sizes won't have a perfect center.")

        board = []
        radius = size // 2

        for r in range(size):
            row = []
            for c in range(size):
                dq = c - radius
                dr = r - radius

                if abs(dq) <= radius and abs(dr) <= radius and abs(dq + dr) <= radius:
                    if dq == 0 and dr == 0:
                        row.append(CellState.HOLE)
                    else:
                        row.append(CellState.PEG)
                else:
                    row.append(CellState.INVALID)

            board.append(row)

        return board

    @staticmethod
    def generate_board_layout(board_type, size):
        if board_type == BoardType.ENGLISH:
            return BoardGenerator.generate_english_board(size)
        if board_type == BoardType.DIAMOND:
            return BoardGenerator.generate_diamond_board(size)
        if board_type == BoardType.HEXAGON:
            return BoardGenerator.generate_hexagon_board(size)
        raise ValueError("Unknown board type") #just in case player bypasses radio buttons


class SolitaireRules:
    """Stateless game-rules engine.

    All methods are pure: they take board data as arguments and return
    results without modifying any instance state.  This makes the rules
    easy to test in isolation and straightforward to swap out for a
    variant ruleset (e.g. diagonal moves, toroidal wrapping, etc.).
    """

    # ------------------------------------------------------------------
    # Move geometry
    # ------------------------------------------------------------------

    def get_jump_directions(self, board_type):
        """Return valid jump offsets (delta_row, delta_col) for the board type."""
        directions = [(0, 2), (0, -2), (2, 0), (-2, 0)]
        if board_type in (BoardType.ENGLISH, BoardType.DIAMOND):
            directions.extend([(2, 2), (2, -2), (-2, 2), (-2, -2)])
        if board_type == BoardType.HEXAGON:
            directions.extend([(2, -2), (-2, 2)])
        return directions

    # ------------------------------------------------------------------
    # Move enumeration
    # ------------------------------------------------------------------

    def get_all_valid_moves(self, board_layout, board_type):
        """Return all legal moves as ((start_row, start_col), (end_row, end_col))."""
        moves = []
        size = len(board_layout)

        for row in range(size):
            for col in range(size):
                if board_layout[row][col] != CellState.PEG:
                    continue

                for delta_row, delta_col in self.get_jump_directions(board_type):
                    end_row = row + delta_row
                    end_col = col + delta_col
                    mid_row = row + delta_row // 2
                    mid_col = col + delta_col // 2

                    if 0 <= end_row < size and 0 <= end_col < size:
                        if board_layout[end_row][end_col] == CellState.HOLE:
                            if board_layout[mid_row][mid_col] == CellState.PEG:
                                moves.append(((row, col), (end_row, end_col)))

        return moves

    # ------------------------------------------------------------------
    # Move execution
    # ------------------------------------------------------------------

    def execute_move(self, board_layout, start_pos, end_pos):
        """Apply one jump move to the board in-place and return the board."""
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        mid_row = (start_row + end_row) // 2
        mid_col = (start_col + end_col) // 2

        board_layout[start_row][start_col] = CellState.HOLE
        board_layout[mid_row][mid_col] = CellState.HOLE
        board_layout[end_row][end_col] = CellState.PEG

        return board_layout

    # ------------------------------------------------------------------
    # End-of-game detection
    # ------------------------------------------------------------------

    def check_game_over(self, board_layout, board_type):
        """Return True when no valid moves remain."""
        return len(self.get_all_valid_moves(board_layout, board_type)) == 0

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def get_score_rating(self, board_layout):
        """Return a text rating based on the number of pegs remaining."""
        peg_count = sum(row.count(CellState.PEG) for row in board_layout)
        if peg_count == 0: 
            return "You win! Congratulations!"
        if peg_count == 1:
            return "Outstanding (1 marble left)"
        if peg_count == 2:
            return "Very Good (2 marbles left)"
        if peg_count == 3:
            return "Good (3 marbles left)"
        return f"Average ({peg_count} marbles left)"


class SolitaireGame:
    """Encapsulates peg solitaire state and game rules.

    Delegates all rule calculations to a SolitaireRules instance so that
    the rules can be replaced or extended without touching this class.
    """

    def __init__(self, board_type=BoardType.ENGLISH, board_size=7, rules=None):
        self.board_type = board_type
        self.board_size = board_size
        self.rules = rules if rules is not None else SolitaireRules()
        self.board_layout = BoardGenerator.generate_board_layout(self.board_type, self.board_size)

    def start_new_game(self, board_type=None, board_size=None):
        if board_type is not None:
            self.board_type = board_type
        if board_size is not None:
            self.board_size = board_size
        self.board_layout = BoardGenerator.generate_board_layout(self.board_type, self.board_size)
        return self.board_layout

    def get_valid_moves(self):
        return self.rules.get_all_valid_moves(self.board_layout, self.board_type)

    def is_valid_move(self, start_pos, end_pos):
        return (start_pos, end_pos) in self.get_valid_moves()

    def make_move(self, start_pos, end_pos):
        if not self.is_valid_move(start_pos, end_pos):
            return False
        self.rules.execute_move(self.board_layout, start_pos, end_pos)
        return True

    def is_game_over(self):
        return self.rules.check_game_over(self.board_layout, self.board_type)

    def get_score_rating(self):
        return self.rules.get_score_rating(self.board_layout)


class SolitaireGameController:
    """Coordinates game interactions independently of any UI framework.

    The controller owns all game-state transitions and raises events that the
    UI layer can subscribe to via on_move and on_game_over callbacks.  This
    keeps every piece of game logic out of the GUI class.
    """

    def __init__(self, game=None):
        self.game = game if game is not None else SolitaireGame()
        self.selected_peg = None
        self._game_over_fired = False

        # Callbacks the UI can register to react to game events.
        # on_move(start_pos, end_pos)  - called after a successful move
        # on_game_over(score_rating)   - called when no moves remain
        self.on_move: Optional[Callable[[tuple[int, int], tuple[int, int]], None]] = None
        self.on_game_over: Optional[Callable[[str], None]] = None

    # ------------------------------------------------------------------
    # Board access helpers
    # ------------------------------------------------------------------

    @property
    def board_layout(self):
        return self.game.board_layout

    @board_layout.setter
    def board_layout(self, value):
        self.game.board_layout = value

    # ------------------------------------------------------------------
    # Game lifecycle
    # ------------------------------------------------------------------

    def start_new_game(self, board_type=None, board_size=None):
        """Reset the board and clear transient state."""
        self.selected_peg = None
        self._game_over_fired = False
        return self.game.start_new_game(board_type=board_type, board_size=board_size)

    def clear_selection(self):
        self.selected_peg = None

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    def is_game_over(self):
        return self.game.is_game_over()

    def get_score_rating(self):
        return self.game.get_score_rating()

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    def handle_cell_click(self, clicked_type, row, col):
        """Handle a click on a parsed board cell and return an action string.

        Returns
        -------
        "locked"   - the game is already over; input ignored
        "selected" - a peg was chosen as the move source
        "moved"    - a valid jump was executed
        "invalid"  - the attempted jump was illegal; selection cleared
        "ignored"  - click had no meaningful effect
        """
        if self.is_game_over():
            return "locked"

        if clicked_type == "peg":
            self.selected_peg = (row, col)
            return "selected"

        if clicked_type == "hole" and self.selected_peg is not None:
            start_pos = self.selected_peg
            end_pos = (row, col)

            if self.game.make_move(start_pos, end_pos):
                self.selected_peg = None
                self._notify_move(start_pos, end_pos)
                self._check_and_notify_game_over()
                return "moved"

            self.selected_peg = None
            return "invalid"

        return "ignored"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _notify_move(self, start_pos, end_pos):
        """Fire the on_move callback if one has been registered."""
        if callable(self.on_move):
            self.on_move(start_pos, end_pos)

    def _check_and_notify_game_over(self):
        """Fire on_game_over exactly once when no valid moves remain."""
        if not self._game_over_fired and self.is_game_over():
            self._game_over_fired = True
            if callable(self.on_game_over):
                self.on_game_over(self.get_score_rating())