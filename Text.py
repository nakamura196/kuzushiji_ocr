import pprint
from urllib import request
from tqdm import tqdm
import requests
import os
import json
from bs4 import BeautifulSoup

# debug = False

# 行の開始xと終了xを求める
def getLines(width, hist, hist_value_mean):
    isLine = False

    lines = []

    line = {
        "x" : 0
    }

    for x in range(len(hist)):
        v = hist[x]

        # 下に転じる
        if v < hist_value_mean and isLine:
            isLine = False

            line = {
                "x" : x
            }

        # 上に転じる
        elif v > hist_value_mean and not isLine:
            isLine = True

            line["x2"] = x
            lines.append(line)

    if not isLine:
        line["x2"] = width
        lines.append(line)

    return lines

def getIdList(aidListByLines):
    idList = []

    for x in range(len(aidListByLines)):
        line = aidListByLines[len(aidListByLines) - x - 1]

        ids2 = []

        for y in sorted(line):
            values = line[y]
            for v in values:

                ids2.append(v["aid"])

        idList.append(ids2)

    return idList

# 行ごとのaidを求める
def getAidListByLines(boxes, lines):
    aidListByLines = []

    # 登録済みのaidを保持する
    dones = []

    for line in lines:
        center = (line["x"] + line["x2"]) / 2

        # y座標をキーとして、boxを格納する
        line2 = {}

        for box in boxes:
            aid = box["aid"]
            x = box["x"]
            y = box["y"]
            w = box["width"]

            box_center = x + w / 2

            # ボックスの中心が、行の中心より小さい場合
            if box_center < center and aid not in dones:
                if y not in line2:
                    line2[y] = []
                line2[y].append(box)
                dones.append(aid)

        if len(line2) > 0:

            aidListByLines.append(line2)

    # 漏れているaids
    missing_boxes = []
    for box in boxes:
        aid = box["aid"]
        if aid not in dones:
            missing_boxes.append(box)

    if len(missing_boxes) > 0:

        # y座標をキーとして、boxを格納する
        line2 = {}
        for box in missing_boxes:
            if box["y"] not in line2:
                line2[box["y"]] = []
            line2[box["y"]].append(box)
            # dones.append(aid)
        
        aidListByLines.append(line2)

    return aidListByLines

def getTotalXVar(members, indexes, idList):
    totalXVar = 0

    for i in range(len(idList)):
        idsByLine = idList[i]

        for j in range(1, len(idsByLine)):
            id = idsByLine[j]

            
            member_prev = members[indexes[idsByLine[j-1]]]
            member = members[indexes[id]]
            
            x_prev = int(member_prev["@id"].split("#xywh=")[1].split(",")[0])
            x = int(member["@id"].split("#xywh=")[1].split(",")[0])

            totalXVar += abs(x - x_prev)

    return totalXVar

# idsに基づき、membersを更新する
def updateMembers(members, indexes, ids):
    for i in range(len(ids)):
        idsByLine = ids[i]
        for j in range(len(idsByLine)):
            id = idsByLine[j]
            member = members[indexes[id]]
            # 先頭かつ次の行がある
            if j == 0 and i != 0:
                
                member["metadata"][0]["value"][0]["resource"]["marker"]["prev_line"] = ids[i-1][0]

            if j == 0 and i != len(ids) - 1:
                member["metadata"][0]["value"][0]["resource"]["marker"]["next_line"] = ids[i+1][0]
    
            if j != 0:
                member["metadata"][0]["value"][0]["resource"]["marker"]["prev"] = idsByLine[j - 1]

            if j != len(idsByLine) - 1:
                member["metadata"][0]["value"][0]["resource"]["marker"]["next"] = idsByLine[j + 1]

class Text:
    @staticmethod
    def exec(task_id, output_dir, curation):
        members = curation["selections"][0]["members"]
        
        canvases = {}
        indexes = {}

        for i in range(len(members)):
            member = members[i]
            member_id = member["@id"]
            spl = member_id.split("#xywh=")
            canvas = spl[0]
            xywh = spl[1].split(",")

            if canvas not in canvases:

                canvases[canvas] = {
                    "width" : member["width"],
                    "boxes" : []
                }

            # try:
            canvases[canvas]["boxes"].append({
                "aid": member["metadata"][0]["value"][0]["@id"],
                # "index" : i,
                "x" : int(xywh[0]),
                "y" : int(xywh[1]),
                "width" : int(xywh[2]),
                "height" : int(xywh[3]),
                # "text" : member["metadata"][0]["value"][0]["resource"]["marker"]["text"]
            })

            indexes[member["metadata"][0]["value"][0]["@id"]] = i

            '''
            except Exception as e:
                print(e)
                pass
            '''

        # print("Setting reading orders ...")
        for canvas in tqdm(canvases):

            boxes = canvases[canvas]["boxes"]

            width = canvases[canvas]["width"]

            # 画像の横幅に基づくヒストグラムを作成
            hist = []

            # 初期化
            for i in range(width + 1):
                hist.append(0)

            for box in boxes:
                x = box["x"]
                w = box["width"]
                # ボックスがある座標をヒストグラムに加算
                for i in range(x, x+w+1):
                    hist[i] += 1

            hist_value_min = 1000
            hist_value_max = 0

            for v in hist:
                if hist_value_min > v:
                    hist_value_min = v
                if hist_value_max < v:
                    hist_value_max = v
            
            totalXVar_min = 1000000
            ids_best = None
            # best_div = -1

            # テキストがある行と
            for div in [2, 4, 6, 8 , 10, 12, 14, 16]:

                hist_value_mean = (hist_value_max + hist_value_min) / div

                # 行の開始xと終了xを求める
                lines = getLines(width, hist, hist_value_mean)

                # 行ごとのaidを求める
                aidListByLines = getAidListByLines(boxes, lines)
                # print(aidListByLines)

                idList = getIdList(aidListByLines)

                # 行ごとの横方向のばらつきを取得する
                totalXVar = getTotalXVar(members, indexes, idList)

                if totalXVar_min > totalXVar:
                    totalXVar_min = totalXVar
                    ids_best = idList
                    # best_div = div

            # idsに基づき、membersを更新する
            updateMembers(members, indexes, ids_best)
        
        import json
        import os

        opath = "{}/{}/text.json".format(output_dir, task_id)
        os.makedirs(os.path.dirname(opath), exist_ok=True)

        with open(opath, 'w') as outfile:
            json.dump(curation, outfile, ensure_ascii=False,
            indent=4, sort_keys=True, separators=(',', ': '))

        items = Text.convert2text(curation, task_id)

        # 全体テキスト
        txt = ""
        
        # XML
        xml_all = '''<?xml version='1.0' encoding='utf-8'?>
<OCRDATASET></OCRDATASET>'''
        soup = BeautifulSoup(xml_all,'xml')
        OCRDATASET = soup.find("OCRDATASET")

        mpath = "{}/{}/manifest.json".format(output_dir, task_id)
        with open(mpath, 'r') as f:
            manifest3_org = json.load(f)

        for i in range(len(items)):
            index = str(i + 1).zfill(4)
            opath = "{}/{}/txt/{}.txt".format(output_dir, task_id, index)

            os.makedirs(os.path.dirname(opath), exist_ok=True)
            item = items[i]
            data = item["data"]
            with open(opath, 'w') as outfile:
                outfile.write("\n".join(data))
            
            # 全体テキスト
            txt += "\n".join(data)

            page = soup.new_tag("PAGE")
            page["IMAGENAME"] = "{}.jpg".format(index)

            annos = []
            canvas = manifest3_org["items"][i]

            # 行ごと
            for j in range(len(data)):
                line = soup.new_tag("LINE")
                line["STRING"] = data[j]
                page.append(line)

                x_min = 100000000
                y_min = 100000000
                x_max = 0
                y_max = 0

                xywhs = item["xywhs"][j]
                for xywh in xywhs:
                    x, y, w, h = xywh.split(",")
                    x = int(x)
                    y = int(y)
                    x2 = x + int(w)
                    y2 = y + int(h)
                    
                    if x_min > x:
                        x_min = x
                    if y_min > y:
                        y_min = y
                    if x_max < x2:
                        x_max = x2
                    if y_max < y2:
                        y_max = y2

                line["X"] = x_min
                line["Y"] = y_min
                line["WIDTH"] = x_max - x_min
                line["HEIGHT"] = y_max - y_min

                
                canvas_id = canvas["id"]

                anno = {
                    "id": "{}/annos/{}".format(canvas_id, j+1),
                    "motivation": "commenting",
                    "target": "{}#xywh={},{},{},{}".format(canvas_id, x_min, y_min, x_max - x_min, y_max - y_min),
                    "type": "Annotation",
                    "body": {
                        "type": "TextualBody",
                        "value": data[j]
                    }
                }
                annos.append(anno)

            OCRDATASET.append(page)

            
            canvas["annotations"][0]["items"] = annos
        

        # TXT
        opath = "{}/{}/all.txt".format(output_dir, task_id)
        with open(opath, 'w') as outfile:
            outfile.write(txt)

        # XML
        html = soup.prettify("utf-8")

        opath = "{}/{}/all.xml".format(output_dir, task_id)
        # os.makedirs(os.path.dirname(opath), exist_ok=True)
        with open(opath, "wb") as file:
            file.write(html)

        # manifest
        opath = "{}/{}/line.json".format(output_dir, task_id)
        os.makedirs(os.path.dirname(opath), exist_ok=True)

        with open(opath, 'w') as outfile:
            json.dump(manifest3_org, outfile, ensure_ascii=False,
            indent=4, sort_keys=True, separators=(',', ': '))

    
    @staticmethod
    def convert2text(curation, task_id):
        manifest = curation["selections"][0]["within"]["@id"]

        opath = "tmp/{}/manifest.json".format(task_id)

        if not os.path.exists(opath):
            df = requests.get(manifest).json()
            with open(opath, 'w') as outfile:
                json.dump(df, outfile, ensure_ascii=False,
                indent=4, sort_keys=True, separators=(',', ': '))
        
        with open(opath, 'r') as f:
            manifest = json.load(f)

        canvases = manifest["sequences"][0]["canvases"]

        members = curation["selections"][0]["members"]
        
        # canvas毎のテキストを取得
        member_map = {}
        canvas_map = {}

        for member in members:
            member_id = member["@id"]

            anno_id = member["metadata"][0]["value"][0]["@id"]

            marker = member["metadata"][0]["value"][0]["resource"]["marker"]
            marker["@id"] = anno_id

            member_map[anno_id] = marker # member

            member_id_spl = member_id.split("#xywh=")
            canvas_id = member_id_spl[0]

            if canvas_id not in canvas_map:
                canvas_map[canvas_id] = []
            canvas_map[canvas_id].append(member)

        canvas_text_map = []

        for canvas in canvases:
            canvas_id = canvas["@id"]

            data = []

            item = {
                "id": canvas_id,
                "data": data
            }

            # 空のページの場合
            if canvas_id not in canvas_map:
                canvas_text_map.append(
                    item
                )
                continue

            # 最初のノードを取得する
            start_node_id = None

            for member in canvas_map[canvas_id]:
                marker = member["metadata"][0]["value"][0]["resource"]["marker"]

                if "prev_line" not in marker and "next_line" in marker:
                    start_node_id = marker["@id"]
                    break

            # 一個しかない場合
            if not start_node_id:
                # print(canvas_map[canvas_id])
                member = canvas_map[canvas_id][0]
                item["data"].append(member["metadata"][0]["value"][0]["resource"]["marker"]["text"])
                xywh = member["@id"].split("#xywh=")[1]
                item["xywhs"] = {
                    0: [xywh]
                }
                canvas_text_map.append(
                    item
                )
                continue

            data = [""]
            xywhs = {}
            
            # IIIFキュレーションリストを再起的に処理する
            def handle(node_id, line_index):

                if line_index not in xywhs:
                    xywhs[line_index] = []
                
                node = member_map[node_id]

                xywhs[line_index].append(node["@id"].split("#xywh=")[1].split("#")[0])
                
                data[line_index] += node["text"]

                if "next" in node:
                    handle(node["next"], line_index)

                if "next_line" in node:
                    # 初期化
                    data.append("")
                    line_index += 1
                    handle(node["next_line"], line_index)

            handle(start_node_id, 0)

            # canvas_text_map[canvas_id] = data
            item["data"] = data
            item["xywhs"] = xywhs
            canvas_text_map.append(item)

            # print(xywhs)

            # break

        # pprint.pprint(canvas_text_map)

        return canvas_text_map
        
