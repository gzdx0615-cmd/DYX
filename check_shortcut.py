import plistlib,re,json
from pathlib import Path
root=Path(__file__).resolve().parent
w=plistlib.loads((root/'Douyin-unsigned.shortcut').read_bytes())
seen=set();stack=[]
def walk(v):
 if isinstance(v,dict):
  if 'OutputUUID' in v:assert v['OutputUUID'] in seen, 'Unresolved action output'
  for z in v.values():walk(z)
 elif isinstance(v,list):
  for z in v:walk(z)
for a in w['WFWorkflowActions']:
 p=a['WFWorkflowActionParameters'];walk(p)
 if a['WFWorkflowActionIdentifier']=='is.workflow.actions.conditional':
  mode=p['WFControlFlowMode'];g=p['GroupingIdentifier']
  if mode==0:stack.append(g)
  elif mode==1:assert stack[-1]==g
  else:assert stack.pop()==g
 seen.add(p['UUID'])
assert not stack
pat=w['WFWorkflowActions'][0]['WFWorkflowActionParameters']['WFMatchTextPattern']
samples=['9.23 复制打开抖音 https://v.douyin.com/EXAMPLE_VIDEO/ 06/25','https://www.douyin.com/video/456?foo=bar','https://www.iesdouyin.com/share/video/456/']
for s in samples:assert re.search(pat,s,re.I)
for s in ['https://example.com/','https://x.com/example/status/123','https://v.douyin.com.evil.example/123/','https://www.douyin.com/user/123']:assert not re.search(pat,s,re.I)
assert w['WFWorkflowNoInputBehavior']['Name']=='WFWorkflowNoInputBehaviorGetClipboard'
assert 'ActionExtension' in w['WFWorkflowTypes']
s=json.dumps(w,ensure_ascii=False)
for text in ['疯果','公众号','data.version','icloud.com/shortcuts']:assert text not in s
print('PASS: plist, output references, nested conditionals, 7 URL cases, share/clipboard input, no branding/update gate.')

urls=[a['WFWorkflowActionParameters'].get('WFURL') for a in w['WFWorkflowActions']]
assert 'https://v4.gh-proxy.org/https://raw.githubusercontent.com/gzdx0615-cmd/DYX/main/douyin.json' in urls
print('PASS: config uses the intended GitHub proxy URL.')

# Check repeat nesting and current-item bindings as well as conditionals.
stack=[]
repeat_groups=set()
for a in w['WFWorkflowActions']:
 p=a['WFWorkflowActionParameters'];name=a['WFWorkflowActionIdentifier']
 if name in ['is.workflow.actions.conditional','is.workflow.actions.repeat.each']:
  mode=p['WFControlFlowMode'];group=p['GroupingIdentifier']
  if mode==0:
   stack.append((name,group))
   if name.endswith('repeat.each'):repeat_groups.add(group)
  elif mode==1:assert stack[-1]==(name,group)
  elif mode==2:assert stack.pop()==(name,group)
assert not stack and len(repeat_groups)==1
for a in w['WFWorkflowActions']:
 if a['WFWorkflowActionIdentifier']=='is.workflow.actions.downloadurl':
  url=a['WFWorkflowActionParameters'].get('WFURL')
  if isinstance(url,dict):
   for v in url.get('Value',{}).get('attachmentsByRange',{}).values():
    assert v.get('Type')!='CurrentRepeatItem', 'Unsupported repeat token encoding'
    if v.get('VariableName')=='Repeat Item':assert v['Type']=='Variable'
print('PASS: gallery repeat nesting and per-item binding.')

# A valid group UUID alone does not make a valid Apple built-in variable.
repeat_downloads=[]
for a in w['WFWorkflowActions']:
 if a['WFWorkflowActionIdentifier']=='is.workflow.actions.downloadurl':
  url=a['WFWorkflowActionParameters'].get('WFURL',{})
  if isinstance(url,dict):
   for value in url.get('Value',{}).get('attachmentsByRange',{}).values():
    if value.get('VariableName')=='Repeat Item':repeat_downloads.append(value)
assert len(repeat_downloads)==1
assert repeat_downloads[0]=={'Type':'Variable','VariableName':'Repeat Item'}
assert 'CurrentRepeatItem' not in json.dumps(w)
print('PASS: per-item download uses Apple Repeat Item built-in variable format.')
