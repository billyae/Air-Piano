import cv2
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import pygame
import time
import math

# original setup
cap = cv2.VideoCapture(0)
frame_width, frame_height = 1280, 720
cap.set(3, frame_width)
cap.set(4, frame_height)
detector = HandDetector(detectionCon=0.8, maxHands=2)

# Initialize pygame
pygame.init()
pygame.mixer.init()  # initialize the audio module of pygame
window = pygame.display.set_mode((frame_width, frame_height))
pygame.display.set_caption("Air Piano")

# load the image 
piano_top_image = pygame.image.load('piano_top.jpg').convert_alpha()

# original image dimensions
original_image_width = piano_top_image.get_width()
original_image_height = piano_top_image.get_height()

# calculate new image height based on the frame width
new_image_height = int(original_image_height * (frame_width / original_image_width))

# resize the image
piano_top_image = pygame.transform.scale(piano_top_image, (frame_width, new_image_height))

# initialize font
pygame.font.init()
font = pygame.font.SysFont('Arial', 36)  # select Aria font with size 36

# set default mode 
mode = "beginner" 
octaves = 2 if mode == "beginner" else 3  # set default octaves based on mode

# the function to generate keys
def generate_keys(octaves):
    white_keys = []
    black_keys = []
    for octave in range(3, 3 + octaves):  
        white_keys += [f"{note}{octave}" for note in ["C", "D", "E", "F", "G", "A", "B"]]
        
        black_keys += [f"{note}{octave}" if note else None for note in ["Db", "Eb", None, "Gb", "Ab", "Bb", None]]
    return white_keys, black_keys

# load the sound with our folder
def load_sounds(keys):
    sounds = {}
    for key in keys:
        if key:
            try:
                sounds[key] = pygame.mixer.Sound(f"sound/notes/{key}.wav")
            except Exception as e:
                print(f"Warning: Could not load sound for {key}: {e}")
    return sounds

# generate the keyboard and load
white_keys, black_keys = generate_keys(octaves)
sounds = load_sounds(set(filter(None, white_keys + black_keys)))

# update keyboard size and position
def update_key_dimensions():
    global white_key_width, white_key_height, black_key_width, black_key_height
    global keyboard_x, keyboard_y, piano_top_height
    white_key_width = frame_width // (7 * octaves)  
    white_key_height = 400  
    black_key_width = int(white_key_width * 0.6)
    black_key_height = int(white_key_height * 0.6)
    piano_top_height = piano_top_image.get_height()  
    keyboard_x = (frame_width - (white_key_width * 7 * octaves)) // 2
    keyboard_y = frame_height - white_key_height  

# initialize the key size
update_key_dimensions()  

# play the key
def play_key(note):
    sound = sounds.get(note)
    if sound:
        sound.play()

# draw the piano keys and the picture above 
def draw_piano_keys(screen, keys_being_pressed):
    key_surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)

    # draw the upper image
    piano_top_x = 0  
    piano_top_y = keyboard_y - piano_top_height
    key_surface.blit(piano_top_image, (piano_top_x, piano_top_y))

    # draw the white keys
    for i, key in enumerate(white_keys):
        x = keyboard_x + i * white_key_width
        
        
        if keys_being_pressed.get(key, False):
            color = (139, 69, 19, 200)  
        else:
            color = (255, 255, 255, 200)  
        pygame.draw.rect(key_surface, color, (x, keyboard_y, white_key_width, white_key_height))
    
        if i < len(white_keys) - 1:
            pygame.draw.line(key_surface, (0, 0, 0), (x + white_key_width - 1, keyboard_y),
                             (x + white_key_width - 1, keyboard_y + white_key_height), 2)
        
        pygame.draw.line(key_surface, (0, 0, 0), (x, keyboard_y), (x + white_key_width, keyboard_y), 2)
        
        font_key = pygame.font.Font(None, 24)
        text = font_key.render(key, True, (0, 0, 0))
        text_rect = text.get_rect(center=(x + white_key_width / 2, keyboard_y + white_key_height - 20))
        key_surface.blit(text, text_rect)

    # draw the black keys 
    for i, key in enumerate(black_keys):
        if key:
            x = keyboard_x + (i + 0.7) * white_key_width
            if keys_being_pressed.get(key, False):
                color = (139, 69, 19, 200)  
            else:
                color = (0, 0, 0, 255)  
            pygame.draw.rect(key_surface, color, (x, keyboard_y, black_key_width, black_key_height))
            
            font_key = pygame.font.Font(None, 18)
            text = font_key.render(key, True, (255, 255, 255))
            text_rect = text.get_rect(center=(x + black_key_width / 2, keyboard_y + black_key_height - 15))
            key_surface.blit(text, text_rect)

    screen.blit(key_surface, (0, 0))

# tract the key press states
key_press_states = {key: False for key in filter(None, white_keys + black_keys)}
prev_positions = {}
last_press_times = {}
press_threshold = 20  


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            
            # change the mode
            mode = "master" if mode == "beginner" else "beginner"
            octaves = 3 if mode == "master" else 2
            white_keys, black_keys = generate_keys(octaves)
            sounds = load_sounds(set(filter(None, white_keys + black_keys)))  
            key_press_states = {key: False for key in filter(None, white_keys + black_keys)}
            update_key_dimensions()  

    success, img = cap.read()
    if not success:
        break

    hands, img = detector.findHands(img, draw=False)  

    # change OpenCV image to Pygame image
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_surface = pygame.surfarray.make_surface(np.rot90(img_rgb))
    window.blit(img_surface, (0, 0))

    # track the keys being pressed
    keys_being_pressed = {key: False for key in key_press_states}

    fingertip_positions = []  # load the fingertip positions

    if hands:
        for hand in hands:
            lmList = hand["lmList"]
            fingertip_indices = [4, 8, 12, 16, 20]

            for fingertip in fingertip_indices:
                finger_id = f"{hands.index(hand)}_{fingertip}"
                finger_x = lmList[fingertip][0]
                finger_y = lmList[fingertip][1]

                
                fingertip_positions.append((frame_width - finger_x, finger_y))

                
                if finger_id in prev_positions:
                    prev_y = prev_positions[finger_id]
                    y_displacement = finger_y - prev_y  

                    # judge whether pressing the key
                    if y_displacement > press_threshold:
                        key_triggered = False  
                        # check the black keys first
                        for i, key in enumerate(black_keys):
                            if key:
                                x = keyboard_x + (i + 0.7) * white_key_width
                                if x < frame_width - finger_x < x + black_key_width and keyboard_y < finger_y < keyboard_y + black_key_height:
                                    keys_being_pressed[key] = True
                                    if not key_press_states[key]:  
                                        play_key(key)
                                        key_press_states[key] = True
                                        last_press_times[key] = time.time()
                                    key_triggered = True
                                    break  
                        # check the white keys 
                        if not key_triggered:
                            for i, key in enumerate(white_keys):
                                x = keyboard_x + i * white_key_width
                                
                                is_covered_by_black = False
                                if i < len(black_keys):
                                    black_key = black_keys[i]
                                    if black_key:
                                        black_x = keyboard_x + (i + 0.7) * white_key_width
                                        if black_x < frame_width - finger_x < black_x + black_key_width and keyboard_y < finger_y < keyboard_y + black_key_height:
                                            is_covered_by_black = True
                                if x < frame_width - finger_x < x + white_key_width and keyboard_y < finger_y < keyboard_y + white_key_height and not is_covered_by_black:
                                    keys_being_pressed[key] = True
                                    if not key_press_states[key]:  
                                        play_key(key)
                                        key_press_states[key] = True
                                        last_press_times[key] = time.time()
                                    break  

                # update the previous position of the finger
                prev_positions[finger_id] = finger_y

    # draw image
    draw_piano_keys(window, keys_being_pressed)

    # draw the fingertip positions above the piano keys
    for pos in fingertip_positions:
        pygame.draw.circle(window, (139, 69, 19), pos, 10)  

    # draw the text
    mode_text = font.render(f"Mode: {mode.capitalize()}", True, (255, 255, 255))
    instruction_text = font.render("Press 'M' to switch modes", True, (255, 255, 255))

    window.blit(mode_text, (10, 10))

    window.blit(instruction_text, (10, 10 + mode_text.get_height()))

    # reset the key press states
    for key in key_press_states:
        if not keys_being_pressed[key] and time.time() - last_press_times.get(key, 0) > 0.1:
            key_press_states[key] = False

    pygame.display.update()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
pygame.quit()
cv2.destroyAllWindows()
