import argparse
import os
from pathlib import Path
from xmltools import XMLTools

xml_tool = XMLTools()
parser = argparse.ArgumentParser(
    description = 'An .xml to .ies converter'
)

subparser = parser.add_subparsers(
    help = 'subcommand help',
    required = True,
    dest = 'subcommand'
)

parser_file = subparser.add_parser(
    'file',
    help = 'file help'
)

parser_file.add_argument(
    '--output', '-o',
    required = False,
    help = 'Optional output for a single file; overwrites default file',
    type = Path
)

parser_file.add_argument(
    'xml_file',
    help = 'The xml file to convert',
    type = Path
)

parser_batch = subparser.add_parser(
    'batch',
    help = 'batch help'
)

parser_batch.add_argument(
    'directory',
    help = 'The directory containing all .xml files to be batch converted',
    type = Path
)

def verify_is_dir(dir: Path) -> bool:
    """Simple function to verify if a path is a directory or not

    Args:
        dir (Path): The directory to verify

    Returns:
        boolean: True if the directory is a valid path or not, false otherwise
    """
    return os.path.isdir(dir)

def convert_to_ies(file: Path):
    """Converts a single xml file to ies format - Creates a folder named "ies_out" in the same directory as xml2ies.py

    Args:
        file (Path): the file to convert
        dest (Path|None, optional): The destination path for the file to be placed. Defaults to None.
    """
    file_name = file.name[0: len(file.name) - 4]
    print(f'Converting {file.name} to {file_name}.ies')
    xml_tool.load_xml(file)
    location = os.path.realpath(os.path.join(os.getcwd(), "ies_out"))
    if not os.path.isdir(location):
        os.mkdir(location)
    xml_tool.create_ies(location)

def batch_convert_to_ies(directory: Path):
    """Converts all xml files within the given directory to .ies files

    Args:
        directory (Path): The directory containing the .xml files
    """
    if not verify_is_dir(directory):
        print(f'Directory not found {directory}. Please verify the correct directory was given')
        return
    
    for xml_file in directory.glob('*.xml'):
        try:
            # Next update will include a specific batch folder
            convert_to_ies(xml_file)
        except Exception as e:
            print(f"""Exception caught: {e}' Skipping {xml_file}""")

    
if __name__ == "__main__":
    args = parser.parse_args()
    print(f'The subcommand chosen: {args.subcommand}')
    if args.subcommand == 'file':
        convert_to_ies(args.xml_file)
    else:
        batch_convert_to_ies(args.directory)