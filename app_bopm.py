import logging
import threading
from datetime import datetime
from tkinter import messagebox
import customtkinter as ctk
from config import Config
from database import BOPMDatabase
from ai_service import GeminiAIService
from validators import BOPMValidator
from user_settings import settings
from security import security
from ui_components import InputFrame, OutputFrame, SearchFrame, SettingsDialog

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

ctk.set_appearance_mode(settings.get("appearance", "theme", "dark"))
ctk.set_default_color_theme(settings.get("appearance", "color_theme", "blue"))

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
    
    def buscar_avancada(self, filtros: dict, limite: int = 50) -> tuple[list | None, str]:
        """Busca avançada com filtros"""
        try:
            query = {}
            if filtros.get('numero'):
                query['numero_bopm'] = {'$regex': filtros['numero'], '$options': 'i'}
            if filtros.get('infrator'):
                query['infrator'] = {'$regex': filtros['infrator'], '$options': 'i'}
            if filtros.get('natureza'):
                query['natureza'] = {'$regex': filtros['natureza'], '$options': 'i'}
            if filtros.get('motorista'):
                query['equipe.motorista'] = {'$regex': filtros['motorista'], '$options': 'i'}
            
            cursor = self.db.collection.find(query).sort('data_atualizacao', -1).limit(limite)
            resultados = list(cursor)
            return resultados, f"{len(resultados)} resultados"
        except Exception as e:
            return None, f"Erro na busca: {str(e)}"
    
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
        
        self.title("Gerador de BOPM - 3° BPM")
        self.geometry(Config.WINDOW_GEOMETRY)
        
        self.autosave_timer = None
        self.validation_labels = {}
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container_left = ctk.CTkScrollableFrame(self, label_text="Dados da Ocorrência")
        container_left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        frame_busca = ctk.CTkFrame(container_left, fg_color="transparent")
        frame_busca.pack(fill="x", pady=(0, 15))
        
        self.lbl_conexao = ctk.CTkLabel(frame_busca, text="🔴 Offline", font=("Arial", 10), width=90)
        self.lbl_conexao.pack(side="left", padx=(0, 5))
        
        self.entry_search = ctk.CTkEntry(frame_busca, placeholder_text="Número BOPM")
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(frame_busca, text="🔍 Buscar", width=80, command=self.buscar_no_banco).pack(side="right")

        self.criar_input("Número do BOPM", "entry_num", container_left)
        self.criar_input("Nome do Infrator", "entry_infrator", container_left)
        self.criar_input("Natureza dos Fatos", "entry_natureza", container_left)
        
        ctk.CTkLabel(container_left, text="--- Equipe Policial ---", text_color="gray").pack(pady=5)
        self.criar_input("Motorista", "entry_mot", container_left)
        self.criar_input("Encarregado", "entry_enc", container_left)
        self.criar_input("1º Auxiliar", "entry_aux1", container_left)
        self.criar_input("2º Auxiliar", "entry_aux2", container_left)

        ctk.CTkLabel(container_left, text="--- Detalhes Finais ---", text_color="gray").pack(pady=5)
        self.criar_input("Material Apreendido", "entry_mat", container_left)
        self.criar_input("Procedimentos", "entry_proc", container_left)
        self.criar_input("Assinatura", "entry_ass", container_left)

        frame_rascunho = ctk.CTkFrame(container_left, fg_color="transparent")
        frame_rascunho.pack(fill="x", pady=(10, 0))
        ctk.CTkLabel(frame_rascunho, text="Rascunho do Relato:", anchor="w").pack(side="left")
        self.lbl_contador = ctk.CTkLabel(frame_rascunho, text="0 caracteres", anchor="e", text_color="gray")
        self.lbl_contador.pack(side="right")
        
        self.txt_relato = ctk.CTkTextbox(container_left, height=150)
        self.txt_relato.pack(fill="x", pady=5)
        self.txt_relato.bind("<KeyRelease>", self.atualizar_contador_e_autosave)

        action_frame = ctk.CTkFrame(container_left, fg_color="transparent")
        action_frame.pack(fill="x", pady=20)
        
        self.btn_gerar = ctk.CTkButton(action_frame, text="🤖 Gerar IA (Ctrl+G)", command=self.iniciar_geracao, height=40, fg_color="green")
        self.btn_gerar.pack(fill="x", pady=(0, 5))
        
        btn_row = ctk.CTkFrame(action_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=5)
        
        ctk.CTkButton(btn_row, text="📋 Histórico", command=self.abrir_historico, height=35, fg_color="#9B59B6").pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(btn_row, text="⚙️ Config", command=self.abrir_configuracoes, height=35, fg_color="#34495E").pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        ctk.CTkButton(action_frame, text="⌨️ Atalhos (F1)", command=self.mostrar_atalhos, height=30, fg_color="#3498DB").pack(fill="x", pady=(5, 0))

        container_right = ctk.CTkFrame(self)
        container_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        container_right.grid_rowconfigure(1, weight=1)
        container_right.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(container_right, text="BOPM Final (Editável)", font=("Arial", 16, "bold")).grid(row=0, column=0, pady=10)
        
        self.txt_output = ctk.CTkTextbox(container_right, font=("Consolas", 12))
        self.txt_output.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        actions = ctk.CTkFrame(container_right, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkButton(actions, text="💾 Salvar (Ctrl+S)", command=self.salvar_tudo, fg_color="#D35400").pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(actions, text="🧹 Limpar", command=self.limpar_output, fg_color="gray", width=80).pack(side="right", padx=(5, 0))
        ctk.CTkButton(actions, text="📋 Copiar", command=self.copiar_texto).pack(side="right", fill="x", padx=(5, 0), expand=True)
        
        self.lbl_status = ctk.CTkLabel(container_right, text="", text_color="gray", font=("Arial", 10))
        self.lbl_status.grid(row=3, column=0, pady=(0, 5))
        
        self.configurar_atalhos()
        self.atualizar_status_conexao()
        self.carregar_ultimos_bopms()
        
        logger.info("Interface inicializada")
    
    def configurar_atalhos(self):
        self.bind("<Control-s>", lambda e: self.salvar_tudo())
        self.bind("<Control-g>", lambda e: self.iniciar_geracao())
        self.bind("<Control-n>", lambda e: self.limpar_campos())
        self.bind("<Control-f>", lambda e: self.entry_search.focus())
        self.bind("<Control-h>", lambda e: self.abrir_busca_avancada())
        self.bind("<Escape>", lambda e: self.limpar_campos())
        self.bind("<F1>", lambda e: self.mostrar_atalhos())
        self.entry_search.bind("<Return>", lambda e: self.buscar_no_banco())

    def atualizar_status_conexao(self):
        if self.backend.db.conectado:
            self.lbl_conexao.configure(text="🟢 MongoDB", text_color="green")
        else:
            self.lbl_conexao.configure(text="🔴 Offline", text_color="red")
    
    def abrir_configuracoes(self):
        SettingsDialog(self, on_save=self.aplicar_configuracoes)
    
    def aplicar_configuracoes(self):
        self.lbl_status.configure(text="⚙️ Configurações salvas", text_color="#3498DB")
    
    def limpar_output(self):
        self.txt_output.delete("1.0", "end")
        self.lbl_status.configure(text="Texto limpo", text_color="gray")
    
    def carregar_ultimos_bopms(self):
        try:
            lista, msg = self.backend.listar_bopms_db(5)
            if lista and len(lista) > 0:
                texto_info = f"ℹ️ Últimos {len(lista)} BOPMs: "
                numeros = [doc.get('numero_bopm', 'N/A') for doc in lista[:3]]
                texto_info += ", ".join(numeros)
                if len(lista) > 3:
                    texto_info += "..."
                self.lbl_status.configure(text=texto_info, text_color="#3498DB")
        except Exception as e:
            logger.debug(f"Erro ao carregar últimos BOPMs: {e}")
    
    def criar_input(self, texto, nome_var, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(5, 0))
        
        label_frame = ctk.CTkFrame(frame, fg_color="transparent")
        label_frame.pack(fill="x")
        ctk.CTkLabel(label_frame, text=texto, anchor="w").pack(side="left")
        
        validation_lbl = ctk.CTkLabel(label_frame, text="", anchor="e", width=20)
        validation_lbl.pack(side="right")
        self.validation_labels[nome_var] = validation_lbl
        
        entry = ctk.CTkEntry(parent)
        entry.pack(fill="x", pady=(0, 5))
        entry.bind("<KeyRelease>", lambda e: self.validar_campo_tempo_real(nome_var))
        setattr(self, nome_var, entry)
    
    def validar_campo_tempo_real(self, nome_campo):
        entry = getattr(self, nome_campo)
        valor = entry.get().strip()
        label = self.validation_labels.get(nome_campo)
        
        if not label:
            return
        
        validacoes = {
            'entry_num': (BOPMValidator.validar_numero_bopm, True),
            'entry_infrator': (lambda v: BOPMValidator.validar_texto(v, 'Infrator', True), True),
            'entry_natureza': (lambda v: BOPMValidator.validar_texto(v, 'Natureza', True), True),
            'entry_mot': (lambda v: BOPMValidator.validar_texto(v, 'Motorista', True), True),
            'entry_enc': (lambda v: BOPMValidator.validar_texto(v, 'Encarregado', True), True),
        }
        
        if nome_campo in validacoes:
            validador, obrigatorio = validacoes[nome_campo]
            if valor or obrigatorio:
                valido, msg = validador(valor)
                if valido:
                    label.configure(text="✓", text_color="green")
                else:
                    label.configure(text="✗", text_color="red")
            else:
                label.configure(text="")
    
    def atualizar_contador_e_autosave(self, event=None):
        texto = self.txt_relato.get("1.0", "end-1c")
        count = len(texto)
        self.lbl_contador.configure(text=f"{count} caracteres")
        
        if count < Config.MIN_RASCUNHO_LENGTH:
            self.lbl_contador.configure(text_color="red")
        elif count > Config.MAX_RASCUNHO_LENGTH:
            self.lbl_contador.configure(text_color="orange")
        else:
            self.lbl_contador.configure(text_color="green")
        
        self.iniciar_autosave_timer(event)
    
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
    def mostrar_atalhos(self):
        janela = ctk.CTkToplevel(self)
        janela.title("⌨️ Atalhos de Teclado")
        janela.geometry("500x500")
        janela.transient(self)
        janela.grab_set()
        
        frame = ctk.CTkFrame(janela)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="⌨️ Atalhos de Teclado", font=("Arial", 18, "bold")).pack(pady=15)
        
        scroll_frame = ctk.CTkScrollableFrame(frame)
        scroll_frame.pack(fill="both", expand=True, pady=10)
        
        atalhos = [
            ("Ctrl+S", "Salvar BOPM no banco"),
            ("Ctrl+G", "Gerar texto com IA"),
            ("Ctrl+N", "Limpar todos os campos"),
            ("Ctrl+F", "Focar no campo de busca"),
            ("Ctrl+H", "Abrir busca avançada"),
            ("Esc", "Limpar campos"),
            ("Enter", "Buscar (quando no campo de busca)"),
            ("F1", "Mostrar esta ajuda")
        ]
        
        for tecla, descricao in atalhos:
            item_frame = ctk.CTkFrame(scroll_frame, fg_color="#34495E")
            item_frame.pack(fill="x", pady=3, padx=5)
            
            ctk.CTkLabel(
                item_frame, 
                text=tecla, 
                font=("Consolas", 13, "bold"),
                width=100,
                anchor="w"
            ).pack(side="left", padx=10, pady=8)
            
            ctk.CTkLabel(
                item_frame, 
                text=descricao,
                anchor="w"
            ).pack(side="left", padx=10, pady=8, fill="x", expand=True)
        
        frame_info = ctk.CTkFrame(frame, fg_color="#2C3E50")
        frame_info.pack(fill="x", pady=10)
        
        info_text = """💡 Dicas:
• Use atalhos para aumentar sua produtividade
• Observe os indicadores ✓/✗ ao preencher campos
• Contador de caracteres indica status do rascunho"""
        
        ctk.CTkLabel(
            frame_info, 
            text=info_text,
            font=("Arial", 10),
            justify="left",
            anchor="w"
        ).pack(padx=15, pady=10)
        
        ctk.CTkButton(
            frame,
            text="Fechar",
            command=janela.destroy,
            fg_color="gray",
            width=150
        ).pack(pady=10)
    
    def limpar_campos(self):
        confirmacao = messagebox.askyesno(
            "Limpar Campos",
            "Deseja realmente limpar todos os campos?",
            parent=self
        )
        if confirmacao:
            self.entry_num.delete(0, "end")
            self.entry_infrator.delete(0, "end")
            self.entry_natureza.delete(0, "end")
            self.entry_mot.delete(0, "end")
            self.entry_enc.delete(0, "end")
            self.entry_aux1.delete(0, "end")
            self.entry_aux2.delete(0, "end")
            self.entry_mat.delete(0, "end")
            self.entry_proc.delete(0, "end")
            self.entry_ass.delete(0, "end")
            self.txt_relato.delete("1.0", "end")
            self.txt_output.delete("1.0", "end")
            self.entry_search.delete(0, "end")
            for label in self.validation_labels.values():
                label.configure(text="")
            self.lbl_contador.configure(text="0 caracteres", text_color="gray")
            self.lbl_status.configure(text="Campos limpos", text_color="gray")
            logger.info("Campos limpos")
    
    def coletar_inputs(self):
        return {
            'numero': security.sanitize_input(self.entry_num.get(), allow_special=False),
            'infrator': security.sanitize_input(self.entry_infrator.get()),
            'natureza': security.sanitize_input(self.entry_natureza.get()),
            'motorista': security.sanitize_input(self.entry_mot.get()),
            'encarregado': security.sanitize_input(self.entry_enc.get()),
            'aux1': security.sanitize_input(self.entry_aux1.get()),
            'aux2': security.sanitize_input(self.entry_aux2.get()),
            'material': security.sanitize_input(self.entry_mat.get()),
            'procedimentos': security.sanitize_input(self.entry_proc.get()),
            'assinatura': security.sanitize_input(self.entry_ass.get()),
            'rascunho': security.sanitize_input(self.txt_relato.get("1.0", "end-1c"))
        }

    def popular_inputs(self, doc):
        """Preenche a tela com dados do Banco"""
        logger.info(f"Populando inputs com BOPM #{doc.get('numero_bopm', 'N/A')}")
        logger.info(f"Infrator no doc: {doc.get('infrator', 'VAZIO')}")
        logger.info(f"Texto_final presente: {bool(doc.get('texto_final', ''))}")
        
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

        texto_salvo = doc.get('texto_final', '')
        self.txt_output.delete("1.0", "end")
        self.txt_output.insert("1.0", texto_salvo)
        
        self.lbl_status.configure(
            text=f"✓ BOPM #{doc.get('numero_bopm')} carregado do banco", 
            text_color="#58D68D"
        )
        logger.info(f"BOPM #{doc.get('numero_bopm')} carregado na interface com sucesso")
    
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
        numero = self.entry_search.get().strip()
        if not numero:
            self.lbl_status.configure(text="Digite um número para buscar", text_color="yellow")
            return
        
        try:
            logger.info(f"Buscando BOPM #{numero}")
            doc, msg = self.backend.buscar_bopm_db(numero)
            
            if doc:
                self.popular_inputs(doc)
            else:
                self.lbl_status.configure(text=msg, text_color="red")
                logger.warning(msg)
        except Exception as e:
            logger.error(f"Erro ao buscar: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao buscar BOPM:\n{str(e)}", parent=self)
            self.lbl_status.configure(text="Erro na busca", text_color="red")
    
    def abrir_busca_avancada(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Busca Avançada")
        janela.geometry("600x400")
        janela.transient(self)
        janela.grab_set()
        
        frame = ctk.CTkFrame(janela)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Busca Avançada", font=("Arial", 16, "bold")).pack(pady=10)
        
        filtros = {}
        
        for campo, label in [("numero", "Número BOPM"), ("infrator", "Infrator"), 
                             ("natureza", "Natureza"), ("motorista", "Motorista")]:
            ctk.CTkLabel(frame, text=label, anchor="w").pack(fill="x", pady=(10, 0))
            entry = ctk.CTkEntry(frame)
            entry.pack(fill="x")
            filtros[campo] = entry
        
        def executar_busca():
            filtros_valores = {k: v.get().strip() for k, v in filtros.items() if v.get().strip()}
            if not filtros_valores:
                messagebox.showwarning("Aviso", "Preencha ao menos um filtro", parent=janela)
                return
            
            resultados, msg = self.backend.buscar_avancada(filtros_valores, 50)
            if resultados:
                janela.destroy()
                self.exibir_resultados_busca(resultados)
            else:
                messagebox.showerror("Erro", msg, parent=janela)
        
        ctk.CTkButton(frame, text="Buscar", command=executar_busca).pack(pady=20)
        ctk.CTkButton(frame, text="Cancelar", command=janela.destroy, fg_color="gray").pack()
    
    def exibir_resultados_busca(self, resultados):
        janela = ctk.CTkToplevel(self)
        janela.title(f"Resultados ({len(resultados)})")
        janela.geometry("800x600")
        janela.transient(self)
        
        frame = ctk.CTkFrame(janela)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text=f"📋 {len(resultados)} resultados encontrados", 
                    font=("Arial", 16, "bold")).pack(pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(frame)
        scroll_frame.pack(fill="both", expand=True, pady=10)
        
        for doc in resultados:
            item_frame = ctk.CTkFrame(scroll_frame, fg_color="#34495E")
            item_frame.pack(fill="x", pady=2)
            
            numero = doc.get('numero_bopm', 'N/A')
            infrator = doc.get('infrator', 'N/A')
            natureza = doc.get('natureza', 'N/A')
            
            ctk.CTkLabel(item_frame, text=numero, width=100).pack(side="left", padx=5)
            ctk.CTkLabel(item_frame, text=infrator[:30], width=200, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(item_frame, text=natureza[:30], width=300, anchor="w").pack(side="left", padx=5)
            
            ctk.CTkButton(item_frame, text="Carregar", width=80,
                         command=lambda n=numero: self.carregar_da_lista(n, janela)).pack(side="right", padx=5)
        
        ctk.CTkButton(frame, text="Fechar", command=janela.destroy, fg_color="gray").pack(pady=10)
    
    def abrir_historico(self):
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
            item_frame.pack(fill="x", pady=2, padx=5)
            
            numero = doc.get('numero_bopm', 'N/A')
            infrator = doc.get('infrator', 'N/A')
            natureza = doc.get('natureza', 'N/A')
            data = doc.get('data_atualizacao', datetime.now())
            
            if isinstance(data, datetime):
                data_str = data.strftime("%d/%m/%Y %H:%M")
            else:
                data_str = str(data)[:16] if data else "N/A"
            
            if infrator and len(infrator) > 25:
                infrator = infrator[:25] + "..."
            if natureza and len(natureza) > 25:
                natureza = natureza[:25] + "..."
            
            ctk.CTkLabel(item_frame, text=numero, width=100, anchor="w").pack(side="left", padx=5, pady=8)
            ctk.CTkLabel(item_frame, text=infrator, width=200, anchor="w").pack(side="left", padx=5, pady=8)
            ctk.CTkLabel(item_frame, text=natureza, width=200, anchor="w").pack(side="left", padx=5, pady=8)
            ctk.CTkLabel(item_frame, text=data_str, width=120, anchor="w").pack(side="left", padx=5, pady=8)
            
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
        try:
            dados = self.coletar_inputs()
            texto_final_atual = self.txt_output.get("1.0", "end-1c")
            
            if not dados['numero']:
                messagebox.showwarning("Aviso", "Número do BOPM é obrigatório", parent=self)
                return
            
            doc_existente, _ = self.backend.buscar_bopm_db(dados['numero'])
            if doc_existente:
                resposta = messagebox.askyesnocancel(
                    "BOPM Existente",
                    f"BOPM #{dados['numero']} já existe.\n\nDeseja sobrescrever?",
                    parent=self
                )
                if resposta is None or resposta is False:
                    self.lbl_status.configure(text="Salvamento cancelado", text_color="gray")
                    return
            
            logger.info(f"Tentando salvar BOPM #{dados.get('numero', 'N/A')}")
            
            sucesso, msg = self.backend.salvar_bopm_db(dados, texto_final_atual)
            cor = "#58D68D" if sucesso else "red"
            self.lbl_status.configure(text=msg, text_color=cor)
            
            if sucesso:
                logger.info(f"✓ BOPM #{dados['numero']} salvo")
                messagebox.showinfo("Sucesso", "BOPM salvo com sucesso!", parent=self)
                self.carregar_ultimos_bopms()
            else:
                logger.warning(f"✗ Falha ao salvar: {msg}")
                messagebox.showerror("Erro", f"Falha ao salvar:\n{msg}", parent=self)
        except Exception as e:
            logger.error(f"Exceção ao salvar: {str(e)}")
            messagebox.showerror("Erro Crítico", f"Erro inesperado:\n{str(e)}", parent=self)
            self.lbl_status.configure(text="Erro ao salvar", text_color="red")

    def iniciar_geracao(self):
        try:
            dados = self.coletar_inputs()
            
            valido, msg = BOPMValidator.validar_rascunho(dados['rascunho'])
            if not valido:
                self.lbl_status.configure(text=msg, text_color="yellow")
                messagebox.showwarning("Validação", msg, parent=self)
                logger.warning(f"Validação falhou: {msg}")
                return

            logger.info("Iniciando geração de texto pela IA")
            self.btn_gerar.configure(state="disabled", text="⏳ Processando IA...")
            threading.Thread(target=self.executar_backend, args=(dados,), daemon=True).start()
        except Exception as e:
            logger.error(f"Erro ao iniciar geração: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao iniciar geração:\n{str(e)}", parent=self)
            self.lbl_status.configure(text="Erro", text_color="red")

    def executar_backend(self, dados):
        try:
            relato_formal = self.backend.gerar_texto_ia(dados['rascunho'], dados['natureza'])
            texto_completo = self.formatar_bopm_template(dados, relato_formal)
            self.after(0, lambda: self.atualizar_ui_pos_processamento(texto_completo))
        except Exception as e:
            logger.error(f"Erro no processamento: {str(e)}", exc_info=True)
            erro_msg = f"Erro ao gerar texto:\n{str(e)}"
            self.after(0, lambda: messagebox.showerror("Erro de Processamento", erro_msg, parent=self))
            self.after(0, lambda: self.lbl_status.configure(text="Erro na IA", text_color="red"))
            self.after(0, lambda: self.btn_gerar.configure(state="normal", text="GERAR / ATUALIZAR TEMPLATE"))

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