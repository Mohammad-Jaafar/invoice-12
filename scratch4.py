import cv2

image = cv2.imread("data/clean/inv_000_en_classic.png")
print(image.shape, image.dtype)
blurred = cv2.GaussianBlur(image, (5, 5), 0)
cv2.imwrite("blurred.png", blurred)
matrix = cv2.getRotationMatrix2D((image.shape[1] / 2, image.shape[0] / 2), 2.0, 1.0)
rotated = cv2.warpAffine(
    image, matrix, (image.shape[1], image.shape[0]), borderValue=(232, 232, 232)
)
cv2.imwrite("rotated.png", rotated)
