"""
✋ Air Sketch — Webcam Hand-Tracking Drawing App
================================================
Controls
--------
  ✏️  Index finger only (other fingers folded)  → Draw / Sketch
  🖐  Open palm (all fingers spread)            → Erase (big circle eraser)
  ✌️  Two fingers up (peace sign)               → Hover / Move without drawing
  [C] key                                        → Clear canvas
  [S] key                                        → Save canvas as sketch_<ts>.png
  [Q] / ESC                                      → Quit
  [+] / [-]                                      → Increase / decrease brush size

Color palette shown top-right; hover your index finger over a swatch for 1 s.
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import os
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
from mediapipe.tasks.python import BaseOptions

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────
MODEL_PATH    = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")
ERASER_RADIUS = 60
BRUSH_SIZE    = 6
HOVER_SECS    = 1.0
CAM_W, CAM_H  = 1280, 720

# BGR colour palette
PALETTE = [
    ("Coral",    (80,  110, 255)),
    ("Sky",      (255, 180,  80)),
    ("Mint",     (120, 220, 120)),
    ("Gold",     ( 40, 200, 230)),
    ("Lavender", (220, 130, 200)),
    ("White",    (255, 255, 255)),
    ("Black",    ( 10,  10,  10)),
]

# Hand landmark indices
WRIST       = 0
INDEX_TIP   = 8
INDEX_MCP   = 5
MIDDLE_TIP  = 12
MIDDLE_MCP  = 9
RING_TIP    = 16
RING_MCP    = 13
PINKY_TIP   = 20
PINKY_MCP   = 17
THUMB_TIP   = 4
THUMB_IP    = 3
PALM_MCP9   = 9   # palm centre proxy

CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),          # thumb
    (0,5),(5,6),(6,7),(7,8),          # index
    (5,9),(9,10),(10,11),(11,12),     # middle
    (9,13),(13,14),(14,15),(15,16),   # ring
    (13,17),(17,18),(18,19),(19,20),  # pinky
    (0,17),                           # palm base
]

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def lm_to_px(landmarks, idx, w, h):
    lm = landmarks[idx]
    return int(lm.x * w), int(lm.y * h)

def fingers_up(landmarks, w, h):
    """Return (thumb, index, middle, ring, pinky) as booleans."""
    def py(i): return landmarks[i].y * h
    def px(i): return landmarks[i].x * w
    thumb  = px(THUMB_TIP)  < px(THUMB_IP)           # mirrored: left = smaller x
    index  = py(INDEX_TIP)  < py(INDEX_MCP)
    middle = py(MIDDLE_TIP) < py(MIDDLE_MCP)
    ring   = py(RING_TIP)   < py(RING_MCP)
    pinky  = py(PINKY_TIP)  < py(PINKY_MCP)
    return thumb, index, middle, ring, pinky

def smooth(prev, curr, alpha=0.55):
    if prev is None:
        return curr
    return (int(alpha * curr[0] + (1 - alpha) * prev[0]),
            int(alpha * curr[1] + (1 - alpha) * prev[1]))

def draw_skeleton(frame, landmarks, w, h, color=(0, 220, 180)):
    pts = [lm_to_px(landmarks, i, w, h) for i in range(21)]
    for a, b in CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], color, 2, cv2.LINE_AA)
    for i, p in enumerate(pts):
        r = 6 if i in (4, 8, 12, 16, 20) else 4
        cv2.circle(frame, p, r, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, p, r, color, 2, cv2.LINE_AA)

def draw_palette(frame, swatches, selected_idx, hover_idx, hover_start):
    sw, sh  = 48, 48
    gap     = 8
    margin  = 16
    total_w = len(swatches) * (sw + gap) - gap
    x0      = frame.shape[1] - total_w - margin
    y0      = margin
    for i, (name, bgr) in enumerate(swatches):
        x = x0 + i * (sw + gap)
        cv2.rectangle(frame, (x - 4, y0 - 4), (x + sw + 4, y0 + sh + 4),
                      (30, 30, 30), -1, cv2.LINE_AA)
        cv2.rectangle(frame, (x, y0), (x + sw, y0 + sh), bgr, -1, cv2.LINE_AA)
        if hover_idx == i and hover_start is not None:
            elapsed = time.time() - hover_start
            angle   = int(360 * min(elapsed / HOVER_SECS, 1.0))
            cx, cy  = x + sw // 2, y0 + sh // 2
            cv2.ellipse(frame, (cx, cy), (sw // 2 + 6, sh // 2 + 6),
                        -90, 0, angle, (255, 255, 255), 3, cv2.LINE_AA)
        if i == selected_idx:
            cv2.rectangle(frame, (x - 6, y0 - 6), (x + sw + 6, y0 + sh + 6),
                          (255, 255, 255), 3, cv2.LINE_AA)
    return x0, y0

def swatch_hit(px_, py_, x0, y0, sw=48, sh=48, gap=8, n=7):
    for i in range(n):
        x = x0 + i * (sw + gap)
        if x <= px_ <= x + sw and y0 <= py_ <= y0 + sh:
            return i
    return -1

def draw_hud(frame, mode, color, brush, fps):
    h, w    = frame.shape[:2]
    strip_h = 58
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - strip_h), (w, h), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
    mc = {"DRAW":(120,220,120),"ERASE":(80,110,255),"HOVER":(230,200,80),"IDLE":(160,160,160)}.get(mode,(200,200,200))
    cv2.putText(frame, f"Mode: {mode}", (20, h - 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.85, mc, 2, cv2.LINE_AA)
    cv2.circle(frame, (295, h - 30), 15, color, -1, cv2.LINE_AA)
    cv2.circle(frame, (295, h - 30), 15, (255,255,255), 1, cv2.LINE_AA)
    cv2.putText(frame, f"Brush: {brush}px", (325, h - 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.72, (200,200,200), 2, cv2.LINE_AA)
    cv2.putText(frame, f"FPS: {fps:.0f}", (w - 130, h - 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.72, (180,180,180), 2, cv2.LINE_AA)
    cv2.putText(frame, "[C] Clear  [S] Save  [+/-] Brush  [Q] Quit",
                (20, h - strip_h + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120,120,120), 1, cv2.LINE_AA)

# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────
def main():
    # ── Build HandLandmarker (video/live mode) ───────────────────────────────
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    landmarker = HandLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)

    ret, frame = cap.read()
    if not ret:
        print("❌  Cannot open camera.")
        landmarker.close()
        return

    h, w   = frame.shape[:2]
    canvas = np.zeros((h, w, 3), dtype=np.uint8)

    prev_pt      = None
    draw_color   = PALETTE[0][1]
    sel_idx      = 0
    brush_size   = BRUSH_SIZE
    hover_swatch = -1
    hover_start  = None

    fps_time   = time.time()
    fps_frames = 0
    fps        = 0.0
    start_time = time.time()   # monotonic clock base for MediaPipe timestamps

    print("🎨  Air Sketch started!")
    print("   ✏️  Index finger only  → Draw")
    print("   🖐  Open palm          → Erase")
    print("   ✌️  Two fingers up     → Hover (no draw)")
    print("   Press Q to quit.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame  = cv2.flip(frame, 1)
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ts_ms  = int((time.time() - start_time) * 1000)   # strictly increasing ms
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect_for_video(mp_img, ts_ms)

        mode    = "IDLE"
        curr_pt = None

        if result.hand_landmarks:
            landmarks = result.hand_landmarks[0]
            thumb, index, middle, ring, pinky = fingers_up(landmarks, w, h)

            draw_skeleton(frame, landmarks, w, h)

            tip8 = lm_to_px(landmarks, INDEX_TIP, w, h)

            all_open   = all([thumb, index, middle, ring, pinky])
            only_index = (index and not middle and not ring and not pinky)
            two_up     = (index and middle and not ring and not pinky)

            # ── ✏️ DRAW ──────────────────────────────────────────────────
            if only_index:
                mode    = "DRAW"
                curr_pt = smooth(prev_pt, tip8)
                if prev_pt is not None:
                    cv2.line(canvas, prev_pt, curr_pt, draw_color, brush_size, cv2.LINE_AA)
                prev_pt = curr_pt
                cv2.circle(frame, curr_pt, brush_size // 2 + 4, draw_color, -1, cv2.LINE_AA)
                cv2.circle(frame, curr_pt, brush_size // 2 + 4, (255,255,255), 2, cv2.LINE_AA)

            # ── 🖐 ERASE (open palm) ──────────────────────────────────────
            elif all_open:
                mode = "ERASE"
                wx = int((landmarks[WRIST].x + landmarks[PALM_MCP9].x) / 2 * w)
                wy = int((landmarks[WRIST].y + landmarks[PALM_MCP9].y) / 2 * h)
                curr_pt = (wx, wy)
                cv2.circle(canvas, curr_pt, ERASER_RADIUS, (0, 0, 0), -1)
                cv2.circle(frame, curr_pt, ERASER_RADIUS, (80, 110, 255), 3, cv2.LINE_AA)
                cv2.circle(frame, curr_pt, ERASER_RADIUS, (255,255,255), 1, cv2.LINE_AA)
                cv2.putText(frame, "ERASE",
                            (curr_pt[0] - 32, curr_pt[1] - ERASER_RADIUS - 14),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.85, (80,110,255), 2, cv2.LINE_AA)
                prev_pt = None

            # ── ✌️ HOVER ──────────────────────────────────────────────────
            elif two_up:
                mode    = "HOVER"
                curr_pt = smooth(prev_pt, tip8)
                cv2.circle(frame, curr_pt, 10, (230,200,80), -1, cv2.LINE_AA)
                cv2.circle(frame, curr_pt, 10, (255,255,255), 2, cv2.LINE_AA)
                prev_pt = None

            else:
                prev_pt = None

            # ── Palette hover selection ───────────────────────────────────
            total_w = len(PALETTE) * (48 + 8) - 8
            pal_x0  = w - total_w - 16
            pal_y0  = 16
            if curr_pt:
                hi = swatch_hit(curr_pt[0], curr_pt[1], pal_x0, pal_y0, n=len(PALETTE))
                if hi >= 0:
                    if hover_swatch != hi:
                        hover_swatch = hi
                        hover_start  = time.time()
                    elif time.time() - hover_start >= HOVER_SECS:
                        sel_idx    = hi
                        draw_color = PALETTE[hi][1]
                        hover_start = time.time()
                else:
                    hover_swatch = -1
                    hover_start  = None
        else:
            prev_pt = None

        # ── Composite canvas over webcam ───────────────────────────────────
        gray     = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        _, mask  = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        bg       = cv2.bitwise_and(frame, frame, mask=mask_inv)
        fg       = cv2.bitwise_and(canvas, canvas, mask=mask)
        frame    = cv2.addWeighted(bg, 1.0, fg, 0.92, 0)

        # ── UI ────────────────────────────────────────────────────────────
        draw_palette(frame, PALETTE, sel_idx, hover_swatch, hover_start)
        fps_frames += 1
        if time.time() - fps_time >= 0.5:
            fps        = fps_frames / (time.time() - fps_time)
            fps_time   = time.time()
            fps_frames = 0
        draw_hud(frame, mode, draw_color, brush_size, fps)

        cv2.imshow("✋ Air Sketch", frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q'), 27):
            break
        elif key in (ord('c'), ord('C')):
            canvas[:] = 0
            print("🧹  Canvas cleared.")
        elif key in (ord('s'), ord('S')):
            fname = f"sketch_{int(time.time())}.png"
            cv2.imwrite(fname, canvas)
            print(f"💾  Saved → {fname}")
        elif key in (ord('+'), ord('=')):
            brush_size = min(brush_size + 2, 40)
        elif key == ord('-'):
            brush_size = max(brush_size - 2, 2)

    cap.release()
    cv2.destroyAllWindows()
    landmarker.close()
    print("👋  Bye!")


if __name__ == "__main__":
    main()
