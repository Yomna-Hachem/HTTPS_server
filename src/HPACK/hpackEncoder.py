from myHpack import HPACK
from hpack import Encoder



class Encoder:
    def __init__(self):
        self.hpack = HPACK()
        self.static_table = self.hpack.static_table
        self.dynamic_table = []  # Dynamic table for headers
        self.max_table_size = 4096  # Default size for dynamic table

    def encode_integer(self, value, prefix_bits):
        """Encode an integer using the variable-length encoding."""
        prefix_max = (1 << prefix_bits) - 1
        if value < prefix_max:
            return bytearray([value])
        else:
            result = bytearray([prefix_max])
            value -= prefix_max
            while value >= 128:
                result.append((value % 128) + 128)
                value //= 128
            result.append(value)
            print("result",result)
            return bytes(result)
        
    def encode(self, headers):

        header_block = []

        # Encode each header
        for name, value in headers.items():
            print("name: ",name)
            print("value: ",value)

            #case 1
            if self.find_in_static_table(name, value):
                print("inside case 1")
                # Header is in the static table
                index = self.find_in_static_table(name, value)
                encoded_integer = self.encode_integer(index, 7)  # Indexed header
                header_block.append(bytes([encoded_integer[0] | 0x80]) + bytes(encoded_integer[1:]))
                
            #case 2    
            elif self.find_in_dynamic_table(name, value):
                print("inside case 2")
                index = self.find_in_dynamic_table(name, value)
                encoded_integer = self.encode_integer(index + 62, 7)  
                header_block.append(bytes([encoded_integer[0] | 0x80]) + bytes(encoded_integer[1:]))

               
            #case 3   
            elif self.find_name_in_static_table(name):
                print("inside case 3")
                index = self.find_name_in_static_table(name)
                encoded_byte = self.encode_integer(index, 6)
                encoded_name_index = bytes([encoded_byte[0] | 0x40]) + encoded_byte[1:]
                value_length = self.encode_integer(len(value), 7)
                encoded_value = self.encode_string(value)
                
                if name not in self.dynamic_table:
                    self.hpack.add_to_dynamic_table({name, value})  # Add to dynamic table
                header_block.append(bytes(encoded_name_index) + bytes(value_length) + bytes(encoded_value)   ) 

            #case 4            
            elif self.find_name_in_dynamic_table(name):
                print("inside case 4")
                index = self.find_name_in_dynamic_table(name)
                encoded_name_index = self.encode_integer(index + 62, 6)  # Indexed name in dynamic table
                # Encode value length (should come before the value)
                value_length = self.encode_integer(len(value), 7)
                encoded_value = self.encode_string(value)  # Encode value literally
                
                if name not in self.dynamic_table:
                    self.hpack.add_to_dynamic_table({name, value})  # Add to dynamic table
                header_block.append(bytes(encoded_name_index) + bytes(value_length) + bytes(encoded_value))
                # Header not in static table, use literal encoding   
                
            else:#case 5    
                print("inside case 5")
                encoded_name = self.encode_string(name)
                encoded_value = self.encode_string(value)
                name_length_encoding = self.encode_integer(len(name), 7)  # Length of name
                value_length_encoding = self.encode_integer(len(value), 7)  # Length of value

                if name not in self.dynamic_table:
                    self.hpack.add_to_dynamic_table({name, value})

                header_block.append(bytes(name_length_encoding) + bytes(value_length_encoding) + bytes(encoded_name) + bytes(encoded_value)  )  
    
                #header_block.append(self._encode_literal(name, value))

        return b''.join(header_block)

    def _encode_literal(self, name, value):
        """
        Encodes a header using the literal representation.
        """
        name_bytes = str(name).encode("utf-8")
        print("inside literal")
        value_bytes = str(value).encode("utf-8")

        # Name and value lengths with prefix encoding
        name_len = self._encode_integer(len(name_bytes), 7)
        value_len = self._encode_integer(len(value_bytes), 7)
        return b'\x00' + bytes(name_len) + name_bytes + bytes(value_len) + value_bytes
    
    
    def encode_string(self, string, huffman=False):
        """
        Encodes a string with optional Huffman encoding.
        """
        encoded = string.encode("utf-8")
        # print("encoded",encoded)
        huffman_flag = 0x80 if huffman else 0x00
        length_encoded = self.encode_integer(len(encoded), 7)
        return bytes([length_encoded[0] | huffman_flag]) + length_encoded[1:] + encoded
    
    def find_in_static_table(self, name, value):
        """
        Searches the static table for a header and returns its index.
        """
        for i, (n, v) in enumerate(self.static_table):
            if n == name and v == value:
                return i + 1  
        return False
    
    def find_in_dynamic_table(self, name, value):
        """
        Searches the static table for a header and returns its index.
        """
        for i, (n, v) in enumerate(self.dynamic_table):
            if n == name and v == value:
                return i + 1  
        return None

    def find_name_in_static_table(self, name):
        
        for i, (n, v) in enumerate(self.static_table):
            if n == name:
                return i + 1  
        return False
    
    def find_name_in_dynamic_table(self, name):
        """
        Searches the static table for a header and returns its index.
        """
        for i, n in enumerate(self.dynamic_table):
            if n == name:
                return i + 1  
        return False
    



    def _encode_integer(self, value, prefix_bits):
        """
        Encodes an integer using HPACK's prefix encoding.
        """
        max_prefix_value = (1 << prefix_bits) - 1
        if value < max_prefix_value:
            return bytes([value])
        result = [max_prefix_value]
        value -= max_prefix_value
        while value >= 128:
            result.append((value & 0x7F) | 0x80)
            value >>= 7
        result.append(value)
        return bytes(result)




if __name__ == "__main__":
    encoder = Encoder()

    # Sample response headers
    response_headers = {
        # ":status": "200",
        "content-type": "text/html",
        # "content-length": "1024",
        # "server": "HTTP2Server",
    }

    # Encode response headers
    encoded_response_headers = encoder.encode(response_headers)

    print("Encoded HTTP/2 Response Headers:")
    print(encoded_response_headers)
