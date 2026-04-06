# 🏗️ Equipment Utilization & Activity Classification Prototype

This project is a real-time, microservices-based pipeline designed to monitor construction equipment (Excavators & Dump Trucks). It tracks utilization states (ACTIVE vs. INACTIVE), classifies specific work activities, and calculates overall efficiency metrics using Computer Vision and a distributed backend architecture.

---

# 🚀 Key Features

- Real-time Activity Classification: Detects Digging, Dumping, Swinging, and Waiting.  
- Utilization Analytics: Calculates Total Working Time, Idle Time, and Utilization Percentage.  
- Articulated Motion Handling: Sophisticated logic to detect activity even when the equipment's base is stationary (e.g., arm-only movement).  
- Scalable Architecture: Built with Python, Apache Kafka, PostgreSQL, and Docker.  
- Live Dashboard: Real-time visual feedback and KPI tracking via Streamlit.  

---

# 🛠️ System Architecture

The system is composed of three main microservices:

- **CV Microservice:** Processes video frames using YOLOv8/YOLOv11, performs spatial analysis, and streams JSON payloads to Kafka.  
- **Data Sink Service:** A Kafka consumer that persists activity logs into a PostgreSQL database.  
- **Analytics Dashboard:** A Streamlit frontend that visualizes the live feed and fetches historical KPIs from the database.  

---

# 🧪 Technical Decisions & Trade-offs

## ⚙️ Technical Methodology & Motion Analysis

While advanced approaches such as **LSTM + YOLO** or **Optical Flow** can capture deep temporal features, this prototype adopts a **High-Frequency Spatial-Temporal Heuristic** approach.

- By tracking sub-components (Bucket / Boom) at ~30 FPS, the system captures fine-grained motion dynamics.  
- This approach approximates the behavior of Optical Flow in detecting motion patterns, but with significantly lower computational overhead.  
- As a result, the system achieves **real-time performance**, making it suitable for **edge deployment scenarios** where compute resources are limited.  

---

## 🦾 Handling Articulated Motion

The core challenge was detecting an ACTIVE state when only the excavator's arm moves while the tracks remain stationary. This was addressed using **Region-Based Part Analysis**:

- Instead of treating the machine as a single bounding box, the system tracks key sub-components: **Bucket, Boom, and Arm**.  
- The relative displacement of the Bucket over time is analyzed along with its spatial relationship to the Boom.  
- Based on vertical and horizontal motion thresholds, the system classifies activities such as **Digging** and **Swinging**, even when the base remains static.  

This approach ensures accurate activity detection in scenarios where traditional global motion analysis would fail.

---

## 🎯 Activity Classification Logic

- **Dumping:** Detected using **Intersection over Union (IoU)** between the Bucket and Dump Truck bounding boxes.  
- **Digging:** Identified based on downward motion and vertical displacement of the Bucket relative to the Boom.  
- **Swinging/Loading:** Detected via horizontal motion patterns of the Bucket.  
- **Waiting:** Triggered when no significant movement is observed across tracked components within a temporal window.  

---

## 🔄 On Re-ID & Dwell Time

To ensure **Dwell Time persistence** and stable tracking:

- The system utilizes the **BoT-SORT tracker**, which handles temporary occlusions and short-term object disappearance.  
- This guarantees consistent ID tracking and reliable time-based analytics.  

For large-scale deployments:

- A dedicated **Re-ID Embedding Network** can be integrated.  
- This enables **cross-camera identity tracking**, making the system scalable across multiple camera views in large construction sites.  

---

# 📊 Dataset, Model & Demo

- **Model:** The model was custom-trained on a curated dataset of construction site imagery.  

- **Google Drive Resources:**  
  All project assets are available here:  
  👉 [Project Files (Model + Training Logs + Demo Video)](https://drive.google.com/drive/folders/1Y0cqDfvDfzFm7a-0Ef_HKR12G5tFUHpO?usp=sharing)

  This includes:
  - Trained model weights (`best.pt`)  
  - Full training dataset (images & labels)  
  - Training logs and outputs  
  - Demo video showcasing the system  

- **Zero-Shot Testing:** ⚠️ Important Note:  
  To ensure unbiased evaluation and demonstrate the model's generalization capabilities, the video used in the demo was completely excluded from the training and validation datasets (Unseen Data).  

---

# ⚙️ Setup & Installation

## Prerequisites

- Docker & Docker Compose  
- Python 3.10+ (for local testing)  

---

## Running the System

### 1. Spin up Infrastructure

```bash
docker-compose up -d
````

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Services

* Run the Data Sink:

```bash
python db_consumer.py
```

* Run the CV Engine:

```bash
python main.py
```

* Launch Dashboard:

```bash
streamlit run app.py
```

---

# 📁 Repository Structure

* `main.py`: The CV Inference & Kafka Producer
* `db_consumer.py`: Kafka Consumer for DB persistence
* `app.py`: Streamlit Frontend Dashboard
* `docker-compose.yml`: Infrastructure orchestration
* `output_data.json`: Sample of the exported Kafka payload
* `requirements.txt`: Dependencies