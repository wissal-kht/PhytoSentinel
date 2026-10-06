# 🌿 PhytoSentinel

**AI-powered plant disease detection and phytosanitary monitoring for farmers in the wilaya of Guelma (Algeria).**

A farmer uploads a photo of a leaf, a deep-learning model identifies the disease, and the app returns the diagnosis, severity, and recommended treatment. Results are stored, mapped by commune, and can be shared with the agricultural authorities (DSA) to help track outbreaks across the region.

---

## Features

- **Disease detection from a photo** — 9 crops supported, one DenseNet model per crop (apple, cherry, corn, grape, peach, pepper, potato, strawberry, tomato), with confidence score and top-3 predictions
- **Diagnosis and treatment** — description, pathogen, severity, infection indicators, and step-by-step treatment advice
- **Analysis history** — every analysis is saved with its image, location, and date; duplicate images are detected by hash
- **Sharing with the DSA** — a farmer can send an analysis to the administrator
- **Weather and risk alerts** — live weather from Open-Meteo plus an expert system that turns weather conditions into disease-risk alerts
- **Health map** — cases per commune of the wilaya of Guelma
- **Statistics and CSV export**
- **User accounts with roles** — farmer, technician, expert, admin (JWT authentication)

---

##  Tech stack

| Part | Technology |
| --- | --- |
| Backend | Python, Flask, Flask-CORS |
| AI | TensorFlow / Keras (`.h5` DenseNet models, trained on PlantVillage classes) |
| Database | SQLite |
| Auth | JWT (PyJWT), PBKDF2 password hashing |
| Frontend | HTML, CSS, vanilla JavaScript |
| Weather | [Open-Meteo](https://open-meteo.com/) (no API key needed) |

---

## 📁 Project structure

```
PhytoSentinel/
├── frontend/
│   ├── css/
│   ├── js/
│   └── pages/              # login.html, agriculteur.html, admin.html, ...
└── phytosentinel-backend/
    ├── app.py              # Flask app and API routes
    ├── database.py         # SQLite access layer
    ├── disease_information.py   # disease knowledge base (descriptions, treatments)
    ├── alert_engine.py / alerts.py
    ├── weather_service.py
    ├── requirements.txt
    ├── .env.example
    └── models/             # ⚠️ NOT in the repo — see "Download the models"
```

The SQLite database (`phytosentinel.db`) and the `uploads/` folder contain user data and are intentionally **not** versioned.

---

## Getting started

### Requirements

- Python **3.10 – 3.12** (3.10+ is required by the code, and TensorFlow does not support the newest Python versions)
- Git

### 1. Clone the repository

```powershell
git clone https://github.com/wissal-kht/PhytoSentinel.git
cd PhytoSentinel
```

### 2. Create a virtual environment and install the dependencies

```powershell
cd phytosentinel-backend
python -m venv venv
venv\Scripts\activate            # Linux / macOS: source venv/bin/activate
pip install -r requirements.txt
```

### 3. Download the models

The trained models are too large for GitHub. Download them from **[ADD YOUR LINK HERE — Google Drive / GitHub Release]** and place them in `phytosentinel-backend/models/`:

```
models/
├── apple_model.h5
├── cherry_model.h5
├── corn_model.h5
├── grape_model.h5
├── peach_model.h5
├── pepper_model.h5
├── potato_model.h5
├── strawberry_model.h5
└── tomato_model.h5
```

A missing model only disables analysis for that one crop; the rest of the app keeps working.

### 4. Configure the environment

Copy `.env.example` to `.env` and fill in your own values. The backend also reads these environment variables:

| Variable | Purpose |
| --- | --- |
| `PHYTO_SECRET_KEY` | Secret used to sign login tokens (JWT). **Set a long random value.** |
| `PHYTO_ADMIN_PASSWORD` | Password of the built-in `admin` account |

PowerShell example:

```powershell
$env:PHYTO_SECRET_KEY = "put-a-long-random-string-here"
$env:PHYTO_ADMIN_PASSWORD = "choose-a-strong-password"
```

> ⚠️ Never commit your `.env` file or real secrets.

### 5. Start the backend

```powershell
python app.py
```

The API runs on **http://localhost:5000**. Check it at http://localhost:5000/health — it lists which models were found.

### 6. Start the frontend

In a second terminal:

```powershell
cd frontend
python -m http.server 8080
```

Open **http://localhost:8080/pages/login.html** in your browser and sign in.

> Do not open the HTML files by double-clicking them (`file://...`): serve them through the local server as above.

---

## 🔌 API overview

Authenticated routes expect an `Authorization: Bearer <token>` header (the token is returned by `/api/auth/login`).

| Method | Route | Description |
| --- | --- | --- |
| POST | `/api/auth/register` | Create a farmer account |
| POST | `/api/auth/login` | Log in, returns a JWT |
| GET | `/api/auth/verify` | Check that a token is valid |
| POST | `/upload-image` | Analyze a leaf image (`image`, `plant`, `commune` form fields) |
| GET | `/api/analyses` | List analyses (farmers see only their own) |
| GET / DELETE | `/api/analyses/<id>` | Read or delete an analysis |
| POST | `/api/analyses/<id>/share` | Share an analysis with the admin |
| GET | `/api/alerts` | List alerts |
| POST | `/api/expert/weather-alerts` | Weather-based risk alerts |
| GET | `/api/statistics` | Global statistics |
| GET | `/api/carte/map-data` | Data for the health map |
| GET | `/api/export/csv` | Export analyses as CSV |
| GET / PUT | `/api/profile` | Read or update the user profile |
| GET | `/health` | Backend and model status |

Admin-only routes manage users (`/api/users`, `/api/admin/create-user`) and shared analyses (`/api/admin/analyses`).

---

## 🤖 About the models

Each model is a DenseNet classifier trained on PlantVillage classes for one crop. Images are resized to 256×256 and passed to the model as raw pixel values (0–255): the models already contain their own rescaling layer, so **do not divide by 255** when preprocessing.

---

## ⚠️ Limitations

- The models were trained on PlantVillage images (clean, single-leaf photos on a uniform background). Accuracy on real field photos can be lower, so results should be treated as decision support, not a final diagnosis. Confirm serious cases with an agronomist.
- Only the 9 crops listed above are supported.

---

## 🗺️ Roadmap

- [ ] Backend support for the farming calendar (currently stored in the browser only)
- [ ] Disease catalogue served from the database instead of the HTML page
- [ ] More crops and local field-collected training images

---

## 📄 License

This project was developed as an academic internship project. All rights reserved © 2025/2026.

## 👤 Author

-**wissal-kht** — [github.com/wissal-kht](https://github.com/wissal-kht)
-**Laritnour** _ [github.com/Laritnour](https://github.com/Laritnour)
-**douaakriba** _ [github.com/douaakriba](https://github.com/douaakriba)


