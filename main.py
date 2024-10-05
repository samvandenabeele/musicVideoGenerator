import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from pydub import AudioSegment
from moviepy.editor import ImageSequenceClip, AudioFileClip
import os

# print progress bar
def progressbar(progress, total):
    progress = int(progress)
    total = int(total)
    percentage = (progress / total) * 100
    print(f"\r|{'*'*int(percentage)}{"-"*int(100-percentage)}|{progress}/{total}|{percentage:.2f}", end="\r")

# Convert MP3 to WAV format using pydub
def mp3_to_wav(mp3_filename):
    audio = AudioSegment.from_mp3(mp3_filename)
    wav_filename = mp3_filename.replace(".mp3", ".wav")
    audio.export(wav_filename, format="wav")
    return wav_filename

# Generate frames from audio file
def generate_waveform_frames(wav_filename, output_folder, sample_rate=44100, frame_duration=1/24):
    # Read the WAV file
    sr, samples = wavfile.read(wav_filename)

    # Calculate the number of samples per frame
    samples_per_frame = int(sample_rate * frame_duration)
    
    # Normalize the audio samples for plotting
    samples = samples / np.max(np.abs(samples), axis=0)

    # Create frames for each segment of the audio
    frame_paths = []
    progressbar(0, len(samples))
    for i in range(0, len(samples), samples_per_frame):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(samples[i:i + samples_per_frame])
        ax.set_xlim([0, samples_per_frame])
        ax.set_ylim([-1, 1])
        plt.axis('off')

        # Save the frame as an image
        frame_path = os.path.join(output_folder, f"frame_{i}.png")
        plt.savefig(frame_path)
        plt.close(fig)
        frame_paths.append(frame_path)
        progressbar(i, len(samples))

    print("\nFrames generated")
    return frame_paths

# Create a video from frames
def create_waveform_video(mp3_filename, frame_paths, output_video_filename, frame_rate=24):
    # Generate video clip from image frames
    clip = ImageSequenceClip(frame_paths, fps=frame_rate)
    
    # Add the original audio to the clip
    audio_clip = AudioFileClip(mp3_filename)
    final_clip = clip.set_audio(audio_clip)

    # Write the result to a video file
    final_clip.write_videofile(output_video_filename, codec="libx264", fps=frame_rate)

# Main function
def generate_waveform_video(mp3_filename, output_video_filename="output_waveform.mp4"):
    # Step 1: Convert MP3 to WAV
    wav_filename = mp3_to_wav(mp3_filename)

    # Step 2: Create an output folder for frames
    output_folder = "waveform_frames"
    os.makedirs(output_folder, exist_ok=True)

    # Step 3: Generate waveform frames
    frame_paths = generate_waveform_frames(wav_filename, output_folder)

    # Step 4: Create and save the video
    create_waveform_video(mp3_filename, frame_paths, output_video_filename)

    # Cleanup: Delete frames
    for frame in frame_paths:
        os.remove(frame)
    print(f"Video saved as {output_video_filename}")

# Run the main function with an example MP3 file
generate_waveform_video(r"C:\Users\SamVandenabeele\OneDrive - Sint-Barbaracollege\Documenten\python\musicVideoGenerator\soundscape.mp3")
