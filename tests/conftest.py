import pytest
from helpers.sample_file_reader import SampleFileReader
from pathlib import Path

@pytest.fixture(scope="module")
def reader(request: pytest.FixtureRequest) -> SampleFileReader:
    """Provides a `SampleFileReader` that reads test data files from a specific directory
    within `tests/helpers/testing_data`.

    The directory is defined via a constant in the test module being used (which means that
    all tests that use this fixture within a single file must use the same directory). The
    directory is interpreted as a relative path with the base path `tests/helpers/testing_data`
    (where `tests` is actually the parent directory of this conftest.py file).

    Example: in a test file, you might have:
    
        ```
        TEST_DATA_DIR = "unit_test_data_files"

        def my_unit_test(reader: SampleFileReader):

            # read tests/helpers/testing_data/unit_test_data_files/data.json
            my_test_file_contents = reader.read("data.json")

            do_testing_with(my_test_file_contents)
        ```
    """
    base_dir = Path(__file__).parent / "helpers/testing_data" / request.module.TEST_DATA_DIR  #FIXME handle missing
    return SampleFileReader(base_dir=base_dir)
