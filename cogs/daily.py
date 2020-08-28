import discord
from discord.ext import commands
import random
import asyncio
from motor import motor_asyncio
import re

client = motor_asyncio.AsyncIOMotorClient()
db = client['Discord']

class daily(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
    
    async def sorted_daily_players(self):
        stars_list = await db.stars.find().to_list(length=None)
        records_list = {}
        for i in stars_list:
            records_list[i['name']] = i['pt']
        sorted_list = {key: value for key, value in sorted(records_list.items(), key=lambda item: item[1], reverse=True)}
        return sorted_list
    
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
    
    @commands.command(name='stars', aliases=['coolstars', 'blobstars'])
    @commands.has_role('Daily Manager')
    async def coolstars(self, ctx, user=None):
        if not user:
            return await ctx.send('Please provide both a user to add points to and a point value. Examples:\n`,remove_stars paqoe 3`\n`,add_stars "Nyan Cat" 4`')
        user=str(user).lower()
        try:
            f = await db.stars.find_one({
                'name': re.compile(user, re.IGNORECASE)
            })
        except:
            pass
        f_2 = f['pt']
        await ctx.send(user + ' has ' + str(f_2) + ' daily stars')
    
    @commands.command(name='daily_fix_name', aliases=['daily_fix_user'])
    @commands.has_role('Daily Manager')
    async def daily_fix_name(self, ctx, old=None, new=None):
        if not old or not new:
            return await ctx.send('Please provide a valid old username and new username.')
        try:
            await db.stars.delete_many({'name': new})
            await db.stars.find_one_and_update({
                'name': old
            },
            {
                '$set': {
                    'name': new
                }
            })
        except:
            return await ctx.send('Failed to update username.')
        await ctx.send('Updated username.')

    @commands.command(name='add_stars', aliases=['add_coolstars', 'add_cool_stars', 'add_star', 'give_stars'])
    @commands.has_role('Daily Manager')
    async def add_stars(self, ctx, user=None, number:int=0):
        if not user or not number:
            return await ctx.send('Please provide both a user to add points to and a point value. Examples:\n`,remove_stars paqoe 3`\n`,add_stars "Nyan Cat" 4`')
        user=str(user).lower()
        message = f'Updating points for user {user}... '
        loading = await ctx.send(message)
        try:
            await db.stars.find_one_and_update({
                'name': re.compile(user, re.IGNORECASE)
            },
            {
                '$set': {
                    'name': user
                },
                '$inc': {
                    'pt': number
                }
            }, upsert=True)
        except:
            pass
        await loading.edit(content=message + '✅')
    
    @commands.command(name='remove_stars', aliases=['remove_coolstars', 'remove_cool_stars', 'remove_star'])
    @commands.has_role('Daily Manager')
    async def remove_stars(self, ctx, user, number:int):
        await self.add_stars(ctx, user, number*-1)
    
    @commands.command(name='stars_list', aliases=['star_list', 'starlist', 'star_leaderboard', 'star_lb', 'starboard', 'starleaderboard', 'starlb', 'starslist', 'dailylist', 'daily_points_list', 'daily_list', 'dailypointslist'])
    async def starlb(self, ctx, page:int=1):
        sorted_list = await self.sorted_daily_players()

        leaderboards_page_max = page*15
        leaderboards_page_min = leaderboards_page_max-14
        if leaderboards_page_max > len(sorted_list.keys()): leaderboards_page_max = len(sorted_list.keys())
        embed = discord.Embed.from_dict({
            **self.bot.footer(ctx.author),
            'title': 'Top Players - Stars',
            'color': 0x960808
        })
        record_iter = 0
        previous_value = -1
        previous_placement = 0
        for key, value in sorted_list.items():
            placement = list(sorted_list.keys()).index(key)+1
            if placement >= leaderboards_page_min and placement <= leaderboards_page_max:

                # Checks if tied with previous placement
                placement_format = placement
                if previous_value == value:
                    placement_format = previous_placement
                
                name = str(key)
                embed.add_field(name=str(placement_format) + '. ' + name, value='%.2f' % value)
                previous_value = value
                previous_placement = placement_format
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(daily(bot))
