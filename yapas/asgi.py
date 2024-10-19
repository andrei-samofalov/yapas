from fastapi import FastAPI
import signal

app = FastAPI()


@app.get('/hello')
async def hello_world():
    return {'message': 'Hello World!'}


@app.get('/restart')
async def restart():
    signal.raise_signal(signal.SIGHUP)
    return 'Restarting...'
