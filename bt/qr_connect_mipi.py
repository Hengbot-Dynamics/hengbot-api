
from maix import display, camera, image, zbar
import time


from hobot_vio import libsrcampy

camera = libsrcampy.Camera()
encode = libsrcampy.Encoder()
ret = camera.open_cam(0, -1, 30, 1920, 1080)
ret = encode.encode(0, 3, 1920, 1080)
ret = libsrcampy.bind(camera, encode)

st = time.time()
c = 0

while True:
    img = encode.get_img()
    with open("img.jpg", "wb") as f:
        f.write(img)
        f.close()
    t = image.open("img.jpg")
    i = t.resize(640,360)
    mks = i.find_qrcodes()
    if time.time() - st > 1:
       c+=1
       st = time.time()
       senddata(('find qrcodes '+str(c)+' s').encode())
    for mk in mks:
      string = mk['payload']
      print(string,time.time())
      get_wifi_info(string)
    time.sleep(0.1)
    