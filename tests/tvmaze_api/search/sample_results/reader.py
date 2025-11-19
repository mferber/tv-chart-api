from pathlib import Path


def read_sample(fname: str) -> str:
    return (Path(__file__).parent / fname).read_text()
