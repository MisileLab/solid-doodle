import os
import uvicorn
from fastapi import FastAPI
from gtts import gTTS
from playsound import playsound

# --- Audio Configuration ---
AUDIO_DIR = "tts_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# TTS messages from main.py
TTS_MESSAGES = [
    "소화기 시뮬레이션을 시작합니다. 먼저 안전핀을 뽑기 쉽도록 소화기를 회전시켜 케이블 타이를 제거해주세요.",
    "좋습니다. 이제 소화기를 바닥에 내려놓고 몸통을 잡아주세요.",
    "안전핀을 뽑으세요. 실제 상황처럼 힘을 주어 당겨주세요!",
    "잘했습니다. 이제 노즐을 잡고 불이 난 방향으로 조준하세요.",
    "손잡이를 꽉 움켜쥐세요.",
    "바람을 등지고 자세를 낮춰 발사를 준비하세요.",
    "발사! 발사! 발사! 발사!",
    "불이 꺼졌습니다. 자세를 낮추고 안전한 곳으로 대피하세요. 시뮬레이션을 종료합니다."
]

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
                playsound(audio_file)
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
