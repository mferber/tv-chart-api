from pathlib import Path


class SampleFileReader:
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(__file__).parent
        if base_dir is not None:
            self.base_dir = self.base_dir / base_dir

    def read(self, fname: str) -> str:
        return (self.base_dir / fname).read_text()
