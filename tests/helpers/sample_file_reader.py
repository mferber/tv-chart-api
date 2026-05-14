from pathlib import Path


class SampleFileReader:
    """Helper class for reading sample text files for use in tests. Intended
    for use in fixtures."""

    def __init__(self, base_dir: str | None = None):
        """Creates a SampleFileReader reading files in a specific base directory.

        Args:
            base_dir: the directory to read files from, given as a relative path;
                the root path is `tests/helpers/testing_data`."""
        self.base_dir = Path(__file__).parent
        if base_dir is not None:
            self.base_dir = self.base_dir / base_dir

    def read(self, fname: str) -> str:
        """Reads and returns the content of a text file in the SampleFileReader's
        directory.

        Args:
            fname: the filename to read. May include subdirectories."""
        return (self.base_dir / fname).read_text()
