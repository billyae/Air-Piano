import cv2
import mediapipe as mp
import numpy as np
from scipy import signal
import pygame
import threading
import time

class AirPiano:
    def __init__(self, mode="beginner"):
        self.mode = mode
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
        self.mp_draw = mp.solutions.drawing_utils
        
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        pygame.init()
        
        self.screen_width = 1280
        self.screen_height = 720
        
        self.note_cache = {}
        self.last_play_time = {}
        
        # 增加master模式的八度数
        if mode == "beginner":
            self.octaves = 2
        else:
            self.octaves = 8  # 增加到8个八度
            
        self.keys = []
        self.setup_piano_keys()
        self.recent_notes = []
        self.is_playing = False
        self.finger_last_touch = {}
        
        # 添加生成旋律按钮
        self.generate_button = {
            'rect': (10, 70, 200, 40),
            'color': (0, 200, 0),
            'text': 'Generate Melody',
            'active': False
        }
        
    def setup_piano_keys(self):
        self.keys = []
        # 调整琴键大小以适应屏幕
        white_width = min(100, self.screen_width // (7 * self.octaves))
        white_height = int(self.screen_height * 0.6)
        black_width = int(white_width * 0.6)
        black_height = int(white_height * 0.6)
        
        start_y = int(self.screen_height * 0.2)
        
        # 计算总宽度并居中放置
        total_width = white_width * 7 * self.octaves
        start_x = (self.screen_width - total_width) // 2
        
        # 先创建所有白键
        for octave in range(self.octaves):
            notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
            for i, note in enumerate(notes):
                x = start_x + (white_width * i) + (octave * 7 * white_width)
                self.keys.append({
                    'note': f'{note}{octave+3}',  # 从低音区开始
                    'rect': (x, start_y, white_width, white_height),
                    'color': (255, 255, 255),
                    'type': 'white',
                    'is_pressed': False
                })
        
        # 再创建所有黑键
        for octave in range(self.octaves):
            black_positions = [0, 1, 3, 4, 5]  # C#, D#, F#, G#, A#
            notes = ['C#', 'D#', 'F#', 'G#', 'A#']
            for i, pos in enumerate(black_positions):
                x = start_x + (white_width * pos) + (white_width - black_width//2) + (octave * 7 * white_width)
                self.keys.append({
                    'note': f'{notes[i]}{octave+3}',
                    'rect': (x, start_y, black_width, black_height),
                    'color': (0, 0, 0),
                    'type': 'black',
                    'is_pressed': False
                })

    def create_note_sound(self, frequency, duration=0.3):
        if frequency in self.note_cache:
            return self.note_cache[frequency]
            
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        wave = 0.7 * np.sin(2 * np.pi * frequency * t)
        wave += 0.2 * np.sin(4 * np.pi * frequency * t)
        wave += 0.1 * np.sin(6 * np.pi * frequency * t)
        
        envelope = np.exp(-3 * t)
        wave = wave * envelope
        
        wave = np.int16(wave * 32767)
        sound = pygame.sndarray.make_sound(np.column_stack((wave, wave)))
        
        self.note_cache[frequency] = sound
        return sound

    def note_to_freq(self, note):
        note_name = note[:-1]
        octave = int(note[-1])
        base_freq = 440
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        if '#' in note_name:
            semitones = notes.index(note_name) - notes.index('A')
        else:
            semitones = notes.index(note_name) - notes.index('A')
            
        octave_diff = octave - 4
        total_semitones = semitones + (12 * octave_diff)
        
        return base_freq * (2 ** (total_semitones / 12))

    def play_note(self, note, finger_id):
        current_time = time.time()
        touch_key = f"{note}_{finger_id}"
        
        if touch_key in self.last_play_time and current_time - self.last_play_time[touch_key] < 0.1:
            return
            
        self.last_play_time[touch_key] = current_time
        freq = self.note_to_freq(note)
        sound = self.create_note_sound(freq)
        sound.play()

    def generate_melody(self):
        if self.is_playing or len(self.recent_notes) < 2:
            return
            
        self.is_playing = True
        base_notes = self.recent_notes[-3:]
        generated_notes = []
        
        # 生成更复杂的旋律
        for note in base_notes:
            generated_notes.append(note)
            # 添加和弦
            if note[0] not in ['E', 'B']:
                generated_notes.append(note[0] + '#' + note[-1])
            # 添加高八度音
            generated_notes.append(note[0] + str(int(note[-1]) + 1))
        
        def play_sequence():
            for note in generated_notes:
                self.play_note(note, -1)
                time.sleep(0.3)
            self.is_playing = False
            
        threading.Thread(target=play_sequence).start()

    def check_key_collision(self, x, y):
        # 先检查黑键（因为黑键在上层）
        for key in self.keys:
            if key['type'] == 'black':
                rect = key['rect']
                if (rect[0] < x < rect[0] + rect[2] and 
                    rect[1] < y < rect[1] + rect[3]):
                    return key
        
        # 如果没有碰到黑键，再检查白键
        for key in self.keys:
            if key['type'] == 'white':
                rect = key['rect']
                if (rect[0] < x < rect[0] + rect[2] and 
                    rect[1] < y < rect[1] + rect[3]):
                    return key
        
        return None

    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.screen_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.screen_height)
        
        while True:
            success, img = cap.read()
            if not success:
                continue
                
            img = cv2.flip(img, 1)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = self.hands.process(img_rgb)
            
            # 绘制钢琴键
            for key in self.keys:
                color = key['color']
                if key['is_pressed']:
                    # 按下时改变颜色
                    color = (0, 255, 0) if key['type'] == 'white' else (0, 100, 0)
                    
                cv2.rectangle(img, 
                            (key['rect'][0], key['rect'][1]), 
                            (key['rect'][0] + key['rect'][2], key['rect'][1] + key['rect'][3]), 
                            color, 
                            -1 if key['type'] == 'black' else 2)
                
                # 添加音符名称标签
                cv2.putText(img, key['note'], 
                          (key['rect'][0] + 5, key['rect'][1] + key['rect'][3] - 10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                          (0, 0, 0) if key['type'] == 'white' else (255, 255, 255), 1)
            
            # 在beginner模式下绘制生成旋律按钮
            if self.mode == "beginner":
                btn = self.generate_button
                color = (0, 255, 0) if btn['active'] else btn['color']
                cv2.rectangle(img, 
                            (btn['rect'][0], btn['rect'][1]),
                            (btn['rect'][0] + btn['rect'][2], btn['rect'][1] + btn['rect'][3]),
                            color, -1)
                cv2.putText(img, btn['text'],
                          (btn['rect'][0] + 10, btn['rect'][1] + 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # 重置所有键的按压状态
            for key in self.keys:
                key['is_pressed'] = False
            
            # 检测手指位置
            if results.multi_hand_landmarks:
                for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    self.mp_draw.draw_landmarks(img, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    finger_tips = [4, 8, 12, 16, 20]
                    
                    for finger_idx in finger_tips:
                        finger = hand_landmarks.landmark[finger_idx]
                        x = int(finger.x * img.shape[1])
                        y = int(finger.y * img.shape[0])
                        
                        finger_id = hand_idx * 5 + finger_tips.index(finger_idx)
                        cv2.circle(img, (x, y), 5, (0, 255, 0), -1)
                        
                        # 检查是否触碰到琴键，使用新的碰撞检测方法
                        touched_key = self.check_key_collision(x, y)
                        if touched_key:
                            touched_key['is_pressed'] = True
                            self.play_note(touched_key['note'], finger_id)
                            if touched_key['note'] not in self.recent_notes:
                                self.recent_notes.append(touched_key['note'])
                                if len(self.recent_notes) > 5:
                                    self.recent_notes.pop(0)
                        
                        # 在beginner模式下检查是否点击生成旋律按钮
                        if self.mode == "beginner":
                            btn = self.generate_button
                            if (btn['rect'][0] < x < btn['rect'][0] + btn['rect'][2] and 
                                btn['rect'][1] < y < btn['rect'][1] + btn['rect'][3]):
                                btn['active'] = True
                                self.generate_melody()
                            else:
                                btn['active'] = False
            
            # 显示模式和提示信息
            mode_text = f"Mode: {self.mode.capitalize()}"
            cv2.putText(img, mode_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            cv2.imshow("Air Piano", img)
            key = cv2.waitKey(1)
            if key == 27:  # ESC
                break
            elif key == ord('m'):  # 切换模式
                self.mode = "master" if self.mode == "beginner" else "beginner"
                self.recent_notes = []
                self.setup_piano_keys()
        
        cap.release()
        cv2.destroyAllWindows()
        pygame.quit()

if __name__ == "__main__":
    piano = AirPiano(mode="beginner")
    piano.run()