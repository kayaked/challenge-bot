import discord
from discord.ext import commands
import random
import asyncio
from motor import motor_asyncio
import re

client = motor_asyncio.AsyncIOMotorClient()
db = client['Discord']

class accounts(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
    
    @commands.command(name='account', aliases=['player', 'user', 'creator', 'verifier', 'acc'])
    async def account(self, ctx, *, user=None):
        if user:
            if user.startswith('<@') and user.endswith('>'):
                user = ctx.guild.get_member(int(''.join([i for i in user if i.isdigit()])))
            if type(user) == discord.Member:
                userid = user.id
                user_account = await db.accounts.find_one({'discord': str(userid)})
            elif type(user) == str:
                # Queries a search for the name.
                user_account = await db.accounts.find_one({'$text': {'$search': user}})
                if not user_account:
                    # Searches for the search term at the start of the word
                    user_account = await db.accounts.find_one({'gd': re.compile('^' + user, re.IGNORECASE)})
                    if not user_account:
                        # Searches for the search term within the word itself
                        user_account = await db.accounts.find_one({'gd': re.compile('.*' + user + '.*', re.IGNORECASE)})
        else:
            userid = ctx.author.id
            user_account = await db.accounts.find_one({'discord': str(userid)})
        
        if user_account:
            username = user_account['gd']
        elif type(user)==str:
            username = user
        completions = []
        creations = []
        verifications = []
        completed_levels = await db.records.find({'player': username}).to_list(length=100)
        created_levels = await db.levels.find({'creators': username}).to_list(length=100)
        verified_levels = await db.levels.find({'verifier': username}).to_list(length=100)
        if verified_levels:
            verifications = [i['name'] for i in verified_levels]
        if completed_levels:
            completions = [i['challenge'] for i in completed_levels if (i['challenge'] not in verifications) and i['status'] == 'approved']
        if created_levels:
            creations = [i['name'] for i in created_levels]
        if any([created_levels, verified_levels, completed_levels]) and not user_account:
            await db.accounts.update_one({'gd': username}, {'$set': {
                'verified': False,
                'gd': username
            }},
            upsert=True)
        elif not user_account:
            return await ctx.send('This user was not found. Please ask a list staff member to use `,account verify`.')
        list_sorted = await self.get_sorted_players()
        new_list_s = {}
        for key, value in list_sorted.items():
            new_list_s[key.lower()] = value
        if new_list_s.get(username.lower()):
            list_points = new_list_s.get(username.lower())
        else:
            list_points = 0


        structure = {
            **self.bot.footer(ctx.author),
            'title': username + ' - Account Info',
            'color': 0x960808,
            'fields': [
                {
                    'name': 'Completions',
                    'value': ', '.join(completions) if completions else 'None',
                    'inline': True
                },
                {
                    'name': 'Creations',
                    'value': ', '.join(creations) if creations else 'None',
                    'inline': True
                },
                {
                    'name': 'Verifications',
                    'value': ', '.join(verifications) if verifications else 'None',
                    'inline': True
                },
                {
                    'name': 'List Points',
                    'value': '%.2f' % list_points,
                    'inline': True
                },
                {
                    'name': 'Geometry Dash',
                    'value': username,
                    'inline': True
                }
            ]
        }
        embed = discord.Embed.from_dict(structure)
        if not user_account:
            embed.set_footer(text='Alert: This account is unverified and was searched by list records.')
        else:
            if user_account['verified']:
                user_cord = await self.bot.fetch_user(int(user_account['discord']))
                embed.add_field(
                    name = 'Discord',
                    value = str(user_cord)
                )
                embed.title += ' ✅'
                embed.set_thumbnail(url=user_cord.avatar_url)
                daily_records = await db.stars.find_one({'name': user_account['gd']})
                if daily_records:
                    embed.add_field(
                        name='Cool-Stars',
                        value=str(daily_records['pt'])
                    )
            else:
                embed.set_footer(text='Alert: This account is unverified and was searched by list records.')

        await ctx.send(embed=embed)
    
    async def get_discord_specific_member(self, user):
        if type(user) == discord.Member:
            return user
        elif user.startswith('<@') and user.endswith('>'):
            user_id = int(''.join([i for i in user if i.isdigit()]))
            user = await self.bot.fetch_user(user_id)
            if user:
                return user
        elif type(user) == str:
            try:
                user_temp = await self.bot.fetch_user(user)
                if user_temp:
                    return user_temp
            except:
                pass
        return None
    
    @commands.command(name='verify')
    @commands.has_role('List Mod')
    async def verify(self, ctx, gd=None, discord=None):
        if not gd or not discord:
            return await ctx.send('Missing a GD or Discord account, check command! Correct formatting is `,verify <gd> <Discord>`')
        discord_mem = await self.get_discord_specific_member(discord)
        await db.accounts.update_one({
            'gd': re.compile(gd, re.IGNORECASE)
        },
        {
            '$set': {
                'verified': True,
                'gd': gd,
                'discord': str(discord_mem.id)
            }
        },
        upsert=True)

        await ctx.send('**Success!** Your account was successfully created. Use `,account` to view your new account.')
    
    async def get_sorted_players(self):
        records_length = await db.records.count_documents({})
        records = await db.records.find().to_list(length=records_length)
        levels_length = await db.records.count_documents({})
        levels = await db.levels.find({'placement': {'$lte': 50}}).to_list(length=levels_length)

        records_list = {}
        for record in records:
            level = [l for l in levels if (l['name'].lower() == record['challenge'].lower()) and record['status'] == 'approved']
            if not level: continue
            placement = level[0]['placement']
            if record['player'] in records_list:
                records_list[record['player']] += (-(.08*placement-6)**3+5)
            else:
                records_list[record['player']] = (-(.08*placement-6)**3+5)
        
        sorted_list = {key: value for key, value in sorted(records_list.items(), key=lambda item: item[1], reverse=True)}
        return sorted_list

    @commands.command(name='leaderboard', aliases=['lb'])
    async def leaderboard(self, ctx, page=1):
        sorted_list = await self.get_sorted_players()

        leaderboards_page_max = page*15
        leaderboards_page_min = leaderboards_page_max-14
        if leaderboards_page_max > len(sorted_list.keys()): leaderboards_page_max = len(sorted_list.keys())
        embed = discord.Embed.from_dict({
            **self.bot.footer(ctx.author),
            'title': 'Top Players - Points',
            'color': 0x960808
        })
        record_iter = 0
        for key, value in sorted_list.items():
            placement = list(sorted_list.keys()).index(key)+1
            if placement >= leaderboards_page_min and placement <= leaderboards_page_max:
                embed.add_field(name=str(placement) + '. ' + key, value='%.2f' % value)
        await ctx.send(embed=embed)
    
    @commands.command(name='submit_record', aliases=['submit'])
    async def add_record(self, ctx):
        banned_ = await db.bans.find_one({'uid': ctx.author.id})
        if banned_:
            await ctx.send('You cannot submit records while banned from the list!')
        cancel = 'Successfully aborted form.'

        def check(msg):
            return msg.channel.id == ctx.author.dm_channel.id and msg.author.id == ctx.author.id
        
        try:
            await ctx.author.send('__Record Addition Form__\nThe following DM form will help you add a record to the list. This can be cancelled at any time using `,cancel`.\nWhat is your in-game username? (case-sensitive)')
            user = await self.bot.wait_for('message', check=check, timeout=60)
            if user.content == ',cancel': return await ctx.author.send(cancel)
            await ctx.author.send('What is the in-game name of the challenge?')
            level_name = await self.bot.wait_for('message', check=check, timeout=60)
            if level_name.content == ',cancel': return await ctx.author.send(cancel)
            levela = await db.levels.find({'name': re.compile(level_name.content, re.IGNORECASE)}).to_list(length=None)
            if not levela:
                return await ctx.author.send('Oops! This level is not on the list. Please add this level to the list or correct the level name.')
            print(levela)
            print(level_name.content)
            if level_name.content.lower() in [r['name'].lower() for r in levela]:
                levelb = levela[[r['name'].lower() for r in levela].index(level_name.content.lower())]
            else:
                levelb = levela[0]
            level_name = levelb['name']
            await ctx.author.send('Please provide a link to a video of this completion.')
            video = await self.bot.wait_for('message', check=check, timeout=60)
            if video.content == ',cancel': return await ctx.author.send(cancel)
        except discord.errors.Forbidden:
            return await ctx.send('I cannot DM you! Please enable DMs for the bot to be able to submit a challenge.')
        except asyncio.TimeoutError:
            return await ctx.author.send("Oops! Response took too long.")

        record = await db.channels.find_one({'name': 'records'})
        if not record: return await ctx.send('Error: Record not submitted because the list team cannot view it! Please ask a list member to set a records channel.')

        id_to = await db.counts.find_one_and_update({'name': 'recordCount'}, {'$inc': {'value': 1}})
        await db.records.insert_one({
            'player': user.content,
            'challenge': level_name,
            'video': video.content,
            'status': 'submitted',
            '_id': id_to['value']+1
        })

        video_id = ''
        if 'youtu.be' in video.content:
            video_id = video.content.split('.be/')[-1]
            if '?list=' in video_id:
                video_id = video_id.split('?')[0]
        elif 'youtube.com' in video.content:
            video_id = video.content.split('?v=')[-1]
            if '&list=' in video_id:
                video_id = video_id.split('&')[0]

        await self.bot.get_channel(int(record['id'])).send(embed=discord.Embed.from_dict({
            **self.bot.footer(ctx.author),
            'title': f'New Record Submitted ({int(id_to["value"])+1})',
            'description': 'To accept a record, use `,record <approve/reject> <id> <reason (optional)>`',
            'color': 0x960808,
            'thumbnail': {
                'url': f'https://img.youtube.com/vi/{video_id}/0.jpg'
            },
            'fields': [
                {
                    'name': 'Submitter',
                    'value': str(ctx.author),
                    'inline': True
                },
                {
                    'name': 'Player',
                    'value': user.content,
                    'inline': True
                },
                {
                    'name': 'Challenge',
                    'value': level_name,
                    'inline': True
                },
                {
                    'name': 'Video',
                    'value': video.content,
                    'inline': True
                }
            ]
        }))
        await ctx.author.send('Record successfully submitted to the list team.')
    
    @commands.command(name='record_lookup')
    @commands.has_role('List Mod')
    async def record_lookup(self, ctx, player, challenge):
        record = await db.records.find_one({'player': re.compile(player, re.IGNORECASE), 'challenge': re.compile(challenge, re.IGNORECASE)})
        if not record:
            return await ctx.send('Record not found. Could be a bug with the command, as this is a new addition. Double-check the GD username and the Challenge name, and remember to use quotes around names with spaces.')
        record_id = str(record.get('_id', 'unspecified'))
        await ctx.send('The ID of this record is ' + record_id)
    
    @commands.command(name='list_submissions')
    async def list_submissions(self, ctx):
        unchecked = await db.records.find({'status': 'submitted'}).to_list(length=None)
        unchecked_formatted = ['**' + record.get('challenge', 'N/A') + '** by ' + record.get('player', 'N/A') + ' (#' + str(int(record.get('_id', 0))) + ')' for record in unchecked]
        message_of_submissions = '**List of challenges unreviewed by the team:**\n' + '\n'.join(unchecked_formatted)
        await ctx.send(message_of_submissions)
    
    @commands.command(name='record')
    @commands.has_role('List Mod')
    async def record(self, ctx, ar, rid:int, *, reason=''):

        if ar.lower() in ['approved', 'approve', 'accept']:
            status = 'approved'
        elif ar.lower() in ['rejected', 'reject', 'deny', 'denied']:
            status = 'rejected'
        else:
            return await ctx.send('Invalid action for record. Valid actions include `approve` and `reject`.')
        
        record = await db.records.find_one_and_update({'_id': rid}, {'$set': {'status': status}})
        if not record:
            return await ctx.send('Record ID not found in record listing.')

        loading = await ctx.send(f'Record successfully {status}. Logging info...')

        video_id = ''
        if 'youtu.be' in record['video']:
            video_id = record['video'].split('.be/')[-1]
        elif 'youtube.com' in record['video']:
            video_id = record['video'].split('?v=')[-1]
        
        record_channel = await db.channels.find_one({'name': 'records'})
        if not record_channel: return await loading.edit(content='Record log channel not found. Please add using `,update_channel records #channel`.')
        await self.bot.get_channel(int(record_channel['id'])).send(embed=discord.Embed.from_dict({
            **self.bot.footer(ctx.author),
            'title': f'Record {status.capitalize()} ({int(rid)})',
            'color': 0x960808,
            'thumbnail': {
                'url': f'https://img.youtube.com/vi/{video_id}/0.jpg'
            },
            'fields': [
                {
                    'name': 'Player',
                    'value': record['player'],
                    'inline': True
                },
                {
                    'name': 'Challenge',
                    'value': record['challenge'],
                    'inline': True
                },
                {
                    'name': 'Status',
                    'value': status.capitalize(),
                    'inline': True
                },
                {
                    'name': 'Video',
                    'value': record['video'],
                    'inline': True
                }
            ]
        }))

        await loading.edit(content=f'Record successfully {status}. Logging info... ✅')



def setup(bot):
    bot.add_cog(accounts(bot))
