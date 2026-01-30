import os
import threading
from datetime import datetime
from dotenv import load_dotenv
import customtkinter as ctk
from google import genai
from google.genai import types
from pymongo import MongoClient, errors
import certifi

# --- CONFIGURAÇÃO INICIAL ---
load_dotenv()
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class BOPMBackend:
    def __init__(self):
        # 1. Configuração Gemini
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

        # 2. Configuração MongoDB
        self.mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.db_client = None
        self.collection = None
        self.conectar_mongo()

    def conectar_mongo(self):
        try:
            self.db_client = MongoClient(
                self.mongo_uri, 
                serverSelectionTimeoutMS=5000,
                tlsCAFile=certifi.where() 
            )
            # Testa conexão
            self.db_client.server_info()
            self.db = self.db_client["bopm_db"]
            self.collection = self.db["ocorrencias"]
            print("[DB] Conectado ao MongoDB com sucesso.")
        except errors.ServerSelectionTimeoutError as e:
            print(f"[DB] ERRO DE CONEXÃO: {e}")
            self.collection = None

    def salvar_bopm_db(self, dados_inputs, texto_final):
        if self.collection is None:
            return False, "Sem conexão com Banco de Dados."
        
        try:
            # Estrutura do Documento
            documento = {
                "numero_bopm": dados_inputs['numero'], # Chave principal
                "infrator": dados_inputs['infrator'],
                "natureza": dados_inputs['natureza'],
                "equipe": {
                    "motorista": dados_inputs['motorista'],
                    "encarregado": dados_inputs['encarregado'],
                    "aux1": dados_inputs['aux1'],
                    "aux2": dados_inputs['aux2']
                },
                "detalhes": {
                    "material": dados_inputs['material'],
                    "procedimentos": dados_inputs['procedimentos'],
                    "assinatura": dados_inputs['assinatura']
                },
                "rascunho_original": dados_inputs['rascunho'],
                "texto_final": texto_final, # Salva o texto editado da direita
                "data_atualizacao": datetime.now()
            }

            # Upsert: Se existe o número, atualiza. Se não, cria.
            self.collection.update_one(
                {"numero_bopm": dados_inputs['numero']},
                {"$set": documento},
                upsert=True
            )
            return True, "BOPM Salvo com Sucesso!"
        except Exception as e:
            return False, f"Erro ao salvar: {str(e)}"

    def buscar_bopm_db(self, numero_bopm):
        if self.collection is None:
            return None, "Sem conexão com Banco."
        
        doc = self.collection.find_one({"numero_bopm": numero_bopm})
        if doc:
            return doc, "Encontrado."
        return None, "BOPM não encontrado."

    def gerar_texto_ia(self, relato_bruto, natureza):
        if not self.client:
            return "[ERRO] API Key não configurada."

        prompt = (
            f"Atue como um Policial Militar (P2). "
            f"Reescreva o rascunho abaixo transformando-o em um texto formal, técnico, coeso e impessoal "
            f"para um Boletim de Ocorrência (BOPM). "
            f"Mantenha ESTRITAMENTE todos os fatos, nomes, quantidades, placas e horários citados.\n\n"
            f"Natureza: {natureza}\n"
            f"Rascunho: {relato_bruto}\n\n"
            f"Saída (Apenas o texto reescrito):"
        )

        modelos = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
        config = types.GenerateContentConfig(temperature=0.2, candidate_count=1)

        for modelo in modelos:
            try:
                response = self.client.models.generate_content(
                    model=modelo, contents=prompt, config=config
                )
                return response.text
            except Exception:
                continue
        
        return f"[FALHA] IA Indisponível.\nTexto Original:\n{relato_bruto}"

    def formatar_bopm_template(self, dados, relato_final):
        # Gera o Markdown para exibição
        bloco_equipe = f"**Equipe Policial**\n**Motorista:** {dados['motorista']}\n**Encarregado:** {dados['encarregado']}"
        if dados['aux1'].strip(): bloco_equipe += f"\n**1º Auxiliar:** {dados['aux1']}"
        if dados['aux2'].strip(): bloco_equipe += f"\n**2º Auxiliar:** {dados['aux2']}"

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
        
        self.title("Gerador de BOPM - 3° BPM (+MongoDB)")
        self.geometry("1200x850")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- FRAME ESQUERDO (Inputs) ---
        self.frame_inputs = ctk.CTkScrollableFrame(self, label_text="Dados da Ocorrência")
        self.frame_inputs.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.frame_inputs.grid_columnconfigure(0, weight=1)

        # == ÁREA DE PESQUISA ==
        self.frame_search = ctk.CTkFrame(self.frame_inputs, fg_color="transparent")
        self.frame_search.pack(fill="x", pady=(0, 15))
        
        self.entry_search = ctk.CTkEntry(self.frame_search, placeholder_text="Buscar Nº BOPM")
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_search = ctk.CTkButton(self.frame_search, text="🔍 Buscar", width=60, command=self.buscar_no_banco)
        self.btn_search.pack(side="right")
        # ======================

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

        self.btn_gerar = ctk.CTkButton(self.frame_inputs, text="GERAR / ATUALIZAR TEMPLATE", command=self.iniciar_geracao, height=40, fg_color="green")
        self.btn_gerar.pack(fill="x", pady=20)

        # --- FRAME DIREITO (Output) ---
        self.frame_output = ctk.CTkFrame(self)
        self.frame_output.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.frame_output.grid_rowconfigure(1, weight=1)
        self.frame_output.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.frame_output, text="BOPM Final (Editável)", font=("Arial", 16, "bold")).grid(row=0, column=0, pady=10)
        
        self.txt_output = ctk.CTkTextbox(self.frame_output, font=("Consolas", 12))
        self.txt_output.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Botões de Ação
        self.frame_actions = ctk.CTkFrame(self.frame_output, fg_color="transparent")
        self.frame_actions.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        self.btn_salvar_db = ctk.CTkButton(self.frame_actions, text="💾 Salvar no Banco", command=self.salvar_tudo, fg_color="#D35400") # Laranja
        self.btn_salvar_db.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_copiar = ctk.CTkButton(self.frame_actions, text="📋 Copiar", command=self.copiar_texto)
        self.btn_copiar.pack(side="right", expand=True, fill="x", padx=(5, 0))
        
        self.lbl_status = ctk.CTkLabel(self.frame_output, text="", text_color="gray", font=("Arial", 10))
        self.lbl_status.grid(row=3, column=0, pady=(0, 5))

    def criar_input(self, texto, nome_var):
        ctk.CTkLabel(self.frame_inputs, text=texto, anchor="w").pack(fill="x", pady=(5, 0))
        entry = ctk.CTkEntry(self.frame_inputs)
        entry.pack(fill="x", pady=(0, 5))
        setattr(self, nome_var, entry)

    # --- LÓGICA DE COLETA DE DADOS ---
    def coletar_inputs(self):
        return {
            'numero': self.entry_num.get(),
            'infrator': self.entry_infrator.get(),
            'natureza': self.entry_natureza.get(),
            'motorista': self.entry_mot.get(),
            'encarregado': self.entry_enc.get(),
            'aux1': self.entry_aux1.get(),
            'aux2': self.entry_aux2.get(),
            'material': self.entry_mat.get(),
            'procedimentos': self.entry_proc.get(),
            'assinatura': self.entry_ass.get(),
            'rascunho': self.txt_relato.get("1.0", "end-1c")
        }

    def popular_inputs(self, doc):
        """Preenche a tela com dados do Banco"""
        self.entry_num.delete(0, "end"); self.entry_num.insert(0, doc.get('numero_bopm', ''))
        self.entry_infrator.delete(0, "end"); self.entry_infrator.insert(0, doc.get('infrator', ''))
        self.entry_natureza.delete(0, "end"); self.entry_natureza.insert(0, doc.get('natureza', ''))
        
        eq = doc.get('equipe', {})
        self.entry_mot.delete(0, "end"); self.entry_mot.insert(0, eq.get('motorista', ''))
        self.entry_enc.delete(0, "end"); self.entry_enc.insert(0, eq.get('encarregado', ''))
        self.entry_aux1.delete(0, "end"); self.entry_aux1.insert(0, eq.get('aux1', ''))
        self.entry_aux2.delete(0, "end"); self.entry_aux2.insert(0, eq.get('aux2', ''))
        
        det = doc.get('detalhes', {})
        self.entry_mat.delete(0, "end"); self.entry_mat.insert(0, det.get('material', ''))
        self.entry_proc.delete(0, "end"); self.entry_proc.insert(0, det.get('procedimentos', ''))
        self.entry_ass.delete(0, "end"); self.entry_ass.insert(0, det.get('assinatura', ''))

        self.txt_relato.delete("1.0", "end")
        self.txt_relato.insert("1.0", doc.get('rascunho_original', ''))

        # Popula o lado direito com o texto salvo anteriormente (se existir)
        # Se não tiver 'texto_final' salvo, gera o template com o rascunho
        texto_salvo = doc.get('texto_final', '')
        self.txt_output.delete("1.0", "end")
        self.txt_output.insert("1.0", texto_salvo)
        
        self.lbl_status.configure(text=f"BOPM #{doc.get('numero_bopm')} carregado do banco.", text_color="#58D68D")

    # --- ACTIONS ---
    def buscar_no_banco(self):
        numero = self.entry_search.get().strip()
        if not numero:
            return
        
        doc, msg = self.backend.buscar_bopm_db(numero)
        if doc:
            self.popular_inputs(doc)
        else:
            self.lbl_status.configure(text=msg, text_color="red")

    def salvar_tudo(self):
        dados = self.coletar_inputs()
        # PEGA O TEXTO DO LADO DIREITO (EDITADO OU NÃO)
        texto_final_atual = self.txt_output.get("1.0", "end-1c")
        
        if not dados['numero']:
            self.lbl_status.configure(text="Erro: Número do BOPM obrigatório para salvar.", text_color="red")
            return

        sucesso, msg = self.backend.salvar_bopm_db(dados, texto_final_atual)
        cor = "#58D68D" if sucesso else "red"
        self.lbl_status.configure(text=msg, text_color=cor)

    def iniciar_geracao(self):
        dados = self.coletar_inputs()
        if not dados['rascunho'].strip():
            self.lbl_status.configure(text="Preencha o rascunho antes de gerar.", text_color="yellow")
            return

        self.btn_gerar.configure(state="disabled", text="Processando IA...")
        threading.Thread(target=self.executar_backend, args=(dados,)).start()

    def executar_backend(self, dados):
        # 1. Gera texto IA
        relato_formal = self.backend.gerar_texto_ia(dados['rascunho'], dados['natureza'])
        
        # 2. Formata Template
        texto_completo = self.backend.formatar_bopm_template(dados, relato_formal)
        
        self.after(0, lambda: self.atualizar_ui_pos_processamento(texto_completo))

    def atualizar_ui_pos_processamento(self, texto):
        self.txt_output.delete("1.0", "end")
        self.txt_output.insert("1.0", texto)
        self.btn_gerar.configure(state="normal", text="GERAR / ATUALIZAR TEMPLATE")
        self.lbl_status.configure(text="Texto gerado pela IA. Revise antes de salvar.", text_color="#3498DB")

    def copiar_texto(self):
        self.clipboard_clear()
        self.clipboard_append(self.txt_output.get("1.0", "end-1c"))
        self.btn_copiar.configure(text="Copiado!", fg_color="gray")
        self.after(2000, lambda: self.btn_copiar.configure(text="📋 Copiar", fg_color="#1f6aa5"))

if __name__ == "__main__":
    app = App()
    app.mainloop()