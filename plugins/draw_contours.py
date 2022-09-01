import cv2
import sys

def process_image(image, mask):
    info   = {}
    output = cv2.bitwise_and(image, image, mask=mask)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges  = cv2.GaussianBlur(mask, (5, 5), 0)
    edges  = cv2.Canny(edges, 50, 150)
    edges  = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations = 2)

    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for c in sorted(contours, key = cv2.contourArea, reverse = True):
        epsilon = 0.01 * cv2.arcLength(c, True) 
        approx  = cv2.approxPolyDP(c, epsilon, True)
        cv2.drawContours(output, [approx], 0, (0, 255, 255), 1)

    return (output, info)

