from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
import polars as pl

from src.constant import FileDir, OutputsPos, Outputs


class SeleniumHandler:
    def __init__(self):
        self.options = Options()
        self.options.page_load_strategy = "eager"
        self.driver: Optional[WebDriver] = None
        self.rows: Optional[list[Outputs]] = None

    def check_driver(self):
        self.driver = webdriver.Chrome(
            executable_path=FileDir.DRIVER_DIR, options=self.options
        )
        browser_version = self.driver.capabilities["browserVersion"]
        webdriver_version = self.driver.capabilities["chrome"][
            "chromedriverVersion"
        ].split(" ")[0]
        try:
            if browser_version[:2] != webdriver_version[:2]:
                raise Exception(
                    f"Verions are not Matched -> Browser: {browser_version[:2]} != Your WebDriver Version: {webdriver_version[:2]}"
                )
        except Exception as e:
            self.driver.quit()
            raise Exception(e)

    def get_filtered_rows(self):
        df = pd.read_excel("\\".join([FileDir.OUTPUT_DIR, "output.xlsx"]))
        df.columns = [str(i) for i in range(len(df.columns))]

        df = pl.from_pandas(df)
        df = df.filter(pl.col(f"{df.width - 1}") == True)
        df = df.drop(f"{df.width - 1}")

        self.rows = [
            Outputs(
                date_used=r[OutputsPos.date_used],
                date_accepted=r[OutputsPos.date_accepted],
                business_num=r[OutputsPos.business_num],
                business_name=r[OutputsPos.business_name],
                price=r[OutputsPos.price],
                vat=r[OutputsPos.vat],
                total=r[OutputsPos.total],
            )
            for r in df.rows()
        ]

    def run_hometax(self):
        # if self.driver == None:
        #     raise Exception("chrome driver is not exist")
        # elif self.rows == None:
        #     raise Exception("rows data are not initialzed")
        # else:

        if self.rows != None:
            for r in self.rows:
                self.run_hometax_helper(r)

    def run_hometax_helper(self, r: Outputs):
        print(r)
