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
from skimage.feature import peak_local_max
from skimage.morphology import watershed
from scipy import ndimage
import argparse
import imutils
import cv2
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt 
import json , requests
def detect_shape(c):
    shape = "unidentified"
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.04 * peri, True)
            # if the shape is a triangle, it will have 3 vertices
    if len(approx) == 3:
        shape = "triangle"

    # if the shape has 4 vertices, it is either a square or
    # a rectangle
    elif len(approx) == 4:
        # compute the bounding box of the contour and use the
        # bounding box to compute the aspect ratio
        (x, y, w, h) = cv2.boundingRect(approx)
        ar = w / float(h)

        # a square will have an aspect ratio that is approximately
        # equal to one, otherwise, the shape is a rectangle
        shape = "square" if ar >= 0.95 and ar <= 1.05 else "rectangle"

    # if the shape is a pentagon, it will have 5 vertices
    elif len(approx) == 5:
        shape = "pentagon"
    #elif len(approx) == 6:
      #  shape = "hexagon"
    # otherwise, we assume the shape is a circle
    else:
        shape = "circle"

    # return the name of the shape
    return shape
def detect_coin(image):
    """
    This function detects the coin to get the pixel metric
    """
    src = image
    ### applying thresholding to seperate foreground pixels from background pixels
    src = cv2.GaussianBlur(src, (9, 9), 0)
    shifted = cv2.pyrMeanShiftFiltering(src, 21, 51)
    gray = cv2.cvtColor(shifted, cv2.COLOR_BGR2GRAY)
    thresh,ret = cv2.threshold(gray, 172, 255,
    cv2.THRESH_BINARY)
    D = ndimage.distance_transform_edt(ret)
    localMax = peak_local_max(D, indices=False, min_distance=20,
    labels=ret)
    # perform a connected component analysis on the local peaks,
    # using 8-connectivity, then appy the Watershed algorithm
    markers = ndimage.label(localMax, structure=np.ones((3, 3)))[0]
    labels = watershed(-D, markers, mask=ret)
    # perform edge detection, then perform a dilation + erosion to
    # close gaps in between object edges
    # find contours in the edge map
    r = 70
    for label in np.unique(labels):
        # if the label is zero, we are examining the 'background'
        # so simply ignore it
        if label == 0:
            continue
        # otherwise, allocate memory for the label region and draw
        # it on the mask
        mask = np.zeros(gray.shape, dtype="uint8")
        mask[labels == label] = 255
        # detect contours in the mask and grab the largest one
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)[-2]
        c = max(cnts, key=cv2.contourArea)
        if(detect_shape(c) != "circle"):
            continue
        # draw a circle enclosing the object
        ((x, y), r) = cv2.minEnclosingCircle(c)
        # show the output image
    pixelpermetric = 2.25/float(2*r)
    return pixelpermetric
def detect_object(image):
    ## applies grab cut algorithm to seperate foreground pixels from background pixels
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)

    # perform edge detection, then perform a dilation + erosion to
    # close gaps in between object edges
    edged = cv2.Canny(gray, 50, 100)
    edged = cv2.dilate(edged, None, iterations=1)
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[1]
    orig = image
    c = max(cnts, key = cv2.contourArea)
    box = cv2.minAreaRect(c)
    box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
    box = np.array(box, dtype="int")
    box = perspective.order_points(box)
    return box
def midpoint(ptA, ptB):
    """This function returns a midpoint of the two points given as input"""
    return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)

def detect(img_coin,img_object):
    """
    This function detects the coin to get the pixel metric and then returns the length and width of the box detected.
    This function takes an image as its argument and returns length and width
    """
    pixelsPerMetric = detect_coin(img_coin)
    print pixelsPerMetric
    box = detect_object(img_object)
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
    width = dA * pixelsPerMetric
    length = dB * pixelsPerMetric
    if(width>length):
        temp=width
        width=length
        length=temp
    return length,width

def url_to_image(url):
    """ 
    This function downloads the image from the url and convert it into a format 
    so that it can be processed using OpenCV library. 
    This function downloads the image, convert it to a NumPy array, and then read
    it into OpenCV format"""
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
    imagetopc = url_to_image(topimageurl)
    imagetopo = url_to_image(topimageurl)
    length,width=detect(imagetopc,imagetopo)
    imagefrontc = url_to_image(frontimageurl)
    imagefronto = url_to_image(frontimageurl)
    length1,width1=detect(imagefrontc,imagefronto)
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
