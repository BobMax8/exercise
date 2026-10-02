import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk
import csv
import os
import json
import sys
from datetime import datetime, timedelta
import calendar
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

def _get_base_dir():
    """Return folder where external data files should be read/written.
    When running as a frozen executable (PyInstaller onefile), use the
    executable's directory so files placed next to the exe are found.
    Otherwise use the source file directory during development.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)

BASE_DIR = _get_base_dir()
CSV_FILE = os.path.join(BASE_DIR, 'exercises.csv')
SUBTYPES_FILE = os.path.join(BASE_DIR, 'subtypes.json')
GOALS_CSV_FILE = os.path.join(BASE_DIR, 'daily_goals.csv')
TYPES = ["Cardio", "Weights", "Stretch", "Yard", "Sports", "Walk", "Other"]
DEFAULT_SUBTYPES = {
    'Cardio': ['Running', 'Cycling', 'Swimming', 'Rowing', 'HIIT'],
    'Weights': ['Upper Body', 'Lower Body', 'Full Body', 'Strength', 'Hypertrophy'],
    'Stretch': ['Yoga', 'Mobility', 'Flexibility'],
    'Yard': ['Mowing', 'Gardening', 'Leaf Raking'],
    'Sports': ['Basketball', 'Soccer', 'Tennis', 'Baseball'],
    'Walk': ['Work', 'Home'],
    'Other': ['General', 'Custom']
}


def load_subtypes():
    if os.path.exists(SUBTYPES_FILE):
        try:
            with open(SUBTYPES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Ensure all types exist
            for t in TYPES:
                if t not in data:
                    data[t] = DEFAULT_SUBTYPES.get(t, [])
            return data
        except Exception:
            pass
    # create defaults
    try:
        with open(SUBTYPES_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_SUBTYPES, f, indent=2)
    except Exception:
        pass
    return dict(DEFAULT_SUBTYPES)


def save_subtypes(subtypes):
    try:
        with open(SUBTYPES_FILE, 'w', encoding='utf-8') as f:
            json.dump(subtypes, f, indent=2)
    except Exception:
        messagebox.showwarning('Warning', 'Failed to save subtype definitions to file')


SUBTYPES = load_subtypes()


def ensure_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'type', 'subtype', 'duration', 'mhr', 'xhr', 'ahr'])


def ensure_csv_with_subtype():
    # If file missing, create with new header
    if not os.path.exists(CSV_FILE):
        ensure_csv()
        return
    # Check header
    with open(CSV_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'type', 'subtype', 'duration', 'mhr', 'xhr', 'ahr'])
        return
    header = rows[0]
    header_lower = [h.strip().lower() for h in header]
    needs_subtype = 'subtype' not in header_lower
    needs_hr = 'mhr' not in header_lower
    
    if not needs_subtype and not needs_hr:
        return
    
    # Rewrite with new columns
    data_rows = rows[1:]
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'type', 'subtype', 'duration', 'mhr', 'xhr', 'ahr'])
        for r in data_rows:
            if len(r) >= 3:
                date = r[0]
                typ = r[1]
                duration = r[2]
            else:
                date = r[0] if len(r) > 0 else ''
                typ = r[1] if len(r) > 1 else ''
                duration = r[2] if len(r) > 2 else ''
            writer.writerow([date, typ, '', duration, '', '', ''])


def ensure_goals_csv():
    if not os.path.exists(GOALS_CSV_FILE):
        with open(GOALS_CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'exercise_goal', 'overall_goal', 'steps_goal'])


class CalendarPopup(tk.Toplevel):
    def __init__(self, parent, date_var):
        super().__init__(parent)
        self.transient(parent)
        self.title('Select Date')
        self.resizable(False, False)
        self.date_var = date_var
        self.parent = parent

        # Parse current value or use today
        try:
            cur = datetime.strptime(self.date_var.get(), '%Y-%m-%d')
            self.year = cur.year
            self.month = cur.month
        except Exception:
            today = datetime.today()
            self.year = today.year
            self.month = today.month

        self.build_ui()
        self.grab_set()
        self.protocol('WM_DELETE_WINDOW', self.on_close)

    def build_ui(self):
        hdr = ttk.Frame(self, padding=6)
        hdr.grid(row=0, column=0)
        prev = tk.Button(hdr, text='<', width=3, command=self.prev_month, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10))
        prev.grid(row=0, column=0)
        self.title_lbl = ttk.Label(hdr, text='')
        self.title_lbl.grid(row=0, column=1, padx=8)
        nxt = tk.Button(hdr, text='>', width=3, command=self.next_month, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10))
        nxt.grid(row=0, column=2)

        self.cal_frame = ttk.Frame(self, padding=6)
        self.cal_frame.grid(row=1, column=0)
        self.render_calendar()

    def render_calendar(self):
        for w in self.cal_frame.winfo_children():
            w.destroy()
        self.title_lbl.config(text=f'{calendar.month_name[self.month]} {self.year}')
        wkdays = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
        for i, d in enumerate(wkdays):
            ttk.Label(self.cal_frame, text=d).grid(row=0, column=i, padx=3, pady=2)

        m = calendar.monthcalendar(self.year, self.month)
        for r, week in enumerate(m, start=1):
            for c, day in enumerate(week):
                if day == 0:
                    lbl = ttk.Label(self.cal_frame, text='')
                    lbl.grid(row=r, column=c, padx=2, pady=2)
                else:
                    btn = tk.Button(self.cal_frame, text=str(day), width=3,
                                     command=lambda d=day: self.select_day(d), bg='#87CEEB', fg='black', font=('TkDefaultFont', 10))
                    btn.grid(row=r, column=c, padx=2, pady=2)

    def prev_month(self):
        if self.month == 1:
            self.month = 12
            self.year -= 1
        else:
            self.month -= 1
        self.render_calendar()

    def next_month(self):
        if self.month == 12:
            self.month = 1
            self.year += 1
        else:
            self.month += 1
        self.render_calendar()

    def select_day(self, day):
        self.date_var.set(f'{self.year:04d}-{self.month:02d}-{day:02d}')
        self.on_close()

    def on_close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


class ExerciseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Exercise Logger')
        self.resizable(False, False)
        ensure_csv_with_subtype()
        ensure_goals_csv()
        self.chart_type = 'exercise'  # Track which chart to display: 'exercise' or 'goals'
        
        # Configure notebook tab style
        style = ttk.Style()
        style.configure('TNotebook.Tab', padding=[20, 10])
        style.map('TNotebook.Tab',
                  background=[('selected', '#87CEEB'), ('', '#f0f0f0')],
                  foreground=[('selected', 'black'), ('', 'black')])
        
        self.create_widgets()
        self.load_entries()
        self.load_goals_entry()

    def create_widgets(self):
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky='NSEW', padx=5, pady=5)
        
        # Exercise Logger Tab
        self.exercise_frame = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.exercise_frame, text='Exercise Logger')
        self.create_exercise_widgets()
        
        # Daily Goals Tab
        self.goals_frame = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.goals_frame, text='Daily Goals')
        self.create_goals_widgets()
        
        # Chart Tab
        self.chart_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chart_frame, text='Chart')
        self.create_chart_widgets()

    def create_exercise_widgets(self):
        frm = self.exercise_frame

        ttk.Label(frm, text='Date (YYYY-MM-DD):').grid(row=0, column=0, sticky='W')
        self.date_var = tk.StringVar(value=(datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d'))
        self.date_entry = ttk.Entry(frm, textvariable=self.date_var, width=20)
        self.date_entry.grid(row=0, column=1, sticky='W')
        self.date_entry.bind('<Button-1>', self.open_calendar)

        ttk.Label(frm, text='Type:').grid(row=1, column=0, sticky='W', pady=(6,0))
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(frm, textvariable=self.type_var, values=TYPES, state='readonly')
        self.type_combo.grid(row=1, column=1, sticky='W', pady=(6,0))
        self.type_combo.set(TYPES[0])
        self.type_combo.bind('<<ComboboxSelected>>', self.on_type_change)

        ttk.Label(frm, text='Subtype:').grid(row=2, column=0, sticky='W', pady=(6,0))
        self.subtype_var = tk.StringVar()
        subtype_frame = ttk.Frame(frm)
        subtype_frame.grid(row=2, column=1, sticky='W', pady=(6,0))
        self.subtype_combo = ttk.Combobox(subtype_frame, textvariable=self.subtype_var, values=SUBTYPES[TYPES[0]], state='readonly', width=20)
        self.subtype_combo.grid(row=0, column=0, sticky='W')
        self.subtype_combo.set(SUBTYPES[TYPES[0]][0])
        add_btn = tk.Button(subtype_frame, text='+', width=3, command=self.add_subtype, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10))
        add_btn.grid(row=0, column=1, padx=(6,2))
        del_btn = tk.Button(subtype_frame, text='-', width=3, command=self.delete_subtype, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10))
        del_btn.grid(row=0, column=2, padx=(2,0))

        ttk.Label(frm, text='Duration (minutes):').grid(row=3, column=0, sticky='W', pady=(6,0))
        self.duration_var = tk.StringVar()
        self.duration_entry = ttk.Entry(frm, textvariable=self.duration_var, width=10)
        self.duration_entry.grid(row=3, column=1, sticky='W', pady=(6,0))

        # Heart rate fields (only for Cardio)
        self.hr_frame = ttk.Frame(frm)
        self.hr_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0), sticky='W')
        
        ttk.Label(self.hr_frame, text='Minimum Heart Rate (MHR):').grid(row=0, column=0, sticky='W')
        self.mhr_var = tk.StringVar()
        self.mhr_entry = ttk.Entry(self.hr_frame, textvariable=self.mhr_var, width=10)
        self.mhr_entry.grid(row=0, column=1, sticky='W', padx=(6, 0))
        
        ttk.Label(self.hr_frame, text='Maximum Heart Rate (XHR):').grid(row=1, column=0, sticky='W', pady=(6, 0))
        self.xhr_var = tk.StringVar()
        self.xhr_entry = ttk.Entry(self.hr_frame, textvariable=self.xhr_var, width=10)
        self.xhr_entry.grid(row=1, column=1, sticky='W', padx=(6, 0), pady=(6, 0))
        
        ttk.Label(self.hr_frame, text='Average Heart Rate (AHR):').grid(row=2, column=0, sticky='W', pady=(6, 0))
        self.ahr_var = tk.StringVar()
        self.ahr_entry = ttk.Entry(self.hr_frame, textvariable=self.ahr_var, width=10)
        self.ahr_entry.grid(row=2, column=1, sticky='W', padx=(6, 0), pady=(6, 0))

        btn_frame = ttk.Frame(frm, relief='raised', borderwidth=2)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(15, 10), sticky='EW', padx=5)

        save_btn = tk.Button(btn_frame, text='Save', command=self.save_entry, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10), padx=12)
        save_btn.grid(row=0, column=0, padx=8, pady=8)
        clear_btn = tk.Button(btn_frame, text='Clear', command=self.clear_form, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10), padx=12)
        clear_btn.grid(row=0, column=1, padx=8, pady=8)
        
        ttk.Separator(btn_frame, orient='vertical').grid(row=0, column=2, padx=5, sticky='NS')
        
        edit_btn = tk.Button(btn_frame, text='Edit', command=self.edit_selected_exercise, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10), padx=12)
        edit_btn.grid(row=0, column=3, padx=8, pady=8)
        del_btn = tk.Button(btn_frame, text='Delete Selected', command=self.delete_selected, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10), padx=12)
        del_btn.grid(row=0, column=4, padx=8, pady=8)
        
        ttk.Separator(btn_frame, orient='vertical').grid(row=0, column=5, padx=5, sticky='NS')
        
        exit_btn = tk.Button(btn_frame, text='Exit', command=self.exit_app, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10), padx=12)
        exit_btn.grid(row=0, column=6, padx=8, pady=8)

        # Treeview to show saved entries
        cols = ('date', 'type', 'subtype', 'duration', 'mhr', 'xhr', 'ahr')
        self.tree = ttk.Treeview(frm, columns=cols, show='headings', height=8)
        col_widths = {'date': 100, 'type': 80, 'subtype': 100, 'duration': 80, 'mhr': 70, 'xhr': 70, 'ahr': 70}
        for c in cols:
            self.tree.heading(c, text=c.upper())
            self.tree.column(c, anchor='center', width=col_widths.get(c, 100))
        self.tree.grid(row=6, column=0, columnspan=2, pady=(10, 0))

        self.tree.bind('<Double-1>', self.on_tree_double)

    def create_goals_widgets(self):
        frm = self.goals_frame

        ttk.Label(frm, text='Date (YYYY-MM-DD):', font=('TkDefaultFont', 11)).grid(row=0, column=0, sticky='W', pady=10)
        self.goals_date_var = tk.StringVar(value=datetime.today().strftime('%Y-%m-%d'))
        self.goals_date_entry = ttk.Entry(frm, textvariable=self.goals_date_var, width=20)
        self.goals_date_entry.grid(row=0, column=1, sticky='W', pady=10)
        self.goals_date_entry.bind('<Button-1>', self.open_goals_calendar)

        # Exercise Goal
        ttk.Label(frm, text='Exercise Goal:', font=('TkDefaultFont', 11)).grid(row=1, column=0, sticky='W', pady=10)
        self.exercise_goal_var = tk.StringVar(value='No')
        exercise_frame = ttk.Frame(frm)
        exercise_frame.grid(row=1, column=1, sticky='W', pady=10)
        ttk.Radiobutton(exercise_frame, text='Yes', variable=self.exercise_goal_var, value='Yes').pack(side='left', padx=10)
        ttk.Radiobutton(exercise_frame, text='No', variable=self.exercise_goal_var, value='No').pack(side='left', padx=10)

        # Overall Goal
        ttk.Label(frm, text='Overall Goal:', font=('TkDefaultFont', 11)).grid(row=2, column=0, sticky='W', pady=10)
        self.overall_goal_var = tk.StringVar(value='No')
        overall_frame = ttk.Frame(frm)
        overall_frame.grid(row=2, column=1, sticky='W', pady=10)
        ttk.Radiobutton(overall_frame, text='Yes', variable=self.overall_goal_var, value='Yes').pack(side='left', padx=10)
        ttk.Radiobutton(overall_frame, text='No', variable=self.overall_goal_var, value='No').pack(side='left', padx=10)

        # Steps Goal
        ttk.Label(frm, text='Steps Goal:', font=('TkDefaultFont', 11)).grid(row=3, column=0, sticky='W', pady=10)
        self.steps_goal_var = tk.StringVar(value='No')
        steps_frame = ttk.Frame(frm)
        steps_frame.grid(row=3, column=1, sticky='W', pady=10)
        ttk.Radiobutton(steps_frame, text='Yes', variable=self.steps_goal_var, value='Yes').pack(side='left', padx=10)
        ttk.Radiobutton(steps_frame, text='No', variable=self.steps_goal_var, value='No').pack(side='left', padx=10)

        # Button frame
        btn_frame = ttk.Frame(frm, relief='raised', borderwidth=2)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(20, 10), sticky='EW', padx=5)

        save_btn = tk.Button(btn_frame, text='Save', command=self.save_goals_entry, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10), padx=12)
        save_btn.grid(row=0, column=0, padx=8, pady=8)
        clear_btn = tk.Button(btn_frame, text='Clear', command=self.clear_goals_form, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10), padx=12)
        clear_btn.grid(row=0, column=1, padx=8, pady=8)
        
        ttk.Separator(btn_frame, orient='vertical').grid(row=0, column=2, padx=5, sticky='NS')
        
        edit_btn = tk.Button(btn_frame, text='Edit', command=self.edit_selected_goals, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10), padx=12)
        edit_btn.grid(row=0, column=3, padx=8, pady=8)
        
        ttk.Separator(btn_frame, orient='vertical').grid(row=0, column=4, padx=5, sticky='NS')
        
        exit_btn = tk.Button(btn_frame, text='Exit', command=self.exit_app, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10), padx=12)
        exit_btn.grid(row=0, column=5, padx=8, pady=8)

        # Treeview for goals entries
        cols = ('date', 'exercise_goal', 'overall_goal', 'steps_goal')
        self.goals_tree = ttk.Treeview(frm, columns=cols, show='headings', height=10)
        col_widths = {'date': 120, 'exercise_goal': 120, 'overall_goal': 120, 'steps_goal': 120}
        for c in cols:
            self.goals_tree.heading(c, text=c.replace('_', ' ').upper())
            self.goals_tree.column(c, anchor='center', width=col_widths.get(c, 120))
        self.goals_tree.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        self.goals_tree.bind('<Double-1>', self.on_goals_tree_double)

    def on_type_change(self, event=None):
        typ = self.type_var.get()
        choices = SUBTYPES.get(typ, [])
        self.subtype_combo.config(values=choices)
        if choices:
            self.subtype_combo.set(choices[0])
        else:
            self.subtype_combo.set('')
        
        # Show heart rate fields for all types except Weights and Stretch
        if typ not in ['Weights', 'Stretch']:
            self.hr_frame.grid()
        else:
            self.hr_frame.grid_remove()

    def open_goals_calendar(self, event=None):
        x = self.winfo_rootx() + self.goals_date_entry.winfo_rootx()
        y = self.winfo_rooty() + self.goals_date_entry.winfo_rooty() + self.goals_date_entry.winfo_height()
        cal = CalendarPopup(self, self.goals_date_var)
        try:
            cal.geometry(f'+{x}+{y}')
        except Exception:
            pass

    def save_goals_entry(self):
        date = self.goals_date_var.get().strip()
        if not self.validate_date(date):
            messagebox.showerror('Invalid date', 'Please enter date as YYYY-MM-DD')
            return
        
        exercise_goal = self.exercise_goal_var.get()
        overall_goal = self.overall_goal_var.get()
        steps_goal = self.steps_goal_var.get()
        
        ensure_goals_csv()
        
        # Check if entry for this date exists
        rows = []
        found = False
        if os.path.exists(GOALS_CSV_FILE):
            with open(GOALS_CSV_FILE, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for r in reader:
                    if r.get('date') == date:
                        found = True
                        rows.append({'date': date, 'exercise_goal': exercise_goal, 'overall_goal': overall_goal, 'steps_goal': steps_goal})
                    else:
                        rows.append(r)
        
        if not found:
            rows.append({'date': date, 'exercise_goal': exercise_goal, 'overall_goal': overall_goal, 'steps_goal': steps_goal})
        
        # Write back
        with open(GOALS_CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['date', 'exercise_goal', 'overall_goal', 'steps_goal'])
            writer.writeheader()
            writer.writerows(rows)
        
        self.load_goals_entry()
        self.clear_goals_form()
        messagebox.showinfo('Saved', 'Daily goals saved successfully')

    def load_goals_entry(self):
        for row in self.goals_tree.get_children():
            self.goals_tree.delete(row)
        if not os.path.exists(GOALS_CSV_FILE):
            return
        rows = []
        with open(GOALS_CSV_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                date = r.get('date', '')
                exercise_goal = r.get('exercise_goal', '')
                overall_goal = r.get('overall_goal', '')
                steps_goal = r.get('steps_goal', '')
                rows.append((date, exercise_goal, overall_goal, steps_goal))
         
        rows.sort(key=lambda x: x[0], reverse=True)
        for row in rows:
            self.goals_tree.insert('', 'end', values=row)

    def clear_goals_form(self):
        # self.goals_date_var.set(datetime.today().strftime('%Y-%m-%d'))
        self.goals_date_var = tk.StringVar(value=datetime.today().strftime('%Y-%m-%d'))
        self.exercise_goal_var.set('No')
        self.overall_goal_var.set('No')
        self.steps_goal_var.set('No')

    def on_goals_tree_double(self, event):
        sel = self.goals_tree.selection()
        if not sel:
            return
        vals = self.goals_tree.item(sel[0])['values']
        if vals:
            self.goals_date_var.set(vals[0])
            self.exercise_goal_var.set(vals[1])
            self.overall_goal_var.set(vals[2])
            self.steps_goal_var.set(vals[3])

    def create_chart_widgets(self):
        frm = self.chart_frame
        
        btn_frame = ttk.Frame(frm, padding=10)
        btn_frame.pack(side='top', fill='x')
        
        tk.Button(btn_frame, text='Exercise Chart', command=self.show_exercise_chart, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10), padx=12).pack(side='left', padx=5)
        tk.Button(btn_frame, text='Daily Goals Chart', command=self.show_goals_chart, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10), padx=12).pack(side='left', padx=5)
        tk.Button(btn_frame, text='Refresh Chart', command=self.render_chart, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10), padx=12).pack(side='left', padx=5)
        tk.Button(btn_frame, text='Exit', command=self.exit_app, bg='#87CEEB', fg='black', font=('TkDefaultFont', 10), padx=12).pack(side='left', padx=5)
        
        self.canvas_frame = ttk.Frame(frm)
        self.canvas_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        
        self.render_chart()

    def load_exercise_data(self):
        data = defaultdict(lambda: defaultdict(float))
        
        if not os.path.exists(CSV_FILE):
            return data
        
        with open(CSV_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                date_str = row.get('date', '').strip()
                duration_str = row.get('duration', '').strip()
                
                if not date_str or not duration_str:
                    continue
                
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    duration = float(duration_str)
                    year = date.year
                    month = date.month
                    data[year][month] += duration
                except (ValueError, KeyError):
                    continue
        
        return data

    def load_goals_data(self):
        data = {}
        
        if not os.path.exists(GOALS_CSV_FILE):
            return data
        
        with open(GOALS_CSV_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                date_str = row.get('date', '').strip()
                exercise_goal = row.get('exercise_goal', '').strip()
                overall_goal = row.get('overall_goal', '').strip()
                steps_goal = row.get('steps_goal', '').strip()
                
                if not date_str:
                    continue
                
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    yeses = sum([1 for goal in [exercise_goal, overall_goal, steps_goal] if goal == 'Yes'])
                    data[date] = yeses
                except ValueError:
                    continue
        
        return data

    def get_weekly_data(self, daily_data):
        weekly = defaultdict(list)
        
        for date, yeses in daily_data.items():
            monday = date - timedelta(days=date.weekday())
            sunday = monday + timedelta(days=6)
            week_key = (monday, sunday)
            weekly[week_key].append(yeses)
        
        result = {}
        for (monday, sunday), values in sorted(weekly.items()):
            avg = sum(values) / len(values) if values else 0
            result[monday] = {'avg': avg, 'end_date': sunday, 'count': len(values)}
        
        return result

    def show_exercise_chart(self):
        self.chart_type = 'exercise'
        self.render_chart()

    def show_goals_chart(self):
        self.chart_type = 'goals'
        self.render_chart()

    def render_chart(self):
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        
        if self.chart_type == 'goals':
            self.render_goals_chart()
        else:
            self.render_exercise_chart()

    def render_exercise_chart(self):
        data = self.load_exercise_data()
        
        if not data:
            label = ttk.Label(self.canvas_frame, text='No exercise data found. Add exercises to see the chart.')
            label.pack(padx=20, pady=20)
            return
        
        years = sorted(data.keys())
        months = range(1, 13)
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        fig = Figure(figsize=(12, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        x = np.arange(len(months))
        width = 0.8 / len(years) if len(years) > 1 else 0.6
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        for idx, year in enumerate(years):
            minutes_per_month = [data[year].get(month, 0) for month in months]
            offset = (idx - len(years)/2 + 0.5) * width
            ax.bar(x + offset, minutes_per_month, width, label=str(year), 
                   color=colors[idx % len(colors)])
        
        ax.set_xlabel('Month', fontsize=12, fontweight='bold')
        ax.set_ylabel('Total Exercise Minutes', fontsize=12, fontweight='bold')
        ax.set_title('Exercise Minutes Per Month', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(month_names)
        ax.legend(title='Year', fontsize=10)
        ax.grid(axis='y', alpha=0.3)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def render_goals_chart(self):
        data = self.load_goals_data()
        
        if not data:
            label = ttk.Label(self.canvas_frame, text='No daily goals data found. Add goals to see the chart.')
            label.pack(padx=20, pady=20)
            return
        
        weekly_data = self.get_weekly_data(data)
        
        sorted_weeks = sorted(weekly_data.keys())
        week_labels = [d.strftime('%m/%d') + ' - ' + weekly_data[d]['end_date'].strftime('%m/%d') for d in sorted_weeks]
        averages = [weekly_data[d]['avg'] for d in sorted_weeks]
        
        fig = Figure(figsize=(12, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        ax.plot(range(len(sorted_weeks)), averages, marker='o', linewidth=2, markersize=8, color='#1f77b4', markerfacecolor='#ff7f0e')
        ax.fill_between(range(len(sorted_weeks)), averages, alpha=0.3, color='#1f77b4')
        
        ax.set_xlabel('Week (Monday - Sunday)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Average "Yes" Goals per Day', fontsize=12, fontweight='bold')
        ax.set_title('Weekly Average Goals Completion', fontsize=14, fontweight='bold')
        ax.set_xticks(range(0, len(sorted_weeks), max(1, len(sorted_weeks)//10)))
        ax.set_xticklabels([week_labels[i] for i in range(0, len(sorted_weeks), max(1, len(sorted_weeks)//10))], rotation=45, ha='right')
        ax.set_ylim(0, 3.5)
        ax.grid(True, alpha=0.3)
        
        for i, (week, avg) in enumerate(zip(sorted_weeks, averages)):
            ax.text(i, avg + 0.15, f'{avg:.1f}', ha='center', va='bottom', fontweight='bold', fontsize=9)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def add_subtype(self):
        typ = self.type_var.get()
        if typ not in TYPES:
            messagebox.showwarning('Warning', 'Select a valid Type before adding a subtype')
            return
        new = simpledialog.askstring('Add Subtype', f'Enter new subtype for {typ}:', parent=self)
        if not new:
            return
        new = new.strip()
        if not new:
            return
        if new in SUBTYPES.get(typ, []):
            messagebox.showinfo('Info', 'Subtype already exists')
            return
        SUBTYPES.setdefault(typ, []).append(new)
        save_subtypes(SUBTYPES)
        # update combo
        self.subtype_combo.config(values=SUBTYPES.get(typ, []))
        self.subtype_combo.set(new)

    def delete_subtype(self):
        typ = self.type_var.get()
        cur = self.subtype_var.get()
        if not cur:
            messagebox.showwarning('Warning', 'No subtype selected to delete')
            return
        if typ not in TYPES:
            messagebox.showwarning('Warning', 'Select a valid Type')
            return
        if not messagebox.askyesno('Confirm', f'Delete subtype "{cur}" from type {typ}?'):
            return
        if cur in SUBTYPES.get(typ, []):
            SUBTYPES[typ].remove(cur)
            save_subtypes(SUBTYPES)
            # update combo values
            choices = SUBTYPES.get(typ, [])
            self.subtype_combo.config(values=choices)
            if choices:
                self.subtype_combo.set(choices[0])
            else:
                self.subtype_combo.set('')
            # clear that subtype from existing CSV rows where appropriate
            try:
                if os.path.exists(CSV_FILE):
                    with open(CSV_FILE, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                    # rewrite
                    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
                        fieldnames = ['date', 'type', 'subtype', 'duration', 'mhr', 'xhr', 'ahr']
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        for r in rows:
                            if r.get('type') == typ and r.get('subtype') == cur:
                                r['subtype'] = ''
                            writer.writerow({k: r.get(k, '') for k in fieldnames})
                    # reload entries
                    self.load_entries()
            except Exception:
                messagebox.showwarning('Warning', 'Failed to update existing entries in CSV')
        else:
            messagebox.showinfo('Info', 'Subtype not found')

    def open_calendar(self, event=None):
        # Position popup near entry
        x = self.winfo_rootx() + self.date_entry.winfo_rootx()
        y = self.winfo_rooty() + self.date_entry.winfo_rooty() + self.date_entry.winfo_height()
        cal = CalendarPopup(self, self.date_var)
        try:
            cal.geometry(f'+{x}+{y}')
        except Exception:
            pass

    def validate_date(self, s):
        try:
            datetime.strptime(s, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def validate_duration(self, s):
        try:
            v = float(s)
            return v >= 0
        except ValueError:
            return False
    
    def validate_heart_rate(self, s):
        if not s or s.strip() == '':
            return True
        try:
            v = float(s)
            return v >= 0
        except ValueError:
            return False

    def save_entry(self):
        date = self.date_var.get().strip()
        typ = self.type_var.get().strip()
        subtype = self.subtype_var.get().strip()
        duration = self.duration_var.get().strip()
        mhr = self.mhr_var.get().strip()
        xhr = self.xhr_var.get().strip()
        ahr = self.ahr_var.get().strip()

        if not self.validate_date(date):
            messagebox.showerror('Invalid date', 'Please enter date as YYYY-MM-DD')
            return
        if typ not in TYPES:
            messagebox.showerror('Invalid type', 'Please select a valid exercise type')
            return
        if subtype not in SUBTYPES.get(typ, []):
            messagebox.showerror('Invalid subtype', 'Please select a valid subtype for the chosen type')
            return
        if not self.validate_duration(duration):
            messagebox.showerror('Invalid duration', 'Please enter a non-negative number for duration')
            return
        
        if typ not in ['Weights', 'Stretch']:
            if not self.validate_heart_rate(mhr):
                messagebox.showerror('Invalid MHR', 'Please enter a non-negative number for Minimum Heart Rate')
                return
            if not self.validate_heart_rate(xhr):
                messagebox.showerror('Invalid XHR', 'Please enter a non-negative number for Maximum Heart Rate')
                return
            if not self.validate_heart_rate(ahr):
                messagebox.showerror('Invalid AHR', 'Please enter a non-negative number for Average Heart Rate')
                return

        ensure_csv_with_subtype()
        # Always add a new entry (allows multiple workouts per day)
        rows = []
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for r in reader:
                    rows.append(r)
         
        rows.append({'date': date, 'type': typ, 'subtype': subtype, 'duration': duration, 'mhr': mhr, 'xhr': xhr, 'ahr': ahr})
        
        # Write back
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['date', 'type', 'subtype', 'duration', 'mhr', 'xhr', 'ahr'])
            writer.writeheader()
            writer.writerows(rows)

        self.load_entries()
        self.clear_form()
        try:
            self.render_chart()
        except Exception:
            pass
        messagebox.showinfo('Saved', 'Exercise saved successfully')

    def load_entries(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        if not os.path.exists(CSV_FILE):
            return
        rows = []
        with open(CSV_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                date = r.get('date', '')
                typ = r.get('type', '')
                subtype = r.get('subtype', '')
                duration = r.get('duration', '')
                mhr = r.get('mhr', '')
                xhr = r.get('xhr', '')
                ahr = r.get('ahr', '')
                rows.append((date, typ, subtype, duration, mhr, xhr, ahr))
         
        rows.sort(key=lambda x: x[0], reverse=True)
        for row in rows:
            self.tree.insert('', 'end', values=row)

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('No selection', 'Select a row to delete')
            return
        if not messagebox.askyesno('Confirm', 'Delete selected entries?'):
            return
        # Build remaining rows and overwrite CSV
        remaining = []
        for item in self.tree.get_children():
            if item not in sel:
                remaining.append(self.tree.item(item)['values'])
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'type', 'subtype', 'duration', 'mhr', 'xhr', 'ahr'])
            for r in remaining:
                writer.writerow(r)
        self.load_entries()
        try:
            self.render_chart()
        except Exception:
            pass

    def clear_form(self):
        self.date_var.set(datetime.today().strftime('%Y-%m-%d'))
        self.type_combo.set(TYPES[0])
        # update subtype choices
        self.subtype_combo.config(values=SUBTYPES[TYPES[0]])
        self.subtype_combo.set(SUBTYPES[TYPES[0]][0])
        self.duration_var.set('')
        self.mhr_var.set('')
        self.xhr_var.set('')
        self.ahr_var.set('')
        # Show heart rate fields for all types except Weights and Stretch
        if TYPES[0] not in ['Weights', 'Stretch']:
            self.hr_frame.grid()
        else:
            self.hr_frame.grid_remove()

    def on_tree_double(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])['values']
        if vals:
            # vals order: date, type, subtype, duration, mhr, xhr, ahr
            self.date_var.set(vals[0])
            self.type_combo.set(vals[1])
            # update subtype choices to match type then set value
            self.subtype_combo.config(values=SUBTYPES.get(vals[1], []))
            self.subtype_combo.set(vals[2])
            self.duration_var.set(vals[3])
            self.mhr_var.set(vals[4] if len(vals) > 4 else '')
            self.xhr_var.set(vals[5] if len(vals) > 5 else '')
            self.ahr_var.set(vals[6] if len(vals) > 6 else '')
            # Show/hide heart rate fields based on type
            if vals[1] not in ['Weights', 'Stretch']:
                self.hr_frame.grid()
            else:
                self.hr_frame.grid_remove()

    def edit_selected_exercise(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('No selection', 'Select an entry to edit')
            return
        vals = self.tree.item(sel[0])['values']
        if vals:
            self.date_var.set(vals[0])
            self.type_combo.set(vals[1])
            self.subtype_combo.config(values=SUBTYPES.get(vals[1], []))
            self.subtype_combo.set(vals[2])
            self.duration_var.set(vals[3])
            self.mhr_var.set(vals[4] if len(vals) > 4 else '')
            self.xhr_var.set(vals[5] if len(vals) > 5 else '')
            self.ahr_var.set(vals[6] if len(vals) > 6 else '')
            if vals[1] not in ['Weights', 'Stretch']:
                self.hr_frame.grid()
            else:
                self.hr_frame.grid_remove()

    def edit_selected_goals(self):
        sel = self.goals_tree.selection()
        if not sel:
            messagebox.showwarning('No selection', 'Select an entry to edit')
            return
        vals = self.goals_tree.item(sel[0])['values']
        if vals:
            self.goals_date_var.set(vals[0])
            self.exercise_goal_var.set(vals[1])
            self.overall_goal_var.set(vals[2])
            self.steps_goal_var.set(vals[3])

    def exit_app(self):
        self.destroy()


if __name__ == '__main__':
    app = ExerciseApp()
    app.mainloop()
