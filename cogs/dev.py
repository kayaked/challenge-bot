# Eval command taken from Corona by jcak (kayaked) and exofeel (ms7m). Permission was granted.

import ast, sys, json
import discord
from discord.ext import commands
import asyncio
import traceback
import discord
import inspect
import aiohttp
import textwrap
import getpass
import time
from contextlib import redirect_stdout
import io
import calendar, datetime
import json
import os

try:
    import pyduktape
except Exception:
    pass
from os import listdir
from os.path import isfile, join
# to expose to the eval command
import datetime
from collections import Counter

class Dev(commands.Cog):


    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.config = bot.config
        self.sessions = set()
    
    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content[3:][:-3].split('\n')[1:])
        if content.startswith('```python') and content.endswith('```'):
            return '\n'.join(content[3:][:-3].split('\n')[1:])
        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, e):
        if e.text is None:
            return f"```python\n{e.__class__.__name__}: {e}\n```"
        else:
            pass
        return f'```python\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    @discord.ext.commands.command(hidden=True, name='js_eval', aliases=['miko_eval'])
    @discord.ext.commands.is_owner()
    async def _js_eval(self, ctx, *, body: str):
        jsctx = pyduktape.DuktapeContext()
        jsctx.set_globals(**globals(), ctx=ctx, bot=self.bot, channel=ctx.message.channel)
        a = jsctx.eval_js(self.cleanup_code(body))
        await ctx.send(f'```js\n{a}\n```')

    @discord.ext.commands.command(hidden=True, name='eval')
    async def _eval(self, ctx, *, body: str):
        
        if ctx.author.id not in [361181986531835904, 287617643853381633]: return

        """Evaluates a code"""
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.message.channel,
            'author': ctx.message.author,
            'guild': ctx.message.guild,
            'message': ctx.message,
            'self':super(),
            '_': self._last_result,
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        if "input(" in to_compile or "input (" in to_compile:
            return await ctx.send("nice try sweaty", delete_after=3)

        try:
            exec(to_compile, env)
        except Exception as e:
            embed = discord.Embed(title="Exception occured!", description="For privacy, exception log has been dm'd to you.", color=0x960808)
            await ctx.send(embed=embed)
            user = ctx.author
            return await user.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            embed = discord.Embed(title="Exception occured!", description="For privacy, exception log has been dm'd to you.", color=0x960808)
            await ctx.send(embed=embed)
            user = ctx.author
            await user.send(f'```python\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```python\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```python\n{value}{ret}\n```')

    @discord.ext.commands.command(name='reload', hidden=True, aliases=['rl'])
    @discord.ext.commands.is_owner()
    async def _reload(self, ctx, *, module=None):
        try:
            cogs = self.bot.config.COGS
            if module: cogs = [module]
            for cog in cogs:
                try:
                    self.bot.unload_extension("cogs." + cog)
                except discord.ext.commands.errors.ExtensionNotLoaded:
                    pass
                self.bot.load_extension("cogs." + cog)
        except Exception:
            embed = discord.Embed(title="Exception occured!", description="For privacy, exception log has been dm'd to you.", color=0x960808)
            await ctx.send(embed=embed)
            user = ctx.author
            await user.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.message.add_reaction('✅')

    @discord.ext.commands.command(name='unload', hidden=True, aliases=['ul'])
    @discord.ext.commands.is_owner()
    async def _unload(self, ctx, *, module=None):
        try:
            cogs = self.bot.config.COGS
            if module: cogs = [module]
            for cog in cogs:
                self.bot.unload_extension("cogs." + cog)
        except Exception:
            embed = discord.Embed(title="Exception occured!", description="For privacy, exception log has been dm'd to you.", color=0x960808)
            await ctx.send(embed=embed)
            user = ctx.author
            await user.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send('trololololololo')
    
    @discord.ext.commands.command(name="embed")
    @discord.ext.commands.is_owner()
    async def embed(self, ctx, *, body):
        body=self.cleanup_code(body)
        
        try:
            body = json.loads(body)
        except:
            try:
                body = ast.literal_eval(body)
                assert isinstance(body, dict)
            except:
                return await ctx.send("Not a valid embed index! (JSON or python dict)", delete_after=3)
        try:
            return await ctx.send(embed=discord.Embed.from_data(body))
        except:
            return await ctx.send("Not a valid embed index! (Missing fields, see leovoel embed visualizer)", delete_after=3)
    
                
def setup(bot):
    bot.add_cog(Dev(bot))
