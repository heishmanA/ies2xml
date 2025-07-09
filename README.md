# ies2xml 

## Overview

`ies2xml` is a fork of  the `ies2csv` utility created by `dark-nova` [github](https://github.com/dark-nova/ies2csv). `ies2xml` is a tool to convert [Tree of Savior][tos] `.ies` files to a readable `.xml` format. 

`xml2ies` is a new tool added to `ies2xml` to convert `.xml` format into `.ies` format.

Please refer to Please refer to the `IES2TSVCHANGELOG.md` and `IES2TSVREADME.md` to see `dark-nova's` original changes. 

## Usage

### Notes
⚠ Both ies2xml and xml2ies will create an output folder named ies_out and xml_files respectively if no output path is specified. 
⚠ All files will be overwritten in these folders upon completion of the program

### ies2xml
---
    ### Main
        $ python.py ies2xml.py -h
        usage: ies2xml.py [-h] {file,batch} ...

        An .ies file to xml converter

        positional arguments:
        {file,batch}  subcommand help
            file        file help
            batch       batch help

        options:
        -h, --help    show this help message and exit

        $ python.py ies2xml.py file -h
        usage: ies2xml.py file [-h] [--output OUTPUT] ies_file

        positional arguments:
        ies_file              The .ies file to convert

        options:
        -h, --help            show this help message and exit
        --output OUTPUT, -o OUTPUT
                                An optional file to output to; overrides default file name

    ### Batch 
    ---
        usage: ies2xml.py batch [-h] directory

        positional arguments:
        directory   The directory with .ies files to batch convert

        options:
        -h, --help  show this help message and exit

### xml2ies
---
    ### Main

        $ python xml2ies.py -h
        usage: xml2ies.py [-h] {file,batch} ...

        An .xml to .ies converter

        positional arguments:
        {file,batch}  subcommand help
            file        file help
            batch       batch help

        options:
        -h, --help    show this help message and exit

        $ python xml2ies.py file -h
        usage: xml2ies.py file [-h] [--output OUTPUT] xml_file

        positional arguments:
        xml_file              The xml file to convert

        options:
        -h, --help            show this help message and exit
        --output OUTPUT, -o OUTPUT
                            Optional output for a single file; overwrites default file

    ### Batch 

        $ python xml2ies.py batch -h
        usage: xml2ies.py batch [-h] directory

        positional arguments:
        directory   The directory containing all .xml files to be batch converted

        options:
        -h, --help  show this help message and exit


## Requirements

This code was designed with the following:
 
 - Python 3.5+
 - [tqdm][tqdm] a library for displaying a progress bar. 

## Disclaimer

This project is not affiliated with or endorsed by [Tree of Savior][tos]. See [`LICENSE`](LICENSE) for more detail.

[tos]: https://treeofsavior.com/
[tqdm]: https://tqdm.github.io/