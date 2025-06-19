import customtkinter as ctk
import subprocess
import psutil
from tkinter import messagebox  # <-- Add this line
import tkinter as tk  # <-- Required for messagebox parent

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class NetstatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Netstat Viewer & Process Killer")
        self.geometry("950x600")

        self.tk_root = tk.Tk()  # Hidden root window for messagebox
        self.tk_root.withdraw()  # Don't show the root window

        self.search_entry = ctk.CTkEntry(self, placeholder_text="Search by port, IP, or PID")
        self.search_entry.pack(padx=10, pady=(10, 5), fill="x")
        self.search_entry.bind("<Return>", lambda e: self.search_processes())

        self.search_button = ctk.CTkButton(self, text="Search", command=self.search_processes)
        self.search_button.pack(padx=10, pady=5)

        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.pack(padx=10, pady=(5, 0), fill="x")

        self.headers = ["Proto", "Local Address", "Foreign Address", "State", "PID"]
        self.columns = [20, 30, 30, 15, 10]

        for i, header in enumerate(self.headers):
            label = ctk.CTkLabel(self.header_frame, text=header, width=self.columns[i]*10, anchor="w")
            label.grid(row=0, column=i, padx=3)

        self.table_frame = ctk.CTkScrollableFrame(self)
        self.table_frame.pack(padx=10, pady=(0, 10), fill="both", expand=True)

        self.kill_entry = ctk.CTkEntry(self, placeholder_text="Enter PID to kill")
        self.kill_entry.pack(padx=10, pady=(5, 0))

        self.kill_button = ctk.CTkButton(self, text="Kill PID", command=self.kill_process)
        self.kill_button.pack(padx=10, pady=10)

        self.raw_lines = []
        self.refresh_table()

    def parse_netstat_output(self, raw_output):
        lines = []
        for line in raw_output.splitlines():
            if line.strip().startswith("TCP") or line.strip().startswith("UDP"):
                parts = line.split()
                if len(parts) >= 5:
                    proto = parts[0]
                    local = parts[1]
                    foreign = parts[2]
                    state = parts[3] if proto == "TCP" else ""
                    pid = parts[4] if proto == "TCP" else parts[3]
                    lines.append((proto, local, foreign, state, pid))
        return lines

    def refresh_table(self):
        try:
            output = subprocess.check_output("netstat -ano", shell=True, text=True)
            self.raw_lines = self.parse_netstat_output(output)
            self.display_table(self.raw_lines)
        except Exception as e:
            self.display_table([("Error", str(e), "", "", "")])

    def display_table(self, data):
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        for row_idx, row in enumerate(data):
            for col_idx, value in enumerate(row):
                label = ctk.CTkLabel(self.table_frame, text=value, width=self.columns[col_idx]*10, anchor="w")
                label.grid(row=row_idx, column=col_idx, padx=3, pady=1)

    def search_processes(self):
        keyword = self.search_entry.get().strip()
        if keyword == "":
            self.refresh_table()
        else:
            filtered = [row for row in self.raw_lines if any(keyword in col for col in row)]
            if filtered:
                self.display_table(filtered)
            else:
                self.display_table([("No Match", "", "", "", "")])

    def kill_process(self):
        pid = self.kill_entry.get().strip()
        if not pid.isdigit():
            messagebox.showerror("Invalid PID", f"'{pid}' is not a valid PID.", parent=self.tk_root)
            return
        try:
            proc = psutil.Process(int(pid))
            proc.terminate()
            proc.wait(timeout=3)
            messagebox.showinfo("Success", f"Successfully terminated PID {pid}.", parent=self.tk_root)
            self.refresh_table()
        except psutil.NoSuchProcess:
            messagebox.showwarning("Process Not Found", f"No process with PID {pid} found.", parent=self.tk_root)
        except psutil.TimeoutExpired:
            messagebox.showerror("Timeout", f"Process {pid} could not be terminated in time.", parent=self.tk_root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to kill PID {pid}:\n{e}", parent=self.tk_root)


if __name__ == "__main__":
    app = NetstatApp()
    app.mainloop()
