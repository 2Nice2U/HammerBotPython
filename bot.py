# HammerBotPython
# bot.py

import discord
from discord.ext import commands
from dotenv import load_dotenv  # load module for usage of a .env file (pip install python-dotenv)
import os  # import module for directory management
from discord.utils import get
from data import coordinate_channel, application_channel, vote_emotes

# discord token is stored in a .env file in the same directory as the bot
load_dotenv()  # load the .env file containing id's that have to be kept secret for security
TOKEN = os.getenv("DISCORD_TOKEN")  # get our discord bot token from .env
bot = commands.Bot(command_prefix="/")


# print a message if the bot is online
@bot.event
async def on_ready():
    print("bot connected")
    # change status to playing mc
    await bot.change_presence(activity=discord.Game("Technical Minecraft on HammerSMP"))


@bot.event
async def on_message(message):
    # check if the bot is online and not responding to itself
    if message.author == bot.user:
        return

    if message.channel.id == coordinate_channel:
        message_format = message.content.split()

        await message.delete()  # delete the message that was just sent
        """
        Check if the message is in the correct format.
        The format we want is the message to start with the dimension, i.e. _n or _ow.
        We also check if the message contains a ':' in the right spot, and checks that the coordinates are
        actual numbers.
        """
        if (message_format[0].startswith("ow_") or message_format[0].startswith("n_")) and message_format[0][-1] == ":"\
                and message_format[1].isnumeric and message_format[2].isnumeric and message_format[3].isnumeric:
            # get the message history of the channel, with a limit of 1 (i.e. 1 message) starting from last.
            # flatten so we get a list
            channel_history = await message.channel.history(limit=1, oldest_first=True).flatten()

            # if there is no message in the channel yet, we want to send a new one
            if not channel_history:
                await message.channel.send(message.content)

            # if del is at the end of the message we want to delete that coordinate from the list
            elif message.content[-3:] == "del":
                coordinate = message.content.strip(" del")
                # we take the message and create a list from the string with \n as separator
                coordinates = channel_history[0].content.split(sep='\n')

                # we also want to know if the coordinate is actually in the list, if tell that to the sender
                if coordinate not in coordinates:
                    await message.channel.send("This coordinate doesn't exist in the list.", delete_after=5)

                else:
                    # remove the coordinate from the list, get the message to edit and join the list back to a string
                    coordinates.remove(coordinate)
                    coordinate_message = channel_history[0]
                    await coordinate_message.edit(content="\n".join(coordinates))

            else:
                # add the new message to the old message
                coordinate_message = channel_history[0]
                coordinate_list = coordinate_message.content
                await coordinate_message.edit(content=coordinate_list + "\n" + message.content)
        else:
            await message.channel.send("Wrong format, please use the correct format", delete_after=5)

    # if a new message is sent in the application forms channel, the bot will automatically add reactions
    if message.channel.id == application_channel:
        for emote in vote_emotes:
            await message.add_reaction(emote)

    await bot.process_commands(message)  # makes sure other commands will also be processed


# command to test if the bot is running
@bot.command(name="test", help="test if the bot is working")
async def test(ctx):
    response = "Don\"t worry, I\"m working!"
    await ctx.send(response)


# command to test if the bot is running
@bot.command(name="role", help="Give yourself the \"tour giver\" role")
# @commands.has_any_role("members") # only allows members to use the role
async def roles(ctx, *args):
    # check if you have provided a role, if not tell the user to do so
    if args == ():
        response = "You have been successfully given the tour giver role! Congratulations."
        await ctx.send(response)
        return

    # combine the *args tuple into a string role
    role = " ".join(args)

    # give the tour giver role if the user asks for this
    if role == "tour giver":
        member = ctx.message.author  # the author of the message, part of the discord.Member class
        role = get(member.guild.roles, name=role)  # the role needed to add

        # if the user doesn't have the right perms, throw an exception
        try:
            await member.add_roles(role)
            response = "You have been successfully given the tour giver role! Congratulations."
            await ctx.send(response)

        except discord.errors.Forbidden:
            response = "Missing permissions"
            await ctx.send(response)

    # if the role is not a role one can add, throw an exception
    else:
        response = "I'm sorry but i'm afraid that role doesn't exist"
        await ctx.send(response)


bot.run(TOKEN)
