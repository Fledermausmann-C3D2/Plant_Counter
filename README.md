# Plant Counter

**Automated Germination Detection in Barley Field Trials: A Python-Based Image Processing Tool with Stage-Dependent Calibration**

Created by Fledermausmann – from CCC

---

## Background

Germination rate analysis is a critical parameter in plant breeding and agronomic research, as it directly influences crop establishment, yield potential, and stress tolerance assessments. Traditional methods for evaluating germination in field trials rely on manual counting of seedlings, which is not only time-consuming but also prone to human error, particularly in large-scale experiments. For instance, at the Julius Kühn-Institut (JKI) in Sanitz, Germany, field trials for barley (*Hordeum vulgare*) often involve **1,000+ plots**, each measuring 0.5 m × 0.5 m and requiring individual assessment. Manual evaluation of such datasets can take **several days**, delaying data analysis and decision-making in breeding programs.

While commercial software solutions exist for plant phenotyping, they are often cost-prohibitive and may lack the flexibility to adapt to specific experimental setups, such as the 0.5 m × 0.5 m plots used in this study. Additionally, these tools frequently require specialized hardware (e.g., high-resolution cameras or hyperspectral sensors), which may not be accessible to all research institutions. Thus, there is a growing need for low-cost, open-source alternatives that can be tailored to the unique demands of field-based agronomic research — this program was developed to fill that gap.

## Challenges in Automated Plant Detection

Automated image-based plant detection has gained traction in recent years, particularly with advances in computer vision and machine learning. However, color-based segmentation — a common approach for distinguishing plants from soil — faces challenges under natural field conditions, where lighting variability, shadows, and occlusions can compromise accuracy. Studies such as those published in *Frontiers in Plant Science* (2020) have highlighted the difficulties in separating overlapping plant canopies, particularly as plants mature and leaf density increases. These challenges are exacerbated in barley field trials, where early-stage seedlings (1–2 leaves) are easier to distinguish than later-stage plants (3–4 leaves), which often exhibit leaf overlapping.

### Objectives

The primary objectives of this project were:

- To develop a low-cost, open-source tool for automated germination detection in barley field trials.
- To evaluate the tool's accuracy across different plant development stages (1–2 vs. 3–4 leaves).
- To implement a calibration method to improve reliability in later-stage plots.
- To demonstrate the tool's scalability for large-scale field trials, such as those conducted at the Institute for Breeding Research on Agricultural Crops (JKI, Sanitz).

### Research Questions

- Can a Python-based image processing tool reliably detect and count germinated barley plants in field conditions?
- How does plant development stage (1–2 vs. 3–4 leaves) affect the accuracy of automated detection?
- Can regression-based calibration improve the tool's performance for later-stage plots?

## Main Function

This program automatically counts plants in images:

1. **Frame detection** – The red frame surrounding each plot is detected first, and only the area inside this frame is analyzed.
2. **Green segmentation** – Green plant areas are segmented.
3. **Watershed separation** – Overlapping plants are separated using a watershed method.
4. **Output** – The number of detected plants per image is saved in a CSV file.

You can choose a complete folder with pictures! The results are written to a CSV file containing each image's filename and its corresponding plant count — a format that facilitates further statistical analysis, such as calculating Pearson's R² for correlation and Mean Absolute Error (MAE) to evaluate the average deviation of automated counts from manual counts.

Example

> \[!IMPORTANT\]  
> Use the Debug windows to sort out the wrong pictures from the list to manually count them.

> \[!TIP\]  
> Because the plants can have different growth situations (like 60% one leaf / 30% two leaves / 10% three leaves) in every plot, a linear regression calibration is used. You need enough manually counted pictures vs. the automatically counted pictures to do this.

## Materials and Methods

The study was conducted at the Julius Kühn-Institut (JKI) in Sanitz, Germany, within the Institute for Breeding Research on Agricultural Crops, focusing on barley (*Hordeum vulgare*) field trials. The trials consisted of over 1,000 plots, each measuring 0.5 m × 0.5 m, marked with a red frame to standardize the imaging area and facilitate automated detection. Images were captured using a standard digital camera under natural field lighting conditions, with the camera positioned perpendicular to the plots to minimize perspective distortion.

Two developmental stages of barley plants were considered for analysis:

- **Early stage (1–2 leaves per plant):** minimal leaf overlap allowed for more straightforward detection.
- **Later stage (3–4 leaves per plant):** increased leaf density and occlusion presented greater challenges for accurate segmentation.

### Implementation

The tool was implemented in **Python 3.14** using VS Codium on a Linux environment. Key libraries:


| Component      | Purpose                                                                          |
| -------------- | -------------------------------------------------------------------------------- |
| OpenCV (v4.13) | Image processing: color space conversion, contour detection, watershed algorithm |
| NumPy          | Numerical operations                                                             |
| Pandas         | Handling data output (CSV)                                                       |
| ttkbootstrap   | Graphical user interface (GUI)                                                   |


The GUI provides an intuitive platform for users to select input folders, visualize progress, and inspect intermediate results in debug mode. The tool and its source code are publicly available on GitHub, ensuring transparency and reproducibility.

### Image Processing Pipeline

The pipeline begins by loading images from a user-selected folder, including all subfolders, and sorting them using a natural sort order to maintain chronological processing. Each image is first converted from the BGR color space to HSV to facilitate color-based segmentation.

**1. Red frame detection.** The red frame surrounding each plot is detected using HSV color thresholding with two defined ranges, combined using a bitwise OR operation to create a comprehensive red mask:

```python
# -------- FRAME DETECTION --------
lower_red1 = np.array([0, 80, 100])
upper_red1 = np.array([3, 255, 255])

lower_red2 = np.array([150, 80, 100])
upper_red2 = np.array([180, 255, 255])

mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
mask_red = mask_red1 | mask_red2
```

To ensure robustness, a morphological closing operation with a **30×30 kernel** is applied to fill any gaps in the red frame mask. The largest contour in the resulting mask is identified as the frame, and the image is cropped to this region of interest (ROI) for further analysis. This step reliably isolates the ROI in **&gt;98% of images**, even under varying lighting conditions, ensuring that subsequent processing steps focus only on the relevant plot area and reducing the risk of false positives from background noise.

**2. Green plant segmentation.** Green plant areas are segmented using an HSV-based green threshold:

```python
lower_green = np.array([25, 30, 35])
upper_green = np.array([90, 255, 255])
```

The resulting green mask undergoes morphological operations to remove noise: an **opening operation with a 10×3 kernel** eliminates small artifacts, while a **closing operation** connects nearby plant regions. The threshold effectively distinguishes plant material from soil, although false negatives can occasionally occur in images with poor lighting or excessive shadows, where green pixels fall outside the defined threshold range.

**3. Watershed separation.** To separate overlapping plants, a **distance transform** is applied to identify plant cores, and a threshold of **30% of the maximum distance** is used to define the sure foreground. The **watershed algorithm** is then employed to separate touching objects, using markers derived from the connected components of the sure foreground. Each unique marker, excluding the background, is analyzed, and objects with an **area greater than 900 pixels** are counted as individual plants.

**4. Visualization &amp; debug mode.** For visualization purposes, bounding boxes are drawn around detected plants in green and filtered objects in red. In debug mode, users can visualize these intermediate results and proceed through the images step-by-step. The GUI allows users to select the image folder and output CSV path, with a progress bar and status updates displayed during the analysis.

### Calibration

To address the stage-dependent accuracy issues observed in the later-stage plots (3–4 leaves), a **linear regression-based calibration** was implemented. A subset of **30–50 images (15–25 per stage)** was manually counted to establish ground truth data. A linear regression model was then fitted to map the automated counts to the manual counts, resulting in an R² value of **0.95 for the 1–2 leaf stage** and **0.92 for the 3–4 leaf stage after calibration**. This model was applied to adjust the automated counts for all images, significantly improving the tool's reliability across varying plant densities.

## Results

The developed Python-based tool successfully automated the detection and counting of germinated plants in standardized field plots, demonstrating its efficiency, scalability, and adaptability for large-scale agronomic research. The program's performance was evaluated based on its accuracy, processing speed, and robustness across varying plant densities and imaging conditions.

### Processing Efficiency

The tool processed **1,000+ images in under 5 minutes** on a standard Linux workstation — a significant improvement compared to the days required for manual counting. This efficiency was achieved through the use of OpenCV's optimized image processing functions, such as `cv2.cvtColor`, `cv2.inRange`, and `cv2.watershed`, which are implemented in C++ and thus highly performant. The parallel processing of images in batches further reduced the overall runtime, making the tool suitable for real-time or near-real-time applications in field trials.

### Accuracy and Stage-Dependent Performance

The tool's accuracy varied with the developmental stage of the plants due to the inherent challenges of image-based detection in natural environments:

- **1–2 leaves per plant:** the program achieved a high correlation (**R² = 0.95**) between automated and manual counts, indicating reliable detection with minimal errors. This stage was identified as the **optimal imaging window**, as the low leaf density allowed for clear segmentation of individual plants.
- **3–4 leaves per plant:** greater challenges due to leaf overlap and occlusion led to reduced accuracy (**R² = 0.68–0.80**). However, the implementation of a linear regression-based calibration using 30–50 manually counted images significantly improved the accuracy (R² = 0.92 after calibration).

### Robustness of the Detection Pipeline

The tool's multi-step image processing pipeline proved effective in handling the complexities of field images. The red frame detection step (HSV color thresholding plus morphological closing) reliably isolated the region of interest in **&gt;98% of images**, even under varying lighting conditions. The green segmentation step effectively distinguished plant material from soil, with false negatives occurring only occasionally in images with poor lighting or excessive shadows.

## Technical Strengths

- **Open source &amp; cost-effective:** The reliance on widely available libraries (OpenCV, NumPy, Pandas) makes the tool accessible and cost-effective for researchers worldwide. Unlike commercial software, which often requires expensive licenses or specialized hardware, this tool can be easily deployed on standard laptops or workstations running Linux or Windows.
- **Modular &amp; adaptable:** The modular design allows for flexible adaptation to different crops, plot sizes, or imaging conditions. For example, the HSV thresholds for red frame detection and green segmentation can be readily adjusted to accommodate variations in soil color, plant species, or lighting. This adaptability was demonstrated by the tool's ability to achieve high accuracy across both early and late-stage barley plots after calibration.

## Features

- Read a folder with all pictures (.jpg, .jpeg, .png), including subfolders
- Automatic red frame detection (ROI cropping) in &gt;98% of images
- Count green plants in each picture (watershed-based separation of overlapping plants)
- Debug mode with intermediate result visualization and step-by-step processing
- Linear regression calibration for stage-dependent accuracy
- Save the counts as CSV (filename + plant count)

> \[!NOTE\]  
> This program is tested on Linux.

## Installation

```bash
git clone https://github.com/Fledermausmann-C3D2/Plant_Counter.git
cd Plant_Counter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## License &amp; Availability

The tool and its source code are publicly available on GitHub, ensuring transparency and reproducibility. This work demonstrates the potential of low-cost, open-source image processing to enhance efficiency in agronomic research, while emphasizing the need for stage-specific calibration to ensure robust automation across varying plant densities.