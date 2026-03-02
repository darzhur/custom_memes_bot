from mcp.server.fastmcp import FastMCP
import requests
from bs4 import BeautifulSoup

mcp = FastMCP("memepedia")

@mcp.tool()
def get_latest_memes() -> list[str]:
    """
    Возвращает список названий мемов с главной страницы Memepedia.
    """
    url = "https://memepedia.ru/"
    resp = requests.get(url, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")

    titles = []
    for link in soup.select("h2.entry-title a"):
        titles.append(link.text.strip())

    return titles[:20]  # ограничим до 20

if __name__ == "__main__":
    mcp.run()