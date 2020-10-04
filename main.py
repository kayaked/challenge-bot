import discord
import config
import traceback
from discord.ext import commands
import time
import datetime

bot = commands.Bot(command_prefix=',')
bot.remove_command("help")

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="1738"))
    print('Challenge List Bot Loaded')

bot.config = config

def footer(author):
    structure= {
        **discord.Embed(timestamp=datetime.datetime.today()).to_dict(),
        'footer':{
            'text':f'{str(author.id)}'
        }
    }
    return structure

bot.footer = footer

cogs = bot.config.COGS

for cog in cogs:
    try:
        if not "__init__" in cog:
            time_stamp = time.monotonic()
            bot.load_extension(f'cogs.{cog}')
            get_time_taken = str("%.2f" % (100 * (time.monotonic() - time_stamp)))
            print(f'[!] Loaded cog {cog} in {get_time_taken} ms.')
    except:
        print(f'[!] Cog {cog} not loaded. Check the traceback for errors.')
        traceback.print_exc()


bot.run(config.TOKEN)
