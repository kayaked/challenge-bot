import discord
from discord.ext import commands
from motor import motor_asyncio
import asyncio
import aiohttp

client = motor_asyncio.AsyncIOMotorClient()
db = client['Discord']

class challenges(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
    
    async def log_level(self, lvtype, level):
        title = lvtype.capitalize()

        record_channel = await db.channels.find_one({'name': 'records'})
        if not record_channel: return
        await self.bot.get_channel(int(record_channel['id'])).send(embed=discord.Embed.from_dict({
            'title': f'Level {title} (#{level["placement"]})',
            'description': level['name'] + ' by ' + level['publisher'],
            'color': 0x960808,
            'fields': [
                {
                    'name': 'Verifier',
                    'value': level['verifier'],
                    'inline': True
                },
                {
                    'name': 'Creators',
                    'value': ', '.join(level['creators']),
                    'inline': True
                },
                {
                    'name': 'Level ID',
                    'value': level['id'],
                    'inline': True
                },
                {
                    'name': 'Video',
                    'value': level['video'],
                    'inline': True
                }
            ]
        }))

    @commands.command(name='add_level', aliases=['add_challenge', 'addlevel'])
    @commands.has_role('List Helper')
    async def add_level(self, ctx):
        def chcheck(msg):
            return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id
        
        cancel = 'Successfully aborted form.'
        
        try:
            await ctx.send('__Level Addition Form__\nThe following form will help you add a challenge to the list.\nUse `,cancel` at any time to cancel the form.\nWhat is the in-game ID of this challenge?')
            level_id = await self.bot.wait_for('message', check=chcheck, timeout=60)
            if level_id.content == ',cancel': return await ctx.send(cancel)
            await ctx.send('What position (number value) will this challenge place on the challenge list?')
            placement = await self.bot.wait_for('message', check=chcheck, timeout=60)
            if placement.content == ',cancel': return await ctx.send(cancel)
            await ctx.send('Who is the verifier of this level?')
            verifier = await self.bot.wait_for('message', check=chcheck, timeout=60)
            if verifier.content == ',cancel': return await ctx.send(cancel)
            await ctx.send('Who are the level\'s creators? Please Separate Names with commas, such as `El3cTr0`, `Nyan Cat`. **Not following this could result in incorrect records.**')
            creators = await self.bot.wait_for('message', check=chcheck, timeout=60)
            if creators.content == ',cancel': return await ctx.send(cancel)
            await ctx.send('Please provide a link to a video of this challenge.')
            video = await self.bot.wait_for('message', check=chcheck, timeout=60)
            if video.content == ',cancel': return await ctx.send(cancel)
        except asyncio.TimeoutError:
            return await ctx.send("Oops! Response took too long.")
        
        loading = await ctx.send('Challenge pending addition, please wait...')

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as sesh:
                async with sesh.get(f"https://gdbrowser.com/api/level/{level_id.content}") as resp:
                    level_info = await resp.json()
            level_name = level_info.get('name', 'Unknown')
            level_publisher = level_info.get('author', 'Unknown')
        except:
            try:
                await ctx.send('**ERROR** This level was not found on the GD servers. Either put in the following information manually or try again later.\nWhat is the name of this challenge? (case-sensitive)')
                level_name = (await self.bot.wait_for('message', check=chcheck, timeout=60)).content
                if level_name == ',cancel': return await ctx.send(cancel)
                await ctx.send('Whose account is this challenge published on?')
                level_publisher = (await self.bot.wait_for('message', check=chcheck, timeout=60)).content
                if level_publisher == ',cancel': return await ctx.send(cancel)
            except:
                return await ctx.send("Oops! Response took too long.")
                
        
        await db.levels.update_many(
            {'placement': {'$gt': int(placement.content)-1}},
            {'$inc': {'placement': 1}}
        )

        funny_level = {
            'name': level_name,
            'placement': int(placement.content),
            'verifier': verifier.content,
            'creators': creators.content.split(', '),
            'video': video.content,
            'id': level_id.content,
            'publisher': level_publisher
        }

        await db.levels.insert_one(funny_level)
        await self.log_level('added', funny_level)

        await ctx.send('Setup completed successfully.')
    
    @commands.command(name='remove_level')
    @commands.has_role('List Helper')
    async def remove_level(self, ctx, aspect:str='', *, value:str=''):
        if aspect not in ['placement', 'name', 'id']:
            return await ctx.send('Invalid identifier! Please remove a level based on its `placement`, `name`, or `id`.\nExample: `,remove_level placement 33` `,remove_level name Georgia Chamber` `,remove_level id 59859310`')
        if not value:
            return await ctx.send('Oops! No value was specified.')
        if aspect == 'placement': value = int(value)
        deleted_level = await db.levels.find_one_and_delete({aspect: value})
        await self.log_level('removed', deleted_level)
        
        await db.levels.update_many(
            {'placement': {'$gt': deleted_level['placement']}},
            {'$inc': {'placement': -1}}
        )

        await ctx.send(f'Successfully updated list by removing level `{deleted_level["name"]}`.')
    
    @commands.command(name='move_level', aliases=['place_level'])
    @commands.has_role('List Helper')
    async def move_level(self, ctx, aspect:str='', *, value):

        def check(msg):
            return msg.channel.id == ctx.channel.id and msg.author.id == ctx.author.id
        
        if aspect not in ['placement', 'name', 'id']:
            return await ctx.send('Invalid identifier! Please place a level based on its `placement`, `name`, or `id`.\nExample: `,move_level placement ')
        if not value:
            return await ctx.send('Oops! No value was specified.')
        if aspect == 'placement': value = int(value)

        await ctx.send('What is this level\'s new placement on the list?')
        placement_message = await self.bot.wait_for('message', check=check, timeout=30)

        placement = int(placement_message.content)

        promise = await ctx.send('Editing the list...')

        deleted_level = await db.levels.find_one_and_delete({aspect: value})
        
        # 14 --> 17
        # Move spots 15,16,17 to 14,15,16
        #
        # 17 --> 14
        # Move Spots 14,15,16 to 15,16,17
        if placement > deleted_level['placement']:
            print('Moved down')
            await db.levels.update_many({
                'placement': {
                    '$lte': placement, '$gte': deleted_level['placement']+1
                }
            },
            {
                '$inc': {
                    'placement': -1
                }
            })
        elif placement < deleted_level['placement']:
            print('Moved up')
            await db.levels.update_many({
                'placement': {
                    '$gte': placement, '$lte': deleted_level['placement']-1
                }
            },
            {
                '$inc': {
                    'placement': 1
                }
            })
        
        deleted_level['placement'] = placement
        await db.levels.insert_one(deleted_level)
        await self.log_level('moved', deleted_level)

        await promise.edit(content=f'List placement for {deleted_level["name"]} successfully updated to #{placement}.')
        


    @commands.command(name='list')
    async def challenge_list(self, ctx, page:int=1):
        challenges = await db.levels.count_documents({})
        challenge_page_max = page*10
        challenge_page_min = challenge_page_max-9
        if challenge_page_max > challenges: challenge_page_max = challenges
        embed = discord.Embed.from_dict({
            **self.bot.footer(ctx.author),
            'title': 'Top Challenges',
            'color': 0x960808
        })
        the_list = db.levels.find({
            'placement': {'$gte': challenge_page_min, '$lte': challenge_page_max}
        })
        the_list = await the_list.to_list(length=challenge_page_max-((page-1)*10))
        the_list = sorted(the_list, key=lambda j: j['placement'])
        for i in the_list:
            embed.add_field(name='#' + str(i['placement']), value=i['name'])
        if page>5:
            embed.title = 'Legacy Challenges'
        embed.description = f'To view the next page of the list, use `,list {page+1}`.\nTo view more info about a challenge, use `,challenge <name/placement>`.'
        await ctx.send(embed=embed)
    
    @commands.command(name='challenge', aliases=['chall', 'level'])
    async def view_challenge(self, ctx, *, query=None):
        if not query:
            return await ctx.send('Oops! No search terms were specified.')
        results = await db.levels.find({'$text': {'$search': query}}).to_list(length=10)
        result = None
        if query.lower() in [r['name'].lower() for r in results]:
            result = results[[r['name'].lower() for r in results].index(query.lower())]
        else:
            try:
                result = results[0]
            except IndexError:
                pass
        if query.isdigit():
            placement_result = await db.levels.find_one({'placement': int(query)})
            if placement_result:
                result = placement_result
        if not result:
            return await ctx.send('Oops! This challenge was not found on the list.')
        
        video_id = ''
        if 'youtu.be' in result['video']:
            video_id = result['video'].split('.be/')[-1]
        elif 'youtube.com' in result['video']:
            video_id = result['video'].split('?v=')[-1]

        victors = await db.records.find({'challenge': result['name']}).to_list(length=100)
        victor_field = ', '.join([f'[{i["player"]}]({i["video"]})' for i in victors if i['player'] != result['verifier'] and i['status'] == 'approved'])
        
        if result['placement'] <= 50:
            points = '%.2f' % (-(.08*result['placement']-6)**3+5)
        else:
            points = 'N/A'
        structure = discord.Embed.from_dict({
            **self.bot.footer(ctx.author),
            'title': f'#{result["placement"]} ' + result['name'] + ' by ' + result['publisher'],
            'description': result['id'],
            'url': result['video'],
            'color': 0x960808,
            'thumbnail': {
                'url': f'https://img.youtube.com/vi/{video_id}/0.jpg'
            },
            'fields': [
                {
                    'name': 'Creator(s)',
                    'value': result['creators'] if type(result['creators']) == str else ', '.join(result['creators']),
                    'inline': True
                },
                {
                    'name': 'Verifier',
                    'value': result['verifier'],
                    'inline': True
                },
                {
                    'name': 'Points',
                    'value': points,
                    'inline': True
                },
                {
                    'name': 'Victors',
                    'value': victor_field if victor_field else 'None',
                    'inline': True
                }
            ]
        })

        await ctx.send(embed=structure)

def setup(bot):
    bot.add_cog(challenges(bot))
