from ultralytics import YOLO


class Model:
    def __init__(self) -> None:
        self.imgsize = 960
        self.model = YOLO("weights/nano960-9.pt")
    
    def predict(self, file_path, conf):
        return self.model.predict(file_path, imgsz=self.imgsize, conf=conf)

class Nano960_9(Model):
    def __init__(self) -> None:
        self.imgsize = 960
        self.model = YOLO("weights/nano960-9.pt")
    
class Nano1280_9(Model):
    def __init__(self) -> None:
        self.imgsize = 1280
        self.model = YOLO("weights/nano1280-9.pt")
        
class Nano960_10(Model):
    def __init__(self) -> None:
        self.imgsize = 1280
        self.model = YOLO("weights/nano960-10.pt")  
    
class Medium960_9(Model):
    def __init__(self) -> None:
        self.imgsize = 960
        self.model = YOLO("weights/medium960-9.pt")
        
class Medium960_10(Model):
    def __init__(self) -> None:
        self.imgsize = 960
        self.model = YOLO("weights/medium960-10.pt")

class Medium_ships(Model):
    def __init__(self) -> None:
        self.imgsize = 800
        self.model = YOLO("weights/medium_ships.pt")