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
from tkinter import scrolledtext, messagebox, ttk
import threading
from collections import defaultdict
import io
from contextlib import redirect_stdout

# ============= ARP TESPİT MODÜLÜ =============

# Örnek veriler (demo modu için)
DEMO_ARP_TABLE = [
    {"ip": "192.168.1.1", "mac": "aa:bb:cc:dd:ee:ff", "interface": "eth0"},
    {"ip": "192.168.1.2", "mac": "11:22:33:44:55:66", "interface": "eth0"},
    {"ip": "192.168.1.3", "mac": "aa:bb:cc:11:22:33", "interface": "eth0"},
    {"ip": "192.168.1.4", "mac": "aa:bb:cc:11:22:33", "interface": "eth0"}, # Tekrarlayan MAC adresi (şüpheli)
    {"ip": "192.168.1.5", "mac": "ff:ff:ff:ff:ff:ff", "interface": "eth0"},
]

DEMO_DEFAULT_GATEWAY = {"ip": "192.168.1.1", "mac": "aa:bb:cc:dd:ee:ff"}

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
    if "--demo" in sys.argv:
        print("📊 Demo modu aktif: Örnek veriler kullanılıyor...")
        time.sleep(1)  # Kullanıcı için küçük bir gecikme
        return DEMO_ARP_TABLE
    
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
        # Hata durumunda demo verilerini kullan
        print("⚠️ Hata oluştuğu için örnek veriler kullanılıyor...")
        return DEMO_ARP_TABLE
    
    return arp_entries

# Varsayılan ağ geçidini bulma
def get_default_gateway():
    """
    Varsayılan ağ geçidini (default gateway) bulur.
    
    Returns:
        dict: Ağ geçidi IP ve MAC adresi
    """
    if "--demo" in sys.argv:
        print("📊 Demo modu aktif: Örnek ağ geçidi kullanılıyor...")
        return DEMO_DEFAULT_GATEWAY
    
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
        
        # Renk şeması
        self.bg_color = "#2E3440"
        self.text_color = "#ECEFF4"
        self.button_color = "#5E81AC"
        self.warning_color = "#BF616A"
        self.success_color = "#A3BE8C"
        
        # Uygulama simgesi
        try:
            self.root.iconbitmap("arp_icon.ico")
        except:
            pass  # Simge dosyası yoksa devam et
        
        # Ana çerçeveyi oluştur
        self.main_frame = tk.Frame(root, bg=self.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Başlık ve açıklama
        title_label = tk.Label(self.main_frame, 
                              text="ARP Spoofing Tespit Aracı", 
                              font=("Arial", 18, "bold"),
                              bg=self.bg_color, 
                              fg=self.text_color)
        title_label.pack(pady=10)
        
        description_label = tk.Label(self.main_frame, 
                                    text="Bu araç, ağınızda olası ARP Spoofing saldırılarını tespit eder.\n"
                                         "ARP Spoofing, bir saldırganın ağ trafiğinizi izlemesine olanak tanır.",
                                    font=("Arial", 10),
                                    bg=self.bg_color, 
                                    fg=self.text_color, 
                                    justify="center")
        description_label.pack(pady=5)
        
        # Seçenekler çerçevesi
        options_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        options_frame.pack(fill=tk.X, pady=10)
        
        # Demo modu onay kutusu
        self.demo_var = tk.BooleanVar()
        demo_check = tk.Checkbutton(options_frame, 
                                   text="Demo modu (Örnek veriler kullan)", 
                                   variable=self.demo_var,
                                   bg=self.bg_color, 
                                   fg=self.text_color,
                                   selectcolor=self.bg_color,
                                   activebackground=self.bg_color,
                                   activeforeground=self.text_color)
        demo_check.pack(side=tk.LEFT, padx=10)
        
        # Periyodik kontrol onay kutusu
        self.periodic_var = tk.BooleanVar()
        self.periodic_check = tk.Checkbutton(options_frame, 
                                          text="Periyodik kontrol (24 saatte bir)", 
                                          variable=self.periodic_var,
                                          bg=self.bg_color, 
                                          fg=self.text_color,
                                          selectcolor=self.bg_color,
                                          activebackground=self.bg_color,
                                          activeforeground=self.text_color)
        self.periodic_check.pack(side=tk.LEFT, padx=10)
        
        # Sonuçlar için metin alanı
        self.results_text = scrolledtext.ScrolledText(self.main_frame, 
                                                    wrap=tk.WORD, 
                                                    height=20,
                                                    bg="#3B4252", 
                                                    fg=self.text_color,
                                                    font=("Consolas", 10))
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=10)
        self.results_text.insert(tk.END, "Program başlatıldı. ARP taraması için 'Tara' butonuna tıklayın.\n")
        self.results_text.config(state=tk.DISABLED)
        
        # İlerleme çubuğu
        self.progress = ttk.Progressbar(self.main_frame, 
                                       orient=tk.HORIZONTAL, 
                                       length=100, 
                                       mode='indeterminate')
        
        # Butonlar çerçevesi
        button_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Tarama butonu
        self.scan_button = tk.Button(button_frame, 
                                   text="Tara", 
                                   command=self.start_scan,
                                   bg=self.button_color, 
                                   fg=self.text_color,
                                   width=15,
                                   font=("Arial", 10, "bold"))
        self.scan_button.pack(side=tk.LEFT, padx=10)
        
        # Durdur butonu (periyodik tarama için)
        self.stop_button = tk.Button(button_frame, 
                                   text="Durdur", 
                                   command=self.stop_periodic_scan,
                                   bg=self.warning_color, 
                                   fg=self.text_color,
                                   width=15,
                                   font=("Arial", 10, "bold"),
                                   state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10)
        
        # Çıkış butonu
        exit_button = tk.Button(button_frame, 
                              text="Çıkış", 
                              command=self.exit_program,
                              bg="#4C566A", 
                              fg=self.text_color,
                              width=15,
                              font=("Arial", 10, "bold"))
        exit_button.pack(side=tk.RIGHT, padx=10)
        
        # Periyodik tarama için durum değişkenleri
        self.periodic_running = False
        self.periodic_thread = None
        
        # Durum çubuğu
        self.status_var = tk.StringVar()
        self.status_var.set("Hazır")
        status_bar = tk.Label(self.main_frame, 
                            textvariable=self.status_var, 
                            bd=1, 
                            relief=tk.SUNKEN, 
                            anchor=tk.W,
                            bg="#4C566A", 
                            fg=self.text_color)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Kapanış sırasında periyodik taramayı düzgün şekilde sonlandır
        self.root.protocol("WM_DELETE_WINDOW", self.exit_program)
    
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
    
    def capture_output(self, func, *args, **kwargs):
        """
        Bir fonksiyonun print çıktılarını yakalar ve GUI'de gösterir.
        
        Args:
            func: Çıktısı yakalanacak fonksiyon
            *args, **kwargs: Fonksiyona geçirilecek argümanlar
            
        Returns:
            Fonksiyonun geri dönüş değeri
        """
        f = io.StringIO()
        with redirect_stdout(f):
            result = func(*args, **kwargs)
        
        output = f.getvalue()
        
        # Okunurluğu artırmak için renklendir
        lines = output.split('\n')
        for line in lines:
            if "⚠️" in line or "❌" in line:
                self.update_text(line + "\n", is_warning=True)
            elif "✅" in line:
                self.update_text(line + "\n", is_success=True)
            elif "📌 Broadcast" in line or "📌 Multicast" in line:
                # Broadcast ve multicast bilgilerini mavi renkle göster
                self.results_text.config(state=tk.NORMAL)
                self.results_text.insert(tk.END, line + "\n", "info")
                if not "info" in self.results_text.tag_names():
                    self.results_text.tag_configure("info", foreground="#88C0D0")
                self.results_text.see(tk.END)
                self.results_text.config(state=tk.DISABLED)
            else:
                self.update_text(line + "\n")
        
        return result
    
    def start_scan(self):
        """
        ARP taramasını başlatır.
        """
        # Demo modu argümanını ayarla
        if self.demo_var.get():
            sys.argv = [sys.argv[0], "--demo"] if len(sys.argv) <= 1 else sys.argv
            if "--demo" not in sys.argv:
                sys.argv.append("--demo")
        else:
            # Demo modu kapalıysa, argüman listesinden "--demo" çıkar
            if "--demo" in sys.argv:
                sys.argv.remove("--demo")
        
        # Arayüzü hazırla
        self.status_var.set("Taranıyor...")
        self.scan_button.config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.start()
        self.update_text("=" * 60 + "\n", clear=True)
        self.update_text("🛡️  ARP SPOOFING TESPİT ARACI  🛡️\n")
        self.update_text("=" * 60 + "\n")
        self.update_text("📌 Bu araç, ağınızda olası ARP Spoofing saldırılarını tespit eder.\n")
        self.update_text("📌 ARP Spoofing, bir saldırganın ağ trafiğinizi izlemesine olanak tanır.\n")
        self.update_text("=" * 60 + "\n")
        
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
        
        self.update_text("\n🕒 Periyodik kontrol aktifleştirildi. 24 saatte bir ARP tablosu kontrol edilecek.\n")
        self.update_text("ℹ️  Durdurmak için 'Durdur' butonuna tıklayabilirsiniz.\n")
        
        # Periyodik tarama iş parçacığını başlat
        self.periodic_thread = threading.Thread(target=self._periodic_scan_thread, daemon=True)
        self.periodic_thread.start()
    
    def _periodic_scan_thread(self):
        """
        Periyodik tarama için arka plan iş parçacığı.
        """
        # Her 24 saatte bir tarama yap (86400 saniye)
        interval_seconds = 86400
        
        # 🚩 DEV TEST: Kısa interval ile test etmek için 
        # (Yorumları kaldırarak test edebilirsiniz)
        #interval_seconds = 30  # Test için 30 saniye
        
        while self.periodic_running:
            # İlk taramayı hemen yap
            self.root.after(0, lambda: self.status_var.set("Periyodik tarama başlatılıyor..."))
            
            try:
                # Ana threadde güvenli bir şekilde UI güncelle
                self.root.after(0, lambda: self.update_text("\n" + "=" * 60 + "\n"))
                self.root.after(0, lambda: self.update_text(f"🕒 Periyodik tarama başlatılıyor - {time.strftime('%Y-%m-%d %H:%M:%S')}\n"))
                
                # Taramayı yap
                self.capture_output(arp_kontrol_et)
                
                # Ana threadde güvenli bir şekilde UI güncelle
                self.root.after(0, lambda: self.update_text(f"✅ Periyodik tarama tamamlandı - {time.strftime('%Y-%m-%d %H:%M:%S')}\n"))
                self.root.after(0, lambda: self.update_text(f"🕒 Bir sonraki tarama: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + interval_seconds))}\n"))
                self.root.after(0, lambda: self.update_text("=" * 60 + "\n"))
                self.root.after(0, lambda: self.status_var.set("Bir sonraki periyodik tarama bekleniyor..."))
            except Exception as e:
                # Hata durumunda güvenli bir şekilde UI güncelle
                error_message = f"❌ Periyodik tarama sırasında hata oluştu: {str(e)}\n"
                self.root.after(0, lambda msg=error_message: self.update_text(msg, is_warning=True))
            
            # 24 saat bekle veya durdurulana kadar
            for _ in range(interval_seconds):
                if not self.periodic_running:
                    break
                time.sleep(1)
    
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
