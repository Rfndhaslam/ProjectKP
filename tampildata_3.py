import tkinter as tk
from tkinter import ttk
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db
import schedule
import time
import threading

cred = credentials.Certificate("D:/vscode/KAPE2/sistempresensidit-firebase-adminsdk-okqli-e67a29dc70.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://sistempresensidit-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

def fetch_attendance_data():
    ref = db.reference('data_presensi')
    data = ref.get()
    return data

def update_table():
    for row in tree.get_children():
        tree.delete(row)
    
    data = fetch_attendance_data()
    if data:
        for date, times in data.items():
            for time, info in times.items():
                nip = info.get('nip', '')
                nama = info.get('nama', '')
                day = info.get('day', '')
                year = info.get('year', '')
                status = info.get('status', '')
                tree.insert('', 'end', values=(nip, nama, time, day, date, year, status))

def listener(event):
    root.after(0, update_table)

def reset_attendance_data():
    ref = db.reference('data_presensi')
    ref.set({})  # Clear all data
    print("Data presensi telah di reset.")

def check_reset():
    now = datetime.now()
    if now.day == 1:
        reset_attendance_data()

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

root = tk.Tk()
root.title("Data Presensi Face Recognition DIT - KAPETK")

columns = ("NIP", "Nama", "Waktu", "Hari", "Tanggal", "Tahun", "Status")
tree = ttk.Treeview(root, columns=columns, show='headings')
tree.heading("NIP", text="NIP")
tree.heading("Nama", text="Nama")
tree.heading("Waktu", text="Waktu")
tree.heading("Hari", text="Hari")
tree.heading("Tanggal", text="Tanggal")
tree.heading("Tahun", text="Tahun")
tree.heading("Status", text="Status")

tree.column("NIP", width=100)
tree.column("Nama", width=150)
tree.column("Waktu", width=100)
tree.column("Hari", width=100)
tree.column("Tanggal", width=100)
tree.column("Tahun", width=100)
tree.column("Status", width=100)

tree.pack(expand=True, fill='both')

attendance_ref = db.reference('data_presensi')
attendance_ref.listen(listener)

schedule.every().day.at("00:00").do(check_reset)

schedule_thread = threading.Thread(target=run_schedule)
schedule_thread.daemon = True
schedule_thread.start()

root.mainloop()
