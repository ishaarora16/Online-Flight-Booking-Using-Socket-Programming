import sys
import time
import socket
import json

import prettytable as pt
import ast

BUF_SIZE = 1024
MAX_SEATS = 20

# host to connect
host = ''
# port to connect
port = 12350
address = (host, port)

# create a TCP socket object
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(address) 

table = pt.PrettyTable()
table.field_names = ["FLIGHT PNR", "SOURCE", "DESTINATION", "DEPARTURE TIME", "ARRIVAL TIME", "SEATS"]

try:
	assigned_id = 'Unknown'
	email = raw_input(sock.recv(BUF_SIZE))
	sock.send(email)
	assigned_id = sock.recv(BUF_SIZE) # receive data from the server
	sock.send("User " + assigned_id + " online.")
	option = None

	# while(option is not):
	option = raw_input(sock.recv(BUF_SIZE).replace("<user_id>",email))
	sock.send(option)
	
	if(int(option) == 1):
		book_details = dict()
		book_details["user"] = assigned_id 
		book_details["place"] = dict()
		book_details["place"]["source"] = raw_input("Place of Departure: ")
		book_details["place"]["dest"] = raw_input("Place of Arrival: ")
		book_details["date"] = raw_input("Departure Date: ")
		book_details["seats"] = raw_input("Number of Seats: ")
		sock.send(json.dumps(book_details).encode())

		available_flights = json.loads(sock.recv(BUF_SIZE).decode())
		for PNR in available_flights["flights"]:
			table.add_row([PNR, available_flights["flights"][PNR]["place"]["source"], available_flights["flights"][PNR]["place"]["dest"], available_flights["flights"][PNR]["time"]["departure"], available_flights["flights"][PNR]["time"]["arrival"], available_flights["flights"][PNR]["seats"]])
		# print pd.DataFrame(json.loads(json.dumps(available_flights["flights"])))
		print table
		table.clear_rows()

		while True:
			flight_selected = raw_input("\nSelect Flight PNR Number you want to Book / 'N' to stop booking: ")
			if(flight_selected != 'N'):
				try:
					sock.send(json.dumps({"user":assigned_id, "PNR":flight_selected, "seats":book_details["seats"]}).encode())
				except KeyError:
					print "Invalid PNR entered. Enter a correct PNR for booking or sending socket failed"
				else:
					print "You Selected Flight " + flight_selected + " :"
					table.add_row([flight_selected, available_flights["flights"][flight_selected]["place"]["source"], available_flights["flights"][flight_selected]["place"]["dest"], available_flights["flights"][flight_selected]["time"]["departure"], available_flights["flights"][flight_selected]["time"]["arrival"], available_flights["flights"][flight_selected]["seats"]])
					print table
					table.clear_rows()

					response = sock.recv(21).decode()
					response = ast.literal_eval(response)
					if response['status'] == 'success':
						print "Your flight {0} for {1} seat(s) has been booked!".format(flight_selected, book_details["seats"])
					else:
						print "Booking failed!"					
					break
			else:
				break

	elif(int(option) == 2):
		sock.send(assigned_id)
		bookings_found = json.loads(sock.recv(BUF_SIZE).decode())
		if(bookings_found["user"] == assigned_id):
			if(len(bookings_found["flights"]) <= 0):
				print "No Bookings found for " + email + "."
			else:
				# print pd.DataFrame(json.loads(json.dumps(bookings_found["flights"])))
				for PNR in bookings_found["flights"]:
					table.add_row([PNR, bookings_found["flights"][PNR]["place"]["source"], bookings_found["flights"][PNR]["place"]["dest"], bookings_found["flights"][PNR]["time"]["departure"], bookings_found["flights"][PNR]["time"]["arrival"], bookings_found["flights"][PNR]["seats"]])
				print table
				table.clear_rows()

				# print json.dumps(bookings_found["flights"], indent=4)

		if(len(bookings_found["flights"]) > 0):
			while True:
				flight_selected = raw_input("\nSelect Flight PNR Number you want to Cancel / 'N' to stop cancellation: ")
				if(flight_selected != "N"):
					try:
						json.dumps(bookings_found["flights"][flight_selected], indent=4)
					except KeyError:
						print "Invalid PNR entered. Enter a correct PNR for cancellation"
					else:
						print "You Requested Cancellation for Flight " + flight_selected + " :"
						table.add_row([flight_selected, bookings_found["flights"][flight_selected]["place"]["source"], bookings_found["flights"][flight_selected]["place"]["dest"], bookings_found["flights"][flight_selected]["time"]["departure"], bookings_found["flights"][flight_selected]["time"]["arrival"], bookings_found["flights"][flight_selected]["seats"]])
						print table
						table.clear_rows()
						# print pd.DataFrame(json.loads(json.dumps(bookings_found["flights"][flight_selected])))
						# print json.dumps(bookings_found["flights"][flight_selected], indent=4)
						sock.send(json.dumps({"PNR":flight_selected	,"user":assigned_id}).encode())
						response =  sock.recv(21).decode()
						response = ast.literal_eval(response)
						if response['status'] == 'success':
							print "Your booking in flight {0} for {1} seat(s) has been cancelled!".format(flight_selected, bookings_found["flights"][flight_selected]["seats"])
						else:
							print "Cancellation failed!"					
						break
				else:
					break

except KeyboardInterrupt:
	sock.send("User " + assigned_id + ' logged out.')
	sock.send("User " + assigned_id + ' logged out.')
	sys.exit(1)
