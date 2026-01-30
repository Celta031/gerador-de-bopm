import os
import threading
from datetime import datetime
from dotenv import load_dotenv
import customtkinter as ctk
from google import genai
from google.genai import types

load_dotenv()
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class BOPMBackend:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    def gerar_texto_ia(self, relato_bruto, natureza):
        if not self.client:
            return "[ERRO] API Key não configurada no arquivo .env"

        prompt = (
            f"Atue como um Policial Militar (P2). "
            f"Reescreva o rascunho abaixo transformando-o em um texto formal, técnico, coeso e impessoal "
            f"para um Boletim de Ocorrência (BOPM). "
            f"Mantenha ESTRITAMENTE todos os fatos, nomes, quantidades, placas e horários citados.\n\n"
            f"Natureza: {natureza}\n"
            f"Rascunho: {relato_bruto}\n\n"
            f"Saída (Apenas o texto reescrito):"
        )

        modelos_para_tentar = [
            'gemini-2.5-flash',          
            'gemini-2.0-flash',          
            'gemini-3-flash-preview',    
            'gemini-2.5-pro'             
        ]

        config = types.GenerateContentConfig(temperature=0.2, candidate_count=1)
        
        erros_log = []

        for modelo in modelos_para_tentar:
            try:
                response = self.client.models.generate_content(
                    model=modelo, contents=prompt, config=config
                )
                return response.text
            except Exception as e:
                erro_limpo = str(e).split('.')[0] 
                erros_log.append(f"{modelo}: {erro_limpo}")
                continue
        
        return f"[FALHA] Nenhum modelo respondeu.\nLogs:\n" + "\n".join(erros_log) + f"\n\nTexto Original:\n{relato_bruto}"

    def formatar_bopm(self, dados, relato_final):
        bloco_equipe = f"**Equipe Policial**\n**Motorista:** {dados['motorista']}\n**Encarregado:** {dados['encarregado']}"

        if dados['aux1'].strip():
            bloco_equipe += f"\n**1º Auxiliar:** {dados['aux1']}"
            
        if dados['aux2'].strip():
            bloco_equipe += f"\n**2º Auxiliar:** {dados['aux2']}"

        return f"""**Título:**
BOPM #{dados['numero']} ({dados['infrator']})

**Modelo:**

**BOLETIM DE OCORRÊNCIA POLICIAL MILITAR – BOPM**

**Data/Hora da Ocorrência:** {datetime.now().strftime("%d/%m/%Y – %H:%M")}

{bloco_equipe}

**Relato dos Fatos:**
{relato_final}

**Natureza dos Fatos:** {dados['natureza']}

**Material Apreendido:** {dados['material']}

**Procedimentos:** {dados['procedimentos']}

**Assinatura do Responsável:** {dados['assinatura']}"""

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.backend = BOPMBackend()
        
        self.title("Gerador de BOPM - 3° BPM")
        self.geometry("1100x800")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame_inputs = ctk.CTkScrollableFrame(self, label_text="Dados da Ocorrência")
        self.frame_inputs.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.frame_inputs.grid_columnconfigure(0, weight=1)

        self.criar_input("Número do BOPM", "entry_num")
        self.criar_input("Nome do Infrator", "entry_infrator")
        self.criar_input("Natureza dos Fatos", "entry_natureza")
        
        ctk.CTkLabel(self.frame_inputs, text="--- Equipe Policial ---", text_color="gray").pack(pady=5)
        self.criar_input("Motorista", "entry_mot")
        self.criar_input("Encarregado", "entry_enc")
        self.criar_input("1º Auxiliar (Opcional)", "entry_aux1")
        self.criar_input("2º Auxiliar (Opcional)", "entry_aux2")

        ctk.CTkLabel(self.frame_inputs, text="--- Detalhes Finais ---", text_color="gray").pack(pady=5)
        self.criar_input("Material Apreendido", "entry_mat")
        self.criar_input("Procedimentos", "entry_proc")
        self.criar_input("Assinatura", "entry_ass")

        ctk.CTkLabel(self.frame_inputs, text="Rascunho do Relato:", anchor="w").pack(fill="x", pady=(10, 0))
        self.txt_relato = ctk.CTkTextbox(self.frame_inputs, height=150)
        self.txt_relato.pack(fill="x", pady=5)

        self.btn_gerar = ctk.CTkButton(self.frame_inputs, text="GERAR BOPM COM I.A.", command=self.iniciar_geracao, height=40, fg_color="green")
        self.btn_gerar.pack(fill="x", pady=20)

        self.frame_output = ctk.CTkFrame(self)
        self.frame_output.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.frame_output, text="BOPM Finalizado (Markdown)", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.txt_output = ctk.CTkTextbox(self.frame_output, font=("Consolas", 12))
        self.txt_output.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.btn_copiar = ctk.CTkButton(self.frame_output, text="Copiar para Área de Transferência", command=self.copiar_texto)
        self.btn_copiar.pack(fill="x", padx=10, pady=10)

    def criar_input(self, texto, nome_var):
        ctk.CTkLabel(self.frame_inputs, text=texto, anchor="w").pack(fill="x", pady=(5, 0))
        entry = ctk.CTkEntry(self.frame_inputs)
        entry.pack(fill="x", pady=(0, 5))
        setattr(self, nome_var, entry)

    def iniciar_geracao(self):
        dados = {
            'numero': self.entry_num.get(),
            'infrator': self.entry_infrator.get(),
            'natureza': self.entry_natureza.get(),
            'motorista': self.entry_mot.get(),
            'encarregado': self.entry_enc.get(),
            'aux1': self.entry_aux1.get(),
            'aux2': self.entry_aux2.get(),
            'material': self.entry_mat.get(),
            'procedimentos': self.entry_proc.get(),
            'assinatura': self.entry_ass.get()
        }
        rascunho = self.txt_relato.get("1.0", "end-1c")

        self.btn_gerar.configure(state="disabled", text="Gerando... Aguarde...")

        threading.Thread(target=self.executar_backend, args=(dados, rascunho)).start()

    def executar_backend(self, dados, rascunho):
        relato_formal = self.backend.gerar_texto_ia(rascunho, dados['natureza'])
        texto_final = self.backend.formatar_bopm(dados, relato_formal)

        self.after(0, lambda: self.atualizar_ui_pos_processamento(texto_final))

    def atualizar_ui_pos_processamento(self, texto):
        self.txt_output.delete("1.0", "end")
        self.txt_output.insert("1.0", texto)
        self.btn_gerar.configure(state="normal", text="GERAR BOPM COM I.A.")
        
        if "[FALHA]" in texto or "[ERRO]" in texto:
             self.txt_output.configure(text_color="#ff5555")
        else:
             self.txt_output.configure(text_color="white")

    def copiar_texto(self):
        self.clipboard_clear()
        self.clipboard_append(self.txt_output.get("1.0", "end-1c"))
        self.btn_copiar.configure(text="Copiado!", fg_color="gray")
        self.after(2000, lambda: self.btn_copiar.configure(text="Copiar para Área de Transferência", fg_color="#1f6aa5"))

if __name__ == "__main__":
    app = App()
    app.mainloop()