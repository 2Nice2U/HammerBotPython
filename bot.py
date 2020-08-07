# HammerBotPython
# main
# bot.py

"""
The source code can be found at:
https://github.com/viktor40/HammerBotPython

bot.py is the main file for the bot.
This file contains task loops for bug and version reporting as well as the main bot loop.

In this file we will check for different discord events like on_member_join, on_member_leave and on_message to handle
different tasks.

This file also contains all the commands that the bot listens to.
It also has dummy commands that are used by the help command so this bot lists the HammerBot Java commands too.

Finally this file will also check for errors inside commands, but also in on_command_error. After an error gets
detected the bot will notify the user. The error message will be deleted after 15 seconds.

The required packages can be found in requirements.txt.
More info can be found in readme.md.

This also requires a .env file containing the following data:
DISCORD_TOKEN
CMP_IP
mojira_username
mojira_password

This file cannot be found on github for security reasons.
"""

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os

from other.role import role_giver
from other.task import task_list
from other.voting import vote_handler

import help_command.help_data as hd
from help_command.helping import helper

from bug.fetcher import mc_bug
import bug.fixed as bug_fix
import bug.utils as bug_utils
import bug.versions as mc_version

import utilities.data as data

# discord token is stored in a .env file in the same directory as the bot
load_dotenv()  # load the .env file containing id's that have to be kept secret for security
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='/')
bot.remove_command('help')
bot.latest_new_person = ""
bot.last_bug_loop = 0


# Print a message if the bot is online and change it's status.
@bot.event
async def on_ready():
    print('bot connected')
    mc_version.get_versions(bot)
    await bot.change_presence(activity=discord.Game('Technical Minecraft on HammerSMP'))


@bot.event
async def on_message(message):
    # Make sure the bot doesn't respond to itself.
    if message.author == bot.user:
        return

    # Ff a new message is sent in the application forms channel, the bot will automatically add reactions.
    if message.channel.id == data.application_channel:
        for e in data.vote_emotes:
            await message.add_reaction(bot.get_emoji(e))

    if '/bug_vote' not in message.content:
        await mc_bug(message)

    # We need this since since overriding the default provided on_message forbids any extra commands from running.
    await bot.process_commands(message)


# Check which user was the latest to join and store this in a global variable.0
@bot.event
async def on_member_join(member):
    bot.latest_new_person = member


# When the newest member leaves, there is a notification in th system channel.
@bot.event
async def on_member_remove(member):
    if bot.latest_new_person == member:
        response = 'Sadly, `{}` left us already.'.format(member.name)
        await bot.get_guild(data.hammer_guild).system_channel.send(response)


# Checking for new reactions being added.
# on_raw_reaction_add is used since it is called regardless of the state of the internal message cache.
@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id == data.vote_channel_id:
        pass


# This will handle some errors and suppress raising them. It will also report to the user what the error was.
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.send("This command doesn't exist", delete_after=15)

    elif isinstance(error, discord.ext.commands.MissingPermissions):
        await ctx.send("You don't have permission to do that!", delete_after=15)

    elif isinstance(error, discord.ext.commands.MissingRole):
        await ctx.send("You don't have the correct role to use that command!", delete_after=15)

    elif isinstance(error, discord.ext.commands.CheckFailure):
        print('Check failed')

    else:
        print('unknown error: {}'.format(error))
        raise error


# This command will provide the users with a way of testing if the bot is online.
@bot.command(name='ping', help=hd.ping_help, usage=hd.ping_usage)
async def ping(ctx):
    response = 'HammerBot Python is online and has a ping of {} ms.'.format(str(bot.latency)[:5])
    await ctx.send(response)


@bot.command(name='help', help=hd.help_help, usage=hd.help_usage)
@commands.has_role('members')
async def helping(ctx, command=''):
    try:
        await ctx.send(embed=helper(ctx, bot, command))
    except KeyError:
        await ctx.send("Help Error: This command doesn't exist.", delete_after=10)


# This is a command purely for testing purposes during development.
@bot.command(name='testing', help=hd.testing_help, usage=hd.testing_usage)
@commands.has_role('members')
async def testing(ctx, *args: str):
    pass


# This command will be used so members can give themselves some roles with a command
@bot.command(name='role', help=hd.role_help, usage=hd.role_usage)
@commands.has_role('members')
async def role(ctx, action, *args):
    await role_giver(ctx, action, args, bot)


# Tell someone to stop being lazy
@bot.command(name='stop_lazy', help=hd.stop_lazy_help, usage=hd.stop_lazy_usage)
@commands.has_role('members')
async def stop_lazy(ctx, mention='jerk'):
    await ctx.message.delete()
    response = 'Stop Lazy {}'.format(mention)
    await ctx.send(response)
    await ctx.send(file=discord.File('stop_lazy.png'))


@bot.command(name='CMP', help=hd.CMP_help, usage=hd.CMP_usage)
@commands.has_any_role('CMP access', 'members')
async def cmp(ctx):
    CMP_IP = os.getenv('CMP_IP')
    response = "Check your DM's"
    await ctx.author.send(CMP_IP)
    await ctx.send(response)


# Command that will handle voting, see voting.py.
@bot.command(name='vote', help=hd.vote_help, usage=hd.vote_usage)
@commands.has_role('members')
async def vote(ctx, vote_type='', *args):
    await ctx.message.delete()
    await vote_handler(ctx, vote_type, args, bot)


# Command to create, add, remove and delete bulletins in the bulletin board.
@bot.command(name='bulletin', help=hd.bulletin_help, usage=hd.bulletin_usage)
@commands.has_role('members')
async def bulletin(ctx, action, *args):
    await ctx.message.delete()
    await task_list(ctx=ctx, action=action, args=args, use='bulletin')


# Command to add a to do list to a project channel and pin it.
@bot.command(name='todo', help=hd.todo_help, usage=hd.todo_usage)
@commands.has_role('members')
async def todo(ctx, action, *args):
    await ctx.message.delete()
    await task_list(ctx=ctx, action=action, args=args, use='todo')


# Command to handle the coordinate list. There is one embed per dimension
@bot.command(name='coordinates', help=hd.coordinates_help, usage=hd.coordinates_usage)
@commands.has_role('members')
async def coordinates(ctx, action, *args):
    await ctx.message.delete()
    if ctx.channel.id == data.coordinate_channel:
        await task_list(ctx=ctx, action=action, args=args, use="bulletin")


"""@bot.command(name="bug_vote", help=hd.bug_vote_help, usage=hd.bug_vote_usage)
@commands.has_any_role("members", "comrades")
async def bug_vote(ctx, bug):
    embed = bug_utils.vote(bug)
    print(embed)
    await ctx.send(embed=embed)"""


# A admin only command to mass delete messages in case of a bad discord discussion.
@bot.command(name='mass_delete', help=hd.mass_delete_help, usage=hd.mass_delete_usage)
@commands.has_role('admin')
async def mass_delete(ctx, number_of_messages: int):
    await ctx.message.delete()
    if number_of_messages > 250:
        response = "You want to delete too many messages at once, I'm sorry."
        await ctx.send(response)
        return
    else:
        await ctx.channel.purge(limit=number_of_messages)


"""
Registering dummy commands so it can be easily implemented to work with other functions like errors and help commands.
These dummy commands are used in HammerBot Java
"""


@bot.command(name='whitelist', help=hd.whitelist_help, usage=hd.whitelist_usage)
@commands.has_role('admin')
async def whitelist(ctx, *args):
    pass


@bot.command(name='online', help=hd.online_help, usage=hd.online_usage)
async def online(ctx, *args):
    pass


@bot.command(name='scoreboard', help=hd.scoreboard_help, usage=hd.scoreboard_usage)
async def scoreboard(ctx, *args):
    pass


@bot.command(name='uploadFile', help=hd.upload_file_help, usage=hd.upload_file_usage)
@commands.has_role('members')
async def upload_file(ctx, *args):
    pass


# this loop is used to check for new updates on the bug tracker every 60 seconds
@tasks.loop(seconds=50, reconnect=True)
async def fixed_bug_loop():
    try:
        # on startup this is ran the first time but the bot isn't yet online so this would return []
        # to make sure it doesn't break we check for this
        channel = bot.get_channel(data.fixed_bug_channel_id)
        if channel:
            await bug_fix.fixes_handler(bot)

    # exceptions need to be handled, otherwise the loop might break
    except Exception as e:
        print(e)
        raise e


@tasks.loop(seconds=75, reconnect=True)
async def version_update_loop():
    try:
        # on startup this is ran the first time but the bot isn't yet online so this would return []
        # to make sure it doesn't break we check for this
        channel = bot.get_channel(data.fixed_bug_channel_id)
        if channel:
            await mc_version.version_update_handler(bot, channel)

    # exceptions need to be handled, otherwise the loop might break
    except Exception as e:
        print(e)


version_update_loop.start()  # start the loop to check for new versions
fixed_bug_loop.start()  # start the loop to check for bugs
bot.run(TOKEN)  # start the bug loop
