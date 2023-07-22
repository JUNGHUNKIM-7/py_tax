import re
import xlrd as x
import csv
import polars as pl
import os
from src.constant import *


def check_dir(path: str):
    exist = os.path.isdir(path)
    if not exist:
        os.mkdir(path)


class FileDirHandler:
    def __init__(self, file_type: FileType):
        check_dir(FileDir.CSV_DIR)
        file_list = (
            os.scandir(FileDir.XLS_DIR)
            if file_type == FileType.XLS
            else os.scandir(FileDir.CSV_DIR)
        )
        self.files = [f for f in file_list]


class CsvHandler:
    def __init__(self):
        self.XLS_FILES = FileDirHandler(FileType.XLS).files

        def make_path(dir: str, f_name: str):
            return "\\".join([dir, f_name])

        for f in self.XLS_FILES:
            match f.name.split(".")[0]:
                case CardType.SHIN.value:
                    self.shin_path = make_path(FileDir.XLS_DIR, f.name)
                case CardType.HANA.value:
                    self.hana_path = make_path(FileDir.XLS_DIR, f.name)

    def gen_csv(self):
        for f in [self.hana_path, self.shin_path]:
            wb: x.Book = x.open_workbook(f)
            sh = wb.sheet_by_index(0)
            f_name = f.split("\\")[-1].split(".")[0]
            temp = f_name

            with open(
                f"{FileDir.CSV_DIR}\\{f_name}.csv", "w", newline="", encoding="utf-8"
            ) as f:
                wr = csv.writer(f, delimiter=",", quoting=csv.QUOTE_ALL)
                for rx in range(sh.nrows):
                    wr.writerow(sh.row_values(rx))
            print(f"DONE: {temp}.csv Generated")


class PolarsHandler:
    def __init__(self):
        self.CSV_FILES = FileDirHandler(FileType.CSV).files
        self.dfs: list[pl.DataFrame] = []
        self.hana_df = None
        self.shin_df = None

        def read_csv_files(f_name: str):
            return pl.read_csv(
                f"{FileDir.CSV_DIR}\\{f_name}", encoding="utf-8", null_values="-"
            )

        for f in self.CSV_FILES:
            file_name = f.name.split(".")[0]
            match file_name:
                case CardType.HANA.value:
                    assert file_name == "hana"
                    self.hana_df = read_csv_files(f.name)
                    assert (
                        self.hana_df.width == 14
                    ), f"curr: {self.hana_df.width} / expected: {Values.HANA_NULL_END}"
                    self.dfs.append(self.hana_df)

                case CardType.SHIN.value:
                    assert file_name == "shin"
                    self.shin_df = read_csv_files(f.name)
                    assert (
                        self.shin_df.width == 11
                    ), f"curr: {self.shin_df.width} / expected: {Values.SHIN_NULL_END}"
                    self.dfs.append(self.shin_df)

    def implFilter(self):
        if len(self.dfs) < 1 or self.hana_df == None or self.shin_df == None:
            print("files are not generated")
            return

        for df in self.dfs:
            df.columns = [str(i) for i in range(df.width)]

        def filter_df(df: pl.DataFrame, start: str, end: str):
            return df.filter((pl.col(start) != "") & (pl.col(end) != "")).slice(1)

        return filter_df(
            df=self.hana_df,
            start=Values.HANA_NULL_START,
            end=Values.HANA_NULL_END,
        ), filter_df(
            df=self.shin_df,
            start=Values.SHIN_NULL_START,
            end=Values.SHIN_NULL_END,
        )

    def get_output(self):
        hana_filtered, shin_filtered = self.implFilter()

        # generate cols for df[arg]
        hana_cols = SelectionColumns(CardType.HANA)
        shin_cols = SelectionColumns(CardType.SHIN)

        def convert_price_to_float(df: pl.DataFrame, cols: SelectionColumns):
            return df.with_columns(
                [
                    pl.col(v).cast(pl.Float64).alias(v)
                    for v in [cols.price, cols.vat, cols.total]
                ]
            )

        hana_filtered = convert_price_to_float(hana_filtered, hana_cols)
        shin_filtered = convert_price_to_float(shin_filtered, shin_cols)

        # set filter condition, then add to column as True/False, then get filter
        def filter_include_or_exclude(df: pl.DataFrame, filter=False):
            match filter:
                case True:
                    return df.filter(pl.col("result") == True)
                case _:
                    return df.filter(pl.col("result") == False)

        def add_result_col(df: pl.DataFrame, business_name_col: str):
            query = "|".join(
                map(re.escape, sorted(Values.KEYWORD, key=len, reverse=True))
            )
            return df.with_columns(
                pl.col(business_name_col).str.contains(query).alias("result")
            )

        hana_include = filter_include_or_exclude(
            add_result_col(hana_filtered, Values.HANA_BNAME_COL), True
        )
        shin_include = filter_include_or_exclude(
            add_result_col(shin_filtered, Values.SHIN_BNAME_COL), True
        )
        hana_exclude = filter_include_or_exclude(
            add_result_col(hana_filtered, Values.HANA_BNAME_COL)
        )
        shin_exclude = filter_include_or_exclude(
            add_result_col(shin_filtered, Values.SHIN_BNAME_COL)
        )

        assert hana_filtered.height == hana_include.height + hana_exclude.height
        assert shin_filtered.height == shin_include.height + shin_exclude.height

        # select columns by col_name
        def col_selection(df: pl.DataFrame, selections: list[pl.Expr]):
            return df.select(selections)

        def get_cols(cols: SelectionColumns):
            return [
                pl.col(v)
                for v in [
                    cols.date_used,
                    cols.date_accepted,
                    cols.business_num,
                    cols.business_name,
                    cols.price,
                    cols.vat,
                    cols.total,
                    "result",
                ]
            ]

        hana_include = col_selection(hana_include, get_cols(hana_cols))
        hana_exclude = col_selection(hana_exclude, get_cols(hana_cols))
        shin_include = col_selection(shin_include, get_cols(shin_cols))
        shin_exclude = col_selection(shin_exclude, get_cols(shin_cols))

        assert hana_include.width == shin_include.width
        assert hana_exclude.width == shin_exclude.width

        for df in [hana_include, hana_exclude, shin_include, shin_exclude]:
            df.columns = [str(i) for i in range(hana_include.width)]

        # stacking include / exclude
        export_include = hana_include.vstack(shin_include)
        export_exclude = hana_exclude.vstack(shin_exclude)
        assert (
            hana_filtered.height + shin_filtered.height
            == export_exclude.height + export_include.height
        )

        # stacking into 1 df
        fianl_df = export_include.vstack(export_exclude)
        assert fianl_df.height == hana_filtered.height + shin_filtered.height

        # save to xlsx
        self.save_as_xlsx(fianl_df)
        print("DONE: output.xlsx Generated")

    def save_as_xlsx(self, df: pl.DataFrame):
        check_dir(FileDir.OUTPUT_DIR)
        pand_df = df.to_pandas()
        pand_df.to_excel(
            "\\".join([FileDir.OUTPUT_DIR, "output.xlsx"]), header=False, index=False
        )

    # extract business nums as [[B_nums -> len(100)], [..], [..]]
    def extract_business_no(self):
        hana_filtered, shin_filtered = self.implFilter()

        hana: list[str] = list(
            map(
                lambda x: x.replace("-", ""),
                hana_filtered.select(Values.HANA_BNUM_COL).to_series().to_list(),
            )
        )
        shin: list[str] = list(
            map(
                lambda x: x.replace("-", ""),
                shin_filtered.select(Values.SHIN_BNUM_COL).to_series().to_list(),
            )
        )

        hana_temp: list[list[str]] | list[str] = []
        shin_temp: list[list[str]] | list[str] = []

        def divide(li, temp):
            if len(li) <= 100:
                temp.append(li)
                return
            else:
                first = li[:100]
                temp.append(first)
                rest = li[100:]
                divide(rest, temp)

        divide(hana, hana_temp)
        divide(shin, shin_temp)

        def equal_len(li: list[list[str]], other: list[str]):
            sum = 0
            for elems in li:
                sum += len(elems)
            return len(other) == sum

        assert equal_len(hana_temp, hana), f"status: {equal_len(hana_temp, hana)}"
        assert equal_len(shin_temp, shin), f"status: {equal_len(shin_temp, shin)}"

        return hana_temp, shin_temp
