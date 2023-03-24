import cv2 as cv
from matplotlib import pyplot as plt
import numpy as np
from PIL import Image


impath = r"D:\Yamaha DB\Inspection Images\2022.02.15\INSPRES [4320AY] 00000014 V013_3.bmp"

image = Image.open(impath)
(rw, rh) = image.info['dpi']

pixel_per_mm2 = (rw * rh) / 645.16 #anzahl pixel pro mm2

sc = 0.991
ar = 3.999
up_ar = 200000
lo_ar = 100

image = cv.imread(impath)
grey = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
grey = cv.medianBlur(grey, 15)
thres, grey = cv.threshold(grey, 110, 255, cv.THRESH_BINARY_INV)
#hist = cv.calcHist(image, [0], None, [256], [0, 256])


# apply connected component analysis to the thresholded image
output = cv.connectedComponentsWithStats(grey, 4, cv.CV_32S)
(numLabels, labels, stats, centroids) = output

# initialize an output mask to store all characters parsed from
# the license plate
mask = np.zeros(grey.shape, dtype="uint8")
output = image.copy()

# loop over the number of unique connected component labels, skipping
# over the first label (as label zero is the background)
for i in range(1, numLabels):
    # extract the connected component statistics for the current
    # label
    x = stats[i, cv.CC_STAT_LEFT]
    y = stats[i, cv.CC_STAT_TOP]
    w = stats[i, cv.CC_STAT_WIDTH]
    h = stats[i, cv.CC_STAT_HEIGHT]
    area = stats[i, cv.CC_STAT_AREA]
    # ensure the width, height, and area are all neither too small
    # nor too big
    keepWidth = w > 5 and w < 100
    keepHeight = h > 5 and h < 100
    keepArea = area > lo_ar and area < up_ar
    # ensure the connected component we are examining passes all
    # three tests
    if all((keepWidth, keepHeight, keepArea)):
        # construct a mask for the current connected component and
        # then take the bitwise OR with the mask
        

        componentMask = (labels == i).astype("uint8") * 255
        mask = cv.bitwise_or(mask, componentMask)
        cv.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 3)
        (a, b) = centroids[i]
        cv.putText(output, str(i), (int(a)-20, int(b)), cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        l = (w * 25.4 / rw) * sc
        b = (h * 25.4 / rh) * sc
        are = area / pixel_per_mm2

        print(f"[INFO] keeping connected component '{i}', width: {w}, height: {h}, area: {area}, threshold: {thres}")
        print(f"[INFO] lenght: {round(l, 3)} width: {round(b, 3)} area: {round(are, 3)}")

    else:
        cv.rectangle(output, (x, y), (x + w, y + h), (255, 0, 255), 3)



# show the original input image and the mask for the license plate
# characters
m = cv.cvtColor(mask, cv.COLOR_GRAY2BGR)
aha = cv.bitwise_and(image, m)
output = cv.resize(output, (800, 600))
mask = cv.resize(mask, (800, 600))
aha = cv.resize(aha, (800, 600))
cv.imshow("Image", output)
cv.imshow("Characters", mask)
cv.imshow("aja", aha)
cv.waitKey(0)




"""
plt.figure()
plt.axis("off")
plt.imshow(cv.cvtColor(grey, cv.COLOR_GRAY2RGB))


plt.figure()
plt.title("Grayscale Histogram")
plt.xlabel("Bins")
plt.ylabel("# of Pixels")
plt.plot(hist)
plt.xlim([0, 256])

# normalize the histogram
hist /= hist.sum()
# plot the normalized histogram
plt.figure()
plt.title("Grayscale Histogram (Normalized)")
plt.xlabel("Bins")
plt.ylabel("% of Pixels")
plt.plot(hist)
plt.xlim([0, 256])
plt.show()
"""