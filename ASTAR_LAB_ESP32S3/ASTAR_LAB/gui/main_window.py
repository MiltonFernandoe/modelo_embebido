import csv
import json
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QSpinBox, QComboBox, QGroupBox, QMessageBox,
    QFileDialog, QPlainTextEdit, QSplitter, QInputDialog
)
from core.astar import astar
from gui.grid_widget import GridWidget
from communication.esp32_serial import available_ports, solve_on_esp32

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("A* LAB - ESP32-S3 Pathfinding System")
        self.resize(1250, 820)
        self.grid = [[0 for _ in range(10)] for _ in range(10)]
        self.start = (0, 0)
        self.goal = (9, 9)
        self.result = None
        self.edit_mode = "wall"
        self._build_ui()
        self.grid_widget.set_map(self.grid)
        self._refresh_ports()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        header = QLabel("A* LAB  |  ESP32-S3 PATHFINDING")
        header.setStyleSheet("font-size:22px;font-weight:700;color:#e8f1ff;padding:8px;")
        root.addWidget(header)

        controls = QHBoxLayout()
        root.addLayout(controls)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(5, 32)
        self.width_spin.setValue(10)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(5, 32)
        self.height_spin.setValue(10)
        controls.addWidget(QLabel("Ancho"))
        controls.addWidget(self.width_spin)
        controls.addWidget(QLabel("Alto"))
        controls.addWidget(self.height_spin)

        resize_btn = QPushButton("Aplicar tamaño")
        resize_btn.clicked.connect(self.resize_map)
        controls.addWidget(resize_btn)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Obstáculo", "Inicio", "Objetivo", "Borrar"])
        self.mode_combo.currentIndexChanged.connect(self.change_mode)
        controls.addWidget(QLabel("Modo de edición"))
        controls.addWidget(self.mode_combo)

        controls.addStretch(1)
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["Python local", "ESP32-S3 por USB"])
        controls.addWidget(QLabel("Ejecutar en"))
        controls.addWidget(self.engine_combo)

        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(100)
        controls.addWidget(self.port_combo)
        refresh_btn = QPushButton("↻")
        refresh_btn.setToolTip("Actualizar puertos seriales")
        refresh_btn.clicked.connect(self._refresh_ports)
        controls.addWidget(refresh_btn)

        body = QSplitter(Qt.Horizontal)
        root.addWidget(body, 1)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        body.addWidget(left)

        self.grid_widget = GridWidget()
        self.grid_widget.cellClicked.connect(self.edit_cell)
        left_layout.addWidget(self.grid_widget, 1)

        legend = QLabel("S = Inicio   G = Objetivo   Amarillo = Ruta   Azul = Explorado   Negro = Obstáculo")
        legend.setWordWrap(True)
        left_layout.addWidget(legend)

        actions = QHBoxLayout()
        left_layout.addLayout(actions)
        run_btn = QPushButton("▶ Ejecutar A*")
        run_btn.clicked.connect(self.run_search)
        actions.addWidget(run_btn)
        clear_btn = QPushButton("Limpiar obstáculos")
        clear_btn.clicked.connect(self.clear_walls)
        actions.addWidget(clear_btn)
        random_btn = QPushButton("Mapa aleatorio")
        random_btn.clicked.connect(self.random_map)
        actions.addWidget(random_btn)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        body.addWidget(right)
        body.setSizes([720, 480])

        result_group = QGroupBox("Resultado del algoritmo")
        rg = QVBoxLayout(result_group)
        self.status_label = QLabel("Esperando ejecución...")
        self.metrics_label = QLabel("Costo: —   |   Nodos: —   |   Tiempo: —")
        self.metrics_label.setWordWrap(True)
        rg.addWidget(self.status_label)
        rg.addWidget(self.metrics_label)
        right_layout.addWidget(result_group)

        export_group = QGroupBox("Exportación y datos")
        eg = QVBoxLayout(export_group)
        self.data_view = QPlainTextEdit()
        self.data_view.setReadOnly(True)
        self.data_view.setPlaceholderText("Aquí aparecerán la matriz y las coordenadas de la ruta.")
        eg.addWidget(self.data_view, 1)

        export_buttons = QHBoxLayout()
        eg.addLayout(export_buttons)
        for label, handler in [
            ("Descargar CSV", self.export_csv),
            ("Descargar JSON", self.export_json),
            ("Descargar TXT", self.export_txt),
        ]:
            b = QPushButton(label)
            b.clicked.connect(handler)
            export_buttons.addWidget(b)
        right_layout.addWidget(export_group, 1)

        self.setStyleSheet("""
            QMainWindow, QWidget { background:#101d2c; color:#e6eef8; }
            QGroupBox { border:1px solid #35516d; border-radius:8px; margin-top:8px; padding:8px; font-weight:600; }
            QGroupBox::title { subcontrol-origin:margin; left:10px; padding:0 4px; }
            QPushButton, QComboBox, QSpinBox { background:#20364d; border:1px solid #496783; border-radius:5px; padding:7px; }
            QPushButton:hover { background:#2d5273; }
            QPlainTextEdit { background:#0b1521; border:1px solid #35516d; border-radius:6px; font-family:Consolas; }
        """)

    def _refresh_ports(self):
        current = self.port_combo.currentText()
        self.port_combo.clear()
        self.port_combo.addItems(available_ports())
        idx = self.port_combo.findText(current)
        if idx >= 0:
            self.port_combo.setCurrentIndex(idx)

    def change_mode(self, index):
        self.edit_mode = ["wall", "start", "goal", "erase"][index]

    def resize_map(self):
        w, h = self.width_spin.value(), self.height_spin.value()
        self.grid = [[0 for _ in range(w)] for _ in range(h)]
        self.start = (0, 0)
        self.goal = (w-1, h-1)
        self.result = None
        self.grid_widget.start = self.start
        self.grid_widget.goal = self.goal
        self.grid_widget.set_map(self.grid)
        self._show_idle()

    def edit_cell(self, x, y):
        self.result = None
        if self.edit_mode == "wall":
            if (x, y) not in (self.start, self.goal):
                self.grid[y][x] = 0 if self.grid[y][x] else 1
        elif self.edit_mode == "erase":
            if (x, y) not in (self.start, self.goal):
                self.grid[y][x] = 0
        elif self.edit_mode == "start":
            if self.grid[y][x] == 0 and (x, y) != self.goal:
                self.start = (x, y)
        elif self.edit_mode == "goal":
            if self.grid[y][x] == 0 and (x, y) != self.start:
                self.goal = (x, y)
        self.grid_widget.start = self.start
        self.grid_widget.goal = self.goal
        self.grid_widget.set_map(self.grid)
        self._show_idle()

    def clear_walls(self):
        self.grid = [[0 for _ in row] for row in self.grid]
        self.result = None
        self.grid_widget.set_map(self.grid)
        self._show_idle()

    def random_map(self):
        import random
        for y in range(len(self.grid)):
            for x in range(len(self.grid[0])):
                self.grid[y][x] = 0 if (x, y) in (self.start, self.goal) else (1 if random.random() < 0.25 else 0)
        self.result = None
        self.grid_widget.set_map(self.grid)
        self._show_idle()

    def run_search(self):
        if self.engine_combo.currentIndex() == 0:
            self.result = astar(self.grid, self.start, self.goal)
        else:
            port = self.port_combo.currentText()
            if not port:
                QMessageBox.warning(self, "Puerto no seleccionado", "Conecta el ESP32-S3 y selecciona su puerto serial.")
                return
            try:
                self.result = solve_on_esp32(port, self.grid, self.start, self.goal)
            except Exception as exc:
                QMessageBox.critical(self, "Error de comunicación", str(exc))
                return

        if self.result["status"] == "success":
            path = self.result["path"]
            self.grid_widget.set_result(path, self.result.get("explored", []))
            expanded = self.result.get("expanded", len(self.result.get("explored", [])))
            self.status_label.setText("✓ Ruta encontrada")
            self.metrics_label.setText(
                f"Costo: {self.result['cost']}   |   Celdas en ruta: {len(path)}   |   "
                f"Expandidos: {expanded}   |   Tiempo: {self.result['elapsed_us']} µs"
            )
            self._update_data()
        else:
            self.grid_widget.set_result([], self.result.get("explored", []))
            self.status_label.setText("No se encontró una ruta: " + self.result["status"])
            self.metrics_label.setText(f"Nodos explorados: {len(self.result.get('explored', []))}")
            self._update_data()

    def _show_idle(self):
        self.status_label.setText("Mapa modificado. Listo para ejecutar.")
        self.metrics_label.setText("Costo: —   |   Nodos: —   |   Tiempo: —")
        self.data_view.clear()
        self.grid_widget.set_result([], [])

    def _update_data(self):
        lines = ["MATRIZ ORIGINAL (0=libre, 1=obstáculo):"]
        lines.extend(",".join(map(str, row)) for row in self.grid)
        lines.append("")
        lines.append("RUTA (x,y):")
        lines.append(" -> ".join(f"({x},{y})" for x, y in self.result.get("path", [])))
        self.data_view.setPlainText("\n".join(lines))

    def _payload(self):
        if self.result is None:
            raise ValueError("Primero ejecuta A* para generar resultados.")
        return {
            "algorithm": "A*",
            "engine": self.engine_combo.currentText(),
            "status": self.result["status"],
            "width": len(self.grid[0]),
            "height": len(self.grid),
            "start": list(self.start),
            "goal": list(self.goal),
            "grid": self.grid,
            "path": [list(p) for p in self.result.get("path", [])],
            "cost": self.result.get("cost"),
            "elapsed_us": self.result.get("elapsed_us"),
            "expanded": self.result.get("expanded", len(self.result.get("explored", []))),
        }

    def export_csv(self):
        try:
            payload = self._payload()
        except ValueError as e:
            QMessageBox.information(self, "Sin resultados", str(e))
            return
        path_set = {tuple(p) for p in payload["path"]}
        sx, sy = self.start
        gx, gy = self.goal
        output = []
        for y, row in enumerate(self.grid):
            outrow = []
            for x, value in enumerate(row):
                if (x, y) == (sx, sy):
                    outrow.append(3)
                elif (x, y) == (gx, gy):
                    outrow.append(4)
                elif (x, y) in path_set:
                    outrow.append(2)
                else:
                    outrow.append(value)
            output.append(outrow)
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar matriz CSV", "matriz_resuelta.csv", "CSV (*.csv)")
        if filename:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows(output)

    def export_json(self):
        try:
            payload = self._payload()
        except ValueError as e:
            QMessageBox.information(self, "Sin resultados", str(e))
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar JSON", "resultado_astar.json", "JSON (*.json)")
        if filename:
            Path(filename).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def export_txt(self):
        try:
            payload = self._payload()
        except ValueError as e:
            QMessageBox.information(self, "Sin resultados", str(e))
            return
        lines = [
            "A* LAB - RESULTADO",
            f"Estado: {payload['status']}",
            f"Inicio: {self.start}",
            f"Objetivo: {self.goal}",
            f"Costo: {payload['cost']}",
            f"Tiempo (us): {payload['elapsed_us']}",
            "",
            "MATRIZ:"
        ]
        lines += [" ".join(map(str, row)) for row in self.grid]
        lines += ["", "COORDENADAS DE LA RUTA:"]
        lines += [f"{i+1}. ({x},{y})" for i, (x, y) in enumerate(payload["path"])]
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar TXT", "resultado_astar.txt", "Texto (*.txt)")
        if filename:
            Path(filename).write_text("\n".join(lines), encoding="utf-8")
