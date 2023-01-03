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
    return '__Match {}/4__\n{}'.format(group.length, ", ".join(player_names)

async def send_beginning_of_game(interaction, game):
    card=game.current_card
    player=game.current_player
    file=discord.File(
    "images/{}_{}.png".format(card.color, card.card_type), filename="image.png")
    result_embed.set_image(url="attachment://image.png")
    response="The starting card is {}.".format(card)
    if player.can_play(card):
        response += "<@{}> is up first!".format(player)
    else:
        response += "Player {} picked up".format(player)
        game.play(player=player.player_id, card=None)
    result_embed.description=response
    await interaction.response.edit_message(embed=result_embed, content=None, view=None, attachments=[file])

async def send_state_of_game(channel: discord.TextChannel, game):
    result_embed=discord.Embed(color=0x9C84EF)
    card=game.current_card

    next_player=game.current_player
    result_embed.description="You played {}. <@{}> is up next!".format(
        card, next_player.player_id)
    result_embed.colour=0xF59E42
    file=discord.File(
        "images/{}_{}.png".format(card.color, card.card_type), filename="image.png")
    result_embed.set_image(url="attachment://image.png")
    await channel.send(embed=result_embed, content=None, view=None, attachments=[file])

class MatchButtons(discord.ui.View):
    def __init__(self, leader_id):
        super().__init__()
        self.value = None
        self.leader_id = leader_id
        self.group = groups[self.leader_id]
        self.game = games[self.leader_id]

    @discord.ui.button(label='Leave', style=discord.ButtonStyle.danger)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Cancelling', ephemeral=True)
        # TODO: only let leader do this, otherwise remove person from group
        #del groups[self.leader_id]
        del self.group
        self.stop()

    @discord.ui.button(label='Join', style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Confirming', ephemeral=True)
        self.group.append(interaction.user)

    @discord.ui.button(label='Start', style=discord.ButtonStyle.secondary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        for user in self.group:
            user_map[user.id] = self.leader_id
        game = UnoGame(self.group)
        game.channel_id = interaction.channel.id
        # games[self.leader_id] = game
        await send_beginning_of_game(interaction, self.game)
        self.stop()
"""         self.game = game
        card = self.game.current_card
        player = self.game.current_player
        result_embed = discord.Embed(color=0x9C84EF)
        file = discord.File(
            "images/{}_{}.png".format(card.color, card.card_type), filename="image.png")
        result_embed.set_image(url="attachment://image.png")
        response = "The starting card is {}.".format(card)
        if player.can_play(card):
            response += "<@{}> is up first!".format(player)
        else:
            response += "Player {} picked up".format(player)
            self.game.play(player=player.player_id, card=None)
        result_embed.description = response
        await interaction.response.edit_message(embed=result_embed, content=None, view=None, attachments=[file]) """
        


class Hand(discord.ui.Select):
    def __init__(self, user_id):
        self.leader_id = user_map[user_id]
        self.game = games[self.leader_id]
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
            if card.color == 'black':
                new_color = random.choice(COLORS)
            else:
                new_color = None
            self.game.play(player_id=self.player.player_id,
                           card=i, new_color=new_color)
            result_embed = discord.Embed(color=0x9C84EF)
            result_embed.set_author(
                name=interaction.user.name,
                icon_url=interaction.user.avatar.url
            )
            card = self.game.current_card

            await send_state_of_game()
            next_player = self.game.current_player
            result_embed.description = "You played {}. <@{}> is up next!".format(
                card, next_player.player_id)
            result_embed.colour = 0xF59E42
            file = discord.File(
                "images/{}_{}.png".format(card.color, card.card_type), filename="image.png")
            result_embed.set_image(url="attachment://image.png")
            await interaction.response.edit_message(embed=result_embed, content=None, view=None, attachments=[file])
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
        view = MatchButtons(context.author.id)

        groups[context.author.id] = [context.author]
        player_names = []
        for player in groups[context.author.id]:
            player_names.append(player.name)
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
        if context.author.id in user_map:
            if context.channel.id == games[user_map[context.author.id]].channel_id:
                view=HandView(context.author.id)
                await context.send(view=view, ephemeral=True)
            else:
                await context.reply("Run /hand in the channel where the game is occuring!", ephemeral=True)
           
        else:
            await context.reply("You aren't in a game of UNO!", ephemeral=True)
async def setup(bot):
    await bot.add_cog(Uno(bot))


