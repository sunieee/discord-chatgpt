# Discord-bot (multi-user, multi-session) for chatGPT

discord Server invite link: https://discord.gg/sp9pbhRjAg

关键的概念是user和session，对应着用户和会话

- 首先discord中每个用户（user）对应chatGPT的用户，相应数据存储在user数据表中
- 每个user可以创建多个会话（session），并且可以对于创建者是自己的会话进行管理
- 用户可使用自己的会话或者公共会话进行对话
  - 如果在公共channel创建session，那么session初始化为公共的（任何人都能进行提问）
  - 如果在DM创建的session，那么session初始化为私有的，即使在公共对话，其他人也无法提问（除非创建者修改权限）

## schema

使用sqlite存储信息到本地，包含session和user两个表格：

**user表：**包括以下信息：name + discod_user_id + 时间（create, update指最晚对话时间, modify指最晚信息修改时间）+ status + model + current_session + system_msg

**session表：**包括以下信息：创建者 + 模型 + 标题 + 时间（create, update指最晚对话时间, modify指最晚信息修改时间）+ 是否公开 + 序列化对话数据（保存每句话的身份）+ system_msg

## 斜杠命令

使用相应的斜杠命令会私发一个消息，该交互具有三个重要的特征：输入参数、输出内容、按钮。

- 输入参数：在命令后面跟上的参数，用于修改字符型属性
- 输出内容：有关于该数据结构的全部信息输出
- 按钮：消息的末尾是按钮，可以对于数据结构的属性进行调整

### /user

输入参数：

- system_msg：默认会话设定（仅在gpt3.5以上模型中有效）
- max_token：最大单次询问token数量（默认为500）

输出内容：

- Name (Discord id)
- Create time
- Update time
- Modify time
- System message
- Sessions

按钮：

- **Show public**：是否显示公共对话，否则只显示自己创建的，从是切换到否，或者从否切换到是（默认为False）
- **attach**：创建会话后是否默认进入会话上下文，否则用户状态会始终处于new（默认为False）
- **clear**：将已有的会话全部清除，慎用
- **使用模型（row2）**：仅对新创建的会话有效，已有会话模型不会变动，在请求API时使用相应的模型
- **用户状态（row3）**：用户三种状态：new, activate, disable，分别代表“创建新会话”、“使用已有会话”、“禁用ChatGPT”，默认处于“禁用ChatGPT”状态。前两种状态均是问答状态，该用户所有消息的都会得到回复。
- **使用会话（row4）**：列举所有会话，可选择已有会话（个人或者共享的），点击已有会话后私发会话栈信息，并且后续的对话有栈的环境。将状态改为new会创建新的会话，默认使用问句中的关键词进行会话命名

### /session

输入参数：

- name：重命名当前会话（默认创建的前10个字符）
- system_msg：会话设定

输出内容：

- Creator
- Name
- Create time
- Update time
- Modify time
- System message
- Conversation

按钮：

- **public**：会话是否是公共的，只有会话创建者才能修改
- **model**：会话使用的模型（只对该session后续的对话有效）
- **remove**：移除当前会话

## 可选模型

OpenAI API 由具有不同功能和价位的多种模型提供支持。[您还可以通过微调](https://platform.openai.com/docs/guides/fine-tuning)针对您的特定用例对我们的原始基础模型进行有限的定制。

| 模型种类                                                     | 描述                                                      |
| ------------------------------------------------------------ | --------------------------------------------------------- |
| [GPT-4](https://platform.openai.com/docs/models/gpt-4)       | 一组在 GPT-3.5 上改进的模型，可以理解并生成自然语言或代码 |
| [GPT-3.5](https://platform.openai.com/docs/models/gpt-3-5)   | 一组在 GPT-3 上改进的模型，可以理解并生成自然语言或代码   |
| DALL E                                                       | 可以在给定自然语言提示的情况下生成和编辑图像的模型        |
| [W](https://platform.openai.com/docs/models/whisper)hisper   | 一种可以将音频转换为文本的模型                            |
| [E](https://platform.openai.com/docs/models/embeddings)mbedding | 一组可以将文本转换为数字形式的模型                        |
| CodeX                                                        | 一组可以理解和生成代码的模型，包括将自然语言翻译成代码    |
| [M](https://platform.openai.com/docs/models/moderation)oderation | 可以检测文本是否敏感或不安全的微调模型                    |
| [GPT-3](https://platform.openai.com/docs/models/gpt-3)       | 一组可以理解和生成自然语言的模型                          |

代表模型：gpt-4、[gpt-3.5-turbo](https://platform.openai.com/docs/models)、text-davinci-003

虽然新`gpt-3.5-turbo`模型针对聊天进行了优化，但它非常适合传统的完成任务。原始的 GPT-3.5 模型针对[文本补全](https://platform.openai.com/docs/guides/completion)进行了优化。还发布了开源模型，包括[Point-E](https://github.com/openai/point-e)、[Whisper](https://github.com/openai/whisper)、[Jukebox](https://github.com/openai/jukebox)和[CLIP](https://github.com/openai/CLIP)。

价格：https://openai.com/pricing

![img](https://act-visual.feishu.cn/space/api/box/stream/download/asynccode/?code=NTI3OTVkY2UwYWQyZTczMmY5NTUyNjQyNTg3MDEwNjNfRWwzNkViYVFqRk9QT1NhVFNJM2ZobFZEbVNmZEs5c2hfVG9rZW46Ym94Y25tN3owVzN2Qml2OXdJWjdkYzNhY1ZiXzE2NzkyMzg2NzM6MTY3OTI0MjI3M19WNA)

chatAPI：https://platform.openai.com/docs/guides/chat/introduction

## 消息命令

为了避免遗忘历史信息，提供对机器人消息的消息命令，私发有关session的所有环境信息

> Plus账号信息：
>
> liubx07@gmail.com sensetime
>
> API key: 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
>
> Organization id: org-LQ0zTSTQKSxRHoDfiU3cLmtw
>
> I'd like to build a discord chat bot, especially integrate it with "Visual ChatGPT", which can help us interpret photos or generate photos highly interactively.
>
> 账号：latavislgvjuyp@gmail.com
>
> 密码：SSss77&&
>
> api_key：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
>
> Org ID: org-MrioZE7Irj32h0rnPjrFxAQa
>
> Discord token: MTA4NzAyNDE5OTYyMjcyMTcyOA.GdxKj5.PdcAnH7mLAzzTO27uWhqNyPcLIiXwoq6ibSiRg


## 样例

### 问答模式

![img](https://act-visual.feishu.cn/space/api/box/stream/download/asynccode/?code=N2ZhMjk1ZTE0OGQzYzFkNmU4ZTJkZGVjMjM1NDU4OTVfVVdIdnUwNDhmUXE2aXVjc0JPdk11T2pEd1BFM05rT3hfVG9rZW46Ym94Y25sb0pLeTgxSVRUaDd4M2J0WWtCTjllXzE2NzkyMzg2NzM6MTY3OTI0MjI3M19WNA)

### /user

![img](https://act-visual.feishu.cn/space/api/box/stream/download/asynccode/?code=MTdlNTcyMDY3MjA3NWY3MGE2Njg1NjliNTRmNDQ2NDJfTDVWZDVZZ205QzAxdlQxTG0xRGVvUlNsazExc2ZZUGhfVG9rZW46Ym94Y25meXdwNTJaU0dNa2pxOWRZUDRaTHhoXzE2NzkyNDE5NDY6MTY3OTI0NTU0Nl9WNA)

### /session

![img](https://act-visual.feishu.cn/space/api/box/stream/download/asynccode/?code=NWRlYmVlYjBjZGIwM2NkNzZkN2UwNDJlZTIzNDg5MTdfMVlVUUpCUEVocmVZMldjWEw5ZGJIbmtoZzdVRWRLQXdfVG9rZW46Ym94Y25zUGhuaDNkR0c4U2tSb3JLTldkc2RnXzE2NzkyNDE5NDY6MTY3OTI0NTU0Nl9WNA)

### 生成过程
生成过程和解释会添加reaction，使用不同的emoji✍🏻与👌分别表示“正在生成”与“生成完成”

![img](https://act-visual.feishu.cn/space/api/box/stream/download/asynccode/?code=ZmI1ZDc2NDA4ODg4MmM0MDI5NzI0NzY0NmY4NTMwMzBfR0VGUTNSWHNTcThrVWcxcWtYWWhlWVdqZ1lhcG5qYzNfVG9rZW46Ym94Y24xMGZFWjhVTUFYSXhWbnhSSjJEaUVnXzE2NzkyNDE5NTk6MTY3OTI0NTU1OV9WNA)