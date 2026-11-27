"""Combine independently maintained, native X and Douyin workflows.
Run from the folder containing the two unsigned shortcut source files.
"""
from pathlib import Path
from copy import deepcopy
import plistlib,uuid
ROOT=Path(__file__).resolve().parent
A=[]
def token(v):return {'Value':v,'WFSerializationType':'WFTextTokenAttachment'}
def action(name,**p):
 u=str(uuid.uuid4()).upper();p['UUID']=u;A.append({'WFWorkflowActionIdentifier':'is.workflow.actions.'+name,'WFWorkflowActionParameters':p});return token({'Type':'ActionOutput','OutputUUID':u,'OutputName':p.get('CustomOutputName','Result')})
def text(v):return {'Value':{'string':'\ufffc','attachmentsByRange':{'{0, 1}':v['Value']}},'WFSerializationType':'WFTextTokenString'}
def start(v,label,condition=100,**kwargs):
 checked=action('gettext',WFTextActionText=text(v),CustomOutputName=label);checked['Value']['Aggrandizements']=[{'Type':'WFCoercionVariableAggrandizement','CoercionItemClass':'WFStringContentItem'}]
 g=str(uuid.uuid4()).upper();action('conditional',WFInput={'Type':'Variable','Variable':checked},WFCondition=condition,WFControlFlowMode=0,GroupingIdentifier=g,**kwargs);return g
def otherwise(g):action('conditional',WFControlFlowMode=1,GroupingIdentifier=g)
def end(g):action('conditional',WFControlFlowMode=2,GroupingIdentifier=g)
X_PATTERN=r'https?://(?:www\.)?(?:x\.com|twitter\.com)/(?:[A-Za-z0-9_]+|i/web)/status/[0-9]+'
DY_PATTERN=r'https?://(?:v\.douyin\.com/[A-Za-z0-9_-]+/?|(?:www\.)?douyin\.com/video/[0-9]+/?|(?:www\.)?iesdouyin\.com/share/video/[0-9]+/?)'
all_links=action('text.match',text=text(token({'Type':'ExtensionInput'})),WFMatchTextPattern='(?i)(?:'+X_PATTERN+'|'+DY_PATTERN+')',WFMatchTextCaseSensitive=False)
valid=start(all_links,'支持的平台链接')
selected=action('getitemfromlist',WFInput=all_links,WFItemSpecifier='First Item')
selected_text=action('gettext',WFTextActionText=text(selected),CustomOutputName='识别到的链接')
action('setvariable',WFInput=selected_text,WFVariableName='待解析链接')
selected=token({'Type':'Variable','VariableName':'待解析链接'})
# The allow-list above only accepts X status and Douyin work URLs. Inspect
# the original scalar link directly: no empty-match or replacement marker.
x_branch=start(selected,'待解析链接',condition=99,WFConditionalActionString={'Value':{'string':'/status/'},'WFSerializationType':'WFTextTokenString'})

def bind_input(v):
 if isinstance(v,dict):
  if v.get('Type')=='ExtensionInput':return deepcopy(selected['Value'])
  return {k:bind_input(z) for k,z in v.items()}
 if isinstance(v,list):return [bind_input(z) for z in v]
 return v

def append_branch(path,concretize=False):
 workflow=plistlib.loads((ROOT/path).read_bytes())
 for a in bind_input(workflow['WFWorkflowActions']):
  p=a['WFWorkflowActionParameters']
  # WFURL is a text parameter; keep the same token-string format as the
  # user-exported, device-tested X shortcut.
  if a['WFWorkflowActionIdentifier']=='is.workflow.actions.downloadurl' and isinstance(p.get('WFURL'),dict) and p['WFURL'].get('WFSerializationType')=='WFTextTokenAttachment':
   p['WFURL']=text(p['WFURL'])
  if concretize and a['WFWorkflowActionIdentifier']=='is.workflow.actions.conditional' and p['WFControlFlowMode']==0:
   # Match the explicit text conditions already validated on the user's iPhone.
   original=p['WFInput']['Variable']
   converted=action('gettext',WFTextActionText=text(original),CustomOutputName='X 判断文本')
   converted['Value']['Aggrandizements']=[{'Type':'WFCoercionVariableAggrandizement','CoercionItemClass':'WFStringContentItem'}]
   p['WFInput']={'Type':'Variable','Variable':converted}
  A.append(a)
 return workflow

# No shared setup requests: network access begins inside the selected branch.
append_branch('X-Working-unsigned.shortcut')
otherwise(x_branch)
dy=append_branch('Douyin-unsigned.shortcut')
end(x_branch)
otherwise(valid)
action('alert',WFAlertActionTitle='X·抖音保存',WFAlertActionMessage='未识别到支持的链接。请分享 X 帖子或抖音作品，或复制分享文案后运行。',WFAlertActionCancelButtonShown=False)
end(valid)
w={k:deepcopy(v) for k,v in dy.items() if k!='WFWorkflowActions'}
w['WFWorkflowName']='X·抖音保存';w['WFWorkflowActions']=A
w['WFWorkflowNoInputBehavior']={'Name':'WFWorkflowNoInputBehaviorGetClipboard','Parameters':{}}
w['WFWorkflowTypes']=['ActionExtension']
w['WFWorkflowInputContentItemClasses']=['WFStringContentItem','WFURLContentItem','WFRichTextContentItem','WFSafariWebPageContentItem']
(ROOT/'X-Douyin-unsigned.shortcut').write_bytes(plistlib.dumps(w,sort_keys=False))
print('Built unified shortcut:',len(A),'native actions; X and Douyin network operations are in separate branches.')
