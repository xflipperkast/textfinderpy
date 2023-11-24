import pygetwindow as gw
import pyautogui
from PIL import ImageGrab, ImageTk
import tkinter as tk
from tkinter import Listbox, Frame, Button, END, Toplevel, Label
import threading
import time
import pytesseract
import re
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Global lists for completed and queue
completed = []
queue = []

def capture_continuous(area, label, update_queue):
    last_update_time = time.time()
    while True:
        screenshot = ImageGrab.grab(bbox=area)
        img = ImageTk.PhotoImage(image=screenshot)
        label.config(image=img)
        label.image = img

        current_time = time.time()
        if current_time - last_update_time >= 0.1:  # Update every 0.1 second
            # Apply OCR to the screenshot
            text = pytesseract.image_to_string(screenshot)
            # Process the text to find usernames
            process_text_for_usernames(text, update_queue)
            last_update_time = current_time

        time.sleep(0.01)  # Small sleep to prevent high CPU usag

def process_text_for_usernames(text, update_queue):
    # Using regular expression to match different username formats
    pattern = re.compile(r'user:\s*(\w+)', re.IGNORECASE)
    for line in text.split('\n'):
        match = pattern.search(line)
        if match:
            username = match.group(1).lower()  # Convert username to lowercase
            if username and username not in [name.lower() for name in completed]:
                add_to_queue(username, update_queue)

def add_to_queue(name, update_queue):
    name = name.lower()  # Convert username to lowercase
    if name not in completed and name not in queue:
        queue.append(name)
        update_queue.set()  # Signal that the queue has been updated

def add_to_completed(name, listbox_queue, listbox_completed, update_queue):
    name = name.lower()  # Convert username to lowercase
    if name not in completed:
        completed.append(name)
        if name in queue:
            queue.remove(name)
        update_queue.set()  # Signal that the completed list has been updated
        update_gui_listboxes(listbox_queue, listbox_completed)

def update_gui_listboxes(listbox_queue, listbox_completed):
    listbox_queue.delete(0, tk.END)
    listbox_completed.delete(0, tk.END)
    for item in queue:
        listbox_queue.insert(tk.END, item)
    for item in completed:
        listbox_completed.insert(tk.END, item)

def select_area(window, listbox_queue, listbox_completed, update_queue):
    root = tk.Toplevel(window)
    root.attributes("-fullscreen", True)
    canvas = tk.Canvas(root, cursor="cross")
    canvas.pack(fill=tk.BOTH, expand=True)

    rect = None
    start_x = None
    start_y = None

    def on_click(event):
        nonlocal start_x, start_y, rect
        start_x = root.winfo_pointerx()
        start_y = root.winfo_pointery()
        rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline='red')

    def on_drag(event):
        nonlocal rect, start_x, start_y
        end_x = root.winfo_pointerx()
        end_y = root.winfo_pointery()
        canvas.coords(rect, start_x, start_y, end_x, end_y)

    def on_release(event):
        nonlocal start_x, start_y
        end_x = root.winfo_pointerx()
        end_y = root.winfo_pointery()
        root.destroy()
        screenshot_window = Toplevel(window)
        screenshot_label = Label(screenshot_window)
        screenshot_label.pack()
        threading.Thread(target=capture_continuous, args=((start_x, start_y, end_x, end_y), screenshot_label, update_queue), daemon=True).start()

    canvas.bind("<ButtonPress-1>", on_click)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

    root.mainloop()

def gui():
    window = tk.Tk()
    window.title("List Manager")

    update_queue = threading.Event()  # Event to signal updates to the queue

    frame_queue = Frame(window)
    frame_completed = Frame(window)
    frame_buttons = Frame(window)

    label_queue = Label(frame_queue, text="Queue")
    label_completed = Label(frame_completed, text="Completed")
    label_queue.pack()
    label_completed.pack()

    listbox_queue = Listbox(frame_queue)
    listbox_completed = Listbox(frame_completed)
    listbox_queue.pack()
    listbox_completed.pack()

    def move_to_completed():
        selected = listbox_queue.curselection()
        if selected:
            name = listbox_queue.get(selected)
            add_to_completed(name, listbox_queue, listbox_completed, update_queue)

    btn_move = Button(frame_buttons, text="Move to Completed", command=move_to_completed)
    btn_screenshot = Button(frame_buttons, text="Select Area", command=lambda: select_area(window, listbox_queue, listbox_completed, update_queue))

    btn_move.pack()
    btn_screenshot.pack()

    frame_queue.pack(side=tk.LEFT)
    frame_completed.pack(side=tk.RIGHT)
    frame_buttons.pack(side=tk.BOTTOM)

    def check_for_updates():
        if update_queue.is_set():
            update_gui_listboxes(listbox_queue, listbox_completed)
            update_queue.clear()
        window.after(100, check_for_updates)

    check_for_updates()  # Start checking for updates

    window.mainloop()

gui()
