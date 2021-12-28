import cv2
import pytesseract
import imutils
import os
from imutils.object_detection import non_max_suppression
import numpy as np
import argparse
import os, sys
import time
import matplotlib.pyplot as plt
from PIL import Image

def east_detect(image):
    layerNames = [
    	"feature_fusion/Conv_7/Sigmoid",
    	"feature_fusion/concat_3"]
    
    orig = image.copy()
    
    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    # orig = cv2.blur(orig, (4,4))

    (H, W) = image.shape[:2]
    
    h = (H // 32) * 32
    w = (W // 32) * 32
    # set the new width and height and then determine the ratio in change
    # for both the width and height: Should be multiple of 32
    (newW, newH) = (w, h)
    
    rW = W / float(newW)
    rH = H / float(newH)
    
    # resize the image and grab the new image dimensions
    image = cv2.resize(image, (newW, newH))
    
    (H, W) = image.shape[:2]
    
    net = cv2.dnn.readNet("frozen_east_text_detection.pb")
    
    blob = cv2.dnn.blobFromImage(image, 1.0, (W, H),
    	(123.68, 116.78, 103.94), swapRB=True, crop=False)
    
    start = time.time()
    
    net.setInput(blob)
    
    (scores, geometry) = net.forward(layerNames)
    
    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []
    # loop over the number of rows
    for y in range(0, numRows):
        # extract the scores (probabilities), followed by the geometrical
        # data used to derive potential bounding box coordinates that
        # surround text
        scoresData = scores[0, 0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]
    
        for x in range(0, numCols):
    		# if our score does not have sufficient probability, ignore it
            # Set minimum confidence as required
            if scoresData[x] < 0.5:
                continue
    		# compute the offset factor as our resulting feature maps will
            #  x smaller than the input image
            (offsetX, offsetY) = (x * 4.0, y * 4.0)
            # extract the rotation angle for the prediction and then
            # compute the sin and cosine
            angle = anglesData[x]
            cos = np.cos(angle)
            sin = np.sin(angle)
            # use the geometry volume to derive the width and height of
            # the bounding box
            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]
            # compute both the starting and ending (x, y)-coordinates for
            # the text prediction bounding box
            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)
            # add the bounding box coordinates and probability score to
            # our respective lists
            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])
                        
    boxes = non_max_suppression(np.array(rects), probs=confidences)
    # loop over the bounding boxes
    for (startX, startY, endX, endY) in boxes:
        # scale the bounding box coordinates based on the respective
        # ratios 
        startX = int(startX * rW)
        startY = int(startY * rH)
        endX = int(endX * rW)
        endY = int(endY * rH)
        # draw the bounding box on the image
        cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 255, 0), 2)
    
    return orig, boxes

def read_text(arr, boxes):
    results = [] # read all of example
    for box in boxes:
        (H, W) = arr.shape[:2]
        h = (H // 32) * 32
        w = (W // 32) * 32
        (newW, newH) = (w, h)
        rW = W / float(newW)
        rH = H / float(newH)

        startY = int(box[1] * rH)
        startX = int(box[0] * rW)
        endY = int(box[3] * rH)
        endX = int(box[2] * rW)

        roi = arr[startY:endY, startX:endX]

        text = pytesseract.image_to_string(roi, lang='eng', config='--psm 6')
        results.append(text)
    print(results)
    return results

def sortBoxes(boxes):
    pass

def main():
    name = "exp1.jpg"
    # name = "DC59E429-245F-4665-9985-C4412825D03C_4_5005_c.jpeg"
    image = cv2.imread(f'uploads/{name}') # example image
    arr = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    arr = cv2.blur(arr, (4,4))
    arr = cv2.GaussianBlur(arr, (3,3), 0)
    # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # arr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 10)
    # arr = cv2.GaussianBlur(arr, (7, 7), 0)
    # kernell = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
    # arr = cv2.filter2D(src=arr, ddepth=-1, kernel=kernell)
    image, boxes = east_detect(arr)
    image = Image.fromarray(image)
    image.save(f'text_detection/processed2_{name}')
    result = read_text(arr, boxes)
    # plt.imsshow(image)

main()