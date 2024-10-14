import librosa
import numpy as np
import cv2
from random import randrange
from moviepy.editor import AudioFileClip, VideoFileClip
# from waveform import progressbar

def get_beat_timestamps(file_path):
    # Load the audio file
    y, sr = librosa.load(file_path)

    # Use librosa's beat detection
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

    # Convert beat frames to timestamps
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    return beat_times

class backgrounds:
    def __init__(self):
        pass

    def background_generator(file_path, fps=12, width=640, height=480):
        global audio_clip
        audio_clip = AudioFileClip(file_path)
        
        beat_times = get_beat_timestamps(file_path)

        frame_count = int(audio_clip.duration*fps)
        for i in range(frame_count):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            current_time = i / fps
            if any(abs(current_time - beat_time) < 1/fps for beat_time in beat_times):
                frame[:] = (randrange(255), randrange(255), randrange(255))
            yield frame 

    def close():
        audio_clip.close()