from fastapi import FastAPI, UploadFile, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import green_channel_v2
from pathlib import Path
import os
import tempfile
import asyncio

app = FastAPI()

app.add_middleware(CORSMiddleware,
                   allow_origins = ["*"],
                   allow_methods = ["*"],
                   allow_headers = ["*"]
                )

async def status_check(check_status, event):
    while not event.is_set():
        await asyncio.sleep(0.5)
        if await check_status():
            event.set()

    return event    

@app.post("/uploadfile")
async def file_upload(file: UploadFile, request: Request):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        shutil.copyfileobj(file.file, tmp)
        video_path = Path(tmp.name)

    event = asyncio.Event()
    waiter_task = asyncio.create_task(status_check(lambda: request.is_disconnected(), event)) 

    try:
        bpm = await asyncio.to_thread(green_channel_v2.find_green_channel, video_path, event)
        waiter_task.cancel()
        return {"Calculated BPM": bpm}
    
    except Exception as err:
        raise HTTPException(status_code=500, detail= str(err))
    
    finally:
        if video_path.exists():
            os.remove(video_path)