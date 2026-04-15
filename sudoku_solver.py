import copy
from collections import deque

class SudokuSolverCSP:
    def __init__(self, filepath):
        self.filepath = filepath
        # Load the initial grid
        self.grid = self._load_grid(filepath)
        # Track possible values for each coordinate (r, c)
        self.possibilities = self._setup_domains(self.grid)
        # Track related cells (row, col, 3x3 box)
        self.related_cells = self._setup_arcs()
        
        # Trackers for the assignment deliverables
        self.call_count = 0
        self.fail_count = 0

    def _load_grid(self, filepath):
        """Reads the Sudoku puzzle and cleans up any formatting issues."""
        parsed_grid = []
        with open(filepath, 'r') as file:
            for line in file:
                # Extract only digits to avoid the IndexError you had earlier
                row_data = [int(char) for char in line.strip() if char.isdigit()]
                if row_data:
                    parsed_grid.append(row_data)
        return parsed_grid

    def _setup_domains(self, grid):
        """Initializes 1-9 for zeros, and a single value for pre-filled spots."""
        options = {}
        for r in range(9):
            for c in range(9):
                if grid[r][c] == 0:
                    options[(r, c)] = set(range(1, 10))
                else:
                    options[(r, c)] = {grid[r][c]}
        return options

    def _setup_arcs(self):
        """Maps each cell to its overlapping row, column, and subgrid peers."""
        peers = {}
        for r in range(9):
            for c in range(9):
                cell_peers = set()
                # Add row and column peers
                for i in range(9):
                    if i != c: cell_peers.add((r, i))
                    if i != r: cell_peers.add((i, c))
                
                # Add 3x3 block peers
                box_r, box_c = (r // 3) * 3, (c // 3) * 3
                for br in range(box_r, box_r + 3):
                    for bc in range(box_c, box_c + 3):
                        if (br, bc) != (r, c):
                            cell_peers.add((br, bc))
                            
                peers[(r, c)] = cell_peers
        return peers

    def _revise_domain(self, cell_i, cell_j):
        """Removes values from cell_i if they violate constraints with cell_j."""
        modified = False
        invalid_vals = set()
        
        for val in self.possibilities[cell_i]:
            if len(self.possibilities[cell_j]) == 1 and val in self.possibilities[cell_j]:
                invalid_vals.add(val)
                
        for val in invalid_vals:
            self.possibilities[cell_i].remove(val)
            modified = True
            
        return modified

    def run_ac3(self):
        """Arc Consistency 3 algorithm to prune search space."""
        # Using deque for O(1) pops from the left
        q = deque([(ci, cj) for ci in self.possibilities for cj in self.related_cells[ci]])
        
        while q:
            ci, cj = q.popleft()
            if self._revise_domain(ci, cj):
                # If a domain is wiped out, no solution exists
                if len(self.possibilities[ci]) == 0:
                    return False
                # Re-evaluate neighbors
                for ck in self.related_cells[ci]:
                    if ck != cj:
                        q.append((ck, ci))
        return True

    def is_solved(self):
        """Verifies if every single cell is narrowed down to one choice."""
        return all(len(self.possibilities[cell]) == 1 for cell in self.possibilities)

    def get_mrv_cell(self):
        """Picks the next unassigned variable using MRV (Minimum Remaining Values)."""
        empty_cells = [cell for cell in self.possibilities if len(self.possibilities[cell]) > 1]
        return min(empty_cells, key=lambda c: len(self.possibilities[c]))

    def apply_forward_checking(self, cell, assigned_val):
        """Prunes the newly assigned value from all peer domains."""
        pruned = {}
        for peer in self.related_cells[cell]:
            if assigned_val in self.possibilities[peer]:
                self.possibilities[peer].remove(assigned_val)
                if peer not in pruned:
                    pruned[peer] = set()
                pruned[peer].add(assigned_val)
        return pruned

    def execute_backtrack(self):
        """Recursive backtracking search with forward checking."""
        self.call_count += 1
        
        if self.is_solved():
            return True
            
        curr_cell = self.get_mrv_cell()
        
        for val in list(self.possibilities[curr_cell]):
            # Check constraint validity before assigning
            is_valid = True
            for peer in self.related_cells[curr_cell]:
                if len(self.possibilities[peer]) == 1 and val in self.possibilities[peer]:
                    is_valid = False
                    break
                    
            if is_valid:
                # Lock in the guess
                old_domain = copy.deepcopy(self.possibilities[curr_cell])
                self.possibilities[curr_cell] = {val}
                
                # Execute FC
                pruned_vals = self.apply_forward_checking(curr_cell, val)
                
                # Ensure no domains were completely emptied by FC
                is_safe = all(len(self.possibilities[p]) > 0 for p in self.related_cells[curr_cell])
                
                if is_safe:
                    if self.execute_backtrack():
                        return True
                        
                # Backtrack: Undo guess and restore pruned values
                self.possibilities[curr_cell] = old_domain
                for peer, restored_vals in pruned_vals.items():
                    self.possibilities[peer].update(restored_vals)
                    
        self.fail_count += 1
        return False

    def solve_puzzle(self):
        """Triggers the AC3 and Backtrack sequence."""
        print(f"\n--- Processing: {self.filepath} ---")
        
        if not self.run_ac3():
            print("Unsolvable: Failed during AC-3 phase.")
            return False
            
        if self.execute_backtrack():
            print("Status: SUCCESS!")
            self.display_grid()
            print(f"Total BACKTRACK Calls: {self.call_count}")
            print(f"Total BACKTRACK Failures: {self.fail_count}")
            return True
        else:
            print("Status: FAILED. No valid arrangement found.")
            return False

    def display_grid(self):
        """Formats and prints the final board state."""
        for r in range(9):
            row_vals = []
            for c in range(9):
                val = list(self.possibilities[(r, c)])[0] if len(self.possibilities[(r, c)]) == 1 else 0
                row_vals.append(str(val))
            print(" ".join(row_vals))


# ==========================================
# Script Execution
# ==========================================
if __name__ == "__main__":
    # Ensure these match the exact filenames in your folder
    puzzle_files = ["easy.txt", "medium.txt", "hard.txt", "veryhard.txt"]
    
    for filename in puzzle_files:
        try:
            agent = SudokuSolverCSP(filename)
            agent.solve_puzzle()
        except FileNotFoundError:
            print(f"\nAlert: '{filename}' is missing. Please place it in the directory.")
        except Exception as e:
            print(f"\nAlert: Issue with '{filename}'. Error: {e}")