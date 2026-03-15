import unittest
from unittest.mock import patch

import tkinter as tk

import board
import game_engine
import solitaire_gui


class SolitaireTests(unittest.TestCase):
	def setUp(self):
		self.root = tk.Tk()
		self.root.withdraw()
		self.app = solitaire_gui.SolitaireGUI(self.root)
		self.root.update_idletasks()

	def tearDown(self):
		self.root.destroy()

	def test_choose_board_size_and_type(self):
		self.app.size_var.set("9")
		self.app.type_var.set(board.BoardType.DIAMOND)

		self.app.update_board()

		self.assertEqual(self.app.type_var.get(), board.BoardType.DIAMOND)
		self.assertEqual(len(self.app.board_layout), 9)
		self.assertTrue(all(len(row) == 9 for row in self.app.board_layout))
		self.assertEqual(self.app.board_layout[4][4], board.CellState.HOLE)
		self.assertEqual(self.app.board_layout[0][0], board.CellState.INVALID)

	def test_start_new_game_of_chosen_board_size_and_type(self):
		self.app.size_var.set("7")
		self.app.type_var.set(board.BoardType.ENGLISH)
		self.app.update_board()

		game_engine.execute_move(self.app.board_layout, (1, 3), (3, 3))
		self.assertEqual(self.app.board_layout[1][3], board.CellState.HOLE)

		self.app.size_var.set("9")
		self.app.type_var.set(board.BoardType.HEXAGON)
		self.app.update_board()

		fresh_board = board.generate_board_layout(board.BoardType.HEXAGON, 9)
		self.assertEqual(self.app.board_layout, fresh_board)
		self.assertEqual(self.app.board_layout[4][4], board.CellState.HOLE)
		self.assertFalse(self.app.game_over)

	def test_making_a_move(self):
		board_layout = board.generate_board_layout(board.BoardType.ENGLISH, 7)

		self.assertIn(((1, 3), (3, 3)), game_engine.get_all_valid_moves(board_layout, board.BoardType.ENGLISH))

		game_engine.execute_move(board_layout, (1, 3), (3, 3))

		self.assertEqual(board_layout[1][3], board.CellState.HOLE)
		self.assertEqual(board_layout[2][3], board.CellState.HOLE)
		self.assertEqual(board_layout[3][3], board.CellState.PEG)

	def test_checking_end_of_game(self):
		end_game_board = [
			[board.CellState.INVALID, board.CellState.INVALID, board.CellState.INVALID],
			[board.CellState.INVALID, board.CellState.PEG, board.CellState.INVALID],
			[board.CellState.INVALID, board.CellState.INVALID, board.CellState.INVALID],
		]

		self.assertTrue(game_engine.check_game_over(end_game_board, board.BoardType.ENGLISH))
		self.assertEqual(game_engine.get_score_rating(end_game_board), "Outstanding (1 marble left)")

	@patch("solitaire_gui.messagebox.showinfo")
	def test_game_over_popup_uses_rating(self, mock_showinfo):
		self.app.board_layout = [
			[board.CellState.INVALID, board.CellState.INVALID, board.CellState.INVALID],
			[board.CellState.INVALID, board.CellState.PEG, board.CellState.INVALID],
			[board.CellState.INVALID, board.CellState.INVALID, board.CellState.INVALID],
		]
		self.app.game_over = False

		self.app.check_for_game_over(board.BoardType.ENGLISH)

		mock_showinfo.assert_called_once_with(
			"Game Over",
			"No more valid moves are possible.\nRating: Outstanding (1 marble left)",
		)
		self.assertTrue(self.app.game_over)


if __name__ == "__main__":
	unittest.main()
