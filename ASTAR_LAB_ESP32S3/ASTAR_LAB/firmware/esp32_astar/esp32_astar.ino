#include <Arduino.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

#define MAX_W 32
#define MAX_H 32
#define MAX_NODES (MAX_W * MAX_H)
#define INF 65535
#define MOVE_COST 10

uint8_t grid[MAX_H][MAX_W];
uint8_t W = 0, H = 0;
uint16_t startNode, goalNode;

uint8_t state[MAX_NODES];       // 0 unseen, 1 open, 2 closed
uint16_t gScore[MAX_NODES];
int16_t parentNode[MAX_NODES];
uint16_t heap[MAX_NODES];
int16_t heapPos[MAX_NODES];
uint16_t heapSize = 0;
uint16_t path[MAX_NODES];
uint16_t pathLength = 0;
uint32_t expandedNodes = 0;

char lineBuffer[160];

uint16_t toID(int x, int y) { return (uint16_t)(y * W + x); }
int getX(uint16_t id) { return id % W; }
int getY(uint16_t id) { return id / W; }

uint16_t heuristic(uint16_t a) {
  return (abs(getX(a) - getX(goalNode)) +
          abs(getY(a) - getY(goalNode))) * MOVE_COST;
}

bool lessNode(uint16_t a, uint16_t b) {
  uint32_t fa = (uint32_t)gScore[a] + heuristic(a);
  uint32_t fb = (uint32_t)gScore[b] + heuristic(b);
  if (fa != fb) return fa < fb;
  return heuristic(a) < heuristic(b);
}

void swapHeap(uint16_t i, uint16_t j) {
  uint16_t t = heap[i]; heap[i] = heap[j]; heap[j] = t;
  heapPos[heap[i]] = i; heapPos[heap[j]] = j;
}

void siftUp(uint16_t i) {
  while (i > 0) {
    uint16_t p = (i - 1) / 2;
    if (!lessNode(heap[i], heap[p])) break;
    swapHeap(i, p); i = p;
  }
}

void siftDown(uint16_t i) {
  while (true) {
    uint16_t l = 2 * i + 1, r = l + 1, m = i;
    if (l < heapSize && lessNode(heap[l], heap[m])) m = l;
    if (r < heapSize && lessNode(heap[r], heap[m])) m = r;
    if (m == i) break;
    swapHeap(i, m); i = m;
  }
}

void insertOrUpdate(uint16_t n) {
  if (heapPos[n] == -1) {
    if (heapSize >= MAX_NODES) return;
    heap[heapSize] = n;
    heapPos[n] = heapSize;
    heapSize++;
    siftUp(heapPos[n]);
  } else {
    siftUp(heapPos[n]);
  }
}

uint16_t popHeap() {
  uint16_t result = heap[0];
  heapPos[result] = -1;
  heapSize--;
  if (heapSize) {
    heap[0] = heap[heapSize];
    heapPos[heap[0]] = 0;
    siftDown(0);
  }
  return result;
}

bool reconstruct(uint16_t start) {
  pathLength = 0;
  int32_t cur = goalNode;
  while (cur >= 0) {
    if (pathLength >= MAX_NODES) return false;
    path[pathLength++] = (uint16_t)cur;
    if ((uint16_t)cur == start) break;
    cur = parentNode[cur];
  }
  return path[pathLength - 1] == start;
}

bool solveAStar() {
  memset(state, 0, sizeof(state));
  for (uint16_t i = 0; i < MAX_NODES; i++) {
    gScore[i] = INF;
    parentNode[i] = -1;
    heapPos[i] = -1;
  }
  heapSize = 0;
  pathLength = 0;
  expandedNodes = 0;

  if (grid[getY(startNode)][getX(startNode)] ||
      grid[getY(goalNode)][getX(goalNode)]) return false;

  gScore[startNode] = 0;
  state[startNode] = 1;
  insertOrUpdate(startNode);

  const int8_t dx[4] = {0, 0, -1, 1};
  const int8_t dy[4] = {-1, 1, 0, 0};

  while (heapSize) {
    uint16_t cur = popHeap();
    if (state[cur] == 2) continue;
    state[cur] = 2;
    expandedNodes++;

    if (cur == goalNode) return reconstruct(startNode);

    int x = getX(cur), y = getY(cur);
    for (int k = 0; k < 4; k++) {
      int nx = x + dx[k], ny = y + dy[k];
      if (nx < 0 || nx >= W || ny < 0 || ny >= H) continue;
      if (grid[ny][nx]) continue;

      uint16_t nb = toID(nx, ny);
      if (state[nb] == 2) continue;

      uint32_t tentative = (uint32_t)gScore[cur] + MOVE_COST;
      if (tentative < gScore[nb]) {
        gScore[nb] = (uint16_t)tentative;
        parentNode[nb] = cur;
        state[nb] = 1;
        insertOrUpdate(nb);
      }
    }
  }
  return false;
}

bool readLine(char *buf, size_t cap) {
  static size_t idx = 0;
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      buf[idx] = '\0';
      idx = 0;
      return true;
    }
    if (idx < cap - 1) buf[idx++] = c;
    else idx = 0;
  }
  return false;
}

void processCommand(char *line) {
  if (strncmp(line, "BEGIN,", 6) == 0) {
    int w, h, sx, sy, gx, gy;
    if (sscanf(line, "BEGIN,%d,%d,%d,%d,%d,%d", &w, &h, &sx, &sy, &gx, &gy) != 6) {
      Serial.println("ERROR,HEADER"); return;
    }
    if (w < 1 || w > MAX_W || h < 1 || h > MAX_H ||
        sx < 0 || sx >= w || gx < 0 || gx >= w ||
        sy < 0 || sy >= h || gy < 0 || gy >= h) {
      Serial.println("ERROR,DIMENSIONS"); return;
    }
    W = w; H = h;
    startNode = toID(sx, sy);
    goalNode = toID(gx, gy);
    memset(grid, 0, sizeof(grid));
    Serial.println("READY");
    return;
  }

  if (strncmp(line, "ROW,", 4) == 0) {
    static uint8_t rowIndex = 0;
    if (rowIndex >= H) rowIndex = 0;
    char *s = line + 4;
    if (strlen(s) != W) { Serial.println("ERROR,ROW_LENGTH"); return; }
    for (uint8_t x = 0; x < W; x++) {
      if (s[x] != '0' && s[x] != '1') { Serial.println("ERROR,CELL"); return; }
      grid[rowIndex][x] = (uint8_t)(s[x] - '0');
    }
    rowIndex++;
    if (rowIndex == H) rowIndex = 0;
    return;
  }

  if (strcmp(line, "END") == 0) {
    uint32_t t0 = micros();
    bool found = solveAStar();
    uint32_t elapsed = micros() - t0;

    Serial.print("RESULT,");
    Serial.print(found ? "OK" : "NO_PATH");
    Serial.print(",");
    Serial.print(found ? gScore[goalNode] : 0);
    Serial.print(",");
    Serial.print(pathLength);
    Serial.print(",");
    Serial.print(expandedNodes);
    Serial.print(",");
    Serial.println(elapsed);

    if (found) {
      for (int i = pathLength - 1; i >= 0; i--) {
        Serial.print("P,");
        Serial.print(getX(path[i]));
        Serial.print(",");
        Serial.println(getY(path[i]));
      }
    }
    Serial.println("DONE");
    return;
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("ASTAR_ESP32_READY");
}

void loop() {
  if (readLine(lineBuffer, sizeof(lineBuffer))) {
    processCommand(lineBuffer);
  }
}
