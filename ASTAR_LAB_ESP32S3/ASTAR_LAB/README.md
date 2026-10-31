# A* LAB — ESP32-S3 Pathfinding System

## Requisitos
- Python 3.10+
- Arduino IDE 2.x
- ESP32 board package
- PySide6 y pyserial

## Instalar Python
En una terminal dentro de la carpeta ASTAR_LAB:

```bash
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

## Uso de la interfaz
1. Elige ancho y alto y pulsa Aplicar tamaño.
2. Selecciona Obstáculo y haz clic en celdas para bloquearlas.
3. Selecciona Inicio y Objetivo para mover S y G.
4. Elige Python local y pulsa Ejecutar A*.
5. Exporta CSV, JSON o TXT.

## Ejecutar en ESP32-S3
1. Abre firmware/esp32_astar/esp32_astar.ino en Arduino IDE.
2. Selecciona la placa ESP32-S3 Dev Module y el puerto correcto.
3. Carga el firmware.
4. Cierra el Monitor Serial (no puede compartir el puerto con Python).
5. En A* LAB selecciona ESP32-S3 por USB y el mismo puerto.
6. Pulsa Ejecutar A*.

## Protocolo serial
Python envía:
- BEGIN,width,height,sx,sy,gx,gy
- ROW, seguido de 0/1 por cada fila
- END

El ESP32-S3 responde con RESULT, una línea P,x,y por cada punto de la ruta y DONE.

## Notas
- La cuadrícula admite hasta 32 x 32 en el firmware.
- Movimientos ortogonales de costo 10.
- Heurística Manhattan.
- Los tiempos Python y ESP32-S3 no son directamente comparables: Python mide tiempo de su proceso y el ESP32-S3 mide micros() en el microcontrolador.
- El firmware de referencia recibe filas en orden y está diseñado para una transferencia completa por cada ejecución.
