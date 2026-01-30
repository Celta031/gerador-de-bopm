import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Optional
from user_settings import settings
import sys
import os

class InputFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._create_widgets()
    
    def _create_widgets(self):
        self.label_numero = ctk.CTkLabel(self, text="Número do BOPM:", font=("Segoe UI", 14, "bold"))
        self.label_numero.pack(pady=(10, 5))
        
        self.entry_numero = ctk.CTkEntry(self, width=300, height=35, font=("Segoe UI", 13))
        self.entry_numero.pack(pady=(0, 5))
        
        self.label_validacao_numero = ctk.CTkLabel(self, text="", font=("Segoe UI", 11))
        self.label_validacao_numero.pack()
        
        self.label_rascunho = ctk.CTkLabel(self, text="Rascunho:", font=("Segoe UI", 14, "bold"))
        self.label_rascunho.pack(pady=(15, 5))
        
        self.textbox_rascunho = ctk.CTkTextbox(self, width=500, height=300, wrap="word",
                                                font=(settings.get("appearance", "font_family", "Segoe UI"), 
                                                      settings.get("appearance", "font_size", 13)))
        self.textbox_rascunho.pack(pady=(0, 5), fill="both", expand=True)
        
        self.label_contador = ctk.CTkLabel(self, text="0 caracteres", font=("Segoe UI", 10))
        self.label_contador.pack()
        
        self.label_validacao_rascunho = ctk.CTkLabel(self, text="", font=("Segoe UI", 11))
        self.label_validacao_rascunho.pack()
    
    def get_numero(self) -> str:
        return self.entry_numero.get()
    
    def get_rascunho(self) -> str:
        return self.textbox_rascunho.get("1.0", "end-1c")
    
    def set_numero(self, text: str):
        self.entry_numero.delete(0, "end")
        self.entry_numero.insert(0, text)
    
    def set_rascunho(self, text: str):
        self.textbox_rascunho.delete("1.0", "end")
        self.textbox_rascunho.insert("1.0", text)
    
    def clear_all(self):
        self.entry_numero.delete(0, "end")
        self.textbox_rascunho.delete("1.0", "end")

class OutputFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._create_widgets()
    
    def _create_widgets(self):
        self.label_output = ctk.CTkLabel(self, text="Texto Formal:", font=("Segoe UI", 14, "bold"))
        self.label_output.pack(pady=(10, 5))
        
        self.textbox_output = ctk.CTkTextbox(self, width=500, height=400, wrap="word",
                                              font=(settings.get("appearance", "font_family", "Segoe UI"),
                                                    settings.get("appearance", "font_size", 13)))
        self.textbox_output.pack(pady=(0, 10), fill="both", expand=True)
    
    def get_text(self) -> str:
        return self.textbox_output.get("1.0", "end-1c")
    
    def set_text(self, text: str):
        self.textbox_output.delete("1.0", "end")
        self.textbox_output.insert("1.0", text)
    
    def clear(self):
        self.textbox_output.delete("1.0", "end")

class SearchFrame(ctk.CTkFrame):
    def __init__(self, master, on_search: Callable, on_load: Callable, **kwargs):
        super().__init__(master, **kwargs)
        self.on_search = on_search
        self.on_load = on_load
        self._create_widgets()
    
    def _create_widgets(self):
        search_container = ctk.CTkFrame(self, fg_color="transparent")
        search_container.pack(fill="x", pady=10, padx=10)
        
        self.entry_search = ctk.CTkEntry(search_container, placeholder_text="Buscar BOPM...", 
                                          width=250, height=35, font=("Segoe UI", 13))
        self.entry_search.pack(side="left", padx=(0, 10))
        
        btn_buscar = ctk.CTkButton(search_container, text="🔍 Buscar", width=100, height=35,
                                    font=("Segoe UI", 12), command=self.on_search)
        btn_buscar.pack(side="left", padx=(0, 10))
        
        self.label_status = ctk.CTkLabel(search_container, text="🔴 Offline", 
                                          font=("Segoe UI", 11, "bold"))
        self.label_status.pack(side="left")
        
        self.listbox = ctk.CTkTextbox(self, height=200, font=("Courier New", 11))
        self.listbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def get_search_text(self) -> str:
        return self.entry_search.get()
    
    def set_results(self, results: str):
        self.listbox.delete("1.0", "end")
        self.listbox.insert("1.0", results)
    
    def update_status(self, connected: bool):
        self.label_status.configure(text="🟢 MongoDB" if connected else "🔴 Offline")

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save: Callable):
        super().__init__(parent)
        self.on_save = on_save
        self.title("⚙️ Configurações")
        self.geometry("600x700")
        self.resizable(False, False)
        
        self._create_widgets()
        self.transient(parent)
        self.grab_set()
    
    def _create_widgets(self):
        container = ctk.CTkScrollableFrame(self, width=560, height=600)
        container.pack(padx=20, pady=20, fill="both", expand=True)
        
        ctk.CTkLabel(container, text="Aparência", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 10))
        
        self.theme_var = ctk.StringVar(value=settings.get("appearance", "theme", "dark"))
        ctk.CTkLabel(container, text="Tema:").pack(anchor="w")
        ctk.CTkSegmentedButton(container, values=["light", "dark", "system"], variable=self.theme_var).pack(pady=5, fill="x")
        
        self.color_var = ctk.StringVar(value=settings.get("appearance", "color_theme", "blue"))
        ctk.CTkLabel(container, text="Cor:").pack(anchor="w", pady=(10, 0))
        ctk.CTkSegmentedButton(container, values=["blue", "green", "dark-blue"], variable=self.color_var).pack(pady=5, fill="x")
        
        ctk.CTkLabel(container, text="IA", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(20, 10))
        
        self.model_var = ctk.StringVar(value=settings.get("ai", "model", "gemini-2.0-flash-exp"))
        ctk.CTkLabel(container, text="Modelo:").pack(anchor="w")
        ctk.CTkOptionMenu(container, values=["gemini-2.0-flash-exp", "gemini-2.5-flash-latest", "gemini-1.5-flash"],
                          variable=self.model_var).pack(pady=5, fill="x")
        
        ctk.CTkLabel(container, text="Editor", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(20, 10))
        
        self.auto_save_var = ctk.BooleanVar(value=settings.get("editor", "auto_save", True))
        ctk.CTkCheckBox(container, text="Auto-salvar", variable=self.auto_save_var).pack(anchor="w", pady=5)
        
        ctk.CTkLabel(container, text="Segurança", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(20, 10))
        
        self.encrypt_var = ctk.BooleanVar(value=settings.get("security", "encrypt_sensitive_data", False))
        ctk.CTkCheckBox(container, text="Criptografar dados sensíveis", variable=self.encrypt_var).pack(anchor="w", pady=5)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(btn_frame, text="Salvar", command=self._save_settings, width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancelar", command=self.destroy, width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Restaurar Padrões", command=self._reset_defaults, width=150).pack(side="left", padx=5)
    
    def _save_settings(self):
        settings.set("appearance", "theme", self.theme_var.get())
        settings.set("appearance", "color_theme", self.color_var.get())
        settings.set("ai", "model", self.model_var.get())
        settings.set("editor", "auto_save", self.auto_save_var.get())
        settings.set("security", "encrypt_sensitive_data", self.encrypt_var.get())
        settings.save_settings()
        
        self.destroy()
        messagebox.showinfo("Sucesso", "Configurações salvas! O aplicativo será reiniciado.")
        
        self.master.after(100, self._restart_app)
    
    def _restart_app(self):
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    def _reset_defaults(self):
        if messagebox.askyesno("Confirmar", "Restaurar todas as configurações para os valores padrão?"):
            settings.reset_to_defaults()
            self.destroy()
            messagebox.showinfo("Sucesso", "Configurações restauradas! O aplicativo será reiniciado.")
            self.master.after(100, self._restart_app)
