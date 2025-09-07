# Project: Solid-Doodle - Fire Extinguisher Simulator

## Commands
- **Run server**: `uvicorn server:app --reload --host 0.0.0.0 --port 8000`
- **Run client**: `python client.py`
- **Run safeknob**: `python safeknob.py`
- **Install dependencies**: `uv sync` (uv.lock present)
- **Check server**: `curl http://localhost:8000/`
- **Test speak endpoint**: `curl -X POST http://localhost:8000/speak/0`

## Code Style
- **Imports**: Standard libs first, third-party next, local modules last
- **Formatting**: 4-space indentation, no tabs, 80-char line length preferred
- **Naming**: snake_case for vars/functions, PascalCase for classes, UPPER_CASE for constants
- **Error handling**: Try-catch blocks with specific exception types, log meaningful errors
- **Types**: Type hints encouraged where practical (FastAPI benefits)

## Project Structure
- `server.py`: FastAPI server with TTS audio generation/playback
- `client.py`: MODI+ device client with state machine logic  
- `safeknob.py`: Safety monitoring module with temperature/light sensors
- `tts_audio/`: Generated Korean TTS audio files
- `typings/`: MODI+ library type stubs

## Key Libraries
- FastAPI for REST API
- gTTS for Korean text-to-speech
- playsound for audio playback
- pymodi-plus for hardware control
- requests for HTTP client

## MODI+ Hardware
- IMU: Motion detection (acceleration, rotation, orientation)
- Button: User input trigger
- Speaker: Audio feedback/beeps
- Env: Temperature/light sensing
- LED: Visual status indicators