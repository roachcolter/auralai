from maix._maix.peripheral.gpio import GPIO
from mutagen.mp3 import MP3
import re,requests, os, base64, subprocess, time as waktu
from PIL import Image
from gtts import gTTS
from maix import camera, display, time, nn, app, gpio, audio, time, app, image as gambar, network, err
from pydub import AudioSegment
from requests.exceptions import ConnectionError, Timeout, RequestException

########################################################
#Synchronization
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
    print("CONVERTING TO PCM")
    audio1 = AudioSegment.from_mp3(mp3_file)
    audio1 = audio1.set_frame_rate(target_sample_rate)
    audio1.export(pcm_file, format="s16le")
    print("CONVERTED TO PCM")

# Open and read PCM data
def play_pcm_with_timer(filename, mp3_length, chunk_size):
    transistor.high()
    p = audio.Player(channel = 1)
    start_time = waktu.time()
    elapsed_time = 0
    with open(filename, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            elapsed_time = waktu.time() - start_time
            if not data:
                break
            try:
                p.play(data)
            except Exception as e:
                print(f"Error playing data chunk: {e}")
        time.sleep(mp3_length - elapsed_time)
        transistor.low()
    

def play_intro_with_timer(filename, mp3_length, chunk_size):  
    transistor.high()
    p = audio.Player(channel = 2)
    start_time = waktu.time()
    elapsed_time = 0
    with open(filename, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            elapsed_time = waktu.time() - start_time
            if not data:
                break
            try:
                p.play(data)
            except Exception as e:
                print(f"Error playing data chunk: {e}")
        time.sleep(mp3_length - elapsed_time)
        transistor.low()
def get_mp3_length(mp3_file):
    audio = MP3(mp3_file)
    return audio.info.length 

# Function to switch mode
def switch_mode():
    global current_mode
    if offlineonly == False :
        if current_mode == "online":
            play_pcm_with_timer(filename="/root/pcm/modeoffline.pcm", mp3_length=get_mp3_length("/root/audio/modeoffline.mp3"), chunk_size=512)
            current_mode = "offline"
        elif current_mode == "offline":
            play_pcm_with_timer(filename="/root/pcm/modeteks.pcm", mp3_length=get_mp3_length("/root/audio/modeteks.mp3"), chunk_size=512)
            current_mode = "text"
        else:
            play_pcm_with_timer(filename="/root/pcm/modeonline.pcm", mp3_length=get_mp3_length("/root/audio/modeonline.mp3"), chunk_size=512)
            current_mode = "online"
        print(f"Switched to {current_mode} mode.")
    if offlineonly == True :
        play_pcm_with_timer(filename="/root/pcm/modeoffline.pcm", mp3_length=get_mp3_length("/root/audio/modeoffline.mp3"), chunk_size=512)
        current_mode = "offline"


# Transfer Data
# def send_file(client_socket, filename):
#     with open(filename, 'rb') as f:
#         while True:
#             data = f.read(1024)
#             if not data:
#                 break
#             client_socket.sendall(data)

# def send_file2(server_address, port, file_name):
#     # Create a socket object
#     client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
#     # Connect to the server
#     client_socket.connect((server_address, port))
    
#     # Open the file to be sent
#     with open(file_name, 'rb') as f:
#         # Read data in chunks and send them
#         data = f.read(1024)
#         while data:
#             client_socket.send(data)
#             data = f.read(1024)
    
#     print(f"File sent successfully: {file_name}")
    
#     # Close the socket
#     client_socket.close()
#####################################################
transistor = GPIO(pin="GPIOA22", mode=gpio.Mode.OUT)
transistor.low()

# Play booting sound
play_pcm_with_timer(filename="/root/pcm/menyalakan.pcm", mp3_length=get_mp3_length("/root/audio/menyalakan.mp3"), chunk_size=512)

# Wifi Connect
#HOST = '192.168.16.27'  # Replace with the server's IP address
#PORT = 12345  # Same port as used by the server
play_pcm_with_timer(filename="/root/pcm/menghubungkan.pcm", mp3_length=get_mp3_length("/root/audio/menghubungkan.mp3"), chunk_size=512)
try:
    w = network.wifi.Wifi()
    e = w.connect("auralai", "juarapimnas", wait=True, timeout=12)
    err.check_raise(e, "connect wifi failed")
    print("Connect success, got ip:", w.get_ip())
    offlineonly = False
    play_pcm_with_timer(filename="/root/pcm/terhubung.pcm", mp3_length=get_mp3_length("/root/audio/terhubung.mp3"), chunk_size=512)
except RuntimeError as e:
    print("No wifi detected")
    play_pcm_with_timer(filename="/root/pcm/tidakterhubung.pcm", mp3_length=get_mp3_length("/root/audio/tidakterhubung.mp3"), chunk_size=512)
    offlineonly = True
    pass

current_mode = ""
if offlineonly == False :
    current_mode = "online"
if offlineonly == True :
    current_mode = "offline"

# Time-Sync
if offlineonly == False :
    pid = get_ntpd_pid()
    if pid:
        play_pcm_with_timer(filename="/root/pcm/sinkron.pcm", mp3_length=get_mp3_length("/root/audio/sinkron.mp3"), chunk_size=512)
        kill_ntpd(pid)
        print("NTPD process.")
        os.system('ntpdate asia.pool.ntp.org')
    else:
        pass
        print("NTPD process not found.")

else :
    pass

# Variables
API_KEY = "sk-proj-PIEy1k039iVBHIeJFOlUT3BlbkFJKhbXkgLYyFnOpBm2EASR"
MODEL = "gpt-4o"
URL = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
cam = camera.Camera(320, 512)   # Manually set resolution, default is too large
disp = display.Display(320, 512) 
img2 = gambar.Image(disp.width(), disp.height())
audio_folder = '/root/pcm/'
detector = nn.YOLOv5(model="/root/models/yolov5s.mud")
camoffline = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())


# Tombol
button_pin = GPIO(pin="GPIOA17", mode=gpio.Mode.OUT, pull=gpio.Pull.PULL_UP)
mode_button_pin = GPIO(pin="GPIOA19", mode=gpio.Mode.OUT, pull=gpio.Pull.PULL_UP)



def is_action_button_pressed():
    return int(button_pin.value()) == 0


# Function to measure button press duration
def measure_mode_button_press_duration():
    start_time = None
    while True:
        transistor.low()
        if int(mode_button_pin.value()) == 0:  # Button is pressed
            if start_time is None:
                start_time = waktu.time()
        else:
            if start_time is not None:
                # Calculate the duration
                duration = waktu.time() - start_time
                return duration
        time.sleep(0.01)  # Small delay to debounce the button

#Audio
mp3_file = '/root/output.mp3'
pcm_file = '/root/suara.pcm'
chunk_size = 512
auralmp3 = '/root/audio/aural.mp3'
auralpcm = '/root/pcm/aural.pcm'
aurallength = get_mp3_length(auralmp3)

########################################################

# Main loop
play_pcm_with_timer(filename="/root/pcm/menyala.pcm", mp3_length=get_mp3_length("/root/audio/menyala.mp3"), chunk_size=512)
play_intro_with_timer(filename="/root/pcm/auralmenyala.pcm", mp3_length=get_mp3_length("/root/audio/auralmenyala.mp3"), chunk_size=512)
if offlineonly == False:
    play_pcm_with_timer(filename="/root/pcm/modeonline.pcm", mp3_length=get_mp3_length("/root/audio/modeonline.mp3"), chunk_size=512)
if offlineonly == True:
    play_pcm_with_timer(filename="/root/pcm/modeoffline.pcm", mp3_length=get_mp3_length("/root/audio/modeoffline.mp3"), chunk_size=512)
while not app.need_exit():
    transistor.low()
    #Clearings
    if os.path.exists('/root/output.mp3'):
        os.remove('/root/output.mp3')
    if os.path.exists('/root/suara.pcm'):
        os.remove('/root/suara.pcm')
    if os.path.exists('/root/jawaban.txt'):
        os.remove('/root/jawaban.txt')
    if os.path.exists('/root/suara.pcm'):
        os.remove('/root/suara.pcm')
    print(f"Current mode: {current_mode}")
    print("----------")
    # Measure the duration of the button press
    if int(mode_button_pin.value()) == 0:
        duration = measure_mode_button_press_duration()
        if duration >= 2 and current_mode == "text":
            # Play palsu.pcm if pressed for more than 3 seconds
            play_intro_with_timer(filename="/root/pcm/shutter.pcm", mp3_length=get_mp3_length("/root/audio/shutter.mp3"), chunk_size=512)
            time.sleep(5)
            play_intro_with_timer(filename="/root/pcm/auralmenyala.pcm", mp3_length=get_mp3_length("/root/audio/auralmenyala.mp3"), chunk_size=512)
            time.sleep(2)
            play_pcm_with_timer(filename="/root/pcm/001.pcm", mp3_length=get_mp3_length("/root/audio/palsu.mp3"), chunk_size=512)
        else:
            # Switch mode if pressed for less than 3 seconds
            switch_mode()
        time.sleep(0.5)  # Debouncing delay
    if is_action_button_pressed():
        play_intro_with_timer(filename="/root/pcm/shutter.pcm", mp3_length=get_mp3_length("/root/audio/shutter.mp3"), chunk_size=512)
        if current_mode == "online":
            try:
                print("Online Mode")
                if os.path.exists('/root/jawaban.txt'):
                    os.remove('/root/jawaban.txt')
                if os.path.exists('/root/output.mp3'):
                    os.remove('/root/output.mp3')
                
                #Take Picture
                img = cam.read()
                img.save("/root/test.jpg")
                image_path = '/root/test.jpg'
                image = Image.open(image_path)
                disp.show(img)
                #Rotate Picture
                rotated_image = image.rotate(90, expand=True)
                rotated_image.save('/root/test2.jpg')
                image_path = ("/root/test2.jpg")
                #Encode Picture
                def encode_image(image_path):
                    with open(image_path, "rb") as image_file:
                        return base64.b64encode(image_file.read()).decode("utf-8")
                base64_image = encode_image(image_path)
                
                #Send to Chat-GPT
                payload = {
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": "Anda adalah sebuah mata yang tugasnya membantu saya menjelaskan apa yang ada di depan saya termasuk warnanya dengan memberi tahu arah setiap benda relatif pada gambar, contohnya seperti kanan,kiri,atas,bawah! BERI TAHU SAJA APA YANG ADA DI GAMBAR DAN JANGAN TAMBAH KATA-KATA LAIN! Maksimal 40 kata dengan BAHASA INDONESIA!"},
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
                
                #Google Text-To-Speech
                speak(jawaban)
                if os.path.exists("/root/output.mp3"):
                    print("TTS Dibuat")
                with open("/root/jawaban.txt", "w") as file:
                    file.write(jawaban)
                print("File has been written.")
                time.sleep(0.2)

                # with open("/root/modeonline.txt", "w") as file:
                #     file.write("1")
                # print("Online Mode.")
                # file_name = '/root/modeonline.txt'
                # send_file2(HOST, PORT, file_name)
                # time.sleep(0.5)
                
                # Play Sound
                play_intro_with_timer(filename="/root/pcm/auralmenyala.pcm", mp3_length=get_mp3_length("/root/audio/auralmenyala.mp3"), chunk_size=512)
                mp3_length = get_mp3_length(mp3_file)
                convert_mp3_to_pcm(mp3_file, pcm_file)
                print("converting to pcm")
                print("playing audio")
                play_pcm_with_timer(pcm_file, mp3_length, chunk_size) 
                print("audio played")               
                
                # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                #     client_socket.connect((HOST, PORT))
                #     send_file(client_socket, '/root/output.mp3')
                #     print("MP3 file sent successfully.")
                # time.sleep(0.8)
                
                # file_name = '/root/jawaban.txt'
                # send_file2(HOST, PORT, file_name)
                # print("All files sent.")
                
            except (ConnectionError, Timeout) as e:
                print(f"Network-related error occurred: {e}")
                play_pcm_with_timer("/root/pcm/koneksi.pcm", get_mp3_length('/root/audio/koneksi.mp3'), chunk_size)
            except RequestException as e:
                print(f"An error occurred: {e}")
                play_pcm_with_timer("/root/pcm/koneksi.pcm", get_mp3_length('/root/audio/koneksi.mp3'), chunk_size)

        # Offline Mode
        elif current_mode == "offline":
            imgoffline = camoffline.read()  # Capture the image
            img2 = imgoffline.rotation_corr(z_rotation=-1.57)  # Rotate the image
            objs = detector.detect(img2, conf_th=0.5, iou_th=0.45)
            objs = detector.detect(img2, conf_th=0.5, iou_th=0.45)
            print("Offline Mode")
            try:
                for obj in objs:
                    img2.draw_rect(obj.x, obj.y, obj.w, obj.h, color=gambar.COLOR_RED)
                    msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
                    img2.draw_string(obj.x, obj.y, msg, color=gambar.COLOR_RED)
                    objek = f'{detector.labels[obj.class_id]}'
                    disp.show(img2)

                    intromp3 = '/root/audio/intro.mp3'
                    intropcm = '/root/pcm/intro.pcm'
                    introlength = get_mp3_length(intromp3)
                    
                    print("123")
                    print(objek.lstrip())
                    objekreal = objek.lstrip()
                    offlinemp3_file = f'/root/audio/{objekreal}.mp3'
                    offline_length = get_mp3_length(offlinemp3_file)
                    offline_file = f"/root/pcm/{objekreal}.pcm"
                    
                    # Play Sound
                    play_pcm_with_timer(intropcm, introlength, chunk_size)
                    play_pcm_with_timer(offline_file, offline_length, chunk_size)             
                

            except Exception as e:
                print(f"An error occurred: {e}")
        
        elif current_mode == "text":
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
                        {"role": "system", "content": "Anda adalah sebuah mata yang tugasnya membantu saya membaca seluruh teks yang ada di gambar ini, tetapi jika ada grafik di dalam gambar, baca seluruh informasi yang ada di grafik tersebut, JIKA ADA LOGO BERUPA TEKS BACA JUGA LOGO TERSEBUT, CUKUP JAWAB SAJA APA YANG ADA DI GAMBAR, JANGAN TAMBAH KATA KATA LAIN, GUNAKAN BAHASA INDONESIA!"},
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

                # Play Sound
                play_intro_with_timer(filename="/root/pcm/auralmenyala.pcm", mp3_length=get_mp3_length("/root/audio/auralmenyala.mp3"), chunk_size=512)
                mp3_length = get_mp3_length(mp3_file)
                convert_mp3_to_pcm(mp3_file, pcm_file)
                print("converting to pcm")
                print("playing audio")
                play_pcm_with_timer(pcm_file, mp3_length, chunk_size) 
                print("audio played")   
                
                # with open("/root/jawaban.txt", "w") as file:
                #     file.write(jawaban)
                # print("File has been written.")
                
                # with open("/root/modeteks.txt", "w") as file:
                #     file.write("1")
                # print("Text Mode.")
                
                # file_name = '/root/modeteks.txt'
                # send_file2(HOST, PORT, file_name)
                # time.sleep(0.2)
                
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
                play_pcm_with_timer("/root/pcm/koneksi.pcm", get_mp3_length('/root/audio/koneksi.mp3'), chunk_size)
                print(f"Network-related error occurred: {e}")
            except RequestException as e:
                play_pcm_with_timer("/root/pcm/koneksi.pcm", get_mp3_length('/root/audio/koneksi.mp3'), chunk_size)
                print(f"An error occurred: {e}")
        time.sleep(0.2)
    if is_action_button_pressed() and int(mode_button_pin.value()) == 0 and current_mode == "text" :
            play_pcm_with_timer("/root/pcm/001.pcm", get_mp3_length('/root/audio/palsu.mp3'), chunk_size)
    else:
        print("Standby")
        time.sleep(0.2)
