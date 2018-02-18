# USAGE
# python object_movement.py --video object_tracking_example.mp4
# python object_movement.py

# import the necessary packages
from collections import deque
import numpy as np
import argparse
import imutils
import cv2
import math
import time


class BossClass:
	speed = 2
	Bdirection = 0
	radius = 20
	position = [200, 200]


	def incSize(self):
		self.radius += 1

	def incSpeed(self):
		self.speed += 1

	def move(self, pos, PRadius, player):
		deltx = pos[0] - self.position[0]
		delty = self.position[1] - pos[1]
		if deltx != 0:
			Bdirection = math.atan(delty / deltx)
			if deltx>0:
				self.position[0] += self.speed * math.cos(Bdirection)
				self.position[1] += self.speed * -math.sin(Bdirection)
			else:
				self.position[0] += self.speed * -math.cos(Bdirection)
				self.position[1] += self.speed * math.sin(Bdirection)


		if math.sqrt(deltx ** 2 + delty ** 2) <= self.radius + PRadius:
			player.damage()

class PlayerClass:

	# VARS
	lives = 0
	buffer = 0

	def __init__(self):
		# CONSTRUCTER
		lives = 3
		buffer = 0

	def damage(self):
		lives = self.lives - 1
		self.dead()
		if self.buffer != 0:
			buffer = time.time() - self.buffer
		else:
			buffer = time.time()
		if buffer > 2:
			buffer = 0;

	def dead(self):
		return self.lives == 0


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video",
	help="path to the (optional) video file")
ap.add_argument("-b", "--buffer", type=int, default=32,
	help="max buffer size")
args = vars(ap.parse_args())

# define the lower and upper boundaries of the "green"
# ball in the HSV color space
greenLower = (29, 86, 6)
greenUpper = (64, 255, 255)

# initialize the list of tracked points, the frame counter,
# and the coordinate deltas
pts = deque(maxlen=args["buffer"])
counter = 0
(dX, dY) = (0, 0)
direction = ""

boss = BossClass()
player = PlayerClass()
# if a video path was not supplied, grab the reference
# to the webcam
if not args.get("video", False):
	camera = cv2.VideoCapture(0)

# otherwise, grab a reference to the video file
else:
	camera = cv2.VideoCapture(args["video"])

# keep looping
while True:
	# grab the current frame
	(grabbed, frame) = camera.read()

	# if we are viewing a video and we did not grab a frame,
	# then we have reached the end of the video
	if args.get("video") and not grabbed:
		break

	# resize the frame, blur it, and convert it to the HSV
	# color space
	frame = imutils.resize(frame, width=600)
	# blurred = cv2.GaussianBlur(frame, (11, 11), 0)
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

	# construct a mask for the color "green", then perform
	# a series of dilations and erosions to remove any small
	# blobs left in the mask
	mask = cv2.inRange(hsv, greenLower, greenUpper)
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)

	# find contours in the mask and initialize the current
	# (x, y) center of the ball
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)[-2]
	center = None

	# only proceed if at least one contour was found
	if len(cnts) > 0:
		# find the largest contour in the mask, then use
		# it to compute the minimum enclosing circle and
		# centroid
		c = max(cnts, key=cv2.contourArea)
		((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)
		center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

		# only proceed if the radius meets a minimum size
		if radius > 10:
			# draw the circle and centroid on the frame,
			# then update the list of tracked points
			#cv2.circle(frame, (int(x), int(y)), int(radius),
			#	(0, 255, 255), 2)
			cv2.circle(frame, center, 5, (0, 0, 255), -1)
			pts.appendleft(center)
	boss.move([center[0], center[1]], 5, player)
	cv2.circle(frame, (round(boss.position[0]), round(boss.position[1])), boss.radius, (0, 255, 255),-1)
	# loop over the set of tracked points
	for i in np.arange(1, len(pts)):
		# if either of the tracked points are None, ignore
		# them
		if pts[i - 1] is None or pts[i] is None:
			continue

		# check to see if enough points have been accumulated in
		# the buffer
		if counter >= 10 and i == 1 and pts[-10] is not None:
			# compute the difference between the x and y
			# coordinates and re-initialize the direction
			# text variables
			dX = pts[-10][0] - pts[i][0]
			dY = pts[-10][1] - pts[i][1]
			(dirX, dirY) = ("", "")

			# ensure there is significant movement in the
			# x-direction
			if np.abs(dX) > 20:
				dirX = "East" if np.sign(dX) == 1 else "West"

			# ensure there is significant movement in the
			# y-direction
			if np.abs(dY) > 20:
				dirY = "North" if np.sign(dY) == 1 else "South"

			# handle when both directions are non-empty
			if dirX != "" and dirY != "":
				direction = "{}-{}".format(dirY, dirX)

			# otherwise, only one direction is non-empty
			else:
				direction = dirX if dirX != "" else dirY

		# otherwise, compute the thickness of the line and
		# draw the connecting lines
		thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
		cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)

		if(center[0] > 10 ):
			cv2.circle(frame, (center[0], center[1]), 63, (0, 0, 255), -1)


	# show the movement deltas and the direction of movement on
	# the frame
	cv2.putText(frame, direction, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
		0.65, (0, 0, 255), 3)
	if not (center == (None)):
		cv2.putText(frame, "dx: {}, dy: {}".format(center[0],center[1]),
			(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
			0.35, (0, 0, 255), 1)
		cv2.putText(frame, "dx: {}, dy: {}".format(round(boss.position[0]),round(boss.position[1])),
				(10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX,
				0.35, (0, 0, 255), 1)

	# show the frame to our screen and increment the frame counter
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF
	counter += 1

	# if the 'q' key is pressed, stop the loop
	if key == ord("q"):
		break

# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()
