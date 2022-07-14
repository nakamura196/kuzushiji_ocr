from OcrTask import OcrTask
url = "https://www.dl.ndl.go.jp/api/iiif/2591006/manifest.json"
output_dir = "./output"
start = 2
end = 4
sleep_time = 0
task_id = "ndl_2591006"

thres = 0.6

task = OcrTask(url, output_dir, start, end, sleep_time, task_id)
task.kuzushijiOcrByManifest()
task.classification()
task.text()