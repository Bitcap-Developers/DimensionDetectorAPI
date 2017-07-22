"""
Documentation for this module:
This module takes the url of the image of top face and front face of the box and computes the 
dimensions of the box and finally returns the type of package that would be required for shipping.
The code is written in python and image processing is performed with the image processing library opencv.
the code converts the BGR image to HSV image and then detects the coin in the image using thresholding
(This can be removed using object detection).Then it calculates a pixel metric which provides conversion between
pixel and centimeters.  This ratio is then used to detect the dimension of the object
to be packaged.
"""
#import the necessary packages

from django.shortcuts import render
import sys
sys.path.append('/usr/local/lib/python2.7/site-packages')
from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import numpy as np
import urllib
import argparse
import imutils
import cv2
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt 
import json , requests

def detect(image):
	"""
	This function detects the coin to get the pixel metric and then returns the length and width of the box detected.
	This function takes an image as its argument and returns length and width"""
	src=image.copy()
	src =cv2.cvtColor(src,cv2.COLOR_BGR2HSV)
	lower = np.array([40,100,100])
	h2=120
	s2=135
	v2=135
	upper = np.array([h2,s2,v2])
	mask = cv2.inRange(image, lower, upper)
	output = cv2.bitwise_and(image, image, mask = mask)
	gray = cv2.GaussianBlur(output, (7, 7), 0)
	# perform edge detection, then perform a dilation + erosion to
	# close gaps in between object edges
	edged = cv2.Canny(gray, 50, 100)
	edged = cv2.dilate(edged, None, iterations=1)
	edged = cv2.erode(edged, None, iterations=1)

	# find contours in the edge map
	cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
	cv2.CHAIN_APPROX_SIMPLE)
	cnts = cnts[0] if imutils.is_cv2() else cnts[1]

	# sort the contours from left-to-right and initialize the
	# 'pixels per metric' calibration variable
	(cnts, _) = contours.sort_contours(cnts)    
	# loop over the contours individually
	c1=cnts[0]
	c1 = max(cnts, key = cv2.contourArea)
	
	orig = image.copy()
	box = cv2.minAreaRect(c1)
	box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
	box = np.array(box, dtype="int")

	# order the points in the contour such that they appear
	# in top-left, top-right, bottom-right, and bottom-left
	# order, then draw the outline of the rotated bounding
	# box
	box = perspective.order_points(box)
	cv2.drawContours(orig, [box.astype("int")], -1, (0, 255, 0), 2)

	# loop over the original points and draw them
	for (x, y) in box:
		cv2.circle(orig, (int(x), int(y)), 5, (0, 0, 255), -1)
	
	# unpack the ordered bounding box, then compute the midpoint
	# between the top-left and top-right coordinates, followed by
	# the midpoint between bottom-left and bottom-right coordinates
	(tl, tr, br, bl) = box
	(tltrX, tltrY) = midpoint(tl, tr)
	(blbrX, blbrY) = midpoint(bl, br)

	# compute the midpoint between the top-left and top-right points,
	# followed by the midpoint between the top-righ and bottom-right
	(tlblX, tlblY) = midpoint(tl, bl)
	(trbrX, trbrY) = midpoint(tr, br)

	# compute the Euclidean distance between the midpoints
	dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
	dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))
	#initialise pixel matrix
	pixelsPerMetric = 2.3/dB
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (7, 7), 0)

	# perform edge detection, then perform a dilation + erosion to
	# close gaps in between object edges
	edged = cv2.Canny(gray, 50, 100)
	edged = cv2.dilate(edged, None, iterations=1)
	edged = cv2.erode(edged, None, iterations=1)
	
	cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
	cnts = cnts[1]
	c = max(cnts, key = cv2.contourArea)
	orig = image.copy()
	box = cv2.minAreaRect(c)
	box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
	box = np.array(box, dtype="int")

	# order the points in the contour such that they appear
	# in top-left, top-right, bottom-right, and bottom-left
	# order, then draw the outline of the rotated bounding
	# box
	box = perspective.order_points(box)
	cv2.drawContours(orig, [box.astype("int")], -1, (0, 255, 0), 2)

	# loop over the original points and draw them
	for (x, y) in box:
		cv2.circle(orig, (int(x), int(y)), 5, (0, 0, 255), -1)
	
	# unpack the ordered bounding box, then compute the midpoint
	# between the top-left and top-right coordinates, followed by
	# the midpoint between bottom-left and bottom-right coordinates
	(tl, tr, br, bl) = box
	(tltrX, tltrY) = midpoint(tl, tr)
	(blbrX, blbrY) = midpoint(bl, br)

	# compute the midpoint between the top-left and top-right points,
	# followed by the midpoint between the top-righ and bottom-right
	(tlblX, tlblY) = midpoint(tl, bl)
	(trbrX, trbrY) = midpoint(tr, br)

	
	# compute the Euclidean distance between the midpoints
	dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
	dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))
	# compute the size of the object
	width = dA * pixelsPerMetric
	length = dB * pixelsPerMetric
	if(width>length):
		temp=width
		width=length
		length=temp
	return length,width

def midpoint(ptA, ptB):
	"""This function returns a midpoint of the two points given as input
	"""
	return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)

def url_to_image(url):
	""" 
	This function downloads the image from the url and convert it into a format 
	so that it can be processed using OpenCV library. 
	This function downloads the image, convert it to a NumPy array, and then read
	it into OpenCV format
	"""
	resp = urllib.urlopen(url)

	image = np.asarray(bytearray(resp.read()), dtype="uint8")
	image = cv2.imdecode(image, cv2.IMREAD_COLOR)
 
	# return the image
	return image

@csrf_exempt
def fun(request):
	""" This function acts as a caller function which processes the request from the server to get the dimensions
		This function performs the required computation and returns the type of box that would ffit to the user requirements
	"""
	x = json.loads(request.body)
	topimageurl = x['url1']
	frontimageurl = x['url2']
	print "The url is "+topimageurl
	#load the image, convert it to grayscale, and blur it slightly
	# load the image, convert it to grayscale, and blur it slightly
	imagetop = url_to_image(topimageurl)
	length,width=detect(imagetop)
	
	imagefront = url_to_image(frontimageurl)
	length1,width1=detect(imagefront)   
	
	if(width1<length1):
		height=width1
	else:
		height=length1
	
	boxNAme = ''
	if(length<23 and width<35 and height<2):
		boxNAme = 'Envelope 1'
	elif(length<34 and width<18 and height<10):
		boxNAme = 'Box 2'
	elif(length<34 and width<32 and height<10):
		boxNAme = 'Box 3'
	elif(length<34 and width<32 and height<18):
		boxNAme = 'Box 4'
	elif(length<34 and width<32 and height<34):
		boxNAme = 'Box 5'
	elif(length<42 and width<36 and height<37):
		boxNAme = 'Box 6'
	elif(length<48 and width<40 and height<39):
		boxNAme = 'Box 7'
	else:
		boxNAme = 'Box 4'

	print "Length is ",length,"Width is ",width,"height is ",height
	box = {'boxName' : boxNAme}
	jsonResponse=json.dumps(box,indent=4)
	return HttpResponse(jsonResponse,content_type="application/json")
	
