from copy import deepcopy
from logging import Logger
from typing import List

logger = Logger("Battle field", level="DEBUG")


class Validator:
    """
    Base interface
    """

    board_length = 10

    def __init__(self, board: List[List[int]]):
        self.board = board

    def validate(self) -> bool:
        raise NotImplementedError


class BoardValidator(Validator):
    """
    Board main validation, if columns and rows numbers are correct
    """

    def validate(self) -> bool:
        if len(self.board) != self.board_length:
            raise ValueError("Board has wrong columns count")

        for column in self.board:
            if len(column) != self.board_length:
                raise ValueError("Column has wrong rows count")

        return True


class AbstractShipValidator(Validator):
    def inspect_cell(self, i_coord: int, j_coord: int) -> int:
        """Check if cell is filled"""
        return self.board[i_coord][j_coord]

    def get_neighbor_cell_status(self, i_coord: int, j_coord: int) -> int:
        """
        Get neighbor cell for check, return 0 if out of board
        """

        if 0 <= i_coord < self.board_length and 0 <= j_coord < self.board_length:
            return self.inspect_cell(i_coord, j_coord)
        return 0

    def validate(self) -> bool:
        raise NotImplementedError


class BattleShipsValidator(AbstractShipValidator):
    """
    This validator check only ship construction.
    Ex, ship must be in one line - vertically or horizontally.
    We do not check here if number of ships on the field is correct
    """

    def check_if_neighbor_cells_set_up_correct(self, i_coord: int, j_coord: int) -> bool:
        left = self.get_neighbor_cell_status(i_coord - 1, j_coord)
        right = self.get_neighbor_cell_status(i_coord + 1, j_coord)
        upper = self.get_neighbor_cell_status(i_coord, j_coord - 1)
        lower = self.get_neighbor_cell_status(i_coord, j_coord + 1)

        if sum([upper, left, right, lower]) in (0, 1):
            return True
        if left and right and not (upper or lower):
            return True
        if upper and lower and not (left or right):
            return True

        raise ValueError(
            f"Ship construction is wrong, cells are: left {left}, right {right}, upper {upper}, lower {lower}"
        )

    def check_if_cross_cells_set_up_correct(self, i_coord: int, j_coord: int) -> bool:
        left_upper = self.get_neighbor_cell_status(i_coord - 1, j_coord + 1)
        left_lower = self.get_neighbor_cell_status(i_coord - 1, j_coord - 1)
        right_upper = self.get_neighbor_cell_status(i_coord + 1, j_coord + 1)
        right_lower = self.get_neighbor_cell_status(i_coord + 1, j_coord - 1)

        if not any([left_upper, left_lower, right_upper, right_lower]):
            return True

        raise ValueError(f"Ship construction is wrong, ships are in contact by diagonal")

    def validate(self) -> bool:
        for i_index, column in enumerate(self.board):
            for j_index, _ in enumerate(column):
                if not self.inspect_cell(i_index, j_index):
                    continue
                self.check_if_neighbor_cells_set_up_correct(i_index, j_index)
                self.check_if_cross_cells_set_up_correct(i_index, j_index)

        return True


class BattleShipsQuantityValidator(AbstractShipValidator):
    """
    Validate warships quantity by size
    For simplifying - work with copy and modify it
    """

    def __init__(self, board: List[List[int]]):
        board = deepcopy(board)
        super().__init__(board)
        self.ship_length_to_count = {key: 5 - key for key in range(1, 5)}

    def validate_ship_vertically(self, i_coord: int, j_coord: int, length: int) -> bool:
        cells = [self.get_neighbor_cell_status(i_coord + i, j_coord) for i in range(1, length)]
        return all(cells)

    def validate_ship_horizontally(self, i_coord: int, j_coord: int, length: int) -> bool:
        cells = [self.get_neighbor_cell_status(i_coord, j_coord + i) for i in range(1, length)]
        return all(cells)

    def drop_vertically(self, i_coord: int, j_coord: int, length: int) -> None:
        for i in range(1, length):
            self.board[i_coord + i][j_coord] = 0

    def drop_horizontally(self, i_coord: int, j_coord: int, length: int) -> None:
        for i in range(1, length):
            self.board[i_coord][j_coord + i] = 0

    def drop_ship(self, i_coord: int, j_coord: int, length: int) -> bool:
        vertical = self.validate_ship_vertically(i_coord, j_coord, length)
        if vertical:
            self.drop_vertically(i_coord, j_coord, length)
        horizontal = self.validate_ship_horizontally(i_coord, j_coord, length)
        if horizontal:
            self.drop_horizontally(i_coord, j_coord, length)
        return vertical or horizontal

    def drop_flagman(self, i_coord: int, j_coord: int) -> bool:
        """
        4-cell ship, should be 1
        """
        length = 4
        return self.drop_ship(i_coord, j_coord, length)

    def drop_cruiser(self, i_coord: int, j_coord: int) -> bool:
        """
        3-cell ship, should be 2
        """
        length = 3
        return self.drop_ship(i_coord, j_coord, length)

    def drop_destroyer(self, i_coord: int, j_coord: int) -> bool:
        """
        2-cell ship, should be 3
        """
        length = 2
        return self.drop_ship(i_coord, j_coord, length)

    def validate(self) -> bool:
        for i_index, column in enumerate(self.board):
            for j_index, _ in enumerate(column):
                if not self.inspect_cell(i_index, j_index):
                    continue
                if self.drop_flagman(i_index, j_index):
                    self.ship_length_to_count[4] -= 1
                elif self.drop_cruiser(i_index, j_index):
                    self.ship_length_to_count[3] -= 1
                elif self.drop_destroyer(i_index, j_index):
                    self.ship_length_to_count[2] -= 1
                else:
                    self.ship_length_to_count[1] -= 1

        result = all(map(lambda x: x == 0, self.ship_length_to_count.values()))
        if not result:
            raise ValueError("Ships are incorrect")
        return True


def validate_battlefield(field: List[List[int]]) -> bool:
    """decorator for codewars"""
    # validators = [BoardValidator, BattleShipsValidator]
    validators = [BoardValidator, BattleShipsValidator, BattleShipsQuantityValidator]

    for validator in validators:
        _validator = validator(field)
        try:
            _validator.validate()
        except ValueError as error:
            logger.debug(error.args[0])
            return False

    return True
