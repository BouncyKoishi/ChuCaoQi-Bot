# from nonebot import on_natural_language, NLPSession, get_bot
# from utils import extractImgUrls
# from kusa_base import config
#
# import io
# import os.path
# import httpx
# import cv2
# import numpy as np
# from pathlib import Path
# from PIL import Image
#
# import torch
# from torch import nn
# from torchvision import transforms
#
# transform = transforms.Compose([transforms.ToTensor(),
#                                 transforms.Normalize(mean=0.5, std=0.5)])
#
#
# class Net(nn.Module):
#     def __init__(self):
#         super(Net, self).__init__()
#         self.conv1 = nn.Conv2d(3, 32, 5, 1, 2)
#         self.max1 = nn.MaxPool2d(2)
#         self.bn1 = nn.BatchNorm2d(32)
#         self.relu1 = nn.ReLU()
#         self.conv2 = nn.Conv2d(32, 32, 5, 1, 2)
#         self.max2 = nn.MaxPool2d(2)
#         self.bn2 = nn.BatchNorm2d(32)
#         self.relu2 = nn.ReLU()
#         self.conv3 = nn.Conv2d(32, 64, 5, 1, 2)
#         self.max3 = nn.MaxPool2d(2)
#         self.bn3 = nn.BatchNorm2d(64)
#         self.relu3 = nn.ReLU()
#         self.fla = nn.Flatten()
#         self.lin1 = nn.Linear(64 * 4 * 4, 64)
#         self.drop = nn.Dropout(0.25)
#         self.lin2 = nn.Linear(64, 11)
#
#     def forward(self, x):
#         x = self.conv1(x)
#         x = self.max1(x)
#         x = self.bn1(x)
#         x = self.relu1(x)
#         x = self.conv2(x)
#         x = self.max2(x)
#         x = self.bn2(x)
#         x = self.relu2(x)
#         x = self.conv3(x)
#         x = self.max3(x)
#         x = self.bn3(x)
#         x = self.relu3(x)
#         x = self.fla(x)
#         x = self.lin1(x)
#         x = self.drop(x)
#         x = self.lin2(x)
#         return x
#
#
# model = Net()
# model_path = os.path.join(Path(__file__).parent, "Nailong(0.7123).pth")
# if os.path.exists(model_path):
#     model.load_state_dict(torch.load(model_path, weights_only=True, map_location='cpu'))
# model.eval()
#
#
# def check_image(image: np.ndarray) -> bool:
#     """
#     :param image: OpenCV图像数组。
#     :return: 如果图像中有奶龙，返回True；否则返回False。
#     """
#     image = cv2.resize(image, (32, 32))
#     image = transform(image)
#     image = image.unsqueeze(0)
#     with torch.no_grad():
#         output = model(image)
#         print(output)
#         print(output.argmax(1))
#         if output.argmax(1) == 10:
#             return True
#         else:
#             return False
#
#
# async def download_image(url: str) -> np.ndarray:
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url)
#         if response.status_code == 200:
#             image_data = response.content
#
#             # 将字节数据加载为Pillow图像对象
#             image = Image.open(io.BytesIO(image_data))
#
#             # 检查图像格式并处理
#             if image.format == 'GIF' and hasattr(image, 'is_animated') and image.is_animated:
#                 # 处理GIF动图：仅获取第一帧
#                 image = image.convert("RGB")
#                 image = image.copy()  # 获取第一帧
#             else:
#                 # 对于非GIF图像（如JPEG）
#                 image = image.convert("RGB")
#
#             # 将Pillow图像转换为NumPy数组
#             image_array = np.array(image)
#
#             # OpenCV通常使用BGR格式，因此需要转换
#             if len(image_array.shape) == 3 and image_array.shape[2] == 3:
#                 image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
#
#             return image_array
#
#
# @on_natural_language(only_to_me=False, allow_empty_message=False)
# async def handle_function(session: NLPSession):
#     groupId = session.event.group_id
#     strippedArg = session.msg
#
#     if groupId != config['group']['main']:
#         return
#     if '[CQ:image' not in strippedArg:
#         return
#
#     bot = get_bot()
#
#     imageUrls = extractImgUrls(strippedArg)
#     for url in imageUrls:
#         image = await download_image(url)
#         if check_image(image):
#             print("检测到奶龙")
#             #await bot.call_api('delete_msg', message_id=session.event.message_id)
#             await bot.send_group_msg(group_id=groupId, message="本群禁止发送奶龙！")
#             return
