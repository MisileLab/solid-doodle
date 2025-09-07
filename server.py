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
    Cross-platform audio player using system commands.
    """
    system = platform.system().lower()
    
    try:
        if system == "windows":
            # Windows: use built-in media player with volume control
            os.system(f'powershell -c "(New-Object Media.SoundPlayer \\"{audio_file}\\").PlaySync()"')
        elif system == "darwin":  # macOS
            subprocess.run(["afplay", "-v", "1.5", audio_file], check=True)  # 150% 음량
        elif system == "linux":
            # Try multiple Linux audio players in order of preference
            players = ["paplay", "aplay", "mpg123", "mpv", "vlc", "mplayer"]
            
            for player in players:
                try:
                    # Check if player is available
                    subprocess.run(["which", player], 
                                 check=True, 
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL)
                    
                    # Play audio with the available player
                    if player == "paplay":
                        subprocess.run([player, audio_file], check=True)
                    elif player == "aplay":
                        subprocess.run([player, audio_file], check=True)
                    elif player == "mpg123":
                        subprocess.run([player, "-q", "-d", "50", audio_file], check=True)  # -d 50으로 속도 증가
                    elif player in ["mpv", "vlc", "mplayer"]:
                        subprocess.run([player, "--no-video", "--speed=1.2", audio_file], check=True)  # 1.2배속으로 재생
                    
                    print(f"Successfully played audio using {player}")
                    return True
                    
                except subprocess.CalledProcessError:
                    continue
                except FileNotFoundError:
                    continue
            
            # If no player worked, try pygame as fallback
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                pygame.mixer.quit()
                print("Successfully played audio using pygame")
                return True
            except ImportError:
                pass
            except Exception as e:
                print(f"Pygame error: {e}")
            
            raise Exception("No suitable audio player found on Linux system")
        else:
            raise Exception(f"Unsupported operating system: {system}")
            
    except Exception as e:
        raise Exception(f"Failed to play audio: {e}")

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
    print(f"Running on {system} system")
    
    # Check available audio players on Linux
    if system.lower() == "linux":
        players = ["paplay", "aplay", "mpg123", "mpv", "vlc", "mplayer"]
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
            print(f"Available audio players: {', '.join(available_players)}")
        else:
            print("Warning: No standard audio players found. Will try pygame as fallback.")

@app.get("/")
def read_root():
    return {"message": "G-FIRE Assist Server is running. POST to /speak/{index} to play a message."}

@app.post("/speak/{index}")
async def speak_message(index: int):
    """
    Plays a pre-generated TTS message based on the index.
    """
    if 0 <= index < len(TTS_MESSAGES):
        audio_file = os.path.join(AUDIO_DIR, f"speech_{index}.mp3")
        if os.path.exists(audio_file):
            try:
                print(f"Received request, playing message index {index}: {TTS_MESSAGES[index]}")
                play_audio_cross_platform(audio_file)
                return {"status": "success", "message_played": TTS_MESSAGES[index]}
            except Exception as e:
                print(f"Error playing sound for index {index}: {e}")
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Audio file for index {index} not found."}
    else:
        return {"status": "error", "message": f"Invalid message index: {index}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
