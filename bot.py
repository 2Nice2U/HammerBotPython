# HammerBotPython
# bot.py

import discord
from discord.ext import commands
from dotenv import load_dotenv  # load module for usage of a .env file (pip install python-dotenv)
import os  # import module for directory management
import datetime
from discord.ext import tasks
import re
from discord.utils import get
from Embeds import RichEmbed
from data import coordinate_channel, application_channel, vote_emotes, role_list, hammer_guild, role_ids, \
    vote_role_id
from coordinates import *
from utils import *
from task import task_list
from bug import mc_bug, regex_normal

# discord token is stored in a .env file in the same directory as the bot
load_dotenv()  # load the .env file containing id's that have to be kept secret for security
TOKEN = os.getenv("DISCORD_TOKEN")  # get our discord bot token from .env

bot = commands.Bot(command_prefix="/")
bot.remove_command('help')

latest_new_person = ""


# print a message if the bot is online
@bot.event
async def on_ready():
    # change status to playing mc
    global latest_new_person
    await bot.change_presence(activity=discord.Game("Technical Minecraft on HammerSMP"))
    print("bot connected")


@bot.event
async def on_message(message):
    # check if the bot is online and not responding to itself
    if message.author == bot.user:
        return

    # if a new message is sent in the application forms channel, the bot will automatically add reactions
    if message.channel.id == application_channel:
        for e in vote_emotes:
            await message.add_reaction(bot.get_emoji(e))

    await mc_bug(message)
    await bot.process_commands(message)  # makes sure other commands will also be processed


@bot.event
async def on_member_join(member):
    global latest_new_person
    latest_new_person = member


@bot.event
async def on_member_remove(member):
    global latest_new_person
    if latest_new_person == member:
        response = "Sadly, **{}** left us already.".format(member.name)
        await bot.get_guild(hammer_guild).system_channel.send(response)


# command to test if the bot is running
@bot.command(name="test", help="test if the bot is working")
@commands.has_role("members")
async def test(ctx):
    response = "Don't worry, I'm working!"
    await ctx.send(response)


@bot.command(name="testing")
@commands.has_role("members")
async def testing(ctx):
    vote_role = ctx.guild.get_role(vote_role_id)
    print(vote_role)


@bot.command(name="temp")
async def help_command(ctx, command=""):
    roles = ctx.author.roles
    com = bot.commands
    print(com)
    for i in com:
        name = i.name
        check = i.checks[0](ctx)
        print(name, check)


# command to test if the bot is running
@bot.command(name="role", help="Give yourself the \"tour giver\" role")
@commands.has_role("members")
async def role(ctx, action, *args):
    if action == "list":
        await ctx.send(role_list)
        return

    # check if you have provided a role, if not tell the user to do so
    if not args:
        response = "You have not specified a role"
        await ctx.send(response)
        return

    # combine the *args tuple into a string role
    role_arg = " ".join(args)

    # give the tour giver role if the user asks for this
    if role_arg in role_ids:
        member = ctx.message.author  # the author of the message, part of the discord.Member class
        guild_role = bot.get_guild(hammer_guild).get_role(role_ids[role_arg])  # the role needed to add

        if action == "add" and guild_role in member.roles:
            response = "I'm sorry but you already have this role"
            await ctx.send(response)
            return
        elif action == "remove" and guild_role not in member.roles:
            response = "I'm sorry but you don't have this role."
            await ctx.send(response)
            return

        # if the user doesn't have the right perms, throw an exception
        try:
            if action == "add":
                await member.add_roles(guild_role)
                response = "You have been successfully given the tour giver role! Congratulations."
                await ctx.send(response)

            elif action == "remove":
                await member.remove_roles(guild_role)
                response = "The role has successfully been removed, congratulations"
                await ctx.send(response)

        except discord.errors.Forbidden:
            response = "Missing permissions"
            await ctx.send(response)

    elif role_arg in get_server_roles(ctx):
        response = "I'm sorry but i'm afraid you can't add/remove that role to yourself using the bot."
        await ctx.send(response)

    # if the role is not a role one can add, throw an exception
    else:
        response = "I'm sorry but i'm afraid that role doesn't exist"
        await ctx.send(response)


# command to test if the bot is running
@bot.command(name="stop_lazy", help="command to tell someone to stop lazy")
@commands.has_role("members")
async def stop_lazy(ctx, mention="jerk"):
    await ctx.message.delete()
    response = "Stop Lazy {}".format(mention)
    await ctx.send(response)
    await ctx.send(file=discord.File('stop_lazy.png'))


@bot.command(name="CMP", help="command to get the CMP IP in your DM's")
@commands.has_any_role("CMP access", "members")
async def CMP(ctx, mention="jerk"):
    CMP_IP = os.getenv("CMP_IP")
    response = "Check your DM's"
    await ctx.author.send(CMP_IP)
    await ctx.send(response)


# command to test if the bot is running
@bot.command(name="vote", help="command to vote")
@commands.has_role("members")
async def vote(ctx, vote_type="", *args):
    await ctx.message.delete()

    if not args:
        response = "I'm sorry but you haven't specified anything to vote on."
        await ctx.send(response, delete_after=5)

    if not vote_type or vote_type not in ("yes_no", "multiple"):
        response = "I'm sorry but you haven't specified a correct vote type."
        await ctx.send(response, delete_after=5)

    vote_role = ctx.guild.get_role(vote_role_id)

    if vote_type == "yes_no":
        string_votes = " ".join(args)
        embed = discord.Embed(
            colour=0xe74c3c,
            title=string_votes,
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="Poll created on {}".format(str(datetime.datetime.now())[:-7]))
        poll_message = await ctx.send(embed=embed)
        for e in vote_emotes:
            await poll_message.add_reaction(bot.get_emoji(e))
        ping = await ctx.send(vote_role.mention)
        await ping.delete()

    elif vote_type == "multiple":
        poll, poll_list, introduction = format_conversion(args, "poll")
        embed = discord.Embed(
            color=0xe74c3c,
            title=introduction,
            description=poll[:-1] + " "
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="Poll created on {}".format(str(datetime.datetime.now())[:-7]))
        poll_message = await ctx.send(embed=embed)
        for n in range(len(poll_list)):
            await poll_message.add_reaction(discord_letters[n])
        ping = await ctx.send(vote_role.mention)
        await ping.delete()


# /bulletin add project description | {first bulletin} & {second bulletin} & {third bulletin}
@bot.command(name="bulletin")
@commands.has_role("members")
async def bulletin(ctx, action, *args):
    await ctx.message.delete()
    """if ctx.channel.id != coordinate_channel:
        response = "Sorry, wrong channel buddy"
        await ctx.send(response, delete_after=5)
        return"""
    await task_list(ctx=ctx, action=action, args=args, use="bulletin")


@bot.command(name="todo")
@commands.has_role("members")
async def todo(ctx, action, *args):
    await ctx.message.delete()
    await task_list(ctx=ctx, action=action, args=args, use="todo")


@bot.command(name="coords")
@commands.has_role("members")
async def coordinates(ctx, action, *args):
    await ctx.message.delete()
    if ctx.channel.id == coordinate_channel:
        await task_list(ctx=ctx, action=action, args=args, use="bulletin")


@bot.command(name="mass_delete")
@commands.has_role("admin")
async def mass_delete(ctx, number_of_messages):
    await ctx.message.delete()
    if number_of_messages > 200:
        response = "You want to delete too many messages at once, I'm sorry."
        await ctx.send(response)
    channel_history = await ctx.channel.history(limit=int(number_of_messages)).flatten()
    for message in channel_history:
        await message.delete()


@tasks.loop(seconds=5)
async def forms():
    pass


forms.start()
bot.run(TOKEN)
