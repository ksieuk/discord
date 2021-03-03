import discord
from discord.ext import commands
import random


class Mafia(commands.Cog, name="Mafia"):
    def __init__(self, bot):
        self.client = bot
        self.message_on_start_id = self.pollmessage_id = None
        self.users_in_game, self.options = [], []
        self.mafia_channel = self.client.get_channel(706947485083500654)
        self.is_playing = False
        self.players_nick = [f' {i} игрок' for i in range(1, 21)]
        self.poll_users_vote = {}
        self.emoji_yes = '<:yes:718437410995830788>'
        self.emoji_no = '<:no:718437410974859283>'

    @commands.command(pass_context=True, name="help_me")
    async def help_(self, ctx):
        """Commands guide"""

        await ctx.message.delete()
        embed = discord.Embed(color=discord.Colour.from_rgb(0, 0, 0))
        embed.set_author(name='Mafia — команды')
        embed.add_field(name='.vote', value='Проголосовать за человека', inline=False)
        await ctx.author.send(embed=embed)

    @commands.command(pass_context=True, name="night")
    @commands.has_role("Ведущий")
    async def mute_players(self, channel: discord.VoiceChannel = None):
        """Mutes players on the game_channel"""

        if not channel:
            channel = self.client.get_channel(730091498380591184)

        for member in channel.members:
            nick = member.nick
            if nick[0] == '[' in nick and ']' in nick and nick[nick.index('[') + 1:nick.index(']')].isdigit(self):
                await member.edit(mute=True)

    @commands.command(pass_context=True, name="day")
    @commands.has_role('Ведущий')
    async def unmute_players(self, channel: discord.VoiceChannel = None):
        """Unmutes players on the game_channel"""

        if not channel:
            channel = self.client.get_channel(730091498380591184)

        for member in channel.members:
            nick = member.nick
            if nick[0] == '[' and ']' in nick and nick[1:nick.index(']')].isdigit(self):
                await member.edit(mute=False)

    @commands.command(pass_context=True)
    @commands.has_role('Ведущий')
    async def on_start(self, ctx):
        """Creating a list of people who want to play"""

        message_on_start = await ctx.send(f'Если хотите играть, отреагируйте ({self.emoji_yes}):')
        await message_on_start.add_reaction(self.emoji_yes)
        await message_on_start.add_reaction(self.emoji_no)

        self.message_on_start_id = message_on_start.id  # wait_for

    @commands.command(pass_context=True)
    @commands.has_role('Ведущий')
    async def start(self, ctx, channel: discord.VoiceChannel = None):
        """Starting the game and changing nicknames"""

        if not channel:
            channel = self.client.get_channel(706947485083500654)

        count = 1
        for member in self.users_in_game:
            if member.voice:
                if member.nick is None:
                    await member.edit(nick=f'[0{str(count)}] {member.name}')
                else:
                    await member.edit(nick=f'[0{str(count)}] {member.nick}')

                await member.move_to(channel)
                count += 1
        else:
            ctx.send("Хорошей игры!")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        msg_id = payload.message_id

        if payload.member.id != 670385873849679902:
            if msg_id == self.message_on_start_id and str(payload.emoji.name) == "yes":
                self.users_in_game.append(payload.member)
                print(1)
            elif msg_id == self.pollmessage_id:
                self.poll_add_vote(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        msg_id = payload.message_id

        if msg_id == self.message_on_start_id:
            del self.users_in_game[list(map(lambda x: x.id, self.users_in_game)).index(payload.user_id)]
        elif msg_id == self.pollmessage_id:
            self.poll_remove_vote(payload)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        print(reaction, user)

    @commands.command(pass_context=False, name="stop")
    @commands.has_role('Ведущий')
    async def stop(self, ctx=None, channel: discord.VoiceChannel = None):
        """Game over... Nicks have taken the previous state"""

        self.is_playing = False

        if channel:
            for member in channel.members:
                nick = member.nick
                if nick[0] == '[' and ']' in nick and nick[1:nick.index(']')].isdigit():
                    await member.edit(nick=f'{member.nick[nick.index("]") + 2:]}')

        else:
            for member in self.users_in_game:
                nick = member.nick
                if nick[0] == '[' and ']' in nick and nick[nick.index('[') + 1:nick.index(']')].isdigit():
                    await member.edit(nick=f'{member.nick[nick.index("]") + 2:]}')

        await ctx.send('Спасибо за игру!')

    @commands.command(pass_context=True, name="start_p")
    @commands.has_role('Ведущий')
    async def start_players(self, ctx, *players: discord.Member):
        count = 1
        for member in players:
            roles_member = map(lambda x: x.name, member.roles)
            if 'Ведущий' not in roles_member:
                # await member.move_to(self.client.get_channel(706947485083500654))
                if member.nick is None:
                    await member.edit(nick=f'[0{str(count)}] {member.name}')
                else:
                    await member.edit(nick=f'[0{str(count)}] {member.nick}')
                count += 1

        await ctx.message.add_reaction(self.emoji_yes)

    @commands.command(pass_context=False)
    @commands.has_role('Ведущий')
    async def stop_players(self, ctx, *players: discord.Member):
        self.is_playing = False

        for member in players:
            nick = str(member.nick)
            if nick[0] == '[' and ']' in nick and nick[1:nick.index(']')].isdigit():
                await member.edit(nick=f'{member.nick[nick.index("]") + 2:]}')

        await ctx.message.add_reaction(self.emoji_yes)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Mute incoming members"""

        if after.channel is self.mafia_channel and not before.channel:
            if self.is_playing:
                await member.edit(mute=True)

    # опросы
    @commands.command(pass_context=True)
    async def poll(self, ctx, name, *variants):
        """Create and submit a survey"""

        # error
        if "admin" not in [role.name.lower() for role in ctx.author.roles]:
            await ctx.send('Невозможно создать опрос: "Недостаточно прав"')
            return

        # заготовка
        if name == 'mafia':
            jail_image_url = scary_image_url()
            title = '🔒 Кого посадим сегодня? 🔒'
            if variants[0].isdigit():
                self.options = self.get_players_nick(range(int(variants[0])))
            elif variants[0] == '$':
                self.options = self.get_players_nick(map(lambda x: int(x) - 1, variants[1:]))

        elif -1 < name.find('{') < name.find('}') and all([-1 < x.find('[') < x.find(']') for x in variants]):
            title = name.replace('{', '').replace('}', '')
            self.options = [x.replace('_', ' ').replace('[', '').replace(']', '') for x in variants]
            jail_image_url = None

        # error
        else:
            await ctx.send('Невозможно создать опрос: "Команда должна соответствовать формату «.poll {Название} [Варивант_1] [Вариант_2]...»"')
            return

        # error
        if len(self.options) > 21:
            await ctx.send('Невозможно создать опрос: "Максимум 20 вариантов"')
            return

        # Create and submit a poll
        ads = ["[:video_game:  Советуем:)](https://www.twitch.tv/limba3)"]
        r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
        embed = discord.Embed(
            title=f"**{title}**",
            description=ads[0],
            colour=discord.Colour.from_rgb(r, g, b)
        )

        # add variants
        variants_first_part = '\n'.join([f'{get_emoji_letter(i)} {self.options[i]}' for i in range(len(self.options) // 2)])
        variants_second_part = '\n'.join([f'{get_emoji_letter(i)} {self.options[i]}' for i in range(len(self.options) // 2, len(self.options))])
        ad_url_image = "https://static-cdn.jtvnw.net/jtv_user_pictures/771a4211-6fc4-48d6-91fd-d414a673381e-profile_image-70x70.jpg"

        embed.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        embed.add_field(name='Голосуйте!', value=variants_first_part, inline=True)
        embed.add_field(name='😲', value=variants_second_part, inline=True)
        embed.set_thumbnail(url=ad_url_image)
        if jail_image_url:
            embed.set_image(url=jail_image_url)

        pollmessage = await ctx.send(embed=embed)
        self.pollmessage_id = pollmessage.id
        self.poll_users_vote = {}

        # Добавление реакций для голосования
        for i in range(len(self.options)):
            self.poll_users_vote[get_emoji_letter(i)] = 0
            await pollmessage.add_reaction(get_emoji_letter(i))

            # return 'Please make sure you are using the format poll: "{title} [Option1] [Option2] [Option 3]"'

    @commands.command(name='e_r')
    async def emoji_say_reaction(self, ctx, message):
        """Sends an empty message and adds reactions (only eng)"""

        emoji_message = await ctx.send('︀')
        for letter in list(message):
            emoji = get_emoji_letter(ord(letter) - 97)
            if emoji:
                await emoji_message.add_reaction(emoji)

    @commands.command(name='e_t')
    async def emoji_say_text(self, ctx, *message):
        """Converts text to emoji (only eng)"""

        message = " ".join(message)
        text = []
        for letter in list(message):
            emoji = get_emoji_letter(ord(letter) - 97)
            if emoji:
                text.append(emoji)
            elif letter == " ":
                text.append(letter)

        await ctx.send(' '.join(text))

    @commands.command(name='set')
    async def set_players_nick(self, ctx, new_nicks=None):
        if new_nicks:
            new_nicks = new_nicks.split(';')
        self.players_nick = [new_nicks[i - 1] if len(new_nicks) >= i else f' {i} игрок' for i in
                             range(1, 21)] if new_nicks else [f' {i} игрок' for i in range(1, 21)]
        if ctx:
            await ctx.send(f'{ctx.author.mention} успешно изменил ники игроков.')

    @commands.command(name='result')
    async def print_the_poll_result(self, ctx):
        """Print the poll result"""

        if self.poll_users_vote:
            res = []
            for i, user_votes in enumerate(self.poll_users_vote.values()):
                if user_votes != 0:
                    res.append((self.options[i], user_votes))
            res = '\n'.join(map(lambda x: f"{str(x[0]).strip()}: {x[1]}",
                                sorted(res, key=lambda y: y[1], reverse=True)))
            await ctx.send(res)

    def poll_add_vote(self, payload):
        emoji_name = str(payload.emoji)
        if payload.user_id != 670385873849679902:
            self.poll_users_vote[emoji_name] += 1

    def poll_remove_vote(self, payload):
        emoji_name = str(payload.emoji)
        if payload.user_id != 670385873849679902:
            self.poll_users_vote[emoji_name] -= 1

    def get_players_nick(self, indexes=None):
        if indexes:
            return [self.players_nick[i] for i in indexes]
        else:
            return self.players_nick

    @commands.command()
    @commands.has_role('Admin')
    async def shutdown(self, ctx=None):
        if ctx:
            print(f"{ctx.author} завершил работу бота")
            await ctx.send("Всем пока!")
            channel = self.client.get_channel(705482683702313092)  # logs
            await channel.send(f"{ctx.author.mention} вырубил бота")
        else:
            print("Бот отключил бота")
        await ctx.bot.logout()


def scary_image_url():
    return random.choice(IMAGES)


def get_emoji_letter(index):
    if not 0 <= index <= 26:
        return
    return EMOJIS[index]


def setup(bot):
    bot.add_cog(Mafia(bot))


# todo global!!!!!!!!!!!!
IMAGES = [
    'https://i.ibb.co/7kxLY10/9.png',
    'https://i.ibb.co/gPWbqXp/1.png',
    'https://i.ibb.co/8sSSshy/image.png',
    'https://i.ibb.co/gv3t83V/image.png',
    'https://i.ibb.co/7kxLY10/9.png',
    'https://i.ibb.co/b7jDySZ/2.png',
    'https://i.ibb.co/nkPKKYY/3.png',
    'https://i.ibb.co/YynxLz4/4.png',
    'https://i.ibb.co/RyY6G3t/Almost-there-decal.png',
    'https://i.ibb.co/b3YKKrp/Cohen-words-decal.png',
    'https://i.ibb.co/vJJN2Wd/Death.png',
    'https://i.ibb.co/vcM2yrn/Drawings-Decal02.png',
    'https://i.ibb.co/3v8s6F6/Dreams-v2-decal.png',
    'https://i.ibb.co/Trqh8MV/Feel-familiar-decal.png',
    'https://i.ibb.co/LxHyjh8/LetUsOut.png',
    'https://i.ibb.co/Mkkcgrj/No-angels-decal.png',
    'https://i.ibb.co/f49chRY/Seeing-tool-decal.png'
    'https://i.ibb.co/WpKnYBD/Singwithme.png'
]

EMOJIS = [
    "\N{REGIONAL INDICATOR SYMBOL LETTER A}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER B}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER C}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER D}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER E}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER F}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER G}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER H}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER I}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER J}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER K}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER L}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER M}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER N}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER O}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER P}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER Q}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER R}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER S}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER T}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER U}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER V}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER W}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER X}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER Y}",
    "\N{REGIONAL INDICATOR SYMBOL LETTER Z}"
]

"""
https://gist.github.com/EvieePy/d78c061a4798ae81be9825468fe146be
https://github.com/AlexFlipnote/discord_bot.py
https://discordpy.readthedocs.io/en/latest/ext/commands/cogs.html
"""
