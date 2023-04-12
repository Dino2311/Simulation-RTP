from tkinter import *
import tkinter.messagebox as tkMessageBox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	
	# Khởi tạo
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	#Tạo giao diện người dùng	
	def createWidgets(self):
		"""Build GUI."""
		# Tạo nút Setup
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Tạo nút Play		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Tạo nút Pause			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Tạo nút Teardown
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Tạo một label để hiển thị movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	#xử lý sự kiện khi người dùng nhấn nút "Setup". 
	def setupMovie(self):
		"""Setup button handler."""
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)
	#xử lý sự kiện khi người dùng nhấn nút "Teardown". 
	def exitClient(self):
		"""Teardown button handler."""
		self.sendRtspRequest(self.TEARDOWN)		
		self.master.destroy() # Close the gui window
		os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT) # Delete the cache image from video
	#xử lý sự kiện khi người dùng nhấn nút "Pause". 
	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	#xử lý sự kiện khi người dùng nhấn nút "Play". 
	def playMovie(self):
		"""Play button handler."""
		if self.state == self.READY:
			# Create a new thread to listen for RTP packets
			threading.Thread(target=self.listenRtp).start()
			self.playEvent = threading.Event()
			self.playEvent.clear()
			self.sendRtspRequest(self.PLAY)
	#lắng nghe các gói RTP và cập nhật trạng thái của ứng dụng. 
	def listenRtp(self):		
		"""Listen for RTP packets."""
		while True:
			try:
				data = self.rtpSocket.recv(20480)
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)
					
					currFrameNbr = rtpPacket.seqNum()
					print("Current Seq Num: " + str(currFrameNbr))
										
					if currFrameNbr > self.frameNbr: # Discard the late packet
						self.frameNbr = currFrameNbr
						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
			except:
				# Stop listening upon requesting PAUSE or TEARDOWN
				if self.playEvent.isSet(): 
					break
				
				# Upon receiving ACK for TEARDOWN request,
				# close the RTP socket
				if self.teardownAcked == 1:
					self.rtpSocket.shutdown(socket.SHUT_RDWR)
					self.rtpSocket.close()
					break
	#ghi khung hình nhận được vào tệp cache và trả về tên tệp cache. 
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(cachename, "wb")
		file.write(data)
		file.close()
		
		return cachename
	#cập nhật hình ảnh đang xem trên giao diện người dùng
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		photo = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image = photo, height=288) 
		self.label.image = photo
	#tạo một đối tượng socket để kết nối với máy chủ thông qua địa chỉ IP và cổng được chỉ định. 
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkMessageBox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' %self.serverAddr)
	# gửi các yêu cầu RTSP tới máy chủ
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		
		# Yêu cầu Setup 
		if requestCode == self.SETUP and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()
			# Update RTSP sequence number.
			# ...
			self.rtspSeq = 1

			# Write the RTSP request to be sent.
			# request = ...
			request = "SETUP " + str(self.fileName) + "\n " + str(self.rtspSeq) + " \n RTSP/1.0 RTP/UDP " + str(self.rtpPort)

			self.rtspSocket.send(request.encode())
			# Keep track of the sent request.
			# self.requestSent = ...
			self.requestSent = self.SETUP
		
		# Yêu cầu request
		elif requestCode == self.PLAY and self.state == self.READY:
			# Update RTSP sequence number.
			# ...
			self.rtspSeq = self.rtspSeq + 1
			# Write the RTSP request to be sent.
			# request = ...
			request = "PLAY " + "\n " + str(self.rtspSeq)

			self.rtspSocket.send(request.encode("utf-8"))
			print ('-'*60 + "\nPLAY request sent to Server...\n" + '-'*60)
			# Keep track of the sent request.
			# self.requestSent = ...
			self.requestSent = self.PLAY
		
		# Yêu cầu Pause 
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			# Update RTSP sequence number.
			# ...
			self.rtspSeq = self.rtspSeq + 1
			# Write the RTSP request to be sent.
			# request = ...
			request = "PAUSE " + "\n " + str(self.rtspSeq)
			self.rtspSocket.send(request.encode("utf-8"))
			print ('-'*60 + "\nPAUSE request sent to Server...\n" + '-'*60)
			# Keep track of the sent request.
			# self.requestSent = ...
			self.requestSent = self.PAUSE
			
		# Yêu cầu Teardown 
		elif requestCode == self.TEARDOWN and not self.state == self.INIT:
			# Update RTSP sequence number.
			# ...
			self.rtspSeq = self.rtspSeq + 1
			# Write the RTSP request to be sent.
			# request = ...
			request = "TEARDOWN " + "\n " + str(self.rtspSeq)
			self.rtspSocket.send(request.encode("utf-8"))
			print ('-'*60 + "\nTEARDOWN request sent to Server...\n" + '-'*60)
			# Keep track of the sent request.
			# self.requestSent = ...
			self.requestSent = self.TEARDOWN
		else:
			return
		
		# Send the RTSP request using rtspSocket.
		# ...
		
		print('\nData sent:\n' + request)
	#nhận phản hồi RTSP từ máy chủ
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True:
			reply = self.rtspSocket.recv(1024)
			
			if reply: 
				self.parseRtspReply(reply.decode("utf-8"))
			
			# Close the RTSP socket upon requesting Teardown
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		lines = data.split('\n')
		seqNum = int(lines[1].split(' ')[1])
		
		# Process only if the server reply's sequence number is the same as the request's
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session
			
			# Process only if the session ID is the same
			if self.sessionId == session:
				if int(lines[0].split(' ')[1]) == 200: 
					if self.requestSent == self.SETUP:
						#-------------
						# TO COMPLETE
						#-------------
						# Update RTSP state.
						print ("Updating RTSP state...")
						# self.state = ...
						self.state = self.READY
						# Open RTP port.
						#self.openRtpPort()
						print ("Setting Up RtpPort for Video Stream")
						self.openRtpPort() 

					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING
						print ('-'*60 + "\nClient is PLAYING...\n" + '-'*60)

					elif self.requestSent == self.PAUSE:
						self.state = self.READY

						# The play thread exits. A new thread is created on resume.
						self.playEvent.set()
					elif self.requestSent == self.TEARDOWN:
						# self.state = ...
						
						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1 
	#mở cổng RTP trên socket
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		# self.rtpSocket = ...
		self.rtpSocket.settimeout(0.5)
		# Set the timeout value of the socket to 0.5sec
		# ...
		
		try:
			self.rtpSocket.bind((self.serverAddr,self.rtpPort))   # WATCH OUT THE ADDRESS FORMAT!!!!!  rtpPort# should be bigger than 1024
			#self.rtpSocket.listen(5)
			print ("Bind RtpPort Success")
		except:
			tkMessageBox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)
	#xử lý sự kiện người dùng đóng GUI
	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.pauseMovie()
		if tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?"):
			self.exitClient()
		else: # When the user presses cancel, resume playing.
			self.playMovie()

