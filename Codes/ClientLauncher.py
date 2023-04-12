import sys
from tkinter import Tk
from Client import Client

if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]
		serverPort = sys.argv[2]
		rtpPort = sys.argv[3]
		fileName = sys.argv[4]	
	except:
		print("[Cu phap su dung: ClientLauncher.py Server_name Server_port RTP_port Video_file]\n")	
	
	root = Tk()
	
	# Tao ra 1 client moi
	app = Client(root, serverAddr, serverPort, rtpPort, fileName)
	app.master.title("RTPClient")	
	root.mainloop()
	