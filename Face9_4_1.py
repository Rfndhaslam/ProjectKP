import face_recognition
import cv2
import numpy as np
import csv
from datetime import datetime, timedelta
import os
import tkinter as tk
from tkinter import simpledialog, Label
from PIL import Image, ImageTk
import firebase_admin
from firebase_admin import credentials, db

# Get the base directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Use the base directory to create a relative path for the Firebase credentials
cred_path = os.path.join(base_dir, "D:/vscode/KAPE2/sistempresensidit-firebase-adminsdk-okqli-e67a29dc70.json")
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://sistempresensidit-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

def insert_attendance_to_firebase(nip, nama, time, day, date, year, status):
    ref = db.reference('data_presensi')
    date_ref = ref.child(date)
    time_ref = date_ref.child(time)
    time_ref.set({
        'nip': nip,
        'nama': nama,
        'day': day,
        'year': year,
        'status': status
    })

def insert_to_firebase(nip, nama, encoding):
    ref = db.reference('data_wajah')
    ref.child(nip).set({
        'nip': nip,
        'nama': nama,
        'encoding_foto': encoding.tolist()
    })

def load_data_wajah():
    ref = db.reference('data_wajah')
    data = ref.get()
    data_wajah = {}
    if data:
        for nip, value in data.items():
            if 'encoding_foto' in value and 'nama' in value:  # Check if necessary keys exist
                value['encoding_foto'] = np.array(value['encoding_foto'])
                data_wajah[nip] = value
    return data_wajah


def register_wajah_baru(nama, nip, encoding_wajah):
    info_data_wajah[nip] = {
        'nip': nip,
        'nama': nama,
        'encoding_foto': encoding_wajah
    }
    insert_to_firebase(nip, nama, encoding_wajah)
    print(f"Wajah baru yang teregistrasi: {nama} - {nip}")
    return nip, nama

info_data_wajah = load_data_wajah()
encodings_data_wajah = [info['encoding_foto'] for info in info_data_wajah.values()]

video_capture = cv2.VideoCapture(0)

datetime_terkini = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
csv_file_path = os.path.join(os.path.dirname(__file__), f'Daftar_Presensi_{datetime_terkini}.csv')

csv_file = open(csv_file_path, 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["NIP", "Nama", "Waktu", "Hari", "Tanggal", "Tahun", "Status Kehadiran"])

deadline_presensi = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
hari_berakhir = deadline_presensi + timedelta(days=1)

register_wajah = False

def prompt_user_input():
    root = tk.Tk()
    root.withdraw()  

    nama = simpledialog.askstring("Input", "Masukkan Nama:")
    nip = simpledialog.askstring("Input", "Masukkan NIP:")

    root.destroy()

    return nama, nip

root = tk.Tk()
root.title("Sistem Presensi Face Recognition DIT")

judul_label = Label(root, text="Sistem Presensi Berbasis Face Recognition", font=("Helvetica", 16))
judul_label.grid(row=0, column=0, columnspan=2)

tanggal_label = Label(root, text="", font=("Helvetica", 12))
tanggal_label.grid(row=1, column=0, columnspan=2)

waktu_label = Label(root, text="", font=("Helvetica", 12))
waktu_label.grid(row=2, column=0, columnspan=2)

kamera_label = Label(root)
kamera_label.grid(row=3, column=0, padx=10, pady=10, sticky="nw")

info_frame = tk.Frame(root, bd=2, relief=tk.SOLID, height=150, width=300)  
info_frame.grid(row=3, column=1, padx=10, pady=10, sticky="nw")
info_frame.grid_propagate(False)  

nama_label = Label(info_frame, text="Nama: ", font=("Helvetica", 12), bg="lightgrey", anchor="w", width=29)
nama_label.grid(row=0, column=0, sticky="w", padx=10, pady=5, ipadx=5, ipady=5)

nip_label = Label(info_frame, text="NIP: ", font=("Helvetica", 12), bg="lightgrey", anchor="w", width=29)
nip_label.grid(row=1, column=0, sticky="w", padx=10, pady=5, ipadx=5, ipady=5)

status_label = Label(info_frame, text="Status: ", font=("Helvetica", 12), bg="lightgrey", anchor="w", width=29)
status_label.grid(row=2, column=0, sticky="w", padx=10, pady=5, ipadx=5, ipady=5)

def info_update_wajah(nip, nama, status, data_wajah2 = True):
    nama_label.config(text=f"Nama: {nama}")
    nip_label.config(text=f"NIP: {nip}")
    status_label.config(text=f"Status: {status}")

    if data_wajah2:
        nama_label.config(bg="lightgreen")
        nip_label.config(bg="lightgreen")
        status_label.config(bg="lightgreen")
    elif nama == "Tak Dikenal":
        nama_label.config(bg="red")
        nip_label.config(bg="red")
        status_label.config(bg="red")
    else:
        nama_label.config(bg="lightgrey")
        nip_label.config(bg="lightgrey")
        status_label.config(bg="lightgrey")


def update_date_time():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    current_date = now.strftime("%A, %Y-%m-%d")
    waktu_label.config(text=f"Waktu: {current_time}")
    tanggal_label.config(text=f"Tanggal: {current_date}")
    root.after(1000, update_date_time)

recorded_wajah = set()

def show_frame():
    global register_wajah

    ret, frame = video_capture.read()
    if not ret:
        return

    frame = cv2.resize(frame, (320, 240)) 

    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
    face_names = []

    if register_wajah:
        for encoding_wajah in face_encodings:
            new_face_name, new_face_nim = prompt_user_input()
            if new_face_name and new_face_nim:
                nip, nama = register_wajah_baru(new_face_name, new_face_nim, encoding_wajah)
                print(f"Registration successful for {new_face_name} - {new_face_nim}")
                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")
                current_day = now.strftime("%A")
                current_date = now.strftime("%Y-%m-%d")
                current_year = now.strftime("%Y")
                status = "Teregistrasi"
                csv_writer.writerow([new_face_nim, new_face_name, current_time, current_day, current_date, current_year, status])
        register_wajah = False
    else:
        detected_faces = {}
        for encoding_wajah in face_encodings:
            found = False
            for nama, face_info in info_data_wajah.items():
                stored_encoding = np.array(face_info['encoding_foto'])
                face_distances = face_recognition.face_distance([stored_encoding], encoding_wajah)
                if face_distances[0] < 0.4: 
                    nip = face_info['nip']
                    full_name = face_info['nama']
                    if full_name not in detected_faces:
                        detected_faces[full_name] = nip
                    found = True
                    break

            if not found:
                face_names.append("Tak Dikenal")
            else:
                face_names.append(full_name)

        nip, full_name, status = "", "", ""

        if detected_faces:
            for full_name, nip in detected_faces.items():
                now = datetime.now()
                if now <= deadline_presensi:
                    status = "Hadir"
                else:
                    status = "Telat"
                info_update_wajah(nip, full_name, status)

                if full_name not in recorded_wajah:
                    recorded_wajah.add(full_name)
                    current_time = now.strftime("%H:%M:%S")
                    current_day = now.strftime("%A")
                    current_date = now.strftime("%Y-%m-%d")
                    current_year = now.strftime("%Y")
                    csv_writer.writerow([nip, full_name, current_time, current_day, current_date, current_year, status])
                    insert_attendance_to_firebase(nip, full_name, current_time, current_day, current_date, current_year, status)
                    recorded_wajah.add(nama)
        else:
            info_update_wajah("", "", "", data_wajah2=False)

    for (top, right, bottom, left), nama in zip(face_locations, face_names):
        top = int(top / 0.5)
        right = int(right / 0.5)
        bottom = int(bottom / 0.5)
        left = int(left / 0.5)
        
        color = (0, 0, 255)  

        if nama != "Unknown":
            if nama in recorded_wajah:
                color = (0, 255, 0)  
            else:
                color = (255, 0, 0)  

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)

        font_thickness = max((right - left) // 300, 1)  
        font = cv2.FONT_HERSHEY_DUPLEX
        text_size = cv2.getTextSize(nama, font, 0.3, font_thickness)[0]

        text_x = left + 6
        text_y = bottom - 6
 
        if text_x + text_size[0] > frame.shape[1]:
            text_x = frame.shape[1] - text_size[0] - 5
        if text_y - text_size[1] < 0:
            text_y = text_size[1] + 5

        cv2.putText(frame, nama, (left + 6, bottom - 6), font, 0.3, (255, 255, 255), font_thickness)

    outline_color = (0, 0, 128)
    frame_height, frame_width = frame.shape[:2]
    outline_thickness = 5
    cv2.rectangle(frame, (0, 0), (frame_width, frame_height), outline_color, outline_thickness)

    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    imgtk = ImageTk.PhotoImage(image=img)
    kamera_label.imgtk = imgtk
    kamera_label.config(image=imgtk)
    kamera_label.after(10, show_frame)

def on_key_press(event):
    global register_wajah
    if event.char == 'r':
        register_wajah = True

root.bind("<Key>", on_key_press)

update_date_time()

show_frame()

root.mainloop()

video_capture.release()
csv_file.close()
