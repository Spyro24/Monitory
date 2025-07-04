import traceback
import time
import socket
from socket import SHUT_RDWR
from threading import Thread

GLOBAL_EXIT = False

most_recent_pc_info_str = ""
clients = []

bind_ip = "0.0.0.0"
bind_port = 54000

def collect_pc_info():
	#print("Collect")
	test = "a"
	# err = (float)(test)
	return ""
	
#client handling thread
def handle_client(client_socket): 
	while not GLOBAL_EXIT:
		try:
			#printing what the client sends 
			# request = client_socket.recv(1024) 
			# print(f"[+] Recieved: {request}") 
			#sending back the packet 
			client_socket.send("Ping recevied".encode())
			time.sleep(0.1)
		except Exception:
			traceback.print_exc()
	
	try:
		client_socket.shutdown(SHUT_RDWR)
		client_socket.close()
	except Exception:
		pass
	
def exit(delay_sec):
	time.sleep(delay_sec)
	global GLOBAL_EXIT
	GLOBAL_EXIT = True

def main():
	# https://medium.com/@mando_elnino/python-tcp-server-b945c68a983c
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
	server.bind((bind_ip, bind_port))
	# we tell the server to start listening with 
	# a maximum backlog of connections set to 5
	server.listen(5)
	print(f"[+] Listening on port {bind_ip} : {bind_port}")
	
	# the hardware info collect loop
	def collect():
		#main.server_start(); //starting the server
		while not GLOBAL_EXIT:
			try:
				most_recent_pc_info_str = collect_pc_info()
			except Exception:
				traceback.print_exc()
		
			time.sleep(0.05)
	
	collect_handler = Thread(target=collect, args=())
	collect_handler.start()
	
	# Exit Test
	collect_handler1 = Thread(target=exit, args=(5,))
	collect_handler1.start()
	
	# the tcp server loop running on the main thread
	while not GLOBAL_EXIT:
		try:
			# When a client connects we receive the 
			# client socket into the client variable, and 
			# the remote connection details into the addr variable
			client, addr = server.accept() 
			print(f"[+] Accepted connection from: {addr[0]}:{addr[1]}")
			#spin up our client thread to handle the incoming data 
			client_handler = Thread(target=handle_client, args=(client,))
			client_handler.start()
			clients.append(client_handler)
		except Exception:
			traceback.print_exc()
	
	print("stopping threads")
	collect_handler.join()
	collect_handler1.join()
	print(f"stopping {len(clients)} clients")
	for client in clients:
		client.join()
	print("stopping server")
	try:
		server.shutdown(SHUT_RDWR)
		server.close()
	except Exception:
		pass
	print("exit code: 0")
	return 0

if __name__ == "__main__":
    main()                         


