class VideoStream:
	def __init__(self, filename):
		self.filename = filename #Lưu tên video
		try:
			self.file = open(filename, 'rb') # Mở file video dưới dạng binary mode
		except:
			raise IOError # Nếu mở file không thành công, ném lỗi
		self.frameNum = 0 # Số thứ tự của frame đang đọc tại thời điểm hiện tại
		
	def nextFrame(self):
		"""Lấy frame kế tiếp."""
		data = self.file.read(5) # Đọc 5 byte đầu tiên của frame, chứa độ dài của frame
		if data: # Nếu đọc được dữ liệu
			framelength = int(data) # Chuyển độ dài frame sang kiểu số nguyên
							
			# Read the current frame
			data = self.file.read(framelength) # Đọc toàn bộ nội dung của frame
			self.frameNum += 1 # Tăng số thứ tự của frame lên 1
		return data # Trả về nội dung của frame
		
	def frameNbr(self):
		"""Lấy số thứ tự của frame."""
		return self.frameNum
	
	