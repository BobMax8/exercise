import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk
import csv
import os
import json
from datetime import datetime
import calendar

CSV_FILE = os.path.join(os.path.dirname(__file__), 'exercises.csv')
SUBTYPES_FILE = os.path.join(os.path.dirname(__file__), 'subtypes.json')
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
        prev = ttk.Button(hdr, text='<', width=3, command=self.prev_month)
        prev.grid(row=0, column=0)
        self.title_lbl = ttk.Label(hdr, text='')
        self.title_lbl.grid(row=0, column=1, padx=8)
        nxt = ttk.Button(hdr, text='>', width=3, command=self.next_month)
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
                    btn = ttk.Button(self.cal_frame, text=str(day), width=3,
                                     command=lambda d=day: self.select_day(d))
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
        self.create_widgets()
        ensure_csv_with_subtype()
        self.load_entries()

    def create_widgets(self):
        frm = ttk.Frame(self, padding=12)
        frm.grid(row=0, column=0, sticky='NSEW')

        ttk.Label(frm, text='Date (YYYY-MM-DD):').grid(row=0, column=0, sticky='W')
        self.date_var = tk.StringVar(value=datetime.today().strftime('%Y-%m-%d'))
        self.date_entry = ttk.Entry(frm, textvariable=self.date_var, width=20)
        self.date_entry.grid(row=0, column=1, sticky='W')
        # Open calendar when clicking the date field
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
        add_btn = ttk.Button(subtype_frame, text='+', width=3, command=self.add_subtype)
        add_btn.grid(row=0, column=1, padx=(6,2))
        del_btn = ttk.Button(subtype_frame, text='-', width=3, command=self.delete_subtype)
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

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(10, 0))

        save_btn = ttk.Button(btn_frame, text='Save', command=self.save_entry)
        save_btn.grid(row=0, column=0, padx=4)
        clear_btn = ttk.Button(btn_frame, text='Clear', command=self.clear_form)
        clear_btn.grid(row=0, column=1, padx=4)
        del_btn = ttk.Button(btn_frame, text='Delete Selected', command=self.delete_selected)
        del_btn.grid(row=0, column=2, padx=4)

        # Treeview to show saved entries
        cols = ('date', 'type', 'subtype', 'duration', 'mhr', 'xhr', 'ahr')
        self.tree = ttk.Treeview(frm, columns=cols, show='headings', height=8)
        col_widths = {'date': 100, 'type': 80, 'subtype': 100, 'duration': 80, 'mhr': 70, 'xhr': 70, 'ahr': 70}
        for c in cols:
            self.tree.heading(c, text=c.upper())
            self.tree.column(c, anchor='center', width=col_widths.get(c, 100))
        self.tree.grid(row=6, column=0, columnspan=2, pady=(10, 0))

        note = ttk.Label(frm, text='Date format: YYYY-MM-DD. Double-click an entry to load it for editing.', foreground='gray')
        note.grid(row=7, column=0, columnspan=2, pady=(6,0))

        self.tree.bind('<Double-1>', self.on_tree_double)

    def on_type_change(self, event=None):
        typ = self.type_var.get()
        choices = SUBTYPES.get(typ, [])
        self.subtype_combo.config(values=choices)
        if choices:
            self.subtype_combo.set(choices[0])
        else:
            self.subtype_combo.set('')
        
        # Show heart rate fields only for Cardio
        if typ == 'Cardio':
            self.hr_frame.grid()
        else:
            self.hr_frame.grid_remove()

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
        
        if typ == 'Cardio':
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
        # Append new row
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([date, typ, subtype, duration, mhr, xhr, ahr])

        self.load_entries()
        self.clear_form()
        messagebox.showinfo('Saved', 'Exercise saved successfully')

    def load_entries(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        if not os.path.exists(CSV_FILE):
            return
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
                self.tree.insert('', 'end', values=(date, typ, subtype, duration, mhr, xhr, ahr))

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
        # Show heart rate fields for default type (Cardio)
        if TYPES[0] == 'Cardio':
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
            if vals[1] == 'Cardio':
                self.hr_frame.grid()
            else:
                self.hr_frame.grid_remove()


if __name__ == '__main__':
    app = ExerciseApp()
    app.mainloop()
