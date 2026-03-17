import unittest
import game_engine

#chatgpt codex 5.3 - generated unit tests for the game engine and controller logic, covering board generation, move validation, game over detection, and scoring. Tests verify correct behavior for different board types and sizes, valid/invalid moves, and game over conditions.
class TestBoardGeneration(unittest.TestCase):
    """AC 1.1 / 1.2: choose board size and type."""

    def test_generate_board_layout_english(self):
        size = 7
        board = game_engine.BoardGenerator.generate_board_layout(game_engine.BoardType.ENGLISH, size)

        self.assertEqual(len(board), size)
        self.assertEqual(len(board[0]), size)
        self.assertEqual(board[size // 2][size // 2], game_engine.CellState.HOLE)

    def test_generate_board_layout_hexagon(self):
        size = 7
        board = game_engine.BoardGenerator.generate_board_layout(game_engine.BoardType.HEXAGON, size)

        self.assertEqual(len(board), size)
        self.assertEqual(len(board[0]), size)
        self.assertEqual(board[size // 2][size // 2], game_engine.CellState.HOLE)

    def test_generate_board_layout_diamond(self):
        size = 7
        board = game_engine.BoardGenerator.generate_board_layout(game_engine.BoardType.DIAMOND, size)

        self.assertEqual(len(board), size)
        self.assertEqual(len(board[0]), size)
        self.assertEqual(board[size // 2][size // 2], game_engine.CellState.HOLE)

    def test_generate_board_layout_unknown_type_raises(self):
        with self.assertRaises(ValueError):
            game_engine.BoardGenerator.generate_board_layout("UnknownType", 7)

    def test_solitaire_game_init_uses_size_and_type(self):
        game = game_engine.SolitaireGame(board_type=game_engine.BoardType.DIAMOND, board_size=9)

        self.assertEqual(game.board_type, game_engine.BoardType.DIAMOND)
        self.assertEqual(game.board_size, 9)
        self.assertEqual(len(game.board_layout), 9)
        self.assertEqual(len(game.board_layout[0]), 9)

    def test_small_size_still_generates_board(self):
        # "invalid values" note: code currently does not raise for tiny sizes;
        # verify it still builds a board object.
        game = game_engine.SolitaireGame(board_type=game_engine.BoardType.ENGLISH, board_size=1)
        self.assertEqual(len(game.board_layout), 1)
        self.assertEqual(len(game.board_layout[0]), 1)
        self.assertEqual(game.board_layout[0][0], game_engine.CellState.HOLE)


class TestStartNewGame(unittest.TestCase):
    """AC 2.1: start a new game of chosen size/type."""

    def test_solitaire_game_start_new_game_updates_type_and_size(self):
        game = game_engine.SolitaireGame(board_type=game_engine.BoardType.ENGLISH, board_size=7)

        game.start_new_game(board_type=game_engine.BoardType.HEXAGON, board_size=9)

        self.assertEqual(game.board_type, game_engine.BoardType.HEXAGON)
        self.assertEqual(game.board_size, 9)
        self.assertEqual(len(game.board_layout), 9)

    def test_controller_start_new_game_resets_selection(self):
        controller = game_engine.SolitaireGameController()
        controller.selected_peg = (3, 3)

        controller.start_new_game(board_type=game_engine.BoardType.DIAMOND, board_size=7)

        self.assertIsNone(controller.selected_peg)
        self.assertEqual(controller.game.board_type, game_engine.BoardType.DIAMOND)
        self.assertEqual(controller.game.board_size, 7)


class TestMoves(unittest.TestCase):
    """AC 3.1 / 3.2: valid and invalid moves."""

    def setUp(self):
        self.game = game_engine.SolitaireGame(board_type=game_engine.BoardType.ENGLISH, board_size=7)
        self.controller = game_engine.SolitaireGameController(self.game)

    def test_valid_moves_exist_at_start(self):
        moves = self.game.get_valid_moves()
        self.assertTrue(len(moves) > 0)

    def test_make_valid_move_returns_true_and_updates_board(self):
        start_pos, end_pos = self.game.get_valid_moves()[0]

        result = self.game.make_move(start_pos, end_pos)

        self.assertTrue(result)
        sr, sc = start_pos
        er, ec = end_pos
        mr, mc = (sr + er) // 2, (sc + ec) // 2
        self.assertEqual(self.game.board_layout[sr][sc], game_engine.CellState.HOLE)
        self.assertEqual(self.game.board_layout[mr][mc], game_engine.CellState.HOLE)
        self.assertEqual(self.game.board_layout[er][ec], game_engine.CellState.PEG)

    def test_make_invalid_move_returns_false(self):
        # Common invalid move: from a corner INVALID/HOLE to center, or a non-jump
        result = self.game.make_move((0, 0), (0, 1))
        self.assertFalse(result)

    def test_make_valid_diagonal_move_returns_true(self):
        self.game.board_type = game_engine.BoardType.DIAMOND
        self.game.board_layout = [
            [game_engine.CellState.PEG, game_engine.CellState.HOLE, game_engine.CellState.HOLE],
            [game_engine.CellState.HOLE, game_engine.CellState.PEG, game_engine.CellState.HOLE],
            [game_engine.CellState.HOLE, game_engine.CellState.HOLE, game_engine.CellState.HOLE],
        ]

        result = self.game.make_move((0, 0), (2, 2))

        self.assertTrue(result)
        self.assertEqual(self.game.board_layout[0][0], game_engine.CellState.HOLE)
        self.assertEqual(self.game.board_layout[1][1], game_engine.CellState.HOLE)
        self.assertEqual(self.game.board_layout[2][2], game_engine.CellState.PEG)

    def test_controller_handle_cell_click_valid_move(self):
        start_pos, end_pos = self.game.get_valid_moves()[0]
        sr, sc = start_pos
        er, ec = end_pos

        action1 = self.controller.handle_cell_click("peg", sr, sc)
        action2 = self.controller.handle_cell_click("hole", er, ec)

        self.assertEqual(action1, "selected")
        self.assertEqual(action2, "moved")
        self.assertIsNone(self.controller.selected_peg)

    def test_controller_handle_cell_click_invalid_move(self):
        # Select a peg and then click a hole that is not a legal destination.
        # Center is usually hole at game start; corner peg is not a legal jump to center.
        action1 = self.controller.handle_cell_click("peg", 2, 3)
        action2 = self.controller.handle_cell_click("hole", 3, 3)

        self.assertEqual(action1, "selected")
        self.assertEqual(action2, "invalid")
        self.assertIsNone(self.controller.selected_peg)


class TestGameOverAndScoring(unittest.TestCase):
    """AC 4.1 / 4.2: game over detection and score rating."""

    def test_check_game_over_true_when_no_moves(self):
        rules = game_engine.SolitaireRules()
        # Minimal board with one peg and no possible jumps
        board = [[game_engine.CellState.PEG]]

        is_over = rules.check_game_over(board, game_engine.BoardType.ENGLISH)

        self.assertTrue(is_over)

    def test_score_rating_values(self):
        rules = game_engine.SolitaireRules()
        board_0 = [[game_engine.CellState.HOLE]]
        board_1 = [[game_engine.CellState.PEG]]
        board_2 = [[game_engine.CellState.PEG, game_engine.CellState.PEG]]
        board_3 = [[game_engine.CellState.PEG, game_engine.CellState.PEG, game_engine.CellState.PEG]]
        board_4 = [[game_engine.CellState.PEG, game_engine.CellState.PEG, game_engine.CellState.PEG, game_engine.CellState.PEG]]
        self.assertEqual(rules.get_score_rating(board_0), "You win! Congratulations!")
        self.assertEqual(rules.get_score_rating(board_1), "Outstanding (1 marble left)")
        self.assertEqual(rules.get_score_rating(board_2), "Very Good (2 marbles left)")
        self.assertEqual(rules.get_score_rating(board_3), "Good (3 marbles left)")
        self.assertEqual(rules.get_score_rating(board_4), "Average (4 marbles left)")

    def test_controller_notifies_game_over_once(self):
        game = game_engine.SolitaireGame(board_type=game_engine.BoardType.ENGLISH, board_size=1)
        controller = game_engine.SolitaireGameController(game)

        calls = []

        def on_game_over(msg):
            calls.append(msg)

        controller.on_game_over = on_game_over

        # Trigger internal check multiple times; callback should fire once
        controller._check_and_notify_game_over()
        controller._check_and_notify_game_over()

        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0].startswith("You win!"))


if __name__ == "__main__":
    unittest.main()