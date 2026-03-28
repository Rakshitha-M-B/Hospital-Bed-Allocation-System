# Hospital Bed Allocation System 🏥

## About the Project
This SQLite-based Hospital Bed Allocation System provides a structured database solution to streamline patient admissions and track real-time bed availability. Designed to showcase core database management skills, it features a well-defined schema and optimized queries that improve administrative efficiency and operational flow in medical centers.

## Key Features
* **Patient Management:** Track patient details, admission dates, and discharge records.
* **Bed & Ward Tracking:** Monitor real-time availability of beds across different specialized wards (e.g., ICU, General, Emergency).
* **Allocation History:** Maintain a log of past and current bed assignments for administrative review.
* **Data Integrity:** Enforce relationships between patients, doctors, and bed availability using primary and foreign keys.

## Technologies Used
* **Database:** SQLite3
* **Tools:** SQLite Command Line Interface / DB Browser for SQLite (or specify any DB viewer you used)

## Database Schema Overview
*(Note: You can update the column names below to match your exact SQL script)*

* `Patients`: Stores patient ID, name, contact info, and medical history.
* `Wards`: Stores ward ID, ward name, and total capacity.
* `Beds`: Stores bed ID, ward ID, and current occupancy status.
* `Admissions`: Links patients to specific beds, including admission and discharge timestamps.

## Getting Started

### Prerequisites
To run this project, you will need to have [SQLite](https://www.sqlite.org/download.html) installed on your machine. 

### Installation & Execution
1. Clone the repository:
   ```bash
   git clone [https://github.com/Rakshitha-M-B/Hospital-Bed-Allocation-System.git](https://github.com/Rakshitha-M-B/Hospital-Bed-Allocation-System.git)