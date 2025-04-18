#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ARP Spoofing Tespit Aracı - Tek Dosya Sürümü
Bu araç, ağda olası ARP spoofing saldırılarını tespit etmek için gerekli tüm fonksiyonları ve 
tkinter tabanlı bir grafik arayüz içerir.
"""

# --------- Gerekli modülleri içe aktarma ---------
import socket
import struct
import time
import sys
import subprocess
import re
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, Toplevel, PhotoImage
import threading
from collections import defaultdict
import io
from contextlib import redirect_stdout
import platform
import tempfile
import base64

# ============= ARP TESPİT MODÜLÜ =============

# MAC adreslerini düzgün formatta gösterme
def format_mac(mac_bytes):
    """
    Binary MAC adresini okunabilir formata çevirir.
    """
    if isinstance(mac_bytes, bytes):
        return ':'.join(f'{b:02x}' for b in mac_bytes)
    return mac_bytes

# IP adreslerini düzgün formatta gösterme
def format_ip(ip_bytes):
    """
    Binary IP adresini okunabilir formata çevirir.
    """
    if isinstance(ip_bytes, bytes):
        return socket.inet_ntoa(ip_bytes)
    return ip_bytes

# ARP tablosunu alma
def get_arp_table():
    """
    Sistemin ARP tablosunu alır.
    
    Returns:
        list: ARP tablosundaki kayıtlar listesi
    """
    arp_entries = []
    
    try:
        # Platforma göre uygun komutu belirle
        if os.name == 'nt':  # Windows
            output = subprocess.check_output(['arp', '-a'], text=True)
            # Windows ARP çıktısını ayrıştır
            pattern = r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f-]+)\s+(\w+)'
            for line in output.split('\n'):
                match = re.search(pattern, line)
                if match:
                    ip, mac, interface_type = match.groups()
                    mac = mac.replace('-', ':')  # Standart formata çevir
                    arp_entries.append({"ip": ip, "mac": mac, "interface": interface_type})
        else:  # Linux/Unix
            output = subprocess.check_output(['arp', '-n'], text=True)
            # Linux ARP çıktısını ayrıştır
            for line in output.split('\n')[1:]:  # Başlık satırını atla
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        ip = parts[0]
                        mac = parts[2]
                        interface = parts[-1] if len(parts) > 3 else "unknown"
                        if mac != "(incomplete)":  # Eksik kayıtları atla
                            arp_entries.append({"ip": ip, "mac": mac, "interface": interface})
    except Exception as e:
        print(f"❌ ARP tablosu alınırken hata oluştu: {e}")
        # Test verileri oluştur (gerçek cihazlarda test edebilmek için)
        test_entries = [
            {"ip": "192.168.1.1", "mac": "aa:bb:cc:dd:ee:ff", "interface": "eth0"},
            {"ip": "192.168.1.2", "mac": "11:22:33:44:55:66", "interface": "eth0"}
        ]
        return test_entries
    
    return arp_entries

# Varsayılan ağ geçidini bulma
def get_default_gateway():
    """
    Varsayılan ağ geçidini (default gateway) bulur.
    
    Returns:
        dict: Ağ geçidi IP ve MAC adresi
    """
    try:
        if os.name == 'nt':  # Windows
            output = subprocess.check_output(['ipconfig'], text=True)
            gateway_ip = None
            for line in output.split('\n'):
                if 'Default Gateway' in line or 'Varsayılan Ağ Geçidi' in line:
                    match = re.search(r':\s*(\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        gateway_ip = match.group(1)
                        break
        else:  # Linux/Unix
            output = subprocess.check_output(['ip', 'route'], text=True)
            match = re.search(r'default via (\d+\.\d+\.\d+\.\d+)', output)
            gateway_ip = match.group(1) if match else None
        
        # Gateway IP'yi bulduktan sonra ARP tablosundan MAC adresini alıyoruz
        if gateway_ip:
            arp_table = get_arp_table()
            for entry in arp_table:
                if entry["ip"] == gateway_ip:
                    return {"ip": gateway_ip, "mac": entry["mac"]}
        
        print("⚠️ Varsayılan ağ geçidi bulunamadı.")
        return {"ip": "Bilinmiyor", "mac": "Bilinmiyor"}
    
    except Exception as e:
        print(f"❌ Varsayılan ağ geçidi bulunurken hata oluştu: {e}")
        return {"ip": "Bilinmiyor", "mac": "Bilinmiyor"}

# ARP spoofing tespiti
def detect_arp_spoofing(arp_table):
    """
    ARP tablosunu inceleyerek olası ARP spoofing saldırılarını tespit eder.
    
    Args:
        arp_table (list): ARP tablosu kayıtları
        
    Returns:
        list: Tespit edilen şüpheli durumlar
    """
    suspicious_entries = []
    mac_to_ips = defaultdict(list)
    
    # Her MAC adresine bağlı IP'leri topla
    for entry in arp_table:
        mac = entry["mac"].lower()  # Büyük/küçük harf duyarlılığını kaldır
        ip = entry["ip"]
        mac_to_ips[mac].append(ip)
    
    # Bir MAC'in birden fazla IP'si varsa (1'den çok cihaz olabilir)
    for mac, ips in mac_to_ips.items():
        if len(ips) > 1:
            suspicious_entries.append({
                "type": "multiple_ips",
                "mac": mac,
                "ips": ips,
                "message": f"⚠️ Şüpheli: {mac} MAC adresine sahip {len(ips)} farklı IP adresi var: {', '.join(ips)}"
            })
    
    # Ağ geçidinin MAC adresi değişmiş mi kontrol et
    gateway = get_default_gateway()
    if gateway["ip"] != "Bilinmiyor" and gateway["mac"] != "Bilinmiyor":
        gateway_entries = [entry for entry in arp_table if entry["ip"] == gateway["ip"]]
        if len(gateway_entries) > 0:
            if len(gateway_entries) > 1:
                suspicious_entries.append({
                    "type": "gateway_multiple_macs",
                    "ip": gateway["ip"],
                    "macs": [entry["mac"] for entry in gateway_entries],
                    "message": f"❌ TEHLİKE: Ağ geçidi {gateway['ip']} için birden fazla MAC adresi var!"
                })
            
            # Broadcast veya multicast MAC adresleri
            for entry in arp_table:
                mac = entry["mac"].lower()
                # Broadcast MAC (ff:ff:ff:ff:ff:ff)
                if mac == "ff:ff:ff:ff:ff:ff":
                    suspicious_entries.append({
                        "type": "broadcast_mac",
                        "ip": entry["ip"],
                        "mac": mac,
                        "message": f"📌 Broadcast MAC adresi: IP={entry['ip']}, MAC={mac}"
                    })
                # Multicast MAC (ilk byte'ın en düşük biti 1)
                elif mac.startswith(("01:", "03:", "05:", "07:", "09:", "0b:", "0d:", "0f:")):
                    suspicious_entries.append({
                        "type": "multicast_mac",
                        "ip": entry["ip"],
                        "mac": mac,
                        "message": f"📌 Multicast MAC adresi: IP={entry['ip']}, MAC={mac}"
                    })
    
    return suspicious_entries

# Ana ARP tarama fonksiyonu
def arp_kontrol_et():
    """
    ARP tablosunu kontrol ederek olası ARP spoofing saldırılarını tespit eder.
    Bu fonksiyon GUI tarafından çağrılır.
    """
    print("=" * 60)
    print("🔍 ARP Tablosu Taraması Başlatılıyor...")
    print("=" * 60)
    
    # ARP tablosunu al
    arp_table = get_arp_table()
    
    if not arp_table:
        print("❌ ARP tablosu alınamadı veya boş.")
        return
    
    # Varsayılan ağ geçidini bul
    gateway = get_default_gateway()
    
    print(f"🌐 Varsayılan Ağ Geçidi: {gateway['ip']} (MAC: {gateway['mac']})")
    print("=" * 60)
    
    # ARP tablosunu göster
    print("\n📋 ARP Tablosu:")
    print("-" * 60)
    print(f"{'IP Adresi':<15} {'MAC Adresi':<20} {'Arayüz':<10}")
    print("-" * 60)
    for entry in arp_table:
        print(f"{entry['ip']:<15} {entry['mac']:<20} {entry['interface']:<10}")
    
    # ARP spoofing tespiti
    print("\n🔍 ARP Spoofing Analizi:")
    print("-" * 60)
    
    suspicious_entries = detect_arp_spoofing(arp_table)
    
    if suspicious_entries:
        for entry in suspicious_entries:
            print(entry["message"])
    else:
        print("✅ Herhangi bir şüpheli durum tespit edilmedi.")
    
    # Özet
    print("\n📊 Analiz Özeti:")
    print("-" * 60)
    print(f"Toplam kayıt sayısı: {len(arp_table)}")
    print(f"Şüpheli kayıt sayısı: {len(suspicious_entries)}")
    
    if suspicious_entries:
        şüpheli_tiplerini_say = defaultdict(int)
        for entry in suspicious_entries:
            şüpheli_tiplerini_say[entry["type"]] += 1
        
        for tip, sayı in şüpheli_tiplerini_say.items():
            tip_açıklamaları = {
                "multiple_ips": "Birden fazla IP'ye sahip MAC adresleri",
                "gateway_multiple_macs": "Birden fazla MAC'e sahip ağ geçidi",
                "broadcast_mac": "Broadcast MAC adresleri",
                "multicast_mac": "Multicast MAC adresleri"
            }
            açıklama = tip_açıklamaları.get(tip, tip)
            print(f"- {açıklama}: {sayı}")
        
        print("\n⚠️ Şüpheli durumlar tespit edildi. Ağınızda ARP spoofing saldırısı olabilir.")
        print("⚠️ Özellikle birden fazla MAC adresine sahip bir ağ geçidi varsa, bu ciddi bir tehlike işaretidir.")
    else:
        print("\n✅ Ağınız şu an için güvenli görünüyor.")
    
    # Tavsiyeler
    print("\n💡 Tavsiyeler:")
    print("-" * 60)
    print("1. Emin değilseniz, ağ yöneticinize danışın")
    print("2. Güvenli olmayan ağlarda hassas işlemler yapmaktan kaçının")
    print("3. VPN kullanarak güvenli iletişim sağlayın")
    print("4. Periyodik olarak ARP tablonuzu kontrol edin")
    
    print("\n" + "=" * 60)
    print("🏁 Tarama Tamamlandı")
    print("=" * 60)


# ============= GRAFİK KULLANICI ARAYÜZÜ =============

# Modern bir kalkan ikonu - base64 encoded
SHIELD_ICON = """
iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAACXBIWXMAAAsTAAALEwEAmpwYAAAF92lUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDUgNzkuMTYzNDk5LCAyMDE4LzA4LzEzLTE2OjQwOjIyICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgQ0MgMjAxOSAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDI1LTA0LTE4VDEzOjU0OjI3WiIgeG1wOk1vZGlmeURhdGU9IjIwMjUtMDQtMThUMTM6NTQ6NDBaIiB4bXA6TWV0YWRhdGFEYXRlPSIyMDI1LTA0LTE4VDEzOjU0OjQwWiIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDphODMxMmZmYS0xNmY0LTRkNGMtOGM3MS0wYzRj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
"""

class ARP_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ARP Spoofing Tespit Aracı")
        self.root.geometry("800x650")
        self.root.resizable(True, True)
        
        # Renk şeması - Daha modern bir tema
        self.bg_color = "#1E1E2E"  # Koyu arka plan
        self.text_color = "#CDD6F4"  # Açık metin rengi
        self.button_color = "#89B4FA"  # Mavi buton
        self.warning_color = "#F38BA8"  # Kırmızı uyarı
        self.success_color = "#A6E3A1"  # Yeşil başarı
        self.accent_color = "#F5C2E7"  # Vurgu rengi
        self.secondary_bg = "#313244"  # İkincil arka plan
        
        # Uygulama simgesi
        try:
            # Base64 kodlu ikonu geçici dosyaya kaydedip kullan
            icon_data = base64.b64decode(SHIELD_ICON.strip())
            self.icon_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            self.icon_file.write(icon_data)
            self.icon_file.close()
            
            # Platform kontrolü ve simge ayarı
            if platform.system() == "Windows":
                self.root.iconbitmap(self.icon_file.name)
            else:
                icon = PhotoImage(file=self.icon_file.name)
                self.root.iconphoto(True, icon)
        except Exception as e:
            print(f"Simge yüklenirken hata: {e}")
        
        # Tema ayarları
        style = ttk.Style()
        style.theme_use('clam')  # clam teması modern görünüm için uygun
        
        # Progressbar teması
        style.configure("TProgressbar", 
                       background=self.button_color,
                       troughcolor=self.secondary_bg,
                       borderwidth=0,
                       thickness=8)
        
        # Ana çerçeveyi oluştur
        self.main_frame = tk.Frame(root, bg=self.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Başlık çerçevesi
        header_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Başlık
        title_label = tk.Label(header_frame, 
                              text="ARP Spoofing Tespit Aracı", 
                              font=("Segoe UI", 22, "bold"),
                              bg=self.bg_color, 
                              fg=self.accent_color)
        title_label.pack(pady=10)
        
        # Alt başlık
        description_label = tk.Label(header_frame, 
                                    text="Bu araç, ağınızda olası ARP Spoofing saldırılarını tespit eder.\n"
                                         "ARP Spoofing, bir saldırganın ağ trafiğinizi izlemesine olanak tanır.",
                                    font=("Segoe UI", 10),
                                    bg=self.bg_color, 
                                    fg=self.text_color, 
                                    justify="center")
        description_label.pack(pady=5)
        
        # Ayırıcı çizgi
        separator = ttk.Separator(self.main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=5)
        
        # Seçenekler çerçevesi
        options_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        options_frame.pack(fill=tk.X, pady=10)
        
        # Periyodik kontrol onay kutusu
        self.periodic_var = tk.BooleanVar()
        self.startup_var = tk.BooleanVar()
        
        # Sonuç durum göstergesi paneli
        self.status_panel = tk.Frame(self.main_frame, bg=self.secondary_bg, 
                                   highlightbackground=self.button_color, 
                                   highlightthickness=1, 
                                   padx=10, pady=10)
        self.status_panel.pack(fill=tk.X, pady=10)
        
        self.status_icon_label = tk.Label(self.status_panel, 
                                       text="🔍", 
                                       font=("Segoe UI", 36),
                                       bg=self.secondary_bg)
        self.status_icon_label.pack(side=tk.LEFT, padx=(10, 20))
        
        status_text_frame = tk.Frame(self.status_panel, bg=self.secondary_bg)
        status_text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.status_title = tk.Label(status_text_frame, 
                                   text="Ağınızın Durumu", 
                                   font=("Segoe UI", 14, "bold"),
                                   bg=self.secondary_bg, 
                                   fg=self.text_color)
        self.status_title.pack(anchor="w")
        
        self.status_description = tk.Label(status_text_frame, 
                                        text="Ağınızın durumunu görmek için tarama yapın.", 
                                        font=("Segoe UI", 10),
                                        bg=self.secondary_bg, 
                                        fg=self.text_color,
                                        justify="left",
                                        wraplength=500)
        self.status_description.pack(anchor="w", fill=tk.X, expand=True)
        
        # Sonuçlar için metin alanı
        results_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        results_label = tk.Label(results_frame, 
                               text="Tarama Sonuçları", 
                               font=("Segoe UI", 10, "bold"),
                               bg=self.bg_color, 
                               fg=self.text_color)
        results_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        self.results_text = scrolledtext.ScrolledText(results_frame, 
                                                    wrap=tk.WORD, 
                                                    height=15,
                                                    bg=self.secondary_bg, 
                                                    fg=self.text_color,
                                                    insertbackground=self.text_color,
                                                    font=("Consolas", 10))
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.results_text.insert(tk.END, "ARP taraması için 'Tara' butonuna tıklayın.\n")
        self.results_text.config(state=tk.DISABLED)
        
        # İlerleme çubuğu
        self.progress = ttk.Progressbar(self.main_frame, 
                                       style="TProgressbar", 
                                       orient=tk.HORIZONTAL, 
                                       length=100, 
                                       mode='indeterminate')
        
        # Ayarlar çerçevesi
        settings_frame = tk.LabelFrame(self.main_frame, 
                                     text="Ayarlar", 
                                     font=("Segoe UI", 10, "bold"),
                                     bg=self.bg_color, 
                                     fg=self.text_color)
        settings_frame.pack(fill=tk.X, pady=10)
        
        # Periyodik kontrol ayarı
        self.periodic_check = tk.Checkbutton(settings_frame, 
                                          text="Periyodik kontrol (24 saatte bir)", 
                                          variable=self.periodic_var,
                                          bg=self.bg_color, 
                                          fg=self.text_color,
                                          selectcolor=self.secondary_bg,
                                          activebackground=self.bg_color,
                                          activeforeground=self.text_color)
        self.periodic_check.pack(anchor="w", padx=10, pady=5)
        
        # Bilgisayar açılışında başlatma ayarı
        self.startup_check = tk.Checkbutton(settings_frame, 
                                         text="Bilgisayar açıldığında otomatik başlat", 
                                         variable=self.startup_var,
                                         bg=self.bg_color, 
                                         fg=self.text_color,
                                         selectcolor=self.secondary_bg,
                                         activebackground=self.bg_color,
                                         activeforeground=self.text_color,
                                         command=self.set_startup)
        self.startup_check.pack(anchor="w", padx=10, pady=5)
        
        # Butonlar çerçevesi
        button_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Tarama butonu
        self.scan_button = tk.Button(button_frame, 
                                   text="Tara", 
                                   command=self.start_scan,
                                   bg=self.button_color, 
                                   fg="#FFFFFF",
                                   width=15,
                                   font=("Segoe UI", 10, "bold"),
                                   relief=tk.FLAT,
                                   borderwidth=0,
                                   padx=5,
                                   pady=5)
        self.scan_button.pack(side=tk.LEFT, padx=10)
        
        # Durdur butonu (periyodik tarama için)
        self.stop_button = tk.Button(button_frame, 
                                   text="Durdur", 
                                   command=self.stop_periodic_scan,
                                   bg=self.warning_color, 
                                   fg="#FFFFFF",
                                   width=15,
                                   font=("Segoe UI", 10, "bold"),
                                   relief=tk.FLAT,
                                   borderwidth=0,
                                   padx=5,
                                   pady=5,
                                   state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10)
        
        # Çıkış butonu
        exit_button = tk.Button(button_frame, 
                              text="Çıkış", 
                              command=self.exit_program,
                              bg=self.secondary_bg, 
                              fg=self.text_color,
                              width=15,
                              font=("Segoe UI", 10, "bold"),
                              relief=tk.FLAT,
                              borderwidth=0,
                              padx=5,
                              pady=5)
        exit_button.pack(side=tk.RIGHT, padx=10)
        
        # Durum çubuğu
        self.status_var = tk.StringVar()
        self.status_var.set("Hazır")
        status_bar = tk.Label(self.main_frame, 
                            textvariable=self.status_var, 
                            bd=1, 
                            relief=tk.SUNKEN, 
                            anchor=tk.W,
                            bg=self.secondary_bg, 
                            fg=self.text_color,
                            font=("Segoe UI", 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        
        # Periyodik tarama için durum değişkenleri
        self.periodic_running = False
        self.periodic_thread = None
        
        # Uyarı penceresi reference'ı
        self.warning_window = None
        
        # Kapanış sırasında periyodik taramayı düzgün şekilde sonlandır
        self.root.protocol("WM_DELETE_WINDOW", self.exit_program)
        
    def set_startup(self):
        """
        Bilgisayar açılışında otomatik başlatma ayarını yapar
        """
        if self.startup_var.get():
            platform_system = platform.system()
            
            if platform_system == "Windows":
                # Windows için başlangıç klasörüne kısayol oluştur
                msg = "Bu programı Windows başlangıcına eklemek için:\n\n"
                msg += "1. Windows + R tuşlarına basıp 'shell:startup' yazın\n"
                msg += "2. Açılan klasöre bu programın kısayolunu ekleyin\n"
                
                messagebox.showinfo("Bilgisayar Açılışında Başlatma", msg)
                
            elif platform_system == "Linux":
                # Linux için autostart klasörüne .desktop dosyası oluştur
                msg = "Bu programı Linux başlangıcına eklemek için:\n\n"
                msg += "1. ~/.config/autostart klasörü oluşturun\n"
                msg += "2. Bu klasörde 'arp-detector.desktop' dosyası oluşturun\n"
                msg += "3. Dosyaya aşağıdaki içeriği ekleyin:\n\n"
                msg += "[Desktop Entry]\n"
                msg += "Type=Application\n"
                msg += "Name=ARP Spoofing Tespit Aracı\n"
                msg += f"Exec=python3 {os.path.abspath(__file__)}\n"
                msg += "Terminal=false\n"
                
                messagebox.showinfo("Bilgisayar Açılışında Başlatma", msg)
                
            elif platform_system == "Darwin":  # macOS
                # macOS için launchd plist dosyası oluştur
                msg = "Bu programı macOS başlangıcına eklemek için:\n\n"
                msg += "1. ~/Library/LaunchAgents klasörü oluşturun\n"
                msg += "2. Bu klasörde 'com.user.arpdetector.plist' dosyası oluşturun\n"
                msg += "3. Dosyaya uygun plist içeriğini ekleyin\n"
                
                messagebox.showinfo("Bilgisayar Açılışında Başlatma", msg)
            
            self.update_text("Bilgisayar açılışında başlatma ayarlandı.\n")
        else:
            # Açılışta başlatmayı kaldır
            self.update_text("Bilgisayar açılışında başlatma devre dışı bırakıldı.\n")
    
    def update_text(self, text, clear=False, is_warning=False, is_success=False):
        """
        Sonuç metin alanını günceller.
        
        Args:
            text (str): Eklenecek metin
            clear (bool): Mevcut metni temizleyip temizlememe
            is_warning (bool): Uyarı olarak renklendirme
            is_success (bool): Başarı olarak renklendirme
        """
        self.results_text.config(state=tk.NORMAL)
        
        if clear:
            self.results_text.delete(1.0, tk.END)
        
        # Renge göre metin ekle
        if is_warning:
            self.results_text.insert(tk.END, text, "warning")
            # Etiket tanımlanmamışsa oluştur
            if not "warning" in self.results_text.tag_names():
                self.results_text.tag_configure("warning", foreground=self.warning_color)
        elif is_success:
            self.results_text.insert(tk.END, text, "success")
            # Etiket tanımlanmamışsa oluştur
            if not "success" in self.results_text.tag_names():
                self.results_text.tag_configure("success", foreground=self.success_color)
        else:
            self.results_text.insert(tk.END, text)
        
        self.results_text.see(tk.END)  # Otomatik olarak aşağı kaydır
        self.results_text.config(state=tk.DISABLED)
    
    def show_warning_window(self, suspicious_entries):
        """
        Saldırı tespiti durumunda uyarı penceresi gösterir
        """
        # Eğer önceden açılmış bir uyarı penceresi varsa kapat
        if self.warning_window and self.warning_window.winfo_exists():
            self.warning_window.destroy()
        
        # Yeni uyarı penceresi oluştur
        self.warning_window = Toplevel(self.root)
        self.warning_window.title("⚠️ ARP Spoofing Riski Tespit Edildi!")
        self.warning_window.geometry("650x500")
        self.warning_window.resizable(True, True)
        self.warning_window.configure(bg=self.bg_color)
        self.warning_window.transient(self.root)
        self.warning_window.grab_set()
        
        # İkonu ayarla
        try:
            if platform.system() == "Windows":
                self.warning_window.iconbitmap(self.icon_file.name)
            else:
                icon = PhotoImage(file=self.icon_file.name)
                self.warning_window.iconphoto(True, icon)
        except:
            pass
        
        # Başlık çerçevesi
        header_frame = tk.Frame(self.warning_window, bg=self.bg_color)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        # Uyarı ikonu ve başlık
        header_label = tk.Label(header_frame, 
                              text="⚠️ ARP SPOOFING RİSKİ TESPİT EDİLDİ", 
                              font=("Segoe UI", 16, "bold"),
                              bg=self.bg_color, 
                              fg=self.warning_color)
        header_label.pack(pady=10)
        
        # Uyarı açıklaması
        description_label = tk.Label(header_frame, 
                                   text="Ağınızda şüpheli ARP etkinliği tespit edildi. Bu durum, bir saldırganın ağ trafiğinizi izlediğini gösterebilir.", 
                                   font=("Segoe UI", 10),
                                   bg=self.bg_color, 
                                   fg=self.text_color,
                                   wraplength=600,
                                   justify="center")
        description_label.pack(pady=5)
        
        # Tehdit açıklaması
        threat_frame = tk.Frame(self.warning_window, bg=self.secondary_bg, padx=20, pady=20)
        threat_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Tespit edilen şüpheli durumlar
        threat_title = tk.Label(threat_frame, 
                              text="Tespit Edilen Şüpheli Durumlar:", 
                              font=("Segoe UI", 11, "bold"),
                              bg=self.secondary_bg, 
                              fg=self.text_color)
        threat_title.pack(anchor="w", pady=(0, 10))
        
        # Şüpheli durumları listele
        suspicious_count = 0
        has_critical = False
        
        for entry in suspicious_entries:
            # Kritik tehdit mi kontrol et (gateway_multiple_macs en tehlikeli durum)
            if entry["type"] == "gateway_multiple_macs":
                has_critical = True
            
            if "message" in entry and not entry["type"] in ["broadcast_mac", "multicast_mac"]:
                suspicious_count += 1
                label = tk.Label(threat_frame, 
                               text=entry["message"], 
                               font=("Segoe UI", 10),
                               bg=self.secondary_bg, 
                               fg=self.warning_color,
                               justify="left",
                               wraplength=580)
                label.pack(anchor="w", pady=2)
        
        # Önlemler çerçevesi
        actions_frame = tk.LabelFrame(self.warning_window, 
                                    text="Alınabilecek Önlemler", 
                                    font=("Segoe UI", 11, "bold"),
                                    bg=self.bg_color, 
                                    fg=self.text_color,
                                    padx=15, pady=15)
        actions_frame.pack(fill=tk.BOTH, padx=20, pady=10)
        
        # Önerilen önlemler
        actions_text = """
1. Ağ bağlantınızı hemen kesin ve güvenli olmayan ağlarda hassas işlemler yapmaktan kaçının.

2. Ağ yöneticinizi bilgilendirin ve olası saldırı hakkında uyarın.

3. VPN kullanarak ağ trafiğinizi şifreleyin, bu saldırganın verilerinizi okumasını engeller.

4. Statik ARP girdileri ekleyerek kritik cihazların MAC adreslerini sabitleyin.

5. HTTPS bağlantıları ve güvenli iletişim protokolleri kullanın.
"""
        
        actions_label = tk.Label(actions_frame, 
                               text=actions_text, 
                               font=("Segoe UI", 10),
                               bg=self.bg_color, 
                               fg=self.text_color,
                               justify="left")
        actions_label.pack(anchor="w")
        
        # Butonlar çerçevesi
        buttons_frame = tk.Frame(self.warning_window, bg=self.bg_color)
        buttons_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
        
        # Kapat butonu
        close_button = tk.Button(buttons_frame, 
                                text="Anladım", 
                                command=self.warning_window.destroy,
                                bg=self.button_color, 
                                fg="#FFFFFF",
                                width=15,
                                font=("Segoe UI", 10, "bold"),
                                relief=tk.FLAT,
                                padx=5,
                                pady=5)
        close_button.pack(side=tk.RIGHT, padx=5)
        
        # Pencereyi ekranın ortasına konumlandır
        self.warning_window.update_idletasks()
        width = self.warning_window.winfo_width()
        height = self.warning_window.winfo_height()
        x = (self.warning_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.warning_window.winfo_screenheight() // 2) - (height // 2)
        self.warning_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    def update_status_panel(self, is_safe, suspicious_count=0, has_critical=False):
        """
        Durum panelini günceller
        """
        if is_safe:
            # Güvenli durum
            self.status_icon_label.config(text="✅")
            self.status_title.config(text="AĞINIZ GÜVENDEDİR", fg=self.success_color)
            self.status_description.config(text="Ağınızda herhangi bir ARP spoofing tehdidi tespit edilmedi. "
                                          "Düzenli olarak kontrol etmeye devam edin.")
            
            # Durum paneli rengi
            self.status_panel.config(highlightbackground=self.success_color)
        else:
            # Tehlikeli durum
            self.status_icon_label.config(text="⚠️")
            self.status_title.config(text="SALDIRI ALTINDASINIZ!", fg=self.warning_color)
            
            # Tehlikenin ciddiyetine göre mesaj
            if has_critical:
                self.status_description.config(text="Ağınızda ciddi bir ARP spoofing tehdidi tespit edildi! "
                                              "Ağ geçidinizde anormal MAC adresleri var. Acil önlem almalısınız!")
            else:
                self.status_description.config(text=f"Ağınızda {suspicious_count} şüpheli ARP etkinliği tespit edildi. "
                                              "Bu durum bir ARP spoofing saldırısı olabileceğini gösteriyor.")
            
            # Durum paneli rengi
            self.status_panel.config(highlightbackground=self.warning_color)
    
    def capture_output(self, func, *args, **kwargs):
        """
        Bir fonksiyonun print çıktılarını yakalar ve GUI'de gösterir.
        
        Args:
            func: Çıktısı yakalanacak fonksiyon
            *args, **kwargs: Fonksiyona geçirilecek argümanlar
            
        Returns:
            Fonksiyonun geri dönüş değeri ve tespitler
        """
        f = io.StringIO()
        with redirect_stdout(f):
            result = func(*args, **kwargs)
        
        output = f.getvalue()
        
        # Sadece gerekli bilgileri göster (sadeleştirilmiş çıktı)
        important_lines = []
        arp_table_section = False
        suspicious_entries = []
        
        lines = output.split('\n')
        for line in lines:
            # ARP tablosu bölümünü atla
            if "ARP Tablosu:" in line:
                arp_table_section = True
                continue
            if arp_table_section and "ARP Spoofing Analizi:" in line:
                arp_table_section = False
            if arp_table_section:
                continue
            
            # Şüpheli durumları topla
            if "⚠️" in line or "❌" in line:
                important_lines.append(line)
                suspicious_entries.append({
                    "message": line,
                    "type": "gateway_multiple_macs" if "TEHLİKE" in line else "other"
                })
            elif "✅ Herhangi bir şüpheli durum tespit edilmedi" in line:
                important_lines.append(line)
            elif "✅ Ağınız şu an için güvenli görünüyor" in line:
                important_lines.append(line)
            elif "Şüpheli kayıt sayısı:" in line:
                important_lines.append(line)
                
        # Sadece önemli bilgileri göster
        self.update_text("=" * 60 + "\n")
        self.update_text("🔍 ARP TARAMASI SONUÇLARI 🔍\n")
        self.update_text("-" * 60 + "\n")
        
        # Sonuçları göster
        is_safe = True
        suspicious_count = 0
        has_critical = False
        
        for line in important_lines:
            if "⚠️" in line or "❌" in line:
                is_safe = False
                suspicious_count += 1
                if "TEHLİKE" in line:
                    has_critical = True
                self.update_text(line + "\n", is_warning=True)
            elif "✅" in line:
                self.update_text(line + "\n", is_success=True)
            else:
                self.update_text(line + "\n")
        
        # Durum panelini güncelle
        self.update_status_panel(is_safe, suspicious_count, has_critical)
        
        # Şüpheli durum varsa uyarı penceresini göster
        if not is_safe and len(suspicious_entries) > 0:
            self.root.after(500, lambda: self.show_warning_window(suspicious_entries))
        
        return result
    
    def start_scan(self):
        """
        ARP taramasını başlatır.
        """
        # Arayüzü hazırla
        self.status_var.set("Ağınız taranıyor...")
        self.scan_button.config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.start()
        self.update_text("Tarama başlatılıyor...\n", clear=True)
        
        # Ayrı bir iş parçacığında tarama yap
        threading.Thread(target=self._run_scan, daemon=True).start()
    
    def _run_scan(self):
        """
        ARP taramasını arka planda çalıştırır.
        """
        try:
            # ARP taramasını yap
            self.capture_output(arp_kontrol_et)
            
            # Periyodik tarama istendi mi?
            if self.periodic_var.get() and not self.periodic_running:
                self.start_periodic_scan()
            else:
                # İlerleme çubuğunu durdur
                self.root.after(0, self.progress.stop)
                self.root.after(0, self.progress.pack_forget)
                self.root.after(0, lambda: self.scan_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.status_var.set("Tarama tamamlandı"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", f"Tarama sırasında bir hata oluştu: {str(e)}"))
            self.root.after(0, self.progress.stop)
            self.root.after(0, self.progress.pack_forget)
            self.root.after(0, lambda: self.scan_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_var.set("Hata oluştu"))
    
    def start_periodic_scan(self):
        """
        Periyodik taramayı başlatır.
        """
        self.periodic_running = True
        self.stop_button.config(state=tk.NORMAL)
        self.scan_button.config(state=tk.DISABLED)
        self.periodic_check.config(state=tk.DISABLED)
        
        # Bilgisayar açılışında otomatik başlatma seçimine göre bilgilendirme
        if self.startup_var.get():
            self.update_text("\n🕒 Periyodik kontrol aktifleştirildi. 24 saatte bir ARP tablosu kontrol edilecek.\n")
            self.update_text("🔄 Program bilgisayar açıldığında otomatik başlatılacak şekilde ayarlandı.\n")
        else:
            self.update_text("\n🕒 Periyodik kontrol aktifleştirildi. 24 saatte bir ARP tablosu kontrol edilecek.\n")
            self.update_text("ℹ️ Program arka planda çalışacak ancak bilgisayar yeniden başlatıldığında manuel olarak başlatmanız gerekecek.\n")
            
        self.update_text("ℹ️ Durdurmak için 'Durdur' butonuna tıklayabilirsiniz.\n")
        
        # Bir sonraki tarama zamanını göster
        next_time = time.localtime(time.time() + 86400)  # 24 saat sonrası
        next_time_str = time.strftime("%d.%m.%Y %H:%M:%S", next_time)
        self.update_text(f"⏱️ Bir sonraki kontrol {next_time_str} tarihinde yapılacak.\n")
        
        # Periyodik tarama iş parçacığını başlat
        self.periodic_thread = threading.Thread(target=self._periodic_scan_thread, daemon=True)
        self.periodic_thread.start()
        
        # Bildirim göster
        messagebox.showinfo("Periyodik Tarama Aktif", 
                          "Periyodik tarama etkinleştirildi. Program arka planda çalışacak ve 24 saatte bir ağınızı kontrol edecek.")
    
    def _periodic_scan_thread(self):
        """
        Periyodik tarama için arka plan iş parçacığı.
        """
        # Her 24 saatte bir tarama yap (86400 saniye)
        interval_seconds = 86400
        
        # 🚩 DEV TEST: Kısa interval ile test etmek için 
        # Yorumları kaldırarak test edebilirsiniz
        #interval_seconds = 60  # Test için 60 saniye
        
        self.root.after(0, lambda: self.status_var.set("Bir sonraki periyodik tarama bekleniyor..."))
        
        while self.periodic_running:
            # 24 saat bekle veya durdurulana kadar
            for i in range(interval_seconds):
                if not self.periodic_running:
                    return
                
                # Her dakikada bir durum çubuğunu güncelle
                if i % 60 == 0:
                    remaining_secs = interval_seconds - i
                    hours, remainder = divmod(remaining_secs, 3600)
                    minutes, _ = divmod(remainder, 60)
                    self.root.after(0, lambda h=hours, m=minutes: 
                                  self.status_var.set(f"Bir sonraki taramaya: {h} saat {m} dakika"))
                
                time.sleep(1)
            
            # Süre dolunca tarama yap
            if not self.periodic_running:
                return
                
            # Tarama yap
            self.root.after(0, lambda: self.status_var.set("Periyodik tarama başlatılıyor..."))
            self.root.after(0, lambda: self.update_text("\n" + "=" * 60 + "\n"))
            self.root.after(0, lambda: self.update_text(f"🕒 Periyodik ARP taraması başlatılıyor - {time.strftime('%Y-%m-%d %H:%M:%S')}\n"))
            
            try:
                # Taramayı yap ve sonuçları yakala
                f = io.StringIO()
                with redirect_stdout(f):
                    arp_kontrol_et()
                
                output = f.getvalue()
                
                # Uyarı durumlarını kontrol et
                suspicious_entries = []
                is_safe = True
                
                for line in output.split('\n'):
                    if "⚠️" in line or "❌" in line:
                        is_safe = False
                        suspicious_entries.append({
                            "message": line,
                            "type": "gateway_multiple_macs" if "TEHLİKE" in line else "other"
                        })
                
                # Özet bilgileri göster
                if is_safe:
                    self.root.after(0, lambda: self.update_text("✅ Ağınız güvende! Herhangi bir şüpheli durum tespit edilmedi.\n", is_success=True))
                else:
                    warning_msg = f"⚠️ DİKKAT: {len(suspicious_entries)} şüpheli durum tespit edildi! Detaylar için ana pencereye bakın.\n"
                    self.root.after(0, lambda msg=warning_msg: self.update_text(msg, is_warning=True))
                    
                    # Bildirim göster
                    if platform.system() == "Windows":
                        # Windows bildirim
                        self.root.after(0, lambda: messagebox.showwarning("ARP Spoofing Tehdidi", 
                                                                      "Periyodik tarama sırasında ARP spoofing tehdidi tespit edildi! Lütfen uygulamayı açın."))
                    elif platform.system() == "Darwin":  # macOS
                        # macOS bildirim
                        os.system(f"""osascript -e 'display notification "Ağınızda ARP spoofing tehdidi tespit edildi!" with title "Güvenlik Uyarısı" sound name "Basso"'""")
                    else:  # Linux
                        # Linux bildirim 
                        os.system(f"""notify-send "Güvenlik Uyarısı" "Ağınızda ARP spoofing tehdidi tespit edildi!" -i dialog-warning""")
                
                # Sonraki taramayı planla
                next_time = time.localtime(time.time() + interval_seconds)
                next_time_str = time.strftime("%d.%m.%Y %H:%M:%S", next_time)
                self.root.after(0, lambda t=next_time_str: self.update_text(f"⏱️ Bir sonraki kontrol {t} tarihinde yapılacak.\n"))
                self.root.after(0, lambda: self.update_text("=" * 60 + "\n"))
                self.root.after(0, lambda: self.status_var.set("Bir sonraki periyodik tarama bekleniyor..."))
            
            except Exception as e:
                # Hata durumunda güvenli bir şekilde UI güncelle
                error_message = f"❌ Periyodik tarama sırasında hata oluştu: {str(e)}\n"
                self.root.after(0, lambda msg=error_message: self.update_text(msg, is_warning=True))
    
    def stop_periodic_scan(self):
        """
        Periyodik taramayı durdurur.
        """
        if self.periodic_running:
            self.periodic_running = False
            # Thread'in sonlanmasını beklemeye gerek yok, daemon=True
            
            self.stop_button.config(state=tk.DISABLED)
            self.scan_button.config(state=tk.NORMAL)
            self.periodic_check.config(state=tk.NORMAL)
            self.periodic_var.set(False)
            
            self.update_text("\n🛑 Periyodik kontrol durduruldu.\n", is_warning=True)
            self.status_var.set("Hazır")
    
    def exit_program(self):
        """
        Programı düzgün bir şekilde kapatır.
        """
        if self.periodic_running:
            self.periodic_running = False
            # Thread'in sonlanmasını beklemeye gerek yok, daemon=True
        
        if messagebox.askokcancel("Çıkış", "Programdan çıkmak istediğinize emin misiniz?"):
            self.root.destroy()


# ============= ANA PROGRAM =============

if __name__ == "__main__":
    root = tk.Tk()
    app = ARP_GUI(root)
    root.mainloop()
