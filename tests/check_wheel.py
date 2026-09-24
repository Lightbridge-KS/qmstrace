"""Run after building: prove every shipped template and browser asset is in the wheel."""

from pathlib import Path
from zipfile import ZipFile

with ZipFile(next(Path("dist").glob("*.whl"))) as wheel:
    for asset in Path("src/qmstrace/assets").rglob("*"):
        if asset.is_file():
            name = asset.relative_to("src").as_posix()
            assert wheel.read(name) == asset.read_bytes(), name
print("Wheel carries every setup, skill and browser asset unchanged.")
