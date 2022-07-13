from KuzushijiOcr import KuzushijiOcr
from Classification import Classification
from Text import Text
import os
import datetime
import pytz

class OcrTask:
    def __init__(self, url, output_dir, start, end, sleep_time, task_id, thres=0.0):
        self.url = url
        self.output_dir = output_dir
        self.start = 0 if start < 1 else start - 1 # start
        self.end = -1 if end == -1 else end - 1 # end
        self.sleep_time = sleep_time
        self.task_id = task_id
        self.thres = thres
        main_dir = "{}/{}".format(output_dir, task_id)
        if os.path.exists(main_dir):
          run_id = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y%m%d%H%M%S')
          task_id = "{}_{}".format(task_id, run_id)
          print("### タスクIDが重複するため、{}に変更します。 ###".format(task_id))
          self.task_id = task_id
        self.main_dir = "{}/{}".format(output_dir, task_id) # main_dir 
        self.manifest_path = "{}/manifest.json".format(self.main_dir)
        self.tmp_dir = "tmp/{}".format(task_id)

    def kuzushijiOcrByManifest(self):
        print("### 文字領域検出を開始します。 ###")
        KuzushijiOcr.execByManifest(self.url, self.main_dir, self.tmp_dir, thres=self.thres, start=self.start, end=self.end, sleep_time=self.sleep_time)

    def classification(self):
        print("### 文字認識を開始します。 ###")
        Classification.exec(self.main_dir, self.manifest_path, self.tmp_dir, start=self.start, end=self.end)

    def text(self):
        print("### 行検出を開始します。 ###")
        curation_path = "{}/character.json".format(self.main_dir)
        Text.exec(self.main_dir, curation_path, self.tmp_dir)