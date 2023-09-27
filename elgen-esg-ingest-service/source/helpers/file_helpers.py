from pathlib import Path
from typing import List

from source.exceptions.service_exceptions import SourceDirectoryNotFound


def get_documents_list(source_directory: str) -> List[str]:
    source_directory = Path(source_directory)

    if not source_directory.exists():
        raise SourceDirectoryNotFound(detail="source directory does not exist!")

    return [str(f) for f in source_directory.rglob("*.pdf")]
