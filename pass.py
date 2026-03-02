import sys, secrets, string, sqlite3, base64, os, time, json, uuid
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from pynput import keyboard

# --- SİSTEME ÖZEL ŞİFRELEME ---
def get_system_key():
    hwid = str(uuid.getnode())
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b'\xaf\x12\x88\xcc', iterations=50000)
    return base64.urlsafe_b64encode(kdf.derive(hwid.encode()))

SYS_FERNET = Fernet(get_system_key())
CACHE_FILE = ".system_cache"

class SecurityManager:
    @staticmethod
    def log_attempt(success):
        count = 0
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "rb") as f:
                    data = json.loads(SYS_FERNET.decrypt(f.read()).decode())
                    count = data["count"]
            except: pass
        new_data = {"count": 0 if success else count + 1, "last_attempt": time.time()}
        with open(CACHE_FILE, "wb") as f: f.write(SYS_FERNET.encrypt(json.dumps(new_data).encode()))

    @staticmethod
    def get_lock_time():
        if not os.path.exists(CACHE_FILE): return 0
        try:
            with open(CACHE_FILE, "rb") as f:
                data = json.loads(SYS_FERNET.decrypt(f.read()).decode())
                penalty = {3:60, 4:300, 5:1200}.get(data["count"], 1800 if data["count"] > 5 else 0)
                return max(0, penalty - (time.time() - data["last_attempt"]))
        except: return 0

# --- KRİPTO ÇEKİRDEĞİ ---
class VaultCore:
    def __init__(self, master_pw):
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b'\x12\xab\xed\xfe', iterations=100000)
        self.key = base64.urlsafe_b64encode(kdf.derive(master_pw.encode()))
        self.fernet = Fernet(self.key)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect("vault_ultra.db") as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS meta (check_str BLOB)")
            conn.execute("CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, site BLOB, email BLOB, password BLOB)")
            if not conn.execute("SELECT check_str FROM meta").fetchone():
                conn.execute("INSERT INTO meta VALUES (?)", (self.fernet.encrypt(b"VALID"),))

    def is_valid(self):
        try:
            with sqlite3.connect("vault_ultra.db") as conn:
                check = conn.execute("SELECT check_str FROM meta").fetchone()[0]
                return self.fernet.decrypt(check) == b"VALID"
        except: return False

# --- ANA ARAYÜZ ---
class MintVaultApp(QWidget):
    def __init__(self):
        super().__init__()
        self.vault = None
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setFixedSize(420, 580)
        self.setStyleSheet("background-color: #1a1b26; color: #a9b1d6; font-family: 'Ubuntu';")
        self.main_layout = QVBoxLayout()
        
        self.stack = QStackedWidget()
        self.login_page = QWidget()
        self.vault_page = QWidget()
        
        self.setup_login_page()
        self.setup_vault_page()
        
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.vault_page)
        
        self.main_layout.addWidget(self.stack)
        self.setLayout(self.main_layout)

    def setup_login_page(self):
        layout = QVBoxLayout(self.login_page)
        label = QLabel("🔐 MASTER KEY"); label.setStyleSheet("font-size: 20px; color: #7aa2f7;")
        label.setAlignment(Qt.AlignCenter)
        
        self.mkey_input = QLineEdit(); self.mkey_input.setEchoMode(QLineEdit.Password)
        self.mkey_input.setPlaceholderText("Şifrenizi yazın ve Enter'a basın...")
        self.mkey_input.returnPressed.connect(self.login) # ENTER DESTEĞİ
        
        btn = QPushButton("GİRİŞ YAP (Enter)")
        btn.clicked.connect(self.login)
        layout.addStretch(); layout.addWidget(label); layout.addWidget(self.mkey_input); layout.addWidget(btn); layout.addStretch()

    def setup_vault_page(self):
        layout = QVBoxLayout(self.vault_page)
        self.tabs = QTabWidget()
        
        # Sekme 1: Ekleme
        self.add_tab = QWidget(); add_layout = QVBoxLayout(self.add_tab)
        self.site_in = QLineEdit(); self.site_in.setPlaceholderText("Site Adı")
        self.mail_in = QLineEdit(); self.mail_in.setPlaceholderText("E-posta")
        self.pass_in = QLineEdit(); self.pass_in.setPlaceholderText("Şifre")
        
        # Giriş alanlarında Enter'a basınca kaydetme
        self.site_in.returnPressed.connect(self.save_data)
        self.mail_in.returnPressed.connect(self.save_data)
        self.pass_in.returnPressed.connect(self.save_data)
        
        gen_btn = QPushButton("🎲 Rastgele Şifre Üret")
        gen_btn.clicked.connect(lambda: self.pass_in.setText(secrets.token_urlsafe(16)))
        
        save_btn = QPushButton("💾 KAYDET (Enter)")
        save_btn.setStyleSheet("background-color: #9ece6a; color: #1a1b26; font-weight: bold; padding: 10px;")
        save_btn.clicked.connect(self.save_data)
        
        add_layout.addWidget(QLabel("Yeni Hesap Bilgileri:")); add_layout.addWidget(self.site_in)
        add_layout.addWidget(self.mail_in); add_layout.addWidget(self.pass_in)
        add_layout.addWidget(gen_btn); add_layout.addWidget(save_btn); add_layout.addStretch()
        
        # Sekme 2: Liste
        self.list_tab = QWidget(); list_layout = QVBoxLayout(self.list_tab)
        self.table = QTableWidget(0, 2); self.table.setHorizontalHeaderLabels(["Site", "E-posta"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemDoubleClicked.connect(self.copy_password)
        
        del_btn = QPushButton("🗑️ SEÇİLİ KAYDI SİL")
        del_btn.setStyleSheet("background-color: #f7768e; color: #1a1b26; margin-top: 5px;")
        del_btn.clicked.connect(self.delete_entry)
        
        list_layout.addWidget(QLabel("Kopyalamak için Çift Tıkla, Silmek için Seç ve Butona Bas:"))
        list_layout.addWidget(self.table); list_layout.addWidget(del_btn)
        
        self.tabs.addTab(self.add_tab, "➕ Ekle")
        self.tabs.addTab(self.list_tab, "📂 Listele")
        layout.addWidget(self.tabs)
        
        exit_btn = QPushButton("SİSTEMİ TAMAMEN KAPAT")
        exit_btn.clicked.connect(sys.exit)
        layout.addWidget(exit_btn)

    def login(self):
        wait = SecurityManager.get_lock_time()
        if wait > 0:
            QMessageBox.warning(self, "Kilitli", f"{int(wait)} saniye beklemelisiniz.")
            return
            
        temp_vault = VaultCore(self.mkey_input.text())
        if temp_vault.is_valid():
            self.vault = temp_vault
            SecurityManager.log_attempt(True)
            self.load_list()
            self.stack.setCurrentIndex(1)
        else:
            SecurityManager.log_attempt(False)
            QMessageBox.critical(self, "Hata", "Master Key Yanlış!")

    def save_data(self):
        site, mail, pw = self.site_in.text(), self.mail_in.text(), self.pass_in.text()
        if not site or not pw: return
        with sqlite3.connect("vault_ultra.db") as conn:
            conn.execute("INSERT INTO accounts (site, email, password) VALUES (?, ?, ?)", 
                (self.vault.fernet.encrypt(site.encode()),
                 self.vault.fernet.encrypt(mail.encode()),
                 self.vault.fernet.encrypt(pw.encode())))
        self.site_in.clear(); self.mail_in.clear(); self.pass_in.clear()
        self.load_list()
        QMessageBox.information(self, "Başarılı", "Kayıt şifrelenerek eklendi.")

    def load_list(self):
        self.table.setRowCount(0)
        with sqlite3.connect("vault_ultra.db") as conn:
            rows = conn.execute("SELECT id, site, email, password FROM accounts").fetchall()
            for r_idx, row in enumerate(rows):
                self.table.insertRow(r_idx)
                site_item = QTableWidgetItem(self.vault.fernet.decrypt(row[1]).decode())
                mail_item = QTableWidgetItem(self.vault.fernet.decrypt(row[2]).decode())
                
                # Gizli verileri (ID ve Şifre) sakla
                site_item.setData(Qt.UserRole, row[0]) # ID
                site_item.setData(Qt.UserRole + 1, self.vault.fernet.decrypt(row[3]).decode()) # Şifre
                
                self.table.setItem(r_idx, 0, site_item)
                self.table.setItem(r_idx, 1, mail_item)

    def copy_password(self, item):
        row = item.row()
        password = self.table.item(row, 0).data(Qt.UserRole + 1)
        QApplication.clipboard().setText(password)
        QMessageBox.information(self, "Kopyalandı", "Şifre panoya kopyalandı!")

    def delete_entry(self):
        curr = self.table.currentRow()
        if curr < 0: return
        
        reply = QMessageBox.question(self, 'Onay', "Bu kaydı silmek istediğinize emin misiniz?", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            db_id = self.table.item(curr, 0).data(Qt.UserRole)
            with sqlite3.connect("vault_ultra.db") as conn:
                conn.execute("DELETE FROM accounts WHERE id = ?", (db_id,))
            self.load_list()

# --- TETİKLEYİCİ ---
app = QApplication(sys.argv)
ex = MintVaultApp()
class SignalHandler(QObject): trigger = pyqtSignal()
sh = SignalHandler(); sh.trigger.connect(lambda: (ex.show(), ex.raise_(), ex.activateWindow()))

keyboard.GlobalHotKeys({'<ctrl>+<alt>+k': lambda: sh.trigger.emit()}).start()
sys.exit(app.exec_())