from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import QWidget

class GridWidget(QWidget):
    cellClicked = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid = [[0 for _ in range(10)] for _ in range(10)]
        self.start = (0, 0)
        self.goal = (9, 9)
        self.path = []
        self.explored = []
        self.setMinimumSize(500, 500)
        self.setMouseTracking(True)

    def set_map(self, grid):
        self.grid = [row[:] for row in grid]
        self.path = []
        self.explored = []
        self.update()

    def set_result(self, path, explored=None):
        self.path = list(path)
        self.explored = list(explored or [])
        self.update()

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(620, 620)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        h = len(self.grid)
        w = len(self.grid[0]) if h else 0
        if not w or not h:
            return
        cell = min(self.width() / w, self.height() / h)
        ox = (self.width() - cell*w) / 2
        oy = (self.height() - cell*h) / 2
        path_set = set(self.path)
        explored_set = set(self.explored)

        colors = {
            "free": QColor("#334b66"),
            "wall": QColor("#111923"),
            "explored": QColor("#25617a"),
            "path": QColor("#f5b942"),
            "start": QColor("#16a36a"),
            "goal": QColor("#e84545"),
        }

        p.setFont(QFont("Arial", max(8, int(cell*0.27)), QFont.Bold))
        for y in range(h):
            for x in range(w):
                rect_x = ox + x*cell
                rect_y = oy + y*cell
                pos = (x, y)
                color = colors["wall"] if self.grid[y][x] else colors["free"]
                if pos in explored_set and pos not in path_set:
                    color = colors["explored"]
                if pos in path_set:
                    color = colors["path"]
                if pos == self.start:
                    color = colors["start"]
                if pos == self.goal:
                    color = colors["goal"]
                p.fillRect(int(rect_x), int(rect_y), int(cell), int(cell), color)
                p.setPen(QPen(QColor("#9fb2c7"), 1))
                p.drawRect(int(rect_x), int(rect_y), int(cell), int(cell))
                p.setPen(QColor("white"))
                label = ""
                if pos == self.start:
                    label = "S"
                elif pos == self.goal:
                    label = "G"
                elif pos in path_set:
                    label = "•"
                elif self.grid[y][x]:
                    label = "1"
                p.drawText(int(rect_x), int(rect_y), int(cell), int(cell),
                           Qt.AlignCenter, label)

    def mousePressEvent(self, event):
        h = len(self.grid)
        w = len(self.grid[0]) if h else 0
        cell = min(self.width() / w, self.height() / h)
        ox = (self.width() - cell*w) / 2
        oy = (self.height() - cell*h) / 2
        x = int((event.position().x() - ox) // cell)
        y = int((event.position().y() - oy) // cell)
        if 0 <= x < w and 0 <= y < h:
            self.cellClicked.emit(x, y)
