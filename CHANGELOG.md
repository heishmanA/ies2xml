# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## 1.2 - 2025-06-23
# Added
- ies tools (and contents) - tools required for constructing an object to represent ies columns, headers and rows and write to file
- xmltools.py - a tool (or library) that can be used to load xml file, columns and rows and convert to ies files

## Fixed
- Fixed a padding bug that caused decoding errors

# Future updates
- Organize files to separate files
- possibly create a batch file to run these w/o having to run from console every time
- documentation
- Code organization

## 1.1 - 2025-06-23

## Added
- xml2ies.py

## 1.0 - 2025-06-23

## Fixed
- Fixed an encoding error that was preventing old TOS files from being read 

## Update
- No longer produces tsv files, but instead produces xml files
- Renamed original CHANGELOG to IES2TSVCHANGELOG.md to make sure that the original fork's changelog exists
