import time
from datetime import datetime

import sentry_sdk
from discord.ext import commands
from discord.ext.commands import Bot
from aiohttp import ClientOSError, ServerDisconnectedError
from discord import ConnectionClosed, Embed, Colour

from utils import Logging, Configuration, Utils, Emoji


class Skybot(Bot):
    loaded = False

    async def on_ready(self):
        if not self.loaded:
            Logging.BOT_LOG_CHANNEL = self.get_channel(Configuration.get_var("log_channel"))
            Emoji.initialize(self)

            Logging.info("Loading cogs...")
            for extension in Configuration.get_var("cogs"):
                try:
                    self.load_extension("cogs." + extension)
                except Exception as e:
                    await Utils.handle_exception(f"Failed to load cog {extension}", self, e)
            Logging.info("Cogs loaded")
            self.loaded = True

        await Logging.bot_log("Sky bot soaring through the skies!")

    async def on_command_error(bot, ctx: commands.Context, error):
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send(error)
        elif isinstance(error, commands.CheckFailure):
            pass
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error)
        elif isinstance(error, commands.MissingRequiredArgument):
            param = list(ctx.command.params.values())[min(len(ctx.args) + len(ctx.kwargs), len(ctx.command.params))]
            bot.help_command.context = ctx
            await ctx.send(
                f"{Emoji.get_chat_emoji('NO')} You are missing a required command argument: `{param._name}`\n{Emoji.get_chat_emoji('WRENCH')} Command usage: `{bot.help_command.get_command_signature(ctx.command)}`")
        elif isinstance(error, commands.BadArgument):
            param = list(ctx.command.params.values())[min(len(ctx.args) + len(ctx.kwargs), len(ctx.command.params))]
            bot.help_command.context = ctx
            await ctx.send(
                f"{Emoji.get_chat_emoji('NO')} Failed to parse the ``{param._name}`` param: ``{error}``\n{Emoji.get_chat_emoji('WRENCH')} Command usage: `{bot.help_command.get_command_signature(ctx.command)}`")
        elif isinstance(error, commands.CommandNotFound):
            return

        else:
            await Utils.handle_exception("Command execution failed", bot,
                                         error.original if hasattr(error, "original") else error, ctx=ctx)
            # notify caller
            e = Emoji.get_chat_emoji('BUG')
            if ctx.channel.permissions_for(ctx.me).send_messages:
                await ctx.send(f"{e} Something went wrong while executing that command {e}")


def before_send(event, hint):
    if event['level'] == "error" and 'logger' in event.keys() and event['logger'] == 'gearbot':
        return None  # we send errors manually, in a much cleaner way
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        for t in [ConnectionClosed, ClientOSError, ServerDisconnectedError]:
            if isinstance(exc_value, t):
                return
    return event


if __name__ == '__main__':
    Logging.init()
    Logging.info("Launching that sky bot!")

    dsn = Configuration.get_var('SENTRY_DSN', '')
    if dsn != '':
        sentry_sdk.init(dsn, before_send=before_send)

    skybot = Skybot(command_prefix="?", case_insensitive=True, guild_subscriptions=False)

    Utils.BOT = skybot

    skybot.run(Configuration.get_var("token"))
    Logging.info("Shutdown complete")