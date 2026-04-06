````markdown
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

## Handling Articulated Motion

The core challenge was detecting an ACTIVE state when only the excavator's arm moves while the tracks remain stationary. I solved this by implementing **Region-Based Part Analysis**:

- Instead of tracking the machine as a single bounding box, the model tracks sub-components: Bucket, Boom, and Arm.  
- By calculating the relative displacement of the Bucket over time and its spatial relationship with the Boom, the system identifies "Digging" or "Swinging" based on vertical and horizontal movement thresholds, effectively capturing activity that global motion analysis would miss.  

---

## Activity Classification Logic

- **Dumping:** Identified via Intersection over Union (IoU) logic between the Bucket and DumpTruck bounding boxes.  
- **Digging:** Classified based on the vertical distance and downward trajectory of the Bucket relative to the Boom.  
- **Waiting:** Triggered when no significant component movement is detected for a specific temporal window.  

---

# 📊 Dataset & Training

- **Model:** The model was custom-trained on a curated dataset of construction site imagery.  
- **Training Data:** You can access the raw images, labels, and training logs via this [https://drive.google.com/drive/folders/159yX3il2xHawUC9rkfMsgXRsLANUY4Ek?usp=sharing](GOOGLE_DRIVE_LINK)..  
- **Zero-Shot Testing:** ⚠️ Important Note: To ensure unbiased evaluation and demonstrate the model's generalization capabilities, the video used in the demo was completely excluded from the training and validation datasets (Unseen Data).  

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
* `best.pt`: Trained YOLO weights
* `output_data.json`: Sample of the exported Kafka payload

```
```
