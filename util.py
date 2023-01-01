import json
import traceback
import os
from os import listdir
from os.path import isfile, join
import copy
from collections import OrderedDict
import collections

oldData = {}

def save_data(obj, name,forceList=False):
	global oldData
	
	if (not isinstance(obj, (list,)) and (not isinstance(obj, str)) and (not forceList)):
		if not os.path.exists('save/'+ name):
			os.makedirs('save/'+ name)
		
		if not name in oldData:
			oldData[name] = {}
		
		for id in obj:
			needsSave = False
			if not id in oldData[name]:
				#print("id "+str(id)+" does not exist in save")
				needsSave = True
			else:
				if oldData[name][id] != obj[id]:
					#print("id "+str(id)+" has changed")
					needsSave = True
				#else:
					#print(oldData[name][id],obj[id])
			
			if needsSave:
				try:
					with open('save/'+ str(name) +"/"+str(id)+ '.json', 'w') as f:
						#print("Save data start")
						json.dump(obj[id], f)
						#print("Save data finish")
				except Exception as ex:
					print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
			#else:
				#print("id "+str(id)+" has not changed")
		
		for oldId in oldData[name]:
			validToRemove = True
			if str(oldId) in obj:
				validToRemove = False
			try:
				if int(oldId) in obj:
					validToRemove = False
			except:
				pass
			
			if validToRemove:
				try:
					os.remove('save/'+ str(name) +"/"+str(oldId)+ '.json')
				except:
					print("Error when removing unsued id from "+str(name)+" ID "+str(oldId))
			
		oldData[name] = copy.deepcopy(obj)
		
	elif isinstance(obj, str):
		#print("Going to save string")
		try:
			if not name in oldData:
				oldData[name] = ""
			oldData[name] = copy.deepcopy(obj)
			with open('save/'+ name + '.json', 'w') as f:
				#print("Save data start")
				json.dump(obj, f)
				#print("Save data finish")
		except Exception as ex:
			print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
			
	else:
		try:
			if not name in oldData:
				oldData[name] = {}
			oldData[name] = copy.deepcopy(obj)
			with open('save/'+ name + '.json', 'w') as f:
				#print("Save data start")
				json.dump(obj, f)
				#print("Save data finish")
		except Exception as ex:
			print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))

def load_data(name):
	global oldData
	
	oldData[name] = {}
	#print("Trying to load folder",str(name))
	
	try:
		onlyfiles = [f for f in listdir("save/"+str(name)+"/") if isfile(join("save/"+str(name)+"/", f))]
	except:
		#print("Error reading folder "+str(name))
		onlyfiles = []
		
	for file in onlyfiles:
		#print(str(file))
		id = str(file).replace(".json","")
		if os.path.isfile('save/'+ name +"/"+str(file)):
			try:
				with open('save/'+ name +"/"+str(file), 'r') as f:
					oldData[name][id] = json.load(f)
			except Exception as ex:
				print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
	
	return copy.deepcopy(oldData[name])

def load_dataSorted(name):
	global oldData
	
	oldData[name] = {}
	#print("Trying to load folder",str(name))
	
	try:
		onlyfilesFullPath = ["save/"+str(name)+"/"+str(f) for f in listdir("save/"+str(name)+"/") if isfile(join("save/"+str(name)+"/", f))]
	except:
		#print("Error reading folder "+str(name))
		onlyfilesFullPath = []
	
	#print(onlyfilesFullPath)
	onlyfilesFullPath = sorted( onlyfilesFullPath,
                        key = os.path.getmtime)
	
	onlyfiles = []
	for fileNew in onlyfilesFullPath:
		onlyfiles.append(fileNew.split("/")[-1])
	
	#print(onlyfiles)
	for file in onlyfiles:
		#print(str(file))
		id = str(file).replace(".json","")
		if os.path.isfile('save/'+ name +"/"+str(file)):
			try:
				with open('save/'+ name +"/"+str(file), 'r') as f:
					oldData[name][id] = json.load(f)
			except Exception as ex:
				print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
	
	return copy.deepcopy(oldData[name])

def load_dataIntegerKeys(name):
	global oldData
	
	oldData[name] = {}
	#print("Trying to load folder",str(name))
	
	try:
		onlyfiles = [f for f in listdir("save/"+str(name)+"/") if isfile(join("save/"+str(name)+"/", f))]
	except:
		#print("Error reading folder "+str(name))
		onlyfiles = []
		
	for file in onlyfiles:
		#print(str(file))
		id = str(file).replace(".json","")
		if os.path.isfile('save/'+ name +"/"+str(file)):
			try:
				with open('save/'+ name +"/"+str(file), 'r') as f:
					oldData[name][int(id)] = json.load(f)
			except Exception as ex:
				print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
	
	return copy.deepcopy(oldData[name])

def load_dataOrderedDict(name):
	global oldData
	
	oldData[name] = collections.OrderedDict()
	#print("Trying to load folder",str(name))
	
	try:
		onlyfiles = [f for f in listdir("save/"+str(name)+"/") if isfile(join("save/"+str(name)+"/", f))]
		onlyfiles.sort(key=lambda x: os.path.getmtime("save/"+str(name)+"/"+x))
	except Exception as ex:
		#print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
		onlyfiles = []
		
	for file in onlyfiles:
		#print(str(file))
		id = str(file).replace(".json","")
		if os.path.isfile('save/'+ name +"/"+str(file)):
			try:
				with open('save/'+ name +"/"+str(file), 'r') as f:
					oldData[name][id] = json.load(f, object_pairs_hook=OrderedDict)
			except Exception as ex:
				print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
	
	return copy.deepcopy(oldData[name])
		
def load_data1File(name):
	global oldData
	
	oldData[name] = []
	
	if os.path.isfile('save/' + name + '.json'):
		try:
			with open('save/' + name + '.json', 'r') as f:
				oldData[name] = json.load(f)
				return copy.deepcopy(oldData[name])
		except Exception as ex:
			print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
	else:
		oldData[name] = []
		return []

def jsonKeys2int(x):
	if isinstance(x, dict):
		#print(x)
		try:
			return {int(k):v for k,v in x.items()}
		except:
			return {k:v for k,v in x.items()}
	return x

def load_data1FileIntegerKeys(name):
	global oldData
	
	oldData[name] = []
	
	if os.path.isfile('save/' + name + '.json'):
		try:
			with open('save/' + name + '.json', 'r') as f:
				oldData[name] = json.load(f, object_hook=jsonKeys2int)
				return copy.deepcopy(oldData[name])
		except Exception as ex:
			print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
	else:
		oldData[name] = []
		return []