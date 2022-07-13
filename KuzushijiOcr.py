import os
from urllib import request
import hashlib
from PIL import Image
import json
import requests
from tqdm import tqdm
import torch
from Converter import Converter
import time
import pprint
from Common import Common

class TaskImage:
    yolo_defined_image_size = 1024

    def __init__(self, url, path, canvas_index, canvas_id, service=None):
        self.url = url
        self.canvas_index = canvas_index
        self.canvas_id = canvas_id
        self.path = path
        self.service = service

    def detect(self, model_yolo, thres=0.0):
        self.img = Image.open(self.path)
        self.getResizedImg()

        results = model_yolo(self.resized_img, size=self.yolo_input_image_size)

        # pprint.pprint(results)
        
        data = results.pandas().xyxy[0].to_json(orient="records")
        data = json.loads(data)

        ratio = 1 / self.ratio

        items = []

        height = self.h
        width = self.w

        canvas = self.canvas_id
        url = self.url

        for i in range(len(data)):
            index = i + 1

            result =data[i]

            # pprint.pprint(result)

            x = int(result["xmin"] * ratio)
            y = int(result["ymin"] * ratio)
            w = int(result["xmax"] * ratio) - x
            h = int(result["ymax"] * ratio) - y

            xywh = "{},{},{},{}".format(x, y, w, h)
            # print(xywh)
            score = result["confidence"]

            if score < thres:
                continue

            items.append({
                "id": "{}/annos/{}".format(canvas, index),
                "motivation": "commenting",
                "target": "{}#xywh={}".format(canvas, xywh),
                "type": "Annotation",
                "body": {
                    "type": "TextualBody",
                    "value": "label:{} score:{}".format(result["name"], round(score, 2))
                }
            })

        body = {
            "format": "image/jpeg",
            "height": height,
            "id": "{}".format(url),
            "type": "Image",
            "width": width
        }

        if self.service:
            body["service"] = [
                {
                    "id": self.service,
                    "type": "ImageService2",
                    "profile": "level2"
                }
            ]

        return {
            "annotations" : [
                {
                    "id" : "{}/annos".format(canvas),
                    "items" : items,
                    "type": "AnnotationPage"
                }
            ],
            "height": height,
            "id": "{}".format(canvas),
            "items": [
                {
                    "id": "{}/page".format(canvas),
                    "items": [
                        {
                            "body": body,
                            "id": "{}/page/imageanno".format(canvas),
                            "motivation": "painting",
                            "target": "{}".format(canvas),
                            "type": "Annotation"
                        }
                    ],
                    "type": "AnnotationPage"
                }
            ],
            "label" : "[{}]".format(self.canvas_index),
            "type": "Canvas",
            "width": width
        }

    def getResizedImg(self):
        img = self.img
        w, h = img.size
        long_line = max(w, h)
        yolo_input_image_size = min(self.yolo_defined_image_size, long_line)

        ratio = 1
        if long_line > yolo_input_image_size:
            ratio = yolo_input_image_size / long_line
            resized_img = img.resize((int(w * ratio), int(h * ratio)))

        self.w = w
        self.h = h
        self.long_line = long_line
        self.yolo_input_image_size = yolo_input_image_size
        self.ratio = ratio
        self.resized_img = resized_img

class KuzushijiOcr:

    @staticmethod
    def createManifest(manifest_uri, items, label, output_dir):
        m_data = {
            "@context": [
                "http://iiif.io/api/presentation/3/context.json",
                "http://www.w3.org/ns.anno.jsonld"
            ],
            "behavior": [
                "individuals"
            ],
            "id": manifest_uri, # request.url,
            "items": items,
            "label": label,
            "type": "Manifest"
        }

        opath = "{}/manifest.json".format(output_dir)
        os.makedirs(os.path.dirname(opath), exist_ok=True)

        with open(opath, 'w') as outfile:
            json.dump(m_data, outfile)

        return m_data

    @staticmethod
    def loadModel():
        return torch.hub.load('ultralytics/yolov5', 'custom', path='model/best.pt', source="local")

    @staticmethod
    def execByUrl(url, output_dir):
        model_yolo = KuzushijiOcr.loadModel()

        hs = hashlib.md5(url.encode()).hexdigest()
        path = "tmp/{}.jpg".format(hs)
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            request.urlretrieve(url, path)
  
        task = TaskImage(url, path, 1, "{url}/canvas/p{}".format(1))
        item = task.detect(model_yolo)
        items = [item]

        label = url
        manifest_uri = "{}/manifest.json".format(url)

        KuzushijiOcr.createManifest(manifest_uri, items, label, output_dir, hs)

    @staticmethod
    def execByManifest(url, output_dir, tmp_dir, thres=0.0, start=0, end=-1, sleep_time=0):
        
        model_yolo = KuzushijiOcr.loadModel()

        # hs = task_id # hashlib.md5(url.encode()).hexdigest()

        manifest_path = "{}/manifest.json".format(tmp_dir)
        
        manifest = Common.getJson(url, manifest_path)

        canvases = manifest["sequences"][0]["canvases"]

        items = []

        for i in tqdm(range(start, end + 1)):

            # for i in tqdm(range(len(canvases))):

            if start <= i and (end == -1 or i <= end):
                pass
            else:
                continue

            index = str(i + 1).zfill(4)
            # print(i)

            canvas = canvases[i]
            canvas_id = canvas["@id"]

            url_img = canvas["images"][0]["resource"]["service"]["@id"] + "/full/full/0/default.jpg"

            path = "{}/img/{}.jpg".format(tmp_dir, index)
            if not os.path.exists(path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                time.sleep(sleep_time)
                request.urlretrieve(url_img, path)

            service = None
            if "service" in canvas["images"][0]["resource"]:
                service = canvas["images"][0]["resource"]["service"]["@id"]

            task = TaskImage(url_img, path, int(index), canvas_id, service)
            item = task.detect(model_yolo, thres=thres)
            items.append(item)

        label = manifest["label"]
        manifest_uri = manifest["@id"]

        # m_data = KuzushijiOcr.createManifest(manifest_uri, items, label, output_dir, hs)
        m_data = KuzushijiOcr.createManifest(manifest_uri, items, label, output_dir)
        
        # キュレーションへの変換
        curation = Converter.convertManifest2Curation(m_data)

        '''
        opath = "{}/{}/detection.json".format(output_dir, hs)
        '''
        opath = "{}/curation.json".format(output_dir)
        os.makedirs(os.path.dirname(opath), exist_ok=True)

        with open(opath, 'w') as outfile:
            json.dump(curation, outfile)

    @staticmethod
    def test(url, output_dir, thres=0.0):

        hs = hashlib.md5(url.encode()).hexdigest()

        path = "/Users/nakamura/git/genji/kuzushiji_ocr/output/5361f893208b0c7f853ea1d0552a9e1a/manifest.json"
        with open(path) as f:
            m_data = json.load(f)

        # キュレーションへの変換
        curation = Converter.convertManifest2Curation(m_data)

        opath = "{}/{}/detection.json".format(output_dir, hs)
        os.makedirs(os.path.dirname(opath), exist_ok=True)

        with open(opath, 'w') as outfile:
            json.dump(curation, outfile)

        import pprint
        pprint.pprint(curation)




