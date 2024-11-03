import cv2
import mediapipe as mp
import numpy as np
import pygame
import time
import math

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
        
        self.octaves = 2 if mode == "beginner" else 8
        self.keys = []
        self.setup_piano_keys()
        
        # Store last positions and angles for each fingertip to detect movement
        self.finger_last_position = {}
        self.finger_last_angle = {}

    def setup_piano_keys(self):
        self.keys = []
        white_width = min(100, self.screen_width // (7 * self.octaves))
        white_height = int(self.screen_height * 0.6)
        black_width = int(white_width * 0.6)
        black_height = int(white_height * 0.6)
        
        start_y = int(self.screen_height * 0.2)
        total_width = white_width * 7 * self.octaves
        start_x = (self.screen_width - total_width) // 2
        
        for octave in range(self.octaves):
            notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
            for i, note in enumerate(notes):
                x = start_x + (white_width * i) + (octave * 7 * white_width)
                self.keys.append({
                    'note': f'{note}{octave+3}',
                    'rect': (x, start_y, white_width, white_height),
                    'color': (255, 255, 255),
                    'type': 'white',
                    'is_pressed': False
                })
        
        black_positions = [0, 1, 3, 4, 5]
        notes = ['C#', 'D#', 'F#', 'G#', 'A#']
        for octave in range(self.octaves):
            for i, pos in enumerate(black_positions):
                x = start_x + (white_width * pos) + (white_width - black_width // 2) + (octave * 7 * white_width)
                self.keys.append({
                    'note': f'{notes[i]}{octave+3}',
                    'rect': (x, start_y, black_width, black_height),
                    'color': (0, 0, 0),
                    'type': 'black',
                    'is_pressed': False
                })

    def note_to_freq(self, note):
        note_name = note[:-1]
        octave = int(note[-1])
        base_freq = 440
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        semitones = notes.index(note_name) - notes.index('A')
        octave_diff = octave - 4
        total_semitones = semitones + (12 * octave_diff)
        
        return base_freq * (2 ** (total_semitones / 12))

    def play_note_if_pressing(self, note, finger_id, finger_y, angle):
        if finger_id in self.finger_last_position:
            last_y = self.finger_last_position[finger_id]
            last_angle = self.finger_last_angle.get(finger_id, angle)
            
            if finger_y - last_y > 5 and angle < 160:
                # Play sound only if finger is pressing down and bending
                if not self.keys[finger_id]['is_pressed']:
                    self.keys[finger_id]['is_pressed'] = True
                    self.play_sound(note)
            elif finger_y - last_y < -5 or angle > 170:
                # Stop sound if finger lifts or straightens
                self.keys[finger_id]['is_pressed'] = False
        # Update last position and angle
        self.finger_last_position[finger_id] = finger_y
        self.finger_last_angle[finger_id] = angle

    def play_sound(self, note):
        freq = self.note_to_freq(note)
        sound = pygame.mixer.Sound(buffer=np.array(np.sin(2 * np.pi * np.arange(44100 * 0.3) * freq / 44100), dtype=np.int16))
        sound.play()

    def calculate_finger_angle(self, joint1, joint2, joint3):
        a = np.array(joint1)
        b = np.array(joint2)
        c = np.array(joint3)
        ba = a - b
        bc = c - b
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(cosine_angle)
        return np.degrees(angle)

    def check_key_collision(self, x, y):
        for key in self.keys:
            rect = key['rect']
            if (rect[0] < x < rect[0] + rect[2] and rect[1] < y < rect[1] + rect[3]):
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
            
            # Draw keys
            for key in self.keys:
                color = (0, 255, 0) if key['is_pressed'] else key['color']
                cv2.rectangle(img, (key['rect'][0], key['rect'][1]), 
                              (key['rect'][0] + key['rect'][2], key['rect'][1] + key['rect'][3]), 
                              color, -1 if key['type'] == 'black' else 2)
                cv2.putText(img, key['note'], 
                            (key['rect'][0] + 5, key['rect'][1] + key['rect'][3] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                            (0, 0, 0) if key['type'] == 'white' else (255, 255, 255), 1)
            
            # Finger detection
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    finger_tips = [4, 8, 12, 16, 20]
                    for i, tip in enumerate(finger_tips):
                        fingertip = hand_landmarks.landmark[tip]
                        x, y = int(fingertip.x * img.shape[1]), int(fingertip.y * img.shape[0])
                        
                        finger_id = i
                        touched_key = self.check_key_collision(x, y)
                        if touched_key:
                            # Calculate finger bending angle
                            joint1 = (hand_landmarks.landmark[tip - 2].x * img.shape[1], hand_landmarks.landmark[tip - 2].y * img.shape[0])
                            joint2 = (hand_landmarks.landmark[tip - 1].x * img.shape[1], hand_landmarks.landmark[tip - 1].y * img.shape[0])
                            joint3 = (fingertip.x * img.shape[1], fingertip.y * img.shape[0])
                            angle = self.calculate_finger_angle(joint1, joint2, joint3)
                            
                            # Play sound if pressing detected
                            self.play_note_if_pressing(touched_key['note'], finger_id, y, angle)
            
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
