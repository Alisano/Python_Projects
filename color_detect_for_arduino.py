import cv2 as cv
import numpy as np
import serial
import time

SerialObj = serial.Serial("COM3", 9600)
time.sleep(2)
cap = cv.VideoCapture(0)
SerialObj.reset_input_buffer()

# frame_rate = 10
time_for_average = 6
prev = 0
window_name = "AMS-0_Mashinie Zrenie"
counter = 0
hue_sum = 0

if not cap.isOpened():
    print("Cannot open camera ")
    exit()

while True:
    ret, img = cap.read()
    center_pos = np.array([int(img.shape[0] / 2), int(img.shape[1] / 2)])
    img = cv.circle(img, (center_pos[1], center_pos[0]), 10, (255, 0, 0), -1)
    # img = cv.rectangle(img,(center_pos[1], center_pos[0]),(21,21),(0,255,0),-1)
    hsv_img = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    text = "Undefined color "
    # hue_img = hsv_img[center_pos[1], center_pos[0]][0]
    # saturation = hsv_img[center_pos[1], center_pos[0]][1]
    # value = hsv_img[center_pos[1], center_pos[0]][2]
    hue_img = 0
    saturation = 0
    value = 0
    arr_hsv_arr = hsv_img[center_pos[1] - 10 : center_pos[1] + 10, center_pos[0] - 10 : center_pos[0] + 10]
    for i in range(arr_hsv_arr.shape[0]):
        for j in range(arr_hsv_arr.shape[1]):
                hue_img += arr_hsv_arr[i][j][0] / (arr_hsv_arr.shape[0] * arr_hsv_arr.shape[0])
                saturation += arr_hsv_arr[i][j][1] / (arr_hsv_arr.shape[0] * arr_hsv_arr.shape[0])
                value += arr_hsv_arr[i][j][2] / (arr_hsv_arr.shape[0] * arr_hsv_arr.shape[0])

    counter += 1
    hue_sum += hue_img
    mean_hue = hue_sum / counter

    if (mean_hue < 10 and (mean_hue > 1)):
        text = "Red "
    elif (hue_img > 14 and (mean_hue < 20)):
        text = "Yellow "
    elif (mean_hue > 65 and (mean_hue < 85)):
        text = "Green "


    # if (hue_img < 10 and (hue_img > 1)):
    #     text = "Red "
    # elif (hue_img > 14 and (hue_img < 20)):
    #     text = "Yellow "
    # elif (hue_img > 65 and (hue_img < 85)):
    #     text = "Green "

    # elif(hue_img > 55):
    #      text = "Undefined color"
    # text = str(int(hue_img))
    # elif (hue_img < 140):
    #     text = "Blue" 
    # elif (hue_img < 167):
    #     text = "Violet"
    # else:
    #     text = "Red"

    time_elapsed = time.time() - prev

    # if time_elapsed > 1./frame_rate:
    #     prev = time.time()
    #     if (text == "Green "):
    #         SerialObj.write(b'1')
    #         # prev_c = "Green"
    #     elif ((text == "Red ") or (text == "Yellow ")):
    #         SerialObj.write(b'0')
    #             # prev_c = "Red"
    #     print(counter)
    #     counter = 0
    #     hue_sum = 0

    if time_elapsed >= time_for_average:
        prev = time.time()
        print(text)
        if (text == "Green "):
            SerialObj.write(b'1')
            # prev_c = "Green"
        elif ((text == "Red ") or (text == "Yellow ")):
            SerialObj.write(b'0')
                # prev_c = "Red"
        counter = 0
        hue_sum = 0

    img = cv.putText(img, 'AMS-0', (300, 30), 3, 1, (200, 200, 100), 2)
    img = cv.putText(img, text + str(int(hue_img)), (280, 60), 3, 1, (255, 255, 255), 2)    
    cv.imshow(window_name, img)
    k = cv.waitKey(1)
    if(k != -1):
       break
    if cv.getWindowProperty(window_name, cv.WND_PROP_VISIBLE) < 1:        
        break  
cap.release()
SerialObj.close()
cv.destroyAllWindows()