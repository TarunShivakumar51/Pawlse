from ultralytics import YOLO
import cv2 as cv
import numpy as np
import time
import sys
import matplotlib.pyplot as plt
import calculate_bpm

if __name__ == '__main__':
    model = YOLO("best.pt")

    cap = cv.VideoCapture(0)
    name = "Webcam"

    locked_det_id = None
    collecting_data = False
    start_time = sys.maxsize
    green_channel_mean = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        key = cv.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('u'):
            locked_det_id = None
            collecting_data = False
            green_channel_mean.clear()
            start_time = time.perf_counter()

        results = model.track(
            frame,
            persist=True,
            conf=0.25,
            max_det=1,
            tracker="bytetrack.yaml",
            verbose=False
        )

        boxes = results[0].boxes
        masks = results[0].masks

        out = frame.copy()

        if key == ord('l') and locked_det_id is None:
            if boxes.id is None:
                cv.putText(
                    out,
                    "No track IDs yet — try again",
                    (20, 40),
                    cv.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2
                )
            else:
                best_det_idx = int(boxes.conf.argmax())
                locked_det_id = int(boxes.id[best_det_idx])

                text_size = cv.getTextSize(
                    "Status: Finding BPM",
                    cv.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    2
                )[0]

                text_x = (out.shape[1] - text_size[0]) // 2

                cv.putText(
                    out,
                    "Status: Finding BPM",
                    (text_x, 40),
                    cv.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 255),
                    2
                )

                start_time = time.perf_counter()
                collecting_data = True

        ids_in_frame = []

        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            tid = int(box.id[0]) if box.id is not None else None

            if tid is not None:
                ids_in_frame.append(tid)

            if locked_det_id is not None and tid != locked_det_id:
                continue

            color = (0, 255, 0) if locked_det_id is not None else (255, 255, 255)
            prefix = "LOCKED " if locked_det_id is not None else ""
            label = f"{prefix}ID {tid} {conf:.2f}" if tid is not None else f"{conf:.2f}"

            cv.rectangle(out, (x1, y1), (x2, y2), color, 2)
            cv.putText(out, label, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        if locked_det_id is not None and locked_det_id not in ids_in_frame:
            cv.putText(
                out,
                "TARGET LOST",
                (20, 40),
                cv.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )
            start_time = time.perf_counter()
            green_channel_mean.clear()
            collecting_data = False

        elif locked_det_id is not None and locked_det_id in ids_in_frame and not collecting_data:
            collecting_data = True
            start_time = time.perf_counter()

        overlaid_img = out.copy()

        if collecting_data:

            overlay = out.copy()
            seg_area_cords = []

            if results[0].masks is not None:
                seg_area_cords = results[0].masks.xy

            green_fn = (0, 255, 0)

            seg_area_numpy = np.array(seg_area_cords, dtype=np.int32)

            if len(seg_area_cords) > 0:
                frame_array = np.zeros(frame.shape[:2], dtype=np.uint8)
                frame_mask = cv.fillPoly(frame_array, seg_area_numpy, 255)
                roi = cv.bitwise_and(frame, frame, mask=frame_mask)

            if seg_area_cords is not None:
                segmented_array = cv.fillPoly(overlay, seg_area_numpy, color=green_fn)
                overlaid_img = cv.addWeighted(out, 0.7, segmented_array, 0.3, 0)
            else:
                overlaid_img = out

            blue, green, red = cv.split(roi)
            green[green > 0]

            green_array = np.array(green)
            green_array_mean = np.mean(green_array)
            green_channel_mean.append(green_array_mean)

        cv.setWindowTitle(
            name,
            f"Webcam — LOCKED: {locked_det_id}" if locked_det_id else "Webcam"
        )

        cv.imshow(name, overlaid_img)

        if time.perf_counter() - start_time >= 15:
            break
    
    green_channel_mean = np.array(green_channel_mean)
    cap.release()
    cv.destroyAllWindows()

    bpm = calculate_bpm(green_channel_mean, cap.get(cv.CAP_PROP_FPS))