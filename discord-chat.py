import os
import discord
from discord import app_commands
from discord.ui import Button, View
import asyncio
import pandas as pd
import openai
import requests_async as req 
from asgiref.sync import sync_to_async
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import json
from datetime import datetime
import numpy as np


openai.api_key = os.getenv("OPENAI_API_KEY")
default_model = "gpt-3.5-turbo"
failed_str = '[Failed]'
chat_models = ['gpt-4', 'gpt-3.5-turbo']
models = ['gpt-4', 'gpt-3.5-turbo', 'text-davinci-003']

def init_client(proxy):
    intends = discord.Intents.default()
    intends.members = True
    intends.presences = True
    intends.messages = True
    intends.message_content = True
    return discord.Client(intents=intends, proxy=proxy if proxy else None)

client = init_client(os.getenv('http_proxy'))
tree = app_commands.CommandTree(client)
# MY_GUILD = discord.Object(id=1054244324939931668)
MY_GUILD = None

# 启动mysql连接，到本地sqlite数据库
engine = create_engine('sqlite:///chat.db?check_same_thread=False', echo=True)
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    # 默认是discord_user_id
    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String)
    create_time = Column(DateTime, default=datetime.now())
    update_time = Column(DateTime, default=datetime.now())
    modify_time = Column(DateTime, default=datetime.now())
    status = Column(String)
    model = Column(String)
    current_session_id = Column(Integer)
    sessions = relationship("Session", backref="creator")
    system_msg = Column(String)
    show_public = Column(Boolean)
    attach = Column(Boolean)
    max_tokens = Column(Integer)
    temperature = Column(Float)

    def strfy(self):
        s = f'''name: {self.name} (id: {self.id})
max tokens: {self.max_tokens}
temperature: {self.temperature}
create time: {self.create_time.strftime('%m/%d/%Y, %H:%M:%S')}
update time: {self.update_time.strftime('%m/%d/%Y, %H:%M:%S')}
modify time: {self.modify_time.strftime('%m/%d/%Y, %H:%M:%S')}
system message: {self.system_msg if self.system_msg else '(None)'}
owned sessions: {'' if len(self.sessions) else '(None)'}
'''
        for session in self.sessions:
            s += '\t{:>10s}: {}\n'.format(str(session.id), session.name)
        return s


class Session(Base):
    __tablename__ = 'session'
    id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey('user.id'))
    name = Column(String)
    create_time = Column(DateTime, default=datetime.now())
    update_time = Column(DateTime, default=datetime.now())
    modify_time = Column(DateTime, default=datetime.now())
    model = Column(String)
    public = Column(Boolean)
    conversation = Column(String)
    system_msg = Column(String)

    def strfy(self):
        s = f'''name: {self.name}
creator: {self.creator.name} (id:{self.creator_id})
create time: {self.create_time.strftime('%m/%d/%Y, %H:%M:%S')}
update time: {self.update_time.strftime('%m/%d/%Y, %H:%M:%S')}
modify time: {self.modify_time.strftime('%m/%d/%Y, %H:%M:%S')}
system message: {self.system_msg if self.system_msg else '(None)'}
conversation:
'''
        for item in json.loads(self.conversation):
            s += '\t{:>10s}: {}\n'.format(item[0], item[1])
        return s
    
    def request(self, prompt, username):
        conversation = json.loads(self.conversation)
        conversation.append((username, prompt))
        print(conversation)
        try:
            if self.model in chat_models:
                messages = [{'role': 'assistant' if msg[0] == 'assistant' else 'user', 'content': msg[1]} for msg in conversation]
                if self.system_msg:
                    messages = [{"role": "system", "content": self.system_msg}] + messages
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages = messages,
                    temperature=self.creator.temperature,
                    max_tokens=self.creator.max_tokens,
                    top_p=1,
                )
                tokens = response['usage']['total_tokens']
                ret = response['choices'][0]['message']['content'].replace('\n\n', '\n')
                print(tokens)
            else:
                s = ''
                for item in conversation:
                    if item[0] in ['AI', 'assistant']:
                        s += f'assistant: {item[1]}\n'
                    else:
                        s += f'user: {item[1]}\n'
                response = openai.Completion.create(
                    model=self.model,
                    prompt=s,
                    temperature=self.creator.temperature,
                    max_tokens=self.creator.max_tokens,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0.6,
                    stop=["user:", "assistant:"]
                )
                ret = response.choices[0].text
            # print(ret)
        except Exception as e:
            return failed_str + str(e)

        conversation.append(('assistant', ret))
        self.conversation = json.dumps(conversation)
        self.update_time = datetime.now()
        self.creator.update_time = datetime.now()
        db_session.commit()
        return ret.replace('AI: ', '').replace('AI Assistant: ', '')

    async def async_request(self, prompts, username):
        try:
            ret = await asyncio.wait_for(sync_to_async(self.request)(prompts, username), 60)
        except Exception as e:
            ret = failed_str + str(e)
        return ret


Base.metadata.create_all(engine)
db_session = sessionmaker(bind=engine)()
    

@client.event
async def on_ready():
    await tree.sync(guild=MY_GUILD)
    print("Ready!")


def get_user(author):
    user = db_session.query(User).filter_by(id=author.id).first()
    if not user:
        user = User(id=author.id, name=author.name, status='disable', model=default_model, 
                    current_session_id=0, system_msg='', show_public=False, attach=False,
                    max_tokens=600, temperature=0.8)
        db_session.add(user)
        db_session.commit()

    if user.name != author.name:
        user.name = author.name
        db_session.commit()
    return user


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    
    user = get_user(message.author)
    if user.status == 'disable':
        return
    
    print(message.content)

    if user.status == 'new':
        is_private = isinstance(message.channel, discord.channel.DMChannel)
        session = Session(creator=user, name=message.content[:10], model=user.model, 
                          public=not is_private, conversation='[]', system_msg=user.system_msg)
    else:
        session = db_session.query(Session).filter_by(id=user.current_session_id)

    if session.creator != user and not session.public:
        await message.reply(f'{failed_str}This is a private session created by {session.creator.name}.')
        return

    await message.add_reaction('✍🏻')
    ret = await session.async_request(message.content, user.name)
    await message.reply(ret)
    await message.remove_reaction('✍🏻', client.user)
    await message.add_reaction('👌')

@tree.command(name = "session", description = "reset current session", guild=MY_GUILD) #Add the guild ids in which the slash command will appear. If it should be in all, remove the argument, but note that it will take some time (up to an hour) to register the command if it's for all guilds.
async def set_session(interaction: discord.Interaction, name:str='', system_msg:str=''):
    await interaction.response.defer()
    user = get_user(interaction.user)
    if user.status != 'activate':
        await interaction.followup.send(failed_str + 'You are not activating any session!')
        return
    
    session = db_session.query(Session).filter_by(id=user.current_session_id).first()
    if session.creator != user:
        await interaction.followup.send(f'{failed_str}This is a private session created by {session.creator.name}.')
        return
    
    if name or system_msg:
        session.name = name
        session.system_msg = system_msg
        session.modify_time = datetime.now()
        db_session.commit()
    await interaction.followup.send(session.strfy(), view=SessionView(session))


class SettingButton(Button):
    def __init__(self, name, activated, row=None, id=None, disabled=False):
        super().__init__(label=name, style=discord.ButtonStyle.blurple if activated else discord.ButtonStyle.gray, 
                         row=row, disabled=disabled)
        self.id = id
        self.name = name

    async def callback(self, interaction: discord.Interaction):
        if self.style == discord.ButtonStyle.blurple:
            return
        await self._view.change_model(interaction, self)


class BoolButton(Button):
    def __init__(self, name, activated, row=None, disabled=False):
        super().__init__(label=name, style=discord.ButtonStyle.green if activated else discord.ButtonStyle.gray, 
                         row=row, disabled=disabled)
        self.name = name
        self.activated = activated

    async def callback(self, interaction: discord.Interaction):
        self.activated = not self.activated
        self.style = discord.ButtonStyle.green if self.activated else discord.ButtonStyle.gray
        await self._view.change_bool(interaction, self)


class SessionView(View):
    def __init__(self, session):
        super().__init__(timeout=None)
        self.session = session
        user = session.creator
        self.model_buttons = []

        button = Button(label='remove', style=discord.ButtonStyle.red)
        async def delete_session(interaction: discord.Interaction):
            db_session.delete(session)
            user.status = 'new'
            db_session.commit()
            await interaction.followup.send(f'Successfully delete session: {session.name} (id: {session.id}))')
        button.callback = delete_session
        self.add_item(button)
        self.add_item(BoolButton('public', session.public))

        for model in models:
            button = SettingButton(model, session.model == model, row=2)
            self.add_item(button)
            self.model_buttons.append(button)

    async def change_bool(self, interaction: discord.Interaction, button):
        self.session.public = not self.session.public
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f'Successfully change {button.name} to `{button.activated}`', ephemeral=True)

    async def change_model(self, interaction: discord.Interaction, button):
        self.session.model = button.name
        db_session.commit()
        for b in self.model_buttons:
            b.style = discord.ButtonStyle.gray
        button.style = discord.ButtonStyle.blurple
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f'Successfully change model to `{button.name}`', ephemeral=True)


class UserView(View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user
        self.status_buttons = []
        self.model_buttons = []

        button = Button(label='clear', style=discord.ButtonStyle.red)
        async def clear_session(interaction: discord.Interaction):
            for session in user.sessions:
                db_session.delete(session)
            db_session.commit()
            await interaction.response.send_message('All sessions have been cleared!', ephemeral=True)
        button.callback = clear_session
        self.add_item(button)
        self.add_item(BoolButton('show public', user.show_public))
        self.add_item(BoolButton('attach', user.attach))

        for model in models:
            button = SettingButton(model, user.model == model, row=2)
            self.add_item(button)
            self.model_buttons.append(button)
        
        for status in ['new', 'disable', 'activate']:
            button = SettingButton(status, user.status == status, row=3, disabled=status=='activate')
            self.add_item(button)
            self.status_buttons.append(button)

        for session in user.sessions:
            button = SettingButton(session.name, user.current_session_id == session.id, id=session.id, row=4)
            self.add_item(button)
            self.status_buttons.append(button)

        if user.show_public:
            for session in db_session.query(Session).filter_by(public=True):
                if session.creator != user:
                    button = SettingButton(session.name, user.current_session_id == session.id, id=session.id, row=4)
                    self.add_item(button)
                    self.status_buttons.append(button)
    

    async def change_bool(self, interaction: discord.Interaction, button):
        if button.name == 'show public':
            self.user.show_public = not self.user.show_public
        elif button.name == 'attach':
            self.user.attach = not self.user.attach
        db_session.commit()
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f'Successfully change {button.name} to `{button.activated}`', ephemeral=True)


    async def change_model(self, interaction: discord.Interaction, button):
        if button in self.status_buttons:
            buttons = self.status_buttons
            if button.name in ['new', 'disable']:
                self.user.status = button.name
                self.user.current_session_id = 0
                msg = f'successfully change status to {button.name}'
            else:
                self.user.status = 'activate'
                self.user.current_session_id = button.id
                session = db_session.query(Session).filter_by(id=button.id).first()
                msg = 'successfully change session!\n' + session.strfy()
            
        else:
            buttons = self.model_buttons
            self.user.model = button.name
            msg = f'successfully change model to {button.name}'
        
        db_session.commit()
        for b in buttons:
            b.style = discord.ButtonStyle.gray
        button.style = discord.ButtonStyle.blurple
        self.activate_button = discord.ButtonStyle.blurple if self.user.status == 'activate' else discord.ButtonStyle.gray
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(msg, ephemeral=True)


@tree.command(name = "user", description = "list sessions of ChatGPT", guild=MY_GUILD) 
async def set_user(interaction: discord.Interaction, system_msg: str=''):
    user = get_user(interaction.user)
    if system_msg and system_msg != user.system_msg:
        user.system_msg = system_msg
        user.modify_time = datetime.now()
        db_session.commit()
    await interaction.response.send_message(user.strfy(), view=UserView(user), ephemeral=True)


client.run(os.getenv("DISCORD_TOKEN"))
