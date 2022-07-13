from KuzushijiOcr import KuzushijiOcr
# from Classification import Classification
from Text import Text
import hashlib

# url = "https://kotenseki.nijl.ac.jp/api/iiif/100179206/v4/0020/0020-52202/0020-52202-0003.tif/full/full/0/default.jpg"
# url = "https://gist.githubusercontent.com/nakamura196/c83367eb3a415bad3195b143125821eb/raw/e2a5b45f5fed0d84374837075ac62702c5318c08/manifest.json"
url = "https://clioapi.hi.u-tokyo.ac.jp/iiif/81/adata/bd1/BD2017-016900/1/manifest"
output_dir = "./output"

# thres = 0.6
thres = 0.6

# KuzushijiOcr.execByUrl(url, output_dir)

hs = hashlib.md5(url.encode()).hexdigest()

main_dir = "{}/{}".format(output_dir, hs)

print("### 文字領域検出を開始します。 ###")
# KuzushijiOcr.execByManifest(url, output_dir, thres=thres)

path = main_dir + "/manifest.json"

# path = "/Users/nakamura/git/genji/kuzushiji_ocr/output/5361f893208b0c7f853ea1d0552a9e1a/manifest.json"
import json
with open(path) as f:
    m_data = json.load(f)

print("### 文字認識を開始します。 ###")
# Classification.exec(url, output_dir, m_data)

'''
ins = KuzushijiOcr()
print(ins.detect("test.png"))
'''

print("### 行検出を開始します。 ###")

curation_path = "{}/{}/character.json".format(output_dir, hs)

with open(curation_path) as f:
    curation = json.load(f)

Text.exec(hs, output_dir, curation)