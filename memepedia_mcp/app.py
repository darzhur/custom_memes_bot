from fastapi import FastAPI
from fastapi.responses import JSONResponse
import requests
from bs4 import BeautifulSoup

app = FastAPI(title="MCP Memes Server")

BASE_URL = "https://memepedia.ru"

def fetch_latest_memes(limit: int = 10):
    resp = requests.get(BASE_URL)
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    memes = []

    # Находим все заголовки мемов
    for entry in soup.find_all("h2", class_="entry-title")[:limit]:
        a_tag = entry.find("a")
        if not a_tag:
            continue
        title = a_tag.text.strip()
        url = BASE_URL + a_tag['href']
        memes.append({
            "title": title,
            "url": url
        })

    return memes

@app.get("/memes")
async def get_memes():
    data = fetch_latest_memes(limit=10)  # возвращаем 10 последних мемов
    return JSONResponse(content=data)

@app.get("/")
async def root():
    return {"status": "MCP Memes server running"}