﻿"""
Module to provide the news.
"""


try:
    import tkinter as tk    
    from tkinter import Frame
    from io import BytesIO
    from io import StringIO
except:
    import Tkinter as tk    
    from Tkinter import Frame
    import StringIO
    import StringIO as BytesIO
import uuid
from ttkHyperlinkLabel import HyperlinkLabel
import requests
import json
import re
import myNotebook as nb
from config import config
import zipfile
import io
import os
import shutil
import threading
from  .player import Player
from .debug import debug
from .debug import debug,error
import plug
import random

RELEASE_CYCLE = 60 * 1000 * 60 # 1 Hour
DEFAULT_URL = 'https://github.com/VAKazakov/EDMC-Triumvirate/releases'
WRAP_LENGTH = 200

def _callback(matches):
    id = matches.group(1)
    try:
        return chr(int(id))
    except:
        return id


def decode_unicode_references(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data)

class ReleaseLink(HyperlinkLabel):

    def __init__(self, parent):

        HyperlinkLabel.__init__(self,
            parent,
            text="Поиск",
            url=DEFAULT_URL,
            wraplength=50,  # updated in __configure_event below
            anchor=tk.NW)
        self.bind('<Configure>', self.__configure_event)

    def __configure_event(self, event):
        "Handle resizing."

        self.configure(wraplength=event.width)
    
class ReleaseThread(threading.Thread):
    def __init__(self, release):
        threading.Thread.__init__(self)
        self.release = release
    
    def run(self):
        debug("Release: UpdateThread")
        self.release.release_pull()
        
        
class Release(Frame):

    def __init__(self, parent, release, gridrow):
        "Initialise the ``News``."

        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW        
        
        Frame.__init__(
            self,
            parent
        )
        
        self.installed = False
        
        self.auto = tk.IntVar(value=config.getint("AutoUpdate"))                
        self.novoices = tk.IntVar(value=config.getint("NoVoices"))                
        self.rmbackup = tk.IntVar(value=config.getint("RemoveBackup"))                
        
        self.columnconfigure(1, weight=1)
        self.grid(row = gridrow, column = 0, sticky="NSEW",columnspan=2)
        
        self.label = tk.Label(self, text=  "Версия:")
        self.label.grid(row = 0, column = 0, sticky=sticky)
        
        
        self.hyperlink = ReleaseLink(self)
        self.hyperlink.grid(row = 0, column = 1,sticky="NSEW")
        
        self.button = tk.Button(self, text="Нажмите чтобы обновить", command=self.click_installer)
        self.button.grid(row = 1, column = 0,columnspan=2,sticky="NSEW")
        self.button.grid_remove()
        
        self.release = release
        self.news_count = 0
        self.news_pos = 0
        self.minutes = 0
        self.latest = {}
        self.update()
        #self.hyperlink.bind('<Configure>',
        #self.hyperlink.configure_event)
        
        debug(config.get('Canonn:RemoveBackup'))
        
        if self.rmbackup.get() == 0 and config.get('Canonn:RemoveBackup') != "None":
            delete_dir = config.get('Canonn:RemoveBackup')
            debug('Canonn:RemoveBackup {}'.format(delete_dir))
            try:
                shutil.rmtree(delete_dir)
                
            except:
                error("Cant delete {}".format(delete_dir))
                
            ## lets not keep trying
            config.set('Canonn:RemoveBackup',"None")
            
        
    def update(self):    
        self.release_thread()
        self.after(1000, self.release_update)
        
    def version2number(self,version):
        major,minor,patch = version.split('.')
        return (int(major) * 1000000) + (int(minor) * 1000) + int(patch)

    def release_thread(self):    
        ReleaseThread(self).start()
        
    def release_pull(self):
        self.latest = {}
        r = requests.get("https://api.github.com/repos/VAKazakov/EDMC-Triumvirate/releases/latest")
        latest = r.json()
        #debug(latest)
        if not r.status_code == requests.codes.ok:
            
            error("Error fetching release from github")
            error(r.status_code)
            error(r.json())
            
        else:
            self.latest = latest
            debug("latest release downloaded")
       
        
        
    def release_update(self):

        # if we have just installed a
        # new version we can end the
        # cycle
        if not self.installed:
            
            if self.latest:
                debug("Latest is not null")
                
                
                #checjed again in an
                #hour
                self.after(RELEASE_CYCLE, self.update)    
                
                #self.latest=requests.get("https://api.github.com/repos/VAKazakov/EDMC-Triumvirate/releases/latest").json()
                
                current = self.version2number(self.release)
                release = self.version2number(self.latest.get("tag_name"))
                
                self.hyperlink['url'] = self.latest.get("html_url")
                self.hyperlink['text'] = "EDMC-Triumvirate: {}".format(self.latest.get("tag_name"))

                if current == release:
                    self.grid_remove()
                elif current > release:
                    self.hyperlink['text']= "Тестовая версия {}".format(self.release)                     
                    self.grid()
                    
                else:
                    
                    if self.auto.get() == 1:
                        self.hyperlink['text'] = "Версия {}  установлена. Пожалуйста, перезапустите EDMC".format(self.latest.get("tag_name"))     
                        
                        if self.installer():
                            self.hyperlink['text'] = "Версия {}  установлена. Пожалуйста, перезапустите EDMC".format(self.latest.get("tag_name"))     
                        else:
                            self.hyperlink['text'] = "Обновление до версии {} не удалось".format(self.latest.get("tag_name"))     
                        
                    else:
                        self.hyperlink['text'] = "Пожалуйста поставьте версию {}".format(self.latest.get("tag_name"))
                        self.button.grid()
                        if self.novoices.get() != 1:
                            nag_sel = random.randint(0,1)
                            if nag_sel == 1:
                                Player(Release.plugin_dir,["sounds\\nag1.wav"]).start()
                            else: Player(Release.plugin_dir,["sounds\\nag0.wav"]).start()
                    self.grid()
            else:
                debug("Latest is null")
                self.after(1000,self.release_update)
    
    def plugin_prefs(self, parent, cmdr, is_beta,gridrow):
        "Called to get a tk Frame for the settings dialog."

        self.auto = tk.IntVar(value=config.getint("AutoUpdate"))
        self.rmbackup = tk.IntVar(value=config.getint("RemoveBackup"))
        self.novoices = tk.IntVar(value=config.getint("NoVoices"))
        
        frame = nb.Frame(parent)
        frame.columnconfigure(2, weight=1)
        frame.grid(row = gridrow, column = 0,sticky="NSEW")
        nb.Checkbutton(frame, text="Включить автообновление", variable=self.auto).grid(row = 0, column = 0,sticky="NW")
        nb.Checkbutton(frame, text="Хранить бекапы версий", variable=self.rmbackup).grid(row = 0, column = 1,sticky="NW")
        nb.Checkbutton(frame, text="Отключить голосовые сообщения", variable=self.novoices).grid(row = 0, column = 2,sticky="NW")
        
        return frame

    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set('AutoUpdate', self.auto.get())      
        config.set('RemoveBackup', self.rmbackup.get())      
        config.set('NoVoices', self.novoices.get())   
        


    #def versionInSettings(self,
    #parent, cmdr,
    #is_beta,version,gridrow):
     #   frame = nb.Frame(parent)
      #  nb.Label(frame, text="Current
      #  version is"+version)
        
    def click_installer(self):
        self.button.grid_remove()
                
        if self.installer():
            self.hyperlink['text'] = "Релиз {}  Установлен, пожалуйста перезагрузите EDMC".format(self.latest.get("tag_name"))     
        else:
            self.hyperlink['text'] = "Релиз {}  Не установлен, ошибка".format(self.latest.get("tag_name"))     
        
        
    def installer(self):
        # need to add some defensive
        # code around this
        tag_name = self.latest.get("tag_name")
        
        debug("Installing {}".format(tag_name))
        
        new_plugin_dir = os.path.join(os.path.dirname(Release.plugin_dir),"EDMC-Triumvirate-{}".format(tag_name))
        
        debug("Checking for pre-existence")
        if os.path.isdir(new_plugin_dir):
            error("Download already exists: {}".format(new_plugin_dir))
            plug.show_error("Triumvirate upgrade failed")
            return False
                
        try:
            debug("Downloading new version")
            download = requests.get("https://github.com/VAKazakov/EDMC-Triumvirate/archive/{}.zip".format(tag_name), stream=True)
            try:
                z = zipfile.ZipFile(io.BytesIO(download.content))
                z.extractall(os.path.dirname(Release.plugin_dir))
            except:
                z = zipfile.ZipFile(io.StringIO.StringIO(download.content))
                z.extractall(os.path.dirname(Release.plugin_dir))
        except:
            error("Download failed: {}".format(new_plugin_dir))
            plug.show_error("Triumvirate upgrade failed")
            return False
        
        #If we got this far then we
        #have a new plugin so any
        #failures and we will need to
        #delete it
        
        debug("disable the current plugin")
        try:
            os.rename(Release.plugin_dir,str("{}.disabled".format(Release.plugin_dir)))
            debug("Renamed {} to {}".format(Release.plugin_dir,"{}.disabled".format(Release.plugin_dir)))
        except:
            error("Upgrade failed reverting: {}".format(new_plugin_dir))
            plug.show_error("Canonn upgrade failed")
            shutil.rmtree(new_plugin_dir)
            return False
        
        
        if self.rmbackup.get() == 0:
            config.set('Canonn:RemoveBackup',"{}.disabled".format(Release.plugin_dir))
            
        debug("Upgrade complete")    
            
        Release.plugin_dir = new_plugin_dir
        self.installed = True
        
        return True
        
    @classmethod            
    def get_auto(cls):
        return tk.IntVar(value=config.getint("AutoUpdate")).get()
        
    @classmethod    
    def plugin_start(cls,plugin_dir):
        cls.plugin_dir = plugin_dir







