import io
import struct
from pathlib import Path

class BinaryWriterTools:

    __XOR_KEY: int = 1
    __NULL_BYTE = b'\x00'
    def __init__(self, writer: io.BufferedRandom):
        self.writer = writer
    
    def __encode_str__(self, value: str, max_bytes:int = -1) -> bytes:
        """
        Encodes a string to UTF-8 bytes, optionally ensuring it fits within a byte limit.

        Args:
            value (str): The string to encode
            max_bytes (int): Max number of bytes allowed in result. Use -1 for no limit.

        Returns:
            bytes: UTF-8 encoded string safely trimmed to max_bytes, if provided.
        """

        encoded = value.encode('utf-8', errors='replace')
        if  max_bytes == -1 or len(encoded) <= max_bytes:
            return encoded
        return encoded[:max_bytes].decode('utf-8', errors='ignore').encode('utf-8')
    
    def __compare_write_length___(self, buffer: bytes, length: int) -> int:
        """ Compares the write lengths and returns the proper length for the buffer to write

        Args:
            encoded_bytes (bytes): The bytes of the string to write
            length (int): the length of the string

        Returns:
            _type_: returns the length if the length of encoded bytes is larger than length, 
                    else the length of the encoded bytes
        """
        return length if len(buffer) > length else len(buffer)
    
    def __write_null_bytes__(self, write_length: int, length: int):
        """Appends null bytes to the writer based on the difference between write length and length 

        Args:
            write_length (int): The amount written to the file
            length (int): the actual amount to be written to file
        """
        self.writer.write(self.__NULL_BYTE * (length - write_length))
    
    def x_or_buffer(self, buffer:bytearray):
        """ Uses the XOR operation on the buffer and returns a new bytearray containing the XOR'd results

        Args:
            buffer (bytearray): The buffer to XOR

        Returns:
            bytearray: The array containing the XOR'd results of the buffer
        """
        return bytes(b ^ self.__XOR_KEY for b in buffer)
    
    def write_xor_lp_str(self, output: str):
        """ Writes the XOR'd output to buffer as a UTF-8 string with a prefixed length
        
        Args:
            output (str): The output to be XOR'd and written to the buffer 
        """
        byte_length = len(self.__encode_str__(output))
        self.writer.write(struct.pack('<H', byte_length))
        self.write_xored_fixed_string(output, byte_length)
        

    def write_xored_fixed_string(self,output: str, length: int):
        """ Writes the XOR'd output to buffer as UTF-8 string
            String is cut off if too long, but extended with padding if too short

        Args:
            output (str): The output to be XOR'd and written to buffer
            length (int): The length of the string to be written to the buffer
        """
        buffer = self.__encode_str__(output, length)
        write_length = self.__compare_write_length___(buffer, length)
        x_ored_output = self.x_or_buffer(bytearray(buffer))
        self.writer.write(x_ored_output[0:write_length])
      
        if write_length < length:
            self.__write_null_bytes__(write_length, length)
    
    
    def write_fixed_string(self, output:str, length: int):
        """ Writes the given output to buffer as UTF-8 string (No XOR)
            String is cut off if too long, but extended with padding if too short

        Args:                   
            output (str): The output to be XOR'd and written to buffer
            length (int): The length of the string to be written to the buffer
        """
        buffer = self.__encode_str__(output, length)
        write_length = self.__compare_write_length___(buffer, length)
        self.writer.write(buffer[0:write_length])
        
        if write_length < length:
            self.__write_null_bytes__(write_length, length)
        
        