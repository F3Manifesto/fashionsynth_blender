# import cv2
# import numpy as np
# import os

# img = "/Users/devdesign/Documents/Blender Scripting/fashionsynth/scripts/bomberjacket.png"

# def findContours(img):

#     img = cv2.imread(img)
#     img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     thresh, img_edges = cv2.threshold(img_gray, 100, 255, cv2.THRESH_BINARY)

#     canvas = np.zeros(img.shape, np.uint8)
#     canvas.fill(255)

#     mask = np.zeros(img.shape, np.uint8)
#     mask.fill(255)

#     # all contours
#     contours_draw, hierarchy = cv2.findContours(
#         img_edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

#     pattern = {}
#     patternCount = 0
#     stitching_pairs = {}

#     for cnt in contours_draw:
#         approx = cv2.approxPolyDP(cnt, 0.009*cv2.arcLength(cnt, True), True)
#         cv2.drawContours(canvas, [approx], 0, (0,0,255), 3)
#         n = approx.ravel()
#         coords = []
#         pattern[patternCount] = coords
#         i = 0
#         patternCount += 1
#         for j in n:
#             coords.append(j)
#             if i % 2 == 0:
#                 x = n[i]
#                 y = n[i+1]
#                 result = str(x) + " " + str(y) 
#                 # cv2.putText(canvas, result, (x,y), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0,0,0))
#                 # take the pairs
#                 stitching_pairs[i] = (x,y)
#                 cv2.putText(canvas, str(i), (x,y), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0,0,0))

            
#             i += 1
#     print(pattern)
#     print(stitching_pairs)
#     # cv2.imshow('canvas', canvas)
#     # cv2.waitKey(0)
#     # cv2.destroyAllWindows()
            
#     for key in range(patternCount):
#         print(pattern[key])

#         for i in pattern[key]:
#             print(i)

#     return pattern, stitching_pairs

import numpy as np
import cv2

'''
note that stitching arrays follow a left right cross pattern
'''

img = "/Users/devdesign/Documents/BlenderScripting/fashionsynth/scripts/bomberjacket.png"
url = "http://bafybeidjaj733ywm4zjmgbrnnad7ayep4vmg25kavm4offqyhpq5vaddzu.ipfs.w3s.link/bomberjacket.png"

img = cv2.imread(img)
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
pattern_count = 0
stitching_pairs = {}
stitching_count = 0
area = []
count = 0
for cnt in contours_draw:
    # skip the image border
    if count != 0:
        approx = cv2.approxPolyDP(cnt, 0.009*cv2.arcLength(cnt, True), True)
        cv2.drawContours(canvas, [approx], 0, (0,0,255), 3)
        n = approx.ravel()
        coords = []
        pattern[pattern_count] = coords
        i = 0
        stitch_nested = {}
        pattern_count += 1
        area.append(cv2.contourArea(cnt))
        for j in n:
            coords.append(j)
            if i % 2 == 0:
                x = n[i]
                y = n[i+1]
                result = str(x) + " " + str(y) 
                # cv2.putText(canvas, result, (x,y), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0,0,0))
                # take the pairs
                stitch_nested[i] = (x,y)
                cv2.putText(canvas, result, (x,y), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0,0,0))

            
            i += 1
        stitching_pairs[pattern_count] = stitch_nested
    count += 1

print(pattern)
print("\n\nstitching pairs\n", stitching_pairs)
print("\n\narea", area)
cv2.imshow('canvas', canvas)
cv2.waitKey(0)
cv2.destroyAllWindows()
        
# for key in range(patternCount):
#     print(pattern[key])

#     for i in pattern[key]:
#         print(i)

# return pattern, stitching_pairs

