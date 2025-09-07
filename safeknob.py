import modi_plus
import time

# --- SafeKnob 설정 ---
CRITICAL_TEMP = 60  # 적색 경고 임계 온도 (°C)
WARNING_TEMP = 55   # 황색 경고 임계 온도 (°C)

def run_safeknob():
    """SafeKnob 모듈의 메인 로직을 실행합니다."""
    try:
        print("MODI+ 모듈을 초기화합니다 (SafeKnob)...")
        bundle = modi_plus.MODIPlus()
        env = bundle.envs[0]
        led = bundle.leds[0]
        speaker = bundle.speakers[0]
        print("초기화 완료. SafeKnob 작동을 시작합니다.")
        time.sleep(1)

    except Exception as e:
        print(f"초기화 중 오류 발생: {e}")
        print("MODI+ 모듈(Env, LED, Speaker)이 모두 연결되었는지 확인해주세요.")
        return

    # 상태 변수
    is_beeping = False

    while True:
        try:
            temp = env.temperature
            illuminance = env.illuminance
            
            print(f"현재 온도: {temp:.1f}°C, 조도: {illuminance:.1f}%", end='\r')

            # 1. 고온 위험 (적색 경고)
            if temp > CRITICAL_TEMP:
                led.set_rgb(255, 0, 0)
                # 경고음이 울리고 있지 않으면 시작
                if not is_beeping:
                    speaker.set_tune(frequency=2000, volume=100)
                    is_beeping = True
            
            # 2. 예비 경고 (황색)
            elif temp > WARNING_TEMP:
                led.set_rgb(255, 165, 0) # 주황색에 가까운 노란색
                # 경고음 중지
                if is_beeping:
                    speaker.turn_off()
                    is_beeping = False
            
            # 3. 안전 (녹색)
            else:
                led.set_rgb(0, 255, 0)
                # 경고음 중지
                if is_beeping:
                    speaker.turn_off()
                    is_beeping = False

            # 조도 기반 예비 경고 (연기 감지 보조)
            # 어두워지면 황색으로 표시 (단, 이미 고온 경고 상태가 아닐 때)
            if illuminance < 30 and temp <= WARNING_TEMP:
                led.set_rgb(255, 255, 0) # 노란색

        except Exception as e:
            print(f"\n작동 중 오류 발생: {e}")
            # 오류 발생 시 LED를 파란색으로 설정하여 문제 표시
            led.set_rgb(0, 0, 255)
            time.sleep(1)

        time.sleep(0.5) # 0.5초 간격으로 센서 값 확인

if __name__ == "__main__":
    run_safeknob()
