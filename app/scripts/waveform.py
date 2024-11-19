import numpy as np #type: ignore
import cv2 #type: ignore
from scipy.io import wavfile #type: ignore
from pydub import AudioSegment #type: ignore
from moviepy.editor import AudioFileClip, VideoFileClip #type: ignore
import os
from app.scripts.backgrounds import backgrounds as bg


def mp3_to_wav(mp3_filename, callback):
    audio = AudioSegment.from_mp3(mp3_filename)
    callback(1, 3, "converting mp3 to wav")
    wav_filename = mp3_filename.replace('.mp3', '.wav')
    callback(2, 3, "converting mp3 to wav")
    audio.export(wav_filename, format="wav")
    callback(3, 3, "converting mp3 to wav")
    del audio
    return wav_filename

def generate_waveform_frame(samples, generator, width, height, fps):
    frame = next(generator)
    for x in range(len(samples) - 1):
        start_point = (int(x * width * 2 / len(samples)), int((1 - float(samples[x, 0])) * height))
        end_point = (int((x + 1) * width * 2 / len(samples)), int((1 - samples[x + 1, 0]) * height))
        cv2.line(frame, start_point, end_point, (255, 255, 255), 1)
    _, frame = cv2.threshold(frame, 10, 255, cv2.THRESH_BINARY)
    return frame

def frame_generator(wav_filename, callback, sample_rate=44100, frame_rate=12, sub_frame_rate=2):
    height, width = 480, 640  # Frame size
    bg_gen = bg.background_generator(wav_filename, fps=frame_rate * (sub_frame_rate + 1), width=width*2, height=height*2)
    sample_rate, samples = wavfile.read(wav_filename)
    samples_per_frame = int(sample_rate / frame_rate)
    samples = samples / np.max(np.abs(samples), axis=0)  # Normalize the samples
    total_frames = len(samples) // samples_per_frame

    if total_frames == 0:
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
        print("Error: No frames generated.", flush=True)
        return

    height, width, _ = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_filename[:-4] + "temp" + output_video_filename[-4:], fourcc, frame_rate * (sub_frame_rate + 1), (width, height))

    frame_count = 0
    for frame in frames:
        out.write(frame)
    frame_count += 1
    for new_frames, frame_number, total_frames in frame_gen:
        for frame in new_frames:
            out.write(frame)
        frame_count += 1
        callback(frame_number+1, total_frames, "generating frames")

    out.release()

    if frame_count == 0:
        print("Error: No frames were written to the video.", flush=True)
        return

    audio_clip = AudioFileClip(mp3_filename)
    video_clip = VideoFileClip(output_video_filename[:-4] + "temp" + output_video_filename[-4:])

    final_duration = min(audio_clip.duration, video_clip.duration)
    video_clip = video_clip.set_audio(audio_clip.subclip(0, final_duration))

    video_clip.write_videofile(output_video_filename, codec="libx264", fps=frame_rate*(sub_frame_rate+1), audio_codec='aac', temp_audiofile='temp-audio.m4a', remove_temp=True)
    file_directorys = os.listdir("data/videos")
    print(file_directorys)
    for file in file_directorys:
        try:
            if file != os.path.basename(output_video_filename):
                os.remove(os.path.join("data/videos", file))
        except:
            print(f"Error: Could not delete file {file}.", flush=True)
    video_clip.close()

def generate_waveform_video(mp3_filename, callback, output_video_filename="data/videos/output.mp4", frame_rate=12, sub_frame_rate=2):
    if not os.path.isfile(mp3_filename):
        print(f"Error: The file '{mp3_filename}' does not exist.")
        return

    wav_filename = mp3_to_wav(mp3_filename, callback)
    frames = frame_generator(wav_filename, callback=callback, frame_rate=frame_rate, sub_frame_rate=sub_frame_rate)
    create_waveform_video(mp3_filename, frames, callback, output_video_filename=output_video_filename, frame_rate=frame_rate, sub_frame_rate=sub_frame_rate)

    return