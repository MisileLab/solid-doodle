import os
import uvicorn
import platform
import subprocess
from fastapi import FastAPI
from gtts import gTTS

# --- Audio Configuration ---
AUDIO_DIR = "tts_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# TTS messages from main.py
TTS_MESSAGES = [
    "먼저 안전핀을 뽑기 쉽도록 소화기를 회전시켜 케이블 타이를 제거해주세요.",
    "좋습니다. 이제 소화기를 바닥에 내려놓고 몸통을 잡아주세요.",
    "안전핀을 뽑으세요. 실제 상황처럼 힘을 주어 당겨주세요!",
    "잘했습니다. 이제 노즐을 잡고 불이 난 방향으로 조준하세요.",
    "손잡이를 꽉 움켜쥐세요.",
    "바람을 등지고 자세를 낮춰 발사를 준비하세요.",
    "발사! 발사! 발사! 발사!",
    "불이 꺼졌습니다. 자세를 낮추고 안전한 곳으로 대피하세요."
]

def play_audio_cross_platform(audio_file):
    """
    Cross-platform audio player using system commands with 400% volume.
    """
    system = platform.system().lower()
    
    try:
        if system == "windows":
            # Windows: use PowerShell with volume amplification (4.0 = 400%)
            powershell_cmd = f'''
            Add-Type -AssemblyName presentationCore
            $mediaPlayer = New-Object system.windows.media.mediaplayer
            $mediaPlayer.open([System.Uri]::new("{audio_file}"))
            $mediaPlayer.Volume = 1.0
            $mediaPlayer.Play()
            Start-Sleep -Milliseconds 500
            while($mediaPlayer.NaturalDuration.HasTimeSpan -eq $false) {{ Start-Sleep -Milliseconds 50 }}
            $duration = $mediaPlayer.NaturalDuration.TimeSpan.TotalMilliseconds
            Start-Sleep -Milliseconds $duration
            $mediaPlayer.Close()
            '''
            # Use ffplay for better volume control on Windows
            try:
                subprocess.run(["ffplay", "-nodisp", "-autoexit", "-volume", "400", audio_file], 
                             check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (FileNotFoundError, subprocess.CalledProcessError):
                # Fallback to PowerShell
                subprocess.run(["powershell", "-Command", powershell_cmd], check=True)
                
        elif system == "darwin":  # macOS
            # macOS: use afplay with maximum volume amplification (4.0 = 400%)
            subprocess.run(["afplay", "-v", "4.0", audio_file], check=True)
            
        elif system == "linux":
            # Try multiple Linux audio players with volume amplification
            players_with_volume = [
                ("ffplay", ["-nodisp", "-autoexit", "-volume", "400", audio_file]),
                ("mpv", ["--no-video", "--volume=400", "--speed=1.0", audio_file]),
                ("vlc", ["--no-video", "--gain=12", "--volume=400", "--play-and-exit", audio_file]),
                ("mplayer", ["-volume", "400", "-novideo", audio_file]),
                ("paplay", ["--volume", "65536", audio_file]),  # 65536 = 400% for pulseaudio
                ("aplay", ["-D", "pulse", audio_file])  # Use with pulseaudio volume control
            ]
            
            # First try to set system volume high for basic players
            try:
                subprocess.run(["amixer", "set", "Master", "100%"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "400%"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass  # Ignore if volume control commands fail
            
            for player, cmd in players_with_volume:
                try:
                    # Check if player is available
                    subprocess.run(["which", player], 
                                 check=True, 
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL)
                    
                    # Play audio with volume amplification
                    subprocess.run(cmd, check=True, 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    print(f"Successfully played audio at 400% volume using {player}")
                    return True
                    
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            
            # If no player worked, try pygame with volume amplification
            try:
                import pygame
                pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
                
                # Load and play with volume adjustment
                sound = pygame.mixer.Sound(audio_file)
                sound.set_volume(1.0)  # Pygame max volume
                sound.play()
                
                # Wait for sound to finish
                while pygame.mixer.get_busy():
                    pygame.time.wait(100)
                    
                pygame.mixer.quit()
                print("Successfully played audio using pygame (note: pygame limited to 100% volume)")
                return True
            except ImportError:
                pass
            except Exception as e:
                print(f"Pygame error: {e}")
            
            raise Exception("No suitable audio player found on Linux system")
        else:
            raise Exception(f"Unsupported operating system: {system}")
            
    except Exception as e:
        raise Exception(f"Failed to play audio at 400% volume: {e}")

def prepare_all_sounds():
    """Generates all TTS audio files if they don't exist."""
    for i, msg in enumerate(TTS_MESSAGES):
        audio_file = os.path.join(AUDIO_DIR, f"speech_{i}.mp3")
        if not os.path.exists(audio_file):
            print(f"Generating TTS audio for index {i}: '{msg}'")
            try:
                tts = gTTS(text=msg, lang='ko')
                tts.save(audio_file)
                print(f"Audio file saved: {audio_file}")
            except Exception as e:
                print(f"Failed to generate TTS for index {i}: {e}")

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Prepare all sound files when the server starts."""
    prepare_all_sounds()
    
    # Print system information
    system = platform.system()
    print(f"Running on {system} system with 400% volume amplification")
    
    # Check available audio players
    if system.lower() == "linux":
        players = ["ffplay", "mpv", "vlc", "mplayer", "paplay", "aplay"]
        available_players = []
        
        for player in players:
            try:
                subprocess.run(["which", player], 
                             check=True, 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
                available_players.append(player)
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        if available_players:
            print(f"Available audio players with volume control: {', '.join(available_players)}")
        else:
            print("Warning: No standard audio players found. Will try pygame as fallback.")
            
        # Check if volume control utilities are available
        volume_utils = []
        for util in ["amixer", "pactl"]:
            try:
                subprocess.run(["which", util], 
                             check=True, 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
                volume_utils.append(util)
            except:
                pass
        
        if volume_utils:
            print(f"Available volume control utilities: {', '.join(volume_utils)}")

@app.get("/")
def read_root():
    return {"message": "G-FIRE Assist Server is running with 400% volume amplification. POST to /speak/{index} to play a message."}

@app.post("/speak/{index}")
async def speak_message(index: int):
    """
    Plays a pre-generated TTS message based on the index at 400% volume.
    """
    if 0 <= index < len(TTS_MESSAGES):
        audio_file = os.path.join(AUDIO_DIR, f"speech_{index}.mp3")
        if os.path.exists(audio_file):
            try:
                print(f"Received request, playing message index {index} at 400% volume: {TTS_MESSAGES[index]}")
                play_audio_cross_platform(audio_file)
                return {"status": "success", "message_played": TTS_MESSAGES[index], "volume": "400%"}
            except Exception as e:
                print(f"Error playing sound for index {index}: {e}")
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Audio file for index {index} not found."}
    else:
        return {"status": "error", "message": f"Invalid message index: {index}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
