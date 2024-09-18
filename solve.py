import argparse
import collections
import dataclasses
import enum
import random
import typing

EDGE_COUNT = 4
PIECE_PADDING = 4

Position: typing.TypeAlias = tuple[int, int]

class Shape(enum.Enum):
    Flat = enum.auto()
    Knob = enum.auto()
    Socket = enum.auto()

class Rotation(enum.Enum):
    R0 = 0
    R90 = 1
    R180 = 2
    R270 = 3

class Direction(enum.Enum):
    Up = 0
    Right = 1
    Down = 2
    Left = 3

    def delta(self) -> tuple[int, int]:
        if self == Direction.Up:
            return (-1, 0)
        elif self == Direction.Down:
            return (1, 0)
        elif self == Direction.Right:
            return (0, 1)
        elif self == Direction.Left:
            return (0, -1)
        
    def inverse(self) -> "Direction":
        if self == Direction.Up:
            return Direction.Down
        elif self == Direction.Down:
            return Direction.Up
        elif self == Direction.Right:
            return Direction.Left
        elif self == Direction.Left:
            return Direction.Right

@dataclasses.dataclass(eq=False)
class Edge:
    group: int | None = dataclasses.field(default=None)
    shape: Shape = dataclasses.field(default=Shape.Flat)
    connection: typing.Optional["Edge"] | None = dataclasses.field(default=None)
    merges: set["Edge"] = dataclasses.field(default_factory=set) 

@dataclasses.dataclass
class Piece:
    id: int
    edges: int
    rotation: Rotation

@dataclasses.dataclass
class Board:
    width: int
    height: int
    pieces: list[Piece] = dataclasses.field(default_factory=list)
    edges: list[Edge] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        assert self.width > 1, "Invalid width"
        assert self.height > 1, "Invalid height"

        for i in range(self.height):
            for j in range(self.width):
                if i == 0:
                    rotation = Rotation.R270
                elif j == self.width - 1:
                    rotation = Rotation.R180
                elif i == self.height - 1:
                    rotation = Rotation.R90
                else:
                    rotation = Rotation.R0

                piece_index = len(self.pieces)
                piece_edges = len(self.edges)

                for _ in range(EDGE_COUNT):
                    self.edges.append(Edge())

                self.pieces.append(Piece(piece_index, piece_edges, rotation))

    def is_adjacent(self, from_index: Position, to_index: Position) -> bool:
        return (abs(from_index[0] - to_index[0]) + abs(from_index[1] - to_index[1])) == 1

    def in_bounds(self, index: Position) -> bool:
        return (
            0 <= index[0] 
            and index[0] < self.height
            and 0 <= index[1] 
            and index[1] < self.width
        )

    def get_piece_index(self, index: Position) -> int:
        return index[0] * self.width + index[1]

    def get_edge_index(self, index: Position, direction: Direction) -> int:
        piece = self.pieces[self.get_piece_index(index)]
        rotation = piece.rotation
        offset = (rotation.value + direction.value) % EDGE_COUNT 

        return piece.edges + offset

    def corner_indices(self) -> list[Position]:
        tl = (0, 0)
        tr = (0, self.height-1)
        br = (self.width-1, self.height-1)
        bl = (self.width-1, 0)

        return [tl, tr, br, bl]

    def connect_edges(
        self,
        from_edge_index: int,
        to_edge_index: int,
    ) -> bool:
        if from_edge_index == to_edge_index:
            return False

        from_edge = self.edges[from_edge_index]
        to_edge = self.edges[to_edge_index]

        from_edge.connection = to_edge
        to_edge.connection = from_edge

        return True

    def connect_pieces(self, from_index: Position, to_index: Position) -> bool:
        assert self.is_adjacent(from_index, to_index), "Piece not adjacent"

        directions: tuple[Direction, Direction]
        if from_index[0] < to_index[0]:
            directions = (Direction.Down, Direction.Up)
        elif from_index[0] > to_index[0]:
            directions = (Direction.Up, Direction.Down)
        elif from_index[1] < to_index[1]:
            directions = (Direction.Right, Direction.Left)
        elif from_index[1] > to_index[1]:
            directions = (Direction.Left, Direction.Right)
        else:
            assert False, "Unreachable"

        from_edge_index = self.get_edge_index(from_index, directions[0])
        to_edge_index = self.get_edge_index(to_index, directions[1])

        return self.connect_edges(from_edge_index, to_edge_index)

    def swap_pieces(
        self,
        from_index: Position,
        to_index: Position,
    ) -> None:
        fpi = self.get_piece_index(from_index)
        tpi = self.get_piece_index(to_index)

        self.pieces[fpi], self.pieces[tpi] = self.pieces[tpi], self.pieces[fpi]

    def swap(
        self,
        from_index: Position,
        to_index: Position,
    ) -> bool:
        none_counts = []
        for index in (from_index, to_index):
            none_counts.append(
                sum(
                    self.edges[self.get_edge_index(index, direction)].connection == None
                    for direction in Direction
                )
            )

        from_count, to_count = none_counts
        if from_count != to_count:
            return False

        if from_count > 0:
            from_piece = self.pieces[self.get_piece_index(from_index)]
            to_piece = self.pieces[self.get_piece_index(to_index)]

            from_piece.rotation, to_piece.rotation = to_piece.rotation, from_piece.rotation

        self.swap_pieces(from_index, to_index)

        return True

    def connect_adjacent_edges(self) -> bool:
        for i in range(self.height):
            for j in range(self.width):
                from_index = (i, j)

                for direction in Direction:
                    di, dj = direction.delta()
                    to_index = (i + di, j + dj)

                    if not self.in_bounds(to_index):
                        continue

                    if not self.connect_pieces(from_index, to_index):
                        return False
     
        return True
    
    def shuffle(self) -> None:
        edges: list[tuple[int, int]] = []

        for i in (0, self.height - 1):
            for j in range(1, self.width - 1):
                if i == j:
                    continue

                edges.append((i, j))

        for j in (0, self.width - 1):
            for i in range(1, self.height - 1):
                if i == j:
                    continue

                edges.append((i, j))

        random.shuffle(edges)

        for i in range(0, len(edges), 3):
            e = edges[i:i+3]

            if len(e) != 3:
                break

            assert self.swap(e[0], e[1])
            assert self.swap(e[0], e[2])

        centers = []

        for i in range(1, self.height - 1):
            for j in range(1, self.width - 1):
                centers.append((i, j))

        random.shuffle(centers)

        for i in range(0, len(centers), 3):
            c = centers[i:i+3]

            if len(c) != 3:
                break

            assert self.swap(c[0], c[1])
            assert self.swap(c[0], c[2])

            self.pieces[self.get_piece_index(c[0])].rotation = random.choice([v for v in Rotation])

    def merge_edges(self) -> None:
        for i in range(self.height):
            for j in range(self.width):
                from_index = (i, j)

                for direction in Direction:
                    di, dj = direction.delta()
                    to_index = (i + di, j + dj)

                    if not self.in_bounds(to_index):
                        continue

                    from_edge_index = self.get_edge_index(from_index, direction)
                    from_edge = self.edges[from_edge_index]

                    adjacent_edge_index = self.get_edge_index(to_index, direction.inverse())

                    to_edge = self.edges[adjacent_edge_index].connection

                    from_edge.merges.add(to_edge)
                    to_edge.merges.add(from_edge)

    def collapse_edges(self) -> bool:
        edge_group_map: dict[Edge, int] = {}
        groups: dict[int, set[Edge]] = {}

        for edge in self.edges:
            if edge.connection is None:
                continue

            if edge in edge_group_map:
                continue

            group = set()
            group_id = len(groups)

            queue = [edge]
            while queue:
                next_edge = queue.pop()
                if next_edge in group:
                    continue

                group.add(next_edge)

                queue += next_edge.merges

            for next_edge in group:
                edge_group_map[next_edge] = group_id

            groups[group_id] = group

        group_connections = collections.defaultdict(set)
        for edge in self.edges:
            if edge.connection is None:
                continue

            group_connections[edge_group_map[edge]].add(edge_group_map[edge.connection])
        group_connections = dict(group_connections)

        group_group_map: dict[int, int] = {}
        group_groups: dict[int, set[int]] = {}
        group_group_shape: dict[int, Shape] = {}
        for group_id in group_connections.keys():
            if group_id in group_group_map:
                continue

            queue = [(group_id, 0)]
            seen = set()

            layers = collections.defaultdict(set)
            while queue:
                group_id, depth = queue.pop()

                if group_id in group_group_map:
                    continue

                if group_id in seen:
                    continue
                seen.add(group_id)

                layers[depth].add(group_id)

                queue += [(c, depth + 1) for c in group_connections[group_id]]

            even, odd = set(), set()
            for depth, group_id in layers.items():
                if depth % 2 == 0:
                    even = even.union(group_id)
                else:
                    odd = odd.union(group_id)

            if even.intersection(odd):
                return False
            
            for group_group, shape in [(even, Shape.Knob), (odd, Shape.Socket)]:
                gg_id = len(group_groups)

                group_groups[gg_id] = group_group
                group_group_shape[gg_id] = shape

                for group_id in group_group:
                    group_group_map[group_id] = gg_id

        for gg_id, g_ids in group_groups.items():
            shape = group_group_shape[gg_id]

            for g_id in g_ids:
                for edge in groups[g_id]:
                    edge.group = gg_id // 2
                    edge.shape = shape

        return True

    def check_all_unique(self) -> bool:
        piece_set = set()

        for piece in self.pieces:
            edges = []

            for edge in self.edges[piece.edges:piece.edges+EDGE_COUNT]:
                edges.append((edge.group, edge.shape))

            out_piece = tuple(edges)
            if out_piece in piece_set:
                return False

            piece_set.add(out_piece)

        return True

    def edge_str(self, index: int) -> str:
        edge = self.edges[index]
        shape = edge.shape

        if shape == Shape.Knob:
            return f"+{edge.group}"
        elif shape == Shape.Socket:
            return f"-{edge.group}" 

        return ""

    def piece_str(self, index: Position) -> str:
        piece = self.pieces[self.get_piece_index(index)]
        edge_indices = [self.get_edge_index(index, direction) for direction in Direction]

        up, right, down, left = [self.edge_str(index) for index in edge_indices]

        name = str(piece.id).rjust(PIECE_PADDING, " ")

        up = up.rjust(PIECE_PADDING, " ")
        right = right.rjust(PIECE_PADDING, " ")
        down = down.rjust(PIECE_PADDING, " ")
        left = left.ljust(PIECE_PADDING, " ")

        lines = [
            " " * PIECE_PADDING + up + " " * PIECE_PADDING,
            left + name + right,
            " " * PIECE_PADDING + down + " " * PIECE_PADDING,
        ]

        return "\n".join(lines)

    def board_str(self) -> str:
        piece_lines = 4

        lines_segments = [[] for _ in range(piece_lines * self.height)]

        for i in range(self.height):
            line_offset = i * piece_lines

            for j in range(self.width):
                for k, line in enumerate(self.piece_str((i, j)).split("\n")):
                    lines_segments[line_offset + k].append(line)

        return "\n".join(" ".join(line_segments) for line_segments in lines_segments).rstrip() + "\n"

def main(width: int, height: int) -> None:
    while True:
        board = Board(width, height)

        board.connect_adjacent_edges()

        board.shuffle()
        board.merge_edges()

        board.collapse_edges()
        
        if board.check_all_unique():
            break

    print("Initial")
    pieces = board.pieces
    board.pieces = Board(board.width, board.height).pieces
    print(board.board_str())

    print("Final")
    board.pieces = pieces
    print(board.board_str())

def cli() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--width", help="Number of jigsaw pieces on the X-axis", type=int, default=5)
    parser.add_argument("--height", help="Number of jigsaw pieces on the Y-axis", type=int, default=5)

    args = parser.parse_args()

    main(
        width=args.width,
        height=args.height
    )

if __name__ == "__main__":
    cli()
