from ultralytics import YOLO
from PIL import Image, ImageDraw
import os


class ClientDetector:
    def split_image(self, image_path, output_dir, tile_size=256):
        os.makedirs(output_dir, exist_ok=True)
        img = Image.open(image_path)
        width, height = img.size
        
        tiles = []
        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):
                box = (x, y, min(x + tile_size, width), min(y + tile_size, height))
                tile = img.crop(box)
                
                tile_path = os.path.join(output_dir, f"tile_{x}_{y}.png")
                tile.save(tile_path)
                tiles.append((x, y, tile_path))
        
        return tiles
    

    def process_tiles(self, tiles):
        model = YOLO("weights/medium_ships.pt")  
        
        detections = []
        for x, y, tile_path in tiles:
            results = model(tile_path)
            
            for result in results:
                boxes = result.boxes.xyxy  
                classes = result.boxes.cls  
                confs = result.boxes.conf  
                
                for box, cls, conf in zip(boxes, classes, confs):
                    x1, y1, x2, y2 = box
                    global_box = (x + x1, y + y1, x + x2, y + y2, cls, conf)
                    detections.append(global_box)
        
        return detections
    

    def draw_detections(self, image_path, detections, output_path):
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)

        for (x1, y1, x2, y2, cls, conf) in detections:
            draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
            draw.text((x1, y1), f"{cls}: {conf:.2f}", fill="red")

        img.save(output_path)
        
    def detect(self, image_path, output_path):
        tiles = self.split_image(image_path, "tiles")
        detections = self.process_tiles(tiles)
        self.draw_detections(image_path, detections, output_path)