from myHpack import HPACK

class Decoder:
    def __init__(self):
        self.hpack = HPACK()
        self.static_table = self.hpack.static_table
        self.dynamic_table = []  # Dynamic table for headers
        self.max_table_size = 4096  # Default size for dynamic table
        
    def decode_integer(self, data, prefix_bits):
        """Decode an integer from the variable-length encoding."""
        prefix_max = (1 << prefix_bits) - 1
        result = data[0] & prefix_max
        data = data[1:]
        multiplier = 1
        while data:
            byte = data[0]
            data = data[1:]
            result += (byte & 127) * multiplier
            multiplier *= 128
            if (byte & 128) == 0:
                break
        return result, data


    def decode_string(self, data):
        """Decode a string literal."""
        length, data = self.decode_integer(data, 7)
        return data[:length].decode("utf-8"), data[length:]


    def decode_headers(self, payload):
        """Decode headers from an HPACK payload."""
        headers = []
        i = 0
        while i < len(payload):
            byte = payload[i]
            
            if byte & 0x80:  # Indexed Header Field (1xxxxxxx)
                index = byte & 0x7F  # Clear the high bit
                if index == 0:
                    print(f"Invalid header index 0.")
                    i += 1
                    continue
                elif 1 <= index <= len(self.static_table):
                    headers.append(self.static_table[index - 1])
                elif index > len(self.static_table):
                    # Handle dynamic table
                    dynamic_index = index - len(self.static_table) - 1
                    if 0 <= dynamic_index < len(self.dynamic_table):
                        headers.append(self.dynamic_table[dynamic_index])
                    # else:
                    #     print(f"Invalid dynamic header index: {index}")
                else:
                    print(f"Invalid index: {index}")
                i += 1
            
            elif byte & 0x40:  # Literal Header Field with Indexed Name
                i += 1
                print(f"Literal header field with indexed name.")
                
                # Step 1: Extract the index of the name
                index = byte & 0x3F  # Mask out the high two bits
                i += 1
                if index == 0:
                    print(f"Invalid index: 0 in literal header with indexed name.")
                    continue
                elif 1 <= index <= len(self.static_table):
                    header_name = self.static_table[index - 1][0]
                elif index > len(self.static_table):
                    dynamic_index = index - len(self.static_table) - 1
                    if 0 <= dynamic_index < len(self.dynamic_table):
                        header_name = self.dynamic_table[dynamic_index][0]
                    else:
                        print(f"Invalid dynamic index: {index}")
                        continue  # Invalid dynamic index
                else:
                    print(f"Invalid index: {index}")
                    continue  # Invalid index
                
                # Step 2: Decode the header value length and value
                value_length, remaining_data = self.decode_integer(payload[i:], 7)  # Decode value length
                i += len(payload[i:]) - len(remaining_data)  # Adjust the pointer
                header_value = remaining_data[:value_length].decode("utf-8")  # Decode the value
                i += value_length  # Move the pointer past the value
                
                print(f"Decoded Header: Name={header_name}, Value={header_value}")
                headers.append((header_name, header_value))
                
                # Step 3: Add to dynamic table
                self.hpack.add_to_dynamic_table((header_name, header_value))

            
            elif byte & 0x20:  # Literal Header Field with New Name (0x20 for new name)
                # Step 1: Extract the length of the header name
                i += 1  # Move to the next byte, where we can get the name length
                name_length, data = self.decode_integer(payload[i:], 7)  # Decode the length of the name (7-bit prefix)
                i += len(payload[i:]) - len(data)  # Adjust the pointer after decoding the length
                
                header_name = data[:name_length].decode("utf-8")
                i += name_length  # Move pointer past the header name
                
                value_length, remaining_data = self.decode_integer(payload[i:], 7)  # Decode the length of the value (7-bit prefix)
                i += len(payload[i:]) - len(remaining_data)  # Adjust the pointer after decoding the length
                
                header_value = remaining_data[:value_length].decode("utf-8")
                i += value_length  # Move pointer past the header value
                
                self.hpack.add_to_dynamic_table((header_name, header_value))
                headers.append((header_name, header_value))

            else:
                #print(f"Unsupported header type: {byte}")
                i += 1  # Move to the next byte

        return headers

        


