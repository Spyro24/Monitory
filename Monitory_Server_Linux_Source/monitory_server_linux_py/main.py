import traceback
import time
import socket
from socket import SHUT_RDWR
from threading import Thread
from enum import Enum
import os
from string import Template
from time import localtime, strftime
import json
import signal
import sys


CPU_NAME = "Compute Unit"
GPU_NAME = "Graphics"

GLOBAL_EXIT = False
WORKING_DIR = ""
RUN_FOREVER = False

bind_ip = "0.0.0.0"
bind_port = 54000

most_recent_pc_info_str = ""
most_recent_iostat_str = ""
most_recent_ifstat_str = ""

export_stats_json =	{"Time_Now": "",
			"Date_Now": "",
			"Cpu_Utility_Total": 0,
			"Cpu_Utility_Thread": [],
			"Cpu_Clock_Average": 0,
			"Cpu_Clock_Thread": [],
			"Cpu_Wattage": 0,
			"Cpu_Temperature": 0,
			"Cpu_Memory_Available": 0,
			"Cpu_Memory_Used": 0,
			"Storage_Load": {},
			"Net_Upload_Speed": 0,
			"Net_Download_Speed": 0,
			"Gpu_Utility": 0,
			"Gpu_Clock": 0,
			"Gpu_Memory_Available": 0,
			"Gpu_Memory_Used": 0,
			"Gpu_Wattage": 0,
			"Gpu_Temperature": 0}

class Commands(Enum):
	CPU_MHZ_STR = 1
	# Total \n Used
	RAM_STR = 2
	CPU_NAME = 3
	GPU_NAME = 4
	GPU_UTIL = 5
	GPU_CLOCK = 6
	GPU_FREE_MEM = 7
	GPU_USED_MEM = 8
	GPU_TEMP = 9
	GPU_WATT = 10
	WORKING_DIR = 11
	IO = 12
	NET = 13
	HAS_NGPU = 14
	TAIL = 15
	STATS_UTIL = 16
	SPLIT_STATS = 17
	STATS_UTIL_SUDO = 18

_commands = dict()
_commands[Commands.CPU_MHZ_STR] = "cat /proc/cpuinfo | grep 'MHz' | uniq | awk '{print $4}'"
_commands[Commands.RAM_STR] = 'free -m | grep Mem | awk \'{printf("%f\\n%f"), $2/1000, $3/1000}\''
_commands[Commands.HAS_NGPU] = 'which nvidia-smi'
_commands[Commands.GPU_UTIL] = 'nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits'
_commands[Commands.GPU_CLOCK] = 'nvidia-smi --query-gpu=clocks.gr --format=csv,noheader,nounits'
_commands[Commands.GPU_FREE_MEM] = 'nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits'
_commands[Commands.GPU_USED_MEM] = 'nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits'
_commands[Commands.GPU_TEMP] = 'nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader'
_commands[Commands.GPU_WATT] = 'nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits'
_commands[Commands.WORKING_DIR] = 'cd -- "$( dirname -- \'${BASH_SOURCE[0]}\' )" &> /dev/null && pwd'
_commands[Commands.IO] = "iostat -d -x 1 2"
_commands[Commands.NET] = 'ifstat -nt -T 1 1 | tail -n 1 | awk \'{printf("%f\\n%f", $(NF-1), $NF)}\''
_commands[Commands.TAIL] = Template('tail -n 200 "$file" > "$file1" && mv "$file1" "$file" --force')
# make sure the trace loop does allow to have a nice transition between the iteration ends
_commands[Commands.STATS_UTIL] = Template('turbostat --quiet --interval=$sec --num_iterations=$num_iter --show Busy%,PkgWatt,PkgTmp -out="$file"')
# on debian we need sudo
_commands[Commands.STATS_UTIL_SUDO] = Template('sudo turbostat --quiet --interval=$sec --num_iterations=$num_iter --show Busy%,PkgWatt,PkgTmp -out="$file"')
# c1 c2 c3 > Busy%,PkgWatt,PkgTmp
_commands[Commands.SPLIT_STATS] = Template('echo "$input" | while read c1 c2 c3; do echo $c_idx; done')

def signal_handler(signal, frame):
	exit(0)
	# Perform cleanup tasks here
	print("Ctrl+C pressed. Cleaning up and exiting/restarting...")
	
	dispose()
	
	if RUN_FOREVER:
		print("Restart server in 5 sec ...")
		time.sleep(5)
	
		global GLOBAL_EXIT
		GLOBAL_EXIT = False
		main()
	
	print("exiting... make sure to have set --run-forever if you wish to run it forever")
	sys.exit(0)

def run_command(cmd):
	process = os.popen(cmd)

	output = process.read()
	process.close()

	return output.strip()
	
def normalize_path(path_str):
	path_str = os.path.normpath(path_str)
	path_str = os.path.normcase(path_str)
	return path_str
	
def get_safe_number(number, should_output_float):
	if number is None:
		return 0
	try:
		val = number.replace(",", ".")
		if should_output_float:
			return (float)(val)
		else:
			return (int)(val)
	except ValueError:
		return 0

def run_turbostats():
	try: 
		file_location_util = normalize_path(os.path.join(WORKING_DIR, "turbostat_info_util.txt"))
		file1_location_util = normalize_path(os.path.join(WORKING_DIR, "turbostat_info1_util.txt"))
		run_command(f'touch "{file_location_util}"')
		
		write_every_sec = 0.2
		max_iter = 100
		needs_sudo = False
		expected_loop_seconds = write_every_sec * max_iter
		
		while not GLOBAL_EXIT:
			try:
				# start time for detecting turbostat is running
				start = time.time()
			
				# Trim
				run_command(_commands[Commands.TAIL].substitute(file=file_location_util, file1=file1_location_util))
				# Write
				# on debian we need sudo
				if needs_sudo:
					run_command(_commands[Commands.STATS_UTIL_SUDO].substitute(file=file_location_util, sec=write_every_sec, num_iter=max_iter))
				else:
					run_command(_commands[Commands.STATS_UTIL].substitute(file=file_location_util, sec=write_every_sec, num_iter=max_iter))
					
				end = time.time()
				# seems turbostat is not starting, we need sudo here
				if end - start < expected_loop_seconds * 0.7:
					print("Trying to run turbostat with sudo")
					needs_sudo = True
					continue
				
				# Sleep
				time.sleep(write_every_sec)
			except Exception:
				traceback.print_exc()
	except Exception:
		traceback.print_exc()

def run_iostat():
	try: 
		while not GLOBAL_EXIT:
			try:
				global most_recent_iostat_str
				most_recent_iostat_str = run_command(_commands[Commands.IO])
				# Sleep
				time.sleep(0.1)
			except Exception:
				traceback.print_exc()
	except Exception:
		traceback.print_exc()

def run_ifstat():
	try: 
		while not GLOBAL_EXIT:
			try:
				global most_recent_ifstat_str
				most_recent_ifstat_str = run_command(_commands[Commands.NET])
				# Sleep
				time.sleep(0.1)
			except Exception:
				traceback.print_exc()
	except Exception:
		traceback.print_exc()

def collect_cpu_info():
	file_location_util = normalize_path(os.path.join(WORKING_DIR, "turbostat_info_util.txt"))
	
	util_file_arr = []
	for line in reversed(list(open(file_location_util))):
		row = line.rstrip()
		util_file_arr.append(row)
		if "Busy%" in row or "PkgWatt" in row or "PkgTmp" in row:
			break
	
	util_file_arr.reverse()
	util_file_lean = ""
	for line in util_file_arr:
		util_file_lean += line + "\n"

	colums = []
	for i in range(3):
		idx = f"$c{i+1}"
		col = run_command(_commands[Commands.SPLIT_STATS].substitute(input=util_file_lean, c_idx=idx))
		col_arr = col.split("\n")
		if len(col_arr) > 0:
			colums.append(col_arr)
			
	
	# num threads
	num_processors = run_command("nproc --all")
	num_processors = get_safe_number(num_processors, False)
	
	utils = [None] * (num_processors + 1)
	utils_index = 0
	watt = 0
	tmp = 0
	for col in colums:
		if "Busy%" in col[0]:
			for line in col:
				try:
					# we have to trigger the exception here
					val = (float)(line)
					val = get_safe_number(line, True)
					utils[utils_index] = val
					utils_index += 1
					utils_index = utils_index % (num_processors + 1)
				except:
					continue
		if "PkgWatt" in col[0]:
			for line in col:
				try:
					# we have to trigger the exception here
					val = (float)(line)
					val = get_safe_number(line, True)
					watt = val
					break
				except:
					continue
		if "PkgTmp" in col[0]:
			for line in col:
				try:
					# we have to trigger the exception here
					val = (float)(line)
					val = get_safe_number(line, True)
					tmp = val
					break
				except:
					continue
	
	avg_util = 0
	if len(utils) > 0:
		avg_util = utils[0]
		utils.pop(0)

		
	# do this sensor thing for amd cpus
	if tmp == 0:
		sensor_trace = run_command("sensors")
		sensor_arr = sensor_trace.split("\n")
		found_tmp = False
		tmp_str = ""
		for s in sensor_arr:
			s_upper = s.upper()
			if found_tmp and ("TCTL" in s_upper or "TDIE" in s_upper):
				for x in s:
					if x in "0123456789,.+-":
						tmp_str += x
				try:
					val = get_safe_number(tmp_str, True)
					tmp = val
				except:
					break
				break
			if "K10TEMP" in s_upper:
				found_tmp = True
				continue
				
	
	# mhz
	mhz_str = run_command(_commands[Commands.CPU_MHZ_STR])
	mhz_str_arr = mhz_str.split("\n")
	mhz_arr = [None] * num_processors
	mhz_arr_index = 0
	avg_mhz = 0
	for mhz in mhz_str_arr:
		try:
			# we have to trigger the exception here
			val = (float)(mhz)
			val = get_safe_number(mhz, True)
			mhz_arr[mhz_arr_index] = val
			mhz_arr_index += 1
			mhz_arr_index = mhz_arr_index % num_processors
			
			if avg_mhz == 0:
				avg_mhz = val
			else:
				avg_mhz = (avg_mhz + val) * 0.5
		except:
			pass
	
	global export_stats_json
	export_stats_json["Cpu_Utility_Total"] = avg_util
	data = f"Cpu_Utility:Total:{avg_util}:0:100|"
	for i in range(num_processors):
		data += f"Cpu_Utility:{i}:{utils[i]}:0:100|"
		export_stats_json["Cpu_Utility_Thread"][i] = utils[i]
	
	export_stats_json["Cpu_Clock_Average"] = avg_mhz
	data += f"Cpu_Clock:Total:{avg_mhz}:0:100|"
	for i in range(num_processors):
		data += f"Cpu_Clock:{i}:{mhz_arr[i]}:0:100|"
		export_stats_json["Cpu_Clock_Thread"][i] = mhz_arr[i]
	
	export_stats_json["Cpu_Wattage"] = watt
	export_stats_json["Cpu_Temperature"] = tmp
	
	data += f"Wattage:{CPU_NAME}:{watt}:0:100|"
	data += f"Temperature:{CPU_NAME}:{tmp}:0:100|"
	
	return data


def collect_cpu_memory():
	memory_str = run_command(_commands[Commands.RAM_STR])
	memory_str_arr = memory_str.split("\n")
	
	data = ""
	global export_stats_json
	if len(memory_str) == 0:
		data += f"Cpu_Memory:Used:0:0:100|"
		data += f"Cpu_Memory:Available:0:0:100|"
		export_stats_json["Cpu_Memory_Available"] = 0
		export_stats_json["Cpu_Memory_Used"] = 0
		
		return data
	
	used_mem = get_safe_number(memory_str_arr[1], True)
	max_mem = get_safe_number(memory_str_arr[0], True)
	
	data += f"Cpu_Memory:Used:{used_mem}:0:100|"
	data += f"Cpu_Memory:Available:{max_mem - used_mem}:0:100|"
		
	export_stats_json["Cpu_Memory_Available"] = max_mem - used_mem
	export_stats_json["Cpu_Memory_Used"] = used_mem
		
	return data


def collect_disks():
	device_str_arr = most_recent_iostat_str.split("\n")
	
	global export_stats_json
	export_stats_json["Storage_Load"] = dict()
	data = ""
	device_index = -1
	util_index = -1
	for i in range(len(device_str_arr)):
		if i < 1:
			continue
		if "%util" in device_str_arr[i]:
			device_index = i
			row_arr = device_str_arr[i].split(" ")
			row_arr = [x for x in row_arr if x.strip()]
			for y in range(len(row_arr)):
				if "%util" in row_arr[y]:
					util_index = y
					break
			break
	if util_index == -1:
		return ""
	
	for row in reversed(device_str_arr):
		if "%util" in row:
			break
		row_arr = row.split(" ")
		row_arr = [x for x in row_arr if x.strip()]
		val = row_arr[util_index]
		load = get_safe_number(val, True)
		data += f"Storage_Load:{row_arr[0]}:{load}:0:100|"
		export_stats_json["Storage_Load"][f"{row_arr[0]}"] = load
	
	return data
		

def collect_net():
	net_str_arr = most_recent_ifstat_str.split("\n")
	
	data = ""
	global export_stats_json
	if len(net_str_arr) <= 1:
		data += f"Upload_Speed:Total:0:0:0|"
		export_stats_json["Net_Upload_Speed"] = 0
	
		data += f"Download_Speed:Total:0:0:0|"
		export_stats_json["Net_Download_Speed"] = 0
		
		return data
		
	up = get_safe_number(net_str_arr[1], True) * 1024
	down = get_safe_number(net_str_arr[0], True) * 1024
	
	data = f"Upload_Speed:Total:{up}:{up}:0|"
	export_stats_json["Net_Upload_Speed"] = up
	
	data += f"Download_Speed:Total:{down}:{down}:0|"
	export_stats_json["Net_Download_Speed"] = down
	
	return data
	
def collect_gpu():
	# check if nvidia gpu is available
	has_gpu = run_command(_commands[Commands.HAS_NGPU])
	data = ""
	global export_stats_json
	if not "/" in has_gpu:
		data += f"Gpu_Utility:Clock:0:0:100|"
		export_stats_json["Gpu_Utility"] = 0
	
		data += f"Gpu_Clock:Clock:0:0:100|"
		export_stats_json["Gpu_Clock"] = 0
	
		data += f"Gpu_Memory:Available:0:0:100|"
		export_stats_json["Gpu_Memory_Available"] = 0
	
		data += f"Gpu_Memory:Used:0:0:100|"
		export_stats_json["Gpu_Memory_Used"] = 0
	
		data += f"Wattage:{GPU_NAME}:0:0:100|"
		export_stats_json["Gpu_Wattage"] = 0
	
		data += f"Temperature:{GPU_NAME}:0:0:100|"
		export_stats_json["Gpu_Temperature"] = 0
		
		return data
	
	util = run_command(_commands[Commands.GPU_UTIL])
	util = get_safe_number(util, True)
	data += f"Gpu_Utility:Clock:{util}:0:100|"
	export_stats_json["Gpu_Utility"] = util
	
	clock = run_command(_commands[Commands.GPU_CLOCK])
	clock = get_safe_number(clock, True)
	data += f"Gpu_Clock:Clock:{clock}:0:100|"
	export_stats_json["Gpu_Clock"] = clock
	
	mem_available = run_command(_commands[Commands.GPU_FREE_MEM])
	mem_available = get_safe_number(mem_available, True) / 1000
	data += f"Gpu_Memory:Available:{mem_available}:0:100|"
	export_stats_json["Gpu_Memory_Available"] = mem_available
	
	mem_used = run_command(_commands[Commands.GPU_USED_MEM])
	mem_used = get_safe_number(mem_used, True) / 1000
	data += f"Gpu_Memory:Used:{mem_used}:0:100|"
	export_stats_json["Gpu_Memory_Used"] = mem_used
	
	wattage = run_command(_commands[Commands.GPU_WATT])
	wattage = get_safe_number(wattage, True)
	data += f"Wattage:{GPU_NAME}:{wattage}:0:100|"
	export_stats_json["Gpu_Wattage"] = wattage
	
	temp = run_command(_commands[Commands.GPU_TEMP])
	temp = get_safe_number(temp, True)
	data += f"Temperature:{GPU_NAME}:{temp}:0:100|"
	export_stats_json["Gpu_Temperature"] = temp
	
	return data
	

def collect_pc_info():
	data = ""	
	
	data += f"""Time_Now:{strftime("%H~%M", localtime())}:0:0:0|"""
	data += f"""Date_Now:{strftime("%d/%m/%Y", localtime())}:0:0:0|"""
	
	global export_stats_json
	export_stats_json["Time_Now"] = strftime("%H:%M", localtime())
	export_stats_json["Date_Now"] = strftime("%d/%m/%Y", localtime())
	
	data += collect_cpu_info()
	data += collect_cpu_memory()
	data += collect_disks()
	data += collect_net()
	data += collect_gpu()
	
	return data
	
def write_placeholder_data():
	num_processors = run_command("nproc --all")
	num_processors = get_safe_number(num_processors, False)
	
	data = ""
	data += f"""Time_Now:00~00:0:0:0|"""
	data += f"""Date_Now:01/01/2000:0:0:0|"""
	
	global export_stats_json
	export_stats_json["Cpu_Utility_Thread"] = [None] * num_processors
	export_stats_json["Cpu_Clock_Thread"] = [None] * num_processors
	export_stats_json["Storage_Load"] = dict()
	
	data = f"Cpu_Utility:Total:0:0:100|"
	export_stats_json["Cpu_Utility_Total"] = 0
	for i in range((int)(num_processors)):
		data += f"Cpu_Utility:{i}:0:0:100|"
	
	data += f"Cpu_Clock:Total:0:0:100|"
	for i in range((int)(num_processors)):
		data += f"Cpu_Clock:{i}:0:0:100|"
		
	export_stats_json["Cpu_Clock_Average"] = 0
	export_stats_json["Cpu_Wattage"] = 0
	export_stats_json["Cpu_Temperature"] = 0
	
	data += f"Wattage:{CPU_NAME}:0:0:100|"
	data += f"Temperature:{CPU_NAME}:0:0:100|"
	
	data += f"Cpu_Memory:Used:0:0:100|"
	data += f"Cpu_Memory:Available:0:0:100|"
	export_stats_json["Cpu_Memory_Available"] = 0
	export_stats_json["Cpu_Memory_Used"] = 0
	
	data += f"Upload_Speed:Total:0:0:0|"
	export_stats_json["Net_Upload_Speed"] = 0
	
	data += f"Download_Speed:Total:0:0:0|"
	export_stats_json["Net_Download_Speed"] = 0
	
	data += f"Gpu_Utility:Clock:0:0:100|"
	export_stats_json["Gpu_Utility"] = 0
	
	data += f"Gpu_Clock:Clock:0:0:100|"
	export_stats_json["Gpu_Clock"] = 0
	
	data += f"Gpu_Memory:Available:0:0:100|"
	export_stats_json["Gpu_Memory_Available"] = 0
	
	data += f"Gpu_Memory:Used:0:0:100|"
	export_stats_json["Gpu_Memory_Used"] = 0
	
	data += f"Wattage:{GPU_NAME}:0:0:100|"
	export_stats_json["Gpu_Wattage"] = 0
	
	data += f"Temperature:{GPU_NAME}:0:0:100|"
	export_stats_json["Gpu_Temperature"] = 0
	
	return data
	
	
#client handling thread
def handle_client(client_socket):
	is_first_send = True
	try: 
		while not GLOBAL_EXIT:
			#printing what the client sends 
			# request = client_socket.recv(1024) 
			# print(f"[+] Recieved: {request}")
			# print(most_recent_pc_info_str)
			#sending back the packet
			if CPU_NAME in most_recent_pc_info_str and GPU_NAME in most_recent_pc_info_str:
				client_socket.send(most_recent_pc_info_str.encode())
				if is_first_send:
					is_first_send = False
					time.sleep(2)
			time.sleep(0.2)
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
	

def dispose():
	print("stopping threads")
	collect_handler.join()
	turbostats_handler.join()
	iostat_handler.join()
	ifstat_handler.join()
	print(f"stopping {len(clients)} clients")
	for client in clients:
		client.join()
	print("stopping server")
	try:
		server.shutdown(SHUT_RDWR)
		server.close()
	except Exception:
		pass

def main():
	if len(sys.argv) > 1:
		for i in range(1, len(sys.argv)):
			msg = sys.argv[i].upper()
			if msg == "--RUN-FOREVER":
				global RUN_FOREVER
				RUN_FOREVER = True

	# Register the signal handler
	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGPIPE, signal_handler)

	# https://medium.com/@mando_elnino/python-tcp-server-b945c68a983c
	global server
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server.bind((bind_ip, bind_port))
	# we tell the server to start listening with 
	# a maximum backlog of connections set to 5
	server.listen(5)
	print(f"[+] Listening on port {bind_ip} : {bind_port}")
	
	# Defaulting values
	global clients
	clients = []
	global WORKING_DIR
	WORKING_DIR = normalize_path(run_command(_commands[Commands.WORKING_DIR]))
	
	# Write placeholder data for allowing the network adapt to the data
	global most_recent_pc_info_str
	most_recent_pc_info_str = write_placeholder_data()
	
	# Wait 2 sec to have all data already written
	time.sleep(2)
	
	# the hardware info collect loop
	def collect():
		#main.server_start(); //starting the server
		while not GLOBAL_EXIT:
			try:
				global most_recent_pc_info_str
				most_recent_pc_info_str = collect_pc_info()
				
				# Write the json
				with open(normalize_path(os.path.join(WORKING_DIR, "exported_data.json")), 'w') as f:
					json.dump(export_stats_json, f)
			except Exception:
				traceback.print_exc()
		
			time.sleep(0.05)
	
	global collect_handler
	collect_handler = Thread(target=collect, args=())
	collect_handler.start()
	
	# Background worker
	global turbostats_handler
	turbostats_handler = Thread(target=run_turbostats, args=())
	turbostats_handler.start()
	global iostat_handler
	iostat_handler = Thread(target=run_iostat, args=())
	iostat_handler.start()
	global ifstat_handler
	ifstat_handler = Thread(target=run_ifstat, args=())
	ifstat_handler.start()
	
	global client_ips
	client_ips = []
	
	# the tcp server loop running on the main thread
	while not GLOBAL_EXIT:
		try:
			clients = [x for x in clients if x.is_alive()]
			# When a client connects we receive the 
			# client socket into the client variable, and 
			# the remote connection details into the addr variable
			client, addr = server.accept()
			if addr[0] in client_ips:
				print("cancel connecting twice")
				continue
			print(f"[+] Accepted connection from: {addr[0]}:{addr[1]}")
			#spin up our client thread to handle the incoming data
			client_handler = Thread(target=handle_client, args=(client,))
			client_handler.start()
			clients.append(client_handler)
			def whitelist_client_ip(delay, ip):
				time.sleep(delay)
				global client_ips
				client_ips = [x for x in client_ips if x != ip]
			client_whitelist_handler = Thread(target=whitelist_client_ip, args=(5,addr[0]))
		except Exception:
			traceback.print_exc()
	
	dispose()
	sys.exit(0)

if __name__ == "__main__":
    main()                         


