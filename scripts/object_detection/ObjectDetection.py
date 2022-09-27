import cv2
import matplotlib.pyplot as plt
from PIL import Image
from torchvision import transforms

input_image = Image.open(
    "/Users/devdesign/Documents/Blender Scripting/fashionsynth/scripts/object_detection/jacket.png")

plt.imshow(input_image)
plt.show()

Transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]),
])

transformed_image = Transform(input_image)

