import numpy as np
import cv2
from scipy.io import wavfile
from pydub import AudioSegment
from moviepy.editor import AudioFileClip, VideoFileClip
from concurrent.futures import ThreadPoolExecutor
import os
from scripts.backgrounds import backgrounds as bg

def progressbar(progress, total):
    percentage = (progress / total) * 100
    bar_length = 40
    filled_length = int(bar_length * progress / total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f'\r|{bar}| {progress}/{total} | {percentage:.2f}%', end='\r')
    if round(percentage, 2) == 100.00:
        print()

def mp3_to_wav(mp3_filename):
    audio = AudioSegment.from_mp3(mp3_filename)
    wav_filename = mp3_filename.replace(".mp3", ".wav")
    audio.export(wav_filename, format="wav")
    return wav_filename

def generate_waveform_frame(samples, generator, width, height, fps):
    frame = np.zeros((height*2, width*2, 3), dtype=np.uint8)
    frame = next(generator)
    for x in range(len(samples) - 1):
        start_point = (int(x * width * 2 / len(samples)), int((1 - samples[x]) * height))
        end_point = (int((x + 1) * width * 2 / len(samples)), int((1 - samples[x + 1]) * height))
        cv2.line(frame, start_point, end_point, (255, 255, 255), 1)
    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)
    _, frame = cv2.threshold(frame, 10, 255, cv2.THRESH_BINARY)
    return frame

def frame_generator(wav_filename, sample_rate=44100, frame_rate=12, sub_frame_rate=2):
    height, width = 480, 640  # Frame size
    bg_gen = bg.background_generator('data/videos/soundscape.wav', fps=frame_rate * (sub_frame_rate + 1), width=width*2, height=height*2)
    sample_rate, samples = wavfile.read(wav_filename)
    samples_per_frame = int(sample_rate / frame_rate)
    samples = samples / np.max(np.abs(samples), axis=0)  # Normalize the samples
    total_frames = len(samples) // samples_per_frame

    if total_frames == 0:
        print("Warning: Not enough samples to generate any frames.")
        return

    for frame_number in range(total_frames):
        subframe_step = samples_per_frame // (sub_frame_rate+1)
        frames = []
        start_idx = frame_number * samples_per_frame
        end_idx = start_idx + samples_per_frame
        
        frame = generate_waveform_frame(samples[start_idx:end_idx], bg_gen, width, height, fps=frame_rate*(sub_frame_rate+1))
        frames.append(frame)

        for sub_frame_number in range(sub_frame_rate):
            start_idx += subframe_step
            end_idx += subframe_step
            frame = generate_waveform_frame(samples[start_idx:end_idx], bg_gen, width, height, fps=frame_rate*(sub_frame_rate+1))
            frames.append(frame)

        yield frames, (frame_number+1)*(sub_frame_rate + 1), total_frames*(sub_frame_rate+1)

def create_waveform_video(mp3_filename, frame_gen, callback, output_video_filename="data/videos/output.mp4", frame_rate=12, sub_frame_rate=2):
    try:
        frames, _, _ = next(frame_gen)
    except StopIteration:
        print("Error: No frames generated.")
        return

    height, width, _ = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    print(output_video_filename)
    print(type(output_video_filename))
    out = cv2.VideoWriter(output_video_filename, fourcc, frame_rate*(sub_frame_rate+1), (width, height))

    frame_count = 0
    for frame in frames:
        out.write(frame)
        frame_count += 1

    for frames, frame_number, total_frames in frame_gen:
        for frame in frames:
            out.write(frame)
        frame_count += 1
        progressbar(frame_number, total_frames)
        callback(frame_number, total_frames)


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
    
    final_clip.write_videofile("soundscape.mp4", codec="libx264", fps=frame_rate*(sub_frame_rate+1), audio_codec='aac', temp_audiofile='temp-audio.m4a', remove_temp=True)
    video_clip.close()
    bg.close()
    os.remove('data/videos/soundscape.wav')
    # os.remove('data/videos/output_waveform_temp.mp4')

def generate_waveform_video(mp3_filename, callback, output_video_filename="data/videos/output.mp4", frame_rate=12, sub_frame_rate=2):
    if not os.path.isfile(mp3_filename):
        print(f"Error: The file '{mp3_filename}' does not exist.")
        return

    wav_filename = mp3_to_wav(mp3_filename)
    frames = frame_generator(wav_filename, frame_rate=frame_rate, sub_frame_rate=sub_frame_rate)
    create_waveform_video(mp3_filename, frames, callback, frame_rate=frame_rate, sub_frame_rate=sub_frame_rate)
    print(f"Video saved as {output_video_filename}")

if __name__ == "__main__":
    mp3_filename = input("Enter the path to the MP3 file: ").strip()
    frame_rate = int(input("Enter the frame rate: ").strip())
    sub_frame_rate = int(input("Enter the sub-frame rate: ").strip())
    generate_waveform_video(mp3_filename, frame_rate=frame_rate, sub_frame_rate=sub_frame_rate)
    
