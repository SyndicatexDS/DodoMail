import configparser
import os, sys, codecs

if getattr(sys, 'frozen', False):
	application_path = os.path.dirname(sys.executable)
elif __file__:
	application_path = os.path.dirname(__file__)

config = configparser.ConfigParser()

config.read_file(codecs.open(str(application_path) + '/config.ini', "r", "utf8"))

discordtoken = config['SETTINGS']['discordtoken'].strip()
adminRole = config['SETTINGS']['adminRole'].strip()
owner = config['SETTINGS']['owner'].strip()
testServer=123
sponsorInfo=config['SETTINGS']['sponsorInfo'].strip()
supportInvite=config['SETTINGS']['supportInvite'].strip()
ownerId=config['SETTINGS']['ownerId'].strip()

