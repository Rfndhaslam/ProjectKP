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
import dlib
import threading

# Initialize dlib's face detector (HOG-based) and create the facial landmark predictor
detector = dlib.get_frontal_face_detector()
predictor_path = os.path.expanduser("~/kape_venv/lib64/python3.11/site-packages/face_recognition_models/models/shape_predictor_68_face_landmarks.dat")
predictor = dlib.shape_predictor(predictor_path)

# Get the base directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Use the base directory to create a relative path for the Firebase credentials
cred_path = os.path.join(base_dir, "sistempresensiditkape-firebase-adminsdk-nepdc-1f2e74a2d4.json")
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
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Set width
video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)  # Set height

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

# Function to detect nodding motion
def detect_head_shake(landmarks):
    left_eye = landmarks[36:42]
    right_eye = landmarks[42:48]
    nose = landmarks[27:36]

    nose_x = [point[0] for point in nose]
    left_eye_x = [point[0] for point in left_eye]
    right_eye_x = [point[0] for point in right_eye]

    # Calculate the horizontal movement of the nose relative to eyes
    eye_center_x = (sum(left_eye_x) + sum(right_eye_x)) / 12
    nose_mean_x = sum(nose_x) / len(nose_x)

    # Check for significant lateral movement (shaking head)
    head_shake_detected = abs(nose_mean_x - eye_center_x) > 5

    return head_shake_detected

frame = None
ret = False
processing_lock = threading.Lock()

def video_stream():
    global frame, ret
    while True:
        with processing_lock:
            ret, frame = video_capture.read()

def show_frame():
    global register_wajah, frame, ret

    if not ret:
        root.after(10, show_frame)  # Continue loop even if no frame
        return

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    detected_faces = detector(gray_frame)

    face_names = []
    face_statuses = []
    
    for face in detected_faces:
        shape = predictor(gray_frame, face)
        landmarks = [(shape.part(i).x, shape.part(i).y) for i in range(68)]
        head_shake_detected = detect_head_shake(landmarks)

        # Lakukan identifikasi hanya jika geleng kepala terdeteksi
        if head_shake_detected:
            top, right, bottom, left = face.top(), face.right(), face.bottom(), face.left()
            encoding_wajah = face_recognition.face_encodings(frame, [(top, right, bottom, left)])[0]

            if len(encodings_data_wajah) > 0:
                face_distances = face_recognition.face_distance(encodings_data_wajah, encoding_wajah)
                best_match_index = np.argmin(face_distances)
                if face_distances[best_match_index] < 0.6:
                    nip = list(info_data_wajah.keys())[best_match_index]
                    name = info_data_wajah[nip]['nama']
                    face_statuses.append("Dikenal")
                else:
                    name = "Tak Dikenal"
                    face_statuses.append("Tak Dikenal")
            else:
                name = "Tak Dikenal"
                face_statuses.append("Tak Dikenal")

            face_names.append(name)

            if name not in recorded_wajah:
                recorded_wajah.add(name)

                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")
                current_day = now.strftime("%A")
                current_date = now.strftime("%Y-%m-%d")
                current_year = now.strftime("%Y")

                if now <= deadline_presensi:
                    status = "Tepat Waktu"
                else:
                    status = "Terlambat"

                if name != "Tak Dikenal":
                    csv_writer.writerow([nip, name, current_time, current_day, current_date, current_year, status])
                    csv_file.flush()
                    insert_attendance_to_firebase(nip, name, current_time, current_day, current_date, current_year, status)
                    info_update_wajah(nip, name, status, True)
                else:
                    info_update_wajah("N/A", "Tak Dikenal", "Tak Dikenal", False)
        else:
            face_names.append("Tak Dikenal")
            face_statuses.append("Tak Dikenal")
            info_update_wajah("N/A", "Tak Dikenal", "Tak Dikenal", False)

    if register_wajah and detected_faces:
        face = detected_faces[0]
        top, right, bottom, left = face.top(), face.right(), face.bottom(), face.left()
        encoding_wajah = face_recognition.face_encodings(frame, [(top, right, bottom, left)])[0]

        new_face_name, new_face_nim = prompt_user_input()
        register_wajah_baru(new_face_name, new_face_nim, encoding_wajah)
        info_update_wajah(new_face_nim, new_face_name, "Registered", True)

        register_wajah = False

    for (face, name, status) in zip(detected_faces, face_names, face_statuses):
        top, right, bottom, left = face.top(), face.right(), face.bottom(), face.left()

        if status == "Tak Dikenal":
            color = (0, 0, 255)  # Red for unknown
        else:
            color = (0, 255, 0)  # Green for known

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

    # Convert the frame to an image that can be displayed
    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    img = Image.fromarray(cv2image)
    imgtk = ImageTk.PhotoImage(image=img)
    kamera_label.imgtk = imgtk
    kamera_label.configure(image=imgtk)
    root.after(10, show_frame)

def on_key_press(event):
    global register_wajah
    if event.char == "r":
        register_wajah = True

def on_closing():
    root.quit()
    video_capture.release()
    csv_file.close()

root.bind("<Key>", on_key_press)

update_date_time()

video_thread = threading.Thread(target=video_stream)
video_thread.daemon = True
video_thread.start()

root.protocol("WM_DELETE_WINDOW", on_closing)
show_frame()
root.mainloop()
