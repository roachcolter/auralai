from typing import Self, Text
from maix._maix.audio import Player
from maix._maix.peripheral.gpio import GPIO
import requests
import os
import sys
import base64
import socket
import subprocess
from PIL import Image
from gtts import gTTS
from maix import image as gambar
from maix import camera, display, time, nn, app, touchscreen, gpio, pinmap
from maix import audio, time, app
from pydub import AudioSegment
from maix import network, err
from requests.exceptions import ConnectionError, Timeout, RequestException
import re
########################################################

def get_ntpd_pid():
    try:
        # Get the output of the ps aux | grep ntp command
        result = subprocess.run(
            "ps aux | grep '[n]tpd' | awk '{print $1}'", 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            text=True
        )
        pid = result.stdout.strip()
        return pid
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        return None

def kill_ntpd(pid):
    try:
        # Kill the process with the given PID
        os.system(f"kill -9 {pid}")
        print(f"Process with PID {pid} has been killed.")
    except Exception as e:
        print(f"Error occurred: {e}")

#Clean-Text
def clean_text(text):
    cleaned_text = re.sub(r'#[^\s]*', '', text)  # Remove hashtags
    cleaned_text = re.sub(r'\*+', '', cleaned_text)
    cleaned_text = re.sub(r'\_+', '', cleaned_text)  # Remove asterisks
    return cleaned_text.strip()

#TTS
def speak(text):
    cleaned_text = clean_text(text)
    tts = gTTS(text=cleaned_text, lang='id')
    tts.save("/root/output.mp3")

# Function to convert MP3 to PCM
def convert_mp3_to_pcm(mp3_file, pcm_file, target_sample_rate=48000):
    audio1 = AudioSegment.from_mp3(mp3_file)
    audio1 = audio1.set_frame_rate(target_sample_rate)
    audio1.export(pcm_file, format="s16le")

# Open and read PCM data
def play_pcm_in_chunks(filename, chunk_size):
    with open(filename, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            if len(data) > 0:
                try:
                    print(f"Playing chunk of size {len(data)} bytes")
                    p.play(data)
                except Exception as e:
                    print(f"Error playing data chunk: {e}")
            
#Transfer Data
def send_file(client_socket, filename):
    with open(filename, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            client_socket.sendall(data)

def send_file2(server_address, port, file_name):
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Connect to the server
    client_socket.connect((server_address, port))
    
    # Open the file to be sent
    with open(file_name, 'rb') as f:
        # Read data in chunks and send them
        data = f.read(1024)
        while data:
            client_socket.send(data)
            data = f.read(1024)
    
    print(f"File sent successfully: {file_name}")
    
    # Close the socket
    client_socket.close()

# Open and read PCM data
def intro():
    p = audio.Player(sample_rate=48000, format=audio.Format.FMT_S16_LE, channel = 1)
    with open('/root/aural.pcm', 'rb') as f:
        ctx = f.read()

    while not app.need_exit():
        p.play(bytes(ctx))
        time.sleep(1.5)
        break
    print("play finish!")

#####################################################


#Wifi Connect
HOST = '192.168.1.10'  # Replace with the server's IP address
PORT = 12345  # Same port as used by the server
try:
    w = network.wifi.Wifi()
    print("IP:", w.get_ip())
    SSID = "Aural"
    PASSWORD = "roach2024"
    print("Connecting to", SSID)
    e = w.connect(SSID, PASSWORD, wait=True, timeout=15)
    err.check_raise(e, "Failed to connect to WiFi")
    print("IP:", w.get_ip())
except RuntimeError as e:
    print("No wifi detected")
    pass
#Time-Sync
pid = get_ntpd_pid()
if pid:
    kill_ntpd(pid)
    print("NTPD process.")
else:
    pass
    print("NTPD process not found.")

# Function to measure button press duration
def measure_button_press_duration(button_pin):
    start_time = None
    
    while not app.need_exit():
        if int(button_pin.value()) == 0:
            if start_time is None:
                start_time = time.time()
        else:
            if start_time is not None:
                duration = time.time() - start_time
                start_time = None
                return duration
        time.sleep(0.01)  # Small delay to debounce the button

#Starters
os.system('ntpdate asia.pool.ntp.org')
API_KEY = "sk-proj-PIEy1k039iVBHIeJFOlUT3BlbkFJKhbXkgLYyFnOpBm2EASR"
MODEL = "gpt-4o"
URL = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
ts = touchscreen.TouchScreen()
cam = camera.Camera(320, 512)   # Manually set resolution, default is too large
disp = display.Display(320, 512)  
img2 = gambar.Image(disp.width(), disp.height())
audio_folder = '/root/pcm/'
detector = nn.YOLOv5(model="/root/models/yolov5s.mud")
camoffline = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())

#Tombol
button_pin = GPIO(pin="GPIOA17", mode=gpio.Mode.OUT, pull=gpio.Pull.PULL_UP)
button_pin2 = GPIO(pin="GPIOA19", mode=gpio.Mode.OUT, pull=gpio.Pull.PULL_UP)

#Audio
pinmap.set_pin_function("A24", "GPIOA24")
transistor = gpio.GPIO("GPIOA24", gpio.Mode.OUT)
p = audio.Player(channel=1)
print("sample_rate:{} format:{} channel:{}".format(p.sample_rate(), p.format(), p.channel()))
mp3_file = '/root/output.mp3'
pcm_file = '/root/kontol.pcm'
chunk_size = 512  # Adjusted chunk size

########################################################

#########ONLINE##########

# Main loop
while not app.need_exit():
    transistor.value(0)
    # Measure the duration of the button press
    duration = measure_button_press_duration(button_pin)
    print("Standby...")
    print("----------")
    if duration is not None:
        if duration < 1:
            # Online Mode
            try:
                print("Online Mode")
                disp.show(img2)
                if os.path.exists('/root/jawaban.txt'):
                    os.remove('/root/jawaban.txt')
                if os.path.exists('/root/output.mp3'):
                    os.remove('/root/output.mp3')
                
                img = cam.read()
                img.save("/root/test.jpg")
                image_path = '/root/test.jpg'
                image = Image.open(image_path)
                disp.show(img)
                
                rotated_image = image.rotate(90, expand=True)
                rotated_image.save('/root/test2.jpg')
                image_path = ("/root/test2.jpg")
                
                def encode_image(image_path):
                    with open(image_path, "rb") as image_file:
                        return base64.b64encode(image_file.read()).decode("utf-8")
                
                base64_image = encode_image(image_path)
                
                payload = {
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": "Anda adalah sebuah mata yang tugasnya membantu saya menjelaskan apa yang ada di depan saya termasuk warnanya dengan memberi tahu arah setiap benda relatif pada gambar, contohnya seperti kanan,kiri,atas,bawah! Maksimal 50 kata dengan BAHASA INDONESIA!"},
                        {"role": "user", "content": [
                            {"type": "image_url", "image_url": {
                                "url": f"data:image/jpg;base64,{base64_image}"}
                            }
                        ]}
                    ],
                }
                
                response = requests.post(URL, headers=headers, json=payload)
                jawaban = str("")
                if response.status_code == 200:
                    completion = response.json()
                    jawaban = str(completion['choices'][0]['message']['content'])
                    print(jawaban)
                else:
                    print(f"Error: {response.status_code}, {response.text}")
                
                speak(jawaban)
                if os.path.exists("/root/output.mp3"):
                    print("TTS Dibuat")
                
                with open("/root/jawaban.txt", "w") as file:
                    file.write(jawaban)
                print("File has been written.")
                
                with open("/root/modeonline.txt", "w") as file:
                    file.write("1")
                print("Online Mode.")
                
                file_name = '/root/modeonline.txt'
                send_file2(HOST, PORT, file_name)
                time.sleep(0.2)
                
                convert_mp3_to_pcm(mp3_file, pcm_file)
                transistor.value(1)
                play_pcm_in_chunks(pcm_file, chunk_size)                
                time.sleep(1)
                transistor.value(0)
                
                # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                #     client_socket.connect((HOST, PORT))
                #     send_file(client_socket, '/root/output.mp3')
                #     print("MP3 file sent successfully.")
                # time.sleep(0.8)
                
                # file_name = '/root/jawaban.txt'
                # send_file2(HOST, PORT, file_name)
                # print("All files sent.")
                
                if os.path.exists('/root/output.mp3'):
                    os.remove('/root/output.mp3')
                if os.path.exists('/root/output.pcm'):
                    os.remove('/root/output.pcm')
                if os.path.exists('/root/jawaban.txt'):
                    os.remove('/root/jawaban.txt')
                
            except (ConnectionError, Timeout) as e:
                print(f"Network-related error occurred: {e}")
            except RequestException as e:
                print(f"An error occurred: {e}")
        
        elif 1 <= duration < 3:
            # Offline Mode
            try:
                print("Offline Mode")
                img = camoffline.read()
                
                def send_text_file_for_object(obj):
                    obj = obj.strip()
                    text_file_name = f"{obj}.txt"
                    text_file_path = os.path.join(audio_folder, text_file_name)
                    
                    with open(text_file_path, 'w') as f:
                        f.write(f"Detected object: {obj}")
                    
                    server_address = (HOST, PORT)
                    
                    with open("/root/modeoffline.txt", "w") as file:
                        file.write("0")
                    print("Offline Mode.")
                    
                    file_name = '/root/modeoffline.txt'
                    send_file2(HOST, PORT, file_name)
                    time.sleep(0.5)
                    
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.connect(server_address)
                        sock.sendall(obj.encode())
                    
                    print(f"Sent text file for {obj}")
                
                img3 = img.rotation_corr(z_rotation=-1.57)
                objs = detector.detect(img3, conf_th=0.5, iou_th=0.45)
                
                for obj in objs:
                    img3.draw_rect(obj.x, obj.y, obj.w, obj.h, color=gambar.COLOR_RED)
                    msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
                    img3.draw_string(obj.x, obj.y, msg, color=gambar.COLOR_RED)
                    objek = f'{detector.labels[obj.class_id]}'
                    disp.show(img3)
                    send_text_file_for_object(objek)
                    time.sleep(3.5)
            
            except Exception as e:
                print(f"An error occurred: {e}")
        
        else:
            # Text Mode
            try:
                print("Text mode")
                disp.show(img2)
                if os.path.exists('/root/jawaban.txt'):
                    os.remove('/root/jawaban.txt')
                if os.path.exists('/root/output.mp3'):
                    os.remove('/root/output.mp3')
                
                img = cam.read()
                img.save("/root/test.jpg")
                image_path = '/root/test.jpg'
                image = Image.open(image_path)
                disp.show(img)
                
                rotated_image = image.rotate(90, expand=True)
                rotated_image.save('/root/test2.jpg')
                image_path = ("/root/test2.jpg")
                
                def encode_image(image_path):
                    with open(image_path, "rb") as image_file:
                        return base64.b64encode(image_file.read()).decode("utf-8")
                
                base64_image = encode_image(image_path)
                
                payload = {
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": "Anda adalah sebuah mata yang tugasnya membantu saya membaca seluruh teks yang ada di gambar ini, GUNAKAN BAHASA INDONESIA!"},
                        {"role": "user", "content": [
                            {"type": "image_url", "image_url": {
                                "url": f"data:image/jpg;base64,{base64_image}"}
                            }
                        ]}
                    ],
                }
                
                response = requests.post(URL, headers=headers, json=payload)
                jawaban = str("")
                if response.status_code == 200:
                    completion = response.json()
                    jawaban = str(completion['choices'][0]['message']['content'])
                    print(jawaban)
                else:
                    print(f"Error: {response.status_code}, {response.text}")
                
                speak(jawaban)
                if os.path.exists("/root/output.mp3"):
                    print("TTS Dibuat")
                
                with open("/root/jawaban.txt", "w") as file:
                    file.write(jawaban)
                print("File has been written.")
                
                with open("/root/modeteks.txt", "w") as file:
                    file.write("1")
                print("Text Mode.")
                
                file_name = '/root/modeteks.txt'
                send_file2(HOST, PORT, file_name)
                time.sleep(0.2)
                
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                    client_socket.connect((HOST, PORT))
                    send_file(client_socket, '/root/output.mp3')
                    print("MP3 file sent successfully.")
                time.sleep(0.8)
                
                file_name = '/root/jawaban.txt'
                send_file2(HOST, PORT, file_name)
                print("All files sent.")
                
                if os.path.exists('/root/output.mp3'):
                    os.remove('/root/output.mp3')
                if os.path.exists('/root/output.pcm'):
                    os.remove('/root/output.pcm')
                if os.path.exists('/root/jawaban.txt'):
                    os.remove('/root/jawaban.txt')
                
            except (ConnectionError, Timeout) as e:
                print(f"Network-related error occurred: {e}")
            except RequestException as e:
                print(f"An error occurred: {e}")
    
    else:
        print("Standby")
        time.sleep(0.2)