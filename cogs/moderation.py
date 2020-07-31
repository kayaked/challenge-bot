import discord
from discord.ext import commands
from motor import motor_asyncio
import asyncio
import time
import aiohttp
import humanize
import traceback
import re

client = motor_asyncio.AsyncIOMotorClient()
db = client['Discord']

class moderation(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.bot.loop.create_task(self.check_list_bans())
    
    @commands.command(name='merge_user', aliases=['fix_user', 'fix_record', 'merge_record', 'fix_name', 'rename', 'merge_name', 'update_name', 'change_name', 'update_record'])
    @commands.has_permissions(ban_members=True)
    async def merge_user(self, ctx, old_name:str, new_name:str):
        def check(msg):
            return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id
        
        msg = await ctx.send(f'Are you SURE you want to update `{old_name}`\'s records to the account `{new_name}`? (Respond `YES` to continue)\n This action will NOT be reversable if records exist under the new name.')
        try:
            confirmation = await self.bot.wait_for('message', check=check, timeout=15)
        except asyncio.TimeoutError:
            return await ctx.send("Oops! Response took too long.")
        if confirmation.content != 'YES':
            await msg.delete()
            return
        await db.records.update_many({'player': old_name}, {'$set': {'player': new_name}})
        await db.levels.update_many({'verifier': old_name}, {'$set': {'verifier': new_name}})
        await db.levels.update_many({'publisher': old_name}, {'$set': {'publisher': new_name}})
        await db.levels.update_many({'creators': old_name}, {'$set': {'creators.$': new_name}})
        if (await db.accounts.find_one({'gd': new_name})) and (await db.accounts.find_one({'gd': old_name})):
            await db.accounts.delete_one({'gd': new_name})
        await db.accounts.update_one({'gd': old_name}, {'$set': {'gd': new_name}})

        await ctx.send('Successfully updated records.')
    
    @commands.command(name='merge_challenge', aliases=['fix_challenge', 'rename_challenge'])
    @commands.has_permissions(ban_members=True)
    async def merge_chall(self, ctx, old_name:str, new_name:str):
        def check(msg):
            return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id
        
        msg = await ctx.send(f'Are you SURE you want to update `{old_name}`\'s records to the account `{new_name}`? (Respond `YES` to continue)\n This action will NOT be reversable if records exist under the new name.')
        try:
            confirmation = await self.bot.wait_for('message', check=check, timeout=15)
        except asyncio.TimeoutError:
            return await ctx.send("Oops! Response took too long.")
        if confirmation.content != 'YES':
            await msg.delete()
            return
        await db.records.update_many({'challenge': old_name}, {'$set': {'challenge': new_name}})
        await db.levels.update_many({'name': old_name}, {'$set': {'name': new_name}})

        await ctx.send('Successfully updated records.')

    @commands.command(name='update_channel')
    @commands.has_permissions(administrator=True)
    async def update_channel(self, ctx, variable, channel:discord.TextChannel=None):
        possible_vars = ['suggest', 'records']
        if variable not in possible_vars:
            return await ctx.send('Oops! This channel type was not found. Valid channels to change are {}.'.format(', '.join([f'`{var}`' for var in possible_vars])))
        if not channel:
            channel = ctx.channel
        await db.channels.update_one({'name': variable}, {'$set': {'id': str(channel.id)}}, upsert=True)

        await ctx.send('Successfully updated channel configuration.')
    
    async def check_list_bans(self):
        await asyncio.sleep(10)
        while not self.bot.is_closed():
            banlist = await db.bans.find().to_list(length=None)
            for ban in banlist:
                if ban['expires'] <= time.time(): # If enough time has passed since the ban
                    await self.unban(ban, 'Time expired')
            await asyncio.sleep(1)
    
    async def unban(self, ban, reason='N/A'):
        await db.bans.delete_many({'uid': ban['uid']})
        print(ban)

        # Retrieves user by ID
        user = await self.bot.fetch_user(ban['uid'])

        # Gets the bot records channel and sends an unban log report.
        gd = 'N/A'
        gdacc = await db.accounts.find_one({'discord': str(user.id)})
        if gdacc: gd = gdacc['gd']
        record_channel = await db.channels.find_one({'name': 'records'})
        if not record_channel: return
        done = False
        await self.bot.get_channel(int(record_channel['id'])).send(embed=discord.Embed.from_dict({
            **self.bot.footer(user),
            'title': f'User unbanned from the list',
            'description': str(ban['uid']),
            'color': 0x960808,
            "thumbnail": {
                "url": str(user.avatar_url)
            },
            'fields': [
                {
                    'name': 'User',
                    'value': str(user),
                    'inline': True
                },
                {
                    'name': 'GD Username',
                    'value': gd,
                    'inline': True
                },
                {
                    'name': 'Reason',
                    'value': reason,
                    'inline': True
                }
            ]
        }))
    
    async def get_member(self, user):
        if type(user) == discord.Member:
            pass
        elif user.startswith('<@') and user.endswith('>'):
            user_id = int(''.join([i for i in user if i.isdigit()]))
            user = await self.bot.fetch_user(user_id)
            if not user: return None
        elif type(user) == str:
            try:
                user_temp = await self.bot.fetch_user(user)
                if user_temp:
                    return user_temp
            except:
                pass
            user_account = await db.accounts.find_one({'gd': re.compile(user, re.IGNORECASE)})
            if not user_account: return None
            if 'discord' in user_account: user = await self.bot.fetch_user(user_account['discord'])
        return user

    @commands.command(name='unban', aliases=['pardon'])
    @commands.has_role('List Mod')
    async def unban_cmd(self, ctx, user, *, reason='N/A'):
        member = await self.get_member(user)
        if not member:
            return await ctx.send('No matching member was found.')
        user = await db.bans.find_one({'uid': member.id})
        await self.unban(user, reason)

    @commands.command(name='listban', aliases=['ban', 'tempban', 'permban'])
    @commands.has_role('List Mod')
    async def ban(self, ctx, user, timevalue='99y', *, reason="None"):
        user = await self.get_member(user)
        if not user:
            return await ctx.send('No matching member was found.')
        # Calculating the time for a ban
        try:
            timevalue = re.findall(r'[0-9]+[ymwdhs]', timevalue)
            if not timevalue: raise Exception
            tadd = 0.
            for i in timevalue:
                print(i)
                if i.endswith('y'):
                    tadd += float(i[:-1])*31536000
                if i.endswith('m'):
                    tadd += float(i[:-1])*86400*31
                if i.endswith('w'):
                    tadd += float(i[:-1])*86400*7
                if i.endswith('d'):
                    tadd += float(i[:-1])*86400
                elif i.endswith('h'):
                    tadd += float(i[:-1])*3600
                elif i.endswith('s'):
                    tadd += float(i[:-1])*1
            timevalue = time.time() + tadd
            duration = humanize.naturaltime(tadd).rsplit(" ", 1)[0]
            print(humanize.naturaltime(tadd))
        except:
            traceback.print_exc()
            return await ctx.send("I do not understand this time value!")
        
        # Inserting the ban into the bans database
        if await db.bans.find_one({'uid':user.id}):
            return await ctx.send("User already list banned! Please unban and re-ban to change time slot.")
        await db.bans.insert_one({'uid':user.id, 'expires':timevalue, 'reason': reason})

        # Checking for the bot records channel and sending a log embed
        gd = 'N/A'
        gdacc = await db.accounts.find_one({'discord': str(user.id)})
        if gdacc: gd = gdacc['gd']
        record_channel = await db.channels.find_one({'name': 'records'})
        if not record_channel: return
        await self.bot.get_channel(int(record_channel['id'])).send(embed=discord.Embed.from_dict({
            **self.bot.footer(user),
            'title': f'User banned from the list',
            'description': str(user.id),
            'color': 0x960808,
            "thumbnail": {
                "url": str(user.avatar_url)
            },
            'fields': [
                {
                    'name': 'User',
                    'value': str(user),
                    'inline': True
                },
                {
                    'name': 'GD Username',
                    'value': gd,
                    'inline': True
                },
                {
                    'name': 'Duration',
                    'value': duration,
                    'inline': True
                },
                {
                    'name': 'Reason',
                    'value': reason,
                    'inline': True
                }
            ]
        }))

def setup(bot):
    bot.add_cog(moderation(bot))
