# 🐾 PawRescue — Animal Rescue & Health Assistance

**A web-based platform designed to help people respond to animal emergencies, discover nearby animal-care facilities, and access first-aid guidance.**

PawRescue brings essential animal-care resources together in one place, helping users take informed action when an animal needs assistance.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [How It Works](#-how-it-works)
- [Installation and Setup](#-installation-and-setup)
- [Environment Variables](#-environment-variables)
- [API Endpoints](#-api-endpoints)
- [Important Notes](#-important-notes)
- [Future Improvements](#-future-improvements)

---

## 🌟 Overview

Animal emergencies can be difficult to manage when people don't know where to seek help or what immediate steps to take.

PawRescue aims to make animal-care information more accessible through three main services:

1. **Emergency Rescue:** Submit an animal emergency report with its location and condition, and search for nearby emergency veterinary facilities.
2. **Find Care:** Discover veterinary clinics and animal-welfare organizations based on location and animal-care requirements.
3. **AI First Aid:** Access first-aid guidance for animal-related situations.

The project combines a lightweight web frontend with a Python backend and external search capabilities.

---

## ✨ Key Features

### 🚨 1. Emergency Rescue

- Report an animal emergency.
- Specify the animal type and describe its condition.
- Enter geographic coordinates manually or use browser geolocation.
- Save emergency reports through the backend.
- Search for nearby emergency veterinary facilities using TinyFish.

### 🏥 2. Find Care

- Search for animal-care facilities using a location.
- Specify the animal type and care requirements.
- Retrieve information about relevant veterinary clinics and animal-welfare organizations.
- Display available facility information and source links when returned by the search service.

### 🩺 3. AI First Aid

- Access guidance for animal-related first-aid situations.
- Provide an injury or condition description.
- Display guidance through a dedicated first-aid interface.

First-aid guidance is informational and does not replace professional veterinary assessment.

### 📍 4. Location Support

- Use browser geolocation when permission is granted.
- Enter latitude and longitude manually.
- Supply location coordinates to the emergency-reporting workflow.

### 💾 5. Emergency Page State Persistence

The frontend uses browser session storage to preserve emergency form information and displayed results when navigating between pages in the same browser tab.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML5 |
| Styling | CSS3 |
| Client-side logic | JavaScript |
| Backend framework | FastAPI |
| Backend language | Python |
| Database ORM | SQLAlchemy |
| Database | PostgreSQL |
| External search integration | TinyFish |
| Configuration management | Python dotenv |
| ASGI server | Uvicorn |
| Version control | Git and GitHub |

---

## 📂 Project Structure

```text
PawRescue/
│
├── index.html                  # Homepage and main navigation
├── emergency.html              # Emergency Rescue interface
├── routine.html                # Find Care interface
├── firstaid.html               # AI First Aid interface
│
├── style.css                   # Shared website styling
├── script.js                   # Frontend interactions and API requests
│
├── .gitignore                  # Excludes secrets and unnecessary files
├── README.md                   # Project documentation
│
└── backend/
    │
    ├── main.py                 # FastAPI application entry point
    ├── config.py               # Environment-variable configuration
    ├── database.py             # Database engine and session management
    ├── models.py               # SQLAlchemy database models
    ├── schemas.py              # Pydantic request/response schemas
    ├── requirements.txt        # Python dependencies
    ├── README.md               # Backend-specific documentation
    │
    └── routes/
        ├── emergency.py        # Emergency reporting and vet search
        ├── routine.py          # Routine animal-care facility search
        └── ai_aid.py           # First-aid guidance endpoint
```

**Note:** Virtual environments, Python cache directories, and the `.env` file are excluded from version control.

---

## ⚙️ Installation and Setup

### Prerequisites

Install or configure the following:

- Python 3.10 or a compatible version
- pip
- Git
- PostgreSQL
- A TinyFish API key
- Any additional credentials required by the configured backend integrations

### 1. Clone the repository

```bash
git clone https://github.com/aadij2008-cell/PawRescue.git
```

Navigate to the project directory:

```bash
cd PawRescue
```

### 2. Set up the backend

Navigate to the backend folder:

```bash
cd backend
```

Create a Python virtual environment:

```bash
python3 -m venv venv
```

Activate it on Linux:

```bash
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file inside the `backend/` directory:

```bash
nano .env
```

Add the following placeholders and replace them with your own configuration:

```dotenv
TINYFISH_API_KEY=your_tinyfish_api_key
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=your_postgresql_connection_url
```

Do not commit this file or share its contents publicly.

The Gemini key is included because the current configuration supports it; whether it is required depends on the implemented backend functionality.

### 4. Configure PostgreSQL

Create or obtain a PostgreSQL database and configure `DATABASE_URL` with its connection string.

Ensure that the database is running and accessible before starting the backend.

The application creates its declared database tables during startup.

### 5. Start the backend

From the `backend/` directory, with the virtual environment activated, run:

```bash
uvicorn main:app --reload
```

The backend will normally be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### 6. Open the frontend

Open `index.html` in a browser or serve the project directory through a local HTTP server.

For example, from the project root:

```bash
python3 -m http.server 5500
```

Then visit:

```text
http://127.0.0.1:5500
```

**Important:** The frontend's API base URL must point to the running backend. A locally configured URL such as `http://127.0.0.1:8000` will not work for other users accessing the website from their own devices.

---

## 🔐 Environment Variables

The backend reads configuration from environment variables through `config.py`.

| Variable | Purpose |
|---|---|
| `TINYFISH_API_KEY` | Authentication for TinyFish integration |
| `GEMINI_API_KEY` | Configuration for potential Gemini integration |
| `DATABASE_URL` | PostgreSQL database connection |

Keep all credentials private. For cloud deployment, configure these variables through the hosting provider's environment-variable settings instead of uploading `.env`.

---

## 🔌 API Endpoints

The backend uses FastAPI routers to organize its functionality.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Check backend status |
| `POST` | `/api/emergency/broadcast` | Submit an emergency report |
| `GET` | `/api/emergency/search/{incident_id}` | Retrieve emergency veterinary search status and results |
| `POST` | `/api/routine/allocate` | Search for animal-care facilities |
| `POST` | `/api/ai/first-aid` | Request first-aid guidance |

For the exact request fields and response schemas, start the backend and visit `/docs`.

---

## ⚠️ Important Notes

- PawRescue is an assistance platform, not a substitute for professional veterinary care.
- Emergency report submission does not guarantee that a rescue organization has been contacted or that assistance has been dispatched.
- Search results may take time to arrive and should be independently verified.
- Confirm clinic availability and contact information directly before travelling.
- Browser geolocation requires permission and may not be available in every environment.
- The local setup uses a development server and is not, by itself, a public deployment.

---

## 🚀 Future Improvements

Potential areas for further development include:

- Live deployment of the frontend and backend.
- Reliable emergency-notification integrations with verified recipients.
- Improved emergency tracking and status updates.
- More robust location-based facility discovery.
- Better search-result verification and error handling.
- Secure user authentication and access controls.
- Improved mobile responsiveness and accessibility.
- Automated testing and deployment workflows.

---

## 👨‍💻 Repository

**GitHub:** https://github.com/aadij2008-cell/PawRescue

PawRescue is a project focused on making animal-care information and emergency assistance workflows easier to access through a simple web interface.

---

**Built with the goal of helping animals get the attention and care they need. 🐾**
