import heapq
import time

def astar(grid, start, goal):
    """
    grid[y][x]: 0 libre, 1 obstáculo.
    start y goal: (x, y).
    Devuelve dict con path, explored, cost, elapsed_us y status.
    """
    h = len(grid)
    w = len(grid[0]) if h else 0
    sx, sy = start
    gx, gy = goal

    if not (0 <= sx < w and 0 <= gx < w and 0 <= sy < h and 0 <= gy < h):
        return {"status": "invalid", "path": [], "explored": [], "cost": None, "elapsed_us": 0}
    if grid[sy][sx] or grid[gy][gx]:
        return {"status": "blocked", "path": [], "explored": [], "cost": None, "elapsed_us": 0}

    t0 = time.perf_counter_ns()
    # heap items: (f, h, insertion_order, x, y)
    heap = []
    counter = 0
    g_score = {start: 0}
    parent = {}
    closed = set()
    explored = []

    def heuristic(p):
        return abs(p[0] - gx) + abs(p[1] - gy)

    heapq.heappush(heap, (heuristic(start), heuristic(start), counter, sx, sy))

    while heap:
        _, _, _, x, y = heapq.heappop(heap)
        current = (x, y)
        if current in closed:
            continue
        closed.add(current)
        explored.append(current)

        if current == goal:
            path = [goal]
            while path[-1] != start:
                path.append(parent[path[-1]])
            path.reverse()
            elapsed = (time.perf_counter_ns() - t0) // 1000
            return {
                "status": "success",
                "path": path,
                "explored": explored,
                "cost": g_score[goal] * 10,
                "elapsed_us": int(elapsed),
            }

        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            nx, ny = x + dx, y + dy
            neighbor = (nx, ny)
            if not (0 <= nx < w and 0 <= ny < h):
                continue
            if grid[ny][nx] == 1 or neighbor in closed:
                continue
            tentative = g_score[current] + 1
            if tentative < g_score.get(neighbor, float("inf")):
                parent[neighbor] = current
                g_score[neighbor] = tentative
                hn = heuristic(neighbor)
                counter += 1
                heapq.heappush(heap, (tentative + hn, hn, counter, nx, ny))

    elapsed = (time.perf_counter_ns() - t0) // 1000
    return {"status": "no_path", "path": [], "explored": explored, "cost": None, "elapsed_us": int(elapsed)}
