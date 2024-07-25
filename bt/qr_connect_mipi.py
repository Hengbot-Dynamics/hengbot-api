import _maix_image
import time


from hobot_vio import libsrcampy

cam = libsrcampy.Camera()

ret = cam.open_cam(0, -1, 30, 640, 480)

st = time.time()
c = 0

while get_threadrunflag():
    img = cam.get_img()


    t = _maix_image.load(img,size = (640, 480),mode = "L")

    mks = t.find_qrcodes()
    if time.time() - st > 1:
       c+=1
       st = time.time()
       senddata(('find qrcodes '+str(c)+' s').encode())
    for mk in mks:
      string = mk['payload']
      print(string,time.time())
      if get_wifi_info(string):
        cam.close_cam()
        import sys
        sys.exit()
    time.sleep(0.1)

cam.close_cam()