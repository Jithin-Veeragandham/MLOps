# FastAPI Lab 1 - Titanic Survival Prediction API

## Overview

This lab demonstrates how to expose ML models as APIs using **FastAPI** and **uvicorn**. The implementation trains a Decision Tree Classifier on the Titanic dataset and serves predictions through a REST API.

## Project Structure

```
fastapi_lab1
├── model/
│   └── titanic_model.pkl
├── src/
│   ├── __init__.py
│   ├── data.py
│   ├── main.py
│   ├── predict.py
│   └── train.py
├── README.md
└── requirements.txt
```

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Lab

1. Navigate to the source folder:
   ```bash
   cd src
   ```

2. Train the model:
   ```bash
   python train.py
   ```

3. Start the API server:
   ```bash
   uvicorn main:app --reload
   ```

4. Test the API at [http://localhost:8000/docs](http://localhost:8000/docs)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/predict` | POST | Predict survival probability |

### Sample Request Body

```json
{
  "pclass": 1,
  "sex": 1,
  "age": 29.0,
  "sibsp": 0,
  "parch": 0,
  "fare": 211.34
}
```

Where `sex`: 0 = male, 1 = female

---

## Data Models

### 1. TitanicData Class

```python
class TitanicData(BaseModel):
    pclass: int
    sex: int          # 0 = male, 1 = female
    age: float
    sibsp: int
    parch: int
    fare: float
```

### 2. TitanicResponse Class

```python
class TitanicResponse(BaseModel):
    response: int
```

---

## Changes from Original Lab (Iris → Titanic)

### 1. data.py

- Changed from `load_iris()` to `fetch_openml('titanic', version=1)`
- Added preprocessing for missing values (`age`, `fare` filled with median)
- Encoded `sex` column (male=0, female=1)
- Features changed from `[sepal_length, sepal_width, petal_length, petal_width]` to `[pclass, sex, age, sibsp, parch, fare]`
- Target changed from flower species to survival status (`survived == '1'`)

### 2. main.py

- Renamed `IrisData` → `TitanicData`
- Renamed `IrisResponse` → `TitanicResponse`
- Updated Pydantic model fields to match Titanic features:
  - `pclass: int` - Passenger class (1, 2, or 3)
  - `sex: int` - Gender (0=male, 1=female)
  - `age: float` - Age in years
  - `sibsp: int` - Number of siblings/spouses aboard
  - `parch: int` - Number of parents/children aboard
  - `fare: float` - Ticket fare
- Renamed endpoint function `predict_iris()` → `predict_survival()`

### 3. train.py

- Changed model save path from `iris_model.pkl` → `titanic_model.pkl`

### 4. predict.py

- Changed model load path from `iris_model.pkl` → `titanic_model.pkl`