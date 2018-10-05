# import the necessary packages
import numpy as np
import argparse
import datetime
import imutils
import urllib
import httplib
import time
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
from gpiozero import *

cam=PiCamera()
cam.resolution=(640,480)
cam.framerate=32
rawCapture=PiRGBArray(cam,size=(640,480))
cam.vflip = True

time.sleep(1)

now = datetime.datetime.now()
time_delay = now + datetime.timedelta(minutes = 15)

# initialize the average frame 
avg = None
min_area = 2000

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the video file")
ap.add_argument("-a", "--min-area", type=int, default=3000, help="minimum area size")
args = vars(ap.parse_args())

# video file
camera = cv2.VideoCapture(args["video"])

# GMM background-foreground initialization
fgbg=cv2.bgsegm.createBackgroundSubtractorMOG()

# initialize variables
flag = 0
movement = 1
ppl = 0

# loop over the frames of the video or the live stream
while True:
        
	# grab the current frame and initialize the occupied/unoccupied text
	(grabbed, frame) = camera.read()
	text = "Unoccupied"
       
	# if the frame could not be grabbed, then read from camera
	if not grabbed:
		cam.capture(rawCapture, format="bgr", use_video_port=True)
                frame=rawCapture.array
                rawCapture.truncate(0)

	# apply GMM (Gaussian Mixture Model)
	fgmask=fgbg.apply(frame)

	# remove noise with erosion-dilate, then find contours
	erosion=cv2.erode(fgmask,(21, 21),iterations=2)
	thresh=cv2.dilate(erosion,(21, 21),iterations=2)
	(_, cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

	# find the max contour
	if len(cnts) > 0:
	
    		# sort the contours and find the largest one
    		cnt =    sorted(cnts, key = cv2.contourArea, reverse = True)[0]
               
		if cv2.contourArea(cnt) > args["min_area"]:
                       
                        # compute the bounding box for the contour, draw it on the frame,
                        # and update the text
                        (x, y, w, h) = cv2.boundingRect(cnt)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        text = "Occupied"
                        flag = 1
                
                else:
                        flag = 0
                        movement = 0
                        

        if movement == 0:
                if flag == 1:
                        movement = 1
                        ppl +=1
                                
                  
                                
           
	# draw the text and timestamp on the frame
	cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
	cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
		(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
	cv2.putText(frame, "People: {}" .format(ppl), (10,40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

	cv2.imshow("Frame", frame)
	cv2.imshow("Mask", thresh)

        #Upload data after an amount of time
        if time_delay < datetime.datetime.now():
                  
            now = datetime.datetime.now()
            time_delay = now + datetime.timedelta(minutes = 15)
                        
            #Upload data to ThingSpeak
            f = urllib.urlencode({'field1' : ppl,'key' : 'ThingSpeak' })
            headers = {"Content-typZZe": "application/x-www-form-urlencoded","Accept": "text/plain"}
            conn=httplib.HTTPConnection("api.thingspeak.com:80")
                
            try:
                    conn.request("POST", "/update", f, headers)
                    response=conn.getresponse()
                    print response.status, response.reason
                    data = response.read()
                    conn.close()
                    ppl = 0
            except:
                    print "Connection Failed"

        #press Q if you want to stop the video or live stream
	k=cv2.waitKey(1) & 0xff
	if k==ord("q"):
	    	break

# cleanup the camera and close any open windows
cv2.destroyAllWindows()
