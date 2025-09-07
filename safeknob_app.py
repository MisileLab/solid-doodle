"""
SafeKnob - Door Handle Safety Monitor
Smart fire door safety system using MODI+ sensors
"""

import time
import modi_plus
import json
import os
from enum import Enum


class SafetyLevel(Enum):
    SAFE = "safe"
    WARNING = "warning"
    DANGER = "danger"


class SafeKnobApp:
    def __init__(self):
        # Temperature thresholds (°C)
        self.SAFE_TEMP = 30
        self.WARNING_TEMP = 45
        self.DANGER_TEMP = 55
        
        # Light level thresholds (for smoke detection)
        self.NORMAL_LIGHT = 50
        self.SMOKE_LIGHT_DROP = 30
        
        # Initialize MODI+ modules
        self.bundle = None
        self.env_sensor = None
        self.led = None
        self.speaker = None
        self.network = None
        
        # State tracking
        self.current_safety_level = SafetyLevel.SAFE
        self.last_alert_time = 0
        self.alert_interval = 2.0  # seconds between alerts
        
        # Log file
        self.log_file = "safeknob_log.json"
        
    def initialize_hardware(self):
        """Initialize MODI+ modules"""
        try:
            print("Initializing SafeKnob hardware...")
            self.bundle = modi_plus.MODIPlus()
            
            # Get modules
            self.env_sensor = self.bundle.envs[0] if self.bundle.envs else None
            self.led = self.bundle.leds[0] if self.bundle.leds else None
            self.speaker = self.bundle.speakers[0] if self.bundle.speakers else None
            self.network = self.bundle.networks[0] if self.bundle.networks else None
            
            if not self.env_sensor:
                raise Exception("Environment sensor not found")
            if not self.led:
                raise Exception("LED module not found")
                
            print("✓ Hardware initialization complete")
            return True
            
        except Exception as e:
            print(f"✗ Hardware initialization failed: {e}")
            return False
    
    def read_sensors(self):
        """Read temperature and light levels"""
        try:
            temperature = self.env_sensor.temperature
            light_level = self.env_sensor.brightness
            return temperature, light_level
        except Exception as e:
            print(f"Sensor read error: {e}")
            return None, None
    
    def assess_safety_level(self, temperature, light_level):
        """Determine safety level based on sensor readings"""
        # Temperature-based assessment
        if temperature >= self.DANGER_TEMP:
            return SafetyLevel.DANGER
        elif temperature >= self.WARNING_TEMP:
            return SafetyLevel.WARNING
        
        # Light-based smoke detection (supplementary)
        if light_level < self.SMOKE_LIGHT_DROP:
            # If light drops significantly, suggest caution
            if temperature >= self.SAFE_TEMP:
                return SafetyLevel.WARNING
        
        return SafetyLevel.SAFE
    
    def update_led_indicator(self, safety_level):
        """Update LED based on safety level"""
        if not self.led:
            return
            
        try:
            if safety_level == SafetyLevel.SAFE:
                # Green solid
                self.led.rgb = 0, 255, 0
                
            elif safety_level == SafetyLevel.WARNING:
                # Yellow blinking
                current_time = time.time()
                if int(current_time * 2) % 2:  # Blink every 0.5 seconds
                    self.led.rgb = 255, 255, 0
                else:
                    self.led.rgb = 0, 0, 0
                    
            elif safety_level == SafetyLevel.DANGER:
                # Red fast blinking
                current_time = time.time()
                if int(current_time * 4) % 2:  # Blink every 0.25 seconds
                    self.led.rgb = 255, 0, 0
                else:
                    self.led.rgb = 0, 0, 0
                    
        except Exception as e:
            print(f"LED update error: {e}")
    
    def play_alert_sound(self, safety_level):
        """Play appropriate alert sound"""
        if not self.speaker:
            return
            
        current_time = time.time()
        if current_time - self.last_alert_time < self.alert_interval:
            return
            
        try:
            if safety_level == SafetyLevel.WARNING:
                # Medium pitch warning beep
                self.speaker.set_tune(1000, 60)
                time.sleep(0.2)
                self.speaker.reset()
                
            elif safety_level == SafetyLevel.DANGER:
                # High pitch urgent beep
                self.speaker.set_tune(2000, 80)
                time.sleep(0.1)
                self.speaker.reset()
                time.sleep(0.1)
                self.speaker.set_tune(2000, 80)
                time.sleep(0.1)
                self.speaker.reset()
                
            self.last_alert_time = current_time
            
        except Exception as e:
            print(f"Speaker error: {e}")
    
    def log_reading(self, temperature, light_level, safety_level):
        """Log sensor readings to file"""
        try:
            log_entry = {
                "timestamp": time.time(),
                "temperature": temperature,
                "light_level": light_level,
                "safety_level": safety_level.value,
                "readable_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Read existing log
            logs = []
            if os.path.exists(self.log_file):
                try:
                    with open(self.log_file, 'r') as f:
                        logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
            
            # Add new entry
            logs.append(log_entry)
            
            # Keep only last 100 entries
            if len(logs) > 100:
                logs = logs[-100:]
            
            # Save log
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            print(f"Logging error: {e}")
    
    def print_status(self, temperature, light_level, safety_level):
        """Print current status to console"""
        status_symbols = {
            SafetyLevel.SAFE: "🟢",
            SafetyLevel.WARNING: "🟡", 
            SafetyLevel.DANGER: "🔴"
        }
        
        symbol = status_symbols.get(safety_level, "⚪")
        
        print(f"\r{symbol} SafeKnob | "
              f"온도: {temperature:.1f}°C | "
              f"조도: {light_level} | "
              f"상태: {safety_level.value.upper()}", end="")
    
    def run(self):
        """Main monitoring loop"""
        if not self.initialize_hardware():
            return
        
        print("\n🔥 SafeKnob 시작 - 문 손잡이 안전 모니터링")
        print(f"안전: <{self.SAFE_TEMP}°C | 주의: {self.WARNING_TEMP}-{self.DANGER_TEMP}°C | 위험: >{self.DANGER_TEMP}°C")
        print("Ctrl+C로 종료\n")
        
        try:
            while True:
                # Read sensors
                temperature, light_level = self.read_sensors()
                
                if temperature is not None and light_level is not None:
                    # Assess safety
                    new_safety_level = self.assess_safety_level(temperature, light_level)
                    
                    # Update indicators
                    self.update_led_indicator(new_safety_level)
                    
                    # Play alerts if safety level changed or is dangerous
                    if (new_safety_level != self.current_safety_level or 
                        new_safety_level == SafetyLevel.DANGER):
                        self.play_alert_sound(new_safety_level)
                    
                    # Log data
                    if new_safety_level != self.current_safety_level:
                        self.log_reading(temperature, light_level, new_safety_level)
                        if new_safety_level != SafetyLevel.SAFE:
                            print(f"\n⚠️  안전 상태 변경: {new_safety_level.value.upper()}")
                    
                    self.current_safety_level = new_safety_level
                    self.print_status(temperature, light_level, new_safety_level)
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n\n🛑 SafeKnob 중지됨")
            if self.led:
                self.led.rgb = 0, 0, 0  # Turn off LED
            if self.speaker:
                self.speaker.reset()  # Turn off sound


def main():
    """Entry point"""
    app = SafeKnobApp()
    app.run()


if __name__ == "__main__":
    main()