from fastapi import FastAPI, status, HTTPException
from pydantic import BaseModel
from predict import predict_data

app = FastAPI()

class TitanicData(BaseModel):
    pclass: int
    sex: int# 0 for male and 1 for female
    age: float
    sibsp: int
    parch: int
    fare: float

class TitanicResponse(BaseModel):
    response:int

@app.get("/", status_code=status.HTTP_200_OK)
async def health_ping():
    return {"status": "healthy"}

@app.post("/predict", response_model=TitanicResponse)
async def predict_survival(passenger: TitanicData):
    try:
        features = [[
            passenger.pclass,
            passenger.sex,
            passenger.age,
            passenger.sibsp,
            passenger.parch,
            passenger.fare
        ]]
        prediction = predict_data(features)
        return TitanicResponse(response=int(prediction[0]))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
