from random import randint
import sys, traceback, threading, socket

from VideoStream import VideoStream
from RtpPacket import RtpPacket

class ServerWorker:
	SETUP = 'SETUP'
	PLAY = 'PLAY'
	PAUSE = 'PAUSE'
	TEARDOWN = 'TEARDOWN'
	
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT

	OK_200 = 0
	FILE_NOT_FOUND_404 = 1
	CON_ERR_500 = 2
	
	clientInfo = {}
	#khởi tạo đối tượng
	def __init__(self, clientInfo):
		self.clientInfo = clientInfo
	#khởi động một luồng mới để nhận request RTSP từ client	
	def run(self):
		threading.Thread(target=self.recvRtspRequest).start()
	#nhận và xử lý các yêu cầu RTSP từ client
	def recvRtspRequest(self):
		"""Receive RTSP request from the client."""
		connSocket = self.clientInfo['rtspSocket'][0]
		while True:            
			data = connSocket.recv(256)
			if data:
				print("Data received:\n" + data.decode("utf-8"))
				self.processRtspRequest(data.decode("utf-8"))
	#xử lý yêu cầu RTSP từ client, bao gồm các yêu cầu SETUP, PLAY, PAUSE, và TEARDOWN.
	def processRtspRequest(self, data):
		"""Process RTSP request sent from the client."""
		# Lấy loại yêu cầu
		request = data.split('\n')
		line1 = request[0].split(' ')
		requestType = line1[0]
		
		# Lấy tên file media
		filename = line1[1]
		
		# Lấy số thứ tự RTSP
		seq = request[1].split(' ')
		# print(f"\n\n\nseq: {seq}\n\n\n")
		
		# Xử lý yêu cầu SETUP
		if requestType == self.SETUP:
			if self.state == self.INIT:
				# Cập nhật trạng thái
				print("processing SETUP\n")
				
				try:
					self.clientInfo['videoStream'] = VideoStream(filename)
					self.state = self.READY
				except IOError:
					self.replyRtsp(self.FILE_NOT_FOUND_404, seq[1])
				
				# Tạo ID phiên RTSP ngẫu nhiên
				self.clientInfo['session'] = randint(100000, 999999)
				
				# Gửi phản hồi RTSP
				self.replyRtsp(self.OK_200, seq[1])
				
				# Lấy tham số cổng RTP/UDP nhập từ dòng lệnh 
				self.clientInfo['rtpPort'] = request[2].split(' ')[3]
		
		# Xử lý yêu cầu PLAY	
		elif requestType == self.PLAY:
			if self.state == self.READY:
				print("processing PLAY\n")
				self.state = self.PLAYING
				
				# Tạo một socket mới cho RTP/UDP
				self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				
				self.replyRtsp(self.OK_200, seq[1])
				
				# Tạo một thread mới và bắt đầu gửi các gói RTP
				self.clientInfo['event'] = threading.Event()
				self.clientInfo['worker']= threading.Thread(target=self.sendRtp) 
				self.clientInfo['worker'].start()
		
		# Xử lý yêu cầu PAUSE
		elif requestType == self.PAUSE:
			if self.state == self.PLAYING:
				print("processing PAUSE\n")
				self.state = self.READY
				
				self.clientInfo['event'].set()
			
				self.replyRtsp(self.OK_200, seq[1])
		
		# Xử lý yêu cầu TEARDOWN
		elif requestType == self.TEARDOWN:
			print("processing TEARDOWN\n")

			self.clientInfo['event'].set()
			
			self.replyRtsp(self.OK_200, seq[1])
			
			# Đóng socket RTP
			self.clientInfo['rtpSocket'].close()
	#Gửi các RTP packets qua UDP		
	def sendRtp(self):
		"""Send RTP packets over UDP."""
		while True:
			self.clientInfo['event'].wait(0.05) 
			
			# Dừng việc gửi nếu yêu cầu là PAUSE hoặc TEARDOWN
			if self.clientInfo['event'].isSet(): 
				break 
				
			# Lấy khung hình tiếp theo của luồng video và chuyển đổi thành dữ liệu 
			data = self.clientInfo['videoStream'].nextFrame()
			if data: 
				frameNumber = self.clientInfo['videoStream'].frameNbr()
				try:
					address = self.clientInfo['rtspSocket'][1][0]
					port = int(self.clientInfo['rtpPort'])
					self.clientInfo['rtpSocket'].sendto(self.makeRtp(data, frameNumber),(address,port))
				except:
					print("Connection Error")
					#print('-'*60)
					#traceback.print_exc(file=sys.stdout)
					#print('-'*60)
	#Chia nhỏ dữ liệu video thành các gói RTP
	def makeRtp(self, payload, frameNbr):
		"""RTP-packetize the video data."""
		version = 2
		padding = 0
		extension = 0
		cc = 0
		marker = 0
		pt = 26 # kiểu MJPEG
		seqnum = frameNbr
		ssrc = 0 
		
		rtpPacket = RtpPacket()
		
		rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
		
		return rtpPacket.getPacket()
	#Trả lời các yêu cầu RTSP từ client	
	def replyRtsp(self, code, seq):
		"""Send RTSP reply to the client."""
		if code == self.OK_200:
			#print("200 OK")
			reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session'])
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send(reply.encode())
		
		# Các thông báo lỗi
		elif code == self.FILE_NOT_FOUND_404:
			print("404 NOT FOUND")
		elif code == self.CON_ERR_500:
			print("500 CONNECTION ERROR")
