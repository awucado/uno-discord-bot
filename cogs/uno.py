""""
Copyright © Krypton 2019-2022 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 5.4.1
"""
import discord
from discord.ext import commands
from discord.ext.commands import Context
from uno import UnoGame, COLORS
from helpers import checks
from collections import defaultdict
import random

groups = {}
games = {}
user_map = defaultdict(int)
color_map = {
    'red': '🍎',
    'yellow': '💛',
    'green': '💚',
    'blue': '💙',
    'black': '🖤',
}


def get_lobby_text(group):
    player_names = []
    for player in group:
        player_names.append(player.name)
    return '__Match {}/4__\n{}'.format(len(group), ", ".join(player_names))


async def send_beginning_of_game(interaction: discord.Interaction, game: UnoGame):
    result_embed = discord.Embed(color=0x9C84EF)
    card = game.current_card
    player = game.current_player
    file = discord.File(
        "images/{}_{}.png".format(card.color, card.card_type), filename="image.png")
    result_embed.set_image(url="attachment://image.png")
    response = "The starting card is {}.".format(card)
    if player.can_play(card):
        response += "<@{}> is up first!".format(player)
    else:
        response += "Player {} picked up".format(player)
        game.play(player_id=player.player_id, card=None)
    result_embed.description = response
    await interaction.response.edit_message(embed=result_embed, content=None, view=None, attachments=[file])


async def send_state_of_game(user: discord.User, channel: discord.TextChannel, game, comments):
    result_embed = discord.Embed(color=0x9C84EF)
    card = game.current_card
    result_embed.set_author(
        name=user.name,
        icon_url=user.avatar.url
    )
    player_names = []
    for player in game.players:
        if player.player_id == game.current_player.player_id:
            player_names.append('__<@{}>__'.format(player.player_id))
        else:
            player_names.append('<@{}>'.format(player.player_id))
        player_names.append("=>")
    text = 'Up next: {}'.format(" ".join(player_names))
    print(text)
    result_embed.description = "You played {}. {}".format(
        card, comments) + "\n" + text
    result_embed.colour = 0xF59E42

    file = discord.File(
        "images/{}_{}.png".format(card.color, card.card_type), filename="image.png")
    result_embed.set_image(url="attachment://image.png")
    await channel.send(embed=result_embed, content=None, view=None, files=[file])


async def send_end_of_game(channel: discord.TextChannel, game, winner):
    result_embed = discord.Embed(color=0x9C84EF)
    player_names = []
    for player in game.players:
        player_names.append(player.name)
    result_embed.set_author(
        name=winner.name,
        icon_url=winner.avatar.url
    )
    result_embed.description = "<@{}> won the game of UNO!\n Players: {}".format(
        winner.player_id, ", ".join(player_names))
    result_embed.colour = 0xF59E42
    await channel.send(embed=result_embed, content=None, view=None)


class MatchButtons(discord.ui.View):
    def __init__(self, leader_id):
        super().__init__()
        self.value = None
        self.leader_id = leader_id
        self.group = groups[self.leader_id]

    @discord.ui.button(label='Leave', style=discord.ButtonStyle.danger)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.leader_id == interaction.user.id:
            # del groups[self.leader_id]
            del self.group
            await interaction.response.send_message("You've left the group! Match has been cancelled.")
        elif interaction.user in self.group:
            self.group.remove(interaction.user)
            await interaction.response.send_message("You've left the group!")
        else:
            await interaction.response.send_message("You can't leave the group, you aren't in it!")
        self.stop()

    @discord.ui.button(label='Join', style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        player_ids = []
        for user in self.group:
            player_ids.append(user.id)
            user_map[user.id] = self.leader_id

        if user_map[interaction.user]:
            await interaction.response.send_message("You are already in a group!")
        elif interaction.user in self.group:
            await interaction.response.send_message("You are already in the group!")
        else:
            await interaction.response.send_message("You've joined the group!")
        self.group.append(interaction.user)
        text = get_lobby_text(self.group)
        await interaction.edit_original_response(content=text)

    @discord.ui.button(label='Start', style=discord.ButtonStyle.secondary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        player_ids = []
        for user in self.group:
            player_ids.append(user.id)
            user_map[user.id] = self.leader_id

        game = UnoGame(player_ids=player_ids)
        game.channel_id = interaction.channel.id
        games[self.leader_id] = game
        await send_beginning_of_game(interaction, game)
        self.stop()


class Hand(discord.ui.Select):
    def __init__(self, user_id):
        self.leader_id = user_map[user_id]
        self.game = games[self.leader_id]
        self.group = groups[self.leader_id]
        for player in games[self.leader_id].players:
            if player.player_id == user_id:
                self.player = player
        options = []
        for i, card in enumerate(self.player.hand):
            print(color_map, card.color, color_map[card.color])
            options.append(discord.SelectOption(label=str(card), description="You chose {} {}".format(
                card.color, card.card_type), emoji=color_map[card.color], value=i))

        super().__init__(
            placeholder="Pick a card to play...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        i = int(self.values[0])
        card = self.player.hand[i]
        print("CHECK!")
        if self.game.current_card.playable(card):
            if len(self.player.hand) <= 1:
                del groups[user_map[interaction.user.id]]
                for user in self.group:
                    del user_map[user.id]
                await send_end_of_game(interaction.channel, self.game, interaction.user)
            else:
                if card.color == 'black':
                    new_color = random.choice(COLORS)
                else:
                    new_color = None
                self.game.play(player_id=self.player.player_id,
                               card=i, new_color=new_color)
                comment = ""
                if not self.game.current_player.can_play(card):
                    comment = "Player {} picked up".format(
                        self.game.current_player)
                    self.game.play(player_id=self.player.player_id, card=None)
                await interaction.response.defer()
                await send_state_of_game(interaction.user, interaction.channel, self.game, comment)
        else:
            await interaction.response.send_message("You can't play that card right now, pick another", ephemeral=True)


class HandView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__()
        self.add_item(Hand(user_id))


class Uno(commands.Cog, name="uno"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="create",
        description="Create a game of UNO.",
    )
    @checks.not_blacklisted()
    async def create(self, context: Context):
        if user_map[context.author.id]:
            await context.reply("You're already in a group. Finish the game first.")
            return
        groups[context.author.id] = [context.author]
        player_names = []
        print(groups[context.author.id])
        for player in groups[context.author.id]:
            player_names.append(player.name)
        view = MatchButtons(context.author.id)
        await context.send(get_lobby_text(groups[context.author.id]), view=view)

        await view.wait()
        if view.value is None:
            print('Timed out...')
        elif view.value:
            print('Confirmed...')
        else:
            print('Cancelled...')

    @commands.hybrid_command(
        name="hand",
        description="Look at your UNO hand."
    )
    @checks.not_blacklisted()
    async def hand(self, context: Context) -> None:
        print(games)
        game = games[user_map[context.author.id]]
        if context.author.id in user_map:
            print(game.current_player.player_id)
            if not game.current_player.player_id == context.author.id:
                await context.reply("It's not your turn yet!", ephemeral=True)
            elif context.channel.id == game.channel_id:
                view = HandView(context.author.id)
                await context.send(view=view, ephemeral=True)
            else:
                await context.reply("Run /hand in the channel where the game is occuring!", ephemeral=True)

        else:
            await context.reply("You aren't in a game of UNO!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Uno(bot))
