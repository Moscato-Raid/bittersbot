from typing import Optional
import os
import re

import discord
from discord import app_commands
import sqlite3

guild_id = os.environ.get('BITTERSTBOT_GUILD_ID')
MY_GUILD = discord.Object(id=guild_id)  # replace with your guild id
brann_idiotbeard = 1343634021799694417
ignored_ids = [89558435930071040, #Bitterst
               brann_idiotbeard #Brann
              ]

ignored_list_str = repr(ignored_ids).replace('[','(').replace(']',')')

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = discord.Intents.default()
intents.members = True
client = MyClient(intents=intents)

con = sqlite3.connect("bitterstbot.db")

cur = con.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS bank(id, balance)")
con.commit()
con.close()


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    for guild in client.guilds:
        await guild.chunk()
    print('------')


async def getUsers(interaction: discord.Interaction, rawMessage: str):
    user_ids = re.findall(r'<@!?(\d+)>', rawMessage)
    if not user_ids:
        await interaction.response.send_message("❌ You must mention at least one member.", ephemeral=True)
        return
    unique_members = []
    seen_ids = set()
    for user_id in user_ids:
        try:
            member = interaction.guild.get_member(int(user_id))
            if member.id not in seen_ids:
                unique_members.append(member)
                seen_ids.add(member.id)
        except:
            continue

    if not unique_members:
        await interaction.response.send_message("❌ No valid members found in mentions.", ephemeral=True)
        return
    return unique_members

@client.tree.command()
@app_commands.describe(
    members='The user(s) to give $bits to. Ie: @Boozleblom @bitterst',
    dollars='The numbers of $bits to give',
)
async def bitsgive(interaction: discord.Interaction, members: str, dollars: int, memo: str):
    caller = interaction.user
    if not any(role.name == "BittersBucks" for role in caller.roles):
        caller_name = str(caller.display_name)
        await interaction.response.send_message(f'{caller_name} does not have $bits ledger write permissions.')
        return

    unique_members = await getUsers(interaction, members)
    if not unique_members:
        return

    responseMessages = [f'Gave **{dollars}** dollars for *{memo}*']
    for member in unique_members:
        member_id = member.id
        member_name = member.nick or member.global_name or member.name

        if dollars < 0:
            dollars = dollars * -1

        con = sqlite3.connect("bitterstbot.db")
        cur = con.cursor()
        res = cur.execute("SELECT * FROM bank WHERE id=?", (member_id,))

        if res.fetchone() is not None:
            res = cur.execute("SELECT * FROM bank WHERE id=?", (member_id,))
            data = res.fetchone()

            update_dollars = data[1] + dollars

            cur.execute("UPDATE bank SET balance=? WHERE id=?", (update_dollars, member_id,))
            con.commit()
            con.close()

            responseMessages.append(f'{member_name} now has {update_dollars} $bits.')

        else:
            cur.execute("INSERT INTO bank VALUES(?,?)", (member_id, dollars,))
            con.commit()
            con.close()

            responseMessages.append(f'{member_name} now has {dollars} $bits.')

    await interaction.response.send_message("\n".join(responseMessages))


@client.tree.command()
@app_commands.describe(
    dollars='The numbers of $bits to steal',
)
async def bitssteal(interaction: discord.Interaction, dollars: int, memo: str):
    valid_id = False
    caller = interaction.user
    caller_name = str(caller.display_name)


    # There is currently one valid criminal interaction
    #   until a table of relationships or something is made, this is hardcoded
    celexxia_id = 227856369464639488
    bitterst_id = 89558435930071040

    dollars = abs(dollars)

    if caller.id == celexxia_id:
        valid_id = True

    if valid_id == True:

        con = sqlite3.connect("bitterstbot.db")
        cur = con.cursor()
        update_source = 0
        update_target = 0

        source_res = cur.execute("SELECT * FROM bank WHERE id=?", (thonir_id,))
        if (source_res is not None):
            source_data = source_res.fetchone()
            update_source = source_data[1] - dollars

        target_res = cur.execute("SELECT * FROM bank WHERE id=?", (sovoke_id,))
        if (target_res is not None):
            target_data = target_res.fetchone()
            update_target = target_data[1] + dollars

            # This should not run if either of the above cursors failed
        if (update_source != 0) and (update_target != 0):
            cur.execute("UPDATE bank SET balance=? WHERE id=?", (update_source, bitterst_id,))
            cur.execute("UPDATE bank SET balance=? WHERE id=?", (update_target, celexxia_id,))
            con.commit()
            con.close()

            await interaction.response.send_message(f'Celexxia has stolen {dollars} $bits from Bitters, and now has {update_target} $bits. \n Bitterst now has {update_source} $bits. Memo: {memo}')
    else:
        await interaction.response.send_message(f'{caller_name} does not have $bits ledger write permissions.')



@client.tree.command()
@app_commands.describe(
    member='The user to take $bits from',
    dollars='The numbers of $bits to take',
)
async def bitstake(interaction: discord.Interaction, member: discord.Member, dollars: int, memo: str):
    valid_role = False
    caller = interaction.user
    caller_name = str(caller.display_name)

    member_name = str(member.display_name)
    member_id = member.id

    if dollars < 0:
        dollars = dollars * -1

    for role in caller.roles:
        if role.name == "BittersBucks":
            valid_role = True

    if valid_role == True:

        con = sqlite3.connect("bitterstbot.db")
        cur = con.cursor()
        res = cur.execute("SELECT * FROM bank WHERE id=?", (member_id,))

        if res.fetchone() is not None:
            res = cur.execute("SELECT * FROM bank WHERE id=?", (member_id,))
            data = res.fetchone()

            update_dollars = data[1] - dollars

            cur.execute("UPDATE bank SET balance=? WHERE id=?", (update_dollars, member_id,))
            con.commit()
            con.close()

            await interaction.response.send_message(f'{member_name} has lost {dollars} $bits, and now has {update_dollars} $bits. Memo: {memo}')

        else:
            init_dollars = 0 - dollars
            cur.execute("INSERT INTO bank VALUES(?,?)", (member_id, init_dollars,))
            con.commit()
            con.close()

            await interaction.response.send_message(f'{member_name} has lost {dollars} $bits, and now has {init_dollars} $bits. Memo: {memo}')

    else:
        await interaction.response.send_message(f'{caller_name} does not have $bits ledger write permissions.')

@client.tree.command()
@app_commands.describe(
    member='The user to check $bits balance'
)
async def bitscheck(interaction: discord.Interaction, member: discord.Member):
    """Checks a user's current $bits balance"""
    member_name = str(member.display_name)
    member_id = member.id

    con = sqlite3.connect("bitterstbot.db")
    cur = con.cursor()
    res = cur.execute("SELECT * FROM bank WHERE id=?", (member_id,))

    if res.fetchone() is not None:
        res = cur.execute("SELECT * FROM bank WHERE id=?", (member_id,))
        data = res.fetchone()
        con.close()

        await interaction.response.send_message(f'{member_name} has {data[1]} $bits')

    else:
        con.close()

        await interaction.response.send_message(f'{member_name} has 0 $bits')

@client.tree.command()
@app_commands.describe(
)
async def bitsrank(interaction: discord.Interaction):
    """Displays current top 10 $bits rankings"""
    con = sqlite3.connect("bitterstbot.db")
    cur = con.cursor()

    #Get only top 10 values
    res = cur.execute("SELECT * FROM bank WHERE id NOT IN %s ORDER BY balance DESC limit 10" % ignored_list_str)
    data = res.fetchall()
    con.close()

    user_rank = []
    user_id = []

    # Build both lists out of our result
    for data_result in data:
        user_id.append(data_result[0])
        user_rank.append(data_result[1])

    guild = await client.fetch_guild(guild_id)

    # Get a list of all members corresponding to ids from the result
    members_by_id = await guild.query_members(limit=10,user_ids=user_id)
    member_dict = dict(map(lambda key: (key.id,key.display_name),members_by_id))


    rank_str = f"Top 10 $bits balance\n"
    for num,id,amnt in zip(range(1,11),user_id,user_rank):
        rank_str += f"{num}. {member_dict[id]}: {amnt} $bits \n"

    await interaction.response.send_message(rank_str)

@client.tree.command()
@app_commands.describe(
)
async def bitsdebt(interaction: discord.Interaction):
    """Displays current bottom 10 $bits rankings"""
    con = sqlite3.connect("bitterstbot.db")
    cur = con.cursor()


    # does this work to make a list for sqlite

    #Get bottom 10 values and filter out ignored ids
    res = cur.execute("SELECT * FROM bank WHERE id NOT IN %s ORDER BY balance ASC limit 10" % ignored_list_str)
    data = res.fetchall()
    con.close()

    user_rank = []
    user_id = []

    # Build both lists out of our result
    for data_result in data:
        user_id.append(data_result[0])
        user_rank.append(data_result[1])

    guild = await client.fetch_guild(guild_id)

    # Get a list of all members corresponding to ids from the result
    members_by_id = await guild.query_members(limit=10,user_ids=user_id)
    member_dict = dict(map(lambda key: (key.id,key.display_name),members_by_id))


    rank_str = f"Bottom 10 $bits balance\n"
    for num,id,amnt in zip(range(1,11),user_id,user_rank):
        rank_str += f"{num}. {member_dict[id]}: {amnt} $bits \n"

    await interaction.response.send_message(rank_str)



client.run(os.environ.get('BITTERSTBOT_TOKEN'))
