import json
import sys
import hashlib

import bencodepy
# import requests - available if you need it!

# Examples:
#
# - decode_bencode(b"5:hello") -> b"hello"
# - decode_bencode(b"10:hello12345") -> b"hello12345"
def decode_string(bencoded_value):
    first_colon_index = bencoded_value.find(b":")
    if first_colon_index == -1:
        raise ValueError("Invalid encoded value")
    length = int(bencoded_value[:first_colon_index].decode())
    start_index = first_colon_index + 1
    try:
        return bencoded_value[start_index:start_index + length].decode('utf-8'), bencoded_value[start_index+length:]
    except:
        return bencoded_value[start_index:start_index + length], bencoded_value[start_index+length:]

def decode_integer(bencoded_value):
    first_e_index = bencoded_value.find(b"e")
    if first_e_index == -1:
        raise ValueError("Invalid encoded value")
    decoded_string = bencoded_value[1:first_e_index].decode()
    return int(decoded_string), bencoded_value[first_e_index+1:]

def decode_list(bencoded_value):
    decoded_list = []
    i = 1
    while bencoded_value[i] != ord('e'):
        element, remaining = decode_bencode(bencoded_value[i:])
        decoded_list.append(element)
        i = len(bencoded_value) - len(remaining)
    
    return decoded_list, bencoded_value[i+1:]

def decode_dict(bencoded_value):
    decoded_dict = {}
    i = 1
    while bencoded_value[i] != ord('e'):
        key, remaining = decode_bencode(bencoded_value[i:])
        i = len(bencoded_value) - len(remaining)
        value, remaining = decode_bencode(bencoded_value[i:])
        i = len(bencoded_value) - len(remaining)
        decoded_dict[key] = value
    
    return decoded_dict, bencoded_value[i+1:]     
    

def decode_bencode(bencoded_value):
    if chr(bencoded_value[0]).isdigit():
        return decode_string(bencoded_value)
    elif chr(bencoded_value[0]) == 'i':
        return decode_integer(bencoded_value)
    elif chr(bencoded_value[0]) == 'l':
        return decode_list(bencoded_value)    
    elif chr(bencoded_value[0]) == 'd':
        return decode_dict(bencoded_value)      
    else:
        raise NotImplementedError("Only strings and numbers are supported at the moment")


def main():
    command = sys.argv[1]

    if command == "decode":
        bencoded_value = sys.argv[2].encode()
        

        # json.dumps() can't handle bytes, but bencoded "strings" need to be
        # bytestrings since they might contain non utf-8 characters.
        #
        # Let's convert them to strings for printing to the console.
        def bytes_to_str(data):
            if isinstance(data, bytes):
                return data.decode()

            raise TypeError(f"Type not serializable: {type(data)}")
        
        decoded_value,_ = decode_bencode(bencoded_value)
        print(json.dumps(decoded_value, default=bytes_to_str))
    
    elif command == 'info':
        bencoded_file = sys.argv[2]
        def bytes_to_str(data):
            if isinstance(data, bytes):
                return data.decode()

            raise TypeError(f"Type not serializable: {type(data)}")
        f = open(bencoded_file, "rb")
        bencoded_value = f.read()
        decoded_value,_ = decode_bencode(bencoded_value)
        info_dict = decoded_value['info']
        bencoded_info_dict = bencodepy.encode(info_dict)
        pieces = info_dict['pieces']
        pieces_list = [pieces[i:i+20] for i in range(0, len(pieces), 20)]
        sha1_hashed_pieces = [hashlib.sha1(piece).hexdigest() for piece in pieces_list]
        sha_hash = hashlib.sha1(bencoded_info_dict).hexdigest()
        
        print(f'Tracker URL: {decoded_value["announce"]}')
        print(f'Length: {decoded_value["info"]["length"]}')
        print(f'Info Hash: {sha_hash}')
        print(f'Piece Length: {info_dict["piece length"]}')
        print('Piece Hashes:')
        for piece in sha1_hashed_pieces:
            print(piece)
     
    else:
        raise NotImplementedError(f"Unknown command {command}")   


if __name__ == "__main__":
    main()
