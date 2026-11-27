from pathlib import Path
import uuid,plistlib,hashlib
ROOT=Path(__file__).resolve().parent
A=[]
def token(v):return {'Value':v,'WFSerializationType':'WFTextTokenAttachment'}
def action(n,**p):
 u=str(uuid.uuid4()).upper();p['UUID']=u;A.append({'WFWorkflowActionIdentifier':'is.workflow.actions.'+n,'WFWorkflowActionParameters':p});return token({'Type':'ActionOutput','OutputUUID':u,'OutputName':'Result'})
def text(v,prefix=''):return {'Value':{'string':prefix+'\ufffc','attachmentsByRange':{'{%d, 1}'%len(prefix):v['Value']}},'WFSerializationType':'WFTextTokenString'}
def start(v):
 g=str(uuid.uuid4()).upper();action('conditional',WFInput={'Type':'Variable','Variable':v},WFCondition=100,WFControlFlowMode=0,GroupingIdentifier=g);return g
def otherwise(g):action('conditional',WFControlFlowMode=1,GroupingIdentifier=g)
def end(g):action('conditional',WFControlFlowMode=2,GroupingIdentifier=g)
def alert(msg):action('alert',WFAlertActionTitle='X 视频保存',WFAlertActionMessage=msg,WFAlertActionCancelButtonShown=False)
source=token({'Type':'ExtensionInput'})
links=action('text.match',text=text(source),WFMatchTextPattern=r'(?i)https?://(?:www\.)?(?:x\.com|twitter\.com)/(?:[A-Za-z0-9_]+|i/web)/status/[0-9]+',WFMatchTextCaseSensitive=False)
g=start(links)
link=action('getitemfromlist',WFInput=links,WFItemSpecifier='First Item')
ids=action('text.match',text=text(link),WFMatchTextPattern=r'(?<=/status/)[0-9]+',WFMatchTextCaseSensitive=False)
id=action('getitemfromlist',WFInput=ids,WFItemSpecifier='First Item')
u=action('gettext',WFTextActionText=text(id,'https://api.fxtwitter.com/2/status/'))
r=action('downloadurl',WFURL=u,WFHTTPMethod='GET')
videos=action('getvalueforkey',WFInput=r,WFDictionaryKey='status.media.videos',WFGetDictionaryValueType='Value')
g2=start(videos)
v=action('getitemfromlist',WFInput=videos,WFItemSpecifier='First Item')
u=action('getvalueforkey',WFInput=v,WFDictionaryKey='url',WFGetDictionaryValueType='Value')
f=action('downloadurl',WFURL=u,WFHTTPMethod='GET')
action('savetocameraroll',WFInput=f)
action('notification',WFNotificationActionTitle='X 视频保存',WFNotificationActionBody='视频已保存到相册')
otherwise(g2);alert('未找到可下载的视频。请检查帖子是否公开、是否包含视频，或稍后重试。');end(g2)
otherwise(g);alert('未识别到 X 帖子链接，请从帖子分享菜单运行，或复制完整链接后重试。');end(g)
w={'WFWorkflowName':'X 视频保存（分享版）','WFWorkflowClientVersion':'3036.0.4.2','WFWorkflowClientRelease':'18.0','WFWorkflowMinimumClientVersion':900,'WFWorkflowMinimumClientVersionString':'900','WFWorkflowIcon':{'WFWorkflowIconStartColor':4282601983,'WFWorkflowIconGlyphNumber':59767},'WFWorkflowTypes':['ActionExtension'],'WFWorkflowInputContentItemClasses':['WFURLContentItem','WFStringContentItem','WFRichTextContentItem','WFSafariWebPageContentItem'],'WFWorkflowNoInputBehavior':{'Name':'WFWorkflowNoInputBehaviorGetClipboard','Parameters':{}},'WFWorkflowHasShortcutInputVariables':True,'WFWorkflowImportQuestions':[],'WFWorkflowActions':A}
b=plistlib.dumps(w,sort_keys=False);(ROOT/'X-Video-Share-unsigned.shortcut').write_bytes(b)
digest=hashlib.sha256(b).hexdigest()
s=(ROOT/'install-mac.sh').read_text();s=s.replace('Douyin-unsigned.shortcut','X-Video-Share-unsigned.shortcut').replace('抖音视频保存','X 视频保存（分享版）');import re;s=re.sub(r'"\$actual" != "[0-9a-f]{64}"','"$actual" != "'+digest+'"',s)
(ROOT/'install-x-mac.sh').write_text(s)
print('Built',len(A),'actions. SHA256:',digest)
