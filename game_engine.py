from enum import Enum
from typing import Any, Callable, Optional
import json
import random
from abc import ABC, abstractmethod
#chatgpt 5.3 - implemented the game engine and controller logic for a peg solitaire game, including board generation for different types, move validation, game over detection, and scoring. The code is structured to separate game rules from state management and UI interactions, making it easy to test and extend.

class CellState(Enum):
    PEG = 1
    HOLE = 0
    INVALID = -1


class BoardType:
    ENGLISH = "English"
    HEXAGON = "Hexagon"
    DIAMOND = "Diamond"


RECORDING_FILE_VERSION = 1


def serialize_board_layout(board_layout):
    """Serialize CellState board to primitive values for JSON storage."""
    return [[cell.value for cell in row] for row in board_layout]


def deserialize_board_layout(serialized_board):
    """Deserialize primitive board values back into CellState values."""
    value_map = {state.value: state for state in CellState}
    board_layout = []

    for row in serialized_board:
        board_row = []
        for cell_value in row:
            if cell_value not in value_map:
                raise ValueError(f"Unknown cell value in recording: {cell_value}")
            board_row.append(value_map[cell_value])
        board_layout.append(board_row)

    return board_layout


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

    def randomize_board_state(self, peg_probability=0.5, rng=None):
        """Randomize PEG/HOLE on playable cells while preserving INVALID cells."""
        if rng is None:
            rng = random

        playable_cells = []
        for row_idx, row in enumerate(self.board_layout):
            for col_idx, cell in enumerate(row):
                if cell == CellState.INVALID:
                    continue

                playable_cells.append((row_idx, col_idx))
                self.board_layout[row_idx][col_idx] = (
                    CellState.PEG if rng.random() < peg_probability else CellState.HOLE
                )

        if not playable_cells:
            return self.board_layout

        peg_count = sum(
            1
            for row_idx, col_idx in playable_cells
            if self.board_layout[row_idx][col_idx] == CellState.PEG
        )

        # Keep the randomized state playable and scoreable.
        if peg_count == 0:
            row_idx, col_idx = playable_cells[0]
            self.board_layout[row_idx][col_idx] = CellState.PEG
        elif peg_count == len(playable_cells):
            row_idx, col_idx = playable_cells[0]
            self.board_layout[row_idx][col_idx] = CellState.HOLE

        return self.board_layout


class GameRecorder:
    """Capture a complete game session and persist it as JSON."""

    def __init__(self):
        self.current_recording: Optional[dict[str, Any]] = None
        self._recording_active = False
        self._game_over_recorded = False

    @property
    def is_recording(self):
        return self._recording_active

    def start(self, board_type, board_size, mode_name, board_layout):
        self.current_recording = {
            "version": RECORDING_FILE_VERSION,
            "mode_name": mode_name,
            "events": [],
        }
        self._recording_active = True
        self._game_over_recorded = False
        self.record_start_new_game(
            board_type=board_type,
            board_size=board_size,
            mode_name=mode_name,
            board_layout=board_layout,
        )
        return self.current_recording

    def stop(self):
        self._recording_active = False
        return self.current_recording

    def _append_event(self, event_type, **event_data):
        if not self._recording_active or self.current_recording is None:
            return

        event = {
            "index": len(self.current_recording["events"]),
            "type": event_type,
        }
        event.update(event_data)
        self.current_recording["events"].append(event)

    def record_start_new_game(self, board_type, board_size, mode_name, board_layout):
        self._game_over_recorded = False
        replacement_event = {
            "index": 0,
            "type": "start_new_game",
            "board_type": board_type,
            "board_size": board_size,
            "mode_name": mode_name,
            "board_after": serialize_board_layout(board_layout),
        }

        # If recording started and the user immediately begins a fresh game,
        # replace the seed state so the first entry reflects that new setup.
        if self._recording_active and self.current_recording is not None:
            events = self.current_recording["events"]
            if len(events) == 1 and events[0].get("type") == "start_new_game":
                events[0] = replacement_event
                return

        self._append_event(
            "start_new_game",
            board_type=board_type,
            board_size=board_size,
            mode_name=mode_name,
            board_after=serialize_board_layout(board_layout),
        )

    def record_move(self, start_pos, end_pos, move_source, board_layout):
        self._append_event(
            "move",
            start_pos=list(start_pos),
            end_pos=list(end_pos),
            move_source=move_source,
            board_after=serialize_board_layout(board_layout),
        )

    def record_randomize(self, peg_probability, seed, board_layout):
        self._append_event(
            "randomize",
            peg_probability=peg_probability,
            seed=seed,
            board_after=serialize_board_layout(board_layout),
        )

    def record_game_over(self, score_rating):
        if self._game_over_recorded:
            return
        self._append_event("game_over", score_rating=score_rating)
        self._game_over_recorded = True

    def save_to_file(self, file_path):
        if self.current_recording is None:
            raise ValueError("No recording data is available to save.")

        with open(file_path, "w", encoding="utf-8") as output_file:
            json.dump(self.current_recording, output_file, indent=2)

    @staticmethod
    def load_from_file(file_path):
        with open(file_path, "r", encoding="utf-8") as input_file:
            recording_data = json.load(input_file)

        if not isinstance(recording_data, dict):
            raise ValueError("Recording file has an invalid format.")
        if recording_data.get("version") != RECORDING_FILE_VERSION:
            raise ValueError("Unsupported recording file version.")
        if not isinstance(recording_data.get("events"), list):
            raise ValueError("Recording file is missing the events array.")

        return recording_data


class GameReplayer:
    """Replay a previously recorded session onto a controller."""

    @staticmethod
    def replay(recording_data, controller):
        events = recording_data.get("events", [])
        if not events:
            raise ValueError("Recording has no events to replay.")

        replayed_moves = 0
        controller._is_replaying = True

        try:
            for event in events:
                event_type = event.get("type")

                if event_type == "start_new_game":
                    board_type = event.get("board_type", controller.game.board_type)
                    board_size = event.get("board_size", controller.game.board_size)

                    controller.start_new_game(board_type=board_type, board_size=board_size)

                    if "board_after" in event:
                        controller.board_layout = deserialize_board_layout(event["board_after"])
                        controller.clear_selection()
                        controller._game_over_fired = False
                        controller._check_and_notify_game_over()

                elif event_type == "move":
                    start_pos = tuple(event["start_pos"])
                    end_pos = tuple(event["end_pos"])

                    if not controller.perform_move(start_pos, end_pos, move_source="replay"):
                        raise ValueError(
                            f"Replay failed at move event #{event.get('index', '?')}: "
                            f"{start_pos} -> {end_pos}"
                        )

                    replayed_moves += 1
                    GameReplayer._assert_expected_board(controller.board_layout, event)

                elif event_type == "randomize":
                    if "board_after" not in event:
                        controller.randomize_board_state(
                            peg_probability=event.get("peg_probability", 0.5),
                            seed=event.get("seed"),
                        )
                    else:
                        controller.board_layout = deserialize_board_layout(event["board_after"])
                        controller.clear_selection()
                        controller._game_over_fired = False
                        controller._check_and_notify_game_over()

                elif event_type == "game_over":
                    expected_score = event.get("score_rating")
                    if expected_score is not None and controller.is_game_over():
                        actual_score = controller.get_score_rating()
                        if actual_score != expected_score:
                            raise ValueError(
                                f"Replay score mismatch. Expected '{expected_score}', got '{actual_score}'."
                            )

                else:
                    raise ValueError(f"Unsupported event type in recording: {event_type}")

        finally:
            controller._is_replaying = False

        return {
            "replayed_moves": replayed_moves,
            "is_game_over": controller.is_game_over(),
            "score_rating": controller.get_score_rating(),
            "mode_name": recording_data.get("mode_name"),
        }

    @staticmethod
    def replay_from_file(file_path, controller):
        recording_data = GameRecorder.load_from_file(file_path)
        return GameReplayer.replay(recording_data, controller)

    @staticmethod
    def _assert_expected_board(board_layout, event):
        expected_board = event.get("board_after")
        if expected_board is None:
            return

        actual_board = serialize_board_layout(board_layout)
        if actual_board != expected_board:
            raise ValueError(
                f"Replay diverged at event #{event.get('index', '?')} ({event.get('type')})."
            )


class ReplaySession:
    """Step-based replay cursor over recorded board snapshots."""

    def __init__(self, recording_data):
        if not isinstance(recording_data, dict):
            raise ValueError("Replay data must be a dictionary.")

        self.recording_data = recording_data
        self.mode_name = recording_data.get("mode_name")
        self._timeline = self._build_timeline(recording_data.get("events", []))
        if not self._timeline:
            raise ValueError("Recording does not contain replayable board states.")

        self._position = 0

    @property
    def position(self):
        return self._position

    @property
    def total_steps(self):
        return len(self._timeline)

    def can_step_next(self):
        return self._position < self.total_steps - 1

    def can_step_previous(self):
        return self._position > 0

    def current_snapshot(self):
        return self._timeline[self._position]

    def step_next(self):
        if self.can_step_next():
            self._position += 1
        return self.current_snapshot()

    def step_previous(self):
        if self.can_step_previous():
            self._position -= 1
        return self.current_snapshot()

    def jump_to_complete(self):
        self._position = self.total_steps - 1
        return self.current_snapshot()

    def apply_current_to_controller(self, controller):
        snapshot = self.current_snapshot()
        controller.set_board_state_for_replay(
            board_layout=deserialize_board_layout(snapshot["board_after"]),
            board_type=snapshot.get("board_type"),
            board_size=snapshot.get("board_size"),
        )
        return snapshot

    @staticmethod
    def from_file(file_path):
        recording_data = GameRecorder.load_from_file(file_path)
        return ReplaySession(recording_data)

    @staticmethod
    def _build_timeline(events):
        if not isinstance(events, list):
            raise ValueError("Recording events must be a list.")

        timeline = []
        current_board_type = None
        current_board_size = None

        for event in events:
            event_type = event.get("type")
            board_after = event.get("board_after")

            if event_type == "start_new_game":
                current_board_type = event.get("board_type")
                current_board_size = event.get("board_size")

            if board_after is None:
                continue

            timeline.append(
                {
                    "event_index": event.get("index"),
                    "event_type": event_type,
                    "board_type": event.get("board_type", current_board_type),
                    "board_size": event.get("board_size", current_board_size),
                    "board_after": board_after,
                }
            )

        return timeline


class SolitaireGameController:
    """Chatgpted class that manages game state and interactions between the SolitaireGame and the UI.
    """

    def __init__(self, game=None):
        self.game = game if game is not None else SolitaireGame()
        self.recorder = GameRecorder()
        self.selected_peg = None
        self._game_over_fired = False
        self._is_replaying = False

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

    def start_new_game(self, board_type=None, board_size=None, mode_name=None):
        """Reset the board and clear transient state."""
        self.selected_peg = None
        self._game_over_fired = False
        board_layout = self.game.start_new_game(board_type=board_type, board_size=board_size)

        if self.recorder.is_recording and not self._is_replaying:
            self.recorder.record_start_new_game(
                board_type=self.game.board_type,
                board_size=self.game.board_size,
                mode_name=mode_name,
                board_layout=board_layout,
            )

        return board_layout

    def clear_selection(self):
        self.selected_peg = None

    def is_recording(self):
        return self.recorder.is_recording

    def start_recording(self, mode_name="Manual"):
        return self.recorder.start(
            board_type=self.game.board_type,
            board_size=self.game.board_size,
            mode_name=mode_name,
            board_layout=self.game.board_layout,
        )

    def stop_recording(self):
        if self.recorder.is_recording and self.is_game_over():
            self.recorder.record_game_over(self.get_score_rating())
        return self.recorder.stop()

    def save_recording(self, file_path):
        self.recorder.save_to_file(file_path)

    def replay_from_file(self, file_path):
        return GameReplayer.replay_from_file(file_path, self)

    def create_replay_session_from_file(self, file_path):
        return ReplaySession.from_file(file_path)

    def set_board_state_for_replay(self, board_layout, board_type=None, board_size=None):
        """Set controller state from replay data without recording new events."""
        self._is_replaying = True
        try:
            if board_type is not None:
                self.game.board_type = board_type
            if board_size is not None:
                self.game.board_size = board_size

            self.board_layout = board_layout
            self.selected_peg = None
            self._game_over_fired = self.is_game_over()
        finally:
            self._is_replaying = False

    def randomize_board_state(self, peg_probability=0.5, seed=None):
        """Randomize current board state for manual play experimentation."""
        rng = random.Random(seed) if seed is not None else random
        self.game.randomize_board_state(peg_probability=peg_probability, rng=rng)
        self.selected_peg = None
        self._game_over_fired = False

        if self.recorder.is_recording and not self._is_replaying:
            self.recorder.record_randomize(
                peg_probability=peg_probability,
                seed=seed,
                board_layout=self.game.board_layout,
            )

        self._check_and_notify_game_over()
        return self.game.board_layout

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

            if self.perform_move(start_pos, end_pos, move_source="manual"):
                self.selected_peg = None
                return "moved"

            self.selected_peg = None
            return "invalid"

        return "ignored"

    def perform_move(self, start_pos, end_pos, move_source="manual"):
        """Attempt one move and emit callbacks when successful."""
        if not self.game.make_move(start_pos, end_pos):
            return False

        if self.recorder.is_recording and not self._is_replaying:
            self.recorder.record_move(
                start_pos=start_pos,
                end_pos=end_pos,
                move_source=move_source,
                board_layout=self.game.board_layout,
            )

        self._notify_move(start_pos, end_pos)
        self._check_and_notify_game_over()
        return True

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

            if self.recorder.is_recording and not self._is_replaying:
                self.recorder.record_game_over(self.get_score_rating())

            if callable(self.on_game_over):
                self.on_game_over(self.get_score_rating())

#chatgpted class
class GameMode(ABC):
    """Base class for Manual and Automated modes.

    Shared responsibilities:
    - start a new game
    - make moves
    - detect game-over
    """

    def __init__(self, controller):
        self.controller = controller

    def start_new_game(self, board_type=None, board_size=None):
        mode_name = self.__class__.__name__.replace("GameMode", "")
        return self.controller.start_new_game(
            board_type=board_type,
            board_size=board_size,
            mode_name=mode_name,
        )

    def is_game_over(self):
        return self.controller.is_game_over()

    @abstractmethod
    def make_move(self, *args, **kwargs) -> object:
        """Mode-specific move execution."""


class ManualGameMode(GameMode):
    """Manual mode: user selects source peg and destination hole."""

    def make_move(self, clicked_type, row, col) -> object:
        return self.controller.handle_cell_click(clicked_type, row, col)


class AutomatedGameMode(GameMode):
    """Automated mode: computer performs random valid moves."""

    def make_move(self) -> object:
        """Perform one random valid move. Returns True if a move was made."""
        moves = self.controller.game.get_valid_moves()
        if not moves:
            self.controller._check_and_notify_game_over()
            return False

        start_pos, end_pos = random.choice(moves)
        return self.controller.perform_move(start_pos, end_pos, move_source="automated")

    def play_until_game_over(self, max_steps=10000):
        """Play random legal moves until no moves remain."""
        steps = 0
        while steps < max_steps and not self.controller.is_game_over():
            if not self.make_move():
                break
            steps += 1
        return steps