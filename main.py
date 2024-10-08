import numpy as np
import cv2
from scipy.io import wavfile
from pydub import AudioSegment
from moviepy.editor import AudioFileClip, VideoFileClip
from concurrent.futures import ThreadPoolExecutor
import os

def progressbar(progress, total):
    percentage = (progress / total) * 100
    bar_length = 40
    filled_length = int(bar_length * progress / total)
    bar = '*' * filled_length + '-' * (bar_length - filled_length)
    print(f'\r|{bar}| {progress}/{total} | {percentage:.2f}%', end='\r')

def mp3_to_wav(mp3_filename):
    audio = AudioSegment.from_mp3(mp3_filename)
    wav_filename = mp3_filename.replace(".mp3", ".wav")
    audio.export(wav_filename, format="wav")
    return wav_filename

def generate_waveform_frame(samples, width, height):
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    for x in range(len(samples) - 1):
        start_point = (int(x * width / len(samples)), int((1 - samples[x]) * height / 2))
        end_point = (int((x + 1) * width / len(samples)), int((1 - samples[x + 1]) * height / 2))
        cv2.line(frame, start_point, end_point, (255, 255, 255), 1)
    return frame

def frame_generator(wav_filename, sample_rate=44100, frame_rate=24):
    sample_rate, samples = wavfile.read(wav_filename)
    samples_per_frame = int(sample_rate / frame_rate)
    samples = samples / np.max(np.abs(samples), axis=0)  # Normalize the samples
    total_frames = len(samples) // samples_per_frame
    height, width = 480, 640  # Frame size

    if total_frames == 0:
        print("Warning: Not enough samples to generate any frames.")
        return

    for frame_number in range(total_frames):
        start_idx = frame_number * samples_per_frame
        end_idx = start_idx + samples_per_frame
        # print(f"Generating frame {frame_number + 1}/{total_frames}")  # Debugging statement
        yield generate_waveform_frame(samples[start_idx:end_idx], width, height), frame_number + 1, total_frames

def create_waveform_video(mp3_filename, frame_gen, output_video_filename, frame_rate=24):
    try:
        first_frame, _, _ = next(frame_gen)
    except StopIteration:
        print("Error: No frames generated.")
        return

    height, width, _ = first_frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_filename, fourcc, frame_rate, (width, height))

    frame_count = 0
    for frame, frame_number, total_frames in frame_gen:
        progressbar(frame_number, total_frames)
        out.write(frame)
        progressbar(frame_number, total_frames)
        frame_count += 1


    out.release()

    if frame_count == 0:
        print("Error: No frames were written to the video.")
        return

    audio_clip = AudioFileClip(mp3_filename)
    video_clip = VideoFileClip(output_video_filename)

    print(f"Audio duration: {audio_clip.duration}")
    print(f"Video duration: {video_clip.duration}")

    # Adjust video duration to match the audio duration
    final_duration = min(audio_clip.duration, video_clip.duration)
    print(f"Final duration: {final_duration}")
    final_clip = video_clip.set_audio(audio_clip.subclip(0, final_duration))
    
    final_clip.write_videofile("soundscape.mp4", codec="libx264", fps=frame_rate, audio_codec='aac', temp_audiofile='temp-audio.m4a', remove_temp=True)
    os.remove('soundscape.wav')
    os.remove('output_waveform_temp.mp4')

def generate_waveform_video(mp3_filename, output_video_filename="output_waveform_temp.mp4"):
    if not os.path.isfile(mp3_filename):
        print(f"Error: The file '{mp3_filename}' does not exist.")
        return

    wav_filename = mp3_to_wav(mp3_filename)
    frames = frame_generator(wav_filename)
    create_waveform_video(mp3_filename, frames, output_video_filename)
    print(f"Video saved as {output_video_filename}")

if __name__ == "__main__":
    mp3_filename = input("Enter the path to the MP3 file: ").strip()
    generate_waveform_video(mp3_filename)
    
