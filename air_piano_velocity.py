import cv2
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import pygame
import time
import math

# 初始设置
cap = cv2.VideoCapture(0)
frame_width, frame_height = 1280, 720
cap.set(3, frame_width)
cap.set(4, frame_height)
detector = HandDetector(detectionCon=0.8, maxHands=2)

# 初始化 Pygame
pygame.init()
pygame.mixer.init()  # 初始化 pygame 的音频模块
window = pygame.display.set_mode((frame_width, frame_height))
pygame.display.set_caption("Air Piano")

# 加载要显示在琴键上方的图片并缩放以填满宽度
piano_top_image = pygame.image.load('piano_top.jpg').convert_alpha()
# 获取原始图片尺寸
original_image_width = piano_top_image.get_width()
original_image_height = piano_top_image.get_height()
# 计算新的高度以保持纵横比
new_image_height = int(original_image_height * (frame_width / original_image_width))
# 缩放图片
piano_top_image = pygame.transform.scale(piano_top_image, (frame_width, new_image_height))

# 初始化字体
pygame.font.init()
font = pygame.font.SysFont('Arial', 36)  # 选择 Arial 字体，大小为 36

# 设置初始模式为 "beginner"
mode = "beginner"
octaves = 2 if mode == "beginner" else 3  # 设置初始八度数量

# 生成琴键的函数
def generate_keys(octaves):
    white_keys = []
    black_keys = []
    for octave in range(3, 3 + octaves):  # 从 C3 开始，根据选择的八度范围
        white_keys += [f"{note}{octave}" for note in ["C", "D", "E", "F", "G", "A", "B"]]
        # 将黑键映射到白键的相对位置
        black_keys += [f"{note}{octave}" if note else None for note in ["Db", "Eb", None, "Gb", "Ab", "Bb", None]]
    return white_keys, black_keys

# 使用 pygame.mixer 加载每个键的声音
def load_sounds(keys):
    sounds = {}
    for key in keys:
        if key:
            try:
                sounds[key] = pygame.mixer.Sound(f"sound/notes/{key}.wav")
            except Exception as e:
                print(f"Warning: Could not load sound for {key}: {e}")
    return sounds

# 生成琴键并加载声音
white_keys, black_keys = generate_keys(octaves)
sounds = load_sounds(set(filter(None, white_keys + black_keys)))

# 更新琴键尺寸和位置的函数
def update_key_dimensions():
    global white_key_width, white_key_height, black_key_width, black_key_height
    global keyboard_x, keyboard_y, piano_top_height
    white_key_width = frame_width // (7 * octaves)  # 调整宽度以适应所有琴键
    white_key_height = 400  # 增加白键高度
    black_key_width = int(white_key_width * 0.6)
    black_key_height = int(white_key_height * 0.6)
    piano_top_height = piano_top_image.get_height()  # 根据缩放后的图片高度设置钢琴顶部高度
    keyboard_x = (frame_width - (white_key_width * 7 * octaves)) // 2
    keyboard_y = frame_height - white_key_height  # 调整键盘的 y 位置

update_key_dimensions()  # 初始化琴键尺寸

# 使用 pygame.mixer 为给定的音符播放声音的函数
def play_key(note):
    sound = sounds.get(note)
    if sound:
        sound.play()

# 绘制钢琴键和上方的图片
def draw_piano_keys(screen, keys_being_pressed):
    key_surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)

    # 绘制钢琴顶部的图片
    piano_top_x = 0  # 图片现在填满宽度，x 位置为 0
    piano_top_y = keyboard_y - piano_top_height
    key_surface.blit(piano_top_image, (piano_top_x, piano_top_y))

    # 绘制白键
    for i, key in enumerate(white_keys):
        x = keyboard_x + i * white_key_width
        # 主键矩形
        if keys_being_pressed.get(key, False):
            color = (139, 69, 19, 200)  # 按下时的棕色，透明度为 200
        else:
            color = (255, 255, 255, 200)  # 默认白键颜色，透明度为 200
        pygame.draw.rect(key_surface, color, (x, keyboard_y, white_key_width, white_key_height))
        # 绘制右边缘的黑线
        if i < len(white_keys) - 1:
            pygame.draw.line(key_surface, (0, 0, 0), (x + white_key_width - 1, keyboard_y),
                             (x + white_key_width - 1, keyboard_y + white_key_height), 2)
        # 在顶部添加细黑边框
        pygame.draw.line(key_surface, (0, 0, 0), (x, keyboard_y), (x + white_key_width, keyboard_y), 2)
        # 键名标签
        font_key = pygame.font.Font(None, 24)
        text = font_key.render(key, True, (0, 0, 0))
        text_rect = text.get_rect(center=(x + white_key_width / 2, keyboard_y + white_key_height - 20))
        key_surface.blit(text, text_rect)

    # 绘制黑键
    for i, key in enumerate(black_keys):
        if key:
            x = keyboard_x + (i + 0.7) * white_key_width
            if keys_being_pressed.get(key, False):
                color = (139, 69, 19, 200)  # 按下时的棕色，透明度为 200
            else:
                color = (0, 0, 0, 255)  # 默认黑键颜色
            pygame.draw.rect(key_surface, color, (x, keyboard_y, black_key_width, black_key_height))
            # 键名标签
            font_key = pygame.font.Font(None, 18)
            text = font_key.render(key, True, (255, 255, 255))
            text_rect = text.get_rect(center=(x + black_key_width / 2, keyboard_y + black_key_height - 15))
            key_surface.blit(text, text_rect)

    screen.blit(key_surface, (0, 0))

# 跟踪每个键的状态以避免重复声音
key_press_states = {key: False for key in filter(None, white_keys + black_keys)}
prev_positions = {}
last_press_times = {}
press_threshold = 20  # 基于 y 位移检测“按下”的阈值

# 主循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            # 切换模式并重新生成键和声音
            mode = "master" if mode == "beginner" else "beginner"
            octaves = 3 if mode == "master" else 2
            white_keys, black_keys = generate_keys(octaves)
            sounds = load_sounds(set(filter(None, white_keys + black_keys)))  # 重新加载声音
            key_press_states = {key: False for key in filter(None, white_keys + black_keys)}
            update_key_dimensions()  # 更新新模式的尺寸

    success, img = cap.read()
    if not success:
        break

    hands, img = detector.findHands(img, draw=False)  # 禁用绘制手部标注

    # 将 OpenCV 图像（BGR）转换为 Pygame 图像（RGB）
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_surface = pygame.surfarray.make_surface(np.rot90(img_rgb))
    window.blit(img_surface, (0, 0))

    # 跟踪当前帧的按键
    keys_being_pressed = {key: False for key in key_press_states}

    fingertip_positions = []  # 用于存储指尖位置的列表

    if hands:
        for hand in hands:
            lmList = hand["lmList"]
            fingertip_indices = [4, 8, 12, 16, 20]

            for fingertip in fingertip_indices:
                finger_id = f"{hands.index(hand)}_{fingertip}"
                finger_x = lmList[fingertip][0]
                finger_y = lmList[fingertip][1]

                # 存储指尖位置以便稍后绘制
                fingertip_positions.append((frame_width - finger_x, finger_y))

                # 仅在向下移动时触发（y 位移增加）
                if finger_id in prev_positions:
                    prev_y = prev_positions[finger_id]
                    y_displacement = finger_y - prev_y  # 计算 y 位移

                    # 如果 y 位移超过阈值则触发
                    if y_displacement > press_threshold:
                        key_triggered = False  # 防止多个键被触发的标志
                        # 首先，检查黑键
                        for i, key in enumerate(black_keys):
                            if key:
                                x = keyboard_x + (i + 0.7) * white_key_width
                                if x < frame_width - finger_x < x + black_key_width and keyboard_y < finger_y < keyboard_y + black_key_height:
                                    keys_being_pressed[key] = True
                                    if not key_press_states[key]:  # 避免重复触发
                                        play_key(key)
                                        key_press_states[key] = True
                                        last_press_times[key] = time.time()
                                    key_triggered = True
                                    break  # 停止检查其他键
                        # 如果没有黑键被触发，检查白键
                        if not key_triggered:
                            for i, key in enumerate(white_keys):
                                x = keyboard_x + i * white_key_width
                                # 排除被黑键覆盖的区域
                                is_covered_by_black = False
                                if i < len(black_keys):
                                    black_key = black_keys[i]
                                    if black_key:
                                        black_x = keyboard_x + (i + 0.7) * white_key_width
                                        if black_x < frame_width - finger_x < black_x + black_key_width and keyboard_y < finger_y < keyboard_y + black_key_height:
                                            is_covered_by_black = True
                                if x < frame_width - finger_x < x + white_key_width and keyboard_y < finger_y < keyboard_y + white_key_height and not is_covered_by_black:
                                    keys_being_pressed[key] = True
                                    if not key_press_states[key]:  # 避免重复触发
                                        play_key(key)
                                        key_press_states[key] = True
                                        last_press_times[key] = time.time()
                                    break  # 停止检查其他键

                # 更新下一帧的前一个 y 位置
                prev_positions[finger_id] = finger_y

    # 绘制钢琴键和上方的图片
    draw_piano_keys(window, keys_being_pressed)

    # 在钢琴键上方绘制指尖点，使用较深的棕色
    for pos in fingertip_positions:
        pygame.draw.circle(window, (139, 69, 19), pos, 10)  # 更深的棕色

    # 绘制当前模式和提示文本
    mode_text = font.render(f"Mode: {mode.capitalize()}", True, (255, 255, 255))
    instruction_text = font.render("Press 'M' to switch modes", True, (255, 255, 255))
    # 绘制模式文本在左上角
    window.blit(mode_text, (10, 10))
    # 绘制提示文本在模式文本下方
    window.blit(instruction_text, (10, 10 + mode_text.get_height()))

    # 重置未在当前帧按下的键的状态，或如果足够的时间已经过去
    for key in key_press_states:
        if not keys_being_pressed[key] and time.time() - last_press_times.get(key, 0) > 0.1:
            key_press_states[key] = False

    pygame.display.update()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
pygame.quit()
cv2.destroyAllWindows()
