import time
import cv2         
import threading   
import playsound   
import datetime
from flask import Flask, Response
import requests
import pyrebase

# Shared variable to track the last access time
last_access_time = time.time()
# Timeout duration in seconds
TIMEOUT = 60  # 60 seconds

firebaseConfig = {
    "apiKey": "AIzaSyDHKv2E3egxrZ9C7YSA3D6CcqcCJynXV6w",
    "authDomain": "send-host-recive-token.firebaseapp.com",
    "projectId": "send-host-recive-token",
    "databaseURL": "https://send-host-recive-token-default-rtdb.firebaseio.com/",
    "storageBucket": "send-host-recive-token.appspot.com",
    "messagingSenderId": "837895804304",
    "appId": "1:837895804304:web:e993e2038b8779ed364f15",
    "measurementId": "G-P483XHD14Q"
}
firebase = pyrebase.initialize_app(firebaseConfig)
database = firebase.database()

Localip = "192.168.169.179"

data = {"localhost": Localip} #Change IP Address
database.child("Host").set (data)


data2 = {"TK":"-"}
database.child("token").set (data2)
data3 = {"UI": 0}
database.child("user_id").set (data3)


token = database.child("token").get().val()
user_id = database.child("user_id").get().val()

while list(user_id.values())[0] == 0 and list(token.values())[0] == "-" :
    token = database.child("token").get().val()
    user_id = database.child("user_id").get().val()
    print("Dosent Login")
    print (list(token.values())[0])
    print (list(user_id.values())[0])
    
time.sleep(2)
# ///////////////////////////////////////////////////////////////////////////////////////
token = database.child("token").get().val()
user_id = database.child("user_id").get().val()
print (list(token.values())[0])
print (list(user_id.values())[0])
token = list(token.values())[0]  
user_id = list(user_id.values())[0] 
# ///////////////////////////////////////////////////////////////////////////////////////

def send_image_to_route(image_file_path, user_id, token):
    try:
        url = 'http://' + Localip + ':8000/api/receive_image' #Change IP Address
        headers = {'Authorization': f'Bearer {token}'}
        
        with open(image_file_path, 'rb') as file:
            files = {'filename': (image_file_path, file, 'multipart/form-data')}
            data = {'user_id': str(user_id)}  
        
            with requests.Session() as session:
                response = session.post(url, headers=headers, files=files, data=data, stream=True)
        
        if response.status_code == 200:
            print("Image sent and stored successfully.")
            print(response.json())
        else:
            print("Error:", response.text)
    except Exception as e:
        print("An error occurred:", str(e))

fire_cascade = cv2.CascadeClassifier('fire_detection_cascade_model.xml') 

vid = cv2.VideoCapture(1) 

def play_alarm_sound_function(): 
    playsound.playsound('Alarm Sound.mp3',True) 
    print("Fire alarm end") 

app = Flask(__name__)

@app.route('/')
def index():
    return "LocalHostIp:5000/video_feed"

def gen_frames():
    global last_access_time
    while(True):
        ret, frame = vid.read()
        if not ret:
            break 
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 
            fire = fire_cascade.detectMultiScale(frame, 1.2, 3) 

            for (x,y,w,h) in fire:
                cv2.rectangle(frame,(x-20,y-20),(x+w+20,y+h+20),(255,0,0),2)
                roi_gray = gray[y:y+h, x:x+w]
                roi_color = frame[y:y+h, x:x+w]
                
                threading.Thread(target=play_alarm_sound_function).start() 

                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                img_name = "openCV_frame_{}.jpg".format(timestamp)
                cv2.imwrite(img_name,frame)
                send_image_to_route(img_name, user_id, token)
                
            
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            last_access_time = time.time()
            
@app.route('/video_feed')
def video_feed():
    global last_access_time
    last_access_time = time.time()
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def check_timeout():
    global last_access_time
    while True:
        current_time = time.time()
        if current_time - last_access_time > TIMEOUT:
            print("Stopping video feed due to inactivity")
            # Add logic to stop the video feed
            break
        time.sleep(5)  # Check every 5 seconds
# Start the background thread
timeout_thread = threading.Thread(target=check_timeout)
timeout_thread.daemon = True
timeout_thread.start()


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)

