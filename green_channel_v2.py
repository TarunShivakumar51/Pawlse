from ultralytics import YOLO
import cv2 as cv
import numpy as np
import calculate_bpm
import asyncio

def find_green_channel(video_path, event):
    model = YOLO("best.pt")

    cap = cv.VideoCapture(video_path)

    green_channel_mean = []

    while cap.isOpened():
        ret, frame = cap.read()
        
        if not ret or event.is_set():
            break

        results = model.track(
            frame,
            persist=True,
            conf=0.25,
            max_det=1,
            tracker="bytetrack.yaml",
            verbose=False
        )

        if results[0].masks is not None:
            seg_area_cords = results[0].masks.xy

            seg_area_numpy = np.array(seg_area_cords, dtype=np.int32)

            if len(seg_area_cords) > 0:
                frame_array = np.zeros(frame.shape[:2], dtype=np.uint8)
                frame_mask = cv.fillPoly(frame_array, seg_area_numpy, 255)
                roi = cv.bitwise_and(frame, frame, mask=frame_mask)

            blue, green, red = cv.split(roi)
            green = green[green > 0]

            green_array = np.array(green)
            green_array_mean = np.mean(green_array)
            green_channel_mean.append(green_array_mean)

    green_channel_mean = np.array(green_channel_mean)
    bpm = calculate_bpm.bpm_calculation(green_channel_mean, cap.get(cv.CAP_PROP_FPS)) 

    cap.release()

    return bpm       

           