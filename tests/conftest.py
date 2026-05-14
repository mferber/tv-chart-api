import pytest
from helpers.sample_file_reader import SampleFileReader
from pathlib import Path

@pytest.fixture(scope="module")
def reader(request: pytest.FixtureRequest) -> SampleFileReader:
    base_dir = Path(__file__).parent / "helpers/testing_data" / request.module.TEST_DATA_DIR  #FIXME handle missing
    return SampleFileReader(base_dir=base_dir)
