from KuzushijiOcr import KuzushijiOcr

# url = "https://kotenseki.nijl.ac.jp/api/iiif/100179206/v4/0020/0020-52202/0020-52202-0003.tif/full/full/0/default.jpg"
url = "https://gist.githubusercontent.com/nakamura196/c83367eb3a415bad3195b143125821eb/raw/e2a5b45f5fed0d84374837075ac62702c5318c08/manifest.json"
output_dir = "./output"

# KuzushijiOcr.execByUrl(url, output_dir)
KuzushijiOcr.execByManifest(url, output_dir)

'''
ins = KuzushijiOcr()
print(ins.detect("test.png"))
'''