# Sales Analytics Dashboard

## Overview

Sales Analytics Dashboard is a Python web application that uses Flask for its REST API, Streamlit for its dashboard, and SQLite for permanent data storage.

Users can upload, view, add, update, delete, filter, and download sales records. The app also calculates sales metrics and displays a revenue chart.

## Features

- Flask REST API
- Streamlit dashboard
- SQLite database
- Create, read, update, and delete operations
- CSV upload and download
- Product filtering and revenue chart
- Application logging
- Memory profiling with `tracemalloc`
- Concurrent analytics with `ThreadPoolExecutor`

## Structure

```text
AnalyticsApp/
|-- app.py
|-- dashboard.py
|-- logger_config.py
|-- requirements.txt
|-- README.md
|-- sales.csv
|-- sales.db
`-- logs/
    `-- application.log
```

## Installation

Open the project folder in VS Code and run:

```powershell
python -m pip install -r requirements.txt
```

## Running the App

Start Flask in the first terminal:

```powershell
python app.py
```

Start Streamlit in a second terminal:

```powershell
python -m streamlit run dashboard.py
```

Open the dashboard at `http://localhost:8501`.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Check the API |
| GET | `/sales` | Get all sales |
| GET | `/sales/<id>` | Get one sale |
| POST | `/sales` | Add a sale |
| PUT | `/sales/<id>` | Update a sale |
| DELETE | `/sales/<id>` | Delete a sale |
| GET | `/analytics` | Get metrics and memory usage |
| POST | `/upload` | Import a CSV file |

## CSV Format

The CSV must contain:

```csv
product,price,quantity
Keyboard,50,2
Mouse,25,3
```

Revenue is calculated as `price x quantity`.

## Advanced Features

- Logs are written to `logs/application.log`.
- `tracemalloc` measures current and peak memory during analytics.
- `ThreadPoolExecutor` runs three analytics queries concurrently.
- SQLite stores records in `sales.db`.

## Deployment

Flask can run with:

```text
gunicorn app:app
```

When deploying Streamlit, change `API_URL` in `dashboard.py` from the local address to the public Flask URL.

## Quick Test

1. Confirm `/sales` and `/analytics` work.
2. Add, update, and delete a sale.
3. Upload and download a CSV.
4. Test the product filter and chart.
5. Check `logs/application.log`.
