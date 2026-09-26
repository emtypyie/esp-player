import cv2
import numpy as np
import os

# --- CONFIGURATION ---
VIDEO_PATH = "assets/maomao.mp4"  # <-- Your exact video filename
OUTPUT_HEADER = "frames.h"
WIDTH = 128
HEIGHT = 64
MAX_FRAMES = 450                   

def apply_dithering(img):
    h, w = img.shape
    out = img.astype(float)
    for y in range(h):
        for x in range(w):
            old_val = out[y, x]
            new_val = 255 if old_val > 128 else 0
            out[y, x] = new_val
            err = old_val - new_val
            if x + 1 < w:            out[y, x + 1] += err * 7 / 16
            if y + 1 < h and x - 1 >= 0: out[y + 1, x - 1] += err * 3 / 16
            if y + 1 < h:            out[y + 1, x] += err * 5 / 16
            if y + 1 < h and x + 1 < w: out[y + 1, x + 1] += err * 1 / 16
    return np.clip(out, 0, 255).astype(np.uint8)

def process_video():
    if not os.path.exists(VIDEO_PATH):
        print(f"Error: Video file '{VIDEO_PATH}' not found.")
        return

    cap = cv2.VideoCapture(VIDEO_PATH)
    frame_count = 0
    all_frames_data = []

    while cap.isOpened() and frame_count < MAX_FRAMES:
        ret, frame = cap.read()
        if not ret: break

        # 1. Resize & Dither
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Center crop to 2:1 aspect ratio
        h, w = gray.shape
        target_ratio = 2.0
        current_ratio = w / h
        if current_ratio > target_ratio:
            new_w = int(h * target_ratio)
            offset = (w - new_w) // 2
            cropped = gray[:, offset:offset+new_w]
        else:
            new_h = int(w / target_ratio)
            offset = (h - new_h) // 2
            cropped = gray[offset:offset+new_h, :]
            
        resized = cv2.resize(cropped, (WIDTH, HEIGHT), interpolation=cv2.INTER_AREA)
        dithered = apply_dithering(resized)

        # 2. XBM PACKING (LSB First for U8g2)
        packed_frame = []
        for y in range(HEIGHT):
            for x in range(0, WIDTH, 8):
                byte = 0
                for bit in range(8):
                    if dithered[y, x + bit] > 0:
                        # LSB First packing for XBM
                        byte |= (1 << bit)
                packed_frame.append(f"0x{byte:02X}")
        
        all_frames_data.append(packed_frame)
        frame_count += 1

    cap.release()

    # 3. Generate Header
    with open(OUTPUT_HEADER, "w") as f:
        f.write("#ifndef FRAMES_H\n#define FRAMES_H\n\n#include <Arduino.h>\n\n")
        f.write(f"#define FRAME_COUNT {frame_count}\n#define FRAME_WIDTH {WIDTH}\n#define FRAME_HEIGHT {HEIGHT}\n\n")
        
        for i, frame_bytes in enumerate(all_frames_data):
            f.write(f"const unsigned char frame_{i}[] U8X8_PROGMEM = {{\n  " + ", ".join(frame_bytes) + "\n};\n\n")
            
        f.write("const unsigned char* const video_frames[] U8X8_PROGMEM = {\n")
        for i in range(frame_count): f.write(f"  frame_{i},\n")
        f.write("};\n\n#endif\n")

    print(f"Success! XBM format {OUTPUT_HEADER} generated for U8g2.")

if __name__ == "__main__":
    process_video()
