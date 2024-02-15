"""
Author: Joe Ingham
Date Created: 12/02/2024
Date Last Updated: 15/02/2024
Description: Burnin Jig Tempsense - Connects to an arduino nano (via serial) and reads the temperatures recorded on the Qest Ku Burn-in Jig
"""





from PyQt6 import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer
import sys
import serial
import serial.tools.list_ports
import os




#Global serial read/write timeout limit - currently 5 seconds
TIMEOUT_LIM = 5


#Application Controller
class app(QApplication):

    #Initialiser
    def __init__(self, args):       
        global stopFlag
        super(app, self).__init__(args)
        
        

        #Open the first window
        mw = main_window(self)
        mw.show()
        sys.exit(self.exec())


#Main window the USB Power Meter 
class main_window(QWidget):

    def __init__(self, master):      

        super(main_window, self).__init__()
        
        #Set the window title
        self.setWindowTitle("Burn-in Jig Temp Reader - V1")

        #Determine the layout (i.e. grid style)
        layout = QGridLayout()
        

        #Place the widgets in the layout (i.e. buttons/textboxes etc)
        #PA A Label
        ALabel = QLabel("PA A")
        ALabel.setFont(QFont("Arial", 23))
        ALabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ALabel, 0, 0)

        #PA B Label
        BLabel = QLabel("PA B")
        BLabel.setFont(QFont("Arial", 23))
        BLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(BLabel, 0, 3)



        #PA A Temp Label
        ATempLabel = QLabel("24<sup>o</sup>C")
        ATempLabel.setFont(QFont("Arial", 36))
        ATempLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ATempLabel, 1, 0)


        #PA B Temp Label
        BTempLabel = QLabel("25<sup>o</sup>C")
        BTempLabel.setFont(QFont("Arial", 36))
        BTempLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(BTempLabel, 1, 3)

        #Store labels for later modification
        self.tempLabels = [ATempLabel, BTempLabel]

        #Connect Button
        connectButton = QPushButton(self)
        connectButton.setText("Connect")
        connectButton.clicked.connect(self.arduinoConnect)
        layout.addWidget(connectButton, 0, 2)

        #Create timer for temp reading
        self.tempTimer = QTimer()
        self.tempTimer.timeout.connect(self.readTemp)
        #self.tempTimer.setInterval(500)
        self.updateTempTimer = QTimer()
        self.updateTempTimer.timeout.connect(self.updateTemp)
        self.updateTempTimer.setInterval(500)


        #Placeholder Label (spreads out the page)
        self.errorLabel = QLabel("                                           ")
        layout.addWidget(self.errorLabel, 1, 2)




        #PFFSETS START PRECALIBRATED

        #PA A offset box
        self.AOffset = -3.0
        self.AOffsetLabel = QLabel(f"Offset: {self.AOffset} <sup>o</sup>C")
        self.AOffsetLabel.setFont(QFont("Arial", 24))
        layout.addWidget(self.AOffsetLabel, 2, 0)

        #PA B offset box
        self.BOffset = -1.0
        self.BOffsetLabel = QLabel(f"Offset: {self.BOffset} <sup>o</sup>C")
        self.BOffsetLabel.setFont(QFont("Arial", 24))
        layout.addWidget(self.BOffsetLabel, 2, 3)

        self.offsets = [self.AOffset, self.BOffset]


  

        #PA A Offset Up Button
        AOffUpButton = QPushButton(self)
        AOffUpButton.setText("^")
        AOffUpButton.clicked.connect(lambda: self.offsetUp("A"))
        layout.addWidget(AOffUpButton, 3, 0)
        

        #PA A Offset Down Button
        AOffDownButton = QPushButton(self)
        AOffDownButton.setText("⌄")
        AOffDownButton.clicked.connect(lambda: self.offsetDown("A"))
        layout.addWidget(AOffDownButton, 4, 0)


        #PA B Offset Up Button
        BOffUpButton = QPushButton(self)
        BOffUpButton.setText("^")
        BOffUpButton.clicked.connect(lambda: self.offsetUp("B"))
        layout.addWidget(BOffUpButton, 3, 3)

        #PA B Offset Down Button
        BOffDownButton = QPushButton(self)
        BOffDownButton.setText("⌄")
        BOffDownButton.clicked.connect(lambda: self.offsetDown("B"))
        layout.addWidget(BOffDownButton, 4, 3)


        #Set appropriate flags
        self.connected = 0

        #Place the widgets into the layout
        self.master = master        
        self.setLayout(layout)
        
    #On close of the GUI ensure every task stops
    def closeEvent(self, event):
        global exitFlag

        exitFlag = 1

        event.accept() 

        os._exit(0)



    #figures out which port is the com port
    def arduinoCOMDetect(self):

        ports = list(serial.tools.list_ports.comports())

        for p in ports:
            print(p)

            if "Arduino" in p[1]:
                print(f"Arduino on port {p[0]}")

                return p[0]
            
        #Return error
        return -1





    #Raises the offset of the side clicked
    def offsetUp(self, id):

        match id:
            case "A":
                self.AOffset = self.AOffset + 0.5
                
                self.AOffsetLabel.setText(f"Offset: {self.AOffset} <sup>o</sup>C")  

                self.offsets[0] = self.AOffset


            case "B":
                self.BOffset = self.BOffset + 0.5
                
                self.BOffsetLabel.setText(f"Offset: {self.BOffset} <sup>o</sup>C")  
                
                self.offsets[1] = self.BOffset

            case _:
                print("INVALID PA ID")


    #Lowers the offset of the side clicked
    def offsetDown(self, id):

        match id:
            case "A":
                self.AOffset = self.AOffset - 0.5
                
                self.AOffsetLabel.setText(f"Offset: {self.AOffset} <sup>o</sup>C")  
                self.offsets[0] = self.AOffset


            case "B":
                self.BOffset = self.BOffset - 0.5
                
                self.BOffsetLabel.setText(f"Offset: {self.BOffset} <sup>o</sup>C")  
                self.offsets[1] = self.BOffset
                

            case _:
                print("INVALID PA ID")



    #Connects to an arduino and begins the temperature reading process
    def arduinoConnect(self):
        
        if not self.connected:
            try:
                #Open USB serial port - autodetect only works when you have the drivers
                #REMEMBER TO CHANGE IF THINGS CANT CONNECT  CHANGE AT END
                self.arduino = serial.Serial(self.arduinoCOMDetect())
                #self.arduino = serial.Serial("COM26")
                self.connected = 1 
            #If the device is already connected
            except PermissionError:        
                print("DEVICE ALREADY CONNECTED")
                self.errorLabel.setText("DEVICE ALREADY CONNECTED")
                #return
            except Exception as e:  
                print(e)      
                print("DEVICE CONNECTION FAILURE")
                self.errorLabel.setText("UNABLE TO CONNECT TO DEVICE")
                return

            #Setup the device
            self.arduino.baudrate = 9600
            self.arduino.bytesize = 8
            self.arduino.parity = serial.PARITY_NONE
            self.arduino.stopbits = 1


        print(self.arduino.readline())

        #Initiate the handshake procedure
        #dself.readMsg()

        #Only activate the timer if it isn't running
        if not self.tempTimer.isActive():
            #Start the Qtimer that reads the buffer every 0.5 seconds
            self.tempTimer.start()
            
    


    """   
        self.arduino.write("<MSG:CONNECT>".encode("utf-8"))

        #Start timer for timeout watchdog
        start_time = time.time()        
 
        while self.arduino.in_waiting > 5:
            #print(self.arduino.in_waiting)
            if (time.time() - start_time) > TIMEOUT_LIM:
                print("SERIAL TIMEOUT")
                self.errorLabel.setText("SERIAL TIMEOUT - DISCONNECTED")
                self.arduino.close()
                return
        

        #Read the response
        if (handshake_resp := self.readMsg()) != "RESP:CONNECT":
            print(f"HANDSHAKE ERROR: {handshake_resp}")
            self.errorLabel.setText("HANDSHAKE ERROR - DISCONNECTED")
            self.arduino.close()
            return
        
        
        #Send command to arduino to start temp sensing
        self.arduino.write("<MSG:STARTTEMP>".encode("utf-8"))


        
        """ 
    #Reads the temperature date from the arduino
    def readTemp(self):

        #Very simplified version - just read a line each time 
        self.tempInfo = self.arduino.readline()

        print(self.tempInfo)

        #Extract the data from the tempinfo (remove wrapper info and seperate info)
        self.tempInfo = self.tempInfo.decode().replace("<", "").replace(">", "").strip().split(" ")

        #Only start the label update timer after tempinfo has been updated the first time
        if not self.updateTempTimer.isActive():
            self.updateTempTimer.start()



    #Updates the temp labels - bit slower 
    def updateTemp(self):
         #Update the labels
        for counter, temp in enumerate(self.tempInfo):
            self.tempLabels[counter].setText(f"{round(float(temp[3:]) + self.offsets[counter], 2)}<sup>o</sup>C")



        
        
    #Reads a message
    def readMsg(self):
        startMarker = "<"
        endMarker = ">"

        msgStarted = False

        buff = []

        print(self.arduino.in_waiting)
        
    

        #While theres bytes in the serial bus
        while self.arduino.in_waiting:
            print(f"Bytes left: {self.arduino.in_waiting}")

            #Read the byte
            rxedByte = self.arduino.read()
            print(f"Byte: {rxedByte}")

            if msgStarted:                
                #If the byte isn't the end marker
                if rxedByte != endMarker:
                    buff.append(rxedByte)

                else:
                    #Finish the string
                    buff.append("\0")
                    break

            #Check to see where the message starts (ensure a message is recieved not garbage)
            if rxedByte == startMarker:
                print("Message starting")
                msgStarted = True


        joined_string = " ".join(buff)

        print(f"RESPONSE: {joined_string}")

        #Turn the recieved message into a string
        return joined_string






            


                
    




if __name__ == "__main__":
    app = app(sys.argv)