import face_recognition
import cv2
import numpy as np
import csv
from datetime import datetime, timedelta
import os
import tkinter as tk
from tkinter import simpledialog, Label, StringVar
from PIL import Image, ImageTk
import json

# File path for storing face encodings and information
face_data_file = "D:/vscode/KAPE2/face_data.json"

# Load known faces from local storage
def load_known_faces():
    if os.path.exists(face_data_file):
        with open(face_data_file, 'r') as file:
            data = json.load(file)
            for key, value in data.items():
                value['encoding'] = np.array(value['encoding'])
            return data
    return {}

# Save known faces to local storage
def save_known_faces(known_faces):
    with open(face_data_file, 'w') as file:
        data_to_save = {key: {'nim': value['nim'], 'name': value['name'], 'encoding': value['encoding'].tolist()} for key, value in known_faces.items()}
        json.dump(data_to_save, file)

# Register a new face
def register_new_face(name, nim, face_encoding):
    known_faces_info[name] = {'nim': nim, 'name': name, 'encoding': face_encoding}
    save_known_faces(known_faces_info)
    print(f"Registered new face: {name} - {nim}")
    return nim, name

# Get known faces from local storage
known_faces_info = load_known_faces()
known_face_encodings = [info['encoding'] for info in known_faces_info.values()]

# Video capture setup
video_capture = cv2.VideoCapture(0)

# Generate CSV file path based on current time
current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
csv_file_path = os.path.join(os.path.dirname(__file__), f'{current_datetime}.csv')

# Open CSV file for writing attendance
csv_file = open(csv_file_path, 'w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["NIM", "Name", "Time", "Day", "Date", "Year", "Status"])

# Attendance deadline
attendance_deadline = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
end_of_day = attendance_deadline + timedelta(days=1)

# Variables for new face registration
register_face = False

def prompt_user_input():
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window
    name = simpledialog.askstring("Input", "Enter name:")
    nim = simpledialog.askstring("Input", "Enter NIM:")
    root.destroy()
    return name, nim

students = list(known_faces_info.keys())
recorded_faces = set()

# Setup Tkinter window
root = tk.Tk()
root.title("Attendance System")

# Real-time display
title_label = Label(root, text="Attendance System", font=('Helvetica', 24))
title_label.grid(row=0, column=0, columnspan=2, pady=10)
time_label = Label(root, font=('Helvetica', 18))
time_label.grid(row=1, column=0, columnspan=2)
date_label = Label(root, font=('Helvetica', 18))
date_label.grid(row=2, column=0, columnspan=2)

# Video frame
video_frame = Label(root)
video_frame.grid(row=3, column=0, padx=10, pady=10)

# Detected face information
name_label = Label(root, text="Name:", font=('Helvetica', 14))
name_label.grid(row=3, column=1, sticky=tk.W, padx=10)
name_var = StringVar()
name_value = Label(root, textvariable=name_var, font=('Helvetica', 14))
name_value.grid(row=3, column=1, sticky=tk.E, padx=10)

nim_label = Label(root, text="NIM:", font=('Helvetica', 14))
nim_label.grid(row=4, column=1, sticky=tk.W, padx=10)
nim_var = StringVar()
nim_value = Label(root, textvariable=nim_var, font=('Helvetica', 14))
nim_value.grid(row=4, column=1, sticky=tk.E, padx=10)

status_label = Label(root, text="Status:", font=('Helvetica', 14))
status_label.grid(row=5, column=1, sticky=tk.W, padx=10)
status_var = StringVar()
status_value = Label(root, textvariable=status_var, font=('Helvetica', 14))
status_value.grid(row=5, column=1, sticky=tk.E, padx=10)

def update_time_date():
    now = datetime.now()
    time_label.config(text=now.strftime("%H:%M:%S"))
    date_label.config(text=now.strftime("%A, %d %B %Y"))
    root.after(1000, update_time_date)

update_time_date()

def update_face_info(nim, name, status):
    now = datetime.now()
    name_var.set(name)
    nim_var.set(nim)
    status_var.set(status)
    csv_writer.writerow([nim, name, now.strftime("%H:%M:%S"), now.strftime("%A"), now.strftime("%Y-%m-%d"), now.strftime("%Y"), status])

def clear_face_info():
    name_var.set("")
    nim_var.set("")
    status_var.set("")

def show_frame():
    global register_face

    ret, frame = video_capture.read()
    if ret:
        small_frame = cv2.resize(frame, (0, 0), fx=0.75, fy=0.75)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        face_names = []

        detected_faces = {}
        for face_encoding in face_encodings:
            found = False
            for name, face_info in known_faces_info.items():
                stored_encoding = face_info['encoding']
                face_distances = face_recognition.face_distance([stored_encoding], face_encoding)
                if face_distances[0] < 0.5:
                    nim = face_info['nim']
                    full_name = face_info['name']
                    if full_name not in detected_faces:
                        detected_faces[full_name] = nim
                    found = True
                    break
            if not found:
                face_names.append("Unknown")
            else:
                face_names.append(full_name)

        if detected_faces:
            for full_name, nim in detected_faces.items():
                if full_name not in recorded_faces:
                    recorded_faces.add(full_name)
                    now = datetime.now()
                    status = "Hadir" if now <= attendance_deadline else "Telat"
                    update_face_info(nim, full_name, status)
        else:
            clear_face_info()

        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top = int(top / 0.75)
            right = int(right / 0.75)
            bottom = int(bottom / 0.75)
            left = int(left / 0.75)
            if name == "Unknown":
                color = (0, 0, 255)
            else:
                nim = detected_faces[name]
                color = (255, 0, 0) if name not in recorded_faces else (0, 255, 0)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 70), (right, bottom), color, cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            font_scale = 0.5
            cv2.putText(frame, nim if name != "Unknown" else "", (left + 6, bottom - 45), font, font_scale, (255, 255, 255), 1)
            cv2.putText(frame, name, (left + 6, bottom - 15), font, font_scale, (255, 255, 255), 1)

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        video_frame.imgtk = imgtk
        video_frame.configure(image=imgtk)
    
    root.after(10, show_frame)

def register_new_face_from_key(event):
    global register_face

    if event.char == 'r':
        ret, frame = video_capture.read()
        if ret:
            small_frame = cv2.resize(frame, (0, 0), fx=0.75, fy=0.75)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            if face_encodings:
                face_encoding = face_encodings[0]
                new_face_name, new_face_nim = prompt_user_input()
                if new_face_name and new_face_nim:
                    nim, name = register_new_face(new_face_name, new_face_nim, face_encoding)
                    now = datetime.now()
                    status = "Teregistrasi"
                    update_face_info(nim, name, status)

root.bind('<Key>', register_new_face_from_key)
show_frame()
root.mainloop()

# Clean up
csv_file.close()
video_capture.release()
