# Discord-bot (multi-user, multi-session) for chatGPT

discord Server invite link: https://discord.gg/sp9pbhRjAg

The key concepts are **user** and **session**

- First, each **user** in discord corresponds to a chatGPT user, and the corresponding data is stored in the user data table
- Each user can create multiple **sessions**, and can manage the session created by himself
- Users can have conversations using their own sessions or public sessions
  - If the session is created on a public channel, the session is initialized as public (anyone can ask questions)
  - If the session is created in DM, then the session is initialized as private, even in a public conversation, others cannot ask questions (unless the creator modifies the permissions)

## schema

Use sqlite to store information locally, including two tables of session and user:

**user table:** includes the following information: name + discod_user_id + time (create, update refers to the latest dialogue time, modify refers to the latest information modification time) + status + model + current_session + system_msg  + public or not

**Session table:** includes the following information: creator + model + title + time (create, update refers to the latest dialogue time, modify refers to the latest information modification time) + public or not + serialized dialogue data (save the identity of each sentence) + system_msg

## slash command

Using the corresponding slash command will send a private message, and this interaction has three important features: input parameters, output content, and buttons.

- Input parameter: the parameter followed by the command, used to modify the character attribute
- Output content: all information about the data structure is output
- Button: The end of the message is a button, which can adjust the properties of the data structure

### /user

Input parameters:

- system_msg: default session settings (only valid in models above gpt3.5)
- max_token: the maximum total number of tokens for a single inquiry (the default is 600 tokens, about 450 words)
- temperature: 0~1, higher temperature can give more random answers (default is 0.8)

Output Content:

- Name (Discord id)
- Create time
- Update time
- Modify time
- System message
- Sessions

Button:

- **Show public** : Whether to show public conversations, otherwise only show the ones created by yourself, switch from yes to no, or from no to yes (default is False)
- **attach** : Whether to enter the session context by default after creating a session, otherwise the user status will always be new (default is False)
- **clear** : Clear all existing sessions, use with caution
- **Use model (row2)** : Only valid for newly created sessions, the existing session model will not change, use the corresponding model when requesting the API
- **User status (row3)** : There are three user statuses: new, activate, and disable, respectively representing "create a new session", "use an existing session", and "disable ChatGPT", and the default is "disable ChatGPT". The first two states are question-and-answer states, and all messages of the user will be replied.
- **Use session (row4)** : List all sessions, select an existing session (personal or shared), click on an existing session to privately send session stack information, and follow-up conversations have a stack environment. Changing the state to new will create a new session, and by default, the keywords in the question are used to name the session

### /session

Input parameters:

- name: Rename the current session (the first 10 characters created by default)
- system_msg: session settings

Output Content:

- Creator
- Name
- Create time
- Update time
- Modify time
- System message
- Conversation

Button:

- **public** : whether the session is public and only the session creator can modify it
- **model** : the model used by the session (only valid for subsequent dialogues of the session)
- **remove** : remove the current session

## optional model

The OpenAI API is powered by a variety of models with different capabilities and price points. You can also do limited customization of our original base model for your specific use case [by fine-tuning it .](https://platform.openai.com/docs/guides/fine-tuning)

| model type                                                   | describe                                                     |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| [GPT-4](https://platform.openai.com/docs/models/gpt-4)       | A set of improved models on GPT-3.5 that can understand and generate natural language or code |
| [GPT-3.5](https://platform.openai.com/docs/models/gpt-3-5)   | A set of improved models on GPT-3 that can understand and generate natural language or code |
| GIVE HER                                                     | Models that can generate and edit images given natural language cues |
| [W](https://platform.openai.com/docs/models/whisper)hisper   | A model that can convert audio to text                       |
| [E](https://platform.openai.com/docs/models/embeddings)mbedding | A set of models that can convert text to digital form        |
| CodeX                                                        | A set of models that can understand and generate code, including translating natural language into code |
| [M](https://platform.openai.com/docs/models/moderation)oderation | A fine-tuned model that can detect whether text is sensitive or insecure |
| [GPT-3](https://platform.openai.com/docs/models/gpt-3)       | A set of models that can understand and generate natural language |

Representative models: gpt-4 (need to apply), gpt-3.5-turbo, text-davinci-003

While the new `gpt-3.5-turbo`model is optimized for chatting, it's perfectly suited for traditional completion tasks. The original GPT-3.5 model is optimized for [text completion . ](https://platform.openai.com/docs/guides/completion)Open source models have also been released, including [Point-E](https://github.com/openai/point-e) , [Whisper](https://github.com/openai/whisper) , [Jukebox](https://github.com/openai/jukebox) , and [CLIP](https://github.com/openai/CLIP) .

Price: https://openai.com/pricing

[![image](https://user-images.githubusercontent.com/42105752/226223978-36559bc5-37fd-458a-bb77-834a546eea37.png)](https://user-images.githubusercontent.com/42105752/226223978-36559bc5-37fd-458a-bb77-834a546eea37.png)

chatAPI：https://platform.openai.com/docs/guides/chat/introduction

## message command (to be developed)

In order to avoid forgetting historical information, provide message commands for robot messages, and privately send all environmental information about sessions.

## sample

### question and answer mode

When the user status is new or activated, the messages sent will be answered by the chatbot:

[![image](https://user-images.githubusercontent.com/42105752/226224063-d4a7bc3e-5ff3-45ae-9fc4-2f6b659effa4.png)](https://user-images.githubusercontent.com/42105752/226224063-d4a7bc3e-5ff3-45ae-9fc4-2f6b659effa4.png)

### /user

[![image](https://user-images.githubusercontent.com/42105752/226224391-7cbebf3f-e43c-4b84-a26f-f3c0a28a89a9.png)](https://user-images.githubusercontent.com/42105752/226224391-7cbebf3f-e43c-4b84-a26f-f3c0a28a89a9.png)

### /session

[![image](https://user-images.githubusercontent.com/42105752/226224531-68c07199-d1bc-4026-921d-ab39ab960d58.png)](https://user-images.githubusercontent.com/42105752/226224531-68c07199-d1bc-4026-921d-ab39ab960d58.png)

### generation process

The generation process and explanation will add reaction, use different emoji✍🏻 with👌Respectively indicate "generating" and "generating completed"

[![image](https://user-images.githubusercontent.com/42105752/226224635-f21ba363-6812-4c9c-96bc-fdbfd8105689.png)](https://user-images.githubusercontent.com/42105752/226224635-f21ba363-6812-4c9c-96bc-fdbfd8105689.png)
