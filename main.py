from src.constant import *
from src.df_handler import PolarsHandler, CsvHandler


def get_run_type():
    try:
        user_input = int(input(INTRO))
        if user_input != 1 and user_input != 2:
            raise Exception("Invalid Command")
        return RunType.GEN_DATA if user_input == 1 else RunType.AUTO_UPLOAD
    except* EOFError as eof:
        raise EOFError(eof)
    except* Exception as e:
        raise Exception(e)


def runner(t: RunType):
    match t:
        case RunType.GEN_DATA:
            f = CsvHandler()
            f.gen_csv()
            d = PolarsHandler()
            d.get_output()
        case RunType.AUTO_UPLOAD:
            pass
        case _:
            raise Exception("Invalid RunType")


def main():
    runner(get_run_type())


if __name__ == "__main__":
    main()
