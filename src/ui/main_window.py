import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES
from config import THEME_MODE, THEME_COLOR, WINDOW_GEOMETRY, WINDOW_TITLE
from tkinter import filedialog
from tkinter import messagebox
from cryptography.hazmat.primitives import serialization
import os
import struct

ctk.set_appearance_mode(THEME_MODE)
ctk.set_default_color_theme(THEME_COLOR)

class DnDCTkWindow(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

class MainWindow(DnDCTkWindow):
    def __init__(self, key_manager, crypto_service):
        super().__init__()
        
        self.key_manager = key_manager
        self.crypto_service = crypto_service
        
        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_GEOMETRY)
        
        self.enc_file_path = None
        self.dec_file_path = None
        self.is_logged_in = False
        
        self._build_login_screen()

    # --- LOGIN ---
    def _build_login_screen(self):
        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        self.title_label = ctk.CTkLabel(self.login_frame, text="Cryptyko Login", font=("Roboto", 24, "bold"))
        self.title_label.pack(pady=(20, 10), padx=40)
        
        self.password_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Master Passwort", show="*")
        self.password_entry.pack(pady=10, padx=40, fill="x")
        
        self.login_button = ctk.CTkButton(self.login_frame, text="Entsperren", command=self._handle_login)
        self.login_button.pack(pady=(10, 20), padx=40)

    def _handle_login(self):
        password = self.password_entry.get()
        if not password:
            messagebox.showwarning("Eingabe fehlt", "Bitte gib ein Passwort ein.")
            return
            
        try:
            self.key_manager.setup_vault(password)
            self.private_key = self.key_manager.load_private_key(password)
            self.is_logged_in = True
            self.login_frame.destroy() 
            self._build_main_workspace() 
        except Exception as e:
            messagebox.showerror("Fehler", f"Login fehlgeschlagen: {e}")

    # --- WORKSPACE ---
    def _build_main_workspace(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_enc_file = self.tabview.add("Datei Verschlüsseln")
        self.tab_enc_text = self.tabview.add("Text Verschlüsseln")
        self.tab_dec_file = self.tabview.add("Datei Entschlüsseln")
        self.tab_settings = self.tabview.add("Schlüssel-Manager")

        self._build_tab_enc_file()
        self._build_tab_enc_text()
        self._build_tab_dec_file()
        self._build_tab_settings()
        
        self._update_all_dropdowns()

    def _update_all_dropdowns(self):
        """Aktualisiert alle Empfänger-Dropdowns mit den gespeicherten Kontakten."""
        contacts = ["Mein Tresor (Ich selbst)"] + self.key_manager.list_contacts()
        
        if hasattr(self, 'recipient_dropdown'):
            self.recipient_dropdown.configure(values=contacts)
            self.recipient_dropdown.set(contacts[0])
            
        if hasattr(self, 'text_recipient_dropdown'):
            self.text_recipient_dropdown.configure(values=contacts)
            self.text_recipient_dropdown.set(contacts[0])

    def _build_tab_settings(self):
        ctk.CTkLabel(self.tab_settings, text="Eigener Schlüssel", font=("Roboto", 16, "bold")).pack(pady=(10,0))
        ctk.CTkButton(self.tab_settings, text="Meinen Public Key exportieren", command=self._export_public_key).pack(pady=10)

        ctk.CTkFrame(self.tab_settings, height=2, fg_color=("gray70", "gray30")).pack(fill="x", pady=20, padx=40)

        ctk.CTkLabel(self.tab_settings, text="Kontakt hinzufügen", font=("Roboto", 16, "bold")).pack(pady=(0,10))
        
        self.contact_name_entry = ctk.CTkEntry(self.tab_settings, placeholder_text="Name des Kontakts (z.B. Finn)")
        self.contact_name_entry.pack(pady=5, padx=100, fill="x")
        
        ctk.CTkButton(self.tab_settings, text="Public Key importieren", 
                      fg_color="green", hover_color="darkgreen",
                      command=self._import_contact_action).pack(pady=10)

    def _import_contact_action(self):
        name = self.contact_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Fehler", "Bitte gib einen Namen für den Kontakt ein.")
            return
            
        path = filedialog.askopenfilename(filetypes=[("Public Key", "*.pem"), ("All Files", "*.*")])
        if path:
            try:
                self.key_manager.import_contact_key(name, path)
                messagebox.showinfo("Erfolg", f"Schlüssel für '{name}' wurde gespeichert.")
                self.contact_name_entry.delete(0, 'end')
                self._update_all_dropdowns()
            except Exception as e:
                messagebox.showerror("Fehler", f"Ungültiger Schlüssel: {e}")

    def _export_public_key(self):
        public_key = self.private_key.public_key()
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        save_path = filedialog.asksaveasfilename(defaultextension=".pem", title="Public Key speichern")
        if save_path:
            with open(save_path, "wb") as f:
                f.write(pem)
            messagebox.showinfo("Export erfolgreich", "Dein Public Key wurde gespeichert.")

    def _build_tab_enc_file(self):
        self.enc_meta_frame = ctk.CTkFrame(self.tab_enc_file, fg_color="transparent")
        self.enc_meta_frame.pack(pady=10, fill="x", padx=40)
        
        ctk.CTkLabel(self.enc_meta_frame, text="An:").grid(row=0, column=1, padx=(10, 5))
        self.recipient_dropdown = ctk.CTkOptionMenu(self.enc_meta_frame, values=["Mein Tresor (Ich selbst)"])
        self.recipient_dropdown.grid(row=0, column=2, padx=5, sticky="ew")
        
        self.enc_meta_frame.grid_columnconfigure(0, weight=1)
        self.enc_meta_frame.grid_columnconfigure(2, weight=1)

        self.enc_drop_btn = ctk.CTkButton(self.tab_enc_file, text="Datei ablegen oder klicken", height=120, border_width=2, command=self._select_enc_file)
        self.enc_drop_btn.pack(pady=10, fill="x", padx=40)
        self.enc_drop_btn.drop_target_register(DND_FILES)
        self.enc_drop_btn.dnd_bind('<<Drop>>', self._on_enc_file_drop)

        self.enc_file_btn = ctk.CTkButton(self.tab_enc_file, text="Verschlüsseln & Speichern", command=self._encrypt_file_action)
        self.enc_file_btn.pack(pady=10)

    def _select_enc_file(self):
        fp = filedialog.askopenfilename()
        if fp: self._set_enc_file(fp)

    def _on_enc_file_drop(self, event):
        self._set_enc_file(event.data.strip('{}'))

    def _set_enc_file(self, path):
        self.enc_file_path = path
        self.enc_drop_btn.configure(text=f"Ausgewählt: {os.path.basename(path)}")

    def _encrypt_file_action(self):
        if not self.enc_file_path: return
        with open(self.enc_file_path, "rb") as f: data = f.read()
        self._process_encryption(data, os.path.basename(self.enc_file_path))

    def _build_tab_enc_text(self):
        self.enc_meta_frame_txt = ctk.CTkFrame(self.tab_enc_text, fg_color="transparent")
        self.enc_meta_frame_txt.pack(pady=5, fill="x", padx=40)
        
        ctk.CTkLabel(self.enc_meta_frame_txt, text="An:").grid(row=0, column=1, padx=(10, 5))
        self.text_recipient_dropdown = ctk.CTkOptionMenu(self.enc_meta_frame_txt, values=["Mein Tresor (Ich selbst)"])
        self.text_recipient_dropdown.grid(row=0, column=2, padx=5, sticky="ew")
        
        self.enc_meta_frame_txt.grid_columnconfigure(0, weight=1)
        self.enc_meta_frame_txt.grid_columnconfigure(2, weight=1)
        
        self.enc_textbox = ctk.CTkTextbox(self.tab_enc_text, height=100)
        self.enc_textbox.pack(pady=10, fill="x", padx=40)
        
        self.enc_text_btn = ctk.CTkButton(self.tab_enc_text, text="Text Verschlüsseln", command=self._encrypt_text_action)
        self.enc_text_btn.pack(pady=10)

    def _encrypt_text_action(self):
        txt = self.enc_textbox.get("0.0", "end-1c").strip()
        if txt: self._process_encryption(txt.encode(), "nachricht.txt", is_text=True)

    def _process_encryption(self, raw_data, filename, is_text=False):
        
        recipient = self.recipient_dropdown.get() if not is_text else self.text_recipient_dropdown.get()
        
        fn_b, r_b = filename.encode(), recipient.encode()
        header = struct.pack('>I', len(fn_b)) + fn_b + \
                struct.pack('>I', len(r_b)) + r_b
        
        payload = header + raw_data

        try:
            target_public_key = self.key_manager.get_public_key_for_contact(recipient)
            
            encrypted = self.crypto_service.encrypt_payload(payload, target_public_key)
            save_path = filedialog.asksaveasfilename(defaultextension=".enc")
            
            if save_path:
                with open(save_path, "wb") as f: f.write(encrypted)
                messagebox.showinfo("Erfolg", f"Datei für '{recipient}' verschlüsselt!")
        except Exception as e:
            messagebox.showerror("Fehler", f"Verschlüsselung fehlgeschlagen:\n{e}")

    def _build_tab_dec_file(self):
        self.dec_drop_btn = ctk.CTkButton(self.tab_dec_file, text="Verschlüsselte Datei ablegen", height=150, command=self._select_dec_file)
        self.dec_drop_btn.pack(pady=20, fill="x", padx=40)
        self.dec_drop_btn.drop_target_register(DND_FILES)
        self.dec_drop_btn.dnd_bind('<<Drop>>', self._on_dec_file_drop)
        self.dec_file_btn = ctk.CTkButton(self.tab_dec_file, text="Entschlüsseln", command=self._decrypt_action)
        self.dec_file_btn.pack(pady=10)

    def _select_dec_file(self):
        fp = filedialog.askopenfilename(filetypes=[("Encrypted", "*.enc")])
        if fp: self._set_dec_file(fp)

    def _on_dec_file_drop(self, event):
        self._set_dec_file(event.data.strip('{}'))

    def _set_dec_file(self, path):
        self.dec_file_path = path
        self.dec_drop_btn.configure(text=f"Geladen: {os.path.basename(path)}")

    def _decrypt_action(self):
        if not self.dec_file_path: return
        try:
            with open(self.dec_file_path, "rb") as f: enc_data = f.read()
            raw = self.crypto_service.decrypt_payload(enc_data, self.private_key)
            
            ptr = 0
            def get_next_str(data, current_ptr):
                length = struct.unpack('>I', data[current_ptr:current_ptr+4])[0]
                content = data[current_ptr+4 : current_ptr+4+length].decode()
                return content, current_ptr + 4 + length

            fn, ptr = get_next_str(raw, ptr)
            recipient, ptr = get_next_str(raw, ptr)
            actual_data = raw[ptr:]

            save_path = filedialog.asksaveasfilename(initialfile=fn)
            if save_path:
                with open(save_path, "wb") as f: f.write(actual_data)
                
                self.dec_file_path = None
                self.dec_drop_btn.configure(text="Verschlüsselte Datei ablegen")
                messagebox.showinfo("Erfolg", f"Datei entschlüsselt!\n\nFür: {recipient}")
        except Exception as e:
            messagebox.showerror("Fehler", "Entschlüsselung fehlgeschlagen. Falscher Key?")