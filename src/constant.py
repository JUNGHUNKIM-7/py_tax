from dataclasses import dataclass
from enum import Enum, auto
import os

INTRO = """[INTRO]\n- <YOUR CARD NAME>.xls must be stored in xls folder firstly
- ALLOW LIST: hana(Hana), shin(Shinhan)\n
[EXAMPLE]
- xls folder in your directory
  + hana.xls
  + shin.xls\n
[EXPLANATION]
- Run COMMAND 1 to generate output/output.xlsx
- Run COMMAND 2 after generating output/output.xlsx\n
[RUN COMMAND]
1. Generate DATA
2. Auto Upload to HOMETAX\n
> Enter Run Command or Cancel Program with <ctrl+c>: """


class RunType(Enum):
    GEN_DATA = auto()
    AUTO_UPLOAD = auto()


class FileDir:
    DRIVER_DIR = "\\".join([os.getcwd(), r"_driver\chromedriver.exe"])
    HTMLS_DIR = "\\".join([os.getcwd(), r"src\htmls"])
    XLS_DIR = rf"{os.getcwd()}\xls"
    CSV_DIR = rf"{os.getcwd()}\src\csv"
    OUTPUT_DIR = rf"{os.getcwd()}\output"


class CardType(Enum):
    SHIN = "shin"
    HANA = "hana"


class FileType(Enum):
    XLS = auto()
    CSV = auto()


class Values:
    HANA_NULL_START = "1"
    SHIN_NULL_START = "1"
    HANA_NULL_END = "13"
    SHIN_NULL_END = "10"
    HANA_BNAME_COL = "3"
    SHIN_BNAME_COL = "5"
    HANA_BNUM_COL = "5"
    SHIN_BNUM_COL = "10"
    KEYWORD = "주유소", "통신요금"


class SelectionColumns:
    # each excel index
    def __init__(self, cardtype: CardType):
        match cardtype:
            case CardType.SHIN:
                self.date_used = "0"
                self.date_accepted = "1"
                self.business_name = Values.SHIN_BNAME_COL
                self.business_num = Values.SHIN_BNUM_COL
                self.total = "6"
                self.price = "7"
                self.vat = "8"
            case CardType.HANA:
                self.date_used = "1"
                self.date_accepted = "2"
                self.business_name = Values.HANA_BNAME_COL
                self.business_num = Values.HANA_BNUM_COL
                self.total = "10"
                self.price = "13"
                self.vat = "11"
            case _:
                raise Exception("Invalid Card Type")


@dataclass
class Outputs:
    date_used: str
    date_accepted: str
    business_num: str
    business_name: str
    price: float
    vat: float
    total: float


class OutputsPos:
    date_used = 0
    date_accepted = 1
    business_num = 2
    business_name = 3
    price = 4
    vat = 5
    total = 6
