#!/usr/bin/env python
import argparse
import os
import struct
import re
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
from xml.dom.minidom import parseString
from tqdm import tqdm

parser = argparse.ArgumentParser(
    description = 'An .ies file to xml converter'
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
    help = 'An optional file to output to; overrides default file name',
    type = Path
    )
parser_file.add_argument(
    'ies_file',
    help = 'The .ies file to convert',
    type = Path
    )

parser_batch = subparser.add_parser(
    'batch',
    help = 'batch help'
    )
parser_batch.add_argument(
    'directory',
    help = 'The directory with .ies files to batch convert',
    type = Path
    )

NULL_BYTE = '\x00'
SEPARATOR = '\t'
LINE = '\n'

def convert_bytestring(bstr: bytes):
    """Converts a bytestring to a readable string.

    Args:
        bstr (bytes): the bytestring to decode

    Returns:
        str: the appropriate string

    """
    return bytes(
        [(int(b) ^ 0x1) for b in bstr if int(b) != 0]
        ).decode(encoding='utf-8', errors='replace').rstrip(NULL_BYTE)
    


def get_int_from_bytes(bstr: bytes):
    """Get `int` from `bytes`. Obviously
    Uses little endian to convert.

    Args:
        bstr (bytes): the bytestring chunk to convert

    Returns:
        int: the number converted

    """
    return int.from_bytes(bstr, byteorder = 'little')

# This was added by Aren
def clean_column_names(name: str) -> str:
    """Cleans the column names if any non-alphabetical characters are included

    Args:
        name (str): the string to clean

    Returns:
        str: a clean string which only includes column names in english
    """
    # matching any non-korean values that get included 
    match = re.match(r'^[A-Za-z0-9_]+', name)
    return match.group(0) if match else name.strip()
    
    
def get_col_names(
    file: Path, bstr: bytes, ncols: int, offset: int, ncols_int: int
    ):
    """Gets column names from the bytestring of an `.ies` file.

    Args:
        file (Path): the file itself
        bstr (bytes): the bytestring
        ncols (int): number of columns
        offset (int): offset to start from the bytestring
        ncols_int (int): offset to specific columns

    Returns:
        dict: with key = index and value = column name

    Raises:
        Exception: if the `.ies` file is corrupt or invalid

    """
    col_names = {}
    for _ in range(ncols):
        #bstr_str = bstr[offset:offset+64]
        col_name = convert_bytestring(bstr[offset:offset+64])
       
        # col_name = clean_column_names(col_name)
        #print(f'The byte string = {bstr_str}\nThe total Size = {len(bstr_str)}\nCol name = {col_name}')
        
        # `n2` is unnecessary in this port.
        # Just add 128; 64 for 64 bytes + 64 for `n2`.
        offset += 128
        col_type = get_int_from_bytes(bstr[offset:offset+2])
        # `dummy` is unnecessary in this port.
        # Just add 6; 2 for short + 4 for `dummy`.
        offset += 6
        col_idx = get_int_from_bytes(bstr[offset:offset+2])
        offset += 2
        if col_type == 0:
            try:
                if col_names[col_idx]:
                    raise Exception(
                        f'IES file {file} is invalid: '
                        f'{col_names[col_idx]} is not null'
                        )
            except KeyError:
                col_names[col_idx] = col_name
        else:
            try:
                if col_names[col_idx + ncols_int]:
                    raise Exception(
                        f'IES file {file} is invalid: '
                        f'{col_names[col_idx+ncols_int]} is not null'
                        )
            except KeyError:
                col_names[col_idx + ncols_int] = col_name
    
    return col_names


def get_rows(
    file: Path, bstr: bytes, tsv: list, nrows: int, offset: int,
    ncols_int: int, ncols_str: int
    ):
    """Gets rows from the bytestring of an `.ies` file.

    Args:
        file (Path): the file itself
        bstr (bytes): the bytestring
        tsv (list): the tsv in list form
        nrows (int): number of rows
        offset: offset to specify columns
        ncols_int (int): number of numeric columns
        ncols_str (int): number of string columns

    Returns:
        list: `tsv` with rows populated

    Raises:
        Exception: if the `.ies` file is corrupt or invalid

    """
    for _ in range(nrows):
        row_id = get_int_from_bytes(bstr[offset:offset+4])
        offset += 4
        # `row_class` is prepended before each record
        # but is not used in the `.tsv` until column 3.
        # This has an effect of creating padding before
        # each "row".
        # `lookupkey` is unnecessary in this port, since
        # `row_class` is equivalent to it.
        row_class = get_int_from_bytes(bstr[offset:offset+2])
        offset += 2 + row_class

        objs = {}

        row = []
    
        for i in range(ncols_int):
            # Equivalent to `br.ReadSingle`, line 103.
            col = int(struct.unpack('<f', bstr[offset:offset+4])[0])
            if col is None:
                raise Exception(
                    f'IES file {file} is invalid: obj is null'
                    )
            row.append(col)
            offset += 4

        for i in range(ncols_str):
            # Equivalent to `br.ReadUInt16`, line 110.
            # `col_len` is the character length of the current column.
            col_len = struct.unpack('<H', bstr[offset:offset+2])[0]
            offset += 2
            col = convert_bytestring(bstr[offset:offset+col_len])
            if col is None:
                raise Exception(
                    f'IES file {file} is invalid: obj is null'
                    )
            row.append(col)
            offset += col_len

        tsv.append(row)

        offset += ncols_str

    return tsv

def pretty_print_xml(tsv:list, header:str, path:Path):
    """Converts the given tsv to an xml file

    Args:
        tsv (list): the tsv to be converted
        header (str): the header to be displayed as the root
        path (Path): the output path for the file(s)
    """
    idspace = Element('idspace', {'id': header})
    category = SubElement(idspace, 'Category')
    columns = tsv[0]
    for row in tsv[1:]:
        attribs = {
            # Values and columns read in as integers - converting to string to prevent this issue
            str(col): (str(val).strip() if str(val).strip() else 'None')
            for col, val in zip(columns, row)
        }
        SubElement(category, 'Class', attrib=attribs)
    # Pretty print and write xml
    rough_string = tostring(idspace, encoding='utf-8', xml_declaration=False)
    pretty_xml = parseString(rough_string).toprettyxml(indent='\t', encoding='utf-8')
    
    with path.open('wb') as f:
        f.write(pretty_xml)
        
    
    

def convert_file(file: Path, dest = None):
    """Converts a `file` fully from bytes to string.
    Optionally outputs to new file `dest`, if not run in batch mode.
    (`dest` is not None.)

    Args:
        file (Path): the file to convert
        dest (Path, optional): the destination output; defaults to None

    Returns:
        bool: True if successful; False otherwise

    Raises:
        Exception: if the `.ies` file is corrupt or invalid

    """
    bstr = file.read_bytes()
    header = bstr[0:128].decode(encoding='utf-8', errors='replace').rstrip(NULL_BYTE)
    header = clean_column_names(header)
    # Equivalent to original `val1`, `offset1`, `offset2`, and `filesize`.
    # I interpreted it as `value`, but I am unsure.
    # Four value slicing equivalent to `ReadInt32`.
    value, offset1, offset2, file_size = [
        get_int_from_bytes(bstr[i:i+4])
        for i
        in (128, 132, 136, 140)
        ]
    if len(bstr) != file_size:
        raise Exception(
            f'IES file {file} has invalid length specified: {len(bstr)}'
            )
    # Aaron - Note that in xml2ies the value is not -1 here - it's possible that because
    # I changed the decoding to utf-8-sig that there might be an issue
    # Apparently the bug is it's looking for the BOM because I decoded it using utf-8-sig
    if value != 1:
        raise Exception(
            f'IES file {file} has incorrect value: {value}'
            )

    # Equivalent to original `rows`, `cols`, `ncols_int`, and `ncols_str`.
    # `short1` is unnecessary in this port.
    # Two value slicing equivalent to `ReadInt16`.
    nrows, ncols, ncols_int, ncols_str = [
        get_int_from_bytes(bstr[i:i+2])
        for i
        in (146, 148, 150, 152)
        ]

    if ncols != ncols_int + ncols_str:
        raise Exception(
            f'IES file {file} has mismatched cols: '
            f'{ncols}!={ncols_int}+{ncols_str}'
            )

    # Equivalent to `ms.Seek`.`
    offset_idx = file_size - offset1 - offset2

    col_names = get_col_names(file, bstr, ncols, offset_idx, ncols_int)

    tsv = []

    row = []
    for i in range(ncols):
        if col_names[i] is None:
            raise Exception(
                f'IES file {file} is invalid: '
                f'col_names at index {i} is null'
                )
        row.append(str(col_names[i]))
    tsv.append(row)

    offset_idx = file_size - offset2 # equivalent to `ms.Seek`, line 89

    tsv = get_rows(file, bstr, tsv, nrows, offset_idx, ncols_int, ncols_str)
    # old code used to create a tsv - skipping this altogether
    # out = Path(
    #     f'{file.stem}.tsv'
    #     if dest is None
    #     else dest
    #     )
    # out.write_text(
    #     LINE.join(
    #         [
    #             SEPARATOR.join(map(str, line))
    #             for line
    #             in tsv
    #             ]
    #         ),
    #     encoding='utf-8-sig'
    #     )
    
    # new path with xml data type
    location = os.path.join(os.getcwd(), "xml_files") if dest is None else dest
    if not os.path.isdir(location):
        os.mkdir(location)
        
    # out_path = Path(f'{file.stem}.xml' if dest is None else dest)
    out_path = Path(f'{location}/{file.stem}.xml') if dest is None else dest
    
        
    # pretty print the xml file
    pretty_print_xml(tsv, header, out_path)

    return True


def batch_convert_dir(directory: Path):
    """Traverses a `directory` with max-depth of 1 to convert all
    `.ies` files.

    Args:
        directory (Path): the directory itself (usually relative)

    Returns:
        None

    """
    
    ies_files = list(directory.glob('*.ies'))
    total_files = len(ies_files)
    print(f'Found {total_files} ies files')
    
    for file in tqdm(ies_files, desc='Converting .ies files to .xml', unit='file'):
        try:
            convert_file(file)
        except Exception as e:
            print(
                f"""Exception caught: {e}'
                {file} was subsequently skipped."""
                )

    # for file in directory.glob('*.ies'):
        # try:
        #     convert_file(file)
        # except Exception as e:
        #     print(
        #         f"""Exception caught: {e}'
        #         {file} was subsequently skipped."""
        #         )
    return


if __name__ == "__main__":
    args = parser.parse_args()
    print(args.subcommand)
    if args.subcommand == 'file':
        convert_file(args.ies_file, args.output)
    else:
        batch_convert_dir(args.directory)
