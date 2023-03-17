import os
import httpx
from bs4 import BeautifulSoup

from src.constant import FileDir


class Parser:
    def __init__(
        self,
    ):
        httpx._config.DEFAULT_CIPHERS += ":HIGH:!DH:!aNULL"

    def check_dir(self):
        exist_dir = os.path.isdir(FileDir.HTMLS_DIR)
        if not exist_dir:
            os.mkdir(FileDir.HTMLS_DIR)

    def parse_hana_html(self):
        target = (
            "https://www.hanacard.co.kr/OPM05000000C.web?schID=pcd&mID=OPM05000000C"
        )
        r = httpx.get(target)
        soup = BeautifulSoup(r.text, "html.parser")
        self.check_dir()
        with open(f"{FileDir.HTMLS_DIR}\\hana.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
