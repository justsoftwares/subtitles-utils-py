import json
import tkinter as tk
from pathlib import Path
from subtitler.utils import Utils
from tkinter import filedialog, messagebox


class App:
    def __init__(self, root):
        self.root = root
        self.root.title('Choose Dubbers for Actors')

        self.file_path: Path = None
        self.utils: Utils = None

        self.browse: tk.Button = None
        self.frame: tk.Frame = None
        self.select_dubber: tk.Button = None
        self.dubbers_list_var: tk.Variable = tk.Variable(value=[])
        self.dubbers_listbox: tk.Listbox = None
        self.copy_preset_btn: tk.Button = None
        self.actors_listbox: tk.Listbox = None
        self.actors_list_var: tk.Variable = tk.Variable(value=[])
        self.new_dubber_entry: tk.Entry = None
        self.config: dict = {'presets': {}}
        self.setup_ui()

    def setup_ui(self):
        self.config = self.load_config()
        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=10, side=tk.TOP)
        self.frame = frame

        self.browse = tk.Button(frame, text='Select ASS File', command=self.browse_file, width=60)
        self.browse.grid(row=0, column=0, sticky=tk.W, columnspan=4)

        tk.Label(frame, text='Dubber List:').grid(row=1, column=1, sticky='w')
        self.select_dubber = tk.Button(frame, text='Select Dubber', command=self.populate_actors_list)
        self.select_dubber.grid(row=1, column=2, sticky='w')
        self.dubbers_listbox = tk.Listbox(frame, listvariable=self.dubbers_list_var)
        self.dubbers_listbox.grid(row=2, column=1, sticky='w', rowspan=3)
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
        scrollbar.config(command=self.dubbers_listbox.yview)
        scrollbar.grid(row=2, column=0, sticky='ns', rowspan=3)
        self.dubbers_listbox.config(yscrollcommand=scrollbar.set)
        # self.dubbers_listbox.bind('<<ListboxSelect>>', self.selected_dubber)

        tk.Label(frame, text='New Dubber:').grid(row=5, column=1, sticky='w')
        self.new_dubber_entry = tk.Entry(frame)
        self.new_dubber_entry.grid(row=6, column=1, sticky='w')
        (tk.Button(frame, text='Add Dubber', command=self.add_dubber)
         .grid(row=6, column=2, sticky='w'))

        tk.Label(frame, text='Actors for Selected Dubber:').grid(row=1, column=3, sticky='w')
        self.actors_listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, listvariable=self.actors_list_var)
        self.actors_listbox.grid(row=2, column=3, sticky='w', rowspan=3)
        (tk.Button(frame, text='Save actors', command=self.save_dubber_to_file)
         .grid(row=6, column=3, sticky=tk.W))

        tk.Label(frame, text='Copy preset from ASS:').grid(row=7, column=1, sticky='w')
        self.copy_preset_btn = tk.Button(frame, text='Browse', command=self.copy_preset)
        self.copy_preset_btn.grid(row=7, column=2, sticky=tk.S)

        (tk.Button(frame, text='Save ASS', command=self.save_ass, width=60)
         .grid(row=8, column=0, sticky=tk.W, columnspan=4))

        self._set_states('disabled')

    def _set_states(self, state):
        for child in self.frame.winfo_children():
            if isinstance(child,
                          (tk.Button, tk.Checkbutton, tk.Entry, tk.Listbox, tk.Label)) and child is not self.browse:
                child.configure(state=state)

    def copy_preset(self):
        file_path = filedialog.askopenfilename(filetypes=[('ASS files', '*.ass')])
        if file_path:
            self.load_config()
            data = self.config['presets'].get(str(Path(file_path)), None)
            if data is None:
                messagebox.showerror('No preset', 'You are did not saved preset for it')
                return
            all_actors = self.utils.get_actors()
            data['free'] = []
            data['busy'] = []
            for dubber, actors in data.get('dubbers', {}).items():
                data['dubbers'][dubber] = [actor for actor in actors if actor in all_actors]

            self.actors_list_var.set([])
            self.dubbers_list_var.set(list(data.get('dubbers', {}).keys()))
            self.save_preset(data)
            self.set_busy()

    def get_selected_dubber(self):
        data = self.load_preset()
        selected_dubber: tuple = self.dubbers_listbox.curselection()
        if selected_dubber:
            data['selected_dubber'] = self.dubbers_listbox.get(selected_dubber[0])
            self.save_preset(data)
        return data.get('selected_dubber', '')

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[('ASS files', '*.ass')])
        if file_path:
            self.actors_list_var.set([])
            self.dubbers_list_var.set([])
            self.file_path = Path(file_path)
            self._set_states('normal')
            self.utils = Utils(Path(file_path))
            self.load_dubbers_from_file()

    def load_dubbers_from_file(self):
        data = self.load_preset()
        self.dubbers_list_var.set(value=list(data.get('dubbers', {}).keys()))

    def get_free(self):
        self.set_busy()
        data = self.load_preset()
        return data['free']

    def populate_actors_list(self, event=None):
        self.actors_listbox.delete(0, tk.END)
        selected_dubber = self.get_selected_dubber()
        if selected_dubber:
            data = self.load_preset()
            selected = data.get('dubbers', {}).get(selected_dubber, [])
            free = self.get_free()
            self.actors_list_var.set(sorted({*free, *selected}))
            for i, actor in enumerate(self.actors_listbox.get(0, tk.END)):
                if actor in selected:
                    self.actors_listbox.select_set(i)

    def add_dubber(self):
        new_dubber_name = self.new_dubber_entry.get().strip()
        if new_dubber_name:
            self.dubbers_listbox.insert(tk.END, new_dubber_name)
            self.new_dubber_entry.delete(0, tk.END)

    def save_dubber_to_file(self):
        selected_dubber = self.get_selected_dubber()
        if selected_dubber:
            data = self.load_preset()
            selected_actors = [self.actors_listbox.get(i) for i in
                               self.actors_listbox.curselection()]
            data['dubbers'][selected_dubber] = selected_actors
            self.save_preset(data)
            self.set_busy()

    def load_preset(self):
        self.load_config()
        data = {'dubbers': {}, 'free': [], 'busy': [], 'selected_dubber': ''}
        preset = self.config['presets'].get(str(self.file_path), data)
        self.save_preset(preset)
        return preset

    def save_preset(self, data):
        self.load_config()
        self.config['presets'][str(self.file_path)] = data
        self.save_config()

    def set_busy(self):
        data = self.load_preset()
        busy = set()
        for dubber, actors in data.get('dubbers', {}).items():
            for actor in actors:
                busy.add(actor)
        data['busy'] = list(busy)
        data['free'] = [actor for actor in self.utils.get_actors() if actor not in data['busy']]
        self.save_preset(data)

    def save_ass(self):
        file_path = Path(
            filedialog.asksaveasfilename(filetypes=[('ASS files', '*.ass')], initialfile=self.file_path.name,
                                         initialdir=self.file_path.parent)
        )
        if file_path:
            self.utils.output_dir = file_path.parent
            self.utils.output_filename = file_path.name
            data = self.load_preset()
            missed = self.utils.check_actors_coverage(data.get('busy', []))
            if missed:
                msg = ', '.join(missed)
                msg += '\nLeave without dubbers?'
                leave = messagebox.askyesno("You didn't specify these actors:", msg)
                if not leave:
                    return
            self.utils.update_actors(data.get('dubbers', {}))
            self.utils.save()

    def load_config(self):
        config = {'presets': {}}
        data = _read_json('subtitler-gui-config.json')
        if not data:
            _save_json('subtitler-gui-config.json', config)
            data = config
        self.config = data

    def save_config(self):
        _save_json('subtitler-gui-config.json', self.config)


def _read_json(json_file_path: Path | str):
    data = None
    if Path(json_file_path).exists():
        with open(json_file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.decoder.JSONDecodeError:
                pass
    return data


def _save_json(json_file_path: Path | str, data: dict):
    with open(Path(json_file_path), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
