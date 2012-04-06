#This is an example for SimpleCV project.
#The pupose of this file is to load webcam and find all sheets of paper.
#It uses opencv rectangle detection algorithm.
#Originally is was designed to show picture or video on paper,but because
#of bug in sprite function I had to use just simple blue polygon.

from SimpleCV import *
import cv
import math
class SubImage(Image):
	"""Subclass of Image, because I do not want to modify Image class and I want to have code in one file."""
	def findLines2(self, threshold=80, minlinelength=30, maxlinegap=10, cannyth1=50, cannyth2=100):
		"""Copy of original findLines. It is an example for me how to implement functions."""
		em = self._getEdgeMap(cannyth1, cannyth2)
		lines = cv.HoughLines2(em, cv.CreateMemStorage(), cv.CV_HOUGH_PROBABILISTIC, 1.0, cv.CV_PI/180.0, threshold, minlinelength, maxlinegap)
		linesFS = FeatureSet()
		for l in lines:
			linesFS.append(Line(self, l))  
		print linesFS
		return linesFS


	def findSquares(self):
		"""Implementation of OpenCV rectangle detection algorithm.
		Result is array of 4-tuple - 4 points of rectangle.
		TODO: implement more arguments."""
		color_img = cv.GetImage(self.getMatrix())
		def find_squares_from_binary( gray ):
			def is_square(contour):
				def angle(pt1, pt2, pt0):
					"calculate angle contained by 3 points(x, y)"
					dx1 = pt1[0] - pt0[0]
					dy1 = pt1[1] - pt0[1]
					dx2 = pt2[0] - pt0[0]
					dy2 = pt2[1] - pt0[1]

					nom = dx1*dx2 + dy1*dy2
					denom = math.sqrt( (dx1*dx1 + dy1*dy1) * (dx2*dx2 + dy2*dy2) + 1e-10 )
					ang = nom / denom
					return ang

				area = math.fabs( cv.ContourArea(contour) )
				isconvex = cv.CheckContourConvexity(contour)
				s = 0
				if len(contour) == 4 and area > 1000 and isconvex:
					for i in range(1, 4):
						# find minimum angle between joint edges (maximum of cosine)
						pt1 = contour[i]
						pt2 = contour[i-1]
						pt0 = contour[i-2]

						t = math.fabs(angle(pt0, pt1, pt2))
						if s <= t:s = t

					# if cosines of all angles are small (all angles are ~90 degree) 
					# then its a square
					if s < 0.3:return True

				return False
			
			"""
			use contour search to find squares in binary image
			returns list of numpy arrays containing 4 points
			"""
			squares = []
			storage = cv.CreateMemStorage(0)
			contours = cv.FindContours(gray, storage, cv.CV_RETR_TREE, cv.CV_CHAIN_APPROX_SIMPLE, (0,0))  
			storage = cv.CreateMemStorage(0)
			while contours:
				#approximate contour with accuracy proportional to the contour perimeter
				arclength = cv.ArcLength(contours)
				polygon = cv.ApproxPoly( contours, storage, cv.CV_POLY_APPROX_DP, arclength * 0.02, 0)
				if is_square(polygon):
					squares.append(polygon[0:4])
				contours = contours.h_next()

			return squares
		#select even sizes only
		width, height = (color_img.width & -2, color_img.height & -2 )
		timg = cv.CloneImage( color_img ) # make a copy of input image
		gray = cv.CreateImage( (width,height), 8, 1 )

		# select the maximum ROI in the image
		cv.SetImageROI( timg, (0, 0, width, height) )

		# down-scale and upscale the image to filter out the noise
		pyr = cv.CreateImage( (width/2, height/2), 8, 3 )
		cv.PyrDown( timg, pyr, 7 )
		cv.PyrUp( pyr, timg, 7 )

		tgray = cv.CreateImage( (width,height), 8, 1 )
		squares = []

		# Find squares in every color plane of the image
		# Two methods, we use both:
		# 1. Canny to catch squares with gradient shading. Use upper threshold
		# from slider, set the lower to 0 (which forces edges merging). Then
		# dilate canny output to remove potential holes between edge segments.
		# 2. Binary thresholding at multiple levels
		N = 11
		for c in [0, 1, 2]:
			#extract the c-th color plane
			cv.SetImageCOI( timg, c+1 );
			cv.Copy( timg, tgray, None );
			cv.Canny( tgray, gray, 0, 50, 5 )
			cv.Dilate( gray, gray)
			squares = squares + find_squares_from_binary( gray )

			# Look for more squares at several threshold levels
			for l in range(1, N):
				cv.Threshold( tgray, gray, (l+1)*255/N, 255, cv.CV_THRESH_BINARY )
				squares = squares + find_squares_from_binary( gray )

		return squares

def square_dimensions(square):
	"""Function that finds average width and height of square."""
	x1, y1 = square[0]
	x2, y2 = square[1]
	x3, y3 = square[2]
	x4, y4 = square[3]
	width1 = sqrt(pow(x1-x2,2)+pow(y1-y2,2))
	width2 = sqrt(pow(x3-x4,2)+pow(y3-y4,2))
	height1 = sqrt(pow(x1-x3,2)+pow(y1-y3,2)) 
	height2 = sqrt(pow(x2-x4,2)+pow(y2-y4,2)) 
	return (width1+width2) // 2, (height1+height2) // 2

cam = Camera()
#i = SubImage("2.JPG")
#i.findLines2().draw()
#fillimg = Image("img.jpg")
vs = VideoStream("out.avi", fps=15)

framecount = 0
while(framecount < 15 * 10):#save as video od 10 seconds
	i = cam.getImage()
	i.__class__ = SubImage# we need to inherit parent class to child
	for square in i.findSquares():# for every square
		dim = square_dimensions (square)
		#print dim[0] / dim[1] # what is fraction between 
		if ((dim[0] / dim[1] > 0.80) and (dim[0] / dim[1] < 0.83)) or ((dim[0] / dim[1] > 1.40) and (dim[0] / dim[1] < 1.44)):
			pass
			#if fraction of papers dimesions is good then write igmae through it
			i.dl().polygon(square, filled=True, color=Color.BLUE, width=5)
			#i.dl().sprite(fillimg, pos=square[0], scale=0.1)
			#sprite does not work - have to use only blue polygon
		else:
			pass
			#If we want to see every rectangle:
			#print "i", i.width, i.height, float(i.width/i.height)
			#i.dl().polygon(square, filled=False, color=Color.RED, width=5)
			print dim[0] / dim[1] 
	i.show()
	#i.save(vs)# saving output strem does not work, use just photos
	i.save("out2.jpg")
	time.sleep(0.1)
	#framecount= framecount+1
	framecount = 10000
"""
import time
c = Camera
vs = VideoStream("out.avi", fps=15)

framecount = 0
while(framecount < 15 * 600): #record for 5 minutes @ 15fps
    c.getImage().save(vs)
    time.sleep(0.1)
"""
