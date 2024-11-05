import shutil
from pathlib import Path


class HandleFiles:
    def __init__(self, folder_input: str, folder_output: str):
        self.folder_input = folder_input
        self.folder_output = folder_output

    def move_file(self, file: str) -> None:
        # Get the full path of the file to move
        file_to_move = Path(self.folder_input) / file

        # Create the output folder with the current year and month
        output_path = Path(self.folder_output)

        # Check if the folder exists
        if not output_path.is_dir():
            output_path.mkdir(parents=True, exist_ok=True)

        # Move the file to the output folder
        file_to_move.replace(Path(output_path) / file)

    def copy_file(self, file: str, new_file: str, metadata: bool = True) -> None:
        # Get the full path of the file to copy
        file_to_copy = Path(self.folder_input) / file

        # Check if the file exists
        if not file_to_copy.is_file():
            raise FileNotFoundError(f'The file {file} does not exist.')

        output_path = Path(self.folder_output)

        # Check if the folder exists
        if not output_path.is_dir():
            output_path.mkdir(parents=True, exist_ok=True)

        # Copy the file to the output folder
        destination = output_path / new_file

        if metadata:
            shutil.copy2(file_to_copy, destination)
        else:
            shutil.copy(file_to_copy, destination)
