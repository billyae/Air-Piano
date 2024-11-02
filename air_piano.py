import cv2
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import pyglet
import time  # 添加此行

# 初始设置
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)
detector = HandDetector(detectionCon=0.8,maxHands=2)

# 初始化Pyglet窗口
keys = ["C", "D", "E", "F", "G", "A", "B"]
key_width = 100  # 每个琴键的宽度
key_height = 200  # 每个琴键的高度

# Load sound files for each key
sounds = {key: pyglet.resource.media(f"{key}.wav", streaming=False) for key in keys}

# 音符播放函数
def play_key(note):
    try:
        sound = sounds.get(note)
        sound.play()
        pyglet.app.platform_event_loop.dispatch_posted_events()  # 确保事件循环处理
        time.sleep(0.1)  # 播放短暂停留
    except pyglet.resource.ResourceNotFoundException:
        print(f"Sound file for {note} not found.")

# 绘制钢琴键
def draw_piano_keys(img):
    for i, key in enumerate(keys):
        x = i * key_width
        color = (255, 255, 255)  # 默认白色
        cv2.rectangle(img, (x, 0), (x + key_width, key_height), color, -1)  # 绘制钢琴键
        cv2.putText(img, key, (x + 30, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

## Track state of each finger to avoid repeated sounds
key_press_states = {key: False for key in keys}

# Reset key press detection for this frame
keys_being_pressed = {key: False for key in keys}

# 检测手势并播放音符
while True:
    success, img = cap.read()
    if not success:
        break

    # 绘制钢琴键

    img = cv2.flip(img, 1)

    draw_piano_keys(img)

    hands, img = detector.findHands(img, draw=True)
    if hands:
        # 获取手的关键点
        for hand in hands:

            lmList = hand["lmList"]
            
            # Define fingertip indices to track
            fingertip_indices = [4, 8, 12, 16, 20]  # Thumb, index, middle, ring, and pinky

            # Check each fingertip position
            for finger_index, fingertip in enumerate(fingertip_indices):
                if lmList:
                    finger_x, finger_y = lmList[fingertip][0], lmList[fingertip][1]

                    # Check if fingertip is touching any key
                    for i, key in enumerate(keys):
                        x = i * key_width
                        if x < finger_x < x + key_width and 0 < finger_y < key_height:
                            keys_being_pressed[key] = True

                            # Check if the finger is not already pressing this key
                            if not key_press_states[key]:
                                play_key(key)

                                
                            # Highlight the pressed key
                            cv2.rectangle(img, (x, 0), (x + key_width, key_height), (0, 255, 0), -1)
                            cv2.putText(img, key, (x + 30, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    for key in keys:
        if not keys_being_pressed[key]:
            key_press_states[key] = False
        else:
            key_press_states[key] = True
        keys_being_pressed[key] = False

    cv2.imshow("Air Piano", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
