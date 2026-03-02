# 🛡️ MintVault

Linux Mint ve diğer Debian tabanlı sistemler için geliştirilmiş, hafif, güvenli ve "Sıfır Bilgi" (Zero-Knowledge) prensibiyle çalışan yerel bir şifre yöneticisi.

## ✨ Özellikler

* **AES-256 Şifreleme:** Site adı, e-posta ve şifreleriniz dahil her şey askeri düzeyde şifrelenir.
* **Zero-Knowledge:** Master Key'iniz hiçbir yerde saklanmaz. Sadece siz girdiğinizde RAM üzerinde geçici bir anahtar oluşturulur.
* **Exponential Backoff (Rate Limit):** Hatalı girişlerde 1 dakikadan 30 dakikaya kadar artan bekleme süreleri ile kaba kuvvet (brute force) saldırılarını engeller.
* **Hızlı Kısayol:** `Ctrl + Alt + K` kombinasyonu ile dilediğiniz her yerden kasanıza erişin.
* **Pratik Kullanım:** * **Enter** desteği ile hızlı giriş ve kayıt.
* Listeye **çift tıklayarak** şifreyi panoya kopyalama.
* Otomatik güçlü şifre üretici.
* Seçili kayıtları silme ve yönetme.



## 🚀 Kurulum

Öncelikle gerekli sistem kütüphanelerini yükleyin:

```bash
sudo apt update
sudo apt install python3-cryptography python3-pyqt5 python3-pynput

```

Ardından repoyu klonlayın veya Python dosyasını indirin:

```bash
python3 MintVault.py

```

## ⌨️ Kısayollar

| Kısayol | İşlem |
| --- | --- |
| `Ctrl + Alt + K` | MintVault Popup Penceresini Aç / Gizle |
| `Enter` | Giriş Yap / Kaydet |
| `Çift Tıklama` | Seçili hesabın şifresini panoya kopyalar |

## 🛠️ Teknik Detaylar

* **Veritabanı:** SQLite (Tüm veriler BLOB formatında şifreli saklanır).
* **Güvenlik Katmanı:** Deneme kayıtları (rate limit), donanım kimliğinizle (UUID) mühürlenmiş gizli bir cache dosyasında saklanır.
* **Arayüz:** PyQt5 (Modern Dark Theme).

## ⚠️ Önemli Not

Bu proje verilerinizi yerel (local) olarak saklar. `vault_ultra.db` dosyasını silmeniz durumunda verileriniz kurtarılamaz. Düzenli olarak bu dosyanın yedeğini almanız önerilir.

---

Ufak bir proje de olsa bu tarz bir dokümantasyon, ileride dönüp baktığında veya birine gösterdiğinde projenin çok daha kaliteli görünmesini sağlar.

Repo için yapabileceğim başka bir şey var mı? Belki bir `.gitignore` dosyası (veritabanı dosyalarının GitHub'a gitmemesi için) hazırlamamı ister misin?
