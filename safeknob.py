import modi_plus
import time
import threading

# --- SafeKnob 설정 (기본값) ---
CRITICAL_TEMP = 60  # 적색 경고 임계 온도 (°C)
WARNING_TEMP = 55   # 황색 경고 임계 온도 (°C)

# 시뮬레이션 온도 (None이면 실제 센서 사용)
simulated_temp = None

def user_input_handler():
    """사용자 입력을 처리하는 스레드"""
    global simulated_temp
    
    print("\n=== SafeKnob 온도 시뮬레이터 ===")
    print("명령어:")
    print("  t <온도> : 현재 온도 설정 (예: t 65)")
    print("  real     : 실제 센서 모드로 전환")
    print("  status   : 현재 상태 확인")
    print("  quit     : 프로그램 종료")
    print("==============================\n")
    
    while True:
        try:
            user_input = input().strip()
            
            if user_input.lower() == 'quit':
                print("프로그램을 종료합니다.")
                exit(0)
            elif user_input.lower() == 'real':
                simulated_temp = None
                print("실제 센서 모드로 전환했습니다.")
            elif user_input.lower() == 'status':
                if simulated_temp is not None:
                    print(f"시뮬레이션 모드 - 설정 온도: {simulated_temp}°C")
                else:
                    print("실제 센서 모드")
                print(f"임계값 - 경고: {WARNING_TEMP}°C, 위험: {CRITICAL_TEMP}°C")
            elif user_input.startswith('t '):
                try:
                    new_temp = float(user_input.split()[1])
                    simulated_temp = new_temp
                    print(f"온도를 {simulated_temp}°C로 설정했습니다.")
                except (IndexError, ValueError):
                    print("올바른 형식: t <온도> (예: t 65)")
            elif user_input:
                print("알 수 없는 명령어입니다. 't <온도>', 'real', 'status', 'quit'를 사용하세요.")
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
            exit(0)

def run_safeknob():
    """SafeKnob 모듈의 메인 로직을 실행합니다."""
    global simulated_temp
    
    try:
        print("MODI+ 모듈을 초기화합니다 (SafeKnob)...")
        bundle = modi_plus.MODIPlus()
        
        # 모듈 연결 상태 확인
        print(f"연결된 모듈 수: Env={len(bundle.envs)}, LED={len(bundle.leds)}, Speaker={len(bundle.speakers)}")
        
        if len(bundle.envs) == 0:
            print("❌ Env 모듈이 연결되지 않았습니다!")
            return
        if len(bundle.leds) == 0:
            print("❌ LED 모듈이 연결되지 않았습니다!")
            return
        if len(bundle.speakers) == 0:
            print("❌ Speaker 모듈이 연결되지 않았습니다!")
            return
            
        env = bundle.envs[0]
        led = bundle.leds[0]
        speaker = bundle.speakers[0]
        print("✅ 초기화 완료. SafeKnob 작동을 시작합니다.")
        
        # 사용자 입력 스레드 시작
        input_thread = threading.Thread(target=user_input_handler, daemon=True)
        input_thread.start()
        
        time.sleep(1)

    except Exception as e:
        print(f"초기화 중 오류 발생: {e}")
        print("MODI+ 모듈(Env, LED, Speaker)이 모두 연결되었는지 확인해주세요.")
        return

    # 상태 변수
    is_beeping = False

    while True:
        try:
            # 시뮬레이션 온도가 설정되어 있으면 사용, 아니면 실제 센서 값 사용
            if simulated_temp is not None:
                temp = simulated_temp
                temp_source = "시뮬레이션"
            else:
                temp = env.temperature
                temp_source = "센서"
            
            print(f"현재 온도: {temp:.1f}°C ({temp_source}) | 위험: {WARNING_TEMP}°C    ", end='\r')

            # 1. 고온 위험 (적색 경고 + 삐 소리)
            if temp > WARNING_TEMP:
                led.set_rgb(255, 0, 0)  # 빨간색
                if not is_beeping:
                    speaker.set_tune(frequency=2000, volume=100)
                    is_beeping = True
            
            # 2. 안전 (녹색)
            else:
                led.set_rgb(0, 255, 0)  # 초록색
                if is_beeping:
                    speaker.turn_off()
                    is_beeping = False

        except Exception as e:
            print(f"\n작동 중 오류 발생: {e}")
            # 오류 발생 시 LED를 파란색으로 설정하여 문제 표시
            try:
                led.set_rgb(0, 0, 255)
            except:
                pass
            time.sleep(1)

        time.sleep(0.5)  # 0.5초 간격으로 센서 값 확인

if __name__ == "__main__":
    run_safeknob()
