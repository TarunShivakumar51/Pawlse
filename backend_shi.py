from fastapi import FastAPI, UploadFile, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import green_channel_v2
from pathlib import Path
import os
import tempfile
import asyncio
import boto3
import botocore

app = FastAPI()

s3_client = boto3.client('s3')

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

@app.post("/api/presigned-url")
async def file_upload(file_name: str, content_type: str, file: UploadFile, request: Request):
    # with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
    #     shutil.copyfileobj(file.file, tmp)
    #     video_path = Path(tmp.name)

    event = asyncio.Event()
    waiter_task = asyncio.create_task(status_check(lambda: request.is_disconnected(), event)) 

    try:
        response = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': 'ear-recordings', 'Key' : file_name, 'ContentType' : content_type},
            ExpiresIn=900
        )
        
        # bpm = await asyncio.to_thread(green_channel_v2.find_green_channel, video_path, event)
        waiter_task.cancel()
        # return {"Calculated BPM": bpm}
        
        return {"URL": response}
        
    except Exception as err:
        raise HTTPException(status_code=500, detail= str(err))
    
    finally:
        try:
            s3_client.head_object(Bucket='ear-recordings', Key=content_type)
            exist = True
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                exist = False
            else:
                raise  

        if exist:
            s3_client.delete_object(Bucket='ear-recordings', Key=content_type)    