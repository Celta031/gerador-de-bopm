import logging
import threading
from datetime import datetime
import customtkinter as ctk
from config import Config
from database import BOPMDatabase
from ai_service import GeminiAIService
from validators import BOPMValidator

# --- CONFIGURAÇÃO DE LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bopm_app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÃO INICIAL ---
ctk.set_appearance_mode(Config.APPEARANCE_MODE)
ctk.set_default_color_theme(Config.COLOR_THEME)

class BOPMBackend:
    """Backend refatorado usando módulos especializados"""
    
    def __init__(self):
        logger.info("=== Inicializando Backend BOPM ===")
        
        # Validar configurações
        valido, msg = Config.validate_config()
        if not valido:
            logger.error(f"Configuração inválida: {msg}")
        
        # Inicializar serviços
        self.db = BOPMDatabase()
        self.ai_service = GeminiAIService()
        
        logger.info(f"Banco: {'✓ Conectado' if self.db.conectado else '✗ Desconectado'}")
        logger.info("=== Backend inicializado ===")
    
    def salvar_bopm_db(self, dados_inputs: dict, texto_final: str) -> tuple[bool, str]:
        """
        Salva BOPM no banco (com validação integrada)
        
        Args:
            dados_inputs: Dados coletados dos campos
            texto_final: Texto processado final
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        return self.db.salvar_bopm(dados_inputs, texto_final)
    
    def buscar_bopm_db(self, numero_bopm: str) -> tuple[dict | None, str]:
        """Busca BOPM por número"""
        return self.db.buscar_bopm(numero_bopm)
    
    def listar_bopms_db(self, limite: int = 50) -> tuple[list | None, str]:
        """Lista BOPMs recentes"""
        return self.db.listar_bopms(limite)
    
    def gerar_texto_ia(self, relato_bruto: str, natureza: str) -> str:
        """Gera texto formal via IA (com cache)"""
        return self.ai_service.gerar_texto_formal(relato_bruto, natureza)
    
    def obter_estatisticas(self) -> dict:
        """Retorna estatísticas gerais"""
        return {
            "cache": self.ai_service.obter_estatisticas_cache(),
            "total_bopms": self.db.contar_bopms(),
            "db_conectado": self.db.conectado
        }


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.backend = BOPMBackend()
        
        self.title("Gerador de BOPM - 3° BPM (Refatorado)")
        self.geometry(Config.WINDOW_GEOMETRY)
        
        # Auto-save timer
        self.autosave_timer = None
        self.autosave_ativo = False
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame_inputs = ctk.CTkScrollableFrame(self, label_text="Dados da Ocorrência")
        self.frame_inputs.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.frame_inputs.grid_columnconfigure(0, weight=1)

        self.frame_search = ctk.CTkFrame(self.frame_inputs, fg_color="transparent")
        self.frame_search.pack(fill="x", pady=(0, 15))
        
        self.entry_search = ctk.CTkEntry(self.frame_search, placeholder_text="Buscar Nº BOPM")
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_search = ctk.CTkButton(self.frame_search, text="🔍 Buscar", width=60, command=self.buscar_no_banco)
        self.btn_search.pack(side="right")

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
        
        # Bind para auto-save quando digitar no rascunho
        self.txt_relato.bind("<KeyRelease>", self.iniciar_autosave_timer)

        self.btn_gerar = ctk.CTkButton(
            self.frame_inputs, 
            text="GERAR / ATUALIZAR TEMPLATE", 
            command=self.iniciar_geracao, 
            height=40, 
            fg_color="green"
        )
        self.btn_gerar.pack(fill="x", pady=20)
        
        # === NOVO: Botão de Histórico ===
        self.btn_historico = ctk.CTkButton(
            self.frame_inputs,
            text="📋 Ver Histórico",
            command=self.abrir_historico,
            height=35,
            fg_color="#9B59B6"  # Roxo
        )
        self.btn_historico.pack(fill="x", pady=(0, 10))

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
        
        self.btn_salvar_db = ctk.CTkButton(
            self.frame_actions, 
            text="💾 Salvar no Banco", 
            command=self.salvar_tudo, 
            fg_color="#D35400"
        )
        self.btn_salvar_db.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_copiar = ctk.CTkButton(
            self.frame_actions, 
            text="📋 Copiar", 
            command=self.copiar_texto
        )
        self.btn_copiar.pack(side="right", expand=True, fill="x", padx=(5, 0))
        
        self.lbl_status = ctk.CTkLabel(self.frame_output, text="", text_color="gray", font=("Arial", 10))
        self.lbl_status.grid(row=3, column=0, pady=(0, 5))
        
        logger.info("Interface inicializada")

    def criar_input(self, texto, nome_var):
        ctk.CTkLabel(self.frame_inputs, text=texto, anchor="w").pack(fill="x", pady=(5, 0))
        entry = ctk.CTkEntry(self.frame_inputs)
        entry.pack(fill="x", pady=(0, 5))
        setattr(self, nome_var, entry)
    
    def formatar_bopm_template(self, dados: dict, relato_final: str) -> str:
        """
        Formata o template do BOPM para exibição
        
        Args:
            dados: Dicionário com dados do BOPM
            relato_final: Texto processado pela IA
            
        Returns:
            String formatada em Markdown
        """
        # Gera o Markdown para exibição
        bloco_equipe = f"**Equipe Policial**\n**Motorista:** {dados['motorista']}\n**Encarregado:** {dados['encarregado']}"
        if dados.get('aux1', '').strip(): 
            bloco_equipe += f"\n**1º Auxiliar:** {dados['aux1']}"
        if dados.get('aux2', '').strip(): 
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

**Material Apreendido:** {dados.get('material', 'Nada consta')}

**Procedimentos:** {dados.get('procedimentos', 'Nada consta')}

**Assinatura do Responsável:** {dados.get('assinatura', '')}"""

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
        texto_salvo = doc.get('texto_final', '')
        self.txt_output.delete("1.0", "end")
        self.txt_output.insert("1.0", texto_salvo)
        
        self.lbl_status.configure(
            text=f"✓ BOPM #{doc.get('numero_bopm')} carregado do banco", 
            text_color="#58D68D"
        )
        logger.info(f"BOPM #{doc.get('numero_bopm')} carregado na interface")
    
    # === AUTO-SAVE ===
    def iniciar_autosave_timer(self, event=None):
        """Inicia/reinicia timer de auto-save após digitação"""
        if self.autosave_timer:
            self.after_cancel(self.autosave_timer)
        
        # Agenda auto-save para daqui a 30 segundos
        self.autosave_timer = self.after(Config.AUTOSAVE_INTERVAL_MS, self.executar_autosave)
    
    def executar_autosave(self):
        """Executa auto-save se houver dados mínimos"""
        dados = self.coletar_inputs()
        
        # Verifica se há dados suficientes para salvar
        if not dados['numero'] or not dados['rascunho'].strip():
            logger.debug("Auto-save ignorado: dados insuficientes")
            return
        
        # Validação básica
        valido, msg = BOPMValidator.validar_numero_bopm(dados['numero'])
        if not valido:
            logger.debug(f"Auto-save ignorado: {msg}")
            return
        
        # Tenta salvar
        texto_atual = self.txt_output.get("1.0", "end-1c")
        sucesso, msg = self.backend.salvar_bopm_db(dados, texto_atual)
        
        if sucesso:
            self.lbl_status.configure(text="💾 Auto-save realizado", text_color="gray")
            logger.info(f"Auto-save: BOPM #{dados['numero']}")
        else:
            logger.debug(f"Auto-save falhou: {msg}")

    # --- ACTIONS ---
    def buscar_no_banco(self):
        """Busca BOPM por número"""
        numero = self.entry_search.get().strip()
        if not numero:
            self.lbl_status.configure(text="Digite um número para buscar", text_color="yellow")
            return
        
        logger.info(f"Buscando BOPM #{numero}")
        doc, msg = self.backend.buscar_bopm_db(numero)
        
        if doc:
            self.popular_inputs(doc)
        else:
            self.lbl_status.configure(text=msg, text_color="red")
            logger.warning(msg)
    
    def abrir_historico(self):
        """Abre janela com histórico de BOPMs"""
        logger.info("Abrindo histórico")
        
        # Busca lista de BOPMs
        lista, msg = self.backend.listar_bopms_db(50)
        
        if not lista:
            self.lbl_status.configure(text=msg, text_color="red")
            return
        
        # Cria janela de diálogo
        janela_historico = ctk.CTkToplevel(self)
        janela_historico.title("Histórico de BOPMs")
        janela_historico.geometry("800x600")
        janela_historico.transient(self)
        janela_historico.grab_set()
        
        # Frame principal
        frame = ctk.CTkFrame(janela_historico)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Label titulo
        ctk.CTkLabel(
            frame, 
            text=f"📋 Últimos {len(lista)} BOPMs", 
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        # Scrollable frame com lista
        scroll_frame = ctk.CTkScrollableFrame(frame)
        scroll_frame.pack(fill="both", expand=True, pady=10)
        
        # Cabeçalho
        header = ctk.CTkFrame(scroll_frame, fg_color="#2C3E50")
        header.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(header, text="Número", width=100, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Infrator", width=200, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Natureza", width=200, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header, text="Data", width=150, font=("Arial", 12, "bold")).pack(side="left", padx=5)
        
        # Lista de BOPMs
        for doc in lista:
            item_frame = ctk.CTkFrame(scroll_frame, fg_color="#34495E")
            item_frame.pack(fill="x", pady=2)
            
            numero = doc.get('numero_bopm', 'N/A')
            infrator = doc.get('infrator', 'N/A')
            natureza = doc.get('natureza', 'N/A')
            data = doc.get('data_atualizacao', datetime.now())
            data_str = data.strftime("%d/%m/%Y %H:%M") if isinstance(data, datetime) else str(data)
            
            ctk.CTkLabel(item_frame, text=numero, width=100).pack(side="left", padx=5)
            ctk.CTkLabel(item_frame, text=infrator[:30], width=200, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(item_frame, text=natureza[:30], width=200, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(item_frame, text=data_str, width=150).pack(side="left", padx=5)
            
            # Botão carregar
            btn_carregar = ctk.CTkButton(
                item_frame,
                text="Carregar",
                width=80,
                command=lambda n=numero: self.carregar_da_lista(n, janela_historico)
            )
            btn_carregar.pack(side="right", padx=5)
        
        # Botão fechar
        ctk.CTkButton(
            frame,
            text="Fechar",
            command=janela_historico.destroy,
            fg_color="gray"
        ).pack(pady=10)
    
    def carregar_da_lista(self, numero: str, janela_historico):
        """Carrega BOPM selecionado do histórico"""
        logger.info(f"Carregando BOPM #{numero} do histórico")
        
        doc, msg = self.backend.buscar_bopm_db(numero)
        if doc:
            self.popular_inputs(doc)
            janela_historico.destroy()
        else:
            self.lbl_status.configure(text=msg, text_color="red")

    def salvar_tudo(self):
        """Salva BOPM com validação"""
        dados = self.coletar_inputs()
        texto_final_atual = self.txt_output.get("1.0", "end-1c")
        
        logger.info(f"Tentando salvar BOPM #{dados.get('numero', 'N/A')}")
        
        sucesso, msg = self.backend.salvar_bopm_db(dados, texto_final_atual)
        cor = "#58D68D" if sucesso else "red"
        self.lbl_status.configure(text=msg, text_color=cor)
        
        if sucesso:
            logger.info(f"✓ BOPM #{dados['numero']} salvo")
        else:
            logger.warning(f"✗ Falha ao salvar: {msg}")

    def iniciar_geracao(self):
        """Inicia geração de texto pela IA"""
        dados = self.coletar_inputs()
        
        # Validação do rascunho
        valido, msg = BOPMValidator.validar_rascunho(dados['rascunho'])
        if not valido:
            self.lbl_status.configure(text=msg, text_color="yellow")
            logger.warning(f"Validação falhou: {msg}")
            return

        logger.info("Iniciando geração de texto pela IA")
        self.btn_gerar.configure(state="disabled", text="⏳ Processando IA...")
        threading.Thread(target=self.executar_backend, args=(dados,), daemon=True).start()

    def executar_backend(self, dados):
        """Executa processamento em background"""
        try:
            # 1. Gera texto IA
            relato_formal = self.backend.gerar_texto_ia(dados['rascunho'], dados['natureza'])
            
            # 2. Formata Template
            texto_completo = self.formatar_bopm_template(dados, relato_formal)
            
            self.after(0, lambda: self.atualizar_ui_pos_processamento(texto_completo))
        except Exception as e:
            logger.error(f"Erro no processamento: {str(e)}")
            self.after(0, lambda: self.lbl_status.configure(
                text=f"Erro: {str(e)}", 
                text_color="red"
            ))
            self.after(0, lambda: self.btn_gerar.configure(
                state="normal", 
                text="GERAR / ATUALIZAR TEMPLATE"
            ))

    def atualizar_ui_pos_processamento(self, texto):
        """Atualiza UI após processamento"""
        self.txt_output.delete("1.0", "end")
        self.txt_output.insert("1.0", texto)
        self.btn_gerar.configure(state="normal", text="GERAR / ATUALIZAR TEMPLATE")
        self.lbl_status.configure(
            text="✓ Texto gerado pela IA. Revise antes de salvar.", 
            text_color="#3498DB"
        )
        logger.info("Texto gerado e exibido na interface")

    def copiar_texto(self):
        """Copia texto para área de transferência"""
        self.clipboard_clear()
        self.clipboard_append(self.txt_output.get("1.0", "end-1c"))
        self.btn_copiar.configure(text="✓ Copiado!", fg_color="gray")
        logger.info("Texto copiado para área de transferência")
        self.after(2000, lambda: self.btn_copiar.configure(
            text="📋 Copiar", 
            fg_color="#1f6aa5"
        ))

if __name__ == "__main__":
    logger.info("=== Iniciando Aplicação BOPM ===")
    app = App()
    
    # Cleanup ao fechar
    def ao_fechar():
        logger.info("Encerrando aplicação...")
        if app.backend.db:
            app.backend.db.fechar_conexao()
        app.destroy()
    
    app.protocol("WM_DELETE_WINDOW", ao_fechar)
    app.mainloop()
    logger.info("=== Aplicação encerrada ===")