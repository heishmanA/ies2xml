import io
import struct
from pathlib import Path

class BinaryWriterTools:

    __XOR_KEY: int = 1
    __NULL_BUTE = b'\x00'
    def __init__(self, writer: io.BufferedRandom):
        self.writer = writer
    
    def __encode_str__(self, value: str) -> bytes:
        """Function to encode a str in utf-8 format 

        Args:
            value (str): The string to encode

        Returns:
            bytes: the encoded string using utf-8 encoding 
        """
        return value.encode('utf-8')
    
    def __compare_write_length___(self, encoded_bytes: bytes, length: int) -> int:
        """ Compares the write lengths and returns the proper length for the buffer to write

        Args:
            encoded_bytes (bytes): The bytes of the string to write
            length (int): the length of the string

        Returns:
            _type_: returns the length if the length of encoded bytes is larger than length, 
                    else the length of the encoded bytes
        """
        return length if len(encoded_bytes) > length else len(encoded_bytes)
    
    def __write_null_bytes__(self, write_length: int, length: int):
        """Appends null bytes to the writer based on the difference between write length and length 

        Args:
            write_length (int): The amount written to the file
            length (int): the actual amount to be written to file
        """
        self.writer.write(self.__NULL_BUTE * (length - write_length))
    
    def x_or_buffer(self, buffer:bytearray) -> bytearray:
        """ Uses the XOR operation on the buffer and returns a new bytearray containing the XOR'd results

        Args:
            buffer (bytearray): The buffer to XOR

        Returns:
            bytearray: The array containing the XOR'd results of the buffer
        """
        r = bytearray()
        for i in range(len(buffer)):
            if buffer[i] == 0:
                break
            buffer[i] ^= self.__XOR_KEY
        return r
    
    def write_xor_lp_str(self, output: str):
        """ Writes the XOR'd output to buffer as a UTF-8 string with a prefixed length
        
        Args:
            output (str): The output to be XOR'd and written to the buffer 
        """
        byte_length = len(self.__encode_str__(output))
        self.writer.write(struct.pack('h', byte_length))
        self.write_xored_fixed_string(output, byte_length)
        

    def write_xored_fixed_string(self,output: str, length: int):
        """ Writes the XOR'd output to buffer as UTF-8 string
            String is cut off if too long, but extended with padding if too short

        Args:
            output (str): The output to be XOR'd and written to buffer
            length (int): The length of the string to be written to the buffer
        """
        buffer = self.__encode_str__(output)
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
        buffer = self.__encode_str__(output)
        write_length = self.__compare_write_length___(buffer, length)
        
        self.writer.write(buffer[0:write_length])
        
        if (write_length < length):
            self.__write_null_bytes__(write_length, length)
        
        