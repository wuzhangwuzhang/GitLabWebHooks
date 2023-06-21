import io
import re
import json
import sys

import notify
import http.server
import gitlab

from CommitFileInfo import ActionType, CommitFileInfo

'''
字典按key value字符串拼接
'''
def string_builder(cSharpFilesDic):
    output = io.StringIO()
    for key in cSharpFilesDic:
        output.write(f"{key} {cSharpFilesDic[key]}")
        output.write('\n')
    result = output.getvalue()
    return result


'''
飞书通知
'''
def notify2Develop(user, issueMsg):
    #notify.FeiShu("SLPKBugRobotTest").set_at_users(user).send(issueMsg)
    notify.FeiShu("SLPKBuildRobot").set_at_users(user).send(issueMsg)


#cs 文件检查目录
PATH_PATTERNS = [
    'Client/Assets/Scripts',
    'Assets/External',
    'Assets/Wwise',
    'Packages/com.yoozoo.owl.rendering.hrp',
    'Packages/com.yoozoo.managers.network',
    'Packages/com.yoozoo.owl.rendering.hrp',
    'Packages/resourcemanagerv2'
]


def getMergeInfo(mrs_url):
    cSharpFileList = []
    pattern = r'.*\/merge_requests\/(\d+)'
    # 使用正则表达式搜索 MR_ID
    match = re.search(pattern, mrs_url)
    if match:
        mr_id = match.group(1)
    else:
        print("Could not find merge request ID in URL")
        sys.exit(1)

    # 4W_mcvajgeqWFAT55XWG gotClient
    # ojhB2Cm3yuKy_76-wFu9 slpk
    gl = gitlab.Gitlab(url='https://gitlab.uuzu.com/', private_token='ojhB2Cm3yuKy_76-wFu9',
                       http_username='zhwu@uuzu.com', http_password="Wz147258")
    gl.auth()  # 安全认证
    project = gl.projects.get(3325)  # 项目的id '3325'   gotClient projectId：2183

    # 获取指定MR id的信息

    real_mr = project.mergerequests.get(mr_id)
    title = real_mr.attributes['title']                             #Merge描述
    createTime = real_mr.attributes['created_at']        #创建Mr时间
    mrUser = real_mr.attributes['author']['username']    #发起MR账号
    mrCName = real_mr.attributes['author']['name']       #中文名
    sourceBranch = real_mr.attributes['source_branch']   #原分支
    targetBranch = real_mr.attributes['target_branch']   #目标分支

    real_mr_id = real_mr.attributes['iid']
    real_mr_url = real_mr.attributes['web_url']
    # print(f"mr_id:{mr_id} real_mr_id：{real_mr_id} real_mr_url：{real_mr_url}")
    all_mrs = real_mr.diffs.list(iterator=True)
    for diff in all_mrs:
        real_diff = real_mr.diffs.get(diff.id)
        for d in real_diff.attributes['diffs']:
            #print(f"diff.id：{diff.id} fileOldPath:{d['old_path']},fileNewPath:{d['new_path']},isNewFile:{d['new_file']},isReNamedFile:{d['renamed_file']},isDeleted:{d['deleted_file']}")  # d['diff']
            for pattern in PATH_PATTERNS:
                if re.match(f".*{pattern}.*", d['old_path']) and str(d['old_path']).endswith("cs"):
                    # print(f"Path {d['old_path']} matched pattern {pattern}")
                    if d['old_path'] not in cSharpFileList:
                        cSharpFileList.append(d['old_path'])
                        print(f"记录修改的C#文件:{d['old_path']}")
    notification = ""
    if len(cSharpFileList) > 0:
        result = f"主题：{title} 提交人:{mrCName} 源分支:{sourceBranch} 目标合并分支:{targetBranch}\n"
        for file in cSharpFileList:
            result += file
            result += "\n"
        notification = f"发现C#修改:\n{result}详情:{mrs_url}"
    else:
        print(f"没有检测到C#文件被修改")
    return notification

'''
Http处理
'''
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def getMatchFile(self, info):
        # 匹配"c#"和"lua"
        matches = re.findall(r'\b\w+\.(?:cs|lua)\b', info)
        print("info:{0} 匹配到目标:{1}".format(info, matches))
        return matches

    def do_POST(self):
        # - request -

        content_length = int(self.headers['Content-Length'])
        # print('content_length:', content_length)

        if content_length:
            input_json = self.rfile.read(content_length)
            input_data = json.loads(input_json)
        else:
            input_data = None
        print(input_data)

        object_kind = input_data['object_kind']
        print(f"eventType:{object_kind}")
        if object_kind == 'merge_request':
            # print("这是一个Merge的Trigger")
            object_attributes = input_data['object_attributes']
            mergeUrl = object_attributes['url']
            # print(f"mergeUrl:{mergeUrl}")
            notifyMsg = getMergeInfo(mergeUrl)
            if notifyMsg != "":
                #notify2Develop('看门狗', notifyMsg)
                notify2Develop('丝路助手', notifyMsg)
        else:
            branchName = input_data['ref']
            if branchName.__contains__('dev') or branchName.__contains__('master'):
                #print("提交分支:{0} before:{1} after:{2} develop:{3} developName:{4}".format(input_data['ref'],input_data['before'],input_data['after'],input_data['user_username'],input_data['user_name']))

                userAccount = input_data['user_username']       #域账户名
                developerName = input_data['user_name']         #开发者名称

                commits = input_data['commits']
                # print("commits length:{0}  git push commit len:{1}".format(len(input_data['commits']),input_data['total_commits_count']))

                index = 0
                commitFileInfoList = []

                for item in commits:
                    index = index + 1
                    # print("第{0}次提交 id：{1} message:{2} title:{3}".format(index,item['id'],item['message'],item['title']))

                    # git新增
                    added = item['added']
                    if len(added) > 0:
                        for addItem in added:
                            if addItem.endswith('.cs'):

                                title = item['title']
                                timeStamp = item['timestamp']
                                url = item['url']
                                commitInfo = CommitFileInfo(addItem, ActionType.ADD, userAccount, developerName,title,timeStamp,url)
                                commitFileInfoList.append(commitInfo)
                        # print("------------------------")

                    # git修改
                    modified = item['modified']
                    if len(modified) > 0:
                        for modifyItem in modified:
                            # print("修改的文件:", item)
                            if modifyItem.endswith('.cs'):
                                title = item['title']
                                timeStamp = item['timestamp']
                                url = item['url']
                                commitInfo = CommitFileInfo(modifyItem, ActionType.MODIFY, userAccount, developerName, title, timeStamp,url)
                                commitFileInfoList.append(commitInfo)
                        # print("------------------------")

                    # git删除
                    removed = item['removed']
                    if len(removed) > 0:
                        for removeItem in removed:
                            # print("删除的文件:", item)
                            if removeItem.endswith('.cs'):
                                title = item['title']
                                timeStamp = item['timestamp']
                                url = item['url']
                                commitInfo = CommitFileInfo(removeItem, ActionType.DELETE, userAccount, developerName, title, timeStamp,url)
                                commitFileInfoList.append(commitInfo)
                        # print("------------------------")
                # 检查文件信息
                result = ""
                notifyUser = ""
                if len(commitFileInfoList) > 0:
                    for commitFileInfo in commitFileInfoList:
                        notifyUser = commitFileInfo.gitlabName
                        result += commitFileInfo.ToString()
                        result += "\n"
                    notification = f"分支:【{input_data['ref']}】 发现C#修改:\n{result}"
                    print(notification)
                    notify2Develop(notifyUser, notification)

        # - response -
        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        self.end_headers()

        output_data = {'status': 'OK', 'result': 'HELLO WORLD!'}
        output_json = json.dumps(output_data)
        self.wfile.write(output_json.encode('utf-8'))
