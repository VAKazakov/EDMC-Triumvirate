﻿from config import config
import myNotebook as nb
from urllib import quote_plus
import requests
import json

from modules import journaldata
from modules import factionkill
from modules import nhss
from modules import codex
from modules import hdreport
from modules import news
from modules import release
from modules import legacy
from modules import legacyCanonn as Clegacy
from modules import clientreport
from modules import fssreports
from modules import patrol
#from modules import friendfoe as FF
from modules.systems import Systems
from modules.debug import Debug
from modules.debug import debug
from modules import materialReport

from modules.whitelist import whiteList



import ttk
import Tkinter as tk
import sys
    
this = sys.modules[__name__]
    
this.Squadrons=[
    ' ',
    "CEC",
    "EGP"]
this.nearloc = {
   'Latitude' : None,
   'Longitude' : None,
   'Altitude' : None,
   'Heading' : None,
   'Time' : None
}


myPlugin = 'EDMC-Triumvirate'


this.version='1.0.9'
this.client_version='{}.{}'.format(myPlugin,this.version)
this.body_name=None
this.SysFactionState=None    
def plugin_prefs(parent, cmdr, is_beta):
    '''
    Return a TK Frame for adding to the EDMC settings dialog.
    '''
    this.SquadronID = config.get("SquadronID")	# Retrieve saved value from config
    this.SquadronID_conf= ""


    frame = nb.Frame(parent)
    frame.columnconfigure(1, weight=1)
    
    this.news.plugin_prefs(frame, cmdr, is_beta,1)
    this.release.plugin_prefs(frame, cmdr, is_beta,2)
    this.patrol.plugin_prefs(frame, cmdr, is_beta,3)
    Debug.plugin_prefs(frame,this.client_version,4)
    this.codexcontrol.plugin_prefs(frame, cmdr, is_beta,5)
    #this.FF.FriendFoe.plugin_prefs(frame, cmdr, is_beta,6)
    hdreport.HDInspector(frame,cmdr, is_beta,this.client_version,7)
    #release.versionInSettings(frame, cmdr, is_beta,8)
   # entry=nb.Entry(frame,None)
    nb.OptionMenu(frame, variable=this.SquadronID_conf, default = this.SquadronID, *this.Squadrons).grid(row = 9, column = 0,columnspan=2,sticky=tk.W)
    
    
    
    return frame

    
def prefs_changed(cmdr, is_beta):
    '''
    Save settings.
    '''
    this.news.prefs_changed(cmdr, is_beta)
    this.release.prefs_changed(cmdr, is_beta)
    this.patrol.prefs_changed(cmdr, is_beta)
    this.codexcontrol.prefs_changed(cmdr, is_beta)
    config.set('SquadronID', this.SquadronID_conf)
    Debug.prefs_changed()
    
   
def plugin_start(plugin_dir):
    '''
    Load Template plugin into EDMC
    '''
    
    #print this.patrol
    release.Release.plugin_start(plugin_dir)
    Debug.setClient(this.client_version)
    patrol.CanonnPatrol.plugin_start(plugin_dir)
    codex.CodexTypes.plugin_start(plugin_dir)
    this.SquadronID=config.get("SquadronID")
    debug(this.SquadronID)
    
    return 'Triumvirate'
    
def plugin_stop():
    '''
    EDMC is closing
    '''
    debug('Stopping the plugin')
    this.patrol.plugin_stop()
    
def plugin_app(parent):

    this.parent = parent
    #create a new frame as a containier for the status
    padx, pady = 10, 5  # formatting
    sticky = tk.EW + tk.N  # full width, stuck to the top
    anchor = tk.NW

    frame = this.frame = tk.Frame(parent)
    frame.columnconfigure(0, weight=1)

    table = tk.Frame(frame)
    table.columnconfigure(1, weight=1)
    table.grid(sticky='NSEW')
    
    this.codexcontrol = codex.CodexTypes(table,0)
    this.news = news.CECNews(table,1)
    this.release = release.Release(table,this.version,2)
    this.patrol = patrol.CanonnPatrol(table,3)
    whitelist=whiteList(parent)
    whitelist.fetchData()
    
    
    
    return frame
    
   
def journal_entry(cmdr, is_beta, system, station, entry, state):
    '''
    
    '''
    # capture some stats when we launch not read for that yet
    startup_stats(cmdr)
    
    if entry.get("event") == "FSDJump":
        Systems.storeSystem(system,entry.get("StarPos"))
        
    if ('Body' in entry):
            this.body_name = entry['Body']
    
    if "SystemFaction" in entry:
        ''' "SystemFaction": { “Name”:"Mob of Eranin", "FactionState":"CivilLiberty" } }'''
        SystemFaction=entry.get("SystemFaction")
        debug(SystemFaction)
        try:
            this.SysFactionState= SystemFaction["FactionState"]
        except: 
            this.SysFactionState=None
        debug(this.SysFactionState)
    
    #if entry.get("event")== "JoinedSquadron":
    #    if entry["SquadronName"]== "EG PILOTS":
    #       this.SquadronID="EGPU"
    #    elif entry["SquadronName"]== "Close Encouters Corps":
    #        this.SquadronID = "SCEC"
    #    else:
    #        this.SquadronID = None
    #    debug(this.SquadronID)
    #    config.set('this.SquadronID', this.SquadronID.get())

    if system:
        x,y,z=Systems.edsmGetSystem(system)
    else:
        x=None
        y=None
        z=None    
    
    return journal_entry_wrapper(cmdr, is_beta, system,this.SysFactionState, station, entry, state,x,y,z,this.body_name,this.nearloc['Latitude'],this.nearloc['Longitude'],this.client_version)    
    

def journal_entry_wrapper(cmdr, is_beta, system,SysFactionState, station, entry, state,x,y,z,body,lat,lon,client):
    '''
    Detect journal events
    '''
    factionkill.submit(cmdr, is_beta, system, station, entry,client)
    nhss.submit(cmdr, is_beta, system, station, entry,client)
    hdreport.submit(cmdr, is_beta, system, station, entry,client)
    codex.submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
    fssreports.submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
    journaldata.submit(cmdr, is_beta, system, station, entry,client)
    clientreport.submit(cmdr,is_beta,client,entry)
    this.patrol.journal_entry(cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client)
    this.codexcontrol.journal_entry(cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client)
    whiteList.journal_entry(cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client)
    materialReport.submit(cmdr, is_beta, system, station, entry,client,lat,lon,body,SysFactionState,x,y,z)



    #legacy to canonn
    Clegacy.statistics(cmdr, is_beta, system, station, entry, state)
    Clegacy.CodexEntry(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
    Clegacy.AXZone(cmdr, is_beta, system,x,y,z, station, entry, state)
    Clegacy.faction_kill(cmdr, is_beta, system, station, entry, state)
    Clegacy.NHSS.submit(cmdr, is_beta, system,x,y,z, station, entry,client)

    #Triumvirate reporting
    #FF.FriendFoe.friendFoe(cmdr, system, station, entry, state)

    # legacy logging to google sheets
    legacy.statistics(cmdr, is_beta, system, station, entry, state)
    legacy.CodexEntry(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
    legacy.AXZone(cmdr, is_beta, system,x,y,z, station, entry, state)
    legacy.faction_kill(cmdr, is_beta, system, station, entry, state)
    #legacy.NHSS.submit(cmdr, is_beta, system,x,y,z, station, entry,client)
    
    

    
    
def dashboard_entry(cmdr, is_beta, entry):
      
    
    this.landed = entry['Flags'] & 1<<1 and True or False
    this.SCmode = entry['Flags'] & 1<<4 and True or False
    this.SRVmode = entry['Flags'] & 1<<26 and True or False
    this.landed = this.landed or this.SRVmode
      #print 'LatLon = {}'.format(entry['Flags'] & 1<<21 and True or False)
      #print entry
    if(entry['Flags'] & 1<<21 and True or False):
        if('Latitude' in entry):
            this.nearloc['Latitude'] = entry['Latitude']
            this.nearloc['Longitude'] = entry['Longitude']
    else:
        this.body_name = None
        this.nearloc['Latitude'] = None
        this.nearloc['Longitude'] = None  
    
    
def cmdr_data(data, is_beta):
    '''
    We have new data on our commander
    '''
    #debug(json.dumps(data,indent=4))
    this.patrol.cmdr_data(data, is_beta)


def startup_stats(cmdr):
    try:
        this.first_event
    except:
      this.first_event = True
      addr = requests.get('https://api.ipify.org').text
      addr6 = requests.get('https://api6.ipify.org').text
      url="https://docs.google.com/forms/d/1h7LG5dEi07ymJCwp9Uqf_1phbRnhk1R3np7uBEllT-Y/formResponse?usp=pp_url"
      url+="&entry.1181808218="+quote_plus(cmdr)
      url+="&entry.254549730="+quote_plus(this.version)
      url+="&entry.1622540328="+quote_plus(addr)
      if addr6 != addr:
          url+="&entry.488844173="+quote_plus(addr6)
      else:
          url+="&entry.488844173="+quote_plus("0")
      legacy.Reporter(url).start()






