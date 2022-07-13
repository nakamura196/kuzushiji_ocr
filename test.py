from OcrTask import OcrTask

# url = "https://kotenseki.nijl.ac.jp/api/iiif/100179206/v4/0020/0020-52202/0020-52202-0003.tif/full/full/0/default.jpg"
# url = "https://gist.githubusercontent.com/nakamura196/c83367eb3a415bad3195b143125821eb/raw/e2a5b45f5fed0d84374837075ac62702c5318c08/manifest.json"
# url = "https://clioapi.hi.u-tokyo.ac.jp/iiif/81/adata/bd1/BD2017-016900/1/manifest"
url = "https://genji.dl.itc.u-tokyo.ac.jp/data/iiif/org/%E6%9D%B1%E5%A4%A7%E6%9C%AC/01/manifest.json"
output_dir = "./output"
start = 1
end = 5 # -1
sleep_time = 0
task_id = "genji2"

process_range = [0, 1, 2]

# thres = 0.6
thres = 0.6

task = OcrTask(url, output_dir, start, end, sleep_time, task_id)
task.kuzushijiOcrByManifest()
task.classification()
task.text()