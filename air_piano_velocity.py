import cv2
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import pyglet
import pygame
import time

# Initial setup
cap = cv2.VideoCapture(0)
frame_width, frame_height = 1280, 720
cap.set(3, frame_width)
cap.set(4, frame_height)
detector = HandDetector(detectionCon=0.8, maxHands=2)

# Initialize Pygame
pygame.init()
window = pygame.display.set_mode((frame_width, frame_height))
pygame.display.set_caption("Air Piano")

# Piano key settings for 2 octaves
white_keys = ["C3", "D3", "E3", "F3", "G3", "A3", "B3", "C4", "D4", "E4", "F4", "G4", "A4", "B4"]
black_keys = ["Db3", "Eb3", "", "Gb3", "Ab3", "Bb3", "", "Db4", "Eb4", "", "Gb4", "Ab4", "Bb4"]

# Set key dimensions for a smaller keyboard
white_key_width, white_key_height = 90, 150
black_key_width, black_key_height = 60, 100

# Transparency levels for white and black keys
white_key_alpha, black_key_alpha = 150, 200

# Calculate keyboard positioning
keyboard_width = white_key_width * len(white_keys)
keyboard_x = (frame_width - keyboard_width) // 2
keyboard_y = frame_height - white_key_height

# Load sound files for each key
sounds = {key: pyglet.resource.media(f"sound/notes/{key}.wav", streaming=False) for key in set(white_keys + black_keys) if key}

# Function to play sound for a given note
def play_key(note):
    sound = sounds.get(note)
    if sound:
        sound.play()
        pyglet.app.platform_event_loop.dispatch_posted_events()

# Draw the white and black keys on a transparent surface
def draw_piano_keys(screen, keys_being_pressed):
    key_surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
    
    for i, key in enumerate(white_keys):
        x = keyboard_x + i * white_key_width
        color = (255, 255, 255, white_key_alpha) if not keys_being_pressed.get(key, False) else (0, 255, 0, white_key_alpha)
        pygame.draw.rect(key_surface, color, (x, keyboard_y, white_key_width, white_key_height))
        font = pygame.font.Font(None, 36)
        text = font.render(key, True, (0, 0, 0))
        key_surface.blit(text, (x + 15, keyboard_y + white_key_height - 40))

    for i, key in enumerate(black_keys):
        if key:
            x = keyboard_x + (i + 0.7) * white_key_width
            color = (0, 0, 0, black_key_alpha) if not keys_being_pressed.get(key, False) else (0, 255, 0, black_key_alpha)
            pygame.draw.rect(key_surface, color, (x, keyboard_y, black_key_width, black_key_height))
            font = pygame.font.Font(None, 24)
            text = font.render(key, True, (255, 255, 255))
            key_surface.blit(text, (x + 5, keyboard_y + black_key_height - 30))

    screen.blit(key_surface, (0, 0))

# Track state of each key to avoid repeated sounds
key_press_states = {key: False for key in set(white_keys + black_keys) if key}

# To track fingertip y-positions over time for velocity and acceleration calculation
prev_positions = {}
last_press_times = {}
press_threshold = 20  # Threshold for detecting a "press" based on acceleration

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    success, img = cap.read()
    if not success:
        break

    hands, _ = detector.findHands(img, draw=False)

    # Convert OpenCV image (BGR) to Pygame image (RGB)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_surface = pygame.surfarray.make_surface(np.rot90(img_rgb))
    window.blit(img_surface, (0, 0))

    # Track key presses for current frame
    keys_being_pressed = {key: False for key in key_press_states}

    if hands:
        for hand in hands:
            lmList = hand["lmList"]
            fingertip_indices = [4, 8, 12, 16, 20]

            for fingertip in fingertip_indices:
                finger_id = f"{hands.index(hand)}_{fingertip}"
                finger_x, finger_y = frame_width - lmList[fingertip][0], lmList[fingertip][1]
                
                # Compute velocity (change in y-position) and acceleration (change in velocity)
                if finger_id in prev_positions:
                    prev_y = prev_positions[finger_id]
                    velocity = finger_y - prev_y
                    acceleration = velocity - (prev_positions.get(f"{finger_id}_velocity", 0))

                    # Check for a "press" based on downward acceleration
                    if acceleration > press_threshold and finger_y > prev_y:
                        for i, key in enumerate(white_keys):
                            x = keyboard_x + i * white_key_width
                            if x < finger_x < x + white_key_width and keyboard_y < finger_y < keyboard_y + white_key_height:
                                keys_being_pressed[key] = True
                                if not key_press_states[key]:
                                    play_key(key)
                                    key_press_states[key] = True
                                    last_press_times[key] = time.time()
                    
                    # Save velocity and update previous y-position
                    prev_positions[f"{finger_id}_velocity"] = velocity
                prev_positions[finger_id] = finger_y

    # Draw the piano keys on top of the camera feed
    draw_piano_keys(window, keys_being_pressed)

    # Reset key press states for keys not pressed this frame or if enough time has passed
    for key in key_press_states:
        if not keys_being_pressed[key] and time.time() - last_press_times.get(key, 0) > 0.1:
            key_press_states[key] = False

    pygame.display.update()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
pygame.quit()
cv2.destroyAllWindows()
