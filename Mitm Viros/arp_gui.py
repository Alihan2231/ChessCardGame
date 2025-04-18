#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ARP Spoofing Tespit Aracı - Grafik Arayüz
Bu araç, ağda olası ARP spoofing saldırılarını tespit etmek için tkinter tabanlı bir grafik arayüz sunar.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import time
import arp_detector

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
        import io
        import sys
        from contextlib import redirect_stdout
        
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
            import sys
            sys.argv = [sys.argv[0], "--demo"]
        else:
            import sys
            sys.argv = [sys.argv[0]]
        
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
            self.capture_output(arp_detector.arp_kontrol_et)
            
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
        
        # 24 saat sonrası için zaman hesapla
        next_time = time.localtime(time.time() + 86400)
        self.update_text(f"\n⏱️  Bir sonraki kontrol {time.strftime('%d.%m.%Y %H:%M:%S', next_time)} tarihinde yapılacak.\n")
        
        # Periyodik tarama iş parçacığını başlat
        self.periodic_thread = threading.Thread(target=self._periodic_scan_thread, daemon=True)
        self.periodic_thread.start()
        
        # Durumu güncelle
        self.status_var.set("Periyodik tarama aktif")
    
    def _periodic_scan_thread(self):
        """
        Periyodik tarama iş parçacığı.
        """
        try:
            while self.periodic_running:
                # 24 saat bekle (86400 saniye)
                for i in range(86400):
                    # Her saniye kontrol et, kalan süreyi güncelle
                    if not self.periodic_running:
                        return
                    
                    if i % 60 == 0:  # Her dakikada bir durum çubuğunu güncelle
                        remaining = 86400 - i
                        hours, remainder = divmod(remaining, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        self.root.after(0, lambda h=hours, m=minutes: self.status_var.set(
                            f"Bir sonraki taramaya {h} saat {m} dakika kaldı"))
                    
                    time.sleep(1)
                
                # Süre dolunca tarama yap
                if self.periodic_running:  # Hala çalışıyor mu?
                    self.root.after(0, lambda: self.status_var.set("Taranıyor..."))
                    self.root.after(0, lambda: self.update_text("\n" + "=" * 60 + "\n"))
                    self.root.after(0, lambda: self.update_text("🔄 Periyodik ARP taraması başlatıldı\n"))
                    
                    # Ana thread'de değiliz, bu yüzden after kullanarak UI thread'inde çalıştır
                    self.root.after(0, lambda: threading.Thread(target=self._run_periodic_scan, daemon=True).start())
                    
                    # Taramanın tamamlanmasını bekle (kısa bir süre)
                    time.sleep(5)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", f"Periyodik tarama sırasında bir hata oluştu: {str(e)}"))
            self.stop_periodic_scan()
    
    def _run_periodic_scan(self):
        """
        Periyodik tarama sırasında tek bir tarama çalıştırır.
        """
        try:
            # ARP taramasını yap
            self.capture_output(arp_detector.arp_kontrol_et)
            
            # 24 saat sonrası için zaman hesapla
            next_time = time.localtime(time.time() + 86400)
            self.update_text(f"\n⏱️  Bir sonraki kontrol {time.strftime('%d.%m.%Y %H:%M:%S', next_time)} tarihinde yapılacak.\n")
            
            # Durumu güncelle
            self.status_var.set("Periyodik tarama aktif")
        except Exception as e:
            messagebox.showerror("Hata", f"Periyodik tarama sırasında bir hata oluştu: {str(e)}")
            self.stop_periodic_scan()
    
    def stop_periodic_scan(self):
        """
        Periyodik taramayı durdurur.
        """
        self.periodic_running = False
        self.stop_button.config(state=tk.DISABLED)
        self.scan_button.config(state=tk.NORMAL)
        self.periodic_check.config(state=tk.NORMAL)
        self.periodic_var.set(False)
        
        self.update_text("\n🛑 Periyodik tarama durduruldu.\n")
        self.status_var.set("Hazır")
    
    def exit_program(self):
        """
        Programdan çıkış yapar.
        """
        if self.periodic_running:
            self.periodic_running = False
            if self.periodic_thread and self.periodic_thread.is_alive():
                self.periodic_thread.join(1.0)  # En fazla 1 saniye bekle
        
        self.root.destroy()
        
def main():
    """
    Ana program çalıştırma fonksiyonu.
    """
    root = tk.Tk()
    root.configure(bg="#2E3440")
    
    # Stil tanımlamaları
    style = ttk.Style()
    style.theme_use('default')
    style.configure("TProgressbar", thickness=10, troughcolor="#3B4252", background="#5E81AC")
    
    app = ARP_GUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
