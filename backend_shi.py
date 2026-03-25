from fastapi import FastAPI, UploadFile
import shutil
import main

app = FastAPI() 

@app.post("/uploadfile/")
async def file_upload(file: UploadFile):
    with open(f"./{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

@app.get("/bpm")
async def get_bpm():
    return {"bpm" : main.bpm}