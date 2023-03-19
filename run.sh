#!/bin/bash


export OPENAI_API_KEY=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
export OPENAI_ORGANIZATION=org-MrioZE7Irj32h0rnPjrFxAQa
export DISCORD_TOKEN=MTA4NzAyNDE5OTYyMjcyMTcyOA.GdxKj5.PdcAnH7mLAzzTO27uWhqNyPcLIiXwoq6ibSiRg
export http_proxy=http://proxy.sensetime.com:3128/
export https_proxy=http://proxy.sensetime.com:3128/

# Advice for CPU Users
# python visual_chatgpt.py --load ImageCaptioning_cpu,Text2Image_cpu
/home/sunye2/anaconda3/bin/python discord-chat.py 