# VIKAS — Vision-based Identification and Knowledge Analysis for Solar Panels

### **AI-powered Solar Panel Detection & Area Scanning System**

VIKAS is a Flask-based web application that detects **solar panels from satellite imagery** using a deep-learning model.
Users can input coordinates manually, click on the map, upload CSV files, scan a surrounding area, and view prediction history.

---

## Features

### **Solar Panel Detection**

* Predicts solar panel presence at a given **latitude & longitude**
* Shows prediction label, confidence score, and satellite image preview
* Saves predictions to CSV automatically

### **Interactive Map**

* Click on map to select coordinates
* Google Satellite view
* Search by address
* Markers for selected coordinates

### **Bulk Upload**

* Upload CSV files containing coordinates
* Smart validation (lat/lon, duplicates, invalid rows)

### **Area Scan Mode**

* Scans a **5×5 grid** around input coordinate
* Generates:

  * Number of tiles containing solar panels
  * Percentage coverage
  * Average confidence
  * Confidence range

### **Prediction History**

* View all saved predictions
* Clear CSV file
* Download CSV

### **Machine Learning**

* PyTorch model (`model_final.pth`)
* Preprocessing with torchvision transforms
* CPU-friendly prediction pipeline

### **Logging**

* Rotating logs
* Logs request + response status
* Stored in `logs/app.log`

---

## 📦 Project Structure

```
flask_app/
│── app/
│   ├── controllers/
│   ├── routes/
│   ├── services/
│   ├── templates/
│   ├── static/
│   ├── utils/
│   └── data/
│       └── .gitkeep        # Keeps folder but ignores CSV files
│
├── models/
│   └── model_final.pth     # Ignored in git
│
├── ml/
│   └── loader.py
│
├── logs/
│   └── app.log             # Ignored in git
│
├── config.py
├── run.py
├── requirements.txt
└── README.md
```

---

## 🛠️ Setup Instructions

### **1️. Clone the repository**

```bash
git clone <your-repo-url>
cd flask_app
```

### **2️. Create virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
```

### **3️. Install dependencies**

> CPU-only PyTorch installation is already handled separately.

```bash
pip install -r requirements.txt
```

### **4️. Install PyTorch (CPU version)**

```bash
pip install torch==2.2.0 torchvision==0.17.0 \
    --index-url https://download.pytorch.org/whl/cpu
```

### **5️. Run the application**

```bash
python run.py
```

App runs at:

```
http://127.0.0.1:5000
```

---

## Testing

### Predict Single Coordinate

* Enter latitude & longitude
* Click **Predict**

### Scan a 5×5 Grid

* Click **Scan** on any coordinate card

### Bulk Upload

* Upload CSV containing:

```
latitude, longitude
34.13747, 77.571188
```

Column names can be:

* `latitude`, `lat`, `Latitude`, `Lat`, etc.

---

## Logging

Logs stored at:

```
logs/app.log
```

Each request is logged automatically:

```
REQUEST: POST /predict | IP=127.0.0.1 | ARGS={} | FORM={'lat': '34.1'}
RESPONSE: 200 OK for POST /predict
```

---

## .gitignore Notes

Included in repo:

* `app/data/.gitkeep`

Ignored:

* model files
* prediction history CSV
* logs
* venv
* **pycache**

---

## Future Enhancements

* GPU inference option
* User authentication
* Heatmap visualization
* Export scan results as PDF

---

## ⭐ Contribute

Pull requests are welcome! For major changes, open an issue first to discuss your ideas.

---