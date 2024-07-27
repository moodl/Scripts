import ffmpeg
import os
import sys

def get_video_duration(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        duration = float(probe['format']['duration'])
        return duration
    except ffmpeg.Error as e:
        print(f"Error probing {file_path}: {e}")
        return 0

def calculate_total_duration_m3u(playlist_file):
    with open(playlist_file, 'r') as file:
        lines = file.readlines()

    total_duration = 0.0

    for line in lines:
        video_file = line.strip()
        if os.path.exists(video_file):
            total_duration += get_video_duration(video_file)
        else:
            print(f"File {video_file} not found.")

    return total_duration

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <playlist.m3u>")
        sys.exit(1)

    playlist_file = sys.argv[1]
    total_duration = calculate_total_duration_m3u(playlist_file)
    print(f"The total duration of the contents in the playlist is {total_duration / 60:.2f} minutes.")