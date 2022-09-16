import cv2
import numpy as np
import os

# class FindContours:
    
#     def getCoordinates():
img = cv2.imread("/Users/devdesign/Documents/Blender Scripting/fashionsynth/scripts/bomberjacket.png")
img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
thresh, img_edges = cv2.threshold(img_gray, 100, 255, cv2.THRESH_BINARY)

canvas = np.zeros(img.shape, np.uint8)
canvas.fill(255)

mask = np.zeros(img.shape, np.uint8)
mask.fill(255)

# all contours
contours_draw, hierarchy = cv2.findContours(
    img_edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

pattern = {}
patternCount = 0

for cnt in contours_draw:
    approx = cv2.approxPolyDP(cnt, 0.009*cv2.arcLength(cnt, True), True)
    cv2.drawContours(canvas, [approx], 0, (0,0,255), 3)
    n = approx.ravel()
    coords = []
    pattern[patternCount] = coords
    i = 0
    patternCount += 1
    for j in n:
        coords.append(j)
        if i % 2 == 0:
            x = n[i]
            y = n[i+1]
            result = str(x) + " " + str(y) 
            cv2.putText(canvas, result, (x,y), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0,0,0))
        
        i += 1
print(pattern)
        
for key in range(patternCount):
    print(pattern[key])

    for i in pattern[key]:
        print(i)



# print(pattern)
# # most significant contours
# contours_mask, hierarchy = cv2.findContours(
#     img_edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

# # loop over contours
# for contour in range(len(contours_draw)):
#     # draw current contour
#     cv2.drawContours(canvas, contours_draw, contour, (0,0,0), 3)

# # loop over contours
# for contour in range(len(contours_mask)):
    
#     # draw current contour
#     if contour != 16:
#         cv2.fillConvexPoly(mask, contours_mask[contour], (0,255,0))
cv2.imshow('image', img) 
cv2.imshow('image', canvas) 
# cv2.imshow('mask', mask) cac
cv2.waitKey(0)


cv2.destroyAllWindows()
