import time
import serial
from serial.tools import list_ports

def available_ports():
    return [p.device for p in list_ports.comports()]

def solve_on_esp32(port, grid, start, goal, baud=115200, timeout=15):
    """
    Protocolo:
      BEGIN,width,height,sx,sy,gx,gy
      ROW,010101...
      ...
      END
    Respuesta:
      RESULT,OK,cost,pathlen,expanded,elapsed_us
      P,x,y
      ...
      DONE
    """
    h = len(grid)
    w = len(grid[0])
    sx, sy = start
    gx, gy = goal

    with serial.Serial(port, baudrate=baud, timeout=1, write_timeout=3) as ser:
        time.sleep(2.0)  # muchas placas se reinician al abrir el puerto
        ser.reset_input_buffer()
        ser.write(f"BEGIN,{w},{h},{sx},{sy},{gx},{gy}\n".encode())
        for row in grid:
            ser.write(("ROW," + "".join(str(int(v)) for v in row) + "\n").encode())
        ser.write(b"END\n")
        ser.flush()

        deadline = time.time() + timeout
        result = None
        path = []
        while time.time() < deadline:
            line = ser.readline().decode("utf-8", errors="replace").strip()
            if not line:
                continue
            parts = line.split(",")
            if parts[0] == "RESULT" and len(parts) >= 6:
                result = {
                    "status": "success" if parts[1] == "OK" else "no_path",
                    "cost": int(parts[2]),
                    "path_length": int(parts[3]),
                    "expanded": int(parts[4]),
                    "elapsed_us": int(parts[5]),
                }
            elif parts[0] == "P" and len(parts) == 3:
                path.append((int(parts[1]), int(parts[2])))
            elif parts[0] == "DONE":
                break

        if result is None:
            raise TimeoutError("El ESP32-S3 no devolvió una respuesta válida. Revisa firmware, puerto y baudrate.")
        result["path"] = path
        result["explored"] = []
        return result
