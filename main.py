import network
import socket
import time
from interstate75 import Interstate75


ssid = 'espWifi'
password = 'ljmu1111'

server_ip = '192.168.237.74'  
server_port = 9876

i75 = Interstate75(display=Interstate75.DISPLAY_INTERSTATE75_256X64)
graphics = i75.display

HEIGHT = 64
WIDTH = 256
BIT_COUNT = 24

# Calculate row size (number of bytes in a row)
row_size = (BIT_COUNT * WIDTH + 31) // 32 * 4

y_coord = 0

wlan = network.WLAN(network.STA_IF)
wlan.active(True)


def main():
    
    connectWifi(ssid, password)  
    
    # Main Loop
    while True:

        monitorWifiConnection()
        client_socket = initSocket()
        
        # Listens for incoming bmp data , b'DEADBEEF' signals EOF
        while socketConnected(client_socket):

            eof = False
            firstChunk = True
    
            is_leftover_chunk_data = False
            leftover_chunk_data = bytearray()

            print("Listening....")
            while not eof:

                chunk = client_socket.recv(4096)
                
                # Remove BMP header from first chunk
                if firstChunk:  
                    header_offset = chunk[10] | (chunk[11] << 8) | (chunk[12] << 16) | (chunk[13] << 24)
                    chunk = chunk[header_offset:]
                    firstChunk = False
        
                if b'DEADBEEF' in chunk:
                    print("End of image detected")
                    eof = True
                    chunk = chunk[0:-8]
                
                
                chunkSize = len(chunk)
                currentIndex = 0
                
                while currentIndex < chunkSize:

                    if is_leftover_chunk_data:
                        # Add the leftover data to new chunk and clear leftover bytearray
                        leftover_chunk_data.extend(chunk)
                        chunk = leftover_chunk_data
                        is_leftover_chunk_data = False
                        leftover_chunk_data = bytearray()

                        # Re-assign chunk size
                        chunkSize = len(chunk)
                    
                    # If not enough data left in chunk for full row, store for display on the next chunk
                    if (chunkSize - currentIndex) < row_size:
                        is_leftover_chunk_data = True                
                        leftover_chunk_data.extend(chunk[currentIndex:])
                        break
                    
                    
                    displayRow(chunk[currentIndex: currentIndex + row_size])
                    currentIndex += row_size   
                
                               
            print(f"Image Received")
            global y_coord
            y_coord = 0
            
                  
        client_socket.close()




def connectWifi(ssid, password):

    wlan.connect(ssid, password)

    while not wlan.isconnected():
        print('Connecting to network...')
        time.sleep(1)

    print('Network connected:', wlan.ifconfig())

def monitorWifiConnection():

    if wlan.status() < 0 or wlan.status() >= 3:
        print("Trying to reconnect...")
        connectWifi(ssid, password)


def displayRow(row):

    global y_coord

    for x in range(WIDTH):
        
       # pixel_index = y_coord * row_size + x * (BIT_COUNT // 8)
        pixel_index = x * (BIT_COUNT // 8)

        blue = int(row[pixel_index])
        green = int(row[pixel_index + 1])
        red = int(row[pixel_index + 2])

        colour = graphics.create_pen(red, green, blue)
        graphics.set_pen(colour)
        graphics.pixel((WIDTH - 1) - x,y_coord)
        
        
    y_coord += 1
    i75.update(graphics)



def initSocket():

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))

    print('Connected to server at', server_ip, ':', server_port)
    return client_socket


def socketConnected(sock):

    try:
        sock.send(b'Heartbeat')
        return True
    except OSError as e:
        return False
    


if __name__ == '__main__':
    main()    