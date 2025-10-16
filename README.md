# MSD Risk Survey Demo

A lightweight, low-code Streamlit application that helps safety professionals and small businesses identify, assess, and control musculoskeletal disorder (MSD) risks in manual handling, pushingpulling, and repetitive tasks.

Providing an intuitive, no-database interface for the New Zealand risk assessment standards (NZMAC, NZRAPP, NZART).

---

## 🚀 Quick Start 

Follow these steps to get the application running on your local machine.

#### 1. Install Requirements
Clone or download the repository:
```bash
git clone httpsgithub.comEdnaZhang-743MSD_Survey_Tool.git
cd MSD_Survey_Tool
```
(Optional) Create a virtual environment：
```bash
python -m venv .venv
```
*   For Windows:
    ```bash
    .venv\Scripts\activate
    ```
*   For macOS/Linux:
    ```bash
    source .venv/bin/activate
    ```
Install dependencies：
```bash
pip install streamlit pandas numpy matplotlib
```

#### 2. Run the App 
```bash
streamlit run app.py
```
Then open your browser at 👉 http://localhost:8501

---

## 🧭 How to Use

#### Step 1 – Select a Tool 
Choose from NZMAC, NZRAPP, or NZART depending on your task type (lifting  pushing  repetitive motion).

#### Step 2 – Enter Task Data
Fill in

Task Name (e.g., “Manual lifting – boxes”)
Task Duration (minutes)
Frequency (per hour)
Posture Type
Load Weight (kg)
Height / Angle / Distance, depending on tool type

#### Step 3 – Calculate Risk
Click the Calculate button to view

Risk Level (Low / Medium / High)
Recommended Control Measures
Estimated Cost Saving (optional)

#### Step 4 – History & Trends
Check historical assessments, visualize risk changes over time, and export data to CSV.

---

## 💾 Data Import / Export 

Export Results download current assessments as CSV
Import Data upload a saved CSV to restore your session
Works offline — no database or server required

---

## 🧩 Tech Stack

Component	Technology
Frontend	Streamlit (Python)
Backend	pandas + numpy
Visualization	matplotlib
Storage	Local CSV files
