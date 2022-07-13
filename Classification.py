
import keras.models
import json
import hashlib
import os
from urllib import request
from PIL import Image
import numpy as np
import codecs
import shutil
from tqdm import tqdm
from Converter import Converter
from Common import Common

imsize = (64, 64)

json_open = open("model/labels.json", 'r')
labels = json.load(json_open)

model = keras.models.load_model("model/model.h5")

debug = False

predict_size = 5

def load_image(img, xywh, r = 1):
    x = int(int(xywh[0]) * r)
    y = int(int(xywh[1]) * r)
    w = int(int(xywh[2]) * r)
    h = int(int(xywh[3]) * r)
    im_crop = img.crop((x, y, x+w, y+h))

    img = im_crop.convert('RGB')
    # 学習時に、(64, 64, 3)で学習したので、画像の縦・横は今回 変数imsizeの(64, 64)にリサイズします。
    img = img.resize(imsize)

    # 画像データをnumpy配列の形式に変更
    img_np = np.asarray(img)
    img_np = img_np / 255.0
    return img_np, img, x, y

def predict(img):
    prd = model.predict(np.array([img]), verbose=0)

    
    y_preds = np.argsort(prd, axis=1)[:, -predict_size:]

    prelabels = y_preds[0]

    values = []

    for prelabel in prelabels:
        code = labels[prelabel].replace("U+", "\\u")
        s_from_s_codecs = codecs.decode(code, 'unicode-escape')

        values.append({
            "label": s_from_s_codecs,
            "score": round(prd[0][prelabel] * 100, 2)
        })

    return {
        "detail" : values, # value + " - " + ", ".join(values), # ""
        "marker" : values[-1]["label"] # s_from_s_codecs_top
    }

class Classification:
    @staticmethod
    def exec(output_dir, manifest_path, tmp_dir, start=0, end=-1):

        o_dir = "{}/chars".format(tmp_dir)
        if os.path.exists(o_dir):
            shutil.rmtree(o_dir)

        anno_index = 0
        
        

        prediction_result = {}

        # start = 0 if start < 1 else start - 1
        # end = len(canvases) if end == -1 else end - 1

        # 注意。アノテーション付きのマニフェスト。
        with open(manifest_path, 'r') as f:
            m_data = json.load(f)

        items = m_data["items"]

        itemMap = {}
        for item in items:
            itemMap[item["id"]] = item

        # 注意2。オリジナルのマニフェスト。
        url = m_data["id"]
        original_manifest_path = "{}/manifest.json".format(tmp_dir)
        
        manifest = Common.getJson(url, original_manifest_path)

        canvases = manifest["sequences"][0]["canvases"]

        

        for i in tqdm(range(start, end + 1)):
            if start <= i and (end == -1 or i <= end):
                pass
            else:
                continue

            # index = str(i + 1).zfill(4)
            # print(i)

            canvas = canvases[i]
            canvas_id = canvas["@id"]

            if canvas_id not in itemMap:
                continue

            item = itemMap[canvas_id]

            # for i in tqdm(range(len(items))):
            # item = items[i]
            
            page = str(i + 1).zfill(4)

            path = "{}/img/{}.jpg".format(tmp_dir, page)
            if not os.path.exists(path):
                '''
                os.makedirs(os.path.dirname(path), exist_ok=True)
                url_img = item["items"][0]["items"][0]["body"]["id"]
                request.urlretrieve(url_img, path)
                '''
                continue
            
            base_img = Image.open(path)

            w, h = base_img.size

            r = w / item["width"]

            anno_list = item["annotations"][0]["items"]
            
            for a in anno_list:
                anno_index += 1
                
                member_id = a["target"]
                spl = member_id.split("#xywh=")

                xywh = spl[1].split(",")

                img_np, img_crop, x, y = load_image(base_img, xywh, r)

                p = predict(img_np)
                prediction_result[member_id] = p

                if debug:
                    basename = "{}-{}-{}-{}.jpg".format(str(page).zfill(4), p["marker"] + "_" + str(anno_index).zfill(5), str(w-x).zfill(5), str(y).zfill(5))
                    t_path = "{}/chars/{}".format(tmp_dir, basename)
                    os.makedirs(os.path.dirname(t_path), exist_ok=True)
                    img_crop.save(t_path)

        curation = Converter.convertManifest2Curation(m_data)

        for member in curation["selections"][0]["members"]:
            member_id = member["@id"]

            if member_id in prediction_result:
                label = prediction_result[member_id]

                chars = member["metadata"][0]["value"][0]["resource"]["chars"]

                region_score = chars.split("<br/>")[1]

                chars_mod = {
                    "detection_score": region_score,
                    "label_top": label["marker"],
                    "label_detail": label["detail"]
                }

                member["metadata"][0]["value"][0]["resource"]["chars"] = str(chars_mod)
                member["metadata"][0]["value"][0]["resource"]["marker"] = {
                    "text" : label["marker"]
                }

        opath = "{}/character.json".format(output_dir)
        os.makedirs(os.path.dirname(opath), exist_ok=True)

        with open(opath, 'w') as outfile:
            json.dump(curation, outfile)

        
