
from maix import image, camera
import time


from hobot_vio import libsrcampy

cam = libsrcampy.Camera()
encode = libsrcampy.Encoder()
ret = cam.open_cam(0, -1, 30, 640, 480)
ret = encode.encode(0, 3, 640, 480)
ret = libsrcampy.bind(cam, encode)

st = time.time()
c = 0

while get_threadrunflag():
    img = encode.get_img()
    with open("img.jpg", "wb") as f:
        f.write(img)
        f.close()
    t = image.open("img.jpg")

    mks = t.find_qrcodes()
    if time.time() - st > 1:
       c+=1
       st = time.time()
       senddata(('find qrcodes '+str(c)+' s').encode())
    for mk in mks:
      string = mk['payload']
      print(string,time.time())
      if get_wifi_info(string):
        encode.close()
        cam.close_cam()
        import sys
        sys.exit()
    time.sleep(0.1)
encode.close()
cam.close_cam()
