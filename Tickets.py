import asyncio
import discord
from discord.ext import commands
import json
import config
from discord import option
from discord.commands import Option, SlashCommandGroup
import traceback
from discord.ui import Button, View
import util

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix = 'dm!',intents = intents)

guildModRoles = util.load_data("guildModRoles")
blacklistedUsers = util.load_data("blacklistedUsers")
ticketEmbeds = util.load_data("ticketEmbeds")

helptext = {
	"setcolor":"This command allows you to change the color of the Dodo Mail embeds to a hex color of choice. The color set by default is #518550",
	"setthumbnail":"This command allows you to change the Default Dodo Mail thumbnail to one of your choice.",
	"setup":"This command allows you to create an embed in a channel of choice. You can select the name, description and what the buttonlabel will be. Once this is done users will be able to simply press the button and it will create a ticket.",
	"add":"This command allows you to add a user to an existing ticket.",
	"remove":"This command allows you to remove an user from an existing ticket.",
	"new":"This command allows you to open a new ticket. (This is a backup command in case the button to open commands doesn't seem to work).",
	"supportrole":"This commands allows you to setup a general support role. Users with the supportrole will be able to see, claim, unclaim and close tickets.",
	"rename":"This command allows you to rename the current ticket you are active in.",
	"ticketpurge":"This command allows you to remove messages in a ticket.",
	"transcript":"This command allows you to create a transcript of the ticket you are currently in. (This is a backup command in case the bot doesnt make the transcripts automatically)",
	"claim":"This command allows you to claim a ticket. (This is a backup command, that should only be used in case the claim button doesn't work)",
	"unclaim":"This command allows you to unclaim a ticket. (This is a backup command, that should only be used in case the unclaim button doesn't work)",
	"close":"This command allows you to claim a ticket. (This is a backup command, that should only be used in case the close button doesn't work)",
	"blacklist":"This command lets you blacklist an user on the server, making it so they are unable to open tickets.",
	"unblacklist":"This command lets you unblacklist an user on the server, making it so they are able to open tickets once again.",
	"reset":"This commands allows you to reset the bot setup completely undoing all changes you have made since you added the bot to your discord server.",
	"botinfo":"This command shows bot statistics and can only be used by the bot developer.",
	"invite":"When using this command Dodo Mail will post a link that you can use to invite the bot into your discord server.",
	"serverinfo":"When using this command the bot will show basic information about how many tickets have been opened in total, how many tickets have been closed in total, which users are currently blacklisted and how many users the discord server has.",
	"sponsor":"When using this command the bot will get a list of all the current sponsors of the bot and invite links to their discords.",
	"support":"When using this command Dodo Mail will provide you with an invite link to join the Dodo Mail support server.",
	"userinfo":"This command allows you to view how many tickets an user has opened and closed on your server and see if the user is currently blacklisted yes or no.",
	"help":"Use this to view all the commands this bot have."
}

def getHelpText(cmd):
	if not cmd in helptext:
		return ""
	else:
		if len(helptext[cmd]) > 99:
			return str(helptext[cmd][:98])
		else:
			return helptext[cmd]

def return_color(guild):
	
	if not str(guild) in ticketEmbeds:
		color = discord.Color.from_rgb(80, 133, 81)
		return color
	else:
		if not "color" in ticketEmbeds[str(guild)]:
			color = discord.Color.from_rgb(80, 133, 81)
			return color

		else:
			color = discord.Color.from_rgb(ticketEmbeds[str(guild)]["color"][0],ticketEmbeds[str(guild)]["color"][1],ticketEmbeds[str(guild)]["color"][2])
			return color

def return_thumbnail(guild):
	if not guild in ticketEmbeds:
		return 'https://i.imgur.com/ZovNveV.png'
	else:
		if not "thumbnail" in ticketEmbeds[str(guild)]:
			return 'https://i.imgur.com/ZovNveV.png'
		else:
			return ticketEmbeds[str(guild)]["thumbnail"]

def hex_to_rgb(value):
    """Return (red, green, blue) for the color given as #rrggbb."""
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
	
@bot.slash_command(description=getHelpText("setcolor"))
@discord.guild_only()
@discord.default_permissions(administrator=True)
async def setcolor(ctx,hex):

	if not str(ctx.guild.id) in ticketEmbeds:
		ticketEmbeds[str(ctx.guild.id)] = {}
	
	try:
		r,g,b=hex_to_rgb(hex)
	except:
		return await ctx.respond('Invalid color-hex')

	ticketEmbeds[str(ctx.guild.id)]["color"] = [r,g,b]
	util.save_data(ticketEmbeds, "ticketEmbeds")
	
	await ctx.respond(':white_check_mark: Color Changed')

@bot.slash_command(description=getHelpText("setthumbnail"))
@discord.guild_only()
@discord.default_permissions(administrator=True)
async def setthumbnail(ctx,url):
	
	if not str(ctx.guild.id) in ticketEmbeds:
		ticketEmbeds[str(ctx.guild.id)] = {}
	
	if not str(url).lower().startswith("https://"):
		await ctx.respond("Invalid url, needs to be https")
	
	ticketEmbeds[str(ctx.guild.id)]["thumbnail"] = str(url)
	util.save_data(ticketEmbeds, "ticketEmbeds")
	
	await ctx.respond(':white_check_mark: Thumbnail Changed')

@bot.event
async def on_ready():
	print('---------- SERVER HAS STARTED ---------')

@bot.event
async def on_interaction(interaction):
	#print("aaa")
	#print("Does this even run?")
	guild = str(interaction.guild.id)

	with open('Tickets.json') as f:
		tickets = json.load(f)
	
	id = str(interaction.channel.id)
	
	#print(dir(interaction))
	#print(interaction.component)
	
	if interaction.custom_id=="button_claim":
		await ticket_claim_cmd(interaction,tickets,id,guild)
			
	elif interaction.custom_id=="button_close":
		await ticket_close_cmd(interaction,tickets,id,guild)
			
	elif interaction.custom_id=="button_open_ticket":
		await open_ticket_button_clicked(interaction)
	
	await bot.process_application_commands(interaction)
	
@bot.slash_command(description=getHelpText("setup"))
@discord.guild_only()
@discord.default_permissions(administrator=True)
async def setup(ctx,channel:discord.TextChannel,name,description,buttonlabel):
	global guildModRoles
	
	buttonLabel=buttonlabel
	
	if not str(ctx.guild.id) in guildModRoles:
		guildModRoles[str(ctx.guild.id)]=config.adminRole
		util.save_data(guildModRoles, "guildModRoles")
	
	if not str(ctx.guild.id) in blacklistedUsers:
		blacklistedUsers[str(ctx.guild.id)] = []
		util.save_data(blacklistedUsers, "blacklistedUsers")
	
	if not str(ctx.guild.id) in ticketEmbeds:
		ticketEmbeds[str(ctx.guild.id)] = {}
		util.save_data(ticketEmbeds, "ticketEmbeds")
	
	if not channel:
		await ctx.respond(':clock1: Usage: /setupticket `<#CHANNEL>` (USED TO FETCH THE CATEGORY)')
		return
	
	await ctx.defer()
	
	with open('Database.json') as f:
		try:
			data = json.load(f)
		except:
			data = {}
	
	category = str(channel.category.id)
	data[category] = {}


	overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False)}
	
	ch = await ctx.guild.create_text_channel(f'transcript', overwrites=overwrites,category = ctx.channel.category)



	embed = discord.Embed(title = name,color = return_color(str(ctx.guild.id)),description = description)
	embed.set_thumbnail(url = return_thumbnail(str(ctx.guild.id)))
	embed.set_footer(text = 'Dodo Mail | ©️ 2022 | www.thelandofark.com',icon_url='https://i.imgur.com/hODYmHU.png')
	
	view=View()
	buttonOpenTicket=discord.ui.Button(style=discord.ButtonStyle.gray, label=buttonLabel, custom_id="button_open_ticket")
	view.add_item(buttonOpenTicket)
	
	msg = await channel.send(embed = embed,view=view)
	#await msg.add_reaction(emoji)
	#await ctx.message.add_reaction('✅')
	
	data[category]['Name'] = name
	data[category]['Description'] = description
	data[category]['ButtonLabel'] = buttonLabel
	data[category]['MSG'] = msg.id
	with open('Database.json','w') as f:
		json.dump(data,f,indent = 3)
	
	await ctx.respond("Setup completed ✅")
	
@bot.slash_command(description=getHelpText("add"))
@discord.guild_only()
async def add(ctx,user:discord.Member = None):
	if not user:
		await ctx.respond(':clock1: !add `<@user>`')
		return

	with open('Tickets.json') as f:
		tickets = json.load(f)
	
	id = str(ctx.channel.id)

	if id in tickets:
		if tickets[id]['Owner'] == ctx.author.id:
			overwrites = {
				user: discord.PermissionOverwrite(read_messages=True,send_messages = True,read_message_history=True,attach_files=True)
			}
			await ctx.channel.edit(overwrites = overwrites)
			await ctx.respond(f':white_check_mark: You have added {user} in the Ticket.')

		else:
			await ctx.respond('This ticket is not claimed by you.')

	else:
		await ctx.respond('Invalid Ticket Channel.')
	
	#ctx.message.delete()

@bot.slash_command(description=getHelpText("remove"))
@discord.guild_only()
async def remove(ctx,user:discord.Member = None):
	if not user:
		await ctx.respond(':clock1: !remove `<@user>`')
		return

	with open('Tickets.json') as f:
		tickets = json.load(f)
	
	id = str(ctx.channel.id)

	if id in tickets:
		if tickets[id]['Owner'] == ctx.author.id:
			overwrites = {
				user: discord.PermissionOverwrite(read_messages=False,send_messages = False,read_message_history=False,attach_files=False)
			}
			await ctx.channel.edit(overwrites = overwrites)
			await ctx.respond(f':white_check_mark: You have removed {user} from the Ticket.')

		else:
			await ctx.respond('This ticket is not claimed by you.')

	else:
		await ctx.respond('Invalid Ticket Channel.')
	
	#ctx.message.delete()

async def open_ticket_button_clicked(interaction,command=False):
	global guildModRoles
	
	await interaction.response.defer()
	
	channel = await bot.fetch_channel(interaction.channel.id)
	guild = channel.guild
	member = channel.guild.get_member(int(interaction.user.id))
	if member == bot.user:
		return
	
	if str(member.id) in blacklistedUsers[str(guild.id)]:
		return
	
	#emoji = payload.emoji
	#emoji = str(emoji)
	with open('Tickets.json') as f:
		try:
			tickets = json.load(f)
		except:
			tickets = {}
	
	with open('Database.json') as f:
		database = json.load(f)
	
	id1 = str(channel.category.id)
	
	if not command:
		msg = await channel.fetch_message(interaction.message.id)
	if id1 in database:
		if not command:
			if not msg is None:
				if 'MSG' in database[id1]:
					if not interaction.message.id == database[id1]['MSG']:
						return
	
		#await msg.remove_reaction(emoji,member)
		role = discord.utils.get(guild.roles,name = guildModRoles[str(guild.id)])
		overwrites = {
			guild.default_role: discord.PermissionOverwrite(read_messages=False),
			role:discord.PermissionOverwrite(read_messages = True,send_messages = True,read_message_history=True,attach_files=True),
			guild.me: discord.PermissionOverwrite(read_messages=True,send_messages = True,read_message_history=True,attach_files=True),
			member: discord.PermissionOverwrite(read_messages=True,send_messages = True,read_message_history=True,attach_files=True)
		}
		category = discord.utils.get(guild.categories,id = int(id1))
		#print(category)
		channel = await guild.create_text_channel(f'ticket-{member.name}', overwrites=overwrites)#,category = category)
		await channel.edit(category = category)
		
		msg = f"Hi there {member.mention} Our {role.mention} have been notified of this Ticket and will be with you as soon as they can.\n\n**__Want to the close the ticket?__**\nPress the :lock: emoji."
		embed = discord.Embed(title = "__GENERAL SUPPORT TICKET__",color = return_color(str(guild.id)),description = msg)
		embed.set_footer(text = 'Dodo Mail | ©️ 2022 | www.thelandofark.com',icon_url='https://i.imgur.com/hODYmHU.png')
		embed.set_thumbnail(url = return_thumbnail(str(guild.id)))
		
		view = View() 
		claimButton=discord.ui.Button(style=discord.ButtonStyle.grey, label='📌 Claim/Unclaim', custom_id="button_claim")
		closeButton=discord.ui.Button(style=discord.ButtonStyle.grey, label="🔒 Close", custom_id="button_close")
		view.add_item(claimButton)
		view.add_item(closeButton)
		
		ticketTopMessage=await channel.send(embed = embed, view = view)
		tickets[str(channel.id)] = {}
		tickets[str(channel.id)]['Owner'] = 'NONE'
		tickets[str(channel.id)]['Creator'] = member.id
		tickets[str(channel.id)]['TicketTopMessage'] = ticketTopMessage.id
		tickets[str(channel.id)]['Guild'] = interaction.guild.id
		tickets[str(channel.id)]['Category'] = category.id
		with open('Tickets.json','w') as f:
			json.dump(tickets,f,indent = 3)
		
		msg = f"Hi there {member.mention}, a Ticket has been created in the {channel.mention} channel. Please visit the ticket and explain the reason for opening it."
		embed = discord.Embed(title = 'Ticket Created',description =  msg,color = return_color(str(guild.id)))
		embed.set_footer(text = 'Dodo Mail | ©️ 2022 | www.thelandofark.com',icon_url='https://i.imgur.com/hODYmHU.png')
		embed.set_image(url = 'https://i.imgur.com/HAsfEXH.png')
		try:
			await member.send(embed = embed)
		except:
			await interaction.channel.send(embed = embed)

async def ticket_close_cmd(interaction,tickets,id,guild):
	
	#await interaction.response.defer()
	
	msg = f"{interaction.user.mention}, Are you sure you would like to close this ticket?"
	embed = discord.Embed(title = 'Close Ticket',color = return_color(str(interaction.guild.id)),description = msg)
	embed.set_footer(text = 'Dodo Mail | ©️ 2022 | www.thelandofark.com',icon_url='https://i.imgur.com/hODYmHU.png')
	embed.set_thumbnail(url = return_thumbnail(str(interaction.guild.id)))
	
	view=View()
	buttonCloseOk=discord.ui.Button(style=discord.ButtonStyle.red, label='Close', custom_id="button_close_ok")
	buttonCloseCancel=discord.ui.Button(style=discord.ButtonStyle.grey, label="Cancel", custom_id="button_close_cancel")
	view.add_item(buttonCloseOk)
	view.add_item(buttonCloseCancel)
	
	await interaction.response.send_message(embed = embed, view=view)
	try:
		
		res = await bot.wait_for("interaction",timeout = 20)
		if res.custom_id == 'button_close_ok':
			#await res.respond(type='7')
			#await res.response.defer()

			import chat_exporter
			file = await chat_exporter.quick_export(interaction)
			try:
				author = await bot.fetch_user(int(tickets[id]['Creator']))
				await author.send(file = file)  
			except:
				pass

			for channels in interaction.channel.category.channels:
				if 'transcript' in channels.name:
					ch = channels
					break
			
			try:
				embed = discord.Embed(color = return_color(str(interaction.guild.id)),description = f'Transcript sent to {author.mention}')
				await interaction.channel.send(embed = embed)
			except:
				await interaction.channel.send('Author has left the Server. [Transcript not sent]')

			embed = discord.Embed(color = return_color(str(interaction.guild.id)),description = f'Transcript sent to {ch.mention}')
			await interaction.channel.send(embed = embed)

			file = await chat_exporter.quick_export(interaction)
			try:
				await ch.send(file = file)
			except:
				print("Error sending to transcript channel, it may have been deleted")

			embed = discord.Embed(color = return_color(str(interaction.guild.id)),description = 'This ticket has been CLOSED.')
			embed.set_footer(text = 'Dodo Mail | ©️ 2022 | www.thelandofark.com',icon_url='https://i.imgur.com/hODYmHU.png')
			embed.set_thumbnail(url = return_thumbnail(str(interaction.guild.id)))
			await interaction.channel.send(embed = embed)

			
			msg = f"{author.mention} I've really enjoyed talking with you. If you need support again feel free to open a new ticket."
			embed = discord.Embed(color = return_color(str(interaction.guild.id)),title = 'Ticket Closed',description = msg)
			embed.set_footer(text = 'Dodo Mail | ©️ 2022 | www.thelandofark.com',icon_url='https://i.imgur.com/hODYmHU.png')
			embed.set_image(url = 'https://i.imgur.com/Wfsj20u.png')
			try:
				await author.send(embed = embed)
			except:
				await interaction.channel.send(embed = embed)
			
			await interaction.delete_original_message()
			await interaction.channel.send(':clock1: This channel will be automatically deleted in 30 seconds.')
			await asyncio.sleep(30)
			await interaction.channel.delete()

		else:
			await interaction.channel.send('Request Cancelled!')
			return

	except asyncio.TimeoutError:
		await interaction.channel.send(':warning: Request Timed-Out')
			
async def ticket_claim_cmd(interaction,tickets,id,guild):
	global guildModRoles
	
	channel = interaction.channel
	if id in tickets:
		author = await bot.fetch_user(int(tickets[id]['Creator']))

		if tickets[id]['Owner'] == 'NONE':

			role = discord.utils.get(interaction.guild.roles,name = guildModRoles[str(interaction.guild.id)])
			if interaction.user.guild_permissions.administrator:
				pass

			elif not role in interaction.user.roles:
				await interaction.response.send_message(":warning: You don't have enough permissions to CLAIM this ticket.")
				return

			tickets[id]['Owner'] = interaction.user.id
			with open('Tickets.json','w') as f: 
				json.dump(tickets,f,indent = 3)

			overwrites = {
				role:discord.PermissionOverwrite(read_messages = False,send_messages = False),
				interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
				interaction.guild.me: discord.PermissionOverwrite(read_messages=True,send_messages = True,read_message_history=True,attach_files=True),
				interaction.user: discord.PermissionOverwrite(read_messages=True,send_messages = True,read_message_history=True,attach_files=True),
				author: discord.PermissionOverwrite(read_messages=True,send_messages = True,read_message_history=True,attach_files=True)
			}

			await interaction.channel.edit(overwrites = overwrites)
			msg = f'This ticket was claimed by {interaction.user.mention}'

			embed = discord.Embed(title = 'Ticket Claimed',color = return_color(str(interaction.guild.id)),description = msg)
			embed.set_footer(text = 'Dodo Mail | ©️ 2022 | www.thelandofark.com',icon_url='https://i.imgur.com/hODYmHU.png')
			embed.set_thumbnail(url = return_thumbnail(str(interaction.guild.id)))
			await interaction.response.send_message(embed = embed,ephemeral=False)
			#await interaction.response.send_message(':white_check_mark: Ticket claimed')

		elif tickets[id]['Owner'] == interaction.user.id:
			#await channel.send(':white_check_mark: You have left the TICKET.')
			role = discord.utils.get(interaction.guild.roles,name = guildModRoles[str(interaction.guild.id)])
			overwrites = {
				role:discord.PermissionOverwrite(read_messages = True,send_messages = True,read_message_history=True,attach_files=True),
				author: discord.PermissionOverwrite(read_messages=True,send_messages = True,read_message_history=True,attach_files=True),
				interaction.user: discord.PermissionOverwrite(read_messages=False,send_messages = False)
			}
			await interaction.channel.edit(overwrites = overwrites)
			tickets[id]['Owner'] = 'NONE'
			with open('Tickets.json','w') as f: 
				json.dump(tickets,f,indent = 3)
				
			msg = f'This ticket was unclaimed by {interaction.user.mention}'
			embed = discord.Embed(title = 'Ticket Unclaimed',color = return_color(str(interaction.guild.id)),description = msg)
			embed.set_footer(text = 'Dodo Mail | ©️ 2022 | www.thelandofark.com',icon_url='https://i.imgur.com/hODYmHU.png')
			embed.set_thumbnail(url = return_thumbnail(str(interaction.guild.id)))
			await interaction.response.send_message(embed = embed,ephemeral=False)
			#await interaction.response.send_message(':white_check_mark: You have left the TICKET.')
			#await interaction.respond(type='7')

		else:
			await interaction.response.send_message(':warning: This ticket is already claimed by someone else.')

@bot.slash_command(description=getHelpText("help"))
@discord.guild_only()
async def help(ctx):
	
	messageToSend = ""
	for command in bot.walk_application_commands():
		#print(command.qualified_name)
		options = ""
		try:
			for option in command.options:
				if option.required:
					options = options + "["+option.name+"] "
				else:
					options = options + "("+option.name+") "
		except:
			handleErrorLogging(traceback.format_exc())
			pass
		
		#command.description
		if not " commands" in command.description:
			messageToSend = messageToSend + "`/"+str(command.qualified_name)+" "+options+"`\n"+helptext[command.qualified_name]+"\n\n"
	
	embed=discord.Embed(title="Commands:", description=messageToSend,color = return_color(str(ctx.guild.id)))
	embed.set_footer(text = 'Dodo Mail | ©️ 2022 | www.thelandofark.com',icon_url='https://i.imgur.com/hODYmHU.png')
	embed.set_thumbnail(url = return_thumbnail(str(ctx.guild.id)))
	await ctx.respond(embed=embed)

@bot.slash_command(description=getHelpText("new"))
@discord.guild_only()
async def new(ctx):
	await open_ticket_button_clicked(ctx.interaction,True)

@bot.slash_command(description=getHelpText("supportrole"))
@discord.guild_only()
@discord.default_permissions(administrator=True)
async def supportrole(ctx,role:discord.Role):
	global guildModRoles
	
	guildModRoles[str(ctx.guild.id)]=role.name
	util.save_data(guildModRoles, "guildModRoles")
	await ctx.respond("Role set")
		
@bot.slash_command(description=getHelpText("rename"))
@discord.guild_only()
async def rename(ctx,name):
	global guildModRoles
	
	with open('Tickets.json') as f:
		try:
			tickets = json.load(f)
		except:
			tickets = {}
	
	for ticket in tickets:
		if str(ticket) == str(ctx.interaction.channel.id):
			msgToEdit = await ctx.interaction.channel.fetch_message(tickets[ticket]["TicketTopMessage"])
			
			'''
			view = View() 
			claimButton=discord.ui.Button(style=discord.ButtonStyle.grey, label='📌 Claim/Unclaim', custom_id="button_claim")
			closeButton=discord.ui.Button(style=discord.ButtonStyle.grey, label="🔒 Close", custom_id="button_close")
			view.add_item(claimButton)
			view.add_item(closeButton)
			'''
			
			member = ctx.guild.get_member(tickets[ticket]["Creator"])
			role = discord.utils.get(ctx.guild.roles,name = guildModRoles[str(ctx.guild.id)])
			msg = f"Hi there {member.mention} Our {role.mention} have been notified of this Ticket and will be with you as soon as they can.\n\n**__Want to the close the ticket?__**\nPress the :lock: emoji."
			embed = discord.Embed(title = "__"+str(name)+"__",color = return_color(str(ctx.guild.id)),description = msg)
			embed.set_footer(text = 'Dodo Mail | ©️ 2022 | www.thelandofark.com',icon_url='https://i.imgur.com/hODYmHU.png')
			embed.set_thumbnail(url = return_thumbnail(str(ctx.guild.id)))
			
			await msgToEdit.edit(embed=embed)
			return await ctx.respond("Ticket name changed")

@bot.slash_command(description=getHelpText("ticketpurge"))
@discord.guild_only()
async def ticketpurge(ctx,amount:int):
	global guildModRoles
	
	await ctx.defer()
	
	if amount < 1:
		return await ctx.respond("Invalid amount")
	
	ticketHandled = None
	with open('Tickets.json') as f:
		try:
			tickets = json.load(f)
		except:
			tickets = {}
	
	def is_not_top(m):
		return m.id != int(tickets[ticketHandled]["TicketTopMessage"])
	
	for ticket in tickets:
		if str(ticket) == str(ctx.interaction.channel.id):
			role = discord.utils.get(ctx.guild.roles,name = guildModRoles[str(ctx.guild.id)])
			if not role in ctx.interaction.user.roles:
				return await ctx.respond("You dont have permission to use this command")
			else:
				channel = bot.get_channel(int(ticket))
				ticketHandled=ticket
				deleted = await channel.purge(limit=amount, check=is_not_top)
				return await ctx.respond(f'Deleted {len(deleted)} message(s)')
	
	return await ctx.respond("This is not a ticket")

@bot.slash_command(description=getHelpText("transcript"))
@discord.guild_only()
async def transcript(ctx):
	
	await ctx.defer()
	
	with open('Tickets.json') as f:
		try:
			tickets = json.load(f)
		except:
			tickets = {}
	
	for ticket in tickets:
		if str(ticket) == str(ctx.interaction.channel.id):
			import chat_exporter
			file = await chat_exporter.quick_export(ctx.interaction)
			try:
				await ctx.interaction.user.send(file = file)
			except:
				await ctx.interaction.messge.channel.send(file = file)
			return await ctx.respond("Transcript created")
	
	return await ctx.respond("This is not a ticket")

@bot.slash_command(description=getHelpText("claim"))
@discord.guild_only()
async def claim(ctx):

	with open('Tickets.json') as f:
		try:
			tickets = json.load(f)
		except:
			tickets = {}
	
	for ticket in tickets:
		if str(ticket) == str(ctx.interaction.channel.id):
			guild = str(ctx.interaction.guild.id)
			id = str(ctx.interaction.channel.id)
			return await ticket_claim_cmd(ctx.interaction,tickets,id,guild)

@bot.slash_command(description=getHelpText("unclaim"))
@discord.guild_only()
async def unclaim(ctx):

	with open('Tickets.json') as f:
		try:
			tickets = json.load(f)
		except:
			tickets = {}
	
	for ticket in tickets:
		if str(ticket) == str(ctx.interaction.channel.id):
			guild = str(ctx.interaction.guild.id)
			id = str(ctx.interaction.channel.id)
			return await ticket_claim_cmd(ctx.interaction,tickets,id,guild)

@bot.slash_command(description=getHelpText("close"))
@discord.guild_only()
async def close(ctx):
	
	with open('Tickets.json') as f:
		try:
			tickets = json.load(f)
		except:
			tickets = {}
	
	for ticket in tickets:
		if str(ticket) == str(ctx.interaction.channel.id):
			guild = str(ctx.interaction.guild.id)
			id = str(ctx.interaction.channel.id)
			return await ticket_close_cmd(ctx.interaction,tickets,id,guild)

@bot.slash_command(description=getHelpText("blacklist"))
@discord.guild_only()
async def blacklist(ctx,member:discord.Member):
	global guildModRoles
	
	for role in ctx.interaction.user.roles:
		if role.permissions.administrator:
			admin = True
	if not admin:
		role = discord.utils.get(ctx.guild.roles,name = guildModRoles[str(ctx.guild.id)])
		if not role in ctx.interaction.user.roles:
			return
	
	if not str(ctx.guild.id) in blacklistedUsers:
		blacklistedUsers[str(ctx.guild.id)] = []
	if not str(member.id) in blacklistedUsers[str(ctx.guild.id)]:
		blacklistedUsers[str(ctx.guild.id)].append(str(member.id))
		util.save_data(blacklistedUsers, "blacklistedUsers")
		await ctx.respond("Member blacklisted")
	else:
		await ctx.respond("Member already blacklisted")
	
@bot.slash_command(description=getHelpText("unblacklist"))
@discord.guild_only()
async def unblacklist(ctx,member:discord.Member):
	global guildModRoles
	
	for role in ctx.interaction.user.roles:
		if role.permissions.administrator:
			admin = True
	
	if not admin:
		role = discord.utils.get(ctx.guild.roles,name = guildModRoles[str(ctx.guild.id)])
		if not role in ctx.interaction.user.roles:
			return
	
	if not str(ctx.guild.id) in blacklistedUsers:
		blacklistedUsers[str(ctx.guild.id)] = []
	if str(member.id) in blacklistedUsers[str(ctx.guild.id)]:
		blacklistedUsers[str(ctx.guild.id)].remove(str(member.id))
		util.save_data(blacklistedUsers, "blacklistedUsers")
		await ctx.respond("Member unblacklisted")
	else:
		await ctx.respond("Member not blacklisted")


@bot.slash_command(description=getHelpText("reset"))
@discord.guild_only()
@discord.default_permissions(administrator=True)
async def reset(ctx):
	global guildModRoles
	
	if str(ctx.guild.id) in blacklistedUsers:
		del blacklistedUsers[str(ctx.guild.id)]
		util.save_data(blacklistedUsers, "blacklistedUsers")
	
	if str(ctx.guild.id) in guildModRoles:
		del guildModRoles[str(ctx.guild.id)]
		util.save_data(guildModRoles, "guildModRoles")
	
	if str(ctx.guild.id) in ticketEmbeds:
		del ticketEmbeds[str(ctx.guild.id)]
		util.save_data(ticketEmbeds, "ticketEmbeds")
	
	with open('Database.json') as f:
		try:
			data = json.load(f)
		except:
			data = {}
	
	for category in ctx.guild.categories:
		if str(category.id) in data:
			del data[str(category.id)]
	
	with open('Database.json','w') as f:
		json.dump(data,f,indent = 3)
	
	await ctx.respond("All settings for this server removed")

@bot.slash_command(description=getHelpText("botinfo"))
@discord.guild_only()
async def botinfo(ctx):
	
	if not str(config.ownerId) == str(ctx.author.id):
		return False
	
	owner = config.owner
	
	with open('Tickets.json') as f:
		tickets = json.load(f)
	
	numTotalUsers = 0
	for member in bot.get_all_members():
		numTotalUsers = numTotalUsers+1
	
	totalBlacklisted = 0
	for guildid in blacklistedUsers:
		for memberid in blacklistedUsers[guildid]:
			totalBlacklisted=totalBlacklisted+1
	
	messageToSend="Owner: "+str(owner)+"\n"+"Created Tickets: "+str(len(tickets))+"\nNumber of Servers: "+str(len(bot.guilds))+"\nTotal Members: "+str(numTotalUsers)+"\nTotal Blacklisted: "+str(totalBlacklisted)
	embed=discord.Embed(title="Bot Statistics:", description=messageToSend,color = return_color(str(ctx.guild.id)))
	await ctx.respond(embed=embed)

@bot.slash_command(description=getHelpText("invite"))
@discord.guild_only()
async def invite(ctx):

	await ctx.respond("To invite the bot in your server use this link:\n https://discord.com/api/oauth2/authorize?client_id=" + str(bot.user.id) + "&permissions=517544070224&scope=bot%20applications.commands")

@bot.slash_command(description=getHelpText("serverinfo"))
@discord.guild_only()
async def serverinfo(ctx):
	
	with open('Tickets.json') as f:
		tickets = json.load(f)
	
	serverTickets = 0
	for ticket in tickets:
		if "Guild" in tickets[ticket]:
			if int(tickets[ticket]["Guild"]) == int(ctx.guild.id):
				serverTickets=serverTickets+1
	
	blacklistedMembers = "Blacklisted Members:\n"
	if str(ctx.guild.id) in blacklistedUsers:
		for memberid in blacklistedUsers[str(ctx.guild.id)]:
			try:
				member=ctx.guild.get_member(int(memberid))
			except:
				member="ID: "+str(memberid)
			blacklistedMembers=blacklistedMembers+member+"\n"
	
	messageToSend="Server Owner: "+str(ctx.guild.owner)+"\n"+"Created Tickets: "+str(serverTickets)+"\nTotal Members: "+str(len(ctx.guild.members))+"\n"+blacklistedMembers
	embed=discord.Embed(title="Server Statistics:", description=messageToSend,color = return_color(str(ctx.guild.id)))
	await ctx.respond(embed=embed)

@bot.slash_command(description=getHelpText("sponsor"))
@discord.guild_only()
async def sponsor(ctx):
	embed=discord.Embed(title="Sponsors", description=config.sponsorInfo,color = return_color(str(ctx.guild.id)))
	await ctx.respond(embed=embed)

@bot.slash_command(description=getHelpText("support"))
@discord.guild_only()
async def support(ctx):
	await ctx.respond(config.supportInvite)


@bot.slash_command(description=getHelpText("userinfo"))
@discord.guild_only()
async def userinfo(ctx,user:discord.Member):
	
	with open('Tickets.json') as f:
		tickets = json.load(f)
	
	serverTickets = 0
	for ticket in tickets:
		if "Guild" in tickets[ticket]:
			if int(tickets[ticket]["Guild"]) == int(ctx.guild.id):
				if int(tickets[ticket]["Creator"]) == int(user.id):
					serverTickets=serverTickets+1
	
	blacklistStatus=False
	if str(user.id) in blacklistedUsers[str(ctx.guild.id)]:
		blacklistStatus=True
	
	messageToSend=user.mention+" ("+str(user.id)+")\nBlacklisted: "+str(blacklistStatus)+"\nCreated Tickets: "+str(serverTickets)
	embed=discord.Embed(title="Member Statistics:", description=messageToSend,color = return_color(str(ctx.guild.id)))
	await ctx.respond(embed=embed)
	
bot.run(config.discordtoken)