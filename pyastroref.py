import threading
import time
import os
import adsabs

import gi

gi.require_version("Gtk", "3.0")
gi.require_version('EvinceDocument', '3.0')
gi.require_version('EvinceView', '3.0')

from gi.repository import GLib, Gtk, GObject, Gio

from gi.repository import EvinceDocument
from gi.repository import EvinceView

ADSABS_SOURCE=1
LOCAL_SOURCE=2

class MyWindow(Gtk.Window):
    def __init__(self):
        self.settings = {}
        self.pages = {}

        Gtk.Window.__init__(self, title="pyAstroRef")
        EvinceDocument.init()

        self.search = Gtk.Entry()
        self.search.set_width_chars(100)

        self.button_search_source = Gtk.Switch()

        self.button_search = Gtk.Button(label="Search")
        self.button_search.connect("clicked", self.on_click_search)
        self.button_search.set_can_default(True)
        self.set_default(self.button_search)


        self.button_opt = Gtk.Button(label="Options")
        self.button_opt.connect("clicked", self.on_click_load_options)

        self.notebook = Gtk.Notebook()

        self.grid = Gtk.Grid()
        self.add(self.grid)

        self.grid.add(self.button_opt)

        self.grid.attach_next_to(self.search,self.button_opt,
                            Gtk.PositionType.RIGHT,1,1)

        self.grid.attach_next_to(self.button_search_source,self.search,
                            Gtk.PositionType.RIGHT,1,1)

        self.grid.attach_next_to(self.button_search,self.button_search_source,
                            Gtk.PositionType.RIGHT,1,1)

        self.grid.attach_next_to(self.notebook,self.button_opt,
                             Gtk.PositionType.BOTTOM,5,5)

        self.search.set_hexpand(True)

        self.notebook.set_hexpand(True)
        self.notebook.set_vexpand(True)
        self.notebook.set_tab_pos(Gtk.PositionType.LEFT)

        # self.main_page = Gtk.Box()
        # self.main_page.set_border_width(10)
        # self.main_page.add(Gtk.Label(label="Main"))
        # self.notebook.append_page(self.main_page, Gtk.Label(label="Home"))
        # self.notebook.set_tab_reorderable(self.main_page, True)

        #self.new_page('1804.06669')

        self.button_search_source.set_active(False)
        self.settings['search'] = LOCAL_SOURCE # default
        self.button_search_source.connect("notify::active", self.on_switch_activated)


    def on_switch_activated(self, switch, gparam):
        if switch.get_active():
            self.settings['search'] = ADSABS_SOURCE
        else:
            self.settings['search'] = LOCAL_SOURCE

    def on_click_load_options(self, button):
        win = OptionsMenu()
        win.show_all()

    def on_click_search(self, button):
        search_source = self.settings['search']
        query = self.search.get_text()

        if len(query) == 0:
            return

        self.new_page(query)


    def new_page(self,filename):

        if filename in self.pages:
            if self.pages[filename].page_num >= 0:
                self.notebook.set_current_page(self.pages[filename].page_num)
                return
        
        self.pages[filename] = pdfPage(self.notebook,'/data/Insync/refs/papers/'+filename+'.pdf')

        page = self.pages[filename]
        #print(page, page.filename)
        index = self.notebook.append_page(page.add_page(),page.make_header())
        page.page_num = index
        self.notebook.set_tab_reorderable(page.page, True)
        self.notebook.show_all()


class pdfPage(object):
    def __init__(self, notebook, filename):
        self._filename = filename
        self.filename = 'file://'+filename
        self.doc = EvinceDocument.Document.factory_get_document(self.filename)

        self.arixv = None
        self.page = None
        self.notebook = notebook
        self.page_num = -1


    def add_page(self):

        page = Gtk.Box()
        page.set_border_width(10)
        page.pack_start(
                self.show_pdf(),
                True,True,0
            )
        self.page = page
        return page

    def make_header(self):
        header = Gtk.HBox()
        title_label = self.name()
        image = Gtk.Image()
        image.set_from_icon_name('gtk-close', Gtk.IconSize.BUTTON)
        close_button = Gtk.Button()
        close_button.set_image(image)
        close_button.set_relief(Gtk.ReliefStyle.NONE)
        close_button.connect('clicked', self.on_tab_close)
        header.pack_start(title_label,
                          expand=True, fill=True, padding=0)
        header.pack_end(close_button,
                        expand=False, fill=False, padding=1)
        header.show_all()

        return header

    def on_tab_close(self, button):
        self.notebook.remove_page(self.page_num)
        self.page_num = -1


    def show_pdf(self):
       scroll = Gtk.ScrolledWindow()
       view = EvinceView.View()
       model = EvinceView.DocumentModel()
       model.set_document(self.doc)
       view.set_model(model)
       scroll.add(view)
       return scroll  

    def name(self):
        return Gtk.Label(label=os.path.basename(self.filename))

    def arixv_num(self):
        page = self.doc.get_page(0)
        text = self.doc.get_text(page)

        for i in text.split('\n'):
            if 'arXiv:' in i :
                self.arixv = i.split()[0][len('arXiv:'):]

    def get_details(self):
        if self.arixv is None:
            self.arixv_num()

        


class OptionsMenu(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Options")

        grid = Gtk.Grid()
        self.add(grid)

        self.ads_entry = Gtk.Entry()
        self.ads_entry.set_width_chars(50)
        self.ads_entry.set_text(adsabs.load_adskey())

        self.orcid_entry = Gtk.Entry()
        self.orcid_entry.set_text(adsabs.load_orcidkey())
        self.orcid_entry.set_width_chars(50)

        self.folder_entry = Gtk.Button(label="Choose Folder")
        self.folder_entry.connect("clicked", self.on_file_clicked)

        ads_label = Gtk.Label(label='ADSABS ID')
        orcid_label = Gtk.Label(label='ORCID ID')
        file_label = Gtk.Label(label='Save folder')

        save_button_ads = Gtk.Button(label="Save")
        save_button_ads.connect("clicked", self.save_ads)

        save_button_orcid = Gtk.Button(label="Save")
        save_button_orcid.connect("clicked", self.save_orcid)

        grid.add(ads_label)
        grid.attach_next_to(self.ads_entry,ads_label,
                            Gtk.PositionType.RIGHT,1,1)
        grid.attach_next_to(save_button_ads,self.ads_entry,
                            Gtk.PositionType.RIGHT,1,1)        

        grid.attach_next_to(orcid_label,ads_label,
                            Gtk.PositionType.BOTTOM,1,1)
        grid.attach_next_to(self.orcid_entry,orcid_label,
                            Gtk.PositionType.RIGHT,1,1)
        grid.attach_next_to(save_button_orcid,self.orcid_entry,
                            Gtk.PositionType.RIGHT,1,1)  

        grid.attach_next_to(file_label,orcid_label,
                            Gtk.PositionType.BOTTOM,1,1)
        grid.attach_next_to(self.folder_entry,file_label,
                            Gtk.PositionType.RIGHT,1,1)        

    def save_ads(self, button):
        value = self.ads_entry.get_text()
        adsabs.save_adskey(value)

    def save_orcid(self, button):
        value = self.orcid_entry.get_text()
        adsabs.save_orcidkey(value)    



    def on_file_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Please choose a file", parent=self, action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            widget.set_label(dialog.get_filename())
            
        dialog.destroy()

if __name__ == "__main__":
    win = MyWindow()
    win.connect("destroy", Gtk.main_quit)
    win.set_hide_titlebar_when_maximized(False)
    win.maximize()
    win.show_all()
    Gtk.main()