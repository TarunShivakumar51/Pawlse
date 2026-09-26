# 🐾 Pawlse

Pawlse is a computer vision and signal-processing project that estimates a pet's heart rate from video. The system uses YOLO segmentation to identify the ear region, ByteTrack to maintain the target across frames, and remote photoplethysmography (rPPG) techniques to extract a physiological signal from changes in pixel intensity.

## Overview

The pipeline is:

```text
Pet Video
    ↓
YOLO Segmentation
    ↓
Ear / Region of Interest
    ↓
ByteTrack Tracking
    ↓
Green-Channel Extraction
    ↓
Signal Normalization
    ↓
Butterworth Band-Pass Filter
    ↓
FFT
    ↓
Dominant Frequency
    ↓
Estimated BPM
```

The goal is to explore whether physiological information such as heart rate can be estimated from an ordinary video without requiring a dedicated wearable sensor.

## Features

- YOLO-based segmentation of the target region
- ByteTrack object tracking
- Green-channel rPPG signal extraction
- Butterworth band-pass filtering
- FFT-based frequency analysis
- BPM estimation from dominant frequency
- FastAPI backend
- S3-compatible video upload workflow using presigned URLs
- Browser-based upload interface

## How It Works

### 1. Video Input

Pawlse processes a video frame-by-frame using OpenCV.

Each frame is passed through the trained YOLO segmentation model.

### 2. YOLO Segmentation

The project uses a trained model stored as:

```text
best.pt
```

The model identifies the target ear region and provides a segmentation mask rather than relying only on a bounding box.

The mask allows the system to isolate the relevant pixels before extracting the physiological signal.

### 3. ByteTrack

Pawlse uses ByteTrack to maintain a consistent detection across consecutive frames.

The tracking pipeline uses:

```python
results = model.track(
    frame,
    persist=True,
    conf=0.25,
    max_det=1,
    tracker="bytetrack.yaml",
    verbose=False
)
```

Using `persist=True` allows detections to maintain their identity across frames.

The current pipeline is configured for a single target with:

```text
max_det = 1
```

### 4. Region of Interest

The YOLO segmentation mask is converted into a binary mask and applied to the original frame.

Conceptually:

```text
Original Frame
      ↓
YOLO Segmentation
      ↓
Binary Mask
      ↓
Target Region
```

This prevents unrelated background pixels from contributing to the extracted signal.

### 5. Green-Channel Extraction

The masked region is separated into its color channels.

The green channel is used to construct the rPPG signal.

For every frame, the average value of the relevant green-channel pixels is calculated. Repeating this process across the video produces a one-dimensional signal that changes over time.

```text
Frame 1 → Green Mean
Frame 2 → Green Mean
Frame 3 → Green Mean
   ...
Frame N → Green Mean

        ↓

Green-Channel Time Series
```

Small periodic changes in this signal can contain information related to blood-volume changes.

### 6. Signal Processing

The extracted signal is normalized and passed through a Butterworth band-pass filter.

The current filter range is approximately:

```text
1.0 Hz → 3.33 Hz
```

Since:

```text
BPM = Hz × 60
```

this corresponds to approximately:

```text
60 BPM → 200 BPM
```

The filter helps remove frequencies outside the target heart-rate range.

### 7. FFT and BPM Estimation

After filtering, Pawlse computes the Fast Fourier Transform (FFT).

The frequency with the strongest magnitude within the filtered range is selected as the dominant frequency.

The frequency is then converted to beats per minute:

```python
bpm = dominant_frequency * 60
```

For example:

```text
1.25 Hz × 60 = 75 BPM
```

The resulting estimate would therefore be approximately:

```text
75 BPM
```

## Project Structure

```text
Pawlse/
│
├── backend_shi.py
├── best.pt
│
├── green_channel.py
├── green_channel_v2.py
├── calculate_bpm.py
│
├── index.html
├── upload.js
├── style.css
│
├── requirements.txt
└── README.md
```

### `backend_shi.py`

FastAPI backend responsible for the web API and S3 presigned upload workflow.

### `best.pt`

Trained YOLO model used for segmentation.

### `green_channel.py`

Earlier/experimental version of the computer-vision and green-channel extraction pipeline.

### `green_channel_v2.py`

Updated video-processing pipeline combining YOLO tracking, segmentation masks, and green-channel extraction.

### `calculate_bpm.py`

Contains the signal-processing logic used to transform the extracted green-channel signal into an estimated BPM value.

### `index.html`

Frontend upload page.

### `upload.js`

Frontend JavaScript responsible for interacting with the backend and handling uploads.

### `style.css`

Styling for the web interface.

### `requirements.txt`

Python dependencies required to run the project.

## Technologies

| Component | Technology |
|---|---|
| Language | Python |
| Computer Vision | OpenCV |
| Segmentation | Ultralytics YOLO |
| Object Tracking | ByteTrack |
| Numerical Computing | NumPy |
| Signal Processing | SciPy |
| Backend | FastAPI |
| Server | Uvicorn |
| Object Storage | Amazon S3 |
| Frontend | HTML, CSS, JavaScript |
| Model | PyTorch / YOLO `.pt` |

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/TarunShivakumar51/Pawlse.git
cd Pawlse
```

### 2. Create a virtual environment

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Backend

Start the FastAPI server with:

```bash
uvicorn backend_shi:app --reload
```

The API will normally be available at:

```text
http://127.0.0.1:8000
```

FastAPI's interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Running the Frontend

The frontend consists of:

```text
index.html
upload.js
style.css
```

A simple local HTTP server can be used:

```bash
python -m http.server 5500
```

Then open:

```text
http://127.0.0.1:5500
```

Make sure the frontend is configured to communicate with the FastAPI server running on the appropriate host and port.

## AWS / S3 Configuration

The backend uses S3 presigned URLs for video uploads.

AWS credentials should be configured using a secure method such as:

```bash
aws configure
```

or environment variables / an appropriate IAM role.

Do **not** commit AWS access keys or secret keys to the repository.

The presigned upload URL is temporary and is generated by the backend for the client.

## Example Pipeline

A simplified example of the complete process is:

```python
# 1. Read video frame
frame = ...

# 2. Run YOLO tracking
results = model.track(frame, persist=True)

# 3. Obtain segmentation mask
mask = ...

# 4. Isolate region of interest
roi = cv.bitwise_and(frame, frame, mask=mask)

# 5. Extract green-channel signal
green = ...

# 6. Repeat for every frame
green_signal.append(green)

# 7. Estimate heart rate
bpm = bpm_calculation(green_signal, fps)
```

## Limitations

Pawlse is a research/prototype project and is **not a veterinary or medical diagnostic device**.

The accuracy of camera-based heart-rate estimation can be affected by:

- Pet movement
- Camera movement
- Lighting changes
- Shadows
- Fur covering the target region
- Ear movement
- Occlusion
- Incorrect segmentation
- Tracking failures
- Video compression
- Frame rate
- Recording length
- Motion artifacts
- Physiological variation

The FFT approach also assumes that the strongest frequency within the selected range corresponds to the heart-rate signal. In noisy recordings, this assumption may not hold.

Results should therefore be treated as experimental estimates rather than clinically validated measurements.

## Future Improvements

Potential improvements include:

- Improve the segmentation dataset and model
- Improve robustness to movement and occlusion
- Add signal-quality metrics
- Detect and remove motion artifacts
- Use sliding-window BPM estimation
- Add temporal smoothing
- Compare multiple color channels
- Add real-time webcam processing
- Add live BPM visualization
- Add historical measurements and graphs
- Automate video processing after upload
- Improve cloud deployment and scalability

## Security Considerations

The application is currently designed primarily for development and experimentation.

Before deploying publicly:

- Restrict CORS to trusted frontend origins
- Keep AWS credentials out of source code
- Use appropriate IAM permissions
- Validate uploaded files
- Limit upload sizes
- Validate video formats
- Protect API endpoints as needed
- Use HTTPS in production

## Project Goals

Pawlse combines several areas of software and AI engineering into one end-to-end system:

```text
Computer Vision
       +
Machine Learning
       +
Object Tracking
       +
Signal Processing
       +
Cloud Infrastructure
       +
Web Development
```

The project explores how visual information from ordinary video can be transformed into a physiological signal and ultimately into an estimated heart-rate measurement.

## Author

**Tarun Shivakumar**

Computer Science & Engineering student interested in:

- Computer Vision
- Robotics
- Machine Learning
- Perception Systems
- Signal Processing
- AI Applications

## License

No open-source license is currently specified for this repository.
