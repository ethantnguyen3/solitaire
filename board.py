from enum import Enum 

class CellState(Enum): 
    PEG = 1
    HOLE = 0
    INVALID = -1 

class BoardType: 
    ENGLISH = "English"
    HEXAGON = "Hexagon"
    DIAMOND = "Diamond" 

class Cell: 
    def __init__(self, row, col, state=CellState.INVALID):
        self.row = row
        self.col = col
        self.state = state 

class PegBoard: 
    def __init__(self, board_type=BoardType.ENGLISH, board_size=7): 
        self.board_type = board_type 
        self.board_size = board_size 
        self.cell_size = 60 
        #lines 25-127 AI generated
        self.peg_radius = 20  
        self.board_layout = generate_board_layout(self.board_type, self.board_size)
        self.pegs = [row[:] for row in self.board_layout]

        # Set center cell to HOLE
        center_row = len(self.pegs) // 2
        center_col = len(self.pegs[0]) // 2
        self.pegs[center_row][center_col] = CellState.HOLE
     
     

def generate_english_board(size):
    # It is highly recommended to use an odd number for size 
    # so there is a perfect center for the starting empty space.
    if size % 2 == 0:
        print("Warning: Even sizes won't have a perfect center.")
        
    board = []
    corner_size = size // 3 
    center = size // 2
    
    for r in range(size):
        row = []
        for c in range(size):
            # Check if the current (r, c) falls into one of the four corners
            in_top_left = (r < corner_size) and (c < corner_size)
            in_top_right = (r < corner_size) and (c >= size - corner_size)
            in_bottom_left = (r >= size - corner_size) and (c < corner_size)
            in_bottom_right = (r >= size - corner_size) and (c >= size - corner_size)
            
            if in_top_left or in_top_right or in_bottom_left or in_bottom_right:
                row.append(CellState.INVALID)
            elif r == center and c == center:
                row.append(CellState.HOLE) # The starting empty hole
            else:
                row.append(CellState.PEG)
                
        board.append(row)
        
    return board 

def generate_diamond_board(size):
    if size % 2 == 0:
        print("Warning: Even sizes won't have a perfect center.")
        
    board = []
    center = size // 2
    
    for r in range(size):
        row = []
        for c in range(size):
            # Calculate the Manhattan distance from the center cell
            distance_from_center = abs(r - center) + abs(c - center)
            
            # If the distance is greater than the center radius, it's a dead corner
            if distance_from_center > center:
                row.append(CellState.INVALID)
            elif r == center and c == center:
                row.append(CellState.HOLE) # The starting empty hole
            else:
                row.append(CellState.PEG)
                
        board.append(row)
        
    return board 

def generate_hexagon_board(size): 
    if size % 2 == 0:
        print("Warning: Even sizes won't have a perfect center.")
        
    board = []
    radius = size // 2
    
    for r in range(size):
        row = []
        for c in range(size):
            # Shift the coordinates so the math treats the center as (0, 0)
            dq = c - radius
            dr = r - radius
            
            # The magic formula for a hexagon in axial coordinates:
            # The column, the row, and their sum must all be within the radius limits
            if abs(dq) <= radius and abs(dr) <= radius and abs(dq + dr) <= radius:
                if dq == 0 and dr == 0:
                    row.append(CellState.HOLE) # The starting empty hole
                else:
                    row.append(CellState.PEG)
            else:
                row.append(CellState.INVALID)
                
        board.append(row)
        
    return board 

def generate_board_layout(board_type, size):
    if board_type == BoardType.ENGLISH:
        return generate_english_board(size)
    elif board_type == BoardType.DIAMOND:
        return generate_diamond_board(size)
    elif board_type == BoardType.HEXAGON:
        return generate_hexagon_board(size)
    else:
        raise ValueError("Unknown board type")