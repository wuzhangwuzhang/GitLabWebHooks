import enum

class ActionType(enum.Enum):
    NONE = 0
    ADD = 1
    MODIFY = 2
    DELETE = 3
    OTHER = 4


def GetActionDesc(actionType):
    if actionType == ActionType.ADD:
        return "新增"
    elif actionType == ActionType.MODIFY:
        return "修改"
    elif actionType == ActionType.DELETE:
        return "删除"

class CommitFileInfo:
    filePath = ""
    actType = ActionType.NONE
    gitlabName = ""
    developerName = ""
    title = ""
    timeStamp = ""
    url = ""

    def __init__(self, _filePath, _actType, _gitlabName, _developerName, _title, _timeStamp, _url):  # 必须要有一个self参数
        self.filePath = _filePath
        self.actType = _actType
        self.gitlabName = _gitlabName
        self.developerName = _developerName
        self.title = _title
        self.timeStamp = _timeStamp
        self.url = _url

    def ToString(self):
        logStr = f"[{GetActionDesc(self.actType)}]文件:{self.filePath} 修改时间：{self.timeStamp} 提交人:{self.developerName} \n详情: {self.url}"
        return logStr
