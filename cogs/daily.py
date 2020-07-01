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
            records_list[i['uid']] = i['pt']
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

    @commands.command(name='add_stars', aliases=['add_coolstars', 'add_cool_stars', 'add_star', 'give_stars'])
    @commands.has_role('List Helper')
    async def add_stars(self, ctx, user=None, number:int=0):
        if not user or not number:
            return await ctx.send('Please provide both a user to add points to and a point value. Examples:\n`,remove_stars paqoe 3`\n`,add_stars "Nyan Cat" 4`')
        message = f'Updating points for user {str(user)}... '
        user = await self.get_member(user)
        if not user or type(user) == str:
            return await ctx.send('Could not find user!')
        loading = await ctx.send(message)
        try:
            await db.stars.find_one_and_update({
                'uid': user.id
            },
            {
                '$set': {
                    'uid': user.id
                },
                '$inc': {
                    'pt': number
                }
            }, upsert=True)
        except:
            pass
        await loading.edit(content=message + '✅')
    
    @commands.command(name='remove_stars', aliases=['remove_coolstars', 'remove_cool_stars', 'remove_star'])
    @commands.has_role('List Helper')
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
                
                name = ctx.guild.get_member(key)
                if not name: name = await self.bot.fetch_user(key)
                embed.add_field(name=str(placement_format) + '. ' + name.name, value='%.2f' % value)
                previous_value = value
                previous_placement = placement_format
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(daily(bot))