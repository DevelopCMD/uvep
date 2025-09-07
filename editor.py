import argparse
import subprocess
import sys
import shlex
import os
import json
import ffmpeg
from pathHelper import getName
from sfx import addSounds
from moviepy.editor import VideoFileClip, AudioFileClip
from math import floor
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
    "huecycle":       ["video"],
    "huesaturation":  ["video"],
    "abr":            ["video"],
    "vbr":            ["video"],
    "sharpen":        ["video"],
    "sfx":            ["video"],
    "acid":           ["video"],
    "crush":          ["audio","video"],
    "zoom":           ["video"],
    "areverse":       ["audio","video"],
    "vreverse":       ["video"],
}

AUDIO_EXTS = (".wav", ".mp3", ".flac", ".ogg", ".m4a")
VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".avi", ".webm")

def run_cmd(cmd):
    try:
        subprocess.run(shlex.split(cmd), check=True)
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
def listOut(dict,title:str,number:bool=False):
  print(title)
  for k, v in dict.items():
      print(f"- {k}")
def constrain(val, min_val, max_val):
    if val == None:
        return None
    if type(val)     == str:
        val     = float(val)
    if type(min_val) == str:
        min_val = float(min_val)
    if type(max_val) == str:
        max_val = float(max_val)
    return min(max_val, max(min_val, val))
def outputAudio(audio_stream,filename:str):
  ffmpeg.output(audio_stream,f"{filename}.wav",format="wav").run(overwrite_output=True, quiet=True)
def parse(commands, input_file, output_file):
    print(f"Args: {commands}")
    file_type = get_file_type(input_file)
    if file_type == "unknown":
        print(f"Error: unsupported input file type: {os.path.splitext(input_file)[1]}")
        sys.exit(1)
    ab = 64000
    vb = 1500000
    if file_type == "video":
      inp = ffmpeg.input(input_file)
      sfx = None
      aud = inp.audio
      vid = inp.video
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
            vid = vid.setpts(f"{1/float(val)}*PTS")
            aud = aud.filter("atempo",val)

        elif cmd == "pitch":
            aud = aud.filter("rubberband",pitch=(float(val)/100)+1)

        elif cmd == "reverb":
            aud = aud.filter("aecho",0.8,0.9,val,0.3)

        elif cmd == "reverse":
            vid = vid.filter("reverse")
            aud = aud.filter("areverse")

        elif cmd == "volume":
            aud = aud.filter("volume",volume=(float(val)/500)*2)
        elif cmd == "crush":
            val = int(constrain(val,1,100))
            aud = aud.filter("acrusher",samples=floor(val*0.32),bits=4,mix=1)
        elif cmd == "bass":
            aud = aud.filter("equalizer",f=60,t="q",w=1,g=float(val)*0.5)

        elif cmd == "mute":
            aud = aud.filter("volume",volume="0")

        # --- VIDEO ---
        elif cmd == "hflip":
            vid = vid.hflip()
        elif cmd == "fps":
            vid = vid.filter("fps",val)
        elif cmd == "watermark":
            print("NOT IMPLEMENT")
        elif cmd == "vflip":
            vid = vid.vflip()
        elif cmd == "invert":
            vid = vid.filter("negate")
        elif cmd == "contrast":
            vid = vid.filter("eq",contrast=(float(val)/100))
        elif cmd == "brightness":
            vid = vid.filter("eq",brightness=(float(val)/100))
        elif cmd == "saturation":
            vid = vid.filter("eq",saturation=(float(val)/100))
        elif cmd == "pixelate":
            vid = vid.filter("scale",f"iw/{val}",f"ih/{val}")
            vid = vid.filter("scale",f"iw*{val}",f"ih*{val}",sws_flags="neighbor")
        elif cmd == "acid":
            val = constrain(val,0,100)
            vid = vid.filter("amplify",3,val)
        elif cmd == "vreverse":
            vid = vid.filter("reverse")
        elif cmd == "areverse":
            aud = aud.filter("areverse")
        elif cmd == "blur":
            vid = vid.filter("boxblur",val,1)
        elif cmd == "sepia":
            vid = vid.filter("colorchannelmixer",.393,.769,.189,0,.349,.686,.168,0,.272,.534,.131)
        elif cmd == "rlag":
            vid = vid.filter("random",frames=val)
        elif cmd == "hue":
            val = constrain(val,-180,180)
            vid.hue(h=val)
        elif cmd == "hcycle":
            val = constrain(val,1,25)
            vid = vid.hue(h=f"t*360*{val}")
        elif cmd == "sharpen":
            val = int(constrain(val,1,25))
            vid = vid.filter("unsharp",val,val)
        elif cmd == "deepfry":
            val = constrain(val,-100,100) / 10
            vid = vid.hue(s=val)
        elif cmd == "huesaturation":
            val = constrain(val,-180,180)
            vid = vid.filter("huesaturation",val,0.1,0,-100,100)
        elif cmd == "zoom":
            val = constrain(val,1,10)
            vid = vid.filter("scale",f"trunc(iw*{val})",f"trunc(ih*{val})").filter("crop",f"iw/{val}",f"ih/{val}")
        elif cmd == "sfx":
            val = int(constrain(val,1,100))
            outputAudio(aud,f"sfx_{getName(input_file)}")
            addSounds(f"sfx_{getName(input_file)}.wav",val,"backend/sounds")
            sfx = f"sfx_{getName(input_file)}.wav"
        elif cmd == "shake":
            vid = vid.filter("crop","iw/1.1","ih/1.1","(random(0)*2-1)*in_w","(random(0)*2-1)*in_h")
            vid = vid.filter("scale",f"iw*{val}",f"ih*{val}")
            vid = vid.filter("setsar",r=1)
        elif cmd == "fisheye":
            val = int(constrain(val,1,2))
            probe = ffprobe(input_file)
            for i in range(val):
              vid = vid.filter("v360",input="e",output="ball")
              vid = vid.filter("scale",w=probe['streams'][0]['width'],h=probe['streams'][0]['height'])
            vid = vid.filter("setsar",r=1)
        elif cmd == "vbr":
            vb = 100 + 2000 * constrain(100 - float(val),2,100)
        elif cmd == "abr":
            ab = 100 + 2000 * constrain(100 - float(val),2,100)
        elif cmd == "grayscale":
            vid = vid.hue(s=0)

    # Build command
    try:
        ffmpeg.output(vid,aud,output_file,pix_fmt='yuv420p', video_bitrate=vb or 640000, audio_bitrate=ab or 192000).run(overwrite_output=True,quiet=True)
    except ffmpeg.Error as e:
      print(f"Error! {e}")
    if sfx:
        bruj = VideoFileClip(output_file)
        soundy = AudioFileClip(sfx)
        if soundy.duration > bruj.duration:
          soundy = soundy.subclip(0, bruj.duration)
        clip = bruj.set_audio(soundy)
        clip.write_videofile(f"{getName(output_file)} (sfx).mp4",codec="libx264",audio_codec="aac",verbose=False)
        bruj.close()
        soundy.close()
        os.remove(output_file)
        os.rename(f"{getName(output_file)} (sfx).mp4",output_file)
        os.remove(sfx)
    return file_type

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
    parser.add_argument("-v","--verbose", help="Verbose Output, includes execution time and adding commands.")
    args = parser.parse_args()

    commands = parse_command_string(args.commands)
    message = parse(commands, args.input, args.output)
    print(message)
    # cmd = build_pipeline(commands, args.input, args.output)
    # run_cmd(cmd)
    print(f"check {args.output}.")
    listOut(SUPPORTED,title="Supported")

if __name__ == "__main__":
    main()
