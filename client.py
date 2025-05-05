import socket
import struct
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from PIL import Image
import numpy as np
from datetime import datetime

class ModeRLI(Enum):
    CHAR = '0'
    UCHAR = '1'
    USHORT = '2'
    FLOAT = '4'

@dataclass
class Mode:
    mode_rli: ModeRLI
    size_x: int
    size_y: int

@dataclass
class Params:
    mode_rli: ModeRLI
    size_x: int
    size_y: int
    num_cadr: int
    latitude: float
    longtitude: float
    way_angle: float
    dy: float
    dx: float

class RLIClient:
    def __init__(self, host='127.0.0.1', port=9977):
        self.set_connect(host, port)
        self.mode = ModeRLI.CHAR
        
        
    def set_connect(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        
    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"Connected to server at {self.host}:{self.port}")
            return True
        except socket.error as e:
            print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        if self.connected:
            self.socket.close()
            self.connected = False
            print("Disconnected from server")
            
    def set_mode(self, mode):
        self.mode = mode
    
    def send_mode(self, x, y):
        mode = Mode(mode_rli=self.mode,
                    size_x=x,
                    size_y=y)
        if not self.connected:
            print("Not connected to server")
            return False
        
        try:
            data = struct.pack(
                '=chh', 
                mode.mode_rli.value.encode('ascii'),
                mode.size_x,
                mode.size_y
            )
            self.socket.sendall(data)
            return True
        except struct.error as e:
            print(f"Error packing mode structure: {e}")
            return False
        except socket.error as e:
            print(f"Error sending mode: {e}")
            return False
    
    def receive_data(self, output_file="tmp/output.raw", progress_callback=None):
        if not self.connected:
            print("Not connected to server")
            return None
        
        try:
            total_size_data = self._receive_exact(8)
            if not total_size_data:
                return None
                
            total_size = struct.unpack('=Q', total_size_data)[0]  
            print(f"Total size to receive: {total_size} bytes")
            
            params_data = self._receive_exact(38)
            if not params_data:
                return None
            
            params = self._unpack_params(params_data)
            if not params:
                return None
                
            print(f"Received params: {params}")
            
            bytes_received = 0
            output_path = Path(output_file)
            
            with output_path.open('wb') as f:
                while bytes_received < total_size:
                    chunk_size = min(65536, total_size - bytes_received)
                    chunk = self._receive_exact(chunk_size)
                    if not chunk:
                        print("Connection terminated prematurely")
                        return None
                        
                    f.write(chunk)
                    bytes_received += len(chunk)
                    
                    if progress_callback:
                        progress_callback(bytes_received, total_size)
                    
                    print(f"Received {bytes_received}/{total_size} bytes ({bytes_received/total_size:.1%})")
            
            print(f"Successfully received {bytes_received} bytes and saved to {output_path}")
            return params, str(output_path)
            
        except (socket.error, struct.error, IOError) as e:
            print(f"Error receiving data: {e}")
            return None
    
    def raw_to_tiff(self, raw_file, tiff_file, width, mode):
        try:
            dtype_map = {
                ModeRLI.CHAR: np.int8,
                ModeRLI.UCHAR: np.uint8,
                ModeRLI.USHORT: np.uint16,
                ModeRLI.FLOAT: np.float32
            }
            
            dtype = dtype_map.get(mode)
            if dtype is None:
                print(f"Unsupported mode: {mode}")
                return False
            with open(raw_file, 'rb') as f:
                raw_data = np.fromfile(f, dtype=dtype)
            available_pixels = len(raw_data)
            height = available_pixels // width
            expected_size = width * height * np.dtype(dtype).itemsize
            actual_size = Path(raw_file).stat().st_size
            
            if actual_size < expected_size:
                print(f"Warning: RAW file is smaller than expected ({actual_size} < {expected_size})")
                height = actual_size // (width * np.dtype(dtype).itemsize)
                print(f"Adjusted height to {height}")
            
            expected_pixels = width * height
            if available_pixels < expected_pixels:
                print(f"Warning: Not enough pixels ({available_pixels} < {expected_pixels})")
                raw_data = np.pad(raw_data, (0, expected_pixels - available_pixels), mode='constant')
            elif available_pixels > expected_pixels:
                raw_data = raw_data[:expected_pixels]
            
            image_data = raw_data.reshape((height, width))
            
            if mode in (ModeRLI.CHAR, ModeRLI.UCHAR):
                pass
            else:
                min_val = np.min(image_data)
                max_val = np.max(image_data)
                if max_val > min_val:
                    image_data = ((image_data - min_val) * (255.0 / (max_val - min_val))).astype(np.uint8)
                else:
                    image_data = np.zeros_like(image_data, dtype=np.uint8)
            
            current_time = datetime.now()

            formatted_time = current_time.strftime("%Y-%m-%d-%H-%M-%S")
            
            img = Image.fromarray(image_data, mode='L')  
            img = img.convert('RGB')
            img.save(f'client_image/image_{formatted_time}.tiff', format='TIFF')
            
            print(f"Successfully converted {raw_file} to {tiff_file}")
            return f'image_{formatted_time}.tiff'
            
        except Exception as e:
            print(f"Error converting RAW to TIFF: {e}")
            return False
    
    def _receive_exact(self, num_bytes):
        data = b''
        while len(data) < num_bytes:
            chunk = self.socket.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    def _unpack_params(self, params_data):
        try:
            fields = struct.unpack('=c2hb3d2f', params_data)
            
            return Params(
                mode_rli=ModeRLI(fields[0].decode('ascii')),
                size_x=fields[1],
                size_y=fields[2],
                num_cadr=fields[3],
                latitude=fields[4],
                longtitude=fields[5],
                way_angle=fields[6],
                dy=fields[7],
                dx=fields[8]
            )
        except (struct.error, ValueError) as e:
            print(f"Error unpacking params: {e}")
            return None