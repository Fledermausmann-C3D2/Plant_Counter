import os
import cv2
import numpy as np
import csv
import threading
import ttkbootstrap as ttk
from tkinter import filedialog
import re

# ---------------- Functions ----------------

# Sorting images
def natural_key(text):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]

# Choose folder
def choose_folder():
    folder = filedialog.askdirectory()
    folder_var.set(folder)

# Choose CSV save location
def choose_output():

    file = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV file","*.csv")],
        title="Save CSV as"
    )

    output_var.set(file)

def start_analysis():
    thread = threading.Thread(target=run_analysis)
    thread.start()

def run_analysis():

    # Folder selection including all subfolders
    image_folder = folder_var.get()

    if not image_folder:
        status_var.set("Please select an image folder first")
        return

    # Determine CSV path
    output_csv = output_var.get()

    # Auto-create CSV if none selected
    if not output_csv:
        output_csv = os.path.join(image_folder,"plant_counts.csv")

    results = []

    # Create image list for progress display
    image_paths = []

    for root_dir, dirs, files in os.walk(image_folder):
        for file in files:

            if file.lower().endswith((".jpg",".jpeg",".png")):
                image_paths.append(os.path.join(root_dir,file))

    image_paths.sort(key=natural_key)

    total_images = len(image_paths)

    progress["maximum"] = total_images

    for i, path in enumerate(image_paths):

        file = os.path.basename(path)

        img = cv2.imread(path)

        # Convert to HSV (better separation)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# ---------------------------
        # Detect frame (count only inside)
        # Mask red frame
        lower_red1 = np.array([0, 120, 70])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 120, 70])
        upper_red2 = np.array([180, 255, 255])

        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = mask_red1 | mask_red2

        # Find contours
        contours, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            # Select largest contour (frame)
            c = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c)

            # Crop image and mask to ROI
            img = img[y:y+h, x:x+w]
            hsv = hsv[y:y+h, x:x+w]

        # Green segmentation - color range
        # small range (35/85)(25/90)
        lower_green = np.array([25,40,40])
        upper_green = np.array([90,255,255])

        mask = cv2.inRange(hsv, lower_green, upper_green)

        # Morphological filters (noise removal)
        # small plants (3/3), larger e.g. (7/7)
        kernel = np.ones((10,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Define background / separate
        # iterations 1-4 define how much plant area is expanded
        sure_bg = cv2.dilate(mask, kernel, iterations=3)

        # Distance transform (find plant core) 
        # center vs plant edges
        dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)

        _, sure_fg = cv2.threshold(dist, 0.3*dist.max(), 255, 0)

        sure_fg = np.uint8(sure_fg)

        unknown = cv2.subtract(sure_bg, sure_fg)

        # Create markers + ID for each plant
        num_labels, markers = cv2.connectedComponents(sure_fg)

        markers = markers + 1

        markers[unknown==255] = 0

        # Watershed (separate overlapping objects)
        markers = cv2.watershed(img, markers)

        plant_count = 0

        # Counting
        for label in np.unique(markers):

            if label <= 1:
                continue
            
            # Skip background
            mask_label = np.uint8(markers == label)

            area = cv2.countNonZero(mask_label)

            # Remove small objects
            # small plant up to 50, larger e.g. 400
            if area > 150:
                plant_count += 1

        print(file, plant_count)

        results.append([file, plant_count])

        progress["value"] = i + 1
        status_var.set(f"Processing image {i+1} / {total_images}")
        root.update_idletasks()

    # Save CSV
    with open(output_csv,"w",newline="") as f:

        writer = csv.writer(f)

        writer.writerow(["image","plants"])

        writer.writerows(results)

    status_var.set(f"Analysis complete. CSV saved at:\n{output_csv}")

# ---------------- GUI ----------------

root = ttk.Window(themename="solar")

root.title("Plant Counter")
root.geometry("900x1200")

folder_var = ttk.StringVar()
output_var = ttk.StringVar()
status_var = ttk.StringVar()

# Description text
description = """
This program automatically counts plants in images.
First, the red frame is detected and only the area
inside this frame is analyzed. 

Then, green plant areas are segmented and separated using a 
watershed method.
You can choose a complete Folder with pictures!
The number of detected plants is saved in a CSV file.

Created by Fledermausmann - CCC
"""

ttk.Label(root,text="Plant Counter",font=("Arial",14,"bold")).pack(pady=5)

ttk.Label(root,text=description,justify="left",wraplength=460).pack(pady=5)

ttk.Label(root,text="Select image folder").pack(pady=5)

ttk.Entry(root,textvariable=folder_var,width=60).pack()

ttk.Button(root,text="Choose folder",command=choose_folder).pack(pady=5)

ttk.Label(root,text="CSV save location (optional)").pack(pady=5)

ttk.Entry(root,textvariable=output_var,width=60).pack()

ttk.Button(root,text="Choose CSV",command=choose_output).pack(pady=5)

ttk.Button(root,text="Start analysis",command=start_analysis).pack(pady=10)

progress = ttk.Progressbar(root,length=400)
progress.pack(pady=5)

ttk.Label(root,textvariable=status_var).pack()

root.mainloop()