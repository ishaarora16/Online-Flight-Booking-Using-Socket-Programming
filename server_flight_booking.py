import socket
from threading import Thread, Lock
import csv, json, copy
import uuid
from datetime import datetime
from time import sleep
import sys

BUF_SIZE = 1024
MAX_SEATS = 20
FLIGHT_DATA = "flight_data_2.json"
USER_DATA = "user_id_data.csv"
LIVE_CONN_COUNT = 0

host = "localhost"
port = 12350
address = (host, port)

# create a socket object
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Next bind to the port
sock.bind(address)
print "Socket Binded to " + str(port)

# socket into listening mode - 5 clients can queue up
sock.listen(5)
print "Socket is Listening"

def generate_client_id(email):
    user_id_data = open("user_id_data.csv","a+")
    unique_user_id = None
    
    for line in user_id_data:
        line = line.strip().split(',')
        if email == line[1]:
            unique_user_id = line[2]
    
    if not unique_user_id:
        unique_user_id = (uuid.uuid4().hex)[:5]
        user_id_data.write("\n" + str(datetime.now()) + "," + email + "," + unique_user_id)
    
    user_id_data.close()

    return unique_user_id

def search_flights(flights_data, search_details):
    available_flights = dict()
    available_flights["flights"] = {k: v for k, v in flights_data["flights"].items() if(len(v["seats_array"]) <= (MAX_SEATS - int(search_details["seats"])) and v["date"] == search_details["date"] and v["place"]["source"] == v["place"]["source"] and v["place"]["dest"] == search_details["place"]["dest"])}
    for flight in available_flights["flights"]:
        available_flights["flights"][flight]["seats"] = MAX_SEATS - len(available_flights["flights"][flight]["seats_array"])
        available_flights["flights"][flight].pop("seats_array", None)
    available_flights["user"] = search_details["user"]
    return available_flights

def book_flight(booking_details):
    write_lock = Lock()
    write_lock.acquire()
    
    with open(FLIGHT_DATA, "r") as json_data:
        check_flight = json.load(json_data)

    if(booking_details["PNR"] in check_flight["flights"] and int(booking_details["seats"]) <= MAX_SEATS - len(check_flight["flights"][booking_details["PNR"]]["seats_array"])):
        for add_person in range(int(booking_details["seats"])):
            check_flight["flights"][booking_details["PNR"]]["seats_array"].append(booking_details["user"])

        with open(FLIGHT_DATA, "w") as json_data:
            json.dump(check_flight, json_data, indent=4)
        print "Booked " + str(booking_details["seats"]) + " tickets for " + booking_details["user"] + "." 
        book_status = {"status":"success"}    

    else:
        book_status = {"status":"failed"}
    
    write_lock.release()
    return book_status

def view_bookings(unique_user_id):
    with open(FLIGHT_DATA, "r") as json_data:
        check_flight = json.load(json_data)

    bookings_found = dict()
    bookings_found["flights"] = dict()

    for flight in check_flight["flights"]:
        if(unique_user_id in check_flight["flights"][flight]["seats_array"]):
            bookings_found["flights"][flight] = check_flight["flights"][flight].copy()
            bookings_found["flights"][flight]["seats"] = bookings_found["flights"][flight]["seats_array"].count(unique_user_id)
            bookings_found["flights"][flight].pop("seats_array", None)
    bookings_found["user"] = unique_user_id
    
    return bookings_found

def cancel_booking(cancellation_details):
    write_lock = Lock()
    write_lock.acquire()
    
    with open(FLIGHT_DATA, "r") as json_data:
        validate_flight = json.load(json_data)

    if(cancellation_details["PNR"] in validate_flight["flights"] and cancellation_details["user"] in validate_flight["flights"][cancellation_details["PNR"]]["seats_array"]):
        num_seats =  validate_flight["flights"][cancellation_details["PNR"]]["seats_array"].count(cancellation_details["user"])
        validate_flight["flights"][cancellation_details["PNR"]]["seats_array"] = copy.deepcopy([user for user in validate_flight["flights"][cancellation_details["PNR"]]["seats_array"] if user != cancellation_details["user"]])
    
        with open(FLIGHT_DATA, "w") as json_data:
            json.dump(validate_flight, json_data, indent=4)
        print "Cancelled " + str(num_seats) + " seats from flight " + cancellation_details["PNR"] + " under " + cancellation_details["user"]  + "."
        cancel_status = {"status":"success"}    

    else:
        cancel_status = {"status":"failed"}
    
    write_lock.release()
    return cancel_status

def client_thread(conn, addr):
    # infinite loop so that function do not terminate and thread do not end.
    while True:
        # try:
        conn.send("Enter Your Email: ")         
        conn.send(generate_client_id(conn.recv(BUF_SIZE)))
        print conn.recv(BUF_SIZE)
        
        # Enter Details for Flight Booking.") #Sending message to connected client
        conn.send("\nWelcome <user_id>.\n\n1. Book Flight\n2. Cancel Flight\n3. Log Out\nEnter Your Choice: ")
        option = conn.recv(BUF_SIZE)

        if(int(option) == 1):
            with open(FLIGHT_DATA,"r") as json_data:
                # send all flight data based on criteria the client sends
                conn.send(json.dumps(search_flights(json.load(json_data), json.loads(conn.recv(BUF_SIZE).decode()))).encode())
            
            # send success/failure status message after booking is done
            conn.send(json.dumps(book_flight(json.loads(conn.recv(BUF_SIZE).decode()))).encode())

        elif(int(option) == 2):
            conn.send(json.dumps(view_bookings(conn.recv(BUF_SIZE))).encode())
            conn.send(json.dumps(cancel_booking(json.loads(conn.recv(BUF_SIZE).decode()))).encode())
        
        # except Exception:
        #     global LIVE_CONN_COUNT
        #     LIVE_CONN_COUNT -= 1
        #     print "A Client Logged Out."
        #     print 'Client Response: ' + conn.recv(BUF_SIZE)
        #     print "Connections Online: " + str(LIVE_CONN_COUNT)
        return

while True:
    # Establish connection with client.
    conn, addr = sock.accept()
    print "Got Connection from", addr
    LIVE_CONN_COUNT += 1
    print "Connections Online: " + str(LIVE_CONN_COUNT)
    thread = Thread(target=client_thread, args=(conn,addr))
    thread.start()
