import argparse
import subprocess
import sys
import shlex
import os
import json
# Supported commands
SUPPORTED = {
    "speed":          ["audio", "video"],
    "pitch":          ["audio", "video"],
    "reverb":         ["audio", "video"],
    "reverse":        ["audio", "video"],
    "volume":         ["audio", "video"],
    "bass":           ["audio", "video"],
    "mute":           ["audio", "video"],
    "hflip":          ["video"],
    "vflip":          ["video"],
    "watermark":      ["video"],
    "invert":         ["video"],
    "contrast":       ["video"],
    "grayscale":      ["video"],
    "brightness":     ["video"],
    "saturation":     ["video"],
    "pixelate":       ["video"],
    "repu":           ["video"],
    "blur":           ["video"],
    "fps":            ["video"],
    "sepia":          ["video"],
    "rlag":           ["video"],
    "shake":          ["video"],
    "fisheye":        ["video"],
    "deepfry":        ["video"],
    "hue":            ["video"],
    "huesaturation":  ["video"],
}

AUDIO_EXTS = (".wav", ".mp3", ".flac", ".ogg", ".m4a")
VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".avi", ".webm")

def run_cmd(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print("Error running command:", e, file=sys.stderr)
        sys.exit(1)

def get_file_type(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in AUDIO_EXTS:
        return "audio"
    elif ext in VIDEO_EXTS:
        return "video"
    else:
        return "unknown"

def ffprobe(file_path):
    """
    Runs ffprobe on a file and returns the output as a Python dictionary.
    """
    command_array = [
        "ffprobe", 
        "-v", "quiet",  # Suppress logging to stderr
        "-print_format", "json",  # Output in JSON format
        "-show_format",  # Show format information
        "-show_streams",  # Show stream information
        str(file_path)  # File path
    ]

    try:
        result = subprocess.run(
            command_array, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,  # For Python 3.7+; use universal_newlines=True for older versions
            check=True  # Raise CalledProcessError if the command fails
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running ffprobe: {e}")
        print(f"Stderr: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Error: ffprobe command not found. Make sure it's installed and in your PATH.")
        return None

def constrain(val, min_val, max_val):
    if val == None:
        return None
    if type(val)     == str:
        val     = int(val    )
    if type(min_val) == str:
        min_val = float(min_val)
    if type(max_val) == str:
        max_val = float(max_val)
    return min(max_val, max(min_val, val))

def build_pipeline(commands, input_file, output_file):
    print(f"Args: {commands}")
    file_type = get_file_type(input_file)
    if file_type == "unknown":
        print(f"Error: unsupported input file type: {os.path.splitext(input_file)[1]}")
        sys.exit(1)

    audio_effects = []
    video_filters = []

    for cmd, val in commands.items():
        # Validate supported commands
        if cmd not in SUPPORTED:
            print(f"Error: unknown command: {cmd}")
            sys.exit(1)
        if file_type not in SUPPORTED[cmd]:
            print(f"Error: command {cmd} does not support {file_type} file type")
            sys.exit(1)

        # --- AUDIO (SoX for audio files, FFmpeg for video) ---
        if cmd == "speed":
            if file_type == "audio":
                audio_effects.append(f"speed {val}")
            else:  # video
                video_filters.append(f"setpts={1/float(val)}*PTS")
                audio_effects.append(f"atempo={val}")

        elif cmd == "pitch":
            if file_type == "audio":
                audio_effects.append(f"rubberband=pitch={(float(val)/100)+1}")
            else:
                audio_effects.append(f"rubberband=pitch={(float(val)/100)+1}")

        elif cmd == "reverb":
            if file_type == "audio":
                audio_effects.append(f"aecho=0.8:0.9:{val}:0.3")
            else:
                audio_effects.append(f"aecho=0.8:0.9:{val}:0.3")

        elif cmd == "reverse":
            if file_type == "audio":
                audio_effects.append(f"areverse")
            else:
                video_effects.append(f"reverse")
                audio_effects.append(f"areverse")

        elif cmd == "volume":
            audio_effects.append(f"volume={(float(val)/500)*2}")

        elif cmd == "bass":
            audio_effects.append(f"equalizer=f=60:t=q:w=1:g={(float(val)*0.5)}")

        elif cmd == "mute":
            audio_effects.append("volume=0")

        # --- VIDEO ---
        elif cmd == "hflip":
            video_filters.append("hflip")
        elif cmd == "fps":
            video_filters.append(f"fps=fps={val}")
        elif cmd == "watermark":
            print("NOT IMPLEMENT")
        elif cmd == "vflip":
            video_filters.append("vflip")
        elif cmd == "invert":
            video_filters.append("negate")
        elif cmd == "contrast":
            video_filters.append(f"eq=contrast={(float(val)/100)}")
        elif cmd == "brightness":
            video_filters.append(f"eq=brightness={(float(val)/100)}")
        elif cmd == "saturation":
            video_filters.append(f"eq=saturation={(float(val)/100)}")
        elif cmd == "pixelate":
            video_filters.append(f"scale=iw/{val}:ih/{val},scale=iw:ih:flags=neighbor")
        elif cmd == "blur":
            video_filters.append(f"boxblur={val}:1")
        elif cmd == "sepia":
            video_filters.append(f"colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131")
        elif cmd == "rlag":
            video_filters.append(f"random={val}")
        elif cmd == "hue":
            val = constrain(val,-180,180)
            video_filters.append(f"hue=h={val}")
        elif cmd == "deepfry":
            val = constrain(val,-100,100) / 10
            video_filters.append(f"hue=s={val}")
        elif cmd == "huesaturation":
            val = constrain(val,-180,180)
            video_filters.append(f"huesaturation={val}:0.1:0:-100:100,format=yuv420p")
        elif cmd == "shake":
            video_filters.append(f"crop='iw/{val}:ih/{val}:(random(0)*2-1)*in_w:(random(0)*2-1)*in_h',scale=iw*{val}:ih*{val},setsar=1:1")
        elif cmd == "fisheye":
            probe = ffprobe(input_file)
            video_filters.append(f"v360=input=e:output=ball,scale={probe['streams'][0]['width']}:{probe['streams'][0]['height']},setsar=1:1")
        elif cmd == "grayscale":
            video_filters.append("hue=s=0")

    # Build command
    if file_type == "audio":
        return f"sox {shlex.quote(input_file)} {shlex.quote(output_file)} " + " ".join(audio_effects)

    if file_type == "video":
        vf = f"-vf \"{','.join(video_filters)}\"" if video_filters else ""
        af = f"-af \"{','.join(audio_effects)}\"" if audio_effects else ""
        return f"ffmpeg -loglevel quiet -y -i {shlex.quote(input_file)} {vf} {af} -c:v libx264 -c:a aac {shlex.quote(output_file)}"

def parse_command_string(cmd_string):
    commands = {}
    if "," in cmd_string:
      for part in cmd_string.split(","):
        if "=" in part:
          key, val = part.split("=", 1)
          commands[key.strip().lower()] = val.strip()
        else:
          commands[part.strip().lower()] = "1"
    else:
      for part in cmd_string.split("|"):
        if "=" in part:
          key, val = part.split("=", 1)
          commands[key.strip().lower()] = val.strip()
        else:
          commands[part.strip().lower()] = "1"
    return commands

def main():
    parser = argparse.ArgumentParser(
        prog="Universal VideoEditor Platform",
        description="Video/Audio editing CLI, easy to port"
    )
    parser.add_argument("-i", "--input", required=True, help="Input media file")
    parser.add_argument("commands", help='Command string, e.g. "speed=1.5,contrast=2,hflip=1"')
    parser.add_argument("output", help="Output file")
    args = parser.parse_args()

    commands = parse_command_string(args.commands)
    cmd = build_pipeline(commands, args.input, args.output)
    run_cmd(cmd)

if __name__ == "__main__":
    main()
