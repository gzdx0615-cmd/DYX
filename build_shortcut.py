"""Build the native, unsigned Apple Shortcut using only Python's standard library."""
from pathlib import Path
import plistlib,uuid
ROOT=Path(__file__).resolve().parent
CONFIG_URL='https://v4.gh-proxy.org/https://raw.githubusercontent.com/gzdx0615-cmd/DYX/main/douyin.json'
A=[]
def action(name,**p):
 u=str(uuid.uuid4()).upper();p['UUID']=u
 A.append({'WFWorkflowActionIdentifier':'is.workflow.actions.'+name,'WFWorkflowActionParameters':p})
 return token({'Type':'ActionOutput','OutputUUID':u,'OutputName':'Result'})
def token(value):return {'Value':value,'WFSerializationType':'WFTextTokenAttachment'}
def textvar(v):return {'Value':{'string':'\ufffc','attachmentsByRange':{'{0, 1}':v['Value']}},'WFSerializationType':'WFTextTokenString'}
def concat(*vs):
 s='';attachments={}
 for v in vs:
  if isinstance(v,str):s+=v
  else:attachments['{%d, 1}'%len(s)]=v['Value'];s+='\ufffc'
 return {'Value':{'string':s,'attachmentsByRange':attachments},'WFSerializationType':'WFTextTokenString'}
def key(v,k):return action('getvalueforkey',WFInput=v,WFDictionaryKey=k,WFGetDictionaryValueType='Value')
def start(v,condition=100,label='判断文本',**kwargs):
 # Dictionary outputs have an unknown type until runtime. Give iOS a concrete
 # text output before it validates the condition's required parameters.
 checked=action('gettext',WFTextActionText=textvar(v),CustomOutputName=label)
 checked['Value']['OutputName']=label
 checked['Value']['Aggrandizements']=[{'Type':'WFCoercionVariableAggrandizement','CoercionItemClass':'WFStringContentItem'}]
 g=str(uuid.uuid4()).upper();action('conditional',WFInput={'Type':'Variable','Variable':checked},WFCondition=condition,WFControlFlowMode=0,GroupingIdentifier=g,**kwargs);return g
def otherwise(g):action('conditional',WFControlFlowMode=1,GroupingIdentifier=g)
def end(g):action('conditional',WFControlFlowMode=2,GroupingIdentifier=g)
def alert(msg):action('alert',WFAlertActionTitle='抖音视频保存',WFAlertActionMessage=textvar(msg) if isinstance(msg,dict) else msg,WFAlertActionCancelButtonShown=False)
def headers(ua):
 return {'Value':{'WFDictionaryFieldValueItems':[{'WFKey':{'Value':{'string':'User-Agent'},'WFSerializationType':'WFTextTokenString'},'WFItemType':0,'WFValue':textvar(ua)}]},'WFSerializationType':'WFDictionaryFieldValue'}
source=token({'Type':'ExtensionInput'})
pattern=r'https?://(?:v\.douyin\.com/[A-Za-z0-9_-]+/?|(?:www\.)?douyin\.com/video/[0-9]+/?|(?:www\.)?iesdouyin\.com/share/video/[0-9]+/?)'
matches=action('text.match',text=textvar(source),WFMatchTextPattern=pattern,WFMatchTextCaseSensitive=False)
g1=start(matches,label='分享链接匹配结果')
link=action('getitemfromlist',WFInput=matches,WFItemSpecifier='First Item')
cfg=action('downloadurl',WFURL=CONFIG_URL,WFHTTPMethod='GET')
base=key(cfg,'parser_url');ua=key(cfg,'user_agent');media_key=key(cfg,'media_key')
g2=start(base,label='解析接口地址')
result=action('downloadurl',WFURL=concat(base,link),WFHTTPMethod='GET',WFHTTPHeaders=headers(ua),ShowHeaders=True)
kind=key(result,'data.type')
supported=action('text.match',text=textvar(kind),WFMatchTextPattern='^(video|images)$',WFMatchTextCaseSensitive=False)
g3=start(supported,label='支持的作品类型')
media=key(result,textvar(media_key))
g4=start(media,label='下载地址列表')
# The provider flattens live images into alternating still/movie URLs.
# Save all components, but never describe them as a paired Apple Live Photo.
is_gallery=action('text.match',text=textvar(kind),WFMatchTextPattern='^images$',WFMatchTextCaseSensitive=False)
gallery_guard=start(is_gallery,label='图集类型')
movies=action('text.match',text=textvar(media),WFMatchTextPattern='(?i)https?://[^\\s]*mime_type=video_mp4[^\\s]*',WFMatchTextCaseSensitive=False)
live_guard=start(movies,label='实况动态片段')
action('alert',WFAlertActionTitle='保存实况素材',WFAlertActionMessage='检测到图片和动态视频，将分别保存到相册，不会合成为可长按播放的 Live Photo。',WFAlertActionCancelButtonShown=True)
end(live_guard)
end(gallery_guard)
repeat_id=str(uuid.uuid4()).upper()
action('repeat.each',WFInput=media,WFControlFlowMode=0,GroupingIdentifier=repeat_id)
item=token({'Type':'Variable','VariableName':'Repeat Item'})
file=action('downloadurl',WFURL=textvar(item),WFHTTPMethod='GET')
saved=action('savetocameraroll',WFInput=file)
action('repeat.each',WFControlFlowMode=2,GroupingIdentifier=repeat_id)
success=key(cfg,'messages.success')
action('notification',WFNotificationActionBody=textvar(success),WFNotificationActionTitle='抖音视频保存')
otherwise(g4);err=key(cfg,'messages.parse_failed');alert(err);end(g4)
otherwise(g3);alert('未获取到支持的视频或图集，请检查作品是否公开或稍后重试。');end(g3)
otherwise(g2);alert('远程配置缺少 parser_url，请检查 GitHub 中的 douyin.json。');end(g2)
otherwise(g1);alert('未识别到抖音链接，请复制作品分享文案后重试。');end(g1)
w={'WFWorkflowName':'抖音视频保存','WFWorkflowMinimumClientVersionString':'900','WFWorkflowMinimumClientVersion':900,'WFWorkflowClientVersion':'3036.0.4.2','WFWorkflowClientRelease':'18.0','WFWorkflowIcon':{'WFWorkflowIconStartColor':4282601983,'WFWorkflowIconGlyphNumber':59767},'WFWorkflowActions':A,'WFWorkflowNoInputBehavior':{'Name':'WFWorkflowNoInputBehaviorGetClipboard','Parameters':{}},'WFWorkflowHasOutputFallback':False,'WFWorkflowOutputContentItemClasses':[],'WFWorkflowInputContentItemClasses':['WFStringContentItem','WFURLContentItem','WFSafariWebPageContentItem','WFRichTextContentItem'],'WFWorkflowImportQuestions':[],'WFQuickActionSurfaces':[],'WFWorkflowTypes':['ActionExtension'],'WFWorkflowHasShortcutInputVariables':True}
path=ROOT/'Douyin-unsigned.shortcut';path.write_bytes(plistlib.dumps(w,sort_keys=False));print('Built',len(A),'native actions:',path.name)
