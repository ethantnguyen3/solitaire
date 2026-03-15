import board as logic


def get_jump_directions(board_type):
    """Returns valid jump offsets (delta_row, delta_col) based on board geometry."""
    directions = [(0, 2), (0, -2), (2, 0), (-2, 0)]

    if board_type == logic.BoardType.HEXAGON:
        directions.extend([(2, -2), (-2, 2)])

    return directions


def get_all_valid_moves(board_layout, board_type):
    """Return all legal moves as ((start_row, start_col), (end_row, end_col))."""
    moves = []
    size = len(board_layout)
    directions = get_jump_directions(board_type)

    for row in range(size):
        for col in range(size):
            if board_layout[row][col] != logic.CellState.PEG:
                continue

            for delta_row, delta_col in directions:
                end_row, end_col = row + delta_row, col + delta_col
                mid_row, mid_col = row + (delta_row // 2), col + (delta_col // 2)

                if 0 <= end_row < size and 0 <= end_col < size:
                    if board_layout[end_row][end_col] == logic.CellState.HOLE:
                        if board_layout[mid_row][mid_col] == logic.CellState.PEG:
                            moves.append(((row, col), (end_row, end_col)))

    return moves


def execute_move(board_layout, start_pos, end_pos):
    """Apply one jump move to the board in-place."""
    start_row, start_col = start_pos
    end_row, end_col = end_pos
    mid_row = (start_row + end_row) // 2
    mid_col = (start_col + end_col) // 2

    board_layout[start_row][start_col] = logic.CellState.HOLE
    board_layout[mid_row][mid_col] = logic.CellState.HOLE
    board_layout[end_row][end_col] = logic.CellState.PEG

    return board_layout


def check_game_over(board_layout, board_type):
    """Return True when there are no valid moves left."""
    return len(get_all_valid_moves(board_layout, board_type)) == 0


def get_score_rating(board_layout):
    """Return text rating based on remaining peg count."""
    peg_count = sum(row.count(logic.CellState.PEG) for row in board_layout)

    if peg_count == 1:
        return "Outstanding (1 marble left)"
    if peg_count == 2:
        return "Very Good (2 marbles left)"
    if peg_count == 3:
        return "Good (3 marbles left)"
    return f"Average ({peg_count} marbles left)"
