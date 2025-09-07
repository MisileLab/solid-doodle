import modi_plus
import time
import os
from gtts import gTTS
from playsound import playsound

# -- TTS 설정 --
# 임시 오디오 파일을 저장할 디렉토리
AUDIO_DIR = "tts_audio"
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

# TTS 메시지
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

def speak(text, index):
    """주어진 텍스트로 TTS를 생성하고 재생합니다."""
    audio_file = os.path.join(AUDIO_DIR, f"speech_{index}.mp3")
    if not os.path.exists(audio_file):
        print(f"TTS 생성 중: {text}")
        tts = gTTS(text=text, lang='ko')
        tts.save(audio_file)
    print(f"음성 안내: {text}")
    playsound(audio_file)

# -- 상태 및 트리거 변수 --
class State:
    START = 0
    ROTATE_TO_BREAK_TIE = 1
    PLACE_ON_FLOOR = 2
    PULL_PIN = 3
    AIM_NOZZLE = 4
    SQUEEZE_HANDLE = 5
    PREPARE_TO_FIRE = 6
    FIRE = 7
    EVACUATE = 8
    END = 9

current_state = State.START

# 트리거 감도를 위한 임계값
ROTATION_VELOCITY_THRESHOLD = 10000  # 각속도 임계값 (회전 감지)
SHAKE_ACCELERATION_THRESHOLD = 3  # 가속도 변화량 임계값 (흔들기 감지)
AIM_ANGLE_THRESHOLD = 45  # 소화기를 들어올렸을 때의 각도 임계값

def main():
    """메인 시뮬레이션 루프"""
    global current_state
    try:
        print("MODI+ 모듈을 초기화합니다...")
        bundle = modi_plus.MODIPlus()
        imu = bundle.imus[0]
        print("초기화 완료. 시뮬레이션을 시작합니다.")
        time.sleep(1)

        # TTS 파일 미리 생성하기
        for i, msg in enumerate(TTS_MESSAGES):
            audio_file = os.path.join(AUDIO_DIR, f"speech_{i}.mp3")
            if not os.path.exists(audio_file):
                tts = gTTS(text=msg, lang='ko')
                tts.save(audio_file)

    except Exception as e:
        print(f"초기화 중 오류 발생: {e}")
        print("MODI+ 모듈, 특히 IMU 모듈이 연결되었는지 확인해주세요.")
        return

    # 상태 머신 루프
    while current_state < State.END:
        # 현재 IMU 값 읽기
        try:
            roll = imu.roll
            pitch = imu.pitch
            yaw = imu.yaw
            ang_vel_z = imu.angular_vel_z
            acc_x = imu.acceleration_x
            acc_y = imu.acceleration_y
            acc_z = imu.acceleration_z
        except Exception as e:
            print(f"IMU 데이터 읽기 오류: {e}")
            time.sleep(1)
            continue

        # -- 상태별 로직 --
        if current_state == State.START:
            speak(TTS_MESSAGES[0], 0)
            current_state = State.ROTATE_TO_BREAK_TIE

        elif current_state == State.ROTATE_TO_BREAK_TIE:
            # Z축 중심의 빠른 회전을 감지
            if abs(ang_vel_z) > ROTATION_VELOCITY_THRESHOLD:
                print("회전 감지됨!")
                speak(TTS_MESSAGES[1], 1)
                current_state = State.PLACE_ON_FLOOR
                time.sleep(2) # 다음 동작을 위한 시간 여유

        elif current_state == State.PLACE_ON_FLOOR:
            # 소화기를 눕혔는지 감지 (roll 각도 기준)
            if abs(roll) > 70:
                print("바닥에 내려놓음 감지됨!")
                speak(TTS_MESSAGES[2], 2)
                current_state = State.PULL_PIN
                time.sleep(2)

        elif current_state == State.PULL_PIN:
            # 안전핀을 뽑는 동작(강한 흔들림)을 감지
            total_acc = (acc_x**2 + acc_y**2 + acc_z**2)**0.5
            if total_acc > SHAKE_ACCELERATION_THRESHOLD:
                print("안전핀 뽑기(흔들림) 감지됨!")
                speak(TTS_MESSAGES[3], 3)
                current_state = State.AIM_NOZZLE
                time.sleep(2)

        elif current_state == State.AIM_NOZZLE:
            # 소화기를 다시 들어올려 조준하는지 감지
            if abs(roll) < AIM_ANGLE_THRESHOLD:
                print("조준 자세 감지됨!")
                speak(TTS_MESSAGES[4], 4)
                current_state = State.SQUEEZE_HANDLE
                time.sleep(3) # 다음 음성 안내까지 시간 여유

        elif current_state == State.SQUEEZE_HANDLE:
            # 손잡이를 쥐는 동작은 감지가 어려우므로 시간 지연으로 대체
            speak(TTS_MESSAGES[5], 5)
            current_state = State.PREPARE_TO_FIRE
            time.sleep(3)

        elif current_state == State.PREPARE_TO_FIRE:
            # 발사 준비 역시 시간 지연으로 대체
            speak(TTS_MESSAGES[6], 6)
            current_state = State.FIRE
            time.sleep(2)

        elif current_state == State.FIRE:
            # 발사!
            speak(TTS_MESSAGES[7], 7)
            current_state = State.EVACUATE
            time.sleep(4) # 발사 시간

        elif current_state == State.EVACUATE:
            # 마지막 안내 후 종료
            current_state = State.END

        time.sleep(0.1) # 루프 지연

if __name__ == "__main__":
    main()
