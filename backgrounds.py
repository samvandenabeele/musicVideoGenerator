import librosa
import numpy as np
import cv2
from random import randrange
from moviepy.editor import AudioFileClip, VideoFileClip

def get_beat_timestamps(file_path):
    # Load the audio file
    y, sr = librosa.load(file_path)

    # Use librosa's beat detection
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

    # Convert beat frames to timestamps
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    return beat_times

def create_video(file_path, fps=12, width=640, height=480):
    audio_clip = AudioFileClip(file_path)
    
    beat_times = get_beat_timestamps(file_path)
    out = cv2.VideoWriter('output_waveform_temp.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, (640, 480))

    frame_count = int(audio_clip.duration*fps) + 1
    for i in range(frame_count):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        current_time = i / fps
        if any(abs(current_time - beat_time) < 1/fps for beat_time in beat_times):
            frame[:] = (randrange(255), randrange(255), randrange(255))
        out.write(frame)
    out.release()

    video_clip = VideoFileClip('output_waveform_temp.mp4')

    print(f"Audio duration: {audio_clip.duration}")
    print(f"Video duration: {video_clip.duration}")

    # Adjust video duration to match the audio duration
    final_duration = min(audio_clip.duration, video_clip.duration)
    print(f"Final duration: {final_duration}")
    final_clip = video_clip.set_audio(audio_clip.subclip(0, final_duration))
    
    final_clip.write_videofile("backgrounds.mp4", codec="libx264", fps=fps, audio_codec='aac', temp_audiofile='temp-audio.m4a', remove_temp=True)
    video_clip.close()

if __name__ == "__main__":
    file_path = 'soundscape.mp3'
    create_video(file_path)