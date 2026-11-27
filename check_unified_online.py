"""Exercise generated action data with real HTTP and media file validation.
Not an Apple Shortcuts runtime: does not validate signing, UI or Photos writes.
"""
from pathlib import Path
import runpy,urllib.request,urllib.parse,json,hashlib,subprocess,io
from PIL import Image
M=runpy.run_path(str(Path(__file__).with_name('check_unified.py')))
Base=M['Run'];ROOT=Path(__file__).resolve().parent.parent/'unified-online';ROOT.mkdir(exist_ok=True)
cache={}
class Online(Base):
 def network(self,url):
  assert isinstance(url,str) and url.startswith('https://'), 'Expected HTTPS media URL'
  self.calls.append(url)
  if url in cache:return cache[url]
  headers={}
  if 'douyin.the847696611.top' in url:
   cfg=next(v for k,v in cache.items() if '/douyin.json' in k);headers={'User-Agent':cfg['user_agent']}
  req=urllib.request.Request(url,headers=headers)
  with urllib.request.urlopen(req,timeout=35) as r:
   b=r.read();mime=r.headers.get('Content-Type','').lower()
   if '/douyin.json' in url or 'api.fxtwitter.com/' in url or 'douyin.the847696611.top/' in url:
    result=json.loads(b)
   else:
    assert b and not mime.startswith('text/'), 'Expected media response'
    path=ROOT/(hashlib.sha256(url.encode()).hexdigest()[:16]+('.mp4' if 'video' in mime else '.image'));path.write_bytes(b)
    if 'video' in mime:
     q=json.loads(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type','-of','json',str(path)],capture_output=True,text=True,check=True).stdout);assert any(s['codec_type']=='video' for s in q['streams'])
    else:
     image=Image.open(io.BytesIO(b));image.verify()
    result={'fileurl':url,'path':str(path),'bytes':len(b),'mime':mime}
  cache[url]=result;return result
# Never commit a real user's links as fixtures. Supply local private cases.
import argparse
parser=argparse.ArgumentParser(description='Use local, private test links; never commit them.')
parser.add_argument('--private-cases',required=True,help='Local JSON list of [label, URL, expected_count, platform]; keep outside the repo')
args=parser.parse_args()
cases=json.loads(Path(args.private_cases).read_text())

report=[]
for name,link,count,platform in cases:
 for entry in ['share','clipboard']:
  run=Online(**{entry:link}).run();assert len(run.saved)==count,(name,entry,run.alerts,run.saved)
  if platform=='X':assert not any('/douyin.json' in u or 'douyin.the847696611.top' in u for u in run.calls)
  else:assert not any('fxtwitter.com' in u for u in run.calls)
  report.append({'case':'private case','entry':entry,'downloaded':len(run.saved),'bytes':sum(v['bytes'] for v in run.saved),'status':'PASS (HTTP + generated-action simulation, not iOS)'})
  print(json.dumps(report[-1],ensure_ascii=False),flush=True)
(ROOT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('All 8 data paths passed. Apple Shortcuts and Photos remain untested.')
