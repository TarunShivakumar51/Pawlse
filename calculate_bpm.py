import numpy as np
import scipy as sci
from scipy.signal import butter, sosfiltfilt
import matplotlib.pyplot as plt

def bpm_calculation(green_channel, fps):

    green_channel_mean = np.mean(green_channel)
    green_channel_std = np.std(green_channel)

    green_channel = green_channel - green_channel_mean
    green_channel = green_channel / green_channel_std

    low_cutoff = 1.0
    high_cutoff = 3.33

    sos = butter(5, [low_cutoff, high_cutoff], btype='band', fs=fps, output="sos")
    green_channel_filtered = sosfiltfilt(sos, green_channel)

    green_channel_fft = np.abs(np.fft.rfft(green_channel_filtered))
    green_channel_rfft = np.fft.rfftfreq(len(green_channel_filtered), d=1/fps)
    
    green_channel_fft = np.delete(green_channel_fft, 0)
    green_channel_rfft = np.delete(green_channel_rfft, 0)
    green_channel_hz = green_channel_rfft[np.argmax(green_channel_fft)]

    bpm = green_channel_hz * 60

    return bpm


    



