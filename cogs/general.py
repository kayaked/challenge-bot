import discord
from discord.ext import commands
import random
import pytz
from motor import motor_asyncio
from datetime import datetime

client = motor_asyncio.AsyncIOMotorClient()
db = client['Discord']

# List of help descriptions and information. To be moved into a separate second config file.
HELP = {
    'submit': {
        'main': 'Submit a record to the challenge list. You will receive a form to fill out in DMs from the bot, so be sure to allow direct messages. List Helpers are given the option to automatically approve or deny records.',
        'example': ['submit']
    },
    'list': {
        'main': 'Lists the current hardest challenges. By specifying a page with `,list #` you can view the next page of the list. Legacy list begins at #51.',
        'example': ['list <page (optional)>']
    },
    'challenge': {
        'main': 'View more information about a challenge on the list.',
        'example': ['challenge <name>']
    },
    'star_leaderboard': {
        'main': 'Displays a list of the top daily stargrinders.',
        'example': ['star_leaderboard']
    },
    'faq': {
        'main': 'Answers to a handful of basic frequently asked questions.',
        'example': ['faq <question (optional)']
    },
    'help': {
        'main': 'Displays the help menu.',
        'example': ['help <command (optional)>']
    },
    'suggest': {
        'main': 'Forwards suggestions given to the list team.',
        'example': ['suggest <suggestion>']
    },
    'account': {
        'main': 'View a user\'s records, verifications and creations. If the account cannot be found, try using a more specific username or searching for their name\'s spelling in other commands.',
        'example': ['account <name>']
    },
    'leaderboard': {
        'main': 'Views the current top players in list points.',
        'example': ['leaderboard <page (optional)>']
    },
    'add_level': {
        'main': 'Adds a level to the challenge list using a discord form.',
        'example': ['add_level']
    },
    'move_level': {
        'main': 'Changes a level\'s placement on the challenge list, via its current placement, name or ID.',
        'example': ['move_level <placement|name|id> <new placement>', 'move_level "Sheol Death" 1', 'move_level 1 4', 'move_level 15859369 5']
    },
    'remove_level': {
        'main': 'Removes a level from the challenge list.',
        'example': ['remove_level <placement|name|id>', 'remove_level "Africa Chamber"', 'remove_level 24', 'remove_level 14306238']
    },
    'record': {
        'main': 'Used for accepting and rejecting list record submissions.',
        'example': ['record accept <submission id>', 'record reject <submission_id>']
    },
    'fix_user': {
        'main': 'Used to rename users in the database if they have incorrect names.',
        'example': ['fix_user <old name> <new name>', 'fix_user Ncat "Nyan Cat"']
    },
    'fix_challenge': {
        'main': 'Used to rename levels in the database if they have incorrect names.',
        'example': ['fix_challenge <old name> <new name>', 'fix_challenge "box benta" "Box Benta"']
    },
    'add_stars': {
        'main': 'Adds Cool-Stars to a discord user in the database.',
        'example': ['remove_stars <user> 1']
    },
    'remove_stars': {
        'main': 'Removes Cool-Stars from a discord user in the database.',
        'example': ['remove_stars <user> 1']
    },
    'update_channel': {
        'main': 'Updates which channel is used for records or suggestions',
        'example': ['update_channel suggest #channel', 'update_channel records #channel']
    },
    'verify': {
        'main': 'Verify a user\'s discord account with their records.',
        'example': ['verify <gd_username> @Discord']
    },
    'record_lookup': {
        'main': 'Look up a record ID for a certain user\'s completion of a challenge',
        'example': ['record_lookup <player> <challenge>', 'record_lookup Andrew7171 D']
    },
    'list_submissions': {
        'main': 'View unapproved and unrejected challenges waiting for review',
        'example': ['list_submissions']
    }
}

FAQ = {
    'rules': ['What are the Challenge List rules?', '`Levels must be shorter than 30 seconds. (Tiny and Short on the in-game time counter.)\nMinimal Proof is required. (e.g. Clicks and No LDM).\nFPS Bypass is allowed on the list, but only between 50fps and 360fps.\nThe level cannot be a copy of an already uploaded challenge; except on a few occasions, those being.\nA Buffed Version made by the same creator. (In which case the original gets removed.)\nIt is a part of a series by the same creator. (E.G. the "gay lol" series by Doopliss.)\nSignificant enough changes to play completely differently.\nAcceptable Changes: Speed Changes, Different Decoration, Buffs/Nerfs. (If it affects the gameplay enough.)\nNot Acceptable Changes: Very Minor Buffs, or none at all; unless if it of a humanly impossible level.\nIf you beat a hack verified challenge, you will be counted as the verifier, and the level can be added.`'],
    'submitting': ["How do I submit a record to the list?", "To submit a record, use the command ,submit. The bot will DM you a form to fill out with information about your completion, so enable DMs when submitting. If you still have troubles submitting or get no response from the bot, contact a list staff or a developer. After submitting, your submission is forwarded to the list team who will approve or reject it after making a decision."],
    'accounts': ["Why don't I show up in the top players?", "Be sure to submit your records using ,submit. Use the right username or else you could risk points not being equally counted until fixed by a staff member. If you ask staff to verify your account properly, all your records will be linked to your account."],
    'wrong_player_names': ["I used the wrong player name when submitting.", "You can ask a List Helper or above for help with incorrect names to get your list name changed."]
}

class general(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
    
    @commands.command(name='help', aliases=['h'])
    async def help(self, ctx, command=None):
        if command:
            command_info = HELP.get(command)
            if not command_info:
                for cmd in self.bot.commands:
                    if command in cmd.aliases:
                        command = cmd.name
                        command_info = HELP.get(command)
            if command_info:
                structure = discord.Embed.from_dict({
                    **self.bot.footer(ctx.author),
                    'title': command,
                    'description': command_info.get('main', 'No info available!'),
                    'color': 0x960808,
                    'fields': [
                        {
                            'name': 'Format',
                            'value': '\n'.join([f'`{i}`' for i in command_info.get('example', ['No example available!'])])
                        }
                    ]
                })
                return await ctx.send(embed=structure)
        structure = discord.Embed.from_dict({
            **self.bot.footer(ctx.author),
            "title": "Usable Commands",
            "description": "These are all the commands available for use, as sorted by the category the command is in.\nUse `help <command>` to find out more information about a command.",
            "color": 0x960808,
            "thumbnail": {
                "url": str(self.bot.user.avatar_url)
            },
            "fields": [
                {
                    "name": "Challenges",
                    "value": "`submit`, `list`, `challenge`, `record`",
                    "inline": True
                },
                {
                    "name": "Daily",
                    "value": "`star_leaderboard`, `add_stars`, `remove_stars`",
                    "inline": True
                },
                {
                    "name": "General",
                    "value": "`faq`, `help`, `ping`, `suggest`",
                    "inline": True
                },
                {
                    "name": "Players",
                    "value": "`account`, `leaderboard`, `verify`",
                    "inline": True
                },
                {
                    "name": "List Moderation",
                    "value": "`add_level`, `move_level`, `remove_level`, `fix_name`, `fix_challenge`, `update_channel`",
                    "inline": True
                }
            ]
        })

        # Checks if user is banned, and adds respective help message. Also gets and formats duration of ban.
        banned_bool = await db.bans.find_one({'uid': ctx.author.id})
        if banned_bool:
            date = datetime.utcfromtimestamp(banned_bool['expires']).astimezone(pytz.timezone('US/Eastern')).strftime('%B %-d, %Y')
            structure.set_footer(text=f'You are currently banned from the Challenge List. If you feel that this ban is unfair or incorrect, please ask a list team member for further assistance. (Expires {date})')

        await ctx.send(embed=structure)

    @commands.command(name='faq')
    async def faq(self, ctx, question=None):
        config = self.config
        config_faq = FAQ
        faq_message = 'Use this command with the format `,faq <question>`.\nI can answer questions about ' + ', '.join([f'`{q}`' for q in config_faq.keys()])
        structure = {
            **self.bot.footer(ctx.author),
            "title": "Frequently Asked Questions",
            "description": "By using the `faq` command, I can answer various questions you have about the list and your records.\n",
            "color": 0x960808
        }
        if type(question) == str:
            answer = config_faq.get(question)
            if answer:
                structure['title'] = f'FAQ: {answer[0]}'
                structure['description'] = answer[-1]
            else:
                structure['description'] = "Oops! I don't know that one. Feel free to ask a list staff member for more assistance if necessary.\n" + faq_message
        else:
            structure['description'] += faq_message
        
        embed = discord.Embed.from_dict(structure)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='ping')
    async def ping(self, ctx):
        if ctx.author.id in self.config.AUTHORIZED:
            await ctx.send(f'**Pong!** Pinged back in {"%.2f" % self.bot.latency}ms.')
    
    @commands.command(name='suggest')
    async def suggest(self, ctx, *, suggestion=None):
        if not suggestion:
            return await ctx.send('Oops! You did not provide a valid suggestion.')
        structure = {
            **self.bot.footer(ctx.author),
            "title": "Suggestion from " + str(ctx.author),
            "description": suggestion,
            "color": 0x960808
        }
        channel_id = await db.channels.find_one({
            'name': 'suggest'
        })
        await self.bot.get_channel(int(channel_id['id'])).send(embed=discord.Embed.from_dict(structure))
        await ctx.send(f'**Success!** Your suggestion has been forwarded to the list staff.')


def setup(bot):
    bot.add_cog(general(bot))
