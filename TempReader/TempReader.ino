
#include <Arduino.h>

int connected = 0;
int connect_time;



float temp1;
float temp2;

//Msg recieve buffer
const byte numChars = 32;
char receivedChars[numChars];
boolean newData = false;



void setup() {

  //Set pins
  pinMode(A1, INPUT);
  pinMode(A4, INPUT);


  //Begin serial connection
  Serial.begin(9600);



}

void loop() {

  //For now dont bother with the handshaking stuff - just send the temperatures forever
  tempRead();


/*
  //See if PC is trying to connect.
  if (connected == 0) {

    connected = checkForHandshake();
  }



  //Once connected - Read temp data and serial write it
  connected = tempRead();

*/
}



void recvWithStartEndMarkers() {
    static boolean recvInProgress = false;
    static byte ndx = 0;
    char startMarker = '<';
    char endMarker = '>';
    char rc;

    
    while (Serial.available() > 0 && newData == false) {
        rc = Serial.read();

        if (recvInProgress == true) {
            if (rc != endMarker) {
                receivedChars[ndx] = rc;
                ndx++;
                if (ndx >= numChars) {
                    ndx = numChars - 1;
                }
            }
            else {
                receivedChars[ndx] = '\0'; // terminate the string
                recvInProgress = false;
                ndx = 0;
                newData = true;
            }
        }

        else if (rc == startMarker) {
            recvInProgress = true;
        }
    }
}


//Checks to see if the serial is asking for a handshake
int checkForHandshake() {

  connected = 0;
  newData = false;

  recvWithStartEndMarkers();
  

  //Check if its the handshake message
  if (receivedChars == "<MSG:CONNECT>") {
    //if not the correct message - leave the function
    return;
  }

  //Respond
  Serial.print("<RESP:CONNECT>");
  

  newData = false;

  recvWithStartEndMarkers();

  //Check if its the handshake message
  if (receivedChars == "<MSG:STARTTEMP>") {
    //Confirm connection
    connected = 1;
    connect_time = millis();
  }
  
  return connected;
}





//Read the voltage of the temp pins, convert it to a temperature and format it
void pinRead() {

  //Read the analogue signals
  int T1 = analogRead(A1);
  int T2 = analogRead(A4);

  //Convert the digital representation to the analogue voltage
  float T1_f = T1 * 0.0049;
  float T2_f = T2 * 0.0049;

  //Convert the voltages to temperatures
  temp1 = (T1_f - 0.5) / 0.01;
  temp2 = (T2_f - 0.5) / 0.01;

}

//Read the values of the temp sensors and send the formatted version to the PC
int tempRead() {


  //newData = false;
  //recvWithStartEndMarkers();


  //if (receivedChars== "T?") {

    //Read the pin values
    pinRead();


    //Convert them to strings
    char temp1_str[5];
    char temp2_str[5];

    dtostrf(temp1, 3, 1, temp1_str);
    dtostrf(temp2, 3, 1, temp2_str);

    //Write the string
    Serial.print("<T1:");
    Serial.print(temp1);
    Serial.print(" T2:");
    Serial.print(temp2);
    Serial.print(">\n");

    //Update the connection time
    //connect_time = millis();

    //Confirm still connected
    return 1;
    //}
  

  //Check to see if still connected (i.e. message recieved)
  if ((millis() - connect_time) > 5000) {
    //Return 0 to show the main loop that connection is lost (or slow)
    return 0;
  }
}

