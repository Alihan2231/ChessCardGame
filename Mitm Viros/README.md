ARP Spoofing Tespit Aracı
Bu araç, ağınızda olası ARP Spoofing saldırılarını tespit etmek için geliştirilmiş bir komut satırı (CLI) uygulamasıdır.

Özellikler
Ağdaki ARP tablosunu analiz eder
Aynı MAC adresine sahip birden fazla IP adresi olup olmadığını kontrol eder
Şüpheli durumlar tespit edildiğinde kullanıcıyı uyarır
Ağ trafiğinin izleniyor olabileceğine dair bilgiler ve güvenlik tavsiyeleri sunar
Demo modu ile güvenli bir ortamda test imkanı sağlar
Windows, Linux ve macOS işletim sistemlerinde çalışabilir
Gereksinimler
Python 3.6 veya daha yeni bir sürüm
Subprocess, Re, Time, Platform modülleri (Python standart kütüphanesi)
Kullanım
Programı çalıştırmak için komut satırından şu komutu kullanın:

python arp_detector.py
Demo modu için:

python arp_detector.py --demo
Güvenlik Tavsiyeleri
Eğer ARP Spoofing tespit edilirse:

Hemen ağ bağlantınızı kesin
Ağ yöneticinizi bilgilendirin
Cihazınızı güvenli bir ağa geçirin
Güvenlik yazılımlarınızı güncelleyin
Şifrelerinizi güvenli bir cihazdan değiştirin
