
from maix import display, camera 
import time


st = time.time()
c = 0

camera.camera.config(size=(320, 240),video=8)
while get_threadrunflag():
    t = camera.capture()
    mks = t.find_qrcodes()
    if time.time() - st > 1:
       c+=1
       st = time.time()
       senddata(('find qrcodes '+str(c)+' s').encode())
    for mk in mks:
      string = mk['payload']
      print(string,time.time())
      if get_wifi_info(string):
        import sys
        sys.exit()
    time.sleep(0.1)
camera.close()
    