import os
import math
import torch
import numpy as np
from PIL import Image
from ultralytics import YOLO

class TiledYOLOProcessor:
    def __init__(self, model_weights, tile_size=256, imgsz=256, overlap=0):
        self.model = YOLO(model_weights)
        self.tile_size = tile_size
        self.imgsz = imgsz
        self.overlap = overlap
        self.tmp_dir = "tmp"
        os.makedirs(self.tmp_dir, exist_ok=True)

    def process_image(self, image_path, conf=0.25):
        original_img = Image.open(image_path)
        original_width, original_height = original_img.size
        filename = os.path.basename(image_path)
        
        tiles = self._generate_tiles(original_width, original_height)
        
        all_detections = []
        
        for i in range(0, len(tiles), 4):
            batch = tiles[i:i+4]
            batch_images = []
            batch_coords = []
            
            for x1, y1, x2, y2 in batch:
                tile = original_img.crop((x1, y1, x2, y2))
                batch_images.append(np.array(tile))
                batch_coords.append((x1, y1, x2, y2))
            
            batch_results = self.model(batch_images, imgsz=self.imgsz, conf=conf)
            
            for result, (offset_x, offset_y, tile_x2, tile_y2) in zip(batch_results, batch_coords):
                if result.boxes is not None:
                    for box in result.boxes:
                        box_xyxy = box.xyxy[0].cpu().numpy()
                        
                        if self._is_in_overlap_zone(box_xyxy, offset_x, offset_y, tile_x2, tile_y2):
                            continue
                        
                        abs_xyxy = [
                            box_xyxy[0] + offset_x,
                            box_xyxy[1] + offset_y,
                            box_xyxy[2] + offset_x,
                            box_xyxy[3] + offset_y
                        ]
                        
                        all_detections.append({
                            'xyxy': abs_xyxy,
                            'conf': box.conf.item(),
                            'cls': box.cls.item()
                        })
        
        filtered_detections = self._filter_overlapping_boxes(all_detections)
        
        result_img = original_img.copy()
        
        if filtered_detections:
            img_np = np.array(result_img)
            dummy_result = self.model(img_np, imgsz=self.imgsz)[0]
            
            boxes = torch.tensor([d['xyxy'] for d in filtered_detections])
            confs = torch.tensor([d['conf'] for d in filtered_detections])
            cls = torch.tensor([d['cls'] for d in filtered_detections])
            
            dummy_result.boxes.data = torch.cat([
                boxes,
                confs.unsqueeze(1),
                cls.unsqueeze(1)
            ], dim=1)
            
            scale_factor = max(original_width, original_height) / 1000
            font_size = max(10, int(20 * scale_factor))
            line_width = max(1, int(2 * scale_factor))
            
            plotted_img_np = dummy_result.plot(
                font_size=font_size,
                line_width=line_width,
                pil=False
            )
            
            result_img = Image.fromarray(plotted_img_np)
        
        output_path = os.path.join(self.tmp_dir, f"detected_{filename}")
        result_img.save(output_path)
        print(f"Результат сохранен в {output_path}")
        return result_img, len(filtered_detections)

    def _is_in_overlap_zone(self, box_xyxy, offset_x, offset_y, tile_x2, tile_y2):
        abs_x1 = box_xyxy[0] + offset_x
        abs_y1 = box_xyxy[1] + offset_y
        abs_x2 = box_xyxy[2] + offset_x
        abs_y2 = box_xyxy[3] + offset_y
        
        overlap_margin = self.overlap // 2
        left_bound = offset_x + overlap_margin
        right_bound = tile_x2 - overlap_margin
        top_bound = offset_y + overlap_margin
        bottom_bound = tile_y2 - overlap_margin
        
        return (abs_x1 < left_bound or abs_x2 > right_bound or 
                abs_y1 < top_bound or abs_y2 > bottom_bound)

    def _filter_overlapping_boxes(self, detections):
        if not detections:
            return []
            
        detections = sorted(detections, key=lambda x: x['conf'], reverse=True)
        
        filtered = []
        used_areas = []
        
        for det in detections:
            x1, y1, x2, y2 = det['xyxy']
            current_area = (x1, y1, x2, y2)
            
            overlap = False
            for used in used_areas:
                if self._iou(current_area, used) > 0.1:  
                    overlap = True
                    break
                    
            if not overlap:
                filtered.append(det)
                used_areas.append(current_area)
                
        return filtered

    def _iou(self, box1, box2):
        x_left = max(box1[0], box2[0])
        y_top = max(box1[1], box2[1])
        x_right = min(box1[2], box2[2])
        y_bottom = min(box1[3], box2[3])
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
            
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
        
        union_area = box1_area + box2_area - intersection_area
        return intersection_area / union_area if union_area > 0 else 0.0

    def _generate_tiles(self, width, height):
        tiles = []
        stride = self.tile_size - self.overlap
        
        nx = math.ceil((width - self.overlap) / stride)
        ny = math.ceil((height - self.overlap) / stride)
        
        for i in range(ny):
            for j in range(nx):
                x1 = j * stride
                y1 = i * stride
                x2 = min(x1 + self.tile_size, width)
                y2 = min(y1 + self.tile_size, height)
                
                if x2 - x1 < self.tile_size or y2 - y1 < self.tile_size:
                    x1 = max(0, x2 - self.tile_size)
                    y1 = max(0, y2 - self.tile_size)
                
                tiles.append((x1, y1, x2, y2))
        
        return tiles