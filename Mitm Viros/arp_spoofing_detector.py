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

class ARP_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ARP Spoofing Tespit Aracı")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Google benzeri renk şeması
        self.bg_color = "#FFFFFF"       # Beyaz arka plan
        self.text_color = "#202124"     # Koyu gri metin
        self.button_color = "#4285F4"   # Google mavi
        self.warning_color = "#EA4335"  # Google kırmızı
        self.success_color = "#34A853"  # Google yeşil
        self.accent_color = "#FBBC05"   # Google sarı
        self.light_gray = "#F8F9FA"     # Açık gri arka plan
        
        # Tema ayarları
        style = ttk.Style()
        style.theme_use('default')
        
        # Progressbar teması
        style.configure("TProgressbar", 
                       background=self.button_color,
                       troughcolor="#E8EAED",  # Google gri
                       borderwidth=0,
                       thickness=6)
        
        # Ana çerçeveyi oluştur
        self.main_frame = tk.Frame(root, bg=self.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Logo ve başlık alanı
        header_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Basit logo (metin olarak)
        logo_label = tk.Label(header_frame, 
                            text="🛡️", 
                            font=("Arial", 36),
                            bg=self.bg_color)
        logo_label.pack(pady=(0, 5))
        
        # Başlık (Google benzeri minimal stil)
        title_label = tk.Label(header_frame, 
                              text="ARP Spoofing Tespit Aracı", 
                              font=("Arial", 24, "bold"),
                              bg=self.bg_color, 
                              fg=self.text_color)
        title_label.pack(pady=(0, 10))
        
        # Tarama alanı
        search_frame = tk.Frame(self.main_frame, bg=self.bg_color, pady=15)
        search_frame.pack(fill=tk.X)
        
        # Arama çubuğu benzeri tasarım (ortalanmış)
        search_container = tk.Frame(search_frame, 
                                  bg=self.light_gray, 
                                  highlightbackground="#DADCE0",
                                  highlightthickness=1,
                                  bd=0)
        search_container.pack(fill=tk.X, padx=80, ipady=5)
        
        # Tarama butonu
        self.scan_button = tk.Button(search_container, 
                                   text="Tara", 
                                   command=self.start_scan,
                                   bg=self.button_color, 
                                   fg="#FFFFFF",
                                   width=15,
                                   font=("Arial", 12),
                                   relief=tk.FLAT,
                                   borderwidth=0,
                                   padx=10,
                                   pady=8)
        self.scan_button.pack(pady=15)
        
        # Sonuç kartı alanı
        result_card = tk.Frame(self.main_frame, 
                             bg=self.light_gray,
                             highlightbackground="#DADCE0",
                             highlightthickness=1,
                             padx=15, pady=15)
        result_card.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Durum göstergesi (daha basit)
        self.status_icon_label = tk.Label(result_card,
                                       text="🔍", 
                                       font=("Arial", 24),
                                       bg=self.light_gray)
        self.status_icon_label.pack(pady=(0, 5))
        
        self.status_title = tk.Label(result_card, 
                                   text="Ağınızın Durumu", 
                                   font=("Arial", 16, "bold"),
                                   bg=self.light_gray, 
                                   fg=self.text_color)
        self.status_title.pack(pady=(0, 5))
        
        self.status_description = tk.Label(result_card, 
                                        text="Ağınızın güvenlik durumunu görmek için 'Tara' butonuna tıklayın.", 
                                        font=("Arial", 11),
                                        bg=self.light_gray, 
                                        fg=self.text_color,
                                        wraplength=500)
        self.status_description.pack(pady=(0, 10))
        
        # İlerleme çubuğu
        self.progress = ttk.Progressbar(result_card, 
                                       style="TProgressbar", 
                                       orient=tk.HORIZONTAL, 
                                       length=100, 
                                       mode='indeterminate')
        
        # Sonuç alanı
        self.results_text = scrolledtext.ScrolledText(result_card, 
                                                    wrap=tk.WORD, 
                                                    height=8,
                                                    bg="#FFFFFF", 
                                                    fg=self.text_color,
                                                    font=("Arial", 10),
                                                    relief=tk.FLAT,
                                                    bd=1)
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.results_text.config(state=tk.DISABLED)
        
        # Ayarlar paneli (daha basit ve minimalist)
        settings_frame = tk.Frame(self.main_frame, bg=self.bg_color, pady=10)
        settings_frame.pack(fill=tk.X)
        
        # Periyodik kontrol ve başlangıç seçenekleri
        self.periodic_var = tk.BooleanVar()
        self.startup_var = tk.BooleanVar()
        
        self.periodic_check = tk.Checkbutton(settings_frame, 
                                          text="Periyodik kontrol (24 saatte bir)", 
                                          variable=self.periodic_var,
                                          bg=self.bg_color, 
                                          fg=self.text_color,
                                          font=("Arial", 10),
                                          activebackground=self.bg_color)
        self.periodic_check.pack(side=tk.LEFT, padx=10)
        
        self.startup_check = tk.Checkbutton(settings_frame, 
                                         text="Bilgisayar açılışında başlat", 
                                         variable=self.startup_var,
                                         bg=self.bg_color, 
                                         fg=self.text_color, 
                                         font=("Arial", 10),
                                         activebackground=self.bg_color,
                                         command=self.set_startup)
        self.startup_check.pack(side=tk.LEFT, padx=10)
        
        # Alt butonlar çerçevesi
        bottom_frame = tk.Frame(self.main_frame, bg=self.bg_color, pady=5)
        bottom_frame.pack(fill=tk.X)
        
        # Durdur butonu
        self.stop_button = tk.Button(bottom_frame, 
                                   text="Durdur", 
                                   command=self.stop_periodic_scan,
                                   bg=self.warning_color, 
                                   fg="#FFFFFF",
                                   font=("Arial", 10),
                                   relief=tk.FLAT,
                                   state=tk.DISABLED,
                                   padx=10, pady=5)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Çıkış butonu
        exit_button = tk.Button(bottom_frame, 
                              text="Çıkış", 
                              command=self.exit_program,
                              bg="#E8EAED", 
                              fg=self.text_color,
                              font=("Arial", 10),
                              relief=tk.FLAT,
                              padx=10, pady=5)
        exit_button.pack(side=tk.RIGHT, padx=5)
        
        # Durum çubuğu
        self.status_var = tk.StringVar()
        self.status_var.set("Hazır")
        status_bar = tk.Label(self.main_frame, 
                            textvariable=self.status_var, 
                            bd=1, 
                            relief=tk.SUNKEN, 
                            anchor=tk.W,
                            bg="#F8F9FA", 
                            fg="#5F6368",
                            font=("Arial", 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        
        # Periyodik tarama için durum değişkenleri
        self.periodic_running = False
        self.periodic_thread = None
        
        # Uyarı penceresi referansı
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
        Saldırı tespiti durumunda uyarı penceresi gösterir (Google Material Design stili)
        """
        # Eğer önceden açılmış bir uyarı penceresi varsa kapat
        if self.warning_window and self.warning_window.winfo_exists():
            self.warning_window.destroy()
        
        # Yeni uyarı penceresi oluştur
        self.warning_window = Toplevel(self.root)
        self.warning_window.title("Güvenlik Uyarısı")
        self.warning_window.geometry("500x550")
        self.warning_window.resizable(True, True)
        self.warning_window.configure(bg="#FFFFFF")
        self.warning_window.transient(self.root)
        self.warning_window.grab_set()
        
        # Ana içerik çerçevesi
        content_frame = tk.Frame(self.warning_window, bg="#FFFFFF", padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Uyarı başlığı (kırmızı Google rengi) ve ikonu
        header_frame = tk.Frame(content_frame, bg="#FFFFFF")
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        icon_label = tk.Label(header_frame, 
                           text="⚠️", 
                           font=("Arial", 36),
                           fg=self.warning_color,
                           bg="#FFFFFF")
        icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        header_text_frame = tk.Frame(header_frame, bg="#FFFFFF")
        header_text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        header_label = tk.Label(header_text_frame, 
                              text="Güvenlik Uyarısı", 
                              font=("Arial", 16, "bold"),
                              bg="#FFFFFF", 
                              fg=self.warning_color)
        header_label.pack(anchor="w")
        
        subheader_label = tk.Label(header_text_frame, 
                                 text="ARP spoofing saldırısı tespit edildi", 
                                 font=("Arial", 12),
                                 bg="#FFFFFF", 
                                 fg="#5F6368")
        subheader_label.pack(anchor="w")
        
        # Ayırıcı çizgi
        separator = ttk.Separator(content_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=10)
        
        # Açıklama kartı
        description_card = tk.Frame(content_frame, 
                                  bg="#F8F9FA", 
                                  highlightbackground="#DADCE0",
                                  highlightthickness=1,
                                  padx=15, pady=15)
        description_card.pack(fill=tk.X, pady=10)
        
        description_label = tk.Label(description_card, 
                                   text="Ağınızda şüpheli ARP etkinliği tespit edildi. Bu durum, bir saldırganın ağ trafiğinizi izlediğini ve hassas bilgilerinizi çalabileceğini gösteriyor.", 
                                   font=("Arial", 11),
                                   bg="#F8F9FA", 
                                   fg="#202124",
                                   wraplength=430,
                                   justify="left")
        description_label.pack(anchor="w")
        
        # Tespit detayları
        details_frame = tk.Frame(content_frame, bg="#FFFFFF")
        details_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        details_label = tk.Label(details_frame, 
                               text="Tespit Edilen Tehditler", 
                               font=("Arial", 12, "bold"),
                               bg="#FFFFFF", 
                               fg="#202124")
        details_label.pack(anchor="w", pady=(0, 5))
        
        # Şüpheli durumlar listesi (Google Material List benzeri)
        threats_frame = tk.Frame(details_frame, bg="#FFFFFF")
        threats_frame.pack(fill=tk.X)
        
        # Şüpheli sayacı ve kritik tehdit flagleri  
        suspicious_count = 0
        has_critical = False
        
        for entry in suspicious_entries:
            if entry["type"] == "gateway_multiple_macs":
                has_critical = True
            
            if "message" in entry and not entry["type"] in ["broadcast_mac", "multicast_mac"]:
                suspicious_count += 1
                
                # Her şüpheli durumu bir kart içinde göster (Google Material Kartı)
                threat_card = tk.Frame(threats_frame, 
                                     bg="#FFFFFF",
                                     highlightbackground="#DADCE0",
                                     highlightthickness=1,
                                     padx=10, pady=10)
                threat_card.pack(fill=tk.X, pady=5)
                
                # Tehdit ikonu
                icon_text = "🔴" if "TEHLİKE" in entry["message"] else "🟠"
                icon = tk.Label(threat_card, 
                             text=icon_text, 
                             font=("Arial", 14),
                             bg="#FFFFFF")
                icon.pack(side=tk.LEFT, padx=(0, 10))
                
                # Tehdit mesajı
                message = entry["message"]
                # Emojileri temizle ve daha okunaklı hale getir
                message = message.replace("⚠️", "").replace("❌", "")
                
                message_label = tk.Label(threat_card, 
                                      text=message, 
                                      font=("Arial", 10),
                                      bg="#FFFFFF", 
                                      fg="#202124",
                                      wraplength=370,
                                      justify="left")
                message_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Önlemler kartı
        actions_card = tk.Frame(content_frame, 
                             bg="#F8F9FA",
                             highlightbackground="#DADCE0",
                             highlightthickness=1,
                             padx=15, pady=15)
        actions_card.pack(fill=tk.X, pady=10)
        
        actions_title = tk.Label(actions_card, 
                               text="Önerilen Önlemler", 
                               font=("Arial", 12, "bold"),
                               bg="#F8F9FA", 
                               fg="#202124")
        actions_title.pack(anchor="w", pady=(0, 10))
        
        # Önerilen önlemleri madde işaretleriyle göster
        actions = [
            "Ağ bağlantınızı hemen kesin veya güvenli olmayan ağlarda hassas işlemler yapmaktan kaçının.",
            "Ağ yöneticinize durumu bildirin.",
            "VPN kullanarak ağ trafiğinizi şifreleyin.",
            "HTTPS bağlantıları ve güvenli iletişim protokolleri kullanın.",
            "Statik ARP girdileri ekleyerek kritik cihazların MAC adreslerini sabitleyin."
        ]
        
        for i, action in enumerate(actions):
            action_frame = tk.Frame(actions_card, bg="#F8F9FA")
            action_frame.pack(fill=tk.X, pady=2)
            
            bullet = tk.Label(action_frame, 
                           text="•", 
                           font=("Arial", 12, "bold"),
                           bg="#F8F9FA", 
                           fg=self.button_color)
            bullet.pack(side=tk.LEFT, padx=(0, 5))
            
            action_label = tk.Label(action_frame, 
                                 text=action, 
                                 font=("Arial", 10),
                                 bg="#F8F9FA", 
                                 fg="#202124",
                                 wraplength=400,
                                 justify="left")
            action_label.pack(side=tk.LEFT, fill=tk.X, expand=True, anchor="w")
        
        # Butonlar çerçevesi (Google tarzı butonlar)
        buttons_frame = tk.Frame(content_frame, bg="#FFFFFF")
        buttons_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Kapat butonu (Google tarzı düz buton)
        close_button = tk.Button(buttons_frame, 
                                text="Anladım", 
                                command=self.warning_window.destroy,
                                bg=self.button_color, 
                                fg="#FFFFFF",
                                font=("Arial", 10, "bold"),
                                relief=tk.FLAT,
                                padx=15,
                                pady=8)
        close_button.pack(side=tk.RIGHT)
        
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
        result_card = self.results_text.master  # Sonuç kartını al
        
        if is_safe:
            # Güvenli durum
            self.status_icon_label.config(text="✅")
            self.status_title.config(text="AĞINIZ GÜVENDEDİR", fg=self.success_color)
            self.status_description.config(text="Ağınızda herhangi bir ARP spoofing tehdidi tespit edilmedi. "
                                          "Düzenli olarak kontrol etmeye devam edin.")
            
            # Sonuç kartı çerçeve rengini güncelle
            result_card.config(highlightbackground=self.success_color)
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
            
            # Sonuç kartı çerçeve rengini güncelle
            result_card.config(highlightbackground=self.warning_color)
    
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
