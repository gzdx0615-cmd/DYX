"""Offline native-action checks, including service failure isolation.
This does not emulate Apple's import/signing/UI or Photos permissions.
"""
from pathlib import Path
import plistlib,re
W=plistlib.loads((Path(__file__).resolve().parent/'X-Douyin-unsigned.shortcut').read_bytes())
A=W['WFWorkflowActions'];F={};stack=[];seen=set()
def walk(v):
 if isinstance(v,dict):
  if 'OutputUUID' in v:assert v['OutputUUID'] in seen
  assert v.get('Type')!='CurrentRepeatItem'
  for z in v.values():walk(z)
 elif isinstance(v,list):
  for z in v:walk(z)
for i,a in enumerate(A):
 p=a['WFWorkflowActionParameters'];walk(p)
 if a['WFWorkflowActionIdentifier'] in ['is.workflow.actions.conditional','is.workflow.actions.repeat.each']:
  m=p['WFControlFlowMode'];g=p['GroupingIdentifier']
  if m==0:stack.append([i,None,g])
  elif m==1:assert stack[-1][2]==g;stack[-1][1]=i
  else:
   start,other,group=stack.pop();assert group==g;F[start]=(other,i)
   if other is not None:F[other]=i
 seen.add(p['UUID'])
assert not stack
assert W['WFWorkflowNoInputBehavior']['Name']=='WFWorkflowNoInputBehaviorGetClipboard'
assert 'ActionExtension' in W['WFWorkflowTypes']

def as_text(v):
 if v is None:return ''
 if isinstance(v,list):return '\n'.join(map(as_text,v))
 return str(v)
class Run:
 def __init__(self,share='',clipboard='',dy_down=False,x_down=False,album=False):
  self.input=share or clipboard;self.dy_down=dy_down;self.x_down=x_down;self.album=album
  self.variables={};self.outputs={};self.calls=[];self.saved=[];self.repeat=None;self.alerts=[]
 def value(self,v):
  if isinstance(v,list):return [self.value(z) for z in v]
  if not isinstance(v,dict):return v
  serial=v.get('WFSerializationType')
  if serial=='WFTextTokenAttachment':return self.value(v['Value'])
  if serial=='WFTextTokenString':
   s=v['Value']['string'];att=v['Value'].get('attachmentsByRange',{})
   for k,z in sorted(att.items(),key=lambda t:int(t[0][1:].split(',')[0]),reverse=True):
    pos=int(k[1:].split(',')[0]);s=s[:pos]+as_text(self.value(z))+s[pos+1:]
   return s
  typ=v.get('Type')
  if typ=='ExtensionInput':return self.input
  if typ=='ActionOutput':return self.outputs[v['OutputUUID']]
  if typ=='Variable':
   if 'Variable' in v:return self.value(v['Variable'])
   if v.get('VariableName')=='Repeat Item':return self.repeat
   if 'VariableName' in v:return self.variables[v['VariableName']]
  return {k:self.value(z) for k,z in v.items()}
 def network(self,url):
  assert isinstance(url,str) and url.startswith('https://'),url
  self.calls.append(url)
  if '/douyin.json' in url:
   if self.dy_down:raise RuntimeError('DY config offline')
   return {'parser_url':'https://dy-parser.example/?url=','user_agent':'test-UA','media_key':'data.media','messages':{'success':'saved','parse_failed':'no media'}}
  if 'api.fxtwitter.com' in url:
   if self.x_down:raise RuntimeError('X API offline')
   return {'status':{'media':{'videos':[{'url':'https://media.example/x.mp4'}]}}}
  if 'dy-parser.example' in url:
   return {'data':{'type':'images' if self.album else 'video','media':['https://media.example/1.jpg','https://media.example/2.jpg'] if self.album else ['https://media.example/dy.mp4']}}
  assert url.startswith('https://media.example/'),url
  return {'fileurl':url}
 def run(self,lo=0,hi=None):
  i=lo;hi=len(A) if hi is None else hi
  while i<hi:
   a=A[i];p=a['WFWorkflowActionParameters'];n=a['WFWorkflowActionIdentifier'].split('.')[-1];result=None
   if n=='conditional':
    mode=p['WFControlFlowMode']
    if mode==0:
     value=self.value(p['WFInput']);condition=p['WFCondition']
     comparison=self.value(p.get('WFConditionalActionString',''))
     ok=bool(value) if condition==100 else (comparison in as_text(value) if condition==99 else as_text(value)==comparison)
     if not ok:
      other,end=F[i];i=(other if other is not None else end)+1;continue
    elif mode==1:i=F[i]+1;continue
   elif n=='each':
    if p['WFControlFlowMode']==0:
     _,end=F[i];items=self.value(p['WFInput']);items=items if isinstance(items,list) else [items]
     for item in items:self.repeat=item;self.run(i+1,end)
     self.repeat=None;i=end+1;continue
   elif n=='match':result=re.findall(p['WFMatchTextPattern'],as_text(self.value(p.get('text',p.get('WFInput')))),re.I if not p.get('WFMatchTextCaseSensitive',True) else 0)
   elif n=='gettext':result=as_text(self.value(p['WFTextActionText']))
   elif n=='replace':
    replacement=re.sub(r'\$(\d+)',r'\g<\1>',p['WFReplaceTextReplace']) if '$' in p['WFReplaceTextReplace'] else p['WFReplaceTextReplace']
    result=re.sub(p['WFReplaceTextFind'],replacement,as_text(self.value(p['WFInput'])))
   elif n=='getitemfromlist':
    values=self.value(p['WFInput']);result=values[0] if isinstance(values,list) else values
   elif n=='setvariable':
    result=self.value(p['WFInput']);self.variables[p['WFVariableName']]=result
   elif n=='downloadurl':
    raw_url=p['WFURL'];assert isinstance(raw_url,str) or raw_url.get('WFSerializationType')=='WFTextTokenString', 'WFURL must be native text parameter, not a generic attachment'
    result=self.network(self.value(raw_url))
   elif n=='getvalueforkey':
    result=self.value(p['WFInput'])
    for part in self.value(p['WFDictionaryKey']).split('.'):
     result=result.get(part) if isinstance(result,dict) else None
   elif n=='savetocameraroll':result=self.value(p['WFInput']);self.saved.append(result)
   elif n=='alert':self.alerts.append(self.value(p.get('WFAlertActionMessage')))
   elif n=='notification':pass
   else:raise AssertionError(n)
   self.outputs[p['UUID']]=result;i+=1
  return self
X='https://x.com/example/status/123/video/1?s=46'
DY='4.89 复制打开抖音 https://v.douyin.com/EXAMPLE_ALBUM/ qRK:/'
for kwargs in [{'share':X},{'clipboard':X},{'share':X,'clipboard':DY}]:
 r=Run(**kwargs,dy_down=True).run();assert len(r.saved)==1;assert all('/douyin.json' not in u and 'dy-parser' not in u for u in r.calls)
for kwargs in [{'share':DY},{'clipboard':DY},{'share':DY,'clipboard':X}]:
 r=Run(**kwargs,x_down=True).run();assert len(r.saved)==1;assert not any('fxtwitter' in u for u in r.calls)
r=Run(clipboard=DY,x_down=True,album=True).run();assert len(r.saved)==2
for invalid in ['', 'https://example.com/', 'https://x.com.evil.example/u/status/1234']:
 r=Run(clipboard=invalid).run();assert not r.calls and r.alerts
r=Run(clipboard=DY+' '+X).run();assert not any('fxtwitter' in u for u in r.calls)
r=Run(clipboard=X+' '+DY).run();assert not any('/douyin.json' in u for u in r.calls)
print('PASS: source structure; shared/clipboard routing; share precedence; gallery loop; invalid links; first-link selection; DY-offline/X-offline isolation.')

# Preserve the device-tested X branch exactly, except binding its input to
# the explicit router variable. Reject the earlier URL parameter encoding.
known=plistlib.loads((Path(__file__).resolve().parent/'X-Working-unsigned.shortcut').read_bytes())
by_id={a['WFWorkflowActionParameters']['UUID']:a for a in A}
for original in known['WFWorkflowActions']:
 found=by_id[original['WFWorkflowActionParameters']['UUID']]
 if original['WFWorkflowActionIdentifier']=='is.workflow.actions.downloadurl':
  assert found==original
assert any(a['WFWorkflowActionIdentifier']=='is.workflow.actions.setvariable' and a['WFWorkflowActionParameters'].get('WFVariableName')=='待解析链接' for a in A)
print('PASS: native URL text parameters, named router input, and unchanged known-working X download actions.')

# Routing must use scalar equality, never 'has any value' on X matches.
routes=[a['WFWorkflowActionParameters'] for a in A if a['WFWorkflowActionIdentifier']=='is.workflow.actions.conditional' and a['WFWorkflowActionParameters'].get('WFConditionalActionString',{}).get('Value',{}).get('string')=='/status/']
assert len(routes)==1 and routes[0]['WFCondition']==99
for link in [DY,'https://v.douyin.com/EXAMPLE_LIVE/','https://www.douyin.com/video/456','https://www.iesdouyin.com/share/video/456/']:
 r=Run(clipboard=link,x_down=True).run();assert not any('fxtwitter' in u for u in r.calls)
original_as_text=as_text
def nonempty_empty_list(value):return '[empty match result]' if value==[] else original_as_text(value)
as_text=nonempty_empty_list
r=Run(clipboard=DY,x_down=True).run();assert r.saved and not any('fxtwitter' in u for u in r.calls)
as_text=original_as_text
print('PASS: native substring routing on original URL; DY isolation with nonempty empty-match coercion.')

assert not any(a['WFWorkflowActionIdentifier']=='is.workflow.actions.text.replace' for a in A)
for url in [X,'https://twitter.com/user/status/1234567890','https://x.com/i/web/status/1234567890']:
 r=Run(share=url,dy_down=True).run();assert r.saved and not any('/douyin.json' in u for u in r.calls)
print('PASS: both X hosts use /status/ routing with explicit native text comparison parameter.')
