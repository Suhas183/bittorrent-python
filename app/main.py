import json
import sys
import hashlib

import bencodepy
import requests

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

def get_decoded_value(bencoded_file):
    f = open(bencoded_file, "rb")
    bencoded_value = f.read()
    f.close()
    decoded_value,_ = decode_bencode(bencoded_value)
    return decoded_value

def announce_url(decoded_value):
    return decoded_value['announce']

def get_info_dict(decoded_value):
    return decoded_value['info']

def get_sha_info(info_dict):
    bencoded_info_dict = bencodepy.encode(info_dict)
    return hashlib.sha1(bencoded_info_dict).hexdigest()

def url_encode(info_hash):
    split_string = ''.join(['%' + info_hash[i:i+2] for i in range(0,len(info_hash),2)])
    return split_string

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
        
        decoded_value = get_decoded_value(bencoded_file)
        url = announce_url(decoded_value)
        info_dict = get_info_dict(decoded_value)
        sha_info_hash = get_sha_info(info_dict)
        
        pieces = info_dict['pieces']
        hex_string = pieces.hex()
        
        print(f'Tracker URL: {url}')
        print(f'Length: {info_dict["length"]}')
        print(f'Info Hash: {sha_info_hash}')
        print(f'Piece Length: {info_dict["piece length"]}')
        print('Piece Hashes:')
        for i in range(0,len(hex_string),40):
            print(hex_string[i:i+40])
            
    elif command == 'peers':
        bencoded_file = sys.argv[2]
        
        decoded_value = get_decoded_value(bencoded_file)
        url = announce_url(decoded_value)
        info_dict = get_info_dict(decoded_value)
        sha_info_hash = get_sha_info(info_dict)
        
        encoded_hash = url_encode(sha_info_hash)
        peer_id = '3a5f9c1e2d4a8e3b0f6c'
        port = 6881
        uploaded = 0
        downloaded = 0
        left = info_dict['length']
        compact = 1
        
        query_string = (
            f"info_hash={encoded_hash}&"
            f"peer_id={peer_id}&"
            f"port={port}&"
            f"uploaded={uploaded}&"
            f"downloaded={downloaded}&"
            f"left={left}&"
            f"compact={compact}"
        )
        
        complete_url = f"{url}?{query_string}"
        r = requests.get(complete_url)
        decoded_dict,_ = decode_bencode(r.content)
        peers = decoded_dict['peers']
        decimal_values = [byte for byte in peers]
        for i in range(0,len(decimal_values),6):
            ip_address = '.'.join(str(num) for num in decimal_values[i:i+4])
            ip_address += f":{int.from_bytes(decimal_values[i+4:i+6], byteorder='big', signed=False)}"
            print(ip_address)
    else:
        raise NotImplementedError(f"Unknown command {command}")   


if __name__ == "__main__":
    main()
